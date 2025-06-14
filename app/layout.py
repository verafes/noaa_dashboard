from dash import html, dcc
from datetime import datetime, date
from .utils import DATA_TYPES, get_data_type_label, format_status_message

def create_layout():

    year_options = [{'label': str(y), 'value': y} for y in range(datetime.now().year, 1940, -1)]

    return html.Div([
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
