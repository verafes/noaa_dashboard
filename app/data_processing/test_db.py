import os
import sqlite3
from datetime import datetime

from app.utils import find_city_in_name, US_CITY_NAMES, SPECIAL_CITY_EXCEPTIONS, DB_PATH, TABLE_NAME
from app.logger import logger
from dotenv import load_dotenv
load_dotenv()

MIN_START_DATE = os.getenv('MIN_START_DATE')
min_start_date = datetime.strptime(MIN_START_DATE, "%Y-%m-%d").date().isoformat()

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

    cursor.execute(f"SELECT DISTINCT NAME FROM {TABLE_NAME}")
    stations = [row[0] for row in cursor.fetchall()]
    logger.info(f"Total unique stations: {len(stations)}")
    logger.info(f"Sample stations: {stations[:10]}")

    cursor.execute(f"SELECT MIN(DATE), MAX(DATE) FROM {TABLE_NAME}")
    min_date, max_date = cursor.fetchone()
    logger.info(f"Date range in {TABLE_NAME}: {min_date} to {max_date}")

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

    cursor.execute(f"""
            SELECT STATION, DATE, TAVG, TMIN, TMAX
            FROM {TABLE_NAME}
            WHERE TAVG < -500 OR TAVG > 500
               OR TMIN < -500 OR TMIN > 500
               OR TMAX < -500 OR TMAX > 512
            ORDER BY STATION, DATE
        """)

    suspect_rows = cursor.fetchall()

    if suspect_rows:
        print(f"Found {len(suspect_rows)} rows with unreal TAVG, TMIN, or TMAX values:")
        for station, date, tavg, tmin, tmax in suspect_rows:
            print(f"Station: {station}, Date: {date}, TAVG: {tavg}, TMIN: {tmin}, TMAX: {tmax}")

        delete_query = f"""
            DELETE FROM {TABLE_NAME}
            WHERE (TAVG IS NOT NULL AND (TAVG < -500 OR TAVG > 500))
               OR (TMIN IS NOT NULL AND (TMIN < -500 OR TMIN > 500))
               OR (TMAX IS NOT NULL AND (TMAX < -500 OR TMAX > 512))
            """
        cursor.execute(delete_query)
        conn.commit()
        print(f"Deleted {cursor.rowcount} rows.")

    else:
        print("No unreal temperature values found.")

    # check how many rows remain
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    total_after = cursor.fetchone()[0]
    print(f"Remaining Total rows after cleanup (unreal temp values): {total_after}")

    # First, check how many rows exist before MIN_START_DATE
    cursor.execute("""
        SELECT COUNT(*) FROM weather_data
        WHERE DATE < ?
    """, (min_start_date,))
    count = cursor.fetchone()[0]

    if count > 0:
        print(f"Found {count} rows with DATE before {MIN_START_DATE}. Deleting them...")
        cursor.execute("""
            DELETE FROM weather_data
            WHERE DATE < ?
        """, (min_start_date,))
        conn.commit()
        print("Old rows removed.")
    else:
        print("No rows before {MIN_START_DATE} found. No action needed.")

    query = f"""
        SELECT
            STATION,
            strftime('%Y', DATE) AS year,
            SUM(PRCP) AS total_precipitation
        FROM weather_data
        WHERE PRCP IS NOT NULL
        GROUP BY STATION, year
        HAVING total_precipitation > 5000
        ORDER BY total_precipitation DESC;
    """
    max_prcp_rows = cursor.fetchall()
    if results:
        print(f"Found {len(max_prcp_rows)} station-year(s) with yearly precipitation > 5000 mm")
        for station, year, total_prcp in max_prcp_rows:
            print(f"Station: {station}, Year: {year}, Total PRCP: {total_prcp} mm")
    else:
        print("No station-year records with yearly precipitation > 5000 mm found.")

    cursor.execute(query)
    conn.commit()

    query = f"""
           SELECT STATION, DATE, TAVG, TMIN, TMAX
           FROM {TABLE_NAME}
           WHERE TAVG < -100 OR TMIN < -100 OR TMAX < -100
           ORDER BY DATE, STATION;
       """
    cursor.execute(query)
    results = cursor.fetchall()

    print(f"Found {len(results)} records with temperature below -100:")
    # for station, date, tavg, tmin, tmax in results:
    #     logger.info(f"Station: {station}, Date: {date}, TAVG: {tavg}, TMIN: {tmin}, TMAX: {tmax}")

    # 1. Count total non-null TSUN values
    cursor.execute(f"""
        SELECT COUNT(*) FROM {TABLE_NAME}
        WHERE TSUN IS NOT NULL;
    """)
    non_null_count = cursor.fetchone()[0]
    print(f"✅ Non-null TSUN values: {non_null_count}")

    # 2. Count values where TSUN > 0
    cursor.execute(f"""
        SELECT COUNT(*) FROM {TABLE_NAME}
        WHERE TSUN > 0;
    """)
    greater_than_zero_count = cursor.fetchone()[0]
    print(f"☀️ TSUN > 0 values: {greater_than_zero_count}")

    # 3. Number of stations with TSUN > 0
    cursor.execute(f"""
        SELECT NAME, COUNT(*) as records
        FROM {TABLE_NAME}
        WHERE TSUN > 0
        GROUP BY NAME
        ORDER BY records DESC
        LIMIT 20;
    """)
    results = cursor.fetchall()
    print("\n📊 Top stations with TSUN > 0:")
    for name, count in results:
        print(f"- {name}: {count} records")

    # check how many rows remain
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    total_after = cursor.fetchone()[0]
    print(f"Remaining Total rows after all cleanups: {total_after}")

    for col in ['WT01', 'WT08', 'WT16']:
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE {col} IS NOT NULL")
        count = cursor.fetchone()[0]
        logger.info(f"Non-null count for {col}: {count}")

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

# station_city_pairs = list_station_city_matches()