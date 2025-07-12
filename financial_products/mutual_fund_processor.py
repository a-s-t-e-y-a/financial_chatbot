"""
Mutual Fund Product Processor

This module implements the MutualFundProcessor class that processes
mutual fund products following SOLID principles.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base_product import BaseProductProcessor, ProductInfo, ScoredProduct, ProductCategory


@dataclass
class MutualFundInfo(ProductInfo):
    """Extended product info for mutual funds"""
    amc: str
    risk_level: str
    rating: int
    returns_1y: Optional[float]
    returns_3y: Optional[float] 
    returns_5y: Optional[float]
    nav: Optional[float]
    aum: Optional[float]
    expense_ratio: Optional[float]
    min_investment: Optional[float]
    fund_manager: Optional[str]
    inception_date: Optional[str]
    holdings: List[str]
    sector_allocation: List[str]


class MutualFundProcessor(BaseProductProcessor):
    """
    Mutual Fund processor that extracts features and calculates scores
    for mutual fund products following Single Responsibility Principle.
    """
    
    def __init__(self):
        self.category = ProductCategory.MUTUAL_FUNDS

    def process_product(self, raw_data: Dict[str, Any]) -> MutualFundInfo:
        """
        Process raw mutual fund data into structured format
        
        Args:
            raw_data: Raw mutual fund data from JSON
            
        Returns:
            MutualFundInfo object with extracted features
        """
        # Extract basic information
        name = raw_data.get('name', '').strip()
        description = raw_data.get('description', '')
        
        # Extract returns and convert to float
        returns_1y = self._extract_return_percentage(raw_data.get('returns_1y'))
        returns_3y = self._extract_return_percentage(raw_data.get('returns_3y'))
        returns_5y = self._extract_return_percentage(raw_data.get('returns_5y'))
        
        # Extract other numeric fields
        nav = self._safe_float_conversion(raw_data.get('nav'))
        aum = self._safe_float_conversion(raw_data.get('aum'))
        expense_ratio = self._safe_float_conversion(raw_data.get('expense_ratio'))
        min_investment = self._safe_float_conversion(raw_data.get('min_investment'))
        
        # Extract rating (ensure it's an integer)
        rating = self._safe_int_conversion(raw_data.get('rating', 0))
        
        # Extract lists
        holdings = raw_data.get('holdings', []) if raw_data.get('holdings') else []
        sector_allocation = raw_data.get('sector_allocation', []) if raw_data.get('sector_allocation') else []
        
        return MutualFundInfo(
            id=f"mf_{hash(name)}",
            name=name,
            description=description,
            category=self.category,
            features=self._extract_features(raw_data),
            amc=raw_data.get('amc', 'Unknown'),
            risk_level=raw_data.get('risk_level', 'Unknown'),
            rating=rating,
            returns_1y=returns_1y,
            returns_3y=returns_3y,
            returns_5y=returns_5y,
            nav=nav,
            aum=aum,
            expense_ratio=expense_ratio,
            min_investment=min_investment,
            fund_manager=raw_data.get('fund_manager'),
            inception_date=raw_data.get('inception_date'),
            holdings=holdings,
            sector_allocation=sector_allocation
        )

    def calculate_score(self, product: MutualFundInfo, user_preferences: Dict[str, Any] = None) -> float:
        """
        Calculate relevance score for mutual fund based on returns, rating, and risk
        
        Args:
            product: MutualFundInfo object
            user_preferences: User preferences for scoring
            
        Returns:
            Calculated score between 0-100
        """
        if user_preferences is None:
            user_preferences = {}
            
        score = 0.0
        max_score = 100.0
        
        # Performance score (40% weight)
        performance_score = self._calculate_performance_score(product)
        score += performance_score * 0.4
        
        # Rating score (25% weight)
        rating_score = self._calculate_rating_score(product.rating)
        score += rating_score * 0.25
        
        # Risk alignment score (20% weight)
        risk_score = self._calculate_risk_score(product.risk_level, user_preferences)
        score += risk_score * 0.2
        
        # Expense ratio score (10% weight)
        expense_score = self._calculate_expense_score(product.expense_ratio)
        score += expense_score * 0.1
        
        # AUM and stability score (5% weight)
        stability_score = self._calculate_stability_score(product)
        score += stability_score * 0.05
        
        return min(score, max_score)

    def _extract_features(self, raw_data: Dict[str, Any]) -> List[str]:
        """Extract key features for the mutual fund"""
        features = []
        
        # Add performance features
        if raw_data.get('returns_3y'):
            features.append(f"3Y Returns: {raw_data['returns_3y']}")
        if raw_data.get('returns_5y'):
            features.append(f"5Y Returns: {raw_data['returns_5y']}")
            
        # Add rating
        if raw_data.get('rating'):
            features.append(f"Rating: {raw_data['rating']}/5 stars")
            
        # Add risk level
        if raw_data.get('risk_level'):
            features.append(f"Risk: {raw_data['risk_level']}")
            
        # Add expense ratio
        if raw_data.get('expense_ratio'):
            features.append(f"Expense Ratio: {raw_data['expense_ratio']}%")
            
        # Add minimum investment
        if raw_data.get('min_investment'):
            features.append(f"Min Investment: ₹{raw_data['min_investment']}")
            
        # Add fund manager
        if raw_data.get('fund_manager'):
            features.append(f"Fund Manager: {raw_data['fund_manager']}")
            
        return features

    def _extract_return_percentage(self, return_str: Optional[str]) -> Optional[float]:
        """Extract return percentage from string format"""
        if not return_str:
            return None
            
        # Remove % sign and convert to float
        try:
            return float(str(return_str).replace('%', '').strip())
        except (ValueError, AttributeError):
            return None

    def _safe_float_conversion(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_int_conversion(self, value: Any) -> int:
        """Safely convert value to int"""
        if value is None:
            return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    def _calculate_performance_score(self, product: MutualFundInfo) -> float:
        """Calculate performance score based on returns"""
        score = 0.0
        
        # Prioritize longer-term returns
        if product.returns_5y is not None:
            score += min(product.returns_5y * 2, 50)  # Max 50 points for 5Y returns
        elif product.returns_3y is not None:
            score += min(product.returns_3y * 1.5, 40)  # Max 40 points for 3Y returns
        elif product.returns_1y is not None:
            score += min(product.returns_1y, 30)  # Max 30 points for 1Y returns
            
        return min(score, 50)

    def _calculate_rating_score(self, rating: int) -> float:
        """Calculate score based on rating"""
        if rating <= 0:
            return 0
        return (rating / 5.0) * 25  # Scale to 25 points max

    def _calculate_risk_score(self, risk_level: str, user_preferences: Dict[str, Any]) -> float:
        """Calculate risk alignment score"""
        risk_mapping = {
            'low risk': 1,
            'low to moderate risk': 2,
            'moderate risk': 3,
            'moderately high risk': 4,
            'high risk': 5,
            'very high risk': 6
        }
        
        user_risk_tolerance = user_preferences.get('risk_tolerance', 'moderate risk')
        
        product_risk = risk_mapping.get(risk_level.lower(), 3)
        user_risk = risk_mapping.get(user_risk_tolerance.lower(), 3)
        
        # Perfect match gets full score, penalize large differences
        risk_diff = abs(product_risk - user_risk)
        if risk_diff == 0:
            return 20
        elif risk_diff == 1:
            return 15
        elif risk_diff == 2:
            return 10
        else:
            return 5

    def _calculate_expense_score(self, expense_ratio: Optional[float]) -> float:
        """Calculate score based on expense ratio (lower is better)"""
        if expense_ratio is None:
            return 5  # Default score if unknown
            
        # Lower expense ratio = higher score
        if expense_ratio <= 0.5:
            return 10
        elif expense_ratio <= 1.0:
            return 8
        elif expense_ratio <= 1.5:
            return 6
        elif expense_ratio <= 2.0:
            return 4
        else:
            return 2

    def _calculate_stability_score(self, product: MutualFundInfo) -> float:
        """Calculate stability score based on AUM and inception date"""
        score = 0
        
        # AUM-based scoring (larger funds are generally more stable)
        if product.aum is not None:
            if product.aum >= 10000:  # 10,000 crores+
                score += 3
            elif product.aum >= 5000:   # 5,000+ crores
                score += 2
            elif product.aum >= 1000:   # 1,000+ crores
                score += 1
                
        # Add points for having fund manager info
        if product.fund_manager:
            score += 1
            
        # Add points for diversification (holdings)
        if len(product.holdings) > 50:
            score += 1
            
        return score
