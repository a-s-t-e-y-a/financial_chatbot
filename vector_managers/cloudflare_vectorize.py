"""
Cloudflare Vectorize Manager

This module implements the Cloudflare Vectorize integration for persistent
vector storage following the Dependency Inversion Principle.
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import requests
from datetime import datetime


@dataclass
class VectorMetadata:
    """Metadata for vector storage"""
    product_id: str
    product_type: str
    product_name: str
    bank_name: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at


class CloudflareVectorizeManager:
    """
    Manager for Cloudflare Vectorize operations
    Implements persistent vector storage with metadata
    """
    
    def __init__(self, 
                 account_id: str = None,
                 api_token: str = None,
                 index_name: str = "financial-products"):
        """
        Initialize Cloudflare Vectorize manager
        
        Args:
            account_id: Cloudflare account ID
            api_token: Cloudflare API token
            index_name: Name of the Vectorize index
        """
        self.account_id = account_id or os.getenv('CLOUDFLARE_ACCOUNT_ID')
        self.api_token = api_token or os.getenv('CLOUDFLARE_API_TOKEN')
        self.index_name = index_name
        
        if not self.account_id or not self.api_token:
            raise ValueError("Cloudflare credentials not provided")
        
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/vectorize/indexes/{self.index_name}"
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
    
    def create_index_if_not_exists(self, dimension: int = 1536) -> bool:
        """
        Create Vectorize index if it doesn't exist
        
        Args:
            dimension: Vector dimension (default for OpenAI embeddings)
            
        Returns:
            True if created or already exists, False if failed
        """
        try:
            # Check if index exists
            response = requests.get(
                f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/vectorize/indexes/{self.index_name}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return True  # Index already exists
            
            # Create index
            create_data = {
                "name": self.index_name,
                "config": {
                    "metric": "cosine",
                    "dimensions": dimension
                }
            }
            
            response = requests.post(
                f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/vectorize/indexes",
                headers=self.headers,
                json=create_data
            )
            
            return response.status_code in [200, 201]
            
        except Exception as e:
            print(f"Error creating Vectorize index: {e}")
            return False
    
    def upsert_vectors(self, 
                      vectors: List[Tuple[str, List[float], VectorMetadata]]) -> bool:
        """
        Upsert vectors to Cloudflare Vectorize
        
        Args:
            vectors: List of (id, vector, metadata) tuples
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare vectors for Cloudflare API
            vector_data = []
            for vector_id, vector, metadata in vectors:
                vector_data.append({
                    "id": vector_id,
                    "values": vector,
                    "metadata": asdict(metadata)
                })
            
            # Split into batches of 1000 (Cloudflare limit)
            batch_size = 1000
            for i in range(0, len(vector_data), batch_size):
                batch = vector_data[i:i + batch_size]
                
                response = requests.post(
                    f"{self.base_url}/upsert",
                    headers=self.headers,
                    json={"vectors": batch}
                )
                
                if response.status_code not in [200, 201]:
                    print(f"Error upserting batch {i//batch_size + 1}: {response.text}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error upserting vectors: {e}")
            return False
    
    def query_vectors(self, 
                     query_vector: List[float],
                     top_k: int = 10,
                     filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Query vectors from Cloudflare Vectorize
        
        Args:
            query_vector: Query vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of matching vectors with metadata
        """
        try:
            query_data = {
                "vector": query_vector,
                "topK": top_k
            }
            
            if filter_metadata:
                query_data["filter"] = filter_metadata
            
            response = requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json=query_data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('result', {}).get('matches', [])
            else:
                print(f"Error querying vectors: {response.text}")
                return []
            
        except Exception as e:
            print(f"Error querying vectors: {e}")
            return []
    
    def delete_vectors(self, vector_ids: List[str]) -> bool:
        """
        Delete vectors from Cloudflare Vectorize
        
        Args:
            vector_ids: List of vector IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/delete",
                headers=self.headers,
                json={"ids": vector_ids}
            )
            
            return response.status_code in [200, 204]
            
        except Exception as e:
            print(f"Error deleting vectors: {e}")
            return False
    
    def get_index_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get index statistics
        
        Returns:
            Index statistics or None if failed
        """
        try:
            response = requests.get(
                f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/vectorize/indexes/{self.index_name}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json().get('result', {})
            else:
                return None
                
        except Exception as e:
            print(f"Error getting index stats: {e}")
            return None
    
    def generate_vector_id(self, product_data: Dict[str, Any]) -> str:
        """
        Generate consistent vector ID from product data
        
        Args:
            product_data: Product data dictionary
            
        Returns:
            Unique vector ID
        """
        # Create a consistent hash from product name and type
        product_name = product_data.get('name', '')
        product_type = product_data.get('type', '')
        bank_name = product_data.get('bank', '')
        
        id_string = f"{product_type}_{bank_name}_{product_name}"
        return hashlib.md5(id_string.encode()).hexdigest()
    
    def clear_index(self) -> bool:
        """
        Clear all vectors from the index (use with caution)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Note: Cloudflare Vectorize doesn't have a direct clear operation
            # This would need to be implemented by querying all vectors and deleting them
            # For now, we'll return a warning
            print("Warning: Clear index operation not implemented for safety")
            return False
            
        except Exception as e:
            print(f"Error clearing index: {e}")
            return False


class FallbackVectorManager:
    """
    Fallback vector manager using local FAISS when Cloudflare is unavailable
    """
    
    def __init__(self, faiss_directory: str = "faiss_indexes"):
        self.faiss_directory = faiss_directory
        self.vectors = {}  # In-memory storage for fallback
    
    def upsert_vectors(self, vectors: List[Tuple[str, List[float], VectorMetadata]]) -> bool:
        """Fallback upsert using in-memory storage"""
        try:
            for vector_id, vector, metadata in vectors:
                self.vectors[vector_id] = {
                    'vector': vector,
                    'metadata': asdict(metadata)
                }
            return True
        except Exception as e:
            print(f"Error in fallback upsert: {e}")
            return False
    
    def query_vectors(self, 
                     query_vector: List[float],
                     top_k: int = 10,
                     filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fallback query using simple similarity"""
        try:
            # Simple cosine similarity implementation
            import numpy as np
            
            query_array = np.array(query_vector)
            similarities = []
            
            for vector_id, data in self.vectors.items():
                vector_array = np.array(data['vector'])
                similarity = np.dot(query_array, vector_array) / (
                    np.linalg.norm(query_array) * np.linalg.norm(vector_array)
                )
                
                # Apply metadata filter if provided
                if filter_metadata:
                    match = True
                    for key, value in filter_metadata.items():
                        if data['metadata'].get(key) != value:
                            match = False
                            break
                    if not match:
                        continue
                
                similarities.append({
                    'id': vector_id,
                    'score': float(similarity),
                    'metadata': data['metadata']
                })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x['score'], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            print(f"Error in fallback query: {e}")
            return []
