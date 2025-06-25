import sqlite3

from app.utils import find_city_in_name, US_CITY_NAMES, SPECIAL_CITY_EXCEPTIONS
from app.logger import logger


DB_PATH = "../db/noaa_weather.db"
TABLE_NAME = "weather_data"

stations_list = []
stations_str_list = []

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()

    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")

    # Get total rows in table
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    row_count = cursor.fetchone()[0]
    logger.info(f"Total rows in table '{TABLE_NAME}': {row_count}")

    # Show first 5 rows from the weather_data table
    cursor.execute("SELECT * FROM weather_data LIMIT 5;")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    # Extract column names
    cursor.execute(f"SELECT * FROM {TABLE_NAME} LIMIT 1")
    column_names = [desc[0] for desc in cursor.description]
    logger.info(f"Columns in '{TABLE_NAME}': {column_names}")

    # stations list with data
    query = """
    SELECT DISTINCT STATION, LATITUDE, LONGITUDE, ELEVATION, NAME, TAVG, TMIN, TMAX
    FROM weather_data
    """
    cursor.execute(query)
    results = cursor.fetchall()
    for row in results:
        stations_list.append(row)
    # print(f"stations_list: {stations_list}" )

    #
    query = """
        SELECT DISTINCT STATION, NAME
        FROM weather_data
        """
    cursor.execute(query)
    results = cursor.fetchall()
    for row in results:
        stations_str_list.append(row)

    stations_str_list = [" ".join(str(item) for item in row) for row in stations_str_list]
    # logger.info(f"stations_str_list {stations_str_list}")


def extract_city_state(name):
    parts = name.split(',')
    if len(parts) > 1:
        return parts[1].strip()
    return None

def extract_city(name):
    if not name:
        return None
    # Split on comma, take first part
    city_part = name.split(',')[0].strip()
    return city_part

def extract_city_advanced(name):
    if not name:
        return None
    first_part = name.split(',')[0].strip()
    words = first_part.split()
    stop_words = {"UNIVERSI", "UNIVERSITY", "AIRPORT", "INTERNATIONAL", "STATION", "FIELD", "MIDWAY", "PARK", "RIVERSIDE", "STATE"}

    city_words = []
    for w in words:
        if w.upper() in stop_words:
            break
        city_words.append(w)
    return " ".join(city_words)

def list_station_city_matches():
    """Match station names to cities and log the results."""
    match_count = 0
    match_cities = []

    for name in stations_str_list:
        city = find_city_in_name(name, US_CITY_NAMES, exceptions=SPECIAL_CITY_EXCEPTIONS)
        logger.info(f"Station Name: {name} -> Matched City: {city}")
        if city:
            match_count += 1

    matched = sum(1 for _, city in match_cities if city)
    logger.info(f"Matched {matched} out of {len(stations_str_list)} stations.")

    return match_cities

station_city_pairs = list_station_city_matches()