import dash
from dash import html, Input, Output, State, no_update

import pandas as pd

from ..cache import cache_exists, load_from_cache, save_to_cache
from ..scraper import scrape_and_download
from ..utils import get_data_type_label, format_status_message
from ..logger import logger


# This updates the dashboard - called when submit-button is clicked
def register_callbacks(app):
    @app.callback(
        [Output('results-container', 'children', allow_duplicate=True), # , allow_duplicate=True
         Output('data-store', 'data', allow_duplicate=True), # , allow_duplicate=True
         Output('visualization-container', 'style'),
         Output('error-container', 'children'),
         Output("main-loading", "type")],
        [Input('submit-button', 'n_clicks')], # Only need submit button here
        [State('city-input', 'value'),
         State('data-type', 'value'),
         State('start-date', 'date'),
         State('end-date', 'date')],
        prevent_initial_call=True
    )
    def update_dashboard(n_clicks, city_name, data_type, start_date=None, end_date=None):
        logger.info("[DASHBOARD] update_dashboard triggered")
        global stations # global_df
        try:
            ctx = dash.ctx or dash.callback_context
        except:
            ctx = dash.callback_context
        if not ctx.triggered:
            logger.warning("[DASHBOARD] No callback triggered")
            return [dash.no_update] * 4, "default"  # ← Add this
        # 2. Validate required inputs
        if not n_clicks or not all([city_name, data_type]):
            logger.warning("[VALIDATION] Missing required inputs: city or data_type")
            return (
                html.Div(""),
                dash.no_update,
                {'display': 'none'},
                format_status_message("Please fill city and data type fields", "error"),
                "default"
            )
        logger.info(f"n_clicks {n_clicks}, City: {city_name}, Data type: {data_type}, Start date: {start_date}, End date: {end_date}")

        trigger_id = ctx.triggered_id if hasattr(ctx, 'triggered_id') else dash.ctx.triggered_id
        if trigger_id == 'reset-button':
            logger.info("[RESET] Reset button triggered inside update_dashboard")
            return None, None, {'display': 'none'}, None

        # 3. Always call scrape_and_download first
        print(f"Fetching data for {city_name} ({data_type})...")
        csv_url = scrape_and_download(city_name, data_type, start_date, end_date)
        # 4. Validate response - Case 1: Received a message (not CSV URL)
        if not csv_url.endswith('.csv'):
            logger.error(f"[FETCH ERROR] Failed to get CSV URL, got message: {csv_url}")
            return (
                    html.Div("", style={'color': 'red'}),
                    dash.no_update,
                    {'display': 'none'},
                    format_status_message(csv_url, "error"),
                    "default"  # Revert spinner
                )
        # Validate response - Case 2: Received CSV URL - display success_msg, save it in dcc.Store in and proceed to create and display graph
        success_msg = html.Div([
            html.Span("✅ Data downloaded successfully!", style={'color': 'green', 'display': 'block'}),
            html.Span(f"Processing {csv_url}...", style={'color': 'gray'})
        ]), True

        try:
            # 5. Process data - Get fresh CSV URL from NOAA
            if cache_exists(city_name, data_type):
                logger.info(f"[CACHE] Loading cached data for {city_name} ({data_type})")
                df = load_from_cache(city_name, data_type)
            else:
                try:
                    logger.info(f"[DOWNLOAD] Reading CSV from URL: {csv_url}")
                    df = pd.read_csv(csv_url, low_memory=False)
                    save_to_cache(df, city_name, data_type)
                    logger.info(f"[CACHE] Saved data to cache for {city_name} ({data_type})")
                except pd.errors.EmptyDataError:
                    return format_status_message("Downloaded file is empty", "error")
                except pd.errors.ParserError:
                    return format_status_message("Could not parse downloaded file", "error")
                except Exception as e:
                    return format_status_message(f"Unexpected error: {str(e)}", "error")

            df['DATE'] = pd.to_datetime(df['DATE'])
            logger.info(f"[DATA] Data loaded successfully with stations: {df['NAME'].unique().tolist()}")
            logger.debug(f"[DATA] Head of dataframe:\n{df.head()}")

            # Standardize column names (DATE vs date)
            date_col = 'DATE' if 'DATE' in df.columns else 'date'
            df[date_col] = pd.to_datetime(df[date_col])

            # Apply date filtering if dates are provided
            start_date = pd.to_datetime(start_date) if start_date else None
            end_date = pd.to_datetime(end_date) if end_date else None
            logger.info(f"[FILTER] Applying date filter: start={start_date}, end={end_date}")

            if start_date:
                df = df[df[date_col] >= start_date]
            if end_date:
                df = df[df[date_col] <= end_date]
                # If filtering resulted in empty dataframe, show error
                if df.empty:
                    logger.warning("[FILTER] No data available after filtering by date range")
                    return (
                        html.Div("!!No data available for the selected date range",
                                 style={'color': 'red', 'margin': '20px'}),
                        dash.no_update,
                        {'display': 'none'},
                        format_status_message("No data available for the selected date range", "error"),
                        "default"
                    )
            # 6. Get unique stations
            stations = df['NAME'].unique().tolist() if 'NAME' in df.columns else []
            logger.info(f"[DATA] Unique stations extracted: {stations}")
            # Create dashboard components
            date_range_text = ""
            if start_date or end_date:
                start_text = start_date.strftime('%Y-%m-%d') if start_date else 'beginning'
                end_text = end_date.strftime('%Y-%m-%d') if end_date else 'present'
                date_range_text = f" from {start_text} to {end_text}"

            # 7. Show visualization section if we have the required columns
            required_cols = {'DATE', 'TMIN', 'TAVG', 'TMAX', 'PRCP', 'NAME'}
            missing = required_cols - set(df.columns)
            if missing:
                logger.warning(f"[DATA] Warning: Missing columns {missing} - some visualizations may be limited")
                return (
                    html.Div(f"Missing columns: {', '.join(missing)}"),
                    dash.no_update,
                    {'display': 'none'},
                    format_status_message(f"Data missing required columns: {missing}", "error"),
                    "default"
                )
            viz_style = {'display': 'block'} if required_cols.issubset(df.columns) else {'display': 'none'}
            logger.debug(f"[DATA] Columns in DataFrame: {df.columns.tolist()}")
            logger.debug(f"[DATA] Required columns present: {required_cols.issubset(df.columns)}")

            results = html.Div([
                html.H3(f"Weather Data for {city_name}"),
                html.P(f"Showing {get_data_type_label(data_type)} data{date_range_text}"),
                html.P(f"Data points: {len(df)}"),
                html.P(f"Date range: {df['DATE'].min().date()} to {df['DATE'].max().date()}"),
                dash.dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in df.columns],
                    page_size=10,
                    style_table={'overflowX': 'auto'}
                )
            ])
            return (
                results,  # Filled results container
                df.to_dict('records'),  # Store processed data
                viz_style,  # Show visualization
                None,  # No errors
                "circle"  # Success spinner style
            )
        except Exception as e:
            logger.error(f"[EXCEPTION] Error processing data: {str(e)}", exc_info=True)
            return (
                html.Div(f"Error: {str(e)}", style={'color': 'red', 'margin': '20px'}),
                dash.no_update,
                {'display': 'none'},
                format_status_message(f"Error: {str(e)}", "error"),
                "default"
            )