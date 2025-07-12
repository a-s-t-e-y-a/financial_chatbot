"""
Credit Card Product Processor

This module implements the CreditCardProcessor class that processes
credit card products following SOLID principles.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base_product import BaseProductProcessor, ProductInfo, ProductCategory


@dataclass
class CreditCardInfo(ProductInfo):
    """Extended product info for credit cards"""
    bank: str
    annual_fee: Optional[float] = None
    cashback_rate: Optional[float] = None
    reward_rate: Optional[float] = None
    welcome_benefit: Optional[str] = None
    fuel_surcharge_waiver: bool = False
    lounge_access: bool = False


class CreditCardProcessor(BaseProductProcessor):
    """
    Credit Card processor that extracts features and calculates scores
    for credit card products following Single Responsibility Principle.
    """
    
    def __init__(self):
        self.category = ProductCategory.CREDIT_CARDS

    def process_product(self, raw_data: Dict[str, Any]) -> CreditCardInfo:
        """
        Process raw credit card data into structured format
        
        Args:
            raw_data: Raw credit card data from JSON
            
        Returns:
            CreditCardInfo object with extracted features
        """
        # Extract basic information
        name = raw_data.get('name', '').strip()
        bank = raw_data.get('bank', raw_data.get('issuer', 'Unknown Bank'))
        description = raw_data.get('description', '')
        
        # Extract features
        features = self._extract_features(raw_data)
        
        # Extract specific credit card attributes
        annual_fee = self._extract_annual_fee(raw_data)
        cashback_rate = self._extract_cashback_rate(raw_data)
        welcome_benefit = self._extract_welcome_benefit(raw_data)
        
        return CreditCardInfo(
            id=f"cc_{hash(name)}",
            name=name,
            description=description,
            category=self.category,
            features=features,
            bank=bank,
            annual_fee=annual_fee,
            cashback_rate=cashback_rate,
            welcome_benefit=welcome_benefit,
            fuel_surcharge_waiver=self._has_fuel_surcharge_waiver(raw_data),
            lounge_access=self._has_lounge_access(raw_data)
        )

    def calculate_score(self, product: CreditCardInfo, user_preferences: Dict[str, Any] = None) -> float:
        """
        Calculate relevance score for credit card based on features and user preferences
        
        Args:
            product: CreditCardInfo object
            user_preferences: User preferences for scoring
            
        Returns:
            Calculated score between 0-100
        """
        if user_preferences is None:
            user_preferences = {}
            
        score = 0.0
        max_score = 100.0
        
        # Cashback rate scoring (30% weight)
        if product.cashback_rate:
            cashback_score = min(product.cashback_rate * 5, 30)  # Max 30 points
            score += cashback_score
        
        # Annual fee scoring (25% weight) - lower is better
        if product.annual_fee is not None:
            if product.annual_fee == 0:
                score += 25  # No annual fee gets full points
            elif product.annual_fee <= 500:
                score += 20  # Low fee
            elif product.annual_fee <= 2000:
                score += 10  # Moderate fee
            else:
                score += 5   # High fee
        else:
            score += 15  # Default score if fee unknown
        
        # Benefits scoring (20% weight)
        benefit_score = 0
        if product.fuel_surcharge_waiver:
            benefit_score += 5
        if product.lounge_access:
            benefit_score += 10
        if product.welcome_benefit:
            benefit_score += 5
        score += min(benefit_score, 20)
        
        # Features scoring (15% weight)
        feature_score = len(product.features) * 2  # 2 points per feature
        score += min(feature_score, 15)
        
        # Bank reputation scoring (10% weight)
        reputable_banks = ['sbi', 'hdfc', 'icici', 'axis', 'kotak']
        if any(bank in product.bank.lower() for bank in reputable_banks):
            score += 10
        else:
            score += 5
        
        return min(score, max_score)

    def _extract_features(self, raw_data: Dict[str, Any]) -> List[str]:
        """Extract key features from raw data"""
        features = []
        
        # Add explicit features from data
        if 'features' in raw_data and raw_data['features']:
            features.extend(raw_data['features'])
        
        # Extract features from description
        description = raw_data.get('description', '')
        if description:
            # Extract cashback mentions
            cashback_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%\s*cashback', description.lower())
            if cashback_matches:
                features.append(f"Up to {max(cashback_matches)}% cashback")
            
            # Extract other benefits
            if 'fuel surcharge' in description.lower():
                features.append("Fuel surcharge waiver")
            if 'lounge' in description.lower():
                features.append("Airport lounge access")
            if 'welcome' in description.lower():
                features.append("Welcome benefits")
        
        return features[:10]  # Limit to top 10 features

    def _extract_annual_fee(self, raw_data: Dict[str, Any]) -> Optional[float]:
        """Extract annual fee from raw data"""
        # Check explicit annual fee field
        if 'annual_fee' in raw_data:
            try:
                return float(raw_data['annual_fee'])
            except (ValueError, TypeError):
                pass
        
        # Extract from description text
        description = raw_data.get('description', '')
        if description:
            # Look for annual fee patterns
            fee_patterns = [
                r'annual fee[:\s]*₹?\s*(\d+)',
                r'₹\s*(\d+)\s*annual fee',
                r'joining fee[:\s]*₹?\s*(\d+)',
            ]
            
            for pattern in fee_patterns:
                matches = re.findall(pattern, description.lower())
                if matches:
                    try:
                        return float(matches[0])
                    except (ValueError, IndexError):
                        continue
        
        return None

    def _extract_cashback_rate(self, raw_data: Dict[str, Any]) -> Optional[float]:
        """Extract cashback rate from raw data"""
        description = raw_data.get('description', '')
        if description:
            # Look for cashback patterns
            cashback_patterns = [
                r'(\d+(?:\.\d+)?)\s*%\s*cashback',
                r'earn\s+(\d+(?:\.\d+)?)\s*%',
                r'(\d+(?:\.\d+)?)\s*percent\s+cashback'
            ]
            
            rates = []
            for pattern in cashback_patterns:
                matches = re.findall(pattern, description.lower())
                for match in matches:
                    try:
                        rates.append(float(match))
                    except ValueError:
                        continue
            
            return max(rates) if rates else None
        
        return None

    def _extract_welcome_benefit(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract welcome benefit information"""
        description = raw_data.get('description', '')
        if description and 'welcome' in description.lower():
            # Look for welcome benefit patterns
            lines = description.split('\n')
            for line in lines:
                if 'welcome' in line.lower():
                    return line.strip()[:100]  # Limit length
        
        return None

    def _has_fuel_surcharge_waiver(self, raw_data: Dict[str, Any]) -> bool:
        """Check if card has fuel surcharge waiver"""
        text = (raw_data.get('description', '') + ' ' + 
                ' '.join(raw_data.get('features', []))).lower()
        return 'fuel surcharge' in text or 'fuel waiver' in text

    def _has_lounge_access(self, raw_data: Dict[str, Any]) -> bool:
        """Check if card has lounge access"""
        text = (raw_data.get('description', '') + ' ' + 
                ' '.join(raw_data.get('features', []))).lower()
        return 'lounge' in text or 'airport access' in text
