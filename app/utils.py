import pandas as pd
from dash import html

# Constants
DATA_TYPES = [
    {'label': 'Average temperature', 'value': 'TAVG'},
    {'label': 'Average cloudiness (midnight-midnight)', 'value': 'ACMH'},
    {'label': 'Average cloudiness (sunrise-sunset)', 'value': 'ACSH'},
    {'label': 'Average Dew Point Temperature', 'value': 'ADPT'},
    {'label': 'Average Sea Level Pressure', 'value': 'ASLP'},
    {'label': 'Average daily wind direction', 'value': 'WDFG'},
    {'label': 'Average daily wind speed', 'value': 'WSFG'},
    {'label': 'Precipitation', 'value': 'PRCP'},
    {'label': 'Average relative humidity', 'value': 'RHAV'},
    {'label': 'Daily total sunshine', 'value': 'TSUN'},
    {'label': 'Fog, ice fog, or freezing fog', 'value': 'WT01'},
    {'label': 'Ground fog', 'value': 'WT02'},
    {'label': 'Drizzle', 'value': 'WT03'},
    {'label': 'Mist', 'value': 'WT04'},
    {'label': 'Smoke or haze', 'value': 'WT05'},
    {'label': 'Rain', 'value': 'WT06'},
    {'label': 'Rain or snow shower', 'value': 'WT07'},
    {'label': 'Snowfall', 'value': 'WT08'},
    {'label': 'Snow depth', 'value': 'WT09'},
    {'label': 'Thickness of ice on water', 'value': 'WT17'},
    {'label': 'Thunder', 'value': 'TS'}
]

# Helper Functions
def get_data_type_label(code):
    """Convert NOAA code to human-readable label"""
    return next((item['label'] for item in DATA_TYPES if item['value'] == code), f"Unknown ({code})")

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

def get_label_from_value(value):
    for item in DATA_TYPES:
        if item['value'] == value:
            return item['label']
    return value



def format_status_message(msg, msg_type="info"):
    """Style messages with consistent formatting"""
    styles = {
        "error": {'color': '#dc3545', 'icon': '❌', 'background': '#f8d7da'},
        "warning": {'color': '#ffc107', 'icon': '⚠️', 'background': '#fff3cd'},
        "info": {'color': '#17a2b8', 'icon': 'ℹ️', 'background': '#d1ecf1'},
        "success": {'color': '#28a745', 'icon': '✓', 'background': '#d4edda'}
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
