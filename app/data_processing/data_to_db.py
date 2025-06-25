import sqlite3
import pandas as pd
import os

from app.data_processing.data_cleaner import list_csv_files, write_file_list, clean_single_csv
from app.utils import PROJECT_ROOT, RAW_DATA_DIR, PROCESSED_DATA_DIR, find_city_in_name, get_latest_csv_filename, \
    get_latest_csv_full_path
from app.logger import logger

input_dir = RAW_DATA_DIR
output_dir = PROCESSED_DATA_DIR
logger.info(f"Input folder: {input_dir}")

# DB location
DB_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../db")
DB_NAME = "noaa_weather.db"
DB_PATH = os.path.join(DB_DIR, DB_NAME)
TABLE_NAME = "weather_data"

# Ensure the DB directory exists
os.makedirs(DB_DIR, exist_ok=True)
logger.info(f"Database directory ensured: {DB_DIR}")

# Column Definitions
base_cols = ['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'ELEVATION', 'NAME']
optional_cols = ['TAVG', 'TMIN', 'TMAX', 'WT16', 'SNOW', 'ACMH', 'WSFG',
                 'PRCP', 'RHAV', 'TSUN', 'WT08', 'WT01', 'WT02']
keep_cols = base_cols + optional_cols

# Get all cleaned CSV files if multiple
# csv_files = list_csv_files(PROCESSED_DATA_DIR) # get list of cleaned files
# logger.info(csv_files)

def clean_latest_csv_file(filename) -> str:
    """Get latest downloaded CSV filename, clean it, and return the filename."""
    full_path = os.path.join(RAW_DATA_DIR, filename)
    clean_single_csv(full_path)
    return filename

def get_cleaned_csv_files(filename: str) -> list[str]:
    """Return full path to cleaned file(s) based on filename."""
    cleaned_path = os.path.join(PROCESSED_DATA_DIR, filename)
    return [cleaned_path] if os.path.exists(cleaned_path) else []


schema = """
CREATE TABLE IF NOT EXISTS weather_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    STATION TEXT, DATE TEXT, LATITUDE REAL, LONGITUDE REAL, ELEVATION REAL,
    NAME TEXT, CITY_NAME TEXT, TAVG REAL, TMIN REAL, TMAX REAL, WT16 REAL, 
    SNOW REAL, ACMH REAL, WSFG REAL, PRCP REAL, RHAV REAL, TSUN REAL,
    WT08 REAL, WT01 REAL, WT02 REAL
)
"""

# Connect to SQLite DB and create table
def import_csv_to_db(csv_path: str = None) -> tuple[bool, str]:
    """
    Import data from given cleaned CSV file path into SQLite DB.
    Returns:
        (success: bool, message: str)
    """
    try:
        # Ensure DB directory exists
        os.makedirs(DB_DIR, exist_ok=True)

        # get latest raw csv, clean and save
        # if csv_path is None:
        #     latest = get_latest_csv_filename()
        #     latest_csv_filename = clean_latest_csv_file(latest)
        #     csv_files = get_cleaned_csv_files(latest_csv_filename)
        #     logger.info(csv_files)
        # else:
        #     csv_files = [csv_path]
        # logger.info(f"CSV files to import: {csv_files}")

        csv_files = [csv_path] #omportant

        if not csv_files:
            msg = "No CSV files to process."
            logger.info(msg)
            return False, msg

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(schema)
            logger.info(f"Ensured table {TABLE_NAME} exists.")

            # Insert data from each CSV
            for csv_file in csv_files:
                logger.info(f"Importing file: {csv_file}")
                df = pd.read_csv(csv_file)

                for col in keep_cols:
                    if col not in df.columns:
                        df[col] = None

                df = df[keep_cols]
                rows = df.itertuples(index=False, name=None)

                placeholders = ', '.join('?' for _ in keep_cols)
                insert_stmt = f"INSERT INTO {TABLE_NAME} ({', '.join(keep_cols)}) VALUES ({placeholders})"

                cursor.executemany(insert_stmt, rows)
                logger.info(f"Inserted {df.shape[0]} rows from {os.path.basename(csv_file)}")

            conn.commit()
            logger.info(f"All data loaded into '{TABLE_NAME}' successfully.")

        return True, f"Successfully imported {df.shape[0]} rows."
    except Exception as e:
        logger.error(f"Failed to import CSV to DB: {e}")
        return False, f"Import failed: {e}"
