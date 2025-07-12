"""
Fixed Deposit product processor.
Handles all fixed deposit specific logic and feature extraction.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .base_product import BaseProductProcessor, ProductInfo, ProductCategory


@dataclass
class FixedDepositInfo(ProductInfo):
    """Extended product info for fixed deposits"""
    bank_name: str
    interest_rate_min: Optional[float] = None
    interest_rate_max: Optional[float] = None
    tenure_from_days: Optional[int] = None
    tenure_to_days: Optional[int] = None
    senior_citizen_rate: Optional[float] = None


class FixedDepositProcessor(BaseProductProcessor):
    """
    Processes fixed deposit products.
    Single responsibility: Handle FD data processing and feature extraction.
    """
    
    def __init__(self):
        self.category = ProductCategory.FIXED_DEPOSITS
    
    def process_product(self, raw_data: Dict[str, Any]) -> FixedDepositInfo:
        """Process raw fixed deposit data into FixedDepositInfo"""
        bank_name = raw_data.get('bank_name', raw_data.get('bank', 'Unknown Bank'))
        name = f"{bank_name} Fixed Deposit"
        
        # Extract features
        features = self._extract_features(raw_data)
        
        # Extract specific FD attributes
        interest_rate_min = self._extract_min_interest_rate(raw_data)
        interest_rate_max = self._extract_max_interest_rate(raw_data)
        senior_citizen_rate = self._extract_senior_citizen_rate(raw_data)
        tenure_from = raw_data.get('tenure_from_days')
        tenure_to = raw_data.get('tenure_to_days')
        
        return FixedDepositInfo(
            id=f"fd_{hash(name)}",
            name=name,
            description=raw_data.get('about', ''),
            category=self.category,
            features=features,
            bank_name=bank_name,
            interest_rate_min=interest_rate_min,
            interest_rate_max=interest_rate_max,
            senior_citizen_rate=senior_citizen_rate,
            tenure_from_days=int(tenure_from) if tenure_from else None,
            tenure_to_days=int(tenure_to) if tenure_to else None
        )

    def calculate_score(self, product: FixedDepositInfo, user_preferences: Dict[str, Any] = None) -> float:
        """Calculate relevance score for fixed deposit"""
        if user_preferences is None:
            user_preferences = {}
            
        score = 0.0
        
        # Interest rate scoring (50% weight)
        if product.interest_rate_max:
            score += min(product.interest_rate_max * 8, 50)  # Max 50 points
        
        # Senior citizen benefits (20% weight)
        if product.senior_citizen_rate and product.interest_rate_max:
            if product.senior_citizen_rate > product.interest_rate_max:
                score += 20
            else:
                score += 10
        
        # Tenure flexibility (20% weight)
        if product.tenure_from_days and product.tenure_to_days:
            tenure_range = product.tenure_to_days - product.tenure_from_days
            if tenure_range > 1000:  # More than ~3 years range
                score += 20
            elif tenure_range > 365:  # More than 1 year range
                score += 15
            else:
                score += 10
        
        # Bank credibility (10% weight)
        reputable_banks = ['sbi', 'hdfc', 'icici', 'axis', 'kotak', 'pnb']
        if any(bank in product.bank_name.lower() for bank in reputable_banks):
            score += 10
        else:
            score += 5
        
        return min(score, 100.0)

    def _extract_features(self, raw_data: Dict[str, Any]) -> List[str]:
        """Extract key features from raw data"""
        features = []
        
        # Extract interest rate info
        max_rate = self._extract_max_interest_rate(raw_data)
        if max_rate:
            features.append(f"Interest rate up to {max_rate}%")
        
        # Extract senior citizen rate
        senior_rate = self._extract_senior_citizen_rate(raw_data)
        if senior_rate and max_rate and senior_rate > max_rate:
            features.append(f"Senior citizen rate: {senior_rate}%")
        
        # Extract tenure info
        tenure_from = raw_data.get('tenure_from_days')
        if tenure_from:
            years = int(tenure_from) / 365
            if years >= 1:
                features.append(f"Minimum tenure: {years:.1f} years")
            else:
                features.append(f"Minimum tenure: {int(tenure_from)} days")
        
        return features

    def _extract_min_interest_rate(self, raw_data: Dict[str, Any]) -> Optional[float]:
        """Extract minimum interest rate"""
        rate_str = raw_data.get('roi_in_percentage_min_tenure')
        return self._parse_rate(rate_str)

    def _extract_max_interest_rate(self, raw_data: Dict[str, Any]) -> Optional[float]:
        """Extract maximum interest rate"""
        rate_str = raw_data.get('roi_in_percentage_max_tenure')
        return self._parse_rate(rate_str)

    def _extract_senior_citizen_rate(self, raw_data: Dict[str, Any]) -> Optional[float]:
        """Extract senior citizen interest rate"""
        rate_str = raw_data.get('roi_in_percentage_senior_citizen_max_tenure')
        return self._parse_rate(rate_str)

    def _parse_rate(self, rate_str) -> Optional[float]:
        """Parse interest rate string to float"""
        if not rate_str:
            return None
        try:
            return float(str(rate_str).replace('%', '').strip())
        except (ValueError, AttributeError):
            return None
    
    def create_description(self, product: ProductInfo) -> str:
        """Create enhanced searchable description for fixed deposit"""
        desc_parts = []
        
        # Basic info
        desc_parts.append(f"Fixed Deposit: {product.bank}")
        
        features = product.features
        
        # Interest rates
        interest_rate = features.get('interest_rate', 0)
        if interest_rate > 0:
            desc_parts.append(f"INTEREST RATE: {interest_rate}%")
        
        senior_rate = features.get('senior_citizen_rate', 0)
        if senior_rate > interest_rate:
            desc_parts.append(f"SENIOR CITIZEN RATE: {senior_rate}%")
        
        # Tenure information
        min_tenure = features.get('min_tenure_days', 0)
        max_tenure = features.get('max_tenure_days', 0)
        if min_tenure > 0:
            desc_parts.append(f"TENURE: {min_tenure} to {max_tenure} days")
        
        # Deposit limits
        min_deposit = features.get('min_deposit', 0)
        max_deposit = features.get('max_deposit_crores', 0)
        if min_deposit > 0:
            desc_parts.append(f"MIN DEPOSIT: ₹{min_deposit}")
        if max_deposit > 0:
            desc_parts.append(f"MAX DEPOSIT: ₹{max_deposit} Cr")
        
        # Bank type and rating
        bank_type = features.get('bank_type', '')
        if bank_type:
            desc_parts.append(f"BANK TYPE: {bank_type}")
        
        rating = features.get('credit_rating', 0)
        if rating > 0:
            desc_parts.append(f"RATING: {rating}")
        
        return " | ".join(desc_parts)
    
    def extract_features(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract numerical and categorical features for ranking"""
        features = {}
        
        # Interest rates
        features['interest_rate'] = self._extract_interest_rate(raw_data)
        features['senior_citizen_rate'] = self._extract_senior_rate(raw_data)
        
        # Tenure information
        features['min_tenure_days'] = self._extract_tenure(raw_data, 'min')
        features['max_tenure_days'] = self._extract_tenure(raw_data, 'max')
        
        # Deposit limits
        features['min_deposit'] = self._extract_deposit_limit(raw_data, 'min')
        features['max_deposit_crores'] = self._extract_deposit_limit(raw_data, 'max')
        
        # Bank information
        features['bank_type'] = self._extract_bank_type(raw_data)
        features['credit_rating'] = self._extract_credit_rating(raw_data)
        
        # Calculated features
        features['rate_premium'] = self._calculate_rate_premium(features)
        features['flexibility_score'] = self._calculate_flexibility_score(features)
        
        return features
    
    def _extract_interest_rate(self, raw_data: Dict[str, Any]) -> float:
        """Extract regular interest rate"""
        rate_sources = [
            raw_data.get('roi_in_percentage', 0),
            raw_data.get('interest_rate', 0),
            raw_data.get('rate', 0)
        ]
        
        for rate in rate_sources:
            if rate and isinstance(rate, (int, float)) and rate > 0:
                return float(rate)
        
        # Try to extract from text
        description = raw_data.get('description', '')
        rate_match = re.search(r'(\d+(?:\.\d+)?)%.*interest', description.lower())
        if rate_match:
            return float(rate_match.group(1))
        
        return 0.0
    
    def _extract_senior_rate(self, raw_data: Dict[str, Any]) -> float:
        """Extract senior citizen interest rate"""
        senior_sources = [
            raw_data.get('roi_senior_citizens_in_percentage', 0),
            raw_data.get('senior_citizen_rate', 0),
            raw_data.get('senior_rate', 0)
        ]
        
        for rate in senior_sources:
            if rate and isinstance(rate, (int, float)) and rate > 0:
                return float(rate)
        
        return self._extract_interest_rate(raw_data)  # Default to regular rate
    
    def _extract_tenure(self, raw_data: Dict[str, Any], tenure_type: str) -> int:
        """Extract tenure information (min or max)"""
        if tenure_type == 'min':
            sources = [
                raw_data.get('tenure_from_days', 0),
                raw_data.get('min_tenure', 0)
            ]
        else:  # max
            sources = [
                raw_data.get('tenure_to_days', 0),
                raw_data.get('max_tenure', 0)
            ]
        
        for tenure in sources:
            if tenure and isinstance(tenure, (int, float)) and tenure > 0:
                return int(tenure)
        
        # Default values
        return 7 if tenure_type == 'min' else 3650  # 7 days to 10 years
    
    def _extract_deposit_limit(self, raw_data: Dict[str, Any], limit_type: str) -> float:
        """Extract deposit limits"""
        if limit_type == 'min':
            sources = [
                raw_data.get('deposit_min', 0),
                raw_data.get('min_deposit', 0)
            ]
            default = 1000  # ₹1,000 typical minimum
        else:  # max
            sources = [
                raw_data.get('deposit_max_in_crores', 0),
                raw_data.get('max_deposit', 0)
            ]
            default = 100  # ₹100 Cr typical maximum
        
        for limit in sources:
            if limit and isinstance(limit, (int, float)) and limit > 0:
                return float(limit)
        
        return default
    
    def _extract_bank_type(self, raw_data: Dict[str, Any]) -> str:
        """Extract bank type"""
        bank_type = raw_data.get('bank_type', '')
        if bank_type:
            return bank_type.title()
        
        # Infer from bank name
        bank_name = raw_data.get('bank_name', '').lower()
        
        private_banks = ['axis', 'icici', 'hdfc', 'kotak', 'yes', 'indusind']
        public_banks = ['sbi', 'pnb', 'bob', 'canara', 'union', 'indian']
        
        for private in private_banks:
            if private in bank_name:
                return 'Private'
        
        for public in public_banks:
            if public in bank_name:
                return 'Public'
        
        return 'Other'
    
    def _extract_credit_rating(self, raw_data: Dict[str, Any]) -> float:
        """Extract credit rating"""
        rating_sources = [
            raw_data.get('credit_rating_mapping', 0),
            raw_data.get('rating', 0),
            raw_data.get('credit_rating', 0)
        ]
        
        for rating in rating_sources:
            if rating and isinstance(rating, (int, float)) and rating > 0:
                return float(rating)
        
        # Default rating based on bank type
        bank_type = self._extract_bank_type(raw_data)
        if bank_type == 'Public':
            return 4.0  # Higher rating for public banks
        elif bank_type == 'Private':
            return 3.5  # Good rating for private banks
        else:
            return 3.0  # Default rating
    
    def _calculate_rate_premium(self, features: Dict[str, Any]) -> float:
        """Calculate how much above average the rate is"""
        interest_rate = features.get('interest_rate', 0)
        bank_type = features.get('bank_type', '')
        
        # Average rates by bank type (approximate market rates)
        average_rates = {
            'Public': 6.5,
            'Private': 7.0,
            'Other': 6.0
        }
        
        avg_rate = average_rates.get(bank_type, 6.5)
        return max(0, interest_rate - avg_rate)
    
    def _calculate_flexibility_score(self, features: Dict[str, Any]) -> float:
        """Calculate flexibility based on tenure and deposit options"""
        min_tenure = features.get('min_tenure_days', 365)
        max_deposit = features.get('max_deposit_crores', 1)
        
        # Lower minimum tenure = more flexible
        tenure_score = max(0, 5 - (min_tenure / 365))  # 5 points for 0 days, 0 for 5+ years
        
        # Higher deposit limit = more flexible
        deposit_score = min(5, max_deposit / 20)  # 5 points for ₹100Cr+
        
        return (tenure_score + deposit_score) / 2
