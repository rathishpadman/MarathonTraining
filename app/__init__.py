import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
# Removed Flask-RESTX to prevent routing conflicts
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import atexit
from datetime import timedelta

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
jwt = JWTManager()
socketio = SocketIO()
# Removed api = Api() to prevent routing conflicts
scheduler = BackgroundScheduler()

def create_app():
    app = Flask(__name__, template_folder='../templates')
    
    # Apply proxy fix for Replit
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Load configuration
    from app.config import Config
    app.config.from_object(Config)
    
    # Configure logging
    from app.config import configure_replit_logging
    configure_replit_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    # Disabled SocketIO to improve performance and fix timeout issues
    # socketio.init_app(app, cors_allowed_origins="*")
    # Removed Flask-RESTX initialization to prevent routing conflicts
    
    # Configure JWT
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'default-jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # Setup JWT error handlers
    from app.security import ReplitSecurity
    security = ReplitSecurity()
    security.setup_jwt_handlers(jwt)
    
    # Register main routes (including community dashboard home page) first
    from app.simple_routes import main_bp
    app.register_blueprint(main_bp)
    
    # Register web routes (individual dashboards)
    from app.web_routes import web_bp
    app.register_blueprint(web_bp)
    
    # Register API routes with prefix
    from app.simple_routes import api_bp
    app.register_blueprint(api_bp)
    
    # Create database tables
    with app.app_context():
        # Import models to ensure they are registered
        from app import models
        db.create_all()
        
        # Log successful database initialization
        logging.info("Database tables created successfully")
    
    # Setup scheduler for background tasks
    if not scheduler.running:
        from app.processing_workflows import replit_daily_processing
        from datetime import datetime
        
        # Schedule daily processing at 3 AM
        scheduler.add_job(
            func=lambda: replit_daily_processing(datetime.now().date()),
            trigger='cron',
            hour=3,
            minute=0,
            id='daily_processing'
        )
        
        # Schedule athlete updates every 5 minutes for better performance
        from app.simple_routes import send_athlete_update
        scheduler.add_job(
            func=send_athlete_update,
            trigger='interval',
            minutes=5,
            id='athlete_updates'
        )
        
        scheduler.start()
        logging.info("Background scheduler started")
        
        # Shutdown scheduler when app exits
        atexit.register(lambda: scheduler.shutdown())
    
    return app

# Global error handler
def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_exception(e):
        from app.models import SystemLog, db
        
        # Log the error
        logging.error(f"Unhandled exception: {str(e)}", exc_info=True)
        
        # Try to log to database
        try:
            error_log = SystemLog(
                level='ERROR',
                message=f"Unhandled exception: {str(e)}",
                module='global_error_handler',
                athlete_id=None
            )
            db.session.add(error_log)
            db.session.commit()
        except Exception as db_error:
            logging.error(f"Failed to log error to database: {str(db_error)}")
        
        return {"error": "Internal server error", "message": "An unexpected error occurred"}, 500
