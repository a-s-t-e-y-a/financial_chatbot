"""
Fixed Deposit Data Loader

This module implements the data loader for fixed deposit products
from JSON files.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from data_loaders.base_loader import BaseDataLoader


class FixedDepositDataLoader(BaseDataLoader):
    """
    Data loader for fixed deposit products
    Loads data from fixed-deposit/fd.json
    """
    
    def __init__(self, data_directory: str = "data"):
        super().__init__(data_directory)
        self.fd_file = self.data_directory / "fixed-deposit" / "fd.json"
    
    def load_data(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load fixed deposit data from JSON file
        
        Args:
            source: Optional filter by bank name or minimum interest rate
            
        Returns:
            List of fixed deposit data dictionaries
        """
        all_fds = self._load_json_file(self.fd_file)
        
        # Extract data from _source field if it exists
        processed_fds = []
        for fd_item in all_fds:
            if '_source' in fd_item:
                fd_data = fd_item['_source']
            else:
                fd_data = fd_item
            processed_fds.append(fd_data)
        
        if source:
            # Filter by bank name or other criteria
            filtered_fds = []
            source_lower = source.lower()
            
            for fd in processed_fds:
                # Check bank name or other fields
                bank_name = fd.get('bank_name', '').lower()
                about = fd.get('about', '').lower()
                
                if (source_lower in bank_name or 
                    source_lower in about):
                    filtered_fds.append(fd)
            
            return filtered_fds
        
        return processed_fds
    
    def get_available_sources(self) -> List[str]:
        """
        Get list of available banks/institutions
        
        Returns:
            List of bank names
        """
        try:
            all_fds = self.load_data()
            
            banks = set()
            
            for fd in all_fds:
                # Extract bank name from 'about' field
                about = fd.get('about', '')
                if about:
                    # Try to extract bank name from the description
                    bank_name = self._extract_bank_name(about)
                    if bank_name:
                        banks.add(bank_name)
            
            return sorted(list(banks))
            
        except Exception:
            return []
    
    def get_fds_by_interest_rate(self, min_rate: float = 0.0) -> List[Dict[str, Any]]:
        """Get FDs with interest rate >= min_rate"""
        try:
            all_fds = self.load_data()
            
            high_rate_fds = []
            for fd in all_fds:
                max_rate = self._extract_max_interest_rate(fd)
                if max_rate and max_rate >= min_rate:
                    fd['extracted_max_rate'] = max_rate
                    high_rate_fds.append(fd)
            
            # Sort by interest rate (descending)
            return sorted(high_rate_fds, 
                         key=lambda x: x.get('extracted_max_rate', 0), 
                         reverse=True)
            
        except Exception:
            return []
    
    def get_fds_by_tenure(self, min_days: int = 0, max_days: int = float('inf')) -> List[Dict[str, Any]]:
        """Get FDs within specified tenure range"""
        try:
            all_fds = self.load_data()
            
            filtered_fds = []
            for fd in all_fds:
                tenure_from = fd.get('tenure_from_days', 0)
                tenure_to = fd.get('tenure_to_days', tenure_from)
                
                if tenure_from >= min_days and tenure_from <= max_days:
                    filtered_fds.append(fd)
            
            return filtered_fds
            
        except Exception:
            return []
    
    def _extract_bank_name(self, about_text: str) -> Optional[str]:
        """Extract bank name from about text"""
        if not about_text:
            return None
            
        # Common patterns for bank names
        bank_patterns = [
            'State Bank of India', 'SBI',
            'HDFC Bank', 'HDFC',
            'ICICI Bank', 'ICICI',
            'Axis Bank', 'Axis',
            'Kotak Mahindra Bank', 'Kotak',
            'Punjab National Bank', 'PNB',
            'Bank of Baroda', 'BOB',
            'Canara Bank',
            'Union Bank',
            'Indian Bank',
            'Central Bank',
            'Yes Bank',
            'IndusInd Bank',
            'Federal Bank',
            'Karnataka Bank',
            'South Indian Bank',
            'City Union Bank'
        ]
        
        about_lower = about_text.lower()
        
        for pattern in bank_patterns:
            if pattern.lower() in about_lower:
                return pattern
        
        # Try to extract from company name patterns
        if 'limited' in about_lower or 'ltd' in about_lower:
            words = about_text.split()
            for i, word in enumerate(words):
                if word.lower() in ['limited', 'ltd', 'corporation']:
                    # Take up to this word as company name
                    company_name = ' '.join(words[:i+1])
                    if len(company_name) > 10:  # Reasonable company name length
                        return company_name[:50]  # Limit length
        
        return None
    
    def _extract_max_interest_rate(self, fd_data: Dict[str, Any]) -> Optional[float]:
        """Extract maximum interest rate from FD data"""
        # Try different fields for interest rate
        rate_fields = [
            'roi_in_percentage_max_tenure',
            'roi_in_percentage_senior_citizen_max_tenure',
            'roi_in_percentage_min_tenure'
        ]
        
        max_rate = 0.0
        
        for field in rate_fields:
            rate_str = fd_data.get(field)
            if rate_str:
                try:
                    rate = float(str(rate_str).replace('%', '').strip())
                    max_rate = max(max_rate, rate)
                except (ValueError, AttributeError):
                    continue
        
        return max_rate if max_rate > 0 else None
