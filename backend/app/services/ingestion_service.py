import time
import random
import threading
from datetime import datetime, timezone
from app.extensions import socketio, db
from app.models.reading import Reading
from app.models.unit import Unit
from app.models.parameter import Parameter
from app import create_app

def mock_ingestion_loop(app):
    with app.app_context():
        while True:
            # Simulate receiving an MQTT payload every 5 seconds
            units = Unit.query.all()
            for unit in units:
                parameters = Parameter.query.filter_by(unit_id=unit.id).all()
                payload = {"unit_id": unit.id, "readings": {}}
                for param in parameters:
                    # Random walk telemetry
                    val = random.uniform(param.warning_threshold * 0.5, param.warning_threshold * 0.95)
                    reading = Reading(unit_id=unit.id, parameter_id=param.id, value=val, timestamp=datetime.now(timezone.utc), data_source='MQTT')
                    db.session.add(reading)
                    payload["readings"][param.name] = val
                db.session.commit()
                
                # Push real-time data to connected clients
                socketio.emit('telemetry_update', payload, namespace='/')
            
            time.sleep(5)

def start_ingestion_thread(app):
    thread = threading.Thread(target=mock_ingestion_loop, args=(app,))
    thread.daemon = True
    thread.start()
