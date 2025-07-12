"""
Financial Products Module

This module contains all financial product processors following SOLID principles.
"""

from .base_product import ProductCategory, ProductInfo, ScoredProduct, BaseProductProcessor

__all__ = [
    'ProductCategory',
    'ProductInfo', 
    'ScoredProduct',
    'BaseProductProcessor'
]
