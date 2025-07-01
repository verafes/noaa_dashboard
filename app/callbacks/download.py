# This handles CSV downloads - called when download-button is clicked

import os

from dash import html, Input, Output, State, no_update

from ..scraper import scrape_and_download
from ..utils import format_status_message
from ..logger import logger


def register_callbacks(app):
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
            return (
                no_update,
                format_status_message("Please fill city and data type fields", "error"),
                no_update,
                no_update
            )
            # raise dash.exceptions.PreventUpdate
        logger.info(f"Download button clicked: n_clicks={n_clicks}")
        try:
            logger.info(f"Starting CSV download for city='{city_name}', data_type='{data_type}', "
                        f"start_date='{start_date}', end_date='{end_date}'")
            csv_url = scrape_and_download(city_name, data_type, start_date, end_date)

            if not isinstance(csv_url, str) or not csv_url.strip().lower().endswith('.csv'):
                # If it's not a CSV, assume it's a message
                logger.warning(f"CSV URL invalid or error message received: {csv_url}")
                return (
                    no_update,
                    format_status_message(csv_url, "error"),
                    no_update,
                    no_update
                )

            logger.info(f"CSV downloaded successfully: {csv_url}")
            return (
                no_update,
                "", # Clear error
                no_update,
                format_status_message(f"Successfully downloaded: {os.path.basename(csv_url)}", "success")
            )
        except Exception as e:
            logger.error(f"Download failed: {str(e)}", exc_info=True)
            return (
                no_update,
                format_status_message(f"Download failed: {str(e)}", "error"),
                no_update,
                ""
            )
