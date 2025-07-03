from dash.exceptions import PreventUpdate
from dash import html, Input, Output, State

import matplotlib

from app.utils import format_status_message, chart_options

matplotlib.use('Agg')
from matplotlib import pyplot as plt
import pandas as pd
from datetime import datetime


from app.data_processing.data_analysis import (
    get_weather_data,
    aggregate_weather_conditions,
    aggregate_by_station_and_time,
    plot_max_temperature_trends,
    plot_temperature_boxplot,
    plot_snowfall_pie, plot_snowfall_bar,
    plot_snowfall_trends,
    label_map, plot_yearly_distributions,
    plot_weather_correlation_heatmap, prepare_event_flags,
    plot_aggregated_weather_event_frequencies,
)

from app.logger import logger

def register_callbacks(app):
    @app.callback(
        # Output("__dummy_output", "children"),  # Required dummy output
        Output('analysis-results', 'children', allow_duplicate=True),
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

        def run_visualization(selected_chart):
            try:
                logger.info("Starting weather data analysis...")

                df = None
                df_weather = get_weather_data()
                logger.info(f"Loaded weather data: {len(df_weather)} records")
                logger.info("Checking for missing values:")
                logger.info(f"\n{df_weather.isna().sum()}")

                if start_date and end_date:
                    start = pd.to_datetime(start_date)
                    end = pd.to_datetime(end_date)
                    df_weather = df_weather[
                        (df_weather['YEAR_PERIOD'].dt.to_timestamp() >= start) &
                        (df_weather['YEAR_PERIOD'].dt.to_timestamp() <= end)
                        ]

                df_agg = aggregate_weather_conditions(df_weather)
                logger.info(f"Aggregated data shape: {df_agg.shape}")

                logger.info(f"Stations in filtered data: {df_agg['NAME'].nunique()}")
                logger.info(f"Years in filtered data: {df_agg['YEAR_PERIOD'].dt.year.unique()}")

                year = pd.to_datetime(start_date).year if start_date else datetime.now().year
                img_src = None
                # Generate selected plot
                if selected_chart == "Max Temp Trends":
                    df_agg_st = aggregate_by_station_and_time(df_weather, date_freq='Y')
                    stations = df_agg_st['NAME'].unique()[:20]
                    img_src = plot_max_temperature_trends(df_agg_st, stations)
                elif selected_chart == "Temp Boxplot":
                    img_src = plot_temperature_boxplot(df_agg)
                elif selected_chart == "Snowfall Pie":
                    img_src = plot_snowfall_pie(df_agg, year)
                elif selected_chart == "Snowfall Bar":
                    img_src = plot_snowfall_bar(df_agg, year)
                elif selected_chart == "Snowfall Trends":
                    df_agg_st = aggregate_by_station_and_time(df_weather, date_freq='Y')
                    stations = df_agg_st['NAME'].unique()[:20]
                    img_src = plot_snowfall_trends(df_agg_st, stations)
                elif selected_chart == "Weather Events":
                    df_weather['YEAR'] = df_weather['DATE'].dt.year
                    conditions = ['WT01', 'WT08', 'WT16', 'WSFG']
                    img_src = plot_aggregated_weather_event_frequencies(
                        prepare_event_flags(df_weather, conditions),
                        conditions,
                        label_map
                    )
                elif selected_chart == "Yearly Distributions":
                    conditions = ['TAVG', 'PRCP', 'SNOW']
                    img_src = plot_yearly_distributions(df_weather, conditions, label_map)
                elif selected_chart == "Correlation Heatmap":
                    conditions = [
                        'TMIN', 'TAVG', 'TMAX', 'PRCP', 'SNOW', 'TSUN',
                        'ACMH', 'WSFG', 'RHAV', 'WT01', 'WT08', 'WT16'
                    ]
                    img_src = plot_weather_correlation_heatmap(df_weather, conditions)

            except Exception as e:
                logger.info(f"Error during visualization: {str(e)}")
                return html.Div(format_status_message(f"Error during visualization: {e}", "error"))
            finally:
                plt.close('all')

            label_for_selected = next((opt['label'] for opt in chart_options if opt['value'] == selected_chart),
                                      selected_chart)
            if isinstance(img_src, list):
                images_to_return = html.Div(
                    [html.Img(src=src, className="responsive-img") for src in img_src],
                    className="analysis-container"
                )
            else:
                images_to_return = html.Div([
                    html.Img(src=img_src, className="responsive-img")
                ], className="analysis-container" )
            images_with_heading = html.Div([
                html.H3(f"Analysis Data for {label_for_selected}", style={"textAlign": "center", "marginTop": "20px"}),
                images_to_return
            ])
            return images_with_heading

        result = run_visualization(selected_chart)
        return result
