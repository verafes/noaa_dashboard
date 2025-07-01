import os
from dash import html, Input, Output

from app.utils import RAW_DATA_DIR, PROCESSED_DATA_DIR, format_status_message
from app.data_processing.data_cleaner import clean_single_csv, get_latest_csv_filename
from app.logger import logger

input_dir=RAW_DATA_DIR
output_dir=PROCESSED_DATA_DIR

def register_callbacks(app):
    @app.callback(
        Output('status-container', 'children', allow_duplicate=True),
        Input('clean-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def handle_clean_click(n_clicks):
        try:
            filename = get_latest_csv_filename()
            full_path = os.path.join(RAW_DATA_DIR, filename)
            logger.info(f"[FILE] Full path to latest CSV: {full_path}")
            if not filename:
                raise FileNotFoundError("No filename found in latest_download.txt")

            logger.info(f"Starting cleaning for: {filename}")
            clean_single_csv(filename)

            return html.Div(
                format_status_message(f"Cleaned and saved: {filename}", "success")
            )

        except FileNotFoundError:
            logger.warning("latest_download.txt is missing.")
            return html.Div(format_status_message("No file found to clean.", "warning"))

        except Exception as e:
            logger.error(f"Cleaning failed: {e}")
            return html.Div(format_status_message(f"Error during cleaning: {e}", "error"))
