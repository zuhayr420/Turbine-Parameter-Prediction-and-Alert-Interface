import os
import sys

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models.station import Station
from app.models.unit import Unit

app = create_app('development')

with app.app_context():
    # Create tables (will create stations table)
    db.create_all()

    # Check if we need to create the default station
    station = Station.query.filter_by(name='Thermal Station Alpha').first()
    if not station:
        station = Station(name='Thermal Station Alpha', location='Bay 1')
        db.session.add(station)
        db.session.commit()
        print("Created default station.")
    
    # Assign existing units to the default station
    units = Unit.query.filter(Unit.station_id == None).all()
    for u in units:
        u.station_id = station.id
    
    if units:
        db.session.commit()
        print(f"Migrated {len(units)} units to station {station.name}.")
    else:
        print("No units needed migration.")
        
print("Migration complete.")
