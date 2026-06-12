from datetime import datetime, timezone
from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user import User
from app.utils.response import success_response, error_response
from app.utils.validators import validate_email

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username') or data.get('email')
    password = data.get('password')

    if not username or not password:
        return error_response("MISSING_CREDENTIALS", "Username and password are required.", 400)

    # Allow login by username or email
    user = User.query.filter((User.username == username) | (User.email == username)).first()
    if not user or not user.check_password(password):
        return error_response("INVALID_CREDENTIALS", "Invalid username or password.", 401)

    if not user.active:
        return error_response("ACCOUNT_INACTIVE", "This account has been deactivated.", 403)

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id), additional_claims={'role': user.role, 'username': user.username})

    return success_response({
        'access_token': access_token,
        'user': user.to_dict()
    }, message="Login successful.")

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return error_response("USER_NOT_FOUND", "User not found.", 404)
    return success_response({'user': user.to_dict()})

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # Client will discard token; endpoint confirms session teardown
    return success_response(message="Logged out successfully.")
