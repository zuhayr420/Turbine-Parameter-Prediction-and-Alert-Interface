import re
from datetime import datetime

EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

def validate_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    return bool(re.match(EMAIL_REGEX, email.strip()))

def validate_numeric(val, min_val=None, max_val=None):
    try:
        f = float(val)
    except (ValueError, TypeError):
        return False, "Value must be a valid number."
    
    if min_val is not None and f < min_val:
        return False, f"Value {f} is below minimum allowed {min_val}."
    if max_val is not None and f > max_val:
        return False, f"Value {f} is above maximum allowed {max_val}."
    return True, f

def parse_iso_datetime(dt_str: str):
    try:
        # Handle 'Z' or offset
        clean_str = dt_str.replace('Z', '+00:00')
        return datetime.fromisoformat(clean_str)
    except Exception:
        return None
