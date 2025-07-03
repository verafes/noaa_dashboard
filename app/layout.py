from dash import html, dcc
from datetime import datetime, date
from .utils import DATA_TYPES, chart_options

def create_layout():

    year_options = [{'label': str(y), 'value': y} for y in range(datetime.now().year, 1950, -1)]

    return html.Div([
        dcc.Download(id='download-data'),
        dcc.Store(id='data-store'),

        html.H1('NOAA Weather Dashboard'),
        html.H4(
                'Analyze and visualize historical daily weather conditions with NOAA’s official data',
            className='subhead'
        ),
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
                html.Small('Please note: selecting only the year won’t update the date — you need to pick a full date.',
                           className='note-text'),
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
                        min_date_allowed=datetime(1950, 1, 1),
                        max_date_allowed=datetime.now(),
                        initial_visible_month=datetime.now(), # get here year user selected
                        clearable=True,
                        with_portal=True
                    ),
                ]),
                html.Label('End Date (optional):', className='date-label'),
                html.Small('Please note: selecting only the year won’t update the date — you need to pick a full date.',
                           className='note-text'),
                dcc.Dropdown(
                    id='end-year-selector',
                    value=None,
                    options=year_options,
                    placeholder='Select year (e.g., 2020)'
                ),
                html.Div([
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
                    'NOAA daily summaries data might be unavailable due to scheduled maintenance.'
                ], style={'margin': '10px 0'}),
                ], id='left-form-wrapper', style={'display': 'flex', 'flexDirection': 'column'}),
            ],
            style={'flex': '2', 'paddingLeft': '20px', 'paddingRight': '20px', 'display': 'flex', 'flexDirection': 'column'}),

            # RIGHT: Chart Selection Dropdown
            html.Div([
                html.H2('Data Analysis'),
                dcc.Dropdown(
                    id='analysis-chart-dropdown',
                    options=chart_options,
                    placeholder='Select a chart...',
                    clearable=False,
                    style={'minWidth': '250px'},
                    maxHeight=550
                ),
                html.Button('Visualize Data', id='visualize-button',
                            className='Button', n_clicks=0, style={'marginTop': '20px', 'marginBottom': '10px'}),
                html.Br(),
                html.P(['Note: After clicking the ', html.Span('Visualize Data', style={'font-weight': 'bold'}),
                           ' button, please wait while the data is retrieved and the visualization is generated.'], className='note'),
                html.Br(),
                # INFO
                html.H4('How to Use the Dashboard'),
                html.P([
                    html.B('This is Pipeline: '),
                    ' Scrape → CSV → Clean → SQLite Import → Analyze → Visualize'
                ], className='note'),
                html.P('1. Enter the city and state, separated by a comma. Missing comma or incorrect state may cause no results.',
                       className='note'),
                html.P(
                    '2. Select a data type. ', className='note'),
                html.P('3. Set date range (optional). Leave blank to use all available data.', className='note'),
                html.P([
                    '4. Click ',
                    html.Span('Download Data', style={'fontWeight': 'bold'}),
                    ' to save the raw CSV file locally.'
                ], className='note'),
                html.P([
                    '5. Click ',
                    html.Span('Submit', style={'font-weight': 'bold'}),
                    ' to fetch NOAA data and generate the table and charts for this location.'
                ], className='note'),
                html.P([
                    '6. Click ',
                    html.Span('Clean data', style={'font-weight': 'bold'}),
                    ' to prepare the data for database import.'
                ], className='note'),
                html.P([
                    '7. Click ',
                    html.Span('Import to DB', style={'font-weight': 'bold'}),
                    ' to save the cleaned data into your local SQLite database.'
                ], className='note'),
                html.P([
                    '8. After importing to DB, use the ',
                    html.Span('Data Analysis', style={'fontWeight': 'bold'}),
                    ' panel to generate aggregated views across stations and weather metrics.',
                ], className='note'),
                html.P([
                    'Tip: Use the ',
                    html.Span('Date Range', style={'font-style': 'italic'}),
                    ' filter below charts to focus on specific periods.'
                ], className='note'),
                html.P([
                    'Weather Dashboard © 2025 Vera Fesianava | Data source: ',
                    html.A('NOAA Daily Summaries',
                           href='https://www.ncei.noaa.gov/access/search/data-search/daily-summaries', target='_blank')
                ], style={'fontSize': '11px', 'color': 'gray', 'marginTop': '20px', 'whiteSpace': 'nowrap'})
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
        # == Results Display ==
        # Analysis Section
        dcc.Loading(
            id='loading-analysis',
            type='default',
            color='#119DFF',
            children=html.Div(id='analysis-results'),
            style={'marginBottom': '20px'}
        ),
        # One Location Section
        dcc.Loading(
            id='main-loading',
            type='default',
            color='#119DFF',
            fullscreen=False,
            children=[
                html.Div(id='results-container', style={'marginTop': '20px'}),
                # Visualization Section (hidden until data is loaded)
                html.Div(id='visualization-container', style={'display': 'none'}, children=[
                    html.H2(id='dashboard-title', className='centered-info'),

                    html.Div([
                        dcc.Dropdown(
                            id='station-dropdown',
                            options=[],
                            value=None,
                            placeholder='Select a station...',
                            clearable=False,
                            style={'width': '100%'}
                        ),
                    ], style={'width': '48%', 'margin': '10px auto'}),

                    dcc.DatePickerRange(
                        id='date-range',
                        min_date_allowed=date(1950, 1, 1),
                        max_date_allowed=datetime.now(),
                        start_date=None,
                        end_date=None,
                        display_format='YYYY-MM-DD',
                        month_format='MMMM YYYY',
                        minimum_nights=0,
                        clearable=True,
                        style={'margin': '5px 0',}
                    ),
                    dcc.Graph(id='weather-graph'),
                    dcc.Graph(id='precip-trend')
                ]),
            ],
            style={'position': 'relative', 'minHeight': '300px', 'backgroundColor': 'transparent'}
        ),

        dcc.Input(id='__dummy_input', style={'display': 'none'}),
        html.Div(id='__dummy_output', style={'display': 'none'}),
    ])
