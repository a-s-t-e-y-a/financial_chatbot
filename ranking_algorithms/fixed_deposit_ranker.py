"""
Fixed Deposit Ranking Algorithm

This module implements ranking algorithms specifically for fixed deposits
following the Single Responsibility Principle.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from financial_products.base_product import ScoredProduct, ProductInfo


@dataclass
class FixedDepositRankingCriteria:
    """Criteria for ranking fixed deposits"""
    interest_rate_weight: float = 0.4
    tenure_flexibility_weight: float = 0.25
    bank_credibility_weight: float = 0.2
    minimum_deposit_weight: float = 0.1
    senior_citizen_benefits_weight: float = 0.05


class FixedDepositRanker:
    """
    Ranking algorithm specifically for fixed deposits
    Implements sophisticated ranking based on interest rates, tenure, and safety
    """
    
    def __init__(self, criteria: FixedDepositRankingCriteria = None):
        self.criteria = criteria or FixedDepositRankingCriteria()
    
    def rank_products(self, 
                     products: List[ScoredProduct], 
                     user_query: str = "",
                     user_preferences: Dict[str, Any] = None) -> List[ScoredProduct]:
        """
        Rank fixed deposits based on sophisticated algorithm
        
        Args:
            products: List of scored fixed deposit products
            user_query: User's search query for context
            user_preferences: User preferences for personalization
            
        Returns:
            Sorted list of products with updated ranking scores
        """
        if not products:
            return []
            
        if user_preferences is None:
            user_preferences = {}
        
        # Apply additional ranking factors
        enhanced_products = []
        for product in products:
            enhanced_score = self._calculate_enhanced_score(
                product, user_query, user_preferences
            )
            
            enhanced_product = ScoredProduct(
                product=product.product,
                score=enhanced_score,
                reasoning=self._generate_ranking_reasoning(product, enhanced_score)
            )
            enhanced_products.append(enhanced_product)
        
        # Sort by enhanced score (descending)
        return sorted(enhanced_products, key=lambda x: x.score, reverse=True)
    
    def _calculate_enhanced_score(self, 
                                 product: ScoredProduct, 
                                 user_query: str,
                                 user_preferences: Dict[str, Any]) -> float:
        """Calculate enhanced ranking score"""
        base_score = product.score
        
        # Tenure alignment boost
        tenure_boost = self._calculate_tenure_alignment(product.product, user_preferences)
        
        # Amount alignment boost
        amount_boost = self._calculate_amount_alignment(product.product, user_preferences)
        
        # Senior citizen optimization
        senior_boost = self._calculate_senior_citizen_boost(product.product, user_preferences)
        
        # Query relevance boost
        query_boost = self._calculate_query_relevance(product.product, user_query)
        
        # Safety and credibility boost
        safety_boost = self._calculate_safety_boost(product.product)
        
        # Combine all factors
        enhanced_score = (
            base_score + 
            tenure_boost * 3 +  # Max 3 point boost for tenure alignment
            amount_boost * 2 +  # Max 2 point boost for amount alignment
            senior_boost * 2 +  # Max 2 point boost for senior citizens
            query_boost * 2 +  # Max 2 point boost for query relevance
            safety_boost * 1  # Max 1 point boost for safety
        )
        
        return min(enhanced_score, 100.0)
    
    def _calculate_tenure_alignment(self, 
                                   product: ProductInfo, 
                                   preferences: Dict[str, Any]) -> float:
        """Calculate alignment with preferred investment tenure"""
        preferred_tenure = preferences.get('investment_tenure')
        if not preferred_tenure:
            return 0
            
        alignment_score = 0
        product_text = (product.name + " " + " ".join(product.features)).lower()
        
        # Extract tenure information from product
        tenure_keywords = {
            'short_term': ['7 days', '15 days', '30 days', '1 month', '3 months', '6 months'],
            'medium_term': ['1 year', '2 years', '3 years', '18 months'],
            'long_term': ['4 years', '5 years', '7 years', '10 years']
        }
        
        if preferred_tenure in tenure_keywords:
            preferred_keywords = tenure_keywords[preferred_tenure]
            for keyword in preferred_keywords:
                if keyword in product_text:
                    alignment_score += 0.5
                    break
        
        # Flexible tenure options get bonus
        if any(term in product_text for term in ['flexible', 'auto renewal', 'premature withdrawal']):
            alignment_score += 0.3
        
        return min(alignment_score, 1.0)
    
    def _calculate_amount_alignment(self, 
                                   product: ProductInfo, 
                                   preferences: Dict[str, Any]) -> float:
        """Calculate alignment with investment amount"""
        investment_amount = preferences.get('investment_amount')
        if not investment_amount:
            return 0
            
        alignment_score = 0
        product_text = " ".join(product.features).lower()
        
        # Check minimum investment requirements
        if investment_amount >= 100000:  # 1 lakh+
            if any(term in product_text for term in ['high value', 'premium', 'bulk deposit']):
                alignment_score += 0.5
        elif investment_amount >= 25000:  # 25k+
            if any(term in product_text for term in ['regular', 'standard']):
                alignment_score += 0.4
        else:  # Below 25k
            if any(term in product_text for term in ['minimum', 'small', 'low amount']):
                alignment_score += 0.4
        
        return min(alignment_score, 1.0)
    
    def _calculate_senior_citizen_boost(self, 
                                       product: ProductInfo, 
                                       preferences: Dict[str, Any]) -> float:
        """Calculate boost for senior citizen benefits"""
        is_senior_citizen = preferences.get('is_senior_citizen', False)
        if not is_senior_citizen:
            return 0
            
        senior_boost = 0
        product_text = (product.name + " " + " ".join(product.features)).lower()
        
        # Check for senior citizen specific benefits
        senior_keywords = [
            'senior citizen', 'senior', 'additional rate', 'extra interest',
            'higher rate for senior', 'bonus rate'
        ]
        
        for keyword in senior_keywords:
            if keyword in product_text:
                senior_boost += 0.3
                break
        
        return min(senior_boost, 1.0)
    
    def _calculate_query_relevance(self, product: ProductInfo, query: str) -> float:
        """Calculate how relevant the product is to the user's query"""
        if not query:
            return 0
            
        query_lower = query.lower()
        relevance_score = 0
        
        # FD specific keywords
        fd_keywords = {
            'high interest': ['high', 'best', 'maximum', 'top'],
            'short term': ['short', 'quick', 'immediate'],
            'long term': ['long', 'extended', 'multi-year'],
            'flexible': ['flexible', 'premature', 'withdrawal'],
            'safe': ['safe', 'secure', 'guaranteed'],
            'senior citizen': ['senior', 'citizen', 'elderly']
        }
        
        product_text = (product.name + " " + " ".join(product.features)).lower()
        
        for query_word in query_lower.split():
            for category, keywords in fd_keywords.items():
                if query_word in keywords:
                    if category.replace(' ', '') in product_text.replace(' ', ''):
                        relevance_score += 0.2
                        break
        
        # Direct name matching
        if any(word in product.name.lower() for word in query_lower.split()):
            relevance_score += 0.3
        
        return min(relevance_score, 1.0)
    
    def _calculate_safety_boost(self, product: ProductInfo) -> float:
        """Calculate safety and credibility boost"""
        safety_score = 0
        product_text = (product.name + " " + " ".join(product.features)).lower()
        
        # Government/PSU banks get higher safety scores
        safe_institutions = [
            'sbi', 'state bank', 'pnb', 'punjab national', 'bank of baroda',
            'canara bank', 'union bank', 'indian bank', 'government'
        ]
        
        for institution in safe_institutions:
            if institution in product_text:
                safety_score += 0.4
                break
        
        # DICGC insured deposits
        if any(term in product_text for term in ['dicgc', 'insured', 'deposit insurance']):
            safety_score += 0.3
        
        # High credit rating
        if any(term in product_text for term in ['aaa', 'aa+', 'stable rating']):
            safety_score += 0.3
        
        return min(safety_score, 1.0)
    
    def _generate_ranking_reasoning(self, 
                                   product: ScoredProduct, 
                                   enhanced_score: float) -> str:
        """Generate human-readable reasoning for the ranking"""
        base_reasoning = product.reasoning
        
        score_improvement = enhanced_score - product.score
        
        if score_improvement > 2:
            additional_reasoning = " Excellent match for your deposit requirements and risk profile."
        elif score_improvement > 1:
            additional_reasoning = " Good alignment with your investment preferences."
        elif score_improvement > 0.5:
            additional_reasoning = " Suitable option for your deposit needs."
        else:
            additional_reasoning = ""
        
        return base_reasoning + additional_reasoning


def get_fixed_deposit_ranker() -> FixedDepositRanker:
    """Factory function to get fixed deposit ranker instance"""
    return FixedDepositRanker()
