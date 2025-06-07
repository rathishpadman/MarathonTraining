import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from flask_restx import Api, Resource, fields, Namespace
from flask_socketio import emit, join_room, leave_room
from app import db, socketio
from app.models import ReplitAthlete, DailySummary, Activity, PlannedWorkout, SystemLog
from app.data_processor import get_athlete_performance_summary, get_team_overview
from app.security import ReplitSecurity
from app.strava_client import ReplitStravaClient
from app.config import Config

# Create blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')
api = Api(api_bp, title='Marathon Training API', version='1.0')

# Initialize components
config = Config()
security = ReplitSecurity()
strava_client = ReplitStravaClient(config.STRAVA_CLIENT_ID, config.STRAVA_CLIENT_SECRET)
logger = logging.getLogger(__name__)

# API Models for documentation and validation
athlete_model = api.model('Athlete', {
    'id': fields.Integer(required=True),
    'name': fields.String(required=True),
    'email': fields.String(required=True),
    'strava_athlete_id': fields.Integer(required=True),
    'is_active': fields.Boolean(required=True),
    'created_at': fields.DateTime(required=True)
})

daily_summary_model = api.model('DailySummary', {
    'id': fields.Integer(required=True),
    'summary_date': fields.DateTime(required=True),
    'total_distance': fields.Float(required=True),
    'total_moving_time': fields.Integer(required=True),
    'activity_count': fields.Integer(required=True),
    'status': fields.String(required=True),
    'training_load': fields.Float(),
    'average_pace': fields.Float(),
    'insights': fields.Raw()
})

# Create namespace for athletes
athletes_ns = Namespace('athletes', description='Athlete operations')
api.add_namespace(athletes_ns)

@athletes_ns.route('')
class AthletesResource(Resource):
    @api.marshal_list_with(athlete_model)
    @jwt_required()
    def get(self):
        """Get all athletes or current user's athlete data"""
        try:
            current_user_id = get_jwt_identity()
            logger.info(f"Fetching athletes for user {current_user_id}")
            
            # For now, assume all users can see all athletes (team view)
            # In production, you might want to implement role-based access
            athletes = db.session.query(ReplitAthlete).filter_by(is_active=True).all()
            
            logger.info(f"Retrieved {len(athletes)} active athletes")
            return athletes
            
        except Exception as e:
            logger.error(f"Error fetching athletes: {str(e)}")
            return {'error': 'Failed to fetch athletes'}, 500

@athletes_ns.route('/<int:athlete_id>/dashboard-data')
class AthleteDashboardResource(Resource):
    @api.marshal_list_with(daily_summary_model)
    @jwt_required()
    def get(self, athlete_id):
        """Get dashboard data for a specific athlete"""
        try:
            current_user_id = get_jwt_identity()
            logger.info(f"Dashboard data requested for athlete {athlete_id} by user {current_user_id}")
            
            # Strict authorization check
            if not security.validate_athlete_access(current_user_id, athlete_id):
                logger.warning(f"Access denied: user {current_user_id} tried to access athlete {athlete_id}")
                return {'error': 'Forbidden', 'message': 'Access denied to athlete data'}, 403
            
            # Get performance summary
            performance_data = get_athlete_performance_summary(db.session, athlete_id)
            
            if not performance_data:
                logger.warning(f"No performance data found for athlete {athlete_id}")
                return {'message': 'No performance data available'}, 404
            
            # Get recent daily summaries
            recent_summaries = db.session.query(DailySummary).filter(
                DailySummary.athlete_id == athlete_id
            ).order_by(DailySummary.summary_date.desc()).limit(30).all()
            
            logger.info(f"Retrieved dashboard data for athlete {athlete_id}: {len(recent_summaries)} summaries")
            return recent_summaries
            
        except Exception as e:
            logger.error(f"Error fetching dashboard data for athlete {athlete_id}: {str(e)}")
            return {'error': 'Failed to fetch dashboard data'}, 500

# Create namespace for real-time data
realtime_ns = Namespace('realtime', description='Real-time operations')
api.add_namespace(realtime_ns)

