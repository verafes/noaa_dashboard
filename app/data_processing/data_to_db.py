import sqlite3
import pandas as pd
import os

from app.data_processing.data_cleaner import list_csv_files, write_file_list
from app.utils import PROJECT_ROOT, PROCESSED_DATA_DIR, find_city_in_name
from app.logger import logger

input_folder = PROCESSED_DATA_DIR
logger.info(f"Input folder: {input_folder}")

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

# Ensure DB directory exists ===
os.makedirs(DB_DIR, exist_ok=True)

# Get all cleaned CSV files
csv_files = list_csv_files()
logger.info(csv_files)
write_file_list(csv_files, os.path.join(DB_DIR, "csv_file_list.txt"))
logger.info("csv_file_list.txt")

if not csv_files:
    logger("No CSV files to process.")
    exit(0)

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
with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()

    cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    logger.info(f"Dropped table {TABLE_NAME}")
    cursor.execute(schema)
    logger.info(f"Created table {TABLE_NAME}")


    conn.commit()
    logger.info(f"Table '{TABLE_NAME}' created.")

    # Insert data from each CSV
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)

            # Add missing optional columns as None
            for col in keep_cols:
                if col not in df.columns:
                    df[col] = None

            df = df[keep_cols]  # Ensure column order

            # Convert DataFrame to list of tuples
            rows = df.itertuples(index=False, name=None)

            # Prepare insert statement
            placeholders = ', '.join('?' for _ in keep_cols)
            insert_stmt = f"INSERT INTO {TABLE_NAME} ({', '.join(keep_cols)}) VALUES ({placeholders})"

            cursor.executemany(insert_stmt, rows)
            logger.info(f"Inserted {df.shape[0]} rows from {os.path.basename(csv_file)}")
        except Exception as e:
            logger.info(f"Error processing {csv_file}: {e}")

    conn.commit()
    logger.info(f"All data loaded into '{TABLE_NAME}' successfully.")

    logger.info("Populating CITY_NAME column in the DB...")

