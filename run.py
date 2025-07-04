import os
from app.dashboard import app

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print("Running locally... at http://localhost:8050/")
    debug_mode=os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(
        host='0.0.0.0',
        port=8050,
        debug=debug_mode,
    )