@realtime_ns.route('/dashboard')
class RealtimeDashboardResource(Resource):
    @jwt_required()
    def get(self):
        """Get lightweight real-time dashboard data"""
        try:
            current_user_id = get_jwt_identity()
            logger.info(f"Real-time dashboard data requested by user {current_user_id}")
            
            # Get lightweight data for current user
            lightweight_data = get_lightweight_update(current_user_id)
            
            logger.info(f"Real-time data retrieved for user {current_user_id}")
            return lightweight_data
            
        except Exception as e:
            logger.error(f"Error fetching real-time data for user {current_user_id}: {str(e)}")
            return {'error': 'Failed to fetch real-time data'}, 500

# Authentication endpoints
auth_ns = Namespace('auth', description='Authentication operations')
api.add_namespace(auth_ns)

@auth_ns.route('/strava/authorize')
class StravaAuthResource(Resource):
    def get(self):
        """Get Strava authorization URL"""
        try:
            redirect_uri = request.args.get('redirect_uri', 'http://localhost:5000/api/auth/strava/callback')
            
            auth_url = strava_client.get_authorization_url(
                redirect_uri=redirect_uri,
                scope=['read', 'activity:read']
            )
            
            logger.info(f"Generated Strava authorization URL")
            return {'authorization_url': auth_url}
            
        except Exception as e:
            logger.error(f"Error generating Strava auth URL: {str(e)}")
            return {'error': 'Failed to generate authorization URL'}, 500

@auth_ns.route('/strava/callback')
class StravaCallbackResource(Resource):
    def post(self):
        """Handle Strava OAuth callback"""
        try:
            data = request.get_json()
            code = data.get('code')
            
            if not code:
                return {'error': 'Authorization code required'}, 400
            
            # Exchange code for tokens
            token_data = strava_client.exchange_code_for_token(code)
            
            # Check if athlete already exists
            existing_athlete = db.session.query(ReplitAthlete).filter_by(
                strava_athlete_id=token_data['athlete_id']
            ).first()
            
            if existing_athlete:
                # Update existing athlete tokens
                existing_athlete.access_token = token_data['access_token']
                existing_athlete.refresh_token = token_data['refresh_token']
                existing_athlete.token_expires_at = token_data['expires_at']
                athlete_id = existing_athlete.id
            else:
                # Create new athlete record
                new_athlete = ReplitAthlete(
                    name=f"Athlete {token_data['athlete_id']}",  # Default name
                    email=f"athlete{token_data['athlete_id']}@example.com",  # Default email
                    strava_athlete_id=token_data['athlete_id'],
                    access_token=token_data['access_token'],
                    refresh_token=token_data['refresh_token'],
                    token_expires_at=token_data['expires_at']
                )
                db.session.add(new_athlete)
                db.session.flush()  # Get the ID
                athlete_id = new_athlete.id
            
            db.session.commit()
            
            # Create JWT tokens
            jwt_tokens = security.create_tokens(athlete_id)
            
            logger.info(f"Strava authentication successful for athlete {athlete_id}")
            
            return {
                'message': 'Authentication successful',
                'athlete_id': athlete_id,
                'tokens': jwt_tokens
            }
            
        except Exception as e:
            logger.error(f"Error in Strava callback: {str(e)}")
            db.session.rollback()
            return {'error': 'Authentication failed'}, 500

