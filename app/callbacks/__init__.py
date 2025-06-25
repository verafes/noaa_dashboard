from . import calendar, reset, fetch_data, visualization, download, clean_data, import_data_to_db


def register_all_callbacks(app, on_import_click=None):
    calendar.register_callbacks(app)
    reset.register_callbacks(app)
    fetch_data.register_callbacks(app)
    visualization.register_callbacks(app)
    download.register_callbacks(app)
    clean_data.register_callbacks(app)
    import_data_to_db.register_callbacks(app)
