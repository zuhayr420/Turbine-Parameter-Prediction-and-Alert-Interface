import os
import logging
from flask import Flask, jsonify
from app.extensions import db, jwt, cors, socketio
from config import config_by_name

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    socketio.init_app(app)

    # Ensure model and data directories exist
    os.makedirs(app.config['MODEL_DIRECTORY'], exist_ok=True)
    if 'sqlite:///' in app.config['SQLALCHEMY_DATABASE_URI']:
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not db_path.startswith(':memory:'):
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    # Register blueprints
    from app.routes import (
        auth_bp, users_bp, units_bp, parameters_bp,
        readings_bp, predictions_bp, alerts_bp, reports_bp,
        dashboard_bp, models_mgmt_bp, data_import_bp, system_bp, stations_bp
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(units_bp)
    app.register_blueprint(parameters_bp)
    app.register_blueprint(readings_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(models_mgmt_bp)
    app.register_blueprint(data_import_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(stations_bp)

    # Global error handlers
    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({
            'success': False,
            'error': {'code': 'RESOURCE_NOT_FOUND', 'message': 'Requested endpoint or resource not found.'}
        }), 404

    @app.errorhandler(500)
    def handle_500(e):
        app.logger.error(f"Internal server error: {e}")
        return jsonify({
            'success': False,
            'error': {'code': 'INTERNAL_SERVER_ERROR', 'message': 'An internal error occurred.'}
        }), 500

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'error': {'code': 'TOKEN_EXPIRED', 'message': 'The authentication token has expired.'}
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'success': False,
            'error': {'code': 'TOKEN_INVALID', 'message': 'Signature verification failed or token is malformed.'}
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'success': False,
            'error': {'code': 'AUTHORIZATION_REQUIRED', 'message': 'Request does not contain an access token.'}
        }), 401

    return app
