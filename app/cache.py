import pandas as pd
import os
from datetime import datetime, timedelta
import hashlib

CACHE_DIR = "data/cache/"
CACHE_EXPIRE_HOURS = 6  # Re-scrape if cache older than this


def get_cache_key(city_name: str, data_type: str) -> str:
    """Generate a unique filename based on inputs."""
    key_str = f"{city_name}_{data_type}".lower().replace(" ", "_")
    return hashlib.md5(key_str.encode()).hexdigest() + ".csv"


def cache_exists(city_name: str, data_type: str) -> bool:
    """Check if valid cache exists."""
    cache_file = os.path.join(CACHE_DIR, get_cache_key(city_name, data_type))
    if not os.path.exists(cache_file):
        return False

    # Check cache age
    mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
    return (datetime.now() - mod_time) < timedelta(hours=CACHE_EXPIRE_HOURS)


def load_from_cache(city_name: str, data_type: str) -> pd.DataFrame:
    """Load cached CSV as DataFrame."""
    cache_file = os.path.join(CACHE_DIR, get_cache_key(city_name, data_type))
    return pd.read_csv(cache_file, low_memory=False)


def save_to_cache(df: pd.DataFrame, city_name: str, data_type: str):
    """Store DataFrame as cached CSV."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, get_cache_key(city_name, data_type))
    df.to_csv(cache_file, index=False)
