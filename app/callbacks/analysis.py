import os

from dash.exceptions import PreventUpdate
from dash import html, Input, Output, State

import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
import threading
import pandas as pd
from datetime import datetime


from app.data_processing.data_analysis import (
    load_data_from_db,
    aggregate_weather_conditions,
    aggregate_by_station_and_time,
    plot_max_temperature_trends,
    plot_temperature_boxplot,
    plot_snowfall_pie, plot_snowfall_bar,
    plot_snowfall_trends, plot_station_trends,
    label_map, plot_yearly_distributions,
    plot_weather_correlation_heatmap, prepare_event_flags,
    plot_aggregated_weather_event_frequencies
)

from app.logger import logger

# DB location
DB_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../db")
DB_NAME = "noaa_weather.db"
DB_PATH = os.path.join(DB_DIR, DB_NAME)
TABLE_NAME = "weather_data"

def register_callbacks(app):
    @app.callback(
        Output("__dummy_output", "children"),  # Required dummy output
        Input("visualize-button", "n_clicks"),
        [State("analysis-chart-dropdown", "value"),
         State("start-date", "date"),
         State("end-date", "date"),
         State("city-input", "value")],
        prevent_initial_call=True
    )
    def visualize_data(n_clicks, selected_chart, start_date, end_date, city_name):
        if n_clicks is None or n_clicks == 0:
            raise PreventUpdate

        def run_visualization():
            try:
                logger.info("Starting weather data analysis...")

                df_weather = load_data_from_db(DB_PATH, TABLE_NAME)
                logger.info(f"Loaded weather data: {len(df_weather)} records")
                logger.info("Checking for missing values:")
                logger.info(f"\n{df_weather.isna().sum()}")

                df_agg = aggregate_weather_conditions(df_weather)
                logger.info(f"Aggregated data shape: {df_agg.shape}")

                logger.info(f"Stations in filtered data: {df_agg['NAME'].nunique()}")
                logger.info(f"Years in filtered data: {df_agg['YEAR_PERIOD'].dt.year.unique()}")

                if start_date and end_date:
                    start = pd.to_datetime(start_date)
                    end = pd.to_datetime(end_date)
                    df_agg = df_agg[
                        (df_agg['YEAR_PERIOD'].dt.to_timestamp() >= start) &
                        (df_agg['YEAR_PERIOD'].dt.to_timestamp() <= end)
                        ]

                plt.switch_backend('TkAgg')  # or 'Qt5Agg'

                year = pd.to_datetime(start_date).year if start_date else datetime.now().year

                # Generate selected plot
                if selected_chart == "Max Temp Trends":
                    df_agg_st = aggregate_by_station_and_time(df_weather, date_freq='Y')
                    stations = df_agg_st['NAME'].unique()[:20]
                    plot_max_temperature_trends(df_agg_st, stations)
                elif selected_chart == "Temp Boxplot":
                    plot_temperature_boxplot(df_agg)
                elif selected_chart == "Snowfall Pie":
                    plot_snowfall_pie(df_agg, year)
                elif selected_chart == "Snowfall Bar":
                    plot_snowfall_bar(df_agg, year)
                elif selected_chart == "Snowfall Trends":
                    df_agg_st = aggregate_by_station_and_time(df_weather, date_freq='Y')
                    stations = df_agg_st['NAME'].unique()[:20]
                    plot_snowfall_trends(df_agg_st, stations)
                elif selected_chart == "Sunshine Trends":
                    conditions = ['TSUN', 'WSFG', 'RHAV']
                    plot_station_trends(df_weather, 'TSUN', label_map)
                elif selected_chart == "Weather Events":
                    df_weather['YEAR'] = df_weather['DATE'].dt.year
                    conditions = ['WT01', 'WT08', 'WT16', 'WSFG']
                    plot_aggregated_weather_event_frequencies(
                        prepare_event_flags(df_weather, conditions),
                        conditions,
                        label_map
                    )
                elif selected_chart == "Yearly Distributions":
                    conditions = ['TAVG', 'PRCP', 'SNOW']
                    plot_yearly_distributions(df_weather, conditions, label_map)
                elif selected_chart == "Correlation Heatmap":
                    conditions = [
                        'TMIN', 'TAVG', 'TMAX', 'PRCP', 'SNOW', 'TSUN',
                        'ACMH', 'WSFG', 'RHAV', 'WT01', 'WT08', 'WT16'
                    ]
                    plot_weather_correlation_heatmap(df_weather, conditions)

                plt.show(block=True)

            except Exception as e:
                print(f"Error during visualization: {str(e)}")
            finally:
                plt.close('all')
        # Run visualization in separate thread to avoid blocking Dash
        thread = threading.Thread(target=run_visualization, daemon=True)
        thread.start()

        return ""
