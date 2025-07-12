"""
Base Data Loader Interface

This module defines the base interface for data loaders following
the Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path


class BaseDataLoader(ABC):
    """
    Abstract base class for data loaders
    Implements the Interface Segregation Principle
    """
    
    def __init__(self, data_directory: str):
        self.data_directory = Path(data_directory)
        
    @abstractmethod
    def load_data(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load data from the specified source
        
        Args:
            source: Optional source identifier (e.g., bank name)
            
        Returns:
            List of raw product data dictionaries
        """
        pass
    
    @abstractmethod
    def get_available_sources(self) -> List[str]:
        """
        Get list of available data sources
        
        Returns:
            List of source identifiers
        """
        pass
    
    def _validate_file_exists(self, file_path: Path) -> bool:
        """Validate that a file exists"""
        return file_path.exists() and file_path.is_file()
    
    def _load_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load and parse JSON file"""
        import json
        
        if not self._validate_file_exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Ensure we return a list
            if isinstance(data, dict):
                return [data]
            elif isinstance(data, list):
                return data
            else:
                raise ValueError(f"Unexpected data format in {file_path}")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {file_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading file {file_path}: {e}")
