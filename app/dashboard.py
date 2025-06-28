import warnings
import os

from dash import Dash

from .callbacks import register_all_callbacks
from .logger import logger
from .layout import create_layout


# Environment settings
os.environ['DASH_DEBUG'] = 'False'
os.environ['DASH_HOT_RELOAD'] = 'False'
os.environ['WEBSOCKET_URL'] = ''
os.environ['NODE_OPTIONS'] = '--no-warnings'

# Suppress Python warnings
warnings.filterwarnings("ignore")

# Ensure data directory exists
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
        assets_ignore=r'.*\.hot-update\.js',
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

    app.layout = create_layout()

    register_all_callbacks(app)

    return app

app = create_dash_app()
server = app.server

