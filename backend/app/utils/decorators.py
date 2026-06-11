from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User
from app.utils.response import error_response

def role_required(allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))
            if not user or not user.active:
                return error_response("ACCOUNT_DISABLED", "User account is inactive or not found.", 403)
            
            if user.role not in allowed_roles:
                return error_response(
                    "INSUFFICIENT_PERMISSIONS",
                    f"Access restricted to {allowed_roles}. Current role is {user.role}.",
                    403
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(fn):
    return role_required(['admin'])(fn)

def engineer_required(fn):
    return role_required(['admin', 'engineer'])(fn)

def audit_action(action_name, resource_name=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from app.extensions import db
            from app.models.audit import AuditLog
            from flask import request
            
            # Execute original function first
            response = fn(*args, **kwargs)
            
            # If successful (assuming tuple of (json, status_code) or just json if 200)
            status_code = response[1] if isinstance(response, tuple) else 200
            if status_code in (200, 201, 204):
                user_id = get_jwt_identity() if request.headers.get('Authorization') else None
                log = AuditLog(
                    user_id=user_id,
                    action=action_name,
                    resource=resource_name or request.endpoint,
                    ip_address=request.remote_addr
                )
                db.session.add(log)
                db.session.commit()
            return response
        return wrapper
    return decorator
