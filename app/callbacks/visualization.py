# Handles creating dash_app graphs (data before analysis)
import os
import dash
from dash import Input, Output, State

import pandas as pd
import numpy as np
import plotly.express as px

from ..utils import get_data_type_label, create_empty_figure, get_vis_config, is_valid_column, set_min_start_date
from ..logger import logger
from dotenv import load_dotenv
load_dotenv()

MIN_START_DATE = os.getenv('MIN_START_DATE')


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
        min_date = df[date_col].min()
        max_date = df[date_col].max()
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
        [Output('weather-graph', 'figure'),
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

            # set start_date to MIN_START_DATE
            start_date = max(pd.to_datetime(start_date), pd.to_datetime(MIN_START_DATE))
            logger.info(f"Start date is set to minimal {start_date} for visualization")

            # Filter by date range
            if start_date and end_date:
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                filtered = filtered[(filtered['DATE'] >= start_date) &
                                    (filtered['DATE'] <= end_date)]
                logger.info(f"Filtered data by date range, rows after filter: {len(filtered)}")

            # Convert numeric columns to float (this fixes the error)
            numeric_cols = ['TMIN', 'TAVG', 'TMAX', 'PRCP', 'NAME', 'SNOW', 'TSUN',
                            'ACMH', 'WSFG', 'RHAV', 'WT01', 'WT02', 'WT08', 'WT16']
            for col in numeric_cols:
                if col in filtered.columns:
                    filtered[col] = pd.to_numeric(filtered[col], errors='coerce')
                    logger.info(f"Converted column {col} to numeric")

            # Create MAIN WEATHER GRAPH based on data_type
            config = get_vis_config(data_type)
            data_type_label = get_data_type_label(data_type)
            logger.info(f"Data type label: {data_type_label}")

            y_cols = config.get('y_cols', [])
            valid_y_cols = [col for col in y_cols if is_valid_column(filtered, col)]
            if not valid_y_cols:
                msg = f"No valid data found for {get_data_type_label(data_type)}"
                logger.warning(msg)
                return create_empty_figure(msg), create_empty_figure(msg)

            # y_col = config['y_cols'][0]
            y_col = valid_y_cols[0]

            if data_type in ['TMAX', 'TMIN', 'TAVG']:  # Temperature
                temp_y_cols = [col for col in ['TMIN', 'TAVG', 'TMAX'] if col in filtered.columns]
                logger.info(f"Temperature columns used for plot: {temp_y_cols}")
                weather_fig = px.line(
                    filtered,
                    x='DATE',
                    y=temp_y_cols, # weather data_type
                    title=f"{data_type_label} Trend - {selected_station}",
                    labels={'value': 'Temperature (°F)', 'variable': 'Metric'},
                    color_discrete_sequence = config['colors'],
                )
                weather_fig.for_each_trace(
                    lambda trace: trace.update(line=dict(width=1), opacity=0.7),
                )
                weather_fig.update_layout(
                    yaxis=dict(
                        title=dict(
                            text='Temperature (°F)',
                            standoff=20
                        )
                    ),
                    legend=dict(itemsizing='constant')
                )

            elif data_type == 'WT16':  # Rain occurrence
                filtered['Rain'] = filtered['WT16'].apply(lambda x: 1 if x > 0 else 0)
                weather_fig = px.bar(
                    filtered[filtered['Rain'] > 0],
                    x=date_col,
                    y='Rain',
                    title=f"Rain Days - {selected_station}",
                    labels={'Rain': 'Rain occurred'},
                    color_discrete_sequence=config['colors']
                )
                weather_fig.update_traces(
                    marker=dict(
                        color='#1E90FF',
                        line=dict(width=0),
                        opacity=1),
                    selector=dict(type='bar')
                )
                weather_fig.update_yaxes(range=[0, 1.1], showticklabels=False)

            elif data_type == 'Snow':  # Snow occurrence
                filtered['Snow'] = filtered['SNOW'].apply(lambda x: 1 if x > 0 else 0)
                weather_fig = px.bar(
                    filtered[filtered['Snow'] > 0],
                    x=date_col,
                    y='Snow',
                    title=f"Snow Days - {selected_station}",
                    labels={'Snow': 'Snowfall occurred'},
                )
                weather_fig.update_traces(
                    marker=dict(
                        color='#4682B4',
                        line=dict(width=0),
                        opacity=1
                    ),
                    selector=dict(type='bar')
                )
                weather_fig.update_yaxes(range=[0, 1.1], showticklabels=False)
            elif data_type == 'WT08':  # Smoke or haze
                filtered['Smoke'] = filtered['WT08'].apply(lambda x: 1 if x > 0 else 0)
                weather_fig = px.bar(
                    filtered[filtered['Smoke'] > 0],
                    x=date_col,
                    y='Smoke',
                    title=f"Smoke or Haze Days - {selected_station}",
                    labels={'Smoke': 'Smoke or haze occurred'},
                )
                weather_fig.update_traces(
                    marker=dict(
                        color='#505050',
                        opacity=1
                    ),
                    selector=dict(type='bar')
                )
                weather_fig.update_yaxes(range=[0, 1.1], showticklabels=False)

            else:  # Default for other data types
                if config['chart_type'] == 'line':
                    weather_fig = px.line(
                        filtered,
                        x='DATE',
                        y=y_col,
                        title=f"{get_data_type_label(data_type)} Over Time",
                        labels=config['labels'],
                        color_discrete_sequence=config['colors'],
                    )
                elif config['chart_type'] == 'bar':
                    weather_fig = px.bar(
                        filtered,
                        x='DATE',
                        y=config['y_cols'][0],
                        title=f"{get_data_type_label(data_type)} Over Time",
                        labels=config['labels'],
                        color_discrete_sequence=config['colors']
                    )
                    weather_fig.update_traces(
                        marker=dict(
                            color=config['colors'],
                            line=dict(width=0),
                            opacity=1),
                        selector=dict(type='bar')
                    )
                elif config['chart_type'] == 'scatter':
                    cols = [c for c in config['y_cols'] if c in filtered.columns]
                    logger.info(f"Columns considered for event: {cols}")

                    event_data = filtered[filtered[cols].gt(0).any(axis=1)]
                    logger.info(f"Event rows found: {len(event_data)}")
                    logger.info(event_data[['DATE'] + cols].head())

                    event_data['fog_event'] = 1 + 0.2 * np.random.randn(len(event_data))
                    config['labels']['fog_event'] = 'Fog Occurrence'

                    weather_fig = px.scatter(
                        event_data,
                        x='DATE',
                        y="fog_event",
                        title=f"{get_data_type_label(data_type)} Occurrence Over Time",
                        labels=config['labels'],
                        color_discrete_sequence=config['colors']
                    )
                    weather_fig.update_traces(
                        marker=dict(
                            size=8,
                            color=config['colors'][0],
                            line=dict(width=1.5, color='light blue'),
                            symbol='circle',
                            opacity=0.7
                        ),
                        showlegend=False
                    )
                    weather_fig.update_yaxes(range=[0, 2], showticklabels=False)
                    weather_fig.update_layout(
                        xaxis_title="Date",
                        hovermode = 'x unified',
                    )
                elif config['chart_type'] == 'binary':
                    event_data = filtered[filtered[config['y_cols'][0]] > 0]
                    if not event_data.empty:
                        weather_fig = px.scatter(
                            event_data,
                            x='DATE',
                            y=config['y_cols'][0],
                            title=f"{get_data_type_label(data_type)} Occurrences",
                            labels=config['labels'],
                            color_discrete_sequence=config['colors']
                        )
                    else:
                        weather_fig = px.scatter(title=f"No {get_data_type_label(data_type)} Events")
                        weather_fig.update_layout(
                            annotations=[dict(
                                text=f"No {get_data_type_label(data_type)} events in selected period",
                                showarrow=False
                            )]
                        )

            if 'PRCP' in filtered.columns:
                # PRCP = Precipitation (tenths of mm)
                filtered['PRCP_IN'] = filtered['PRCP'] / 10 * 0.03937
                precip_fig = px.bar(
                    filtered,
                    x=date_col,
                    y='PRCP_IN',
                    title=f"Precipitation - {selected_station}",
                    labels={'PRCP_IN': 'Precipitation (inches)'},
                    color_discrete_sequence=config['colors']
                )
                precip_fig.update_traces(
                    marker_color='#003366',
                    marker_line_color='blue',  # Add dark border
                    marker_line_width=0.3,
                    opacity=1  # Full opacity
                )
            else:
                precip_fig = create_empty_figure("No PRCP data available")
            # Common layout updates for both figures
            for fig in [weather_fig, precip_fig]:
                fig.update_layout(
                    title_x=0.5,
                    title_xanchor='center',
                    xaxis_title='Date',
                    hovermode='x unified',
                    template='plotly_white',
                    margin=dict(l=40, r=40, t=60, b=40)
                )
                fig.update_traces(
                    opacity=1
                )

            logger.info(f"Updated charts for station '{selected_station}' between {start_date} and {end_date}")
            return weather_fig, precip_fig
        except Exception as e:
            logger.error(f"Error in update_charts: {str(e)}", exc_info=True)
            return create_empty_figure("Error loading data"), create_empty_figure("Error loading data")
