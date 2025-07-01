from dash import html, dcc
from datetime import datetime, date
from .utils import DATA_TYPES

def create_layout():

    year_options = [{'label': str(y), 'value': y} for y in range(datetime.now().year, 1940, -1)]

    return html.Div([
        dcc.Download(id='download-data'),
        dcc.Store(id='data-store'),

        html.H1('NOAA Weather Dashboard'),
        # Two-column section: Left = Data Form, Right = Chart Dropdown
        html.Div([
            # LEFT: NOAA Form Input Form
            html.Div([
            html.H2('NOAA Data Import'),
            # html.Br(),
            html.Div([
                dcc.Input(
                    id='city-input',
                    className='input-field',
                    type='text',  value='',
                    placeholder='City Name (e.g., New York, NY)'
                ),
                dcc.Dropdown(
                    id='data-type',
                    options=DATA_TYPES,
                    value='TAVG',
                    placeholder='Select data type...'
                ),

                html.Label('Start Date (optional):', className='date-label'),
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
                html.Label('End Date (optional):', className='date-label'),
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

                # buttons
                html.Div([
                    html.Button('Download Data', id='download-button', className='Button', n_clicks=0),
                    html.Button('Submit', id='submit-button', className='Button', n_clicks=0),
                    html.Button('Clear/Reset Form', id='reset-button', className='Button', n_clicks=0,
                       style={'background': '#ff4444', 'color': 'white'}),
                    html.Button('Clean Data', id='clean-button', className='Button', n_clicks=0),
                    html.Button('Import to DB', id='import-button', className='Button', n_clicks=0),
                ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '5px', 'marginTop': '5px'}),
                html.Label([
                    'Note: After submitting form, please wait while the data is retrieved and the visualization is generated.',
                    html.Br(),html.Br(),
                    'NOAA daily summaries data might be unavailable (usially Thursday from 12:00 PM to Friday 12:00 PM) due to scheduled maintenance.'
                ], style={'margin': '10px 0'}),
                ], id='left-form-wrapper', style={'display': 'flex', 'flexDirection': 'column'}),
            ],
            style={'flex': '2', 'paddingRight': '20px', 'display': 'flex', 'flexDirection': 'column'}),

            # RIGHT: Chart Selection Dropdown
            html.Div([
                html.H2('Data Analysis'),
                dcc.Dropdown(
                    id='analysis-chart-dropdown',
                    options=[
                        {'label': 'Yearly Max Temperature Trends (Line chart)', 'value': 'Max Temp Trends'},
                        {'label': 'Avg Temperature Over Years (Boxplot)', 'value': 'Temp Boxplot'},
                        {'label': 'Snowfall Contribution by Station (Pie)', 'value': 'Snowfall Pie'},
                        {'label': 'Total Snowfall by Station (Bar)', 'value': 'Snowfall Bar'},
                        {'label': 'Snowfall Max Snowfalls Trends (Line chart)', 'value': 'Snowfall Trends'},
                        {'label': 'Event Frequencies Fog, Smoke, Rain, Wind (Bar)', 'value': 'Weather Events'},
                        {'label': 'Yearly Distributions Temp, Precip, Snow (Boxplot)', 'value': 'Yearly Distributions'},
                        {'label': 'Correlation Heatmap', 'value': 'Correlation Heatmap'},
                    ],
                    value='Max Temp Trends',
                    clearable=False,
                    style={'minWidth': '250px'},
                    maxHeight=550
                ),
                html.Button('Visualize Data', id='visualize-button',
                            className='Button', n_clicks=0, style={'marginTop': '20px', 'marginBottom': '20px'}),
                html.Br(),
                html.Label('Note: After clicking the button, please wait while the data is retrieved and the visualization is generated.'),
                ], style={'flex': '1', 'paddingRight': '30px', 'marginTop': '0' }),
        ], style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'marginBottom': '5px'
        }),

        # error if no data
        html.Div(id='error-container', style={'marginTop': '20px'}),
        # status message
        html.Div(id='status-container', style={'marginTop': '20px'}),
        # Results Display
        dcc.Loading(
            id='main-loading',
            type='default',
            color='#119DFF',
            fullscreen=False,
            children=[
                html.Div(id='results-container', style={'marginTop': '20px'}),
                # Visualization Section (hidden until data is loaded)
                html.Div(id='visualization-container', style={'display': 'none'}, children=[
                    html.H2(id='dashboard-title', style={'textAlign': 'center'}),

                    html.Div([
                        dcc.Dropdown(
                            id='station-dropdown',
                            options=[],
                            value=None,
                            placeholder='Select a station...',
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
                        clearable=True
                    ),
                    dcc.Graph(id='weather-graph'),
                    dcc.Graph(id='precip-trend')
                ]
                )
            ],
            style={'position': 'relative', 'minHeight': '300px', 'backgroundColor': 'transparent'}
        ),

        dcc.Input(id='__dummy_input', style={'display': 'none'}),
        html.Div(id='__dummy_output', style={'display': 'none'}),
    ])
