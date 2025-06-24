from datetime import datetime
from dash import Input, Output, callback

# year picker updater
def register_callbacks(app):
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
