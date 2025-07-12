"""
Credit Card Data Loader

This module implements the data loader for credit card products
from JSON files in the bank directories.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from data_loaders.base_loader import BaseDataLoader


class CreditCardDataLoader(BaseDataLoader):
    """
    Data loader for credit card products
    Loads data from bank-specific JSON files
    """
    
    def __init__(self, data_directory: str = "data"):
        super().__init__(data_directory)
        self.bank_directories = self._discover_bank_directories()
    
    def load_data(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load credit card data from JSON files
        
        Args:
            source: Optional bank name to load data from specific bank
            
        Returns:
            List of credit card data dictionaries
        """
        all_cards = []
        
        if source:
            # Load from specific bank
            bank_data = self._load_bank_data(source.lower())
            all_cards.extend(bank_data)
        else:
            # Load from all banks
            for bank_name in self.bank_directories:
                try:
                    bank_data = self._load_bank_data(bank_name)
                    all_cards.extend(bank_data)
                except Exception as e:
                    print(f"Warning: Failed to load data from {bank_name}: {e}")
                    continue
        
        return all_cards
    
    def get_available_sources(self) -> List[str]:
        """
        Get list of available bank sources
        
        Returns:
            List of bank names
        """
        return list(self.bank_directories.keys())
    
    def _discover_bank_directories(self) -> Dict[str, Path]:
        """Discover bank directories containing card data"""
        bank_dirs = {}
        
        if not self.data_directory.exists():
            return bank_dirs
            
        for item in self.data_directory.iterdir():
            if item.is_dir():
                # Check if directory contains cards.json
                cards_json = item / "cards.json"
                if cards_json.exists():
                    bank_dirs[item.name.lower()] = item
        
        return bank_dirs
    
    def _load_bank_data(self, bank_name: str) -> List[Dict[str, Any]]:
        """Load credit card data from specific bank"""
        if bank_name not in self.bank_directories:
            available_banks = ", ".join(self.bank_directories.keys())
            raise ValueError(f"Bank '{bank_name}' not found. Available banks: {available_banks}")
        
        bank_dir = self.bank_directories[bank_name]
        cards_file = bank_dir / "cards.json"
        
        cards_data = self._load_json_file(cards_file)
        
        # Add bank information to each card if not present
        for card in cards_data:
            if 'bank' not in card or not card['bank']:
                card['bank'] = bank_name.title()
        
        return cards_data
    
    def get_bank_card_count(self) -> Dict[str, int]:
        """Get count of cards per bank"""
        counts = {}
        
        for bank_name in self.bank_directories:
            try:
                bank_data = self._load_bank_data(bank_name)
                counts[bank_name] = len(bank_data)
            except Exception:
                counts[bank_name] = 0
                
        return counts