# WebSocket event handlers
@socketio.on('join_dashboard_room')
def handle_join_dashboard_room(data):
    """Handle client joining a dashboard room for real-time updates"""
    try:
        athlete_id = data.get('athlete_id')
        jwt_token = data.get('jwt_token')
        
        if not athlete_id or not jwt_token:
            logger.warning("Missing athlete_id or jwt_token in join_dashboard_room")
            emit('error', {'message': 'Missing required parameters'})
            return
        
        # Verify token identity
        if security.verify_token_identity(jwt_token, athlete_id):
            # Join the athlete-specific room
            room = f"athlete_{athlete_id}"
            join_room(room)
            
            # Send initial dashboard data
            initial_data = get_lightweight_update(athlete_id)
            emit('dashboard_refresh', initial_data)
            
            logger.info(f"Client joined dashboard room for athlete {athlete_id}")
            emit('joined', {'room': room, 'athlete_id': athlete_id})
            
        else:
            logger.warning(f"Token verification failed for athlete {athlete_id}")
            emit('error', {'message': 'Authentication failed'})
            
    except Exception as e:
        logger.error(f"Error in join_dashboard_room: {str(e)}")
        emit('error', {'message': 'Failed to join dashboard room'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected from WebSocket")

# Helper functions for real-time updates
def send_athlete_update():
    """Send updates to all connected athletes (called by scheduler)"""
    try:
        # Get all active athletes
        active_athletes = db.session.query(ReplitAthlete).filter_by(is_active=True).all()
        
        for athlete in active_athletes:
            try:
                # Get lightweight update for this athlete
                update_data = get_lightweight_update(athlete.id)
                
                # Emit to athlete's room
                room = f"athlete_{athlete.id}"
                socketio.emit('dashboard_refresh', update_data, room=room)
                
            except Exception as e:
                logger.error(f"Error sending update to athlete {athlete.id}: {str(e)}")
        
        logger.info(f"Sent updates to {len(active_athletes)} athletes")
        
    except Exception as e:
        logger.error(f"Error in send_athlete_update: {str(e)}")

def get_lightweight_update(athlete_id):
    """Get lightweight data for real-time updates"""
    try:
        # Get recent performance data
        performance_data = get_cached_performance(athlete_id)
        
        # Get upcoming workouts
        upcoming_workouts = get_upcoming_workouts(athlete_id)
        
        # Get recent notifications
        recent_notifications = get_recent_notifications(athlete_id)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'athlete_id': athlete_id,
            'performance': performance_data,
            'upcoming': upcoming_workouts,
            'notifications': recent_notifications
        }
        
    except Exception as e:
        logger.error(f"Error getting lightweight update for athlete {athlete_id}: {str(e)}")
        return {
            'timestamp': datetime.now().isoformat(),
            'athlete_id': athlete_id,
            'error': 'Failed to fetch update'
        }

def get_cached_performance(athlete_id):
    """Get cached performance metrics for quick access"""
    try:
        # Get latest daily summary
        latest_summary = db.session.query(DailySummary).filter(
            DailySummary.athlete_id == athlete_id
        ).order_by(DailySummary.summary_date.desc()).first()
        
        if latest_summary:
            return {
                'latest_date': latest_summary.summary_date.isoformat(),
                'total_distance': latest_summary.total_distance,
                'status': latest_summary.status,
                'training_load': latest_summary.training_load
            }
        
        return {'message': 'No recent performance data'}
        
    except Exception as e:
        logger.error(f"Error getting cached performance for athlete {athlete_id}: {str(e)}")
        return {'error': 'Failed to fetch performance data'}

def get_upcoming_workouts(athlete_id):
    """Get upcoming planned workouts"""
    try:
        tomorrow = datetime.now().date() + timedelta(days=1)
        next_week = tomorrow + timedelta(days=7)
        
        upcoming = db.session.query(PlannedWorkout).filter(
            PlannedWorkout.athlete_id == athlete_id,
            PlannedWorkout.planned_date >= tomorrow,
            PlannedWorkout.planned_date <= next_week,
            PlannedWorkout.is_completed == False
        ).order_by(PlannedWorkout.planned_date).limit(5).all()
        
        workouts = []
        for workout in upcoming:
            workouts.append({
                'id': workout.id,
                'date': workout.planned_date.isoformat(),
                'type': workout.workout_type,
                'distance': workout.planned_distance,
                'duration': workout.planned_duration
            })
        
        return workouts
        
    except Exception as e:
        logger.error(f"Error getting upcoming workouts for athlete {athlete_id}: {str(e)}")
        return []

def get_recent_notifications(athlete_id):
    """Get recent notifications for an athlete"""
    try:
        from app.models import NotificationLog
        
        recent = db.session.query(NotificationLog).filter(
            NotificationLog.athlete_id == athlete_id
        ).order_by(NotificationLog.sent_at.desc()).limit(5).all()
        
        notifications = []
        for notification in recent:
            notifications.append({
                'id': notification.id,
                'type': notification.notification_type,
                'subject': notification.subject,
                'sent_at': notification.sent_at.isoformat(),
                'status': notification.status
            })
        
        return notifications
        
    except Exception as e:
        logger.error(f"Error getting recent notifications for athlete {athlete_id}: {str(e)}")
        return []

def get_athlete_list_from_api():
    """Get list of athletes for Streamlit dropdown (called from frontend)"""
    try:
        athletes = db.session.query(ReplitAthlete).filter_by(is_active=True).all()
        
        athlete_list = ["Team Overview"]  # Add team overview option
        for athlete in athletes:
            athlete_list.append(athlete.name)
        
        return athlete_list
        
    except Exception as e:
        logger.error(f"Error getting athlete list: {str(e)}")
        return ["Team Overview"]
