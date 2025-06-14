# Handles creating dash_app graph

import dash
from dash import html, Input, Output, State, no_update

import pandas as pd

from ..utils import get_data_type_label, format_status_message
from ..logger import logger


# Callback to update visualization controls
def register_callbacks(app):

    # Enable date range filter once results are loaded
    @app.callback(
        Output('date-range', 'disabled'),
        Input('results-container', 'children')
    )
    def enable_date_filter(_):
        return False

    @app.callback(
        [Output('dashboard-title', 'children'),
         Output('station-dropdown', 'options'),
         Output('station-dropdown', 'value'),
         Output('date-range', 'min_date_allowed'),
         Output('date-range', 'max_date_allowed'),
         Output('date-range', 'start_date'),
         Output('date-range', 'end_date')],
        Input('data-store', 'data')
    )
    def update_visualization_controls(data):
        logger.info("[DEBUG] update_visualization_controls - Visualization controls callback triggered!")
        # global global_df
        if not data:
            raise dash.exceptions.PreventUpdate
        logger.info(f"Data received: {len(data)} records")
        df = pd.DataFrame(data)
        # Standardize date column name
        date_col = 'DATE' if 'DATE' in df.columns else 'date'
        logger.info(f"Using date column: {date_col}")
        df[date_col] = pd.to_datetime(df[date_col])
        logger.info(f"DataFrame columns: {df.columns.tolist()}")
        # Get min/max dates from data
        min_date = df[date_col].min() # min_date grayed - why
        max_date = df[date_col].max() # min_date grayed - why
        logger.info(f"Date range from data: min_date={min_date}, max_date={max_date}")
        # Get city name from the data and Update station dropdown
        if 'NAME' in df.columns and not df['NAME'].empty:
            city_name = df['NAME'].iloc[0].split(',')[0]
            stations = df['NAME'].unique().tolist()
            logger.info(f"City name: {city_name}, Stations found: {stations}")
        else:
            city_name = "Selected Location"
            stations = []
            logger.warning("No 'NAME' column or empty in data; using default city and empty stations")
        # Update station dropdown
        stations = df['NAME'].unique().tolist()
        station_options = [{'label': s, 'value': s} for s in stations]
        logger.info(f"Station options prepared: {station_options}")

        # Update date range picker
        min_date = df[date_col].min()
        max_date = df[date_col].max()

        first_station = stations[0] if stations else None
        logger.info(f"Default station selected: {first_station}")

        logger.info(f"Updating visualization controls for city: {city_name} with stations: {stations}")

        return (
            f"🌦️ Historical {city_name} Weather Dashboard",
            station_options,
            first_station,
            min_date,
            max_date,
            min_date,
            max_date
        )

    # Callback to update charts based on user selections
    @app.callback(
        [Output('temp-trend', 'figure'),
         Output('precip-trend', 'figure')],
        [Input('station-dropdown', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('data-type', 'value')],
        State('data-store', 'data')
    )
    def update_charts(selected_station, start_date, end_date, data_type, data):
        logger.info("[DEBUG] update_charts called")
        if not data or not selected_station:
            logger.warning("No data received; preventing update")
            raise dash.exceptions.PreventUpdate
        try:
            logger.info(f"Data type: {data_type}")

            df = pd.DataFrame(data)
            logger.info(f"Data loaded into DataFrame with {len(df)} rows")

            # Standardize column names
            date_col = 'DATE' if 'DATE' in df.columns else 'date'
            df[date_col] = pd.to_datetime(df[date_col])
            # Filter by station
            filtered = df[df['NAME'] == selected_station].copy()
            logger.info(f"Filtered data by station '{selected_station}', rows: {len(filtered)}")

            # Filter by date range
            if start_date and end_date:
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                filtered = filtered[(filtered['DATE'] >= start_date) &
                                    (filtered['DATE'] <= end_date)]
                logger.info(f"Filtered data by date range, rows after filter: {len(filtered)}")
            # Convert numeric columns to float (this fixes the error)
            numeric_cols = ['TMIN', 'TAVG', 'TMAX', 'PRCP']
            for col in numeric_cols:
                if col in filtered.columns:
                    filtered[col] = pd.to_numeric(filtered[col], errors='coerce')
                    logger.info(f"Converted column {col} to numeric")
            data_type_label = get_data_type_label(data_type)
            logger.info(f"Data type label: {data_type_label}")

            temp_y_cols = [col for col in ['TMIN', 'TAVG', 'TMAX'] if col in filtered.columns]
            logger.info(f"Temperature columns used for plot: {temp_y_cols}")

            # Create  chart
            temp_fig = px.line(
                filtered,
                x='DATE',
                y=temp_y_cols,
                title=f"{data_type_label} Trend - {selected_station}",
                labels={'value': 'Temperature (°F)', 'variable': 'Metric'}
            )
            # Create precipitation chart
            precip_fig = px.bar(
                filtered,
                x='DATE',
                y='PRCP',
                # color='PRCP', -> it shows vertical metricts
                title=f"Precipitation - {selected_station}",
                labels={'PRCP': 'Precipitation (hundredths of inches)'},
                color_discrete_sequence=['#003366'] # #9467bd #1f77b4
            )
            precip_fig.update_traces(
                marker_color='#001f3f',
                marker_line_color='blue',  # Add dark border
                marker_line_width=0.3,
                opacity=1  # Full opacity
            )

            logger.info(f"Updated charts for station '{selected_station}' between {start_date} and {end_date}")
            return temp_fig, precip_fig
        except Exception as e:
            logger.error(f"Error in update_charts: {str(e)}", exc_info=True)
            return no_update, no_update

