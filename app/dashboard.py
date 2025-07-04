import warnings
import os

from dash import Dash

from .callbacks import register_all_callbacks
from .logger import logger
from .layout import create_layout
from app.utils import IS_RENDER, PROJECT_ROOT
from dotenv import load_dotenv
load_dotenv()

# Auto-create DB if missing
from app.utils import DB_PATH
from app.data_processing.data_to_db import get_all_cleaned_csv_files, import_csv_to_db

# Environment settings
os.environ.setdefault('DASH_DEBUG', 'False')
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('NODE_ENV', 'production')
os.environ.setdefault('DASH_HOT_RELOAD', 'False')
os.environ.setdefault('NODE_OPTIONS', '--no-warnings')

# Suppress Python warnings
warnings.filterwarnings("ignore")

# Ensure data directory exists
if IS_RENDER:
    DOWNLOAD_DIR = "/tmp/data"
    REPO_PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
else:
    DOWNLOAD_DIR = os.path.abspath("data")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
logger.info(f"[PATHS] DOWNLOAD_DIR set to: {DOWNLOAD_DIR}")


def create_dash_app():
    """Creates and configures the Dash application"""
    logger.info("[APP] Initializing Dash NOAA Weather Dashboard...")

    if not os.path.exists(DB_PATH):
        logger.info(f"[DB] Database not found at {DB_PATH}, generating from cleaned CSVs...")
        try:
            cleaned_csvs = get_all_cleaned_csv_files()
            if cleaned_csvs:
                for csv_file in cleaned_csvs:
                    import_csv_to_db(csv_file)
            else:
                logger.info(f"[DATA] No cleaned CSV files found to build database.")
        except Exception as e:
            logger.error(f"[DB] An error occurred while generating the database: {e}")
    else:
        logger.info(f"[DB] Database already exists at {DB_PATH}")

    app = Dash(
        __name__,
        assets_folder='../assets',
        suppress_callback_exceptions=True,
        prevent_initial_callbacks='initial_duplicate',
        update_title=None,
        meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}],
        serve_locally=True, # !important
        compress=False, # !important
        assets_ignore=r'.*\.hot-update\.js',
        include_assets_files=True,
       )

    stations = []

    app.layout = create_layout()

    register_all_callbacks(app)

    return app

app = create_dash_app()
server = app.server

logger.info("[APP] Dash NOAA Weather Dashboard app module loaded")
