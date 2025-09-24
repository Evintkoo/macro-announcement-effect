"""
Base class for data collectors.
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from utils.config import Config

logger = logging.getLogger(__name__)

# Global config instance
config = Config()

class BaseDataCollector(ABC):
    """Abstract base class for data collectors."""
    
    def __init__(self, name: str):
        """
        Initialize data collector.
        
        Args:
            name: Name of the data collector
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
    @abstractmethod
    def collect_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> pd.DataFrame:
        """
        Collect data for specified symbols and date range.
        
        Args:
            symbols: List of symbols to collect
            start_date: Start date for data collection
            end_date: End date for data collection
            **kwargs: Additional parameters
            
        Returns:
            DataFrame with collected data
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate collected data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    def save_data(
        self,
        data: pd.DataFrame,
        filename: str,
        file_format: str = "csv"
    ) -> str:
        """
        Save collected data to file.
        
        Args:
            data: Data to save
            filename: Filename (without extension)
            file_format: File format ('csv', 'pickle', 'parquet')
            
        Returns:
            Path to saved file
        """
        data_dir = config.get_data_dir("raw")
        filepath = data_dir / f"{filename}.{file_format}"
        
        if file_format == "csv":
            data.to_csv(filepath, index=True)
        elif file_format == "pickle":
            data.to_pickle(filepath)
        elif file_format == "parquet":
            data.to_parquet(filepath)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        self.logger.info(f"Data saved to {filepath}")
        return str(filepath)
    
    def load_data(
        self,
        filename: str,
        file_format: str = "csv"
    ) -> pd.DataFrame:
        """
        Load data from file.
        
        Args:
            filename: Filename (without extension)
            file_format: File format ('csv', 'pickle', 'parquet')
            
        Returns:
            Loaded DataFrame
        """
        data_dir = config.get_data_dir("raw")
        filepath = data_dir / f"{filename}.{file_format}"
        
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        if file_format == "csv":
            data = pd.read_csv(filepath, index_col=0, parse_dates=True)
        elif file_format == "pickle":
            data = pd.read_pickle(filepath)
        elif file_format == "parquet":
            data = pd.read_parquet(filepath)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        self.logger.info(f"Data loaded from {filepath}")
        return data