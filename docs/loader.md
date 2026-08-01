# loader.py Documentation

## Overview
The `loader.py` module (located in `code/ingestion/loader.py`) is responsible for reading, validating, and caching raw CSV datasets into pandas DataFrames. It is designed to be robust and fail-safe, ensuring bad data does not break the downstream routing logic.

## Class: `CSVLoader`

### Responsibilities
- **Loading:** Ingests single or multiple CSVs from a specified directory.
- **Validation:** Ensures critical columns (`message_id`, `user_id`, `conversation_type`, `created_at`) are present.
- **Handling Missing Values:** Sanitizes empty fields (e.g., converts empty `message_text` to empty strings, default `forwarded_count` to 0).
- **Caching:** Prevents redundant disk I/O by storing processed DataFrames in memory.

### Methods
- `__init__(self, data_dir: str = "dataset")`: Initializes the loader with a target directory.
- `load_all(self) -> Dict[str, pd.DataFrame]`: Discovers and loads all `.csv` files in the directory. Continues even if one file fails to load.
- `load_csv(self, file_path: Path | str) -> pd.DataFrame`: Loads a specific CSV. Checks cache first. Validates and cleans data upon reading.
- `_validate_columns(self, df: pd.DataFrame, file_name: str) -> None`: Internal method that raises a `ValueError` if required schema is violated.
- `_handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame`: Internal method that performs data imputation.
- `get_cached_dataset(self, filename: str) -> Optional[pd.DataFrame]`: Helper method to retrieve a specific cached DataFrame by its filename.
- `clear_cache(self) -> None`: Helper method to empty the internal memory cache.

## Usage Example
```python
from code.ingestion.loader import CSVLoader

loader = CSVLoader(data_dir="dataset")
datasets = loader.load_all()

if "messages.csv" in datasets:
    df = loader.get_cached_dataset("messages.csv")
    print(df.head())
```
