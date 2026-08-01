"""
Data Ingestion Loader Module
Responsible for loading, validating, and caching CSV datasets.
"""
import logging
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class CSVLoader:
    """
    Handles loading, validation, and caching of CSV dataset files.
    """
    
    REQUIRED_COLUMNS = [
        "message_id", "user_id", "conversation_type", "created_at"
    ]

    def __init__(self, data_dir: str = "dataset"):
        self.data_dir = Path(data_dir)
        self._cache: Dict[str, pd.DataFrame] = {}

    def load_all(self) -> Dict[str, pd.DataFrame]:
        """
        Loads all CSV files in the data directory and caches them.
        Returns a dictionary mapping file names to DataFrames.
        """
        if not self.data_dir.exists():
            logger.warning(f"Data directory {self.data_dir} does not exist.")
            return {}

        csv_files = list(self.data_dir.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files to load.")
        
        for file_path in csv_files:
            try:
                self.load_csv(file_path)
            except Exception as e:
                logger.error(f"Failed to load {file_path.name} during batch load: {e}")
            
        return self._cache

    def load_csv(self, file_path: Path | str) -> pd.DataFrame:
        """
        Loads a single CSV, validates, handles missing values, and caches it.
        """
        path = Path(file_path)
        cache_key = path.name
        
        if cache_key in self._cache:
            logger.info(f"Returning cached data for {cache_key}")
            return self._cache[cache_key]
            
        if not path.exists():
            logger.error(f"File {path} does not exist.")
            raise FileNotFoundError(f"File not found: {path}")

        try:
            logger.info(f"Loading {path}...")
            df = pd.read_csv(path)
            self._validate_columns(df, path.name)
            df = self._handle_missing_values(df)
            self._cache[cache_key] = df
            logger.info(f"Successfully loaded and cached {cache_key}")
            return df
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            raise

    def _validate_columns(self, df: pd.DataFrame, file_name: str) -> None:
        """
        Validates that required columns exist in the DataFrame.
        """
        if file_name != "messages.csv":
            return
            
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            error_msg = f"Missing required columns {missing_cols} in {file_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handles missing values based on dataset rules.
        """
        # Fill empty message text with empty string to avoid NaN type errors
        if "message_text" in df.columns:
            df["message_text"] = df["message_text"].fillna("")
            
        # Ensure forwarded_count is 0 if missing
        if "forwarded_count" in df.columns:
            df["forwarded_count"] = df["forwarded_count"].fillna(0).astype(int)
            
        return df

    def get_cached_dataset(self, filename: str) -> Optional[pd.DataFrame]:
        """
        Helper function to retrieve a specific dataset from cache.
        """
        return self._cache.get(filename)
        
    def clear_cache(self) -> None:
        """
        Clears the current DataFrame cache.
        """
        self._cache.clear()
        logger.info("Cache cleared.")
