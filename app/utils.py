import os
import pandas as pd
from dash import html
import plotly.graph_objects as go
import copy
import geonamescache
from collections import defaultdict
import re

from .logger import logger

IS_RENDER = os.getenv("RENDER", "false").lower() == "true"

# IS_RENDER = bool(os.getenv("RENDER_SERVICE_ID"))
logger.info(f"[ENV DETECTION] IS_RENDER={IS_RENDER}")
logger.info(f"RENDER_SERVICE_ID: {os.getenv('RENDER_SERVICE_ID')}")

# Path Constants
if IS_RENDER:
    BASE_DATA_DIR = "/tmp/data"
    DB_DIR = "/tmp/db"
else:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    BASE_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
    DB_DIR = os.path.join(PROJECT_ROOT, "db")

RAW_DATA_DIR = os.path.join(BASE_DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DATA_DIR, "processed")
LOGS_DIR = os.path.join(BASE_DATA_DIR if IS_RENDER else PROJECT_ROOT, "logs")

DB_NAME = "noaa_weather.db"
DB_PATH = os.path.join(DB_DIR, DB_NAME)
TABLE_NAME = "weather_data"

# Create folders if they don't exist
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

logger.info(f"[PATHS] RAW_DATA_DIR: {RAW_DATA_DIR}")
logger.info(f"[PATHS] PROCESSED_DATA_DIR: {PROCESSED_DATA_DIR}")
logger.info(f"[PATHS] LOGS_DIR: {LOGS_DIR}")
logger.info(f"[PATHS] DB_PATH: {DB_PATH}")

# Constants
DATA_TYPES = [
    {'label': 'Average temperature', 'value': 'TAVG'},
    {'label': 'Rain', 'value': 'WT16'},
    {'label': 'Snowfall', 'value': 'Snow'},
    {'label': 'Fog, ice fog, or freezing fog', 'value': 'WT01'},
    {'label': 'Average cloudiness (midnight-midnight)', 'value': 'ACMH'},
    {'label': 'Average daily wind speed', 'value': 'WSFG'},
    {'label': 'Precipitation', 'value': 'PRCP'},
    {'label': 'Average relative humidity', 'value': 'RHAV'},
    {'label': 'Daily total sunshine', 'value': 'TSUN'},
    {'label': 'Smoke or haze', 'value': 'WT08'},
]


# Visualization parameters for each data type
VIS_CONFIG = {
    # Temperature
    'TAVG': {
        'chart_type': 'line',
        'y_cols': ['TMIN', 'TAVG', 'TMAX'],
        'labels': {'value': 'Temperature (°F)', 'variable': 'Metric'},
        'colors': ['#1E90FF', '#FF6347', '#FF0000']  # Blue, Red, Dark Red
    },
    # Precipitation
    'PRCP': {
        'chart_type': 'bar',
        'y_cols': ['PRCP'],
        'labels': {'PRCP': 'Precipitation (inches)'},
        'colors': ['#003366'] # Navy
    },
    # Rain occurrence (weather type 16)
    'WT16': {
        'chart_type': 'line',
        'y_cols': ['WT16'],
        'labels': {'WT16': 'Rain Occurrence'},
        'colors': ['#1E90FF']
    },
    # Snowfall
    'Snow': {
        'chart_type': 'bar',
        'y_cols': ['SNOW'],
        'labels': {'SNOW': 'Snowfall (inches)'},
        'colors': ['#4682B4']
    },
    # Average cloudiness
    'ACMH': {
        'chart_type': 'line',
        'y_cols': ['ACMH'],
        'labels': {'ACMH': 'Cloudiness (%)'},
        'colors': ['#A9A9A9'] # Dark gray
    },
    # Average daily wind speed
    'WSFG': {
        'chart_type': 'line',
        'y_cols': ['WSFG'],
        'labels': {'WSFG': 'Wind Speed (mph)'},
        'colors': ['#4682B4'] # Steel blue
    },
    # Average relative humidity
    'RHAV': {
        'chart_type': 'line',
        'y_cols': ['RHAV'],
        'labels': {'RHAV': 'Relative Humidity (%)'},
        'colors': ['#2E8B57']  # Sea green
    },
    # Daily total sunshine
    'TSUN': {
        'chart_type': 'line',
        'y_cols': ['TSUN'],
        'labels': {'TSUN': 'Sunshine Duration (minutes)'},
        'colors': ['#FFD700']  # Gold
    },
    # Smoke or haze
    'WT08': {
        'chart_type': 'bar',
        'y_cols': ['WT08'],
        'labels': {'WT08': 'Smoke or Haze Occurrence'},
        'colors': ['#505050'] # gray
    },
    # Fog
    'WT01': {
        'chart_type': 'scatter',
        'y_cols': ['WT01', 'WT02'],
        'labels': {'WT01': 'Fog Occurrence', 'WT02': 'Heavy Fog Occurrence'},
        'colors': ['#D3D3D3'] # Light gray
    },
    # Default configuration
    'default': {
        'type': 'line',
        'y_cols': None,
        'labels': None,
        'colors': ['#000000'],
        'required_cols': {'DATE', 'NAME'}
    }
}

