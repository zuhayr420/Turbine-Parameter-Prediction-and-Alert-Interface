import os
from app import create_app
from app.extensions import socketio

env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

from app.services.ingestion_service import start_ingestion_thread
start_ingestion_thread(app)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
