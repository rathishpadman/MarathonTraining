import os
import logging
from logging.handlers import RotatingFileHandler
import sys

class Config:
    """Configuration class for the Marathon Training Dashboard"""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key')
    
    # Database configuration - Force SQLite
    SQLALCHEMY_DATABASE_URI = 'sqlite:///marathon.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLite-specific options
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_timeout": 20,
        "pool_recycle": -1,
    }
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET', 'default-jwt-secret-key')
    
    # Strava API configuration
    STRAVA_CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
    STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
    STRAVA_CALLBACK_URL = os.environ.get('STRAVA_CALLBACK_URL')
    
    # AI API configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Mail configuration
    MAIL_SMTP_SERVER = os.environ.get('MAIL_SMTP_SERVER', 'smtp.gmail.com')
    MAIL_SMTP_PORT = int(os.environ.get('MAIL_SMTP_PORT', '587'))
    MAIL_SMTP_USER = os.environ.get('MAIL_SMTP_USER', 'default@email.com')
    MAIL_SMTP_PASSWORD = os.environ.get('MAIL_SMTP_PASSWORD', 'default_password')
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

def configure_replit_logging(app):
    """Configure logging optimized for Replit environment"""
    
    # Set log level
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
    
    # Create custom formatter with athlete_id support
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] [athlete_id:%(athlete_id)s] %(message)s'
    )
    
    # Custom log record factory to inject athlete_id
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.athlete_id = getattr(record, 'athlete_id', 'N/A')
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    # Configure root logger
    logging.basicConfig(level=log_level)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Add file handler for persistent logs
    try:
        file_handler = RotatingFileHandler(
            'marathon_dashboard.log',
            maxBytes=10485760,  # 10MB
            backupCount=3
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        
        # Add handlers to app logger
        app.logger.addHandler(console_handler)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
        
    except Exception as e:
        app.logger.warning(f"Could not create file handler: {e}")
    
    # Suppress noisy SQLAlchemy logs
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    
    app.logger.info("Replit-optimized logging configured successfully")
