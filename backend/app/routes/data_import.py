import csv
import io
from datetime import datetime, timezone
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.unit import Unit
from app.models.parameter import Parameter
from app.models.reading import Reading
from app.utils.response import success_response, error_response
from app.utils.validators import parse_iso_datetime
from app.utils.decorators import engineer_required

data_import_bp = Blueprint('data_import', __name__, url_prefix='/api/data')

@data_import_bp.route('/import', methods=['POST'])
@jwt_required()
@engineer_required
def import_csv_data():
    """
    Imports historical readings from CSV file.
    Expected format:
    timestamp,unit_code,vibration,pressure,lube_temperature,rpm,load
    """
    if 'file' not in request.files:
        return error_response("MISSING_FILE", "CSV file part 'file' is required in multipart form data.", 400)

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return error_response("INVALID_FORMAT", "File must be a .csv file.", 400)

    stream = io.StringIO(file.stream.read().decode("utf-8-sig", errors='replace'))
    reader = csv.DictReader(stream)

    rows_received = 0
    rows_imported = 0
    rows_rejected = 0
    errors = []

    # Cache units and parameters for performance
    unit_cache = {u.unit_code: u for u in Unit.query.all()}
    param_cache = {}  # (unit_id, param_key) -> Parameter

    for row in reader:
        rows_received += 1
        unit_code = row.get('unit_code', '').strip()
        ts_str = row.get('timestamp', '').strip()

        if not unit_code or not ts_str:
            rows_rejected += 1
            errors.append(f"Row {rows_received}: Missing unit_code or timestamp.")
            continue

        unit = unit_cache.get(unit_code)
        if not unit:
            rows_rejected += 1
            errors.append(f"Row {rows_received}: Turbine unit '{unit_code}' not found.")
            continue

        ts = parse_iso_datetime(ts_str)
        if not ts:
            rows_rejected += 1
            errors.append(f"Row {rows_received}: Invalid timestamp format '{ts_str}'.")
            continue

        # Process each column other than timestamp and unit_code
        row_has_valid_val = False
        for col_key, val_str in row.items():
            col_clean = col_key.strip().lower()
            if col_clean in ('timestamp', 'unit_code') or not val_str:
                continue

            try:
                num_val = float(val_str.strip())
            except ValueError:
                continue

            cache_key = (unit.id, col_clean)
            if cache_key not in param_cache:
                param = Parameter.query.filter_by(unit_id=unit.id, parameter_key=col_clean).first()
                param_cache[cache_key] = param

            param = param_cache[cache_key]
            if not param:
                # Parameter not configured for this unit, ignore column
                continue

            # Validate bounds
            if param.minimum_value is not None and num_val < param.minimum_value:
                continue
            if param.maximum_value is not None and num_val > param.maximum_value:
                continue

            reading = Reading(
                unit_id=unit.id,
                parameter_id=param.id,
                value=num_val,
                timestamp=ts,
                data_source='CSV'
            )
            db.session.add(reading)
            row_has_valid_val = True

        if row_has_valid_val:
            rows_imported += 1
        else:
            rows_rejected += 1

    db.session.commit()

    return success_response({
        'rows_received': rows_received,
        'rows_imported': rows_imported,
        'rows_rejected': rows_rejected,
        'errors': errors[:20]  # truncate error list to top 20
    }, message=f"CSV import complete. {rows_imported} rows imported successfully.")