label_map = {
        'TAVG': 'Average Temperature',
        'TMAX': 'Maximum Temperature',
        'TMIN': 'Minimum Temperature',
        'PRCP': 'Precipitation',
        'SNOW': 'Snowfall',
        'TSUN': 'Sunshine Duration',
        'ACMH': 'Average Cloud Height',
        'WSFG': 'Wind Gust Speed',
        'RHAV': 'Relative Humidity',
        'WT01': 'Fog Occurrence',
        'WT08': 'Smoke or Haze Occurrence',
        'WT16': 'Rain Occurrence',
    }

chart_options = [
    {'label': 'Yearly Max Temperature Trends (Line chart)', 'value': 'Max Temp Trends'},
    {'label': 'Avg Temperature Over Years (Boxplot)', 'value': 'Temp Boxplot'},
    {'label': 'Snowfall Contribution by Station (Pie)', 'value': 'Snowfall Pie'},
    {'label': 'Total Snowfall by Station (Bar)', 'value': 'Snowfall Bar'},
    {'label': 'Snowfall Max Snowfalls Trends (Line chart)', 'value': 'Snowfall Trends'},
    {'label': 'Event Frequencies Fog, Smoke, Rain, Wind (Bar)', 'value': 'Weather Events'},
    {'label': 'Yearly Distributions Temp, Precip, Snow (Boxplot)', 'value': 'Yearly Distributions'},
    {'label': 'Correlation Heatmap', 'value': 'Correlation Heatmap'},
]

def get_vis_config(data_type):
    """Get visualization config for given data type with fallback to default"""
    config = copy.deepcopy(VIS_CONFIG.get(data_type, VIS_CONFIG['default']))

    # For default config, set dynamic values
    if data_type not in VIS_CONFIG:
        config['y_cols'] = [data_type]
        config['labels'] = {data_type: get_data_type_label(data_type)}
        config.setdefault('required_cols', set()).add(data_type)

    return config

def create_empty_figure(message):
    """Create empty figure with message"""
    fig = go.Figure()
    fig.update_layout(
        title=message,
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': message,
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False,
            'font': {'size': 16}
        }]
    )
    return fig

# Helper Functions
def get_data_type_label(code):
    """
    Convert NOAA code to human-readable label.
    Returns a string like "Unknown (XYZ)" if code is not found in DATA_TYPES.
    """
    return next((item['label'] for item in DATA_TYPES if item['value'] == code), f"Unknown ({code})")

def get_label_from_value(value):
    """
    Returns label for the given data type from DATA_TYPES list
    Returns the original value if it is not found in DATA_TYPES.
    """
    for item in DATA_TYPES:
        if item['value'] == value:
            return item['label']
    return value

