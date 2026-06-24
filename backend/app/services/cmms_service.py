import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def dispatch_cmms_work_order(alert):
    """
    Mock integration to an Enterprise CMMS (e.g., SAP PM, IBM Maximo).
    This simulates creating a work order when a CRITICAL predictive alert is triggered.
    """
    if alert.severity != 'CRITICAL':
        return False

    payload = {
        "equipment_id": alert.unit.unit_code,
        "priority": "HIGH",
        "order_type": "PREDICTIVE_MAINTENANCE",
        "description": f"Predictive threshold breach detected for {alert.parameter.name}",
        "expected_failure_time": alert.expected_breach_time.isoformat() if alert.expected_breach_time else None,
        "triggered_at": datetime.now(timezone.utc).isoformat()
    }
    
    # In a real scenario, this would be an HTTP POST to SAP/Maximo REST APIs
    logger.info(f"[CMMS MOCK] Dispatched work order to SAP PM: {json.dumps(payload)}")
    return True
