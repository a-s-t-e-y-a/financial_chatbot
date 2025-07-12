"""
Base product interface and common models for financial products.
Follows Single Responsibility Principle.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum

class ProductCategory(Enum):
    CREDIT_CARDS = "credit_cards"
    FIXED_DEPOSITS = "fixed_deposits"
    MUTUAL_FUNDS = "mutual_funds"
    INSURANCE = "insurance"
    LOANS = "loans"

@dataclass
class ProductInfo:
    """Base product information model"""
    id: str
    name: str
    description: str
    category: ProductCategory
    features: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'features': self.features
        }

@dataclass
class ScoredProduct:
    """Product with associated relevance score"""
    product: ProductInfo
    score: float
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'product': self.product.to_dict(),
            'score': self.score,
            'reasoning': self.reasoning
        }

class BaseProductProcessor(ABC):
    """
    Abstract base class for product processors.
    Follows Single Responsibility Principle and Open/Closed Principle.
    """
    
    @abstractmethod
    def process_product(self, raw_data: Dict[str, Any]) -> ProductInfo:
        """Process raw product data into ProductInfo"""
        pass
    
    @abstractmethod
    def calculate_score(self, product: ProductInfo, user_preferences: Dict[str, Any] = None) -> float:
        """Calculate relevance score for the product"""
        pass
