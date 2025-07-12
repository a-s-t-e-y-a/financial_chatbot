"""
Mutual Fund Data Loader

This module implements the data loader for mutual fund products
from JSON files.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from data_loaders.base_loader import BaseDataLoader


class MutualFundDataLoader(BaseDataLoader):
    """
    Data loader for mutual fund products
    Loads data from mutual-funds/funds.json
    """
    
    def __init__(self, data_directory: str = "data"):
        super().__init__(data_directory)
        self.funds_file = self.data_directory / "mutual-funds" / "funds.json"
    
    def load_data(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load mutual fund data from JSON file
        
        Args:
            source: Optional filter by fund category or AMC
            
        Returns:
            List of mutual fund data dictionaries
        """
        all_funds = self._load_json_file(self.funds_file)
        
        if source:
            # Filter by category or AMC
            filtered_funds = []
            source_lower = source.lower()
            
            for fund in all_funds:
                # Check category match
                category = fund.get('category', '').lower()
                amc = fund.get('amc', '').lower()
                name = fund.get('name', '').lower()
                
                if (source_lower in category or 
                    source_lower in amc or 
                    source_lower in name):
                    filtered_funds.append(fund)
            
            return filtered_funds
        
        return all_funds
    
    def get_available_sources(self) -> List[str]:
        """
        Get list of available categories and AMCs
        
        Returns:
            List of categories and AMCs
        """
        try:
            all_funds = self._load_json_file(self.funds_file)
            
            categories = set()
            amcs = set()
            
            for fund in all_funds:
                if fund.get('category'):
                    categories.add(fund['category'])
                if fund.get('amc') and fund['amc'] != 'Unknown':
                    amcs.add(fund['amc'])
            
            # Combine categories and AMCs
            sources = list(categories) + list(amcs)
            return sorted(sources)
            
        except Exception:
            return []
    
    def get_funds_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get funds grouped by category"""
        try:
            all_funds = self._load_json_file(self.funds_file)
            
            categorized_funds = {}
            
            for fund in all_funds:
                category = fund.get('category', 'Unknown')
                if category not in categorized_funds:
                    categorized_funds[category] = []
                categorized_funds[category].append(fund)
            
            return categorized_funds
            
        except Exception:
            return {}
    
    def get_funds_by_risk_level(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get funds grouped by risk level"""
        try:
            all_funds = self._load_json_file(self.funds_file)
            
            risk_grouped_funds = {}
            
            for fund in all_funds:
                risk_level = fund.get('risk_level', 'Unknown')
                if risk_level not in risk_grouped_funds:
                    risk_grouped_funds[risk_level] = []
                risk_grouped_funds[risk_level].append(fund)
            
            return risk_grouped_funds
            
        except Exception:
            return {}
    
    def get_top_rated_funds(self, min_rating: int = 4) -> List[Dict[str, Any]]:
        """Get funds with rating >= min_rating"""
        try:
            all_funds = self._load_json_file(self.funds_file)
            
            top_rated = []
            for fund in all_funds:
                rating = fund.get('rating', 0)
                if isinstance(rating, (int, float)) and rating >= min_rating:
                    top_rated.append(fund)
            
            # Sort by rating (descending)
            return sorted(top_rated, key=lambda x: x.get('rating', 0), reverse=True)
            
        except Exception:
            return []
