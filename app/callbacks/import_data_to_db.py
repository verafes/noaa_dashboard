import os

from dash import Input, Output, html

from app.logger import logger
from app.data_processing.data_to_db import import_csv_to_db
from app.utils import get_latest_csv_filename, format_status_message, RAW_DATA_DIR, PROCESSED_DATA_DIR
from app.data_processing.data_cleaner import clean_single_csv

def register_callbacks(app):
    @app.callback(
        Output('status-container', 'children', allow_duplicate=True),
        Input('import-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def on_import_click(n_clicks):
        try:
            latest_csv = get_latest_csv_filename()
            raw_path = os.path.join(RAW_DATA_DIR, latest_csv)
            logger.info(f"latest_csv {latest_csv}, raw_path {raw_path}")
            # Clean CSV first
            clean_single_csv(raw_path)

            cleaned_path = os.path.join(PROCESSED_DATA_DIR, latest_csv)

            if not os.path.exists(cleaned_path):
                return format_status_message(f"Cleaned CSV not found: {cleaned_path}", "error")

            success, message = import_csv_to_db(cleaned_path)

            msg_type = "success" if success else "error"
            return html.Div(format_status_message(message, msg_type=msg_type))

        except FileNotFoundError:
            return html.Div(format_status_message(f"Latest CSV filename not found.", msg_type="warning"))
        except Exception as e:
            return html.Div(format_status_message(f"Error: {e}", msg_type="error"))