def is_valid_column(df: pd.DataFrame, col: str) -> bool:
    """Check if col exists in df and has any non-NaN values."""
    return col in df.columns and not df[col].dropna().empty

def validate_dates(start_date, end_date):
    """Ensure dates are in correct format"""
    try:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        return start <= end  # Return False if end date is before start
    except:
        return False

def validate_inputs(city_name, data_type):
    """Validate user inputs before scraping"""
    if not city_name or not isinstance(city_name, str):
        return False
    if data_type not in [item['value'] for item in DATA_TYPES]:
        return False
    return True

def format_status_message(msg, msg_type="info"):
    """Style messages with consistent formatting"""
    styles = {
        "error": {'color': '#dc3545', 'icon': '❌', 'background': '#f8d7da'},
        "warning": {'color': '#ffc107', 'icon': '⚠️', 'background': '#fff3cd'},
        "info": {'color': '#17a2b8', 'icon': 'ℹ️', 'background': '#d1ecf1'},
        "success": {'color': '#28a745', 'icon': '✅', 'background': '#d4edda'}
    }

    return html.Div(
        [
            html.Span(styles[msg_type]['icon']),
            html.Span(msg, style={'margin-left': '8px'})
        ],
        style={
            'color': styles[msg_type]['color'],
            'backgroundColor': styles[msg_type]['background'],
            'padding': '12px',
            'borderRadius': '4px',
            'margin': '10px 0',
            'borderLeft': f"5px solid {styles[msg_type]['color']}",
            'display': 'flex',
            'alignItems': 'center'
        }
    )

def get_latest_csv_filename() -> str:
    latest_file_path = os.path.join(PROJECT_ROOT, "data", "latest_download.txt")
    if os.path.exists(latest_file_path):
        with open(latest_file_path, "r") as f:
            return f.read().strip()
    else:
        logger.info(f"[FILE] latest_download.txt not found.")
        raise FileNotFoundError("latest_download.txt not found.")

def get_latest_csv_full_path() -> str:
    filename = get_latest_csv_filename()
    full_path = os.path.join(RAW_DATA_DIR, filename)
    logger.info(f"[FILE] Full path to latest CSV: {full_path}")
    return full_path

# special name-to-city mapping
SPECIAL_CITY_EXCEPTIONS = {
    "JFK INTERNATIONAL AIRPORT": "NEW YORK",
    "NEWARK LIBERTY INTERNATIONAL AIRPORT": "NEWARK",
    "NY CITY CENTRAL PARK": "NEW YORK",
    "LOWER ST. ANTHONY FALLS, MN US": "MINNEAPOLIS",
    "BALTIMORE HAMILTON, MD US": "BALTIMORE"
}
REVERSED_CITY_PREFS = defaultdict(list)
for station, city in SPECIAL_CITY_EXCEPTIONS.items():
    REVERSED_CITY_PREFS[city.upper()].append(station.upper())

_gc = geonamescache.GeonamesCache()
_us_cities = _gc.get_cities()
US_CITY_NAMES = sorted(
    {info['name'].upper() for info in _us_cities.values() if info['countrycode'] == 'US'},
    key=len,
    reverse=True
)

def find_city_in_name(station_name, city_names=US_CITY_NAMES, exceptions=SPECIAL_CITY_EXCEPTIONS):
    """
    Extract a city name from the station_name string.
    """
    name_upper = station_name.upper()
    sorted_city_names = sorted(city_names, key=len, reverse=True)

    if exceptions:
        for exc_key, exc_val in exceptions.items():
            if exc_key in name_upper:
                return exc_val

    tokens = re.findall(r'\b[\w\s]+\b', name_upper)
    joined_station_name = " ".join(tokens)

    for city in sorted_city_names:
        pattern = rf'\b{re.escape(city)}\b'
        if re.search(pattern, joined_station_name):
            return city

    return None
