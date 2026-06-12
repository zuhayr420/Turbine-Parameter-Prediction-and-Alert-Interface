from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.user import User
from app.utils.response import success_response, error_response
from app.utils.decorators import admin_required
from app.utils.validators import validate_email

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('', methods=['GET'])
@jwt_required()
@admin_required
def list_users():
    users = User.query.all()
    return success_response({'users': [u.to_dict() for u in users]})

@users_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_user():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'operator').lower()

    if not username or not email or not password:
        return error_response("MISSING_FIELDS", "username, email, and password are required.", 400)

    if not validate_email(email):
        return error_response("INVALID_EMAIL", "Invalid email address format.", 400)

    if role not in ('admin', 'engineer', 'operator'):
        return error_response("INVALID_ROLE", "Role must be admin, engineer, or operator.", 400)

    if User.query.filter_by(username=username).first():
        return error_response("USERNAME_TAKEN", f"Username '{username}' already exists.", 409)

    if User.query.filter_by(email=email).first():
        return error_response("EMAIL_TAKEN", f"Email '{email}' already registered.", 409)

    user = User(username=username, email=email, role=role, active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return success_response({'user': user.to_dict()}, message="User created successfully.", status_code=201)

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response("USER_NOT_FOUND", "User not found.", 404)

    data = request.get_json() or {}
    if 'role' in data:
        role = data['role'].lower()
        if role not in ('admin', 'engineer', 'operator'):
            return error_response("INVALID_ROLE", "Invalid role.", 400)
        user.role = role

    if 'active' in data:
        user.active = bool(data['active'])

    if 'password' in data and data['password']:
        user.set_password(data['password'])

    db.session.commit()
    return success_response({'user': user.to_dict()}, message="User updated.")

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response('USER_NOT_FOUND', 'User not found.', 404)
    if user.role == 'admin':
        admins = User.query.filter_by(role='admin').count()
        if admins <= 1:
            return error_response('CANNOT_DELETE_LAST_ADMIN', 'Cannot delete the only admin.', 400)
    db.session.delete(user)
    db.session.commit()
    return success_response(message='User deleted successfully.')
