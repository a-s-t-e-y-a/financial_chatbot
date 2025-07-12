"""
Financial Product Manager

This module orchestrates all financial product components following
the Single Responsibility and Open/Closed principles.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Import processors
from financial_products.base_product import ProductCategory, ScoredProduct
from financial_products.credit_card_processor import CreditCardProcessor
from financial_products.fixed_deposit_processor import FixedDepositProcessor
from financial_products.mutual_fund_processor import MutualFundProcessor

# Import data loaders
from data_loaders.credit_card_loader import CreditCardDataLoader
from data_loaders.fixed_deposit_loader import FixedDepositDataLoader
from data_loaders.mutual_fund_loader import MutualFundDataLoader

# Import ranking algorithms
from ranking_algorithms.credit_card_ranker import get_credit_card_ranker
from ranking_algorithms.fixed_deposit_ranker import get_fixed_deposit_ranker
from ranking_algorithms.mutual_fund_ranker import get_mutual_fund_ranker

# Import vector manager
from vector_managers.cloudflare_vectorize import CloudflareVectorizeManager, FallbackVectorManager, VectorMetadata


@dataclass
class ProductRecommendation:
    """Recommendation result with products and reasoning"""
    products: List[ScoredProduct]
    total_found: int
    query_processed: str
    recommendations_reasoning: str


class FinancialProductManager:
    """
    Central manager that orchestrates all financial product operations
    Implements the Facade pattern for simplified client interaction
    """
    
    def __init__(self, 
                 data_directory: str = "data",
                 use_cloudflare: bool = True,
                 embedding_function=None):
        """
        Initialize the financial product manager
        
        Args:
            data_directory: Path to data directory
            use_cloudflare: Whether to use Cloudflare Vectorize
            embedding_function: Function to generate embeddings
        """
        self.data_directory = data_directory
        self.embedding_function = embedding_function
        
        # Initialize processors
        self.processors = {
            ProductCategory.CREDIT_CARDS: CreditCardProcessor(),
            ProductCategory.FIXED_DEPOSITS: FixedDepositProcessor(),
            ProductCategory.MUTUAL_FUNDS: MutualFundProcessor()
        }
        
        # Initialize data loaders
        self.data_loaders = {
            ProductCategory.CREDIT_CARDS: CreditCardDataLoader(data_directory),
            ProductCategory.FIXED_DEPOSITS: FixedDepositDataLoader(data_directory),
            ProductCategory.MUTUAL_FUNDS: MutualFundDataLoader(data_directory)
        }
        
        # Initialize ranking algorithms
        self.rankers = {
            ProductCategory.CREDIT_CARDS: get_credit_card_ranker(),
            ProductCategory.FIXED_DEPOSITS: get_fixed_deposit_ranker(),
            ProductCategory.MUTUAL_FUNDS: get_mutual_fund_ranker()
        }
        
        # Initialize vector manager
        self.vector_manager = self._initialize_vector_manager(use_cloudflare)
        
        # Cache for processed products
        self._product_cache = {}
    
    def recommend_products(self,
                          user_query: str,
                          product_categories: List[ProductCategory] = None,
                          user_preferences: Dict[str, Any] = None,
                          max_results: int = 10) -> ProductRecommendation:
        """
        Get product recommendations based on user query and preferences
        
        Args:
            user_query: User's search query
            product_categories: Categories to search in (all if None)
            user_preferences: User preferences for personalization
            max_results: Maximum number of results to return
            
        Returns:
            ProductRecommendation with ranked products
        """
        if product_categories is None:
            product_categories = list(ProductCategory)
        
        if user_preferences is None:
            user_preferences = {}
        
        all_products = []
        
        # Process each product category
        for category in product_categories:
            try:
                category_products = self._process_category(
                    category, user_query, user_preferences
                )
                all_products.extend(category_products)
            except Exception as e:
                print(f"Error processing {category.value}: {e}")
                continue
        
        # Rank all products together
        ranked_products = self._rank_across_categories(
            all_products, user_query, user_preferences
        )
        
        # Limit results
        final_products = ranked_products[:max_results]
        
        # Generate reasoning
        reasoning = self._generate_recommendation_reasoning(
            user_query, final_products, len(all_products)
        )
        
        return ProductRecommendation(
            products=final_products,
            total_found=len(all_products),
            query_processed=user_query,
            recommendations_reasoning=reasoning
        )
    
    def get_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific product"""
        # This would query the vector store or cache for product details
        # Implementation depends on how product IDs are structured
        pass
    
    def initialize_vector_store(self) -> bool:
        """
        Initialize and populate the vector store with all products
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create index if using Cloudflare
            if isinstance(self.vector_manager, CloudflareVectorizeManager):
                if not self.vector_manager.create_index_if_not_exists():
                    print("Failed to create Vectorize index")
                    return False
            
            # Process and embed all products
            total_embedded = 0
            
            for category in ProductCategory:
                try:
                    products_embedded = self._embed_category_products(category)
                    total_embedded += products_embedded
                    print(f"Embedded {products_embedded} {category.value} products")
                except Exception as e:
                    print(f"Error embedding {category.value} products: {e}")
                    continue
            
            print(f"Total products embedded: {total_embedded}")
            return total_embedded > 0
            
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            return False
    
    def get_category_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for each product category"""
        stats = {}
        
        for category in ProductCategory:
            try:
                loader = self.data_loaders[category]
                processor = self.processors[category]
                
                # Load raw data
                raw_data = loader.load_data()
                
                # Get available sources
                sources = loader.get_available_sources()
                
                stats[category.value] = {
                    'total_products': len(raw_data),
                    'available_sources': len(sources),
                    'sources': sources[:10]  # Limit to first 10
                }
                
            except Exception as e:
                stats[category.value] = {
                    'error': str(e),
                    'total_products': 0,
                    'available_sources': 0,
                    'sources': []
                }
        
        return stats
    
    def _process_category(self,
                         category: ProductCategory,
                         user_query: str,
                         user_preferences: Dict[str, Any]) -> List[ScoredProduct]:
        """Process products for a specific category"""
        # Load data
        loader = self.data_loaders[category]
        processor = self.processors[category]
        ranker = self.rankers[category]
        
        # Get source filter from preferences
        source_filter = user_preferences.get(f'{category.value}_source')
        raw_data = loader.load_data(source_filter)
        
        # Process products
        scored_products = []
        for raw_product in raw_data:
            try:
                processed_product = processor.process_product(raw_product)
                score = processor.calculate_score(processed_product, user_preferences)
                
                scored_product = ScoredProduct(
                    product=processed_product,
                    score=score,
                    reasoning=f"Base score: {score:.1f}"
                )
                scored_products.append(scored_product)
                
            except Exception as e:
                print(f"Error processing product {raw_product.get('name', 'Unknown')}: {e}")
                continue
        
        # Apply category-specific ranking
        ranked_products = ranker.rank_products(
            scored_products, user_query, user_preferences
        )
        
        return ranked_products
    
    def _rank_across_categories(self,
                               products: List[ScoredProduct],
                               user_query: str,
                               user_preferences: Dict[str, Any]) -> List[ScoredProduct]:
        """Rank products across all categories"""
        # For now, simple sorting by score
        # Could implement more sophisticated cross-category ranking
        return sorted(products, key=lambda x: x.score, reverse=True)
    
    def _generate_recommendation_reasoning(self,
                                         user_query: str,
                                         products: List[ScoredProduct],
                                         total_found: int) -> str:
        """Generate human-readable reasoning for recommendations"""
        if not products:
            return f"No products found matching '{user_query}'. Try different search terms."
        
        top_score = products[0].score
        categories = set(p.product.category.value for p in products)
        
        reasoning = f"Found {total_found} products matching '{user_query}'. "
        reasoning += f"Showing top {len(products)} recommendations "
        reasoning += f"from {len(categories)} categories: {', '.join(categories)}. "
        reasoning += f"Top recommendation score: {top_score:.1f}/100."
        
        return reasoning
    
    def _embed_category_products(self, category: ProductCategory) -> int:
        """Embed all products for a category into vector store"""
        if not self.embedding_function:
            print("No embedding function provided")
            return 0
        
        loader = self.data_loaders[category]
        processor = self.processors[category]
        
        raw_data = loader.load_data()
        vectors_to_upsert = []
        
        for raw_product in raw_data:
            try:
                # Process product
                processed_product = processor.process_product(raw_product)
                
                # Create text for embedding
                embed_text = self._create_embedding_text(processed_product)
                
                # Generate embedding
                embedding = self.embedding_function(embed_text)
                
                # Create metadata
                metadata = VectorMetadata(
                    product_id=processed_product.id,
                    product_type=category.value,
                    product_name=processed_product.name,
                    bank_name=getattr(processed_product, 'bank', None)
                )
                
                # Generate vector ID
                vector_id = self.vector_manager.generate_vector_id({
                    'name': processed_product.name,
                    'type': category.value,
                    'bank': getattr(processed_product, 'bank', '')
                })
                
                vectors_to_upsert.append((vector_id, embedding, metadata))
                
            except Exception as e:
                print(f"Error embedding product {raw_product.get('name', 'Unknown')}: {e}")
                continue
        
        # Upsert to vector store
        if vectors_to_upsert:
            success = self.vector_manager.upsert_vectors(vectors_to_upsert)
            return len(vectors_to_upsert) if success else 0
        
        return 0
    
    def _create_embedding_text(self, product) -> str:
        """Create text representation for embedding"""
        text_parts = [
            product.name,
            product.description,
            f"Category: {product.category.value}"
        ]
        
        # Add features
        if product.features:
            text_parts.append("Features: " + "; ".join(product.features))
        
        # Add category-specific information
        if hasattr(product, 'bank'):
            text_parts.append(f"Bank: {product.bank}")
        
        if hasattr(product, 'risk_level'):
            text_parts.append(f"Risk: {product.risk_level}")
        
        return " | ".join(filter(None, text_parts))
    
    def _initialize_vector_manager(self, use_cloudflare: bool):
        """Initialize the appropriate vector manager"""
        if use_cloudflare:
            try:
                return CloudflareVectorizeManager()
            except Exception as e:
                print(f"Failed to initialize Cloudflare Vectorize: {e}")
                print("Falling back to local vector manager")
                return FallbackVectorManager()
        else:
            return FallbackVectorManager()
