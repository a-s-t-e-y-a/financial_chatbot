"""
Credit Card Ranking Algorithm

This module implements ranking algorithms specifically for credit cards
following the Single Responsibility Principle.
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from financial_products.base_product import ScoredProduct, ProductInfo


@dataclass
class CreditCardRankingCriteria:
    """Criteria for ranking credit cards"""
    cashback_weight: float = 0.3
    annual_fee_weight: float = 0.25
    benefits_weight: float = 0.2
    value_score_weight: float = 0.15
    user_preference_weight: float = 0.1


class CreditCardRanker:
    """
    Ranking algorithm specifically for credit cards
    Implements sophisticated ranking based on multiple criteria
    """
    
    def __init__(self, criteria: CreditCardRankingCriteria = None):
        self.criteria = criteria or CreditCardRankingCriteria()
    
    def rank_products(self, 
                     products: List[ScoredProduct], 
                     user_query: str = "",
                     user_preferences: Dict[str, Any] = None) -> List[ScoredProduct]:
        """
        Rank credit cards based on sophisticated algorithm
        
        Args:
            products: List of scored credit card products
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
        
        # Query relevance boost
        query_boost = self._calculate_query_relevance(product.product, user_query)
        
        # User preference alignment
        preference_boost = self._calculate_preference_alignment(
            product.product, user_preferences
        )
        
        # Spending category optimization
        category_boost = self._calculate_category_optimization(
            product.product, user_preferences
        )
        
        # Combine all factors
        enhanced_score = (
            base_score + 
            query_boost * 5 +  # Max 5 point boost for query relevance
            preference_boost * 3 +  # Max 3 point boost for preferences
            category_boost * 2  # Max 2 point boost for categories
        )
        
        return min(enhanced_score, 100.0)
    
    def _calculate_query_relevance(self, product: ProductInfo, query: str) -> float:
        """Calculate how relevant the product is to the user's query"""
        if not query:
            return 0
            
        query_lower = query.lower()
        relevance_score = 0
        
        # Check product name relevance
        if any(word in product.name.lower() for word in query_lower.split()):
            relevance_score += 0.3
        
        # Check features relevance
        feature_text = " ".join(product.features).lower()
        query_words = query_lower.split()
        
        # Specific keyword matching
        keyword_matches = {
            'cashback': ['cashback', 'cash back', 'rewards'],
            'travel': ['travel', 'miles', 'airline', 'hotel'],
            'fuel': ['fuel', 'petrol', 'gas'],
            'dining': ['dining', 'restaurant', 'food'],
            'shopping': ['shopping', 'online', 'ecommerce'],
            'premium': ['premium', 'luxury', 'exclusive'],
            'no annual fee': ['no annual fee', 'free', 'zero fee']
        }
        
        for query_word in query_words:
            for category, keywords in keyword_matches.items():
                if query_word in keywords and category in feature_text:
                    relevance_score += 0.1
        
        return min(relevance_score, 1.0)
    
    def _calculate_preference_alignment(self, 
                                      product: ProductInfo, 
                                      preferences: Dict[str, Any]) -> float:
        """Calculate alignment with user preferences"""
        alignment_score = 0
        
        # Annual fee preference
        max_annual_fee = preferences.get('max_annual_fee')
        if max_annual_fee is not None:
            # This would need to be extracted from product data
            # For now, we'll use a simplified approach
            if 'no annual fee' in " ".join(product.features).lower():
                alignment_score += 0.4
            elif 'annual fee' in " ".join(product.features).lower():
                alignment_score += 0.2
        
        # Income range alignment
        income_range = preferences.get('income_range')
        if income_range:
            product_name_lower = product.name.lower()
            if income_range == 'premium' and any(word in product_name_lower 
                                               for word in ['premium', 'privilege', 'signature']):
                alignment_score += 0.3
            elif income_range == 'mid' and any(word in product_name_lower 
                                             for word in ['select', 'classic']):
                alignment_score += 0.3
            elif income_range == 'entry' and any(word in product_name_lower 
                                                for word in ['student', 'basic', 'starter']):
                alignment_score += 0.3
        
        # Spending category preferences
        preferred_categories = preferences.get('spending_categories', [])
        feature_text = " ".join(product.features).lower()
        
        for category in preferred_categories:
            if category.lower() in feature_text:
                alignment_score += 0.1
        
        return min(alignment_score, 1.0)
    
    def _calculate_category_optimization(self, 
                                       product: ProductInfo, 
                                       preferences: Dict[str, Any]) -> float:
        """Calculate optimization for spending categories"""
        optimization_score = 0
        
        # High-value category bonuses
        feature_text = " ".join(product.features).lower()
        
        high_value_categories = {
            'travel': 0.3,
            'dining': 0.2,
            'fuel': 0.2,
            'online shopping': 0.25,
            'groceries': 0.15
        }
        
        for category, bonus in high_value_categories.items():
            if category in feature_text:
                optimization_score += bonus
        
        return min(optimization_score, 1.0)
    
    def _generate_ranking_reasoning(self, 
                                   product: ScoredProduct, 
                                   enhanced_score: float) -> str:
        """Generate human-readable reasoning for the ranking"""
        base_reasoning = product.reasoning
        
        score_improvement = enhanced_score - product.score
        
        if score_improvement > 3:
            additional_reasoning = " Highly relevant to your query and preferences."
        elif score_improvement > 1:
            additional_reasoning = " Good match for your requirements."
        elif score_improvement > 0:
            additional_reasoning = " Partially matches your preferences."
        else:
            additional_reasoning = ""
        
        return base_reasoning + additional_reasoning


def get_credit_card_ranker() -> CreditCardRanker:
    """Factory function to get credit card ranker instance"""
    return CreditCardRanker()
