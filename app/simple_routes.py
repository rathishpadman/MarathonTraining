import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from flask_socketio import emit, join_room, leave_room
from app import db, socketio
from app.models import ReplitAthlete, DailySummary, Activity, PlannedWorkout, SystemLog
from app.data_processor import get_athlete_performance_summary, get_team_overview
from app.security import ReplitSecurity
from app.strava_client import ReplitStravaClient
from app.config import Config

# Create blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize components
config = Config()
security = ReplitSecurity()
strava_client = ReplitStravaClient(config.STRAVA_CLIENT_ID, config.STRAVA_CLIENT_SECRET)
logger = logging.getLogger(__name__)

# Athletes API endpoint
@api_bp.route('/athletes', methods=['GET'])
@jwt_required()
def get_athletes():
    """Get all athletes or current user's athlete data"""
    try:
        current_user_id = get_jwt_identity()
        logger.info(f"Fetching athletes for user {current_user_id}")
        
        # Get all active athletes
        athletes = db.session.query(ReplitAthlete).filter_by(is_active=True).all()
        
        athlete_list = []
        for athlete in athletes:
            athlete_list.append({
                'id': athlete.id,
                'name': athlete.name,
                'email': athlete.email,
                'strava_athlete_id': athlete.strava_athlete_id,
                'is_active': athlete.is_active,
                'created_at': athlete.created_at.isoformat() if athlete.created_at else None
            })
        
        logger.info(f"Found {len(athlete_list)} active athletes")
        return jsonify(athlete_list)
        
    except Exception as e:
        logger.error(f"Error fetching athletes: {str(e)}")
        return jsonify({'error': 'Failed to fetch athletes'}), 500

