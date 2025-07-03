import dash
from dash import Input, Output, exceptions
from ..logger import logger

def register_callbacks(app):
    @app.callback(
        [Output('city-input', 'value'),
         Output('data-type', 'value'),
         Output('start-date', 'date'),
         Output('end-date', 'date'),
         Output('start-year-selector', 'value'),
         Output('end-year-selector', 'value'),
         Output('results-container', 'children', allow_duplicate=True),
         Output('error-container', 'children', allow_duplicate=True),
         Output('data-store', 'data'),
         Output('status-container', 'children', allow_duplicate=True),
         Output('visualization-container', 'style', allow_duplicate=True),
         Output('analysis-results', 'style', allow_duplicate=True)
         ],
        Input('reset-button', 'n_clicks'),
        prevent_initial_call=True,
    )
    def handle_clear(n_clicks):
        logger.info(f"Clear button clicked {n_clicks} times")
        if n_clicks:
            return (
                '',  # city-input
                'TAVG',  # data-type
                None,  # start-date
                None,  # end-date
                None,  # start-year-selector
                None,  # end-year-selector
                None,  # results-container
                None,  # error-container
                None,  # data-store
                None,  # status-container
                {'display': 'none'},  # visualization-container
                {'display': 'none'}, # analysis-results container
            )
        raise exceptions.PreventUpdate

    @app.callback(
        Output('status-container', 'children', allow_duplicate=True),
        Output('error-container', 'children', allow_duplicate=True),
        [
            Input('submit-button', 'n_clicks'),
            Input('reset-button', 'n_clicks'),
            Input('import-button', 'n_clicks'),
            Input('visualize-button', 'n_clicks'),
            Input('download-button', 'n_clicks'),
            Input('clean-button', 'n_clicks'),
        ],
        prevent_initial_call=True,
    )
    def clear_status_on_other_clicks(submit_clicks, reset_clicks, import_clicks, viz_clicks, download_clicks, clean_clicks):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        triggered = ctx.triggered_id
        if triggered in [
            'submit-button',
            'reset-button',
            'import-button',
            'visualize-button',
            'download-button',
            'clean-button'
        ]:
            return "", ""
        raise dash.exceptions.PreventUpdate
