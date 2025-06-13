import warnings
import os

os.environ['DASH_DEBUG'] = 'False'
os.environ['DASH_HOT_RELOAD'] = 'False'
os.environ['WEBSOCKET_URL'] = ''
os.environ['NODE_OPTIONS'] = '--no-warnings'
warnings.filterwarnings("ignore")

from .logger import logger

import dash
from dash import Dash, dcc, html, Input, Output, State, no_update

import pandas as pd
import plotly.express as px

from datetime import datetime, date
from .scraper import scrape_and_download, download_csv
from .cache import cache_exists, load_from_cache, save_to_cache
from .utils import DATA_TYPES, get_data_type_label, format_status_message


DOWNLOAD_DIR = os.path.abspath("data")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def create_dash_app():
    """Creates and configures the Dash application"""
    logger.info("[APP] Initializing Dash NOAA Weather Dashboard...")
    app = Dash(
        __name__,
        assets_folder='../assets',
        suppress_callback_exceptions=True,
        prevent_initial_callbacks='initial_duplicate',
        update_title=None,
        meta_tags=[{'name': 'viewport',
        'content': 'width=device-width, initial-scale=1.0'}],
        serve_locally=True, # !important
        compress=False, # !important
        assets_ignore='.*\.hot-update\.js',
        include_assets_files=True,
       )
    # Disable all development tools
    app._hot_reload = False
    # Disable dev tools completely
    app.enable_dev_tools(
        dev_tools_ui=False,
        dev_tools_props_check=False,
    )
    stations = []
    year_options = [{'label': str(y), 'value': y} for y in range(datetime.now().year, 1940, -1)]

    app.layout = html.Div([
        dcc.Download(id="download-data"),
        dcc.Store(id='data-store'),

        html.H1("NOAA Weather Dashboard"),
        # Input Form
        html.Div([
            dcc.Input(
                id='city-input',
                className="input-field",
                type='text',  value='',
                placeholder='City Name (e.g., New York, NY)'
            ),
            dcc.Dropdown(
                id='data-type',
                options=DATA_TYPES,
                value='TAVG',
                placeholder="Select data type..."
            ),
            html.Br(),

            html.Label('Start Date (optional):'),
            dcc.Dropdown(
                id='start-year-selector',
                value=None,
                options=year_options,
                placeholder='Select year (e.g., 1995)',

                clearable=False
            ),
            # Date inputs
            html.Div([
                dcc.DatePickerSingle(
                    id='start-date',
                    display_format='YYYY-MM-DD',
                    month_format='MMMM YYYY',
                    placeholder='Select start date',
                    min_date_allowed=datetime(1941, 1, 1),
                    max_date_allowed=datetime.now(),
                    initial_visible_month=datetime.now(), # get here year user selected
                    clearable=True,
                    with_portal=True
                ),
            ]),
            html.Br(),
            html.Label('End Date (optional):'),
            dcc.Dropdown(
                id='end-year-selector',
                value=None,
                options=year_options,
                placeholder='Select year (e.g., 2020)'
            ),
            html.Div([
                # html.Label('End Date (optional):'),
                dcc.DatePickerSingle(
                    id='end-date',
                    display_format='YYYY-MM-DD',
                    month_format='MMMM YYYY',
                    placeholder='Select end date',
                    min_date_allowed=datetime(1941, 1, 1),
                    max_date_allowed=datetime.now(),
                    initial_visible_month=datetime.now(),
                    clearable=True,
                    with_portal=True,
                ),
            ]),
            html.Br(),
            dcc.Loading(
                id="main-loading",
                type="default",
                color="#119DFF",
                fullscreen=False,
                style={'position': 'relative', 'minHeight': '300px', 'backgroundColor': 'rgba(240, 240, 240, 0.5)'}
            ),
            # buttons
            html.Button('Download Data', id='download-button', className='Button', n_clicks=0),
            html.Button('Submit', id='submit-button', className='Button', n_clicks=0),
            html.Button('Clear/Reset', id='reset-button', className='Button', n_clicks=0,
               style={'background': '#ff4444', 'color': 'white'}),

            dcc.Loading(
                id="loading-spinner",
                type="default",
                children=html.Div(id="loading-output"),
                style={'display': 'none'}
            ),
            html.Label(
        'Note: After submitting form, please wait while getting data and building visualization',
               style={'margin': '10px 0'}
            )
        ]),
        # error if no data
        html.Div(id='error-container', style={'marginTop': '20px'}),
        # status message
        html.Div(id='status-container', style={'marginTop': '20px'}),
        # Results Display
        html.Div(id='results-container', style={'marginTop': '20px'}),
        # Visualization Section (hidden until data is loaded)
        html.Div(id='visualization-container', style={'display': 'none'}, children=[
            html.H2(id='dashboard-title', style={'textAlign': 'center'}),

            html.Div([
                dcc.Dropdown(
                    id='station-dropdown',
                    options=[],
                    value=None,
                    placeholder="Select a station...",
                    clearable=False,
                    style={'width': '100%'}
                ),
            ], style={'width': '48%', 'margin': '20px auto'}),

            dcc.DatePickerRange(
                id='date-range',
                min_date_allowed=date(1941, 1, 1),
                max_date_allowed=datetime.now(),
                start_date=None,
                end_date=None,
                display_format='YYYY-MM-DD',
                month_format='MMMM YYYY',
                minimum_nights=0,
                clearable=True,
                style={'margin': '20px', 'fontSize': '16px'}
            ),

            dcc.Graph(id='temp-trend'),
            dcc.Graph(id='precip-trend')
        ]),
        dcc.Input(id='__dummy_input', style={'display': 'none'}),
        html.Div(id='__dummy_output', style={'display': 'none'}),
    ])

    # year picker updater
    @app.callback(
        Output('start-date', 'initial_visible_month'),
        Output('end-date', 'initial_visible_month'),
        Input('start-year-selector', 'value'),
        Input('end-year-selector', 'value'),
    )
    def update_calendar_visible_month(start_year, end_year):
        """ Updates year in calendar picker """
        start_month = datetime(start_year, 1, 1) if start_year else datetime.today()
        end_month = datetime(end_year, 1, 1) if end_year else datetime.today()
        return start_month, end_month

    @app.callback(
        [Output('city-input', 'value'),
         Output('data-type', 'value'),
         Output('start-date', 'date'),
         Output('end-date', 'date'),
         Output('start-year-selector', 'value'),
         Output('end-year-selector', 'value'),
         Output('results-container', 'children', allow_duplicate=True),
         Output('error-container', 'children', allow_duplicate=True),
         Output('data-store', 'data'),
         Output('status-container', 'children', allow_duplicate=True),
         Output('visualization-container', 'style', allow_duplicate=True)
         ],
        Input('reset-button', 'n_clicks'),
        prevent_initial_call=True,
        # suppress_callback_exceptions=True,
    )
    def handle_clear(n_clicks):
        logger.info(f"Clear button clicked {n_clicks} times")
        if n_clicks:
            return (
                '',  # city-input
                'TAVG',  # data-type
                None,  # start-date
                None,  # end-date
                None,  # start-year-selector
                None,  # end-year-selector
                None,  # results-container
                None,  # error-container
                None,  # data-store
                None,  # status-container
                {'display': 'none'}  # visualization-container
            )
        raise dash.exceptions.PreventUpdate

    @app.callback(
        Output('date-range', 'disabled'),
        Input('results-container', 'children')
    )
    def enable_date_filter(_):
        return False

    # This updates the dashboard - called when submit-button is clicked
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

    # handles creating dash_app graph
    # Callback to update visualization controls
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

    # This handles CSV downloads - called when download-button is clicked
    @app.callback(
        [ Output('download-data', 'data'),
          Output('error-container', 'children', allow_duplicate=True),
          Output("main-loading", "children"),
          Output('status-container', 'children')],
        Input('download-button', 'n_clicks'),
        [State('city-input', 'value'),
         State('data-type', 'value'),
         State('start-date', 'date'),
         State('end-date', 'date')],
        suppress_callback_exceptions=True,
        prevent_initial_call=True
    )
    def handle_download(n_clicks, city_name, data_type, start_date, end_date):
        """ Triggered when download-button is clicked. Downloads CSV file with the selected data. """
        if not n_clicks or not city_name or not data_type:
            return (no_update, format_status_message("Please fill city and data type fields", "error"),
                    no_update, no_update)
            # raise dash.exceptions.PreventUpdate
        logger.info(f"Download button clicked: n_clicks={n_clicks}")
        try:
            logger.info(f"Starting CSV download for city='{city_name}', data_type='{data_type}', "
                        f"start_date='{start_date}', end_date='{end_date}'")
            csv_url = scrape_and_download(city_name, data_type, start_date, end_date)
            if not isinstance(csv_url, str) or not csv_url.strip().lower().endswith('.csv'):
                # If it's not a CSV, assume it's a message
                logger.warning(f"CSV URL invalid or error message received: {csv_url}")
                return no_update, format_status_message(csv_url, "error"), no_update, no_update
            # return dcc.send_file(csv_url)
            logger.info(f"CSV downloaded successfully: {csv_url}")
            return (
                no_update, no_update, no_update,
                format_status_message(f"Successfully downloaded: {os.path.basename(csv_url)}", "success") )
        except Exception as e:
            logger.error(f"Download failed: {str(e)}", exc_info=True)
            return (no_update, format_status_message(f"Download failed: {str(e)}", "error"),
                    no_update, no_update)

    return app

app = create_dash_app()
server = app.server

