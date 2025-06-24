from . import calendar, reset, fetch_data, visualization, download

def register_all_callbacks(app):
    calendar.register_callbacks(app)
    reset.register_callbacks(app)
    fetch_data.register_callbacks(app)
    visualization.register_callbacks(app)
    download.register_callbacks(app)