# Athlete dashboard data endpoint
@api_bp.route('/athletes/<int:athlete_id>/dashboard-data', methods=['GET'])
@jwt_required()
def get_athlete_dashboard_data(athlete_id):
    """Get dashboard data for a specific athlete"""
    try:
        current_user_id = get_jwt_identity()
        
        # Validate access
        if not security.validate_athlete_access(current_user_id, athlete_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get performance summary
        performance_summary = get_athlete_performance_summary(db.session, athlete_id, days=30)
        
        if not performance_summary:
            return jsonify({'error': 'No data found for athlete'}), 404
        
        # Get recent daily summaries
        recent_summaries = db.session.query(DailySummary)\
            .filter_by(athlete_id=athlete_id)\
            .order_by(DailySummary.summary_date.desc())\
            .limit(7).all()
        
        # Format weekly data for charts
        weekly_data = {
            'labels': [],
            'distance': [],
            'training_load': []
        }
        
        for summary in reversed(recent_summaries):
            weekly_data['labels'].append(summary.summary_date.strftime('%Y-%m-%d'))
            weekly_data['distance'].append(summary.total_distance / 1000)  # Convert to km
            weekly_data['training_load'].append(summary.training_load or 0)
        
        # Status distribution
        status_counts = {}
        for summary in recent_summaries:
            status = summary.status or 'Unknown'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        status_distribution = {
            'labels': list(status_counts.keys()),
            'values': list(status_counts.values())
        }
        
        dashboard_data = {
            'performance_summary': performance_summary,
            'weekly_data': weekly_data,
            'status_distribution': status_distribution
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data for athlete {athlete_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch dashboard data'}), 500

# Realtime dashboard endpoint
@api_bp.route('/realtime/dashboard', methods=['GET'])
@jwt_required()
def get_realtime_dashboard():
    """Get lightweight real-time dashboard data"""
    try:
        current_user_id = get_jwt_identity()
        
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'athlete_id': current_user_id,
            'status': 'active'
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error fetching realtime dashboard: {str(e)}")
        return jsonify({'error': 'Failed to fetch realtime data'}), 500

# Strava authorization endpoint
@api_bp.route('/auth/strava/authorize', methods=['GET'])
def get_strava_auth_url():
    """Get Strava authorization URL"""
    try:
        redirect_uri = request.url_root.rstrip('/') + '/api/auth/strava/callback'
        auth_url = strava_client.get_authorization_url(redirect_uri)
        
        logger.info("Generated Strava authorization URL")
        return jsonify({'authorization_url': auth_url})
        
    except Exception as e:
        logger.error(f"Error generating Strava auth URL: {str(e)}")
        return jsonify({'error': 'Failed to generate authorization URL'}), 500

# Strava callback endpoint
@api_bp.route('/auth/strava/callback', methods=['GET'])
def handle_strava_callback():
    """Handle Strava OAuth callback"""
    try:
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            return jsonify({'error': f'Strava authorization failed: {error}'}), 400
        
        if not code:
            return jsonify({'error': 'Authorization code required'}), 400
        redirect_uri = request.url_root.rstrip('/') + '/api/auth/strava/callback'
        
        # Exchange code for tokens
        token_response = strava_client.exchange_token(code, redirect_uri)
        
        if not token_response:
            return jsonify({'error': 'Failed to exchange authorization code'}), 400
        
        # Get athlete info
        athlete_data = strava_client.get_athlete_info(token_response['access_token'])
        
        if not athlete_data:
            return jsonify({'error': 'Failed to retrieve athlete information'}), 400
        
        # Convert expires_at timestamp to datetime object
        from datetime import datetime
        expires_at = None
        if token_response.get('expires_at'):
            expires_at = datetime.fromtimestamp(token_response['expires_at'])
        
        # Check if athlete exists
        existing_athlete = ReplitAthlete.query.filter_by(
            strava_athlete_id=athlete_data['id']
        ).first()
        
        if existing_athlete:
            # Update existing athlete
            existing_athlete.refresh_token = token_response['refresh_token']
            existing_athlete.access_token = token_response['access_token']
            existing_athlete.token_expires_at = expires_at
            existing_athlete.is_active = True
            athlete = existing_athlete
        else:
            # Create new athlete
            athlete = ReplitAthlete(
                name=f"{athlete_data.get('firstname', '')} {athlete_data.get('lastname', '')}".strip(),
                email=athlete_data.get('email', ''),
                strava_athlete_id=athlete_data['id'],
                refresh_token=token_response['refresh_token'],
                access_token=token_response['access_token'],
                token_expires_at=expires_at,
                is_active=True
            )
            db.session.add(athlete)
        
        db.session.commit()
        
        # Create JWT token
        access_token = create_access_token(identity=athlete.id)
        
        logger.info(f"Athlete {athlete.id} authenticated successfully")
        
        # Redirect to success page with athlete info
        from flask import redirect, url_for
        return redirect(f"/auth/success?athlete_id={athlete.id}&athlete_name={athlete.name}")
        
    except Exception as e:
        logger.error(f"Error in Strava callback: {str(e)}")
        return jsonify({'error': 'Authentication failed'}), 500

# WebSocket event handlers
@socketio.on('join_dashboard_room')
def handle_join_dashboard_room(data):
    """Handle client joining a dashboard room for real-time updates"""
    try:
        athlete_id = data.get('athlete_id')
        if athlete_id:
            room = f"athlete_{athlete_id}"
            join_room(room)
            logger.info(f"Client joined dashboard room for athlete {athlete_id}")
            emit('status', {'msg': f'Joined room for athlete {athlete_id}'})
    except Exception as e:
        logger.error(f"Error joining dashboard room: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected from WebSocket")

# Helper functions for real-time updates
def send_athlete_update():
    """Send updates to all connected athletes (called by scheduler)"""
    from app import create_app
    try:
        app = create_app()
        with app.app_context():
            # Get all active athletes
            active_athletes = db.session.query(ReplitAthlete).filter_by(is_active=True).all()
            
            logger.info(f"Processing updates for {len(active_athletes)} athletes")
            
            for athlete in active_athletes:
                try:
                    # Get lightweight update for this athlete
                    update_data = get_lightweight_update(athlete.id)
                    logger.debug(f"Generated update for athlete {athlete.id}")
                    
                except Exception as e:
                    logger.error(f"Error sending update to athlete {athlete.id}: {str(e)}")
            
            logger.info(f"Completed updates for {len(active_athletes)} athletes")
        
    except Exception as e:
        logger.error(f"Error in send_athlete_update: {str(e)}")

def get_lightweight_update(athlete_id):
    """Get lightweight data for real-time updates"""
    try:
        # Get recent performance data
        performance_data = get_cached_performance(athlete_id)
        
        return {
            'athlete_id': athlete_id,
            'timestamp': datetime.now().isoformat(),
            'metrics': performance_data or {},
            'status': 'updated'
        }
    except Exception as e:
        logger.error(f"Error getting lightweight update for athlete {athlete_id}: {str(e)}")
        return {'error': str(e)}

def get_cached_performance(athlete_id):
    """Get cached performance metrics for quick access"""
    try:
        # Get latest daily summary
        latest_summary = db.session.query(DailySummary)\
            .filter_by(athlete_id=athlete_id)\
            .order_by(DailySummary.summary_date.desc())\
            .first()
        
        if latest_summary:
            return {
                'total_distance': latest_summary.total_distance,
                'training_load': latest_summary.training_load,
                'status': latest_summary.status
            }
        
        return None
    except Exception as e:
        logger.error(f"Error getting cached performance for athlete {athlete_id}: {str(e)}")
        return None

def get_upcoming_workouts(athlete_id):
    """Get upcoming planned workouts"""
    try:
        upcoming = db.session.query(PlannedWorkout)\
            .filter_by(athlete_id=athlete_id, is_completed=False)\
            .filter(PlannedWorkout.planned_date >= datetime.now())\
            .order_by(PlannedWorkout.planned_date)\
            .limit(3).all()
        
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
        # This is a placeholder - implement based on your notification system
        return []
    except Exception as e:
        logger.error(f"Error getting notifications for athlete {athlete_id}: {str(e)}")
        return []

def get_athlete_list_from_api():
    """Get list of athletes for Streamlit dropdown (called from frontend)"""
    try:
        athletes = db.session.query(ReplitAthlete).filter_by(is_active=True).all()
        return [{'id': a.id, 'name': a.name} for a in athletes]
    except Exception as e:
        logger.error(f"Error getting athlete list: {str(e)}")
        return []