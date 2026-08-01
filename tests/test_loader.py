import pytest
import pandas as pd
from pathlib import Path
from src.ingestion.loader import CSVLoader

@pytest.fixture
def temp_dataset_dir(tmp_path):
    """Fixture to create a temporary dataset directory with a valid CSV."""
    d = tmp_path / "dataset"
    d.mkdir()
    
    valid_csv = d / "valid.csv"
    valid_csv.write_text(
        "message_id,user_id,conversation_type,created_at,message_text,forwarded_count\n"
        "msg_1,u_1,personal,2026-07-30 22:19,,NaN\n"
        "msg_2,u_2,group,2026-07-30 22:20,Hello,1\n"
    )
    
    invalid_csv = d / "messages.csv"
    invalid_csv.write_text("id,text\n1,Hello\n")
    
    return d

def test_load_all(temp_dataset_dir):
    loader = CSVLoader(data_dir=str(temp_dataset_dir))
    cache = loader.load_all()
    # messages.csv (invalid) will be skipped because validation fails.
    # valid.csv (valid, and not named messages.csv so it skips schema enforcement anyway) will load.
    assert "valid.csv" in cache
    assert "messages.csv" not in cache
    assert len(cache) == 1

def test_load_valid_csv(temp_dataset_dir):
    loader = CSVLoader(data_dir=str(temp_dataset_dir))
    valid_path = temp_dataset_dir / "valid.csv"
    df = loader.load_csv(valid_path)
    
    assert df is not None
    assert len(df) == 2
    assert "valid.csv" in loader._cache
    
    # Check missing values handling
    assert df.loc[0, "message_text"] == ""
    assert df.loc[0, "forwarded_count"] == 0
    assert df.loc[1, "forwarded_count"] == 1

def test_load_invalid_csv(temp_dataset_dir):
    loader = CSVLoader(data_dir=str(temp_dataset_dir))
    invalid_path = temp_dataset_dir / "messages.csv"
    
    with pytest.raises(ValueError, match="Missing required columns"):
        loader.load_csv(invalid_path)

def test_caching(temp_dataset_dir):
    loader = CSVLoader(data_dir=str(temp_dataset_dir))
    valid_path = temp_dataset_dir / "valid.csv"
    
    df1 = loader.load_csv(valid_path)
    df2 = loader.get_cached_dataset("valid.csv")
    
    assert df1 is df2 # Same object reference due to cache

def test_clear_cache(temp_dataset_dir):
    loader = CSVLoader(data_dir=str(temp_dataset_dir))
    valid_path = temp_dataset_dir / "valid.csv"
    loader.load_csv(valid_path)
    
    assert "valid.csv" in loader._cache
    loader.clear_cache()
    assert len(loader._cache) == 0
