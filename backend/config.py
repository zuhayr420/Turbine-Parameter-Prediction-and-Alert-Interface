import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'turbine-scada-secret-key-prod-change-in-env')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'turbine-scada-jwt-secret-key-change-in-env')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_HOURS', 8)))
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(basedir, 'data', 'turbine_monitoring.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis and Celery
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

    # Machine Learning / Forecasting configuration
    MODEL_DIRECTORY = os.environ.get(
        'MODEL_DIRECTORY',
        os.path.join(basedir, 'app', 'ml', 'models')
    )
    PREDICTION_INTERVAL_MINUTES = int(os.environ.get('PREDICTION_INTERVAL_MINUTES', 15))
    PREDICTION_HORIZON_HOURS = int(os.environ.get('PREDICTION_HORIZON_HOURS', 3))
    HISTORY_WINDOW = int(os.environ.get('HISTORY_WINDOW', 30))

    # Email alerts
    EMAIL_ALERTS_ENABLED = os.environ.get('EMAIL_ALERTS_ENABLED', 'false').lower() in ('true', '1', 't')
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.example.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    ALERT_EMAIL_FROM = os.environ.get('ALERT_EMAIL_FROM', 'alerts@turbine-powerplant.com')
    ALERT_EMAIL_TO = os.environ.get('ALERT_EMAIL_TO', 'engineers@turbine-powerplant.com')


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    EMAIL_ALERTS_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
