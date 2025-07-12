"""
Mutual Fund Ranking Algorithm

This module implements ranking algorithms specifically for mutual funds
following the Single Responsibility Principle.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from financial_products.base_product import ScoredProduct, ProductInfo


@dataclass
class MutualFundRankingCriteria:
    """Criteria for ranking mutual funds"""
    performance_weight: float = 0.35
    risk_alignment_weight: float = 0.25
    rating_weight: float = 0.2
    expense_ratio_weight: float = 0.15
    stability_weight: float = 0.05


class MutualFundRanker:
    """
    Ranking algorithm specifically for mutual funds
    Implements sophisticated ranking based on performance, risk, and user goals
    """
    
    def __init__(self, criteria: MutualFundRankingCriteria = None):
        self.criteria = criteria or MutualFundRankingCriteria()
    
    def rank_products(self, 
                     products: List[ScoredProduct], 
                     user_query: str = "",
                     user_preferences: Dict[str, Any] = None) -> List[ScoredProduct]:
        """
        Rank mutual funds based on sophisticated algorithm
        
        Args:
            products: List of scored mutual fund products
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
        
        # Investment goal alignment
        goal_boost = self._calculate_goal_alignment(product.product, user_preferences)
        
        # Investment horizon optimization
        horizon_boost = self._calculate_horizon_optimization(
            product.product, user_preferences
        )
        
        # Query relevance boost
        query_boost = self._calculate_query_relevance(product.product, user_query)
        
        # SIP suitability bonus
        sip_boost = self._calculate_sip_suitability(product.product, user_preferences)
        
        # Combine all factors
        enhanced_score = (
            base_score + 
            goal_boost * 4 +  # Max 4 point boost for goal alignment
            horizon_boost * 3 +  # Max 3 point boost for investment horizon
            query_boost * 2 +  # Max 2 point boost for query relevance
            sip_boost * 1  # Max 1 point boost for SIP suitability
        )
        
        return min(enhanced_score, 100.0)
    
    def _calculate_goal_alignment(self, 
                                 product: ProductInfo, 
                                 preferences: Dict[str, Any]) -> float:
        """Calculate alignment with investment goals"""
        investment_goal = preferences.get('investment_goal', '').lower()
        if not investment_goal:
            return 0
            
        alignment_score = 0
        product_name_lower = product.name.lower()
        product_category = getattr(product, 'category', '').lower()
        
        goal_category_mapping = {
            'wealth creation': ['equity', 'growth', 'large cap', 'mid cap', 'small cap'],
            'retirement': ['equity', 'balanced', 'hybrid', 'retirement'],
            'tax saving': ['elss', 'tax', 'saving'],
            'regular income': ['debt', 'income', 'dividend', 'monthly income'],
            'capital preservation': ['debt', 'liquid', 'ultra short', 'low duration'],
            'child education': ['equity', 'children', 'education'],
            'emergency fund': ['liquid', 'ultra short', 'overnight']
        }
        
        relevant_categories = goal_category_mapping.get(investment_goal, [])
        
        for category in relevant_categories:
            if (category in product_name_lower or 
                category in product_category or
                category in " ".join(product.features).lower()):
                alignment_score += 0.3
                break
        
        return min(alignment_score, 1.0)
    
    def _calculate_horizon_optimization(self, 
                                      product: ProductInfo, 
                                      preferences: Dict[str, Any]) -> float:
        """Calculate optimization for investment time horizon"""
        investment_horizon = preferences.get('investment_horizon', '').lower()
        if not investment_horizon:
            return 0
            
        optimization_score = 0
        product_text = (product.name + " " + " ".join(product.features)).lower()
        
        # Time horizon optimization rules
        if investment_horizon in ['short term', '1-3 years']:
            if any(term in product_text for term in ['debt', 'liquid', 'short term', 'conservative']):
                optimization_score += 0.5
            elif any(term in product_text for term in ['equity', 'aggressive']):
                optimization_score -= 0.2  # Penalty for mismatch
                
        elif investment_horizon in ['medium term', '3-7 years']:
            if any(term in product_text for term in ['balanced', 'hybrid', 'moderate']):
                optimization_score += 0.5
            elif any(term in product_text for term in ['large cap', 'diversified']):
                optimization_score += 0.3
                
        elif investment_horizon in ['long term', '7+ years']:
            if any(term in product_text for term in ['equity', 'growth', 'small cap', 'mid cap']):
                optimization_score += 0.5
            elif any(term in product_text for term in ['debt', 'liquid']):
                optimization_score -= 0.1  # Small penalty for conservative funds
        
        return max(optimization_score, 0)  # Don't allow negative scores
    
    def _calculate_query_relevance(self, product: ProductInfo, query: str) -> float:
        """Calculate how relevant the product is to the user's query"""
        if not query:
            return 0
            
        query_lower = query.lower()
        relevance_score = 0
        
        # Check product name relevance
        if any(word in product.name.lower() for word in query_lower.split()):
            relevance_score += 0.3
        
        # Specific mutual fund keywords
        mf_keywords = {
            'sip': ['sip', 'systematic'],
            'tax saving': ['elss', 'tax'],
            'large cap': ['large cap', 'blue chip'],
            'small cap': ['small cap'],
            'mid cap': ['mid cap'],
            'debt': ['debt', 'bond', 'fixed income'],
            'equity': ['equity', 'stock'],
            'balanced': ['balanced', 'hybrid'],
            'sectoral': ['sectoral', 'thematic'],
            'index': ['index', 'passive']
        }
        
        product_text = (product.name + " " + " ".join(product.features)).lower()
        
        for query_word in query_lower.split():
            for category, keywords in mf_keywords.items():
                if query_word in keywords:
                    if any(keyword in product_text for keyword in keywords):
                        relevance_score += 0.2
                        break
        
        return min(relevance_score, 1.0)
    
    def _calculate_sip_suitability(self, 
                                  product: ProductInfo, 
                                  preferences: Dict[str, Any]) -> float:
        """Calculate SIP suitability bonus"""
        sip_preference = preferences.get('investment_type', '').lower()
        
        if 'sip' not in sip_preference:
            return 0
            
        sip_score = 0
        product_text = (product.name + " " + " ".join(product.features)).lower()
        
        # Equity funds are generally better for SIP
        if any(term in product_text for term in ['equity', 'growth', 'diversified']):
            sip_score += 0.4
        
        # Large cap and diversified funds are stable for SIP
        if any(term in product_text for term in ['large cap', 'diversified', 'bluechip']):
            sip_score += 0.3
        
        # Avoid very high risk funds for SIP beginners
        risk_level = getattr(product, 'risk_level', '').lower()
        if 'very high' in risk_level:
            sip_score -= 0.1
        
        return max(sip_score, 0)
    
    def _generate_ranking_reasoning(self, 
                                   product: ScoredProduct, 
                                   enhanced_score: float) -> str:
        """Generate human-readable reasoning for the ranking"""
        base_reasoning = product.reasoning
        
        score_improvement = enhanced_score - product.score
        
        if score_improvement > 3:
            additional_reasoning = " Excellent alignment with your investment goals and risk profile."
        elif score_improvement > 1.5:
            additional_reasoning = " Good match for your investment strategy."
        elif score_improvement > 0.5:
            additional_reasoning = " Suitable for your investment preferences."
        else:
            additional_reasoning = ""
        
        return base_reasoning + additional_reasoning


def get_mutual_fund_ranker() -> MutualFundRanker:
    """Factory function to get mutual fund ranker instance"""
    return MutualFundRanker()
