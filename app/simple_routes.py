import logging
import numpy as np
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_from_directory, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from flask_socketio import emit, join_room, leave_room
from app import db, socketio
from app.models import ReplitAthlete, DailySummary, Activity, PlannedWorkout, SystemLog
from app.data_processor import get_athlete_performance_summary, get_team_overview
from app.race_predictor_simple import SimpleRacePredictor
from app.industry_standard_race_predictor import predict_race_time_industry_standard
from app.injury_predictor import predict_injury_risk, get_injury_prevention_plan
from app.race_optimizer import optimize_race_performance, get_pacing_strategy, get_training_optimization
from app.security import ReplitSecurity
from app.strava_client import ReplitStravaClient
from app.config import Config
from app.ai_race_advisor import get_race_recommendations
from app.training_load_calculator import get_training_load_metrics
from app.senior_athlete_analytics_simple import get_senior_athlete_analytics_simple
from app.achievement_system import get_athlete_achievements, get_achievement_stats
from app.training_heatmap_simple import generate_training_heatmap

# Create blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Main routes blueprint
main_bp = Blueprint('simple_routes', __name__)

# Configure logger
logger = logging.getLogger(__name__)

@main_bp.route('/')
def home():
    """Home page redirect to community dashboard"""
    try:
        from flask import render_template
        logger.info("Accessing home page")
        return render_template('community_standalone.html')
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}")
        return f"<h1>Error loading home page: {str(e)}</h1>", 500

@main_bp.route('/community')
def community_dashboard():
    """Community dashboard with transparent background"""
    try:
        from flask import render_template
        logger.info("Accessing community dashboard")
        return render_template('community_standalone.html')
    except Exception as e:
        logger.error(f"Error rendering community dashboard: {str(e)}")
        return f"<h1>Error loading dashboard: {str(e)}</h1>", 500

@main_bp.route('/dashboard')
@main_bp.route('/dashboard/<int:athlete_id>')
@main_bp.route('/athlete/<int:athlete_id>')
def athlete_dashboard(athlete_id=1):
    """Individual athlete analytics dashboard"""
    try:
        from flask import render_template
        logger.info(f"Accessing athlete dashboard for athlete {athlete_id}")
        return render_template('athlete_dashboard.html', athlete_id=athlete_id)
    except Exception as e:
        logger.error(f"Error rendering athlete dashboard: {str(e)}")
        return f"<h1>Error loading dashboard: {str(e)}</h1>", 500

@main_bp.route('/race_predictor')
@main_bp.route('/race_predictor/<int:athlete_id>')
def race_predictor(athlete_id=1):
    """Race performance predictor page"""
    try:
        from flask import render_template
        logger.info(f"Accessing race predictor for athlete {athlete_id}")
        return render_template('race_predictor.html', athlete_id=athlete_id)
    except Exception as e:
        logger.error(f"Error rendering race predictor: {str(e)}")
        return f"<h1>Error loading race predictor: {str(e)}</h1>", 500

@main_bp.route('/analytics')
@main_bp.route('/analytics/<int:athlete_id>')
def risk_analyser(athlete_id=1):
    """Injury risk analysis page"""
    try:
        from flask import render_template
        logger.info(f"Accessing risk analyser for athlete {athlete_id}")
        return render_template('risk_analyser.html', athlete_id=athlete_id)
    except Exception as e:
        logger.error(f"Error rendering risk analyser: {str(e)}")
        return f"<h1>Error loading risk analyser: {str(e)}</h1>", 500

@main_bp.route('/achievements')
@main_bp.route('/achievements/<int:athlete_id>')
def achievements(athlete_id=None):
    """Training achievement stickers page"""
    try:
        from flask import render_template, request
        # Check for athlete parameter in URL query string
        if not athlete_id:
            athlete_id = request.args.get('athlete', type=int)
        
        if athlete_id:
            logger.info(f"Accessing achievements page for athlete {athlete_id}")
        else:
            logger.info("Accessing achievements page")
        return render_template('achievements.html', athlete_id=athlete_id)
    except Exception as e:
        logger.error(f"Error rendering achievements page: {str(e)}")
        return f"<h1>Error loading achievements: {str(e)}</h1>", 500

@main_bp.route('/auth/status')
def auth_status():
    """Check authentication status for current user"""
    try:
        # Check if there are any active athletes
        active_athletes = db.session.query(ReplitAthlete).filter_by(is_active=True).all()
        
        if active_athletes:
            # Return authenticated status with athlete info
            return jsonify({
                'authenticated': True,
                'athlete_count': len(active_athletes),
                'message': 'Athletes connected'
            })
        else:
            # No active athletes found
            return jsonify({
                'authenticated': False,
                'athlete_count': 0,
                'message': 'No athletes connected'
            })
            
    except Exception as e:
        logger.error(f"Error checking auth status: {str(e)}")
        return jsonify({
            'authenticated': False,
            'error': 'Failed to check authentication status'
        }), 500

@main_bp.route('/connect/strava')
def strava_connect():
    """Strava connection page"""
    try:
        from flask import render_template, request
        logger.info("Accessing Strava connection page")
        
        # Generate Strava authorization URL
        redirect_uri = request.url_root.rstrip('/') + '/api/auth/strava/callback'
        auth_url = strava_client.get_authorization_url(redirect_uri, scope="read,activity:read")
        
        return render_template('strava_connect.html', auth_url=auth_url)
    except Exception as e:
        logger.error(f"Error rendering Strava connect page: {str(e)}")
        return f"<h1>Error loading Strava connection: {str(e)}</h1>", 500

# Initialize components
config = Config()
security = ReplitSecurity()
strava_client = ReplitStravaClient(config.STRAVA_CLIENT_ID, config.STRAVA_CLIENT_SECRET)
logger = logging.getLogger(__name__)

# Athletes API endpoint
@api_bp.route('/athletes', methods=['GET'])
def get_athletes():
    """Get all athletes or current user's athlete data"""
    try:
        logger.info("Fetching all active athletes")
        
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

# Athlete summary endpoint for analytics dashboard
@api_bp.route('/athletes/<int:athlete_id>/summary', methods=['GET'])
def get_athlete_summary(athlete_id):
    """Get athlete summary data for analytics dashboard"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get athlete
        athlete = db.session.query(ReplitAthlete).filter_by(id=athlete_id).first()
        if not athlete:
            return jsonify({'error': 'Athlete not found'}), 404
        
        # Get recent activities
        start_date = datetime.now() - timedelta(days=days)
        activities = db.session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= start_date
        ).all()
        
        # Calculate summary metrics
        total_distance = sum(a.distance or 0 for a in activities) / 1000  # Convert to km
        total_time = sum(a.moving_time or 0 for a in activities) / 3600  # Convert to hours
        activity_count = len(activities)
        avg_pace = (total_time * 60 / total_distance) if total_distance > 0 else 0  # min/km
        
        # Get recent heart rate data
        hr_activities = [a for a in activities if a.average_heartrate]
        avg_hr = sum(a.average_heartrate for a in hr_activities) / len(hr_activities) if hr_activities else 0
        
        # Calculate training load (simplified)
        training_load = sum(
            (a.moving_time or 0) * (a.average_heartrate or 120) / 3600 
            for a in activities
        ) / 100 if activities else 0
        
        # Get latest daily summary for status
        latest_summary = db.session.query(DailySummary).filter(
            DailySummary.athlete_id == athlete_id
        ).order_by(DailySummary.summary_date.desc()).first()
        
        status = latest_summary.status if latest_summary else "No Data"
        
        summary_data = {
            'athlete_name': athlete.name,
            'total_distance': round(total_distance, 1),
            'total_time': round(total_time, 1),
            'activity_count': activity_count,
            'avg_pace': round(avg_pace, 2) if avg_pace > 0 else 0,
            'avg_heart_rate': round(avg_hr, 0) if avg_hr > 0 else 0,
            'training_load': round(training_load, 1),
            'status': status,
            'period_days': days
        }
        
        return jsonify(summary_data)
        
    except Exception as e:
        logger.error(f"Error getting athlete summary: {str(e)}")
        return jsonify({'error': 'Failed to get athlete summary'}), 500

# Original endpoint definitions removed - using enhanced versions below

# Recent activities endpoint
@api_bp.route('/athletes/<int:athlete_id>/recent-activities', methods=['GET'])
def get_recent_activities(athlete_id):
    """Get recent activities for athlete"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        activities = db.session.query(Activity).filter(
            Activity.athlete_id == athlete_id
        ).order_by(Activity.start_date.desc()).limit(limit).all()
        
        activities_data = []
        for activity in activities:
            pace = 0
            if activity.distance and activity.moving_time and activity.distance > 0:
                pace = (activity.moving_time / 60) / (activity.distance / 1000)
            
            activities_data.append({
                'name': activity.name,
                'date': activity.start_date.strftime('%Y-%m-%d'),
                'distance': round((activity.distance or 0) / 1000, 2),
                'time': round((activity.moving_time or 0) / 60, 0),
                'pace': round(pace, 2) if pace > 0 else 0,
                'sport_type': activity.sport_type
            })
        
        return jsonify(activities_data)
        
    except Exception as e:
        logger.error(f"Error getting recent activities: {str(e)}")
        return jsonify({'error': 'Failed to get recent activities'}), 500

# Performance insights endpoint
@api_bp.route('/athletes/<int:athlete_id>/performance-insights', methods=['GET'])
def get_performance_insights(athlete_id):
    """Get performance insights for athlete"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        activities = db.session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= start_date
        ).all()
        
        if not activities:
            return jsonify({
                'volume_trend': 'No data available',
                'consistency': 'No data available',
                'intensity': 'No data available'
            })
        
        # Calculate insights
        total_distance = sum(a.distance or 0 for a in activities) / 1000
        activity_count = len(activities)
        consistency = f"{activity_count} activities in {days} days"
        
        # Volume trend (compare to previous period)
        prev_start = start_date - timedelta(days=days)
        prev_activities = db.session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= prev_start,
            Activity.start_date < start_date
        ).all()
        
        prev_distance = sum(a.distance or 0 for a in prev_activities) / 1000
        if prev_distance > 0:
            volume_change = ((total_distance - prev_distance) / prev_distance) * 100
            volume_trend = f"{volume_change:+.1f}% vs previous {days} days"
        else:
            volume_trend = "First training period"
        
        # Intensity analysis
        hr_activities = [a for a in activities if a.average_heartrate]
        if hr_activities:
            avg_hr = sum(a.average_heartrate for a in hr_activities) / len(hr_activities)
            intensity = f"Average HR: {avg_hr:.0f} bpm"
        else:
            intensity = "No heart rate data"
        
        return jsonify({
            'volume_trend': volume_trend,
            'consistency': consistency,
            'intensity': intensity
        })
        
    except Exception as e:
        logger.error(f"Error getting performance insights: {str(e)}")
        return jsonify({'error': 'Failed to get performance insights'}), 500

@main_bp.route('/api/race/periodized-prediction/<int:athlete_id>', methods=['GET'])
def get_periodized_race_prediction(athlete_id):
    """Get race prediction with training duration and progression analysis"""
    try:
        # Get parameters from request
        race_distance_km = float(request.args.get('distance', 42.195))
        weeks_to_race = int(request.args.get('weeks', 12))
        target_improvement = request.args.get('target_improvement', type=float)
        
        logger.info(f"Generating periodized prediction for athlete {athlete_id}: {race_distance_km}km in {weeks_to_race} weeks")
        
        # Import and use periodized predictor
        from app.periodized_race_predictor import periodized_predictor
        
        prediction = periodized_predictor.predict_race_performance_with_training_duration(
            db.session, 
            athlete_id, 
            race_distance_km, 
            weeks_to_race,
            target_improvement
        )
        
        # Format response for frontend
        formatted_prediction = {
            'athlete_id': athlete_id,
            'race_distance_km': race_distance_km,
            'weeks_to_race': weeks_to_race,
            'current_baseline': {
                'weekly_volume_km': prediction.get('baseline_fitness', {}).get('weekly_volume_km', 0),
                'avg_pace_per_km': prediction.get('baseline_fitness', {}).get('avg_pace_per_km', 0),
                'threshold_pace_per_km': prediction.get('baseline_fitness', {}).get('threshold_pace_per_km', 0),
                'athlete_level': prediction.get('athlete_level', 'intermediate')
            },
            'race_prediction': {
                'predicted_time_seconds': prediction['predicted_race_time_seconds'],
                'predicted_time_formatted': format_seconds_to_time(prediction['predicted_race_time_seconds']),
                'predicted_pace_per_km': prediction['predicted_race_pace_per_km'],
                'confidence_score': prediction['confidence_score']
            },
            'improvement_analysis': {
                'total_improvement_percent': prediction.get('improvement_potential', {}).get('final_improvement_percent', 0) * 100,
                'athlete_level': prediction.get('improvement_potential', {}).get('athlete_level', 'intermediate'),
                'form_factor': prediction.get('improvement_potential', {}).get('form_factor', 1.0),
                'consistency_factor': prediction.get('improvement_potential', {}).get('consistency_factor', 1.0)
            },
            'training_adaptations': prediction.get('training_adaptation', {}),
            'progressive_milestones': prediction.get('progressive_milestones', []),
            'methodology': prediction['methodology']
        }
        
        return jsonify(formatted_prediction)
        
    except Exception as e:
        logger.error(f"Error generating periodized prediction: {str(e)}")
        return jsonify({'error': 'Failed to generate prediction', 'details': str(e)}), 500

def format_seconds_to_time(seconds):
    """Helper function to format seconds into HH:MM:SS or MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"

@main_bp.route('/api/athletes/<int:athlete_id>/recent-activities')
def get_athlete_recent_activities(athlete_id):
    """Get recent activities for athlete"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # Get athlete
        athlete = db.session.query(ReplitAthlete).filter_by(id=athlete_id).first()
        if not athlete:
            return jsonify({'error': 'Athlete not found'}), 404
        
        # Get recent activities
        activities = db.session.query(Activity).filter(
            Activity.athlete_id == athlete_id
        ).order_by(Activity.start_date.desc()).limit(limit).all()
        
        # Format activities for response
        activities_data = []
        for activity in activities:
            activities_data.append({
                'id': activity.id,
                'name': activity.name,
                'sport_type': activity.sport_type,
                'start_date': activity.start_date.isoformat() if activity.start_date else None,
                'distance': activity.distance,
                'moving_time': activity.moving_time,
                'elapsed_time': activity.elapsed_time,
                'average_speed': activity.average_speed,
                'average_heartrate': activity.average_heartrate,
                'max_heartrate': activity.max_heartrate,
                'calories': activity.calories,
                'total_elevation_gain': activity.total_elevation_gain
            })
        
        return jsonify({
            'activities': activities_data,
            'athlete_name': athlete.name,
            'total_count': len(activities_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching recent activities for athlete {athlete_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch recent activities'}), 500

@api_bp.route('/athletes/<int:athlete_id>/senior-analytics')
def get_senior_athlete_analytics(athlete_id):
    """Get advanced analytics for senior athletes (35+)"""
    try:
        days = request.args.get('days', 30, type=int)
        
        logger.info(f"Fetching senior athlete analytics for athlete {athlete_id} over {days} days")
        
        # Use simplified analytics that work with existing SQLite database
        analytics_data = get_senior_athlete_analytics_simple(db.session, athlete_id, days)
        
        if 'error' in analytics_data:
            return jsonify(analytics_data), 500
        
        return jsonify(analytics_data)
        
    except Exception as e:
        logger.error(f"Error fetching senior analytics for athlete {athlete_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch senior analytics', 'details': str(e)}), 500

# AI Race Recommendations endpoint
@api_bp.route('/athletes/<int:athlete_id>/ai-race-recommendations', methods=['POST'])
def get_ai_race_recommendations(athlete_id):
    """Get AI-powered race recommendations for specific activity data"""
    try:
        # Get request data
        request_data = request.get_json()
        current_activity = {
            'distance': request_data.get('distance', 0),
            'heart_rate': request_data.get('heart_rate', 0),
            'pace': request_data.get('pace', 0)
        }
        
        # Get athlete dashboard data
        athlete = ReplitAthlete.query.filter_by(id=athlete_id, is_active=True).first()
        if not athlete:
            return jsonify({'error': 'Athlete not found'}), 404
        
        # Get recent activities for context
        recent_activities = Activity.query.filter_by(athlete_id=athlete_id).order_by(
            Activity.start_date.desc()
        ).limit(14).all()
        
        # Calculate metrics - only include distance-based activities for distance calculation
        distance_activities = [a for a in recent_activities if a.distance and a.distance > 0]
        total_distance_km = sum(a.distance or 0 for a in distance_activities) / 1000
        total_activities = len(recent_activities)
        total_time = sum(a.moving_time or 0 for a in distance_activities)
        
        avg_pace_min_km = 0
        if total_distance_km > 0 and total_time > 0:
            pace_seconds_per_km = total_time / total_distance_km
            avg_pace_min_km = pace_seconds_per_km / 60
        
        hr_activities = [a for a in recent_activities if a.average_heartrate]
        avg_heart_rate = sum(a.average_heartrate for a in hr_activities) / len(hr_activities) if hr_activities else 0
        
        # Calculate training load
        training_load = 0
        for activity in recent_activities:
            if activity.moving_time and activity.average_heartrate:
                duration_min = activity.moving_time / 60
                avg_hr = activity.average_heartrate
                hr_reserve_factor = max(0, (avg_hr - 60) / (190 - 60))
                activity_load = duration_min * hr_reserve_factor * 1.92
                training_load += activity_load
        
        # Prepare athlete data for AI
        athlete_data = {
            'athlete': {
                'id': athlete.id,
                'name': athlete.name
            },
            'metrics': {
                'total_distance': round(total_distance_km, 2),
                'total_activities': total_activities,
                'avg_pace': round(avg_pace_min_km, 2),
                'training_load': round(training_load, 1),
                'avg_heart_rate': round(avg_heart_rate, 1) if avg_heart_rate > 0 else 0,
                'total_time': total_time
            },
            'performance_summary': {
                'activities': [{
                    'distance': round((a.distance or 0) / 1000, 2),
                    'moving_time': a.moving_time or 0,
                    'average_heartrate': a.average_heartrate
                } for a in recent_activities]
            }
        }
        
        # Get AI recommendations
        recommendations = get_race_recommendations(athlete_data, current_activity)
        
        return jsonify({
            'recommendations': recommendations,
            'athlete_name': athlete.name,
            'current_activity': current_activity
        })
        
    except Exception as e:
        logger.error(f"Error getting AI race recommendations: {str(e)}")
        return jsonify({'error': 'Failed to get race recommendations'}), 500

# Athlete dashboard data endpoint
@api_bp.route('/athletes/<int:athlete_id>/dashboard-data', methods=['GET'])
def get_athlete_dashboard_data(athlete_id):
    """Get dashboard data for a specific athlete"""
    try:
        logger.info(f"Fetching dashboard data for athlete {athlete_id}")
        
        # Get athlete record
        athlete = ReplitAthlete.query.filter_by(id=athlete_id, is_active=True).first()
        if not athlete:
            return jsonify({'error': 'Athlete not found'}), 404
        
        # Try to fetch fresh data from Strava if no local data exists
        activities = Activity.query.filter_by(athlete_id=athlete_id).limit(1).all()
        
        if not activities and athlete.access_token:
            # Fetch activities from Strava
            try:
                strava_activities = strava_client.get_activities(athlete.access_token, per_page=10)
                if strava_activities:
                    # Save activities to database
                    saved_count = 0
                    for activity_data in strava_activities:
                        try:
                            existing_activity = Activity.query.filter_by(
                                strava_activity_id=activity_data['id']
                            ).first()
                            
                            if not existing_activity:
                                # Parse datetime properly
                                start_date_str = activity_data.get('start_date_local', activity_data.get('start_date', ''))
                                if start_date_str:
                                    # Remove timezone suffix and parse
                                    start_date_clean = start_date_str.replace('Z', '').replace('+00:00', '')
                                    if 'T' in start_date_clean:
                                        start_date = datetime.fromisoformat(start_date_clean)
                                    else:
                                        start_date = datetime.now()
                                else:
                                    start_date = datetime.now()
                                
                                # Create activity with safe data conversion
                                activity = Activity()
                                activity.strava_activity_id = activity_data['id']
                                activity.athlete_id = athlete_id
                                activity.name = activity_data.get('name', 'Untitled')
                                activity.sport_type = activity_data.get('sport_type', 'Unknown')
                                activity.start_date = start_date
                                activity.distance = float(activity_data.get('distance', 0)) if activity_data.get('distance') else None
                                activity.moving_time = int(activity_data.get('moving_time', 0)) if activity_data.get('moving_time') else None
                                activity.elapsed_time = int(activity_data.get('elapsed_time', 0)) if activity_data.get('elapsed_time') else None
                                activity.total_elevation_gain = float(activity_data.get('total_elevation_gain', 0)) if activity_data.get('total_elevation_gain') else None
                                activity.average_speed = float(activity_data.get('average_speed', 0)) if activity_data.get('average_speed') else None
                                activity.max_speed = float(activity_data.get('max_speed', 0)) if activity_data.get('max_speed') else None
                                activity.average_cadence = float(activity_data.get('average_cadence', 0)) if activity_data.get('average_cadence') else None
                                activity.average_heartrate = float(activity_data.get('average_heartrate', 0)) if activity_data.get('average_heartrate') else None
                                activity.max_heartrate = float(activity_data.get('max_heartrate', 0)) if activity_data.get('max_heartrate') else None
                                activity.calories = float(activity_data.get('calories', 0)) if activity_data.get('calories') else None
                                activity.created_at = datetime.now()
                                
                                db.session.add(activity)
                                saved_count += 1
                        except Exception as activity_error:
                            logger.warning(f"Failed to save activity {activity_data.get('id', 'unknown')}: {str(activity_error)}")
                            continue
                    
                    if saved_count > 0:
                        db.session.commit()
                        logger.info(f"Fetched and saved {saved_count} activities for athlete {athlete_id}")
                    else:
                        logger.warning(f"No activities were saved for athlete {athlete_id}")
            except Exception as e:
                logger.warning(f"Failed to fetch Strava activities: {str(e)}")
        
        # Get all activities for this athlete
        all_activities = Activity.query.filter_by(athlete_id=athlete_id).all()
        logger.info(f"Total activities in database for athlete {athlete_id}: {len(all_activities)}")
        
        # Get recent activities (last 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_activities = Activity.query.filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= cutoff_date
        ).order_by(Activity.start_date.desc()).all()
        
        logger.info(f"Recent activities (30 days) for athlete {athlete_id}: {len(recent_activities)}")
        
        # Calculate real metrics from our 50 activities
        total_distance_m = sum(a.distance or 0 for a in recent_activities)
        total_distance_km = total_distance_m / 1000
        total_activities = len(recent_activities)
        total_time = sum(a.moving_time or 0 for a in recent_activities)
        
        # Calculate average pace (min/km) 
        avg_pace_min_km = 0
        if total_distance_km > 0 and total_time > 0:
            pace_seconds_per_km = total_time / total_distance_km
            avg_pace_min_km = pace_seconds_per_km / 60
        
        # Calculate average heart rate
        hr_activities = [a for a in recent_activities if a.average_heartrate]
        avg_heart_rate = sum(a.average_heartrate for a in hr_activities) / len(hr_activities) if hr_activities else 0
        
        # Training load calculation using TRIMP (Training Impulse) method
        # TRIMP = Duration (min) × Average HR × HR Reserve Factor
        training_load = 0
        for activity in recent_activities:
            if activity.moving_time and activity.average_heartrate:
                duration_min = activity.moving_time / 60
                avg_hr = activity.average_heartrate
                # Simplified HR reserve factor (assumes max HR 190, resting HR 60)
                hr_reserve_factor = max(0, (avg_hr - 60) / (190 - 60))
                activity_load = duration_min * hr_reserve_factor * 1.92  # 1.92 is gender factor for male
                training_load += activity_load
        
        logger.info(f"Calculated metrics - Distance: {total_distance_km:.2f}km, Activities: {total_activities}, Pace: {avg_pace_min_km:.2f}min/km, HR: {avg_heart_rate:.1f}, Load: {training_load}")
        
        # Get performance summary with fallback
        performance_summary = get_athlete_performance_summary(db.session, athlete_id, days=30)
        
        # Build comprehensive dashboard data
        dashboard_data = {
            'athlete': {
                'id': athlete.id,
                'name': athlete.name,
                'strava_athlete_id': athlete.strava_athlete_id
            },
            'metrics': {
                'total_distance': round(total_distance_km, 2),
                'total_activities': total_activities,
                'avg_pace': round(avg_pace_min_km, 2),
                'training_load': round(training_load, 1),
                'avg_heart_rate': round(avg_heart_rate, 1) if avg_heart_rate > 0 else 0,
                'total_time': total_time
            },
            'recent_activities': [{
                'id': a.id,
                'name': a.name,
                'distance': round((a.distance or 0) / 1000, 2),
                'moving_time': a.moving_time or 0,
                'start_date': a.start_date.isoformat() if a.start_date else None,
                'sport_type': a.sport_type,
                'average_heartrate': a.average_heartrate
            } for a in recent_activities[:10]],
            'performance_summary': performance_summary or {
                'total_distance': round(total_distance_km, 2),
                'total_activities': total_activities,
                'average_pace': round(avg_pace_min_km, 2) if avg_pace_min_km > 0 else None,
                'average_heart_rate': round(avg_heart_rate, 1) if avg_heart_rate > 0 else None,
                'training_load': round(training_load, 1),
                'total_elevation_gain': sum(a.total_elevation_gain or 0 for a in recent_activities)
            }
        }
        
        logger.info(f"Returning dashboard data: {len(dashboard_data['recent_activities'])} activities, {dashboard_data['metrics']['total_distance']}km total")
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data for athlete {athlete_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to fetch dashboard data'}), 500

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

@main_bp.route('/auth/success')
def auth_success():
    """Display success page after Strava authentication"""
    from flask import render_template
    return render_template('auth_success.html')

@main_bp.route('/attached_assets/<path:filename>')
def serve_attached_assets(filename):
    """Serve files from the attached_assets directory"""
    import os
    return send_from_directory(os.path.join(os.getcwd(), 'attached_assets'), filename)

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
    """Sync activities from Strava for all connected athletes (called by scheduler)"""
    from app import create_app
    try:
        app = create_app()
        with app.app_context():
            # Get all active athletes
            active_athletes = db.session.query(ReplitAthlete).filter_by(is_active=True).all()
            
            logger.info(f"Processing Strava sync for {len(active_athletes)} athletes")
            
            for athlete in active_athletes:
                try:
                    # Actually sync activities from Strava
                    sync_result = sync_athlete_activities_internal(athlete.id)
                    logger.info(f"Synced activities for athlete {athlete.id}: {sync_result.get('activities_synced', 0)} new activities")
                    
                except Exception as e:
                    logger.error(f"Error syncing activities for athlete {athlete.id}: {str(e)}")
            
            logger.info(f"Completed Strava sync for {len(active_athletes)} athletes")
        
    except Exception as e:
        logger.error(f"Error in send_athlete_update: {str(e)}")

def sync_athlete_activities_internal(athlete_id):
    """Internal function to sync activities from Strava for a specific athlete"""
    try:
        # Get athlete from database
        athlete = db.session.query(ReplitAthlete).filter_by(id=athlete_id).first()
        if not athlete:
            return {'error': 'Athlete not found', 'activities_synced': 0}
        
        # Check if we have valid tokens
        if not athlete.access_token or not athlete.refresh_token:
            logger.warning(f"No valid tokens for athlete {athlete_id}")
            return {'error': 'No valid tokens', 'activities_synced': 0}
        
        # Refresh access token if needed (refresh 1 hour before expiry for safety)
        refresh_threshold = athlete.token_expires_at - timedelta(hours=1) if athlete.token_expires_at else datetime.now()
        if not athlete.access_token or datetime.now() >= refresh_threshold:
            logger.info(f"Refreshing access token for athlete {athlete_id} (expires: {athlete.token_expires_at})")
            token_data = strava_client.refresh_access_token(athlete.refresh_token)
            if token_data:
                athlete.access_token = token_data['access_token']
                if token_data.get('refresh_token'):
                    athlete.refresh_token = token_data['refresh_token']
                athlete.token_expires_at = datetime.fromtimestamp(token_data['expires_at'])
                athlete.updated_at = datetime.now()
                db.session.commit()
                logger.info(f"Successfully refreshed token for athlete {athlete_id}, new expiry: {athlete.token_expires_at}")
            else:
                logger.error(f"Failed to refresh token for athlete {athlete_id} - may need re-authorization")
                return {'error': 'Token refresh failed - re-authorization required', 'activities_synced': 0}
        
        # Fetch activities from Strava
        logger.info(f"Fetching activities from Strava for athlete {athlete_id}")
        activities_data = strava_client.get_activities(athlete.access_token, per_page=50)
        
        if not activities_data:
            logger.info(f"No activities returned from Strava for athlete {athlete_id}")
            return {'message': 'No activities found', 'activities_synced': 0}
        
        activities_synced = 0
        for activity_data in activities_data:
            try:
                # Enhanced duplicate detection - check by Strava ID first
                existing = db.session.query(Activity).filter_by(
                    strava_activity_id=activity_data['id']
                ).first()
                
                if existing:
                    continue  # Skip if already exists by Strava ID
                
                # Parse the start date properly
                start_date_str = activity_data['start_date_local']
                if start_date_str.endswith('Z'):
                    start_date_str = start_date_str.replace('Z', '+00:00')
                activity_start = datetime.fromisoformat(start_date_str)
                
                # Additional check for activities with same athlete, timestamp, and distance (within 5 minutes)
                time_buffer = timedelta(minutes=5)
                distance = activity_data.get('distance', 0)
                
                similar_activity = db.session.query(Activity).filter(
                    Activity.athlete_id == athlete_id,
                    Activity.start_date >= activity_start - time_buffer,
                    Activity.start_date <= activity_start + time_buffer,
                    Activity.distance == distance
                ).first()
                
                if similar_activity:
                    logger.info(f"Skipping duplicate activity {activity_data['id']} - similar activity {similar_activity.strava_activity_id} already exists")
                    continue
                
                # Create new activity record
                activity = Activity()
                activity.strava_activity_id = activity_data['id']
                activity.athlete_id = athlete_id
                activity.name = activity_data['name']
                activity.sport_type = activity_data['sport_type']
                activity.start_date = activity_start
                activity.distance = activity_data.get('distance')
                activity.moving_time = activity_data.get('moving_time')
                activity.elapsed_time = activity_data.get('elapsed_time')
                activity.total_elevation_gain = activity_data.get('total_elevation_gain')
                activity.average_speed = activity_data.get('average_speed')
                activity.max_speed = activity_data.get('max_speed')
                activity.average_cadence = activity_data.get('average_cadence')
                activity.average_heartrate = activity_data.get('average_heartrate')
                activity.max_heartrate = activity_data.get('max_heartrate')
                activity.calories = activity_data.get('calories')
                activity.created_at = datetime.now()
                
                db.session.add(activity)
                activities_synced += 1
                logger.info(f"Added new activity {activity_data['id']} for athlete {athlete_id}")
                    
            except Exception as e:
                logger.error(f"Error processing activity {activity_data.get('id', 'unknown')}: {str(e)}")
                continue
        
        if activities_synced > 0:
            db.session.commit()
            logger.info(f"Successfully synced {activities_synced} new activities for athlete {athlete_id}")
        
        return {
            'message': f'Successfully synced {activities_synced} activities',
            'activities_synced': activities_synced
        }
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in sync_athlete_activities_internal for athlete {athlete_id}: {str(e)}")
        return {'error': str(e), 'activities_synced': 0}

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

@api_bp.route('/athletes/<int:athlete_id>/sync-activities', methods=['POST'])
def sync_athlete_activities(athlete_id):
    """Sync activities from Strava for a specific athlete"""
    try:
        # Get athlete from database
        athlete = db.session.query(ReplitAthlete).filter_by(id=athlete_id).first()
        if not athlete:
            return jsonify({'error': 'Athlete not found'}), 404
        
        # Initialize Strava client
        from app.strava_client import ReplitStravaClient
        strava_client = ReplitStravaClient()
        
        # Refresh access token if needed
        if not athlete.access_token or (athlete.token_expires_at and athlete.token_expires_at < datetime.now()):
            token_data = strava_client.refresh_access_token(athlete.refresh_token)
            athlete.access_token = token_data['access_token']
            athlete.token_expires_at = datetime.fromtimestamp(token_data['expires_at'])
            db.session.commit()
        
        # Fetch activities from Strava
        activities_data = strava_client.get_activities(athlete.access_token, per_page=50)
        
        activities_synced = 0
        for activity_data in activities_data:
            try:
                # Check if activity already exists
                existing = db.session.query(Activity).filter_by(
                    strava_activity_id=activity_data['id']
                ).first()
                
                if not existing:
                    # Parse the start date properly
                    start_date_str = activity_data['start_date_local']
                    if start_date_str.endswith('Z'):
                        start_date_str = start_date_str.replace('Z', '+00:00')
                    
                    # Create new activity record for SQLite
                    activity = Activity()
                    activity.strava_activity_id = activity_data['id']
                    activity.athlete_id = athlete_id
                    activity.name = activity_data['name']
                    activity.sport_type = activity_data['sport_type']
                    activity.start_date = datetime.fromisoformat(start_date_str)
                    activity.distance = activity_data.get('distance')
                    activity.moving_time = activity_data.get('moving_time')
                    activity.elapsed_time = activity_data.get('elapsed_time')
                    activity.total_elevation_gain = activity_data.get('total_elevation_gain')
                    activity.average_speed = activity_data.get('average_speed')
                    activity.max_speed = activity_data.get('max_speed')
                    activity.average_cadence = activity_data.get('average_cadence')
                    activity.average_heartrate = activity_data.get('average_heartrate')
                    activity.max_heartrate = activity_data.get('max_heartrate')
                    activity.calories = activity_data.get('calories')
                    activity.created_at = datetime.now()
                    
                    db.session.add(activity)
                    
                    activities_synced += 1
                    logger.info(f"Inserted activity {activity_data['id']} for athlete {athlete_id}")
                    
            except Exception as e:
                logger.error(f"Error inserting activity {activity_data.get('id', 'unknown')}: {str(e)}")
                continue
        
        db.session.commit()
        
        logger.info(f"Synced {activities_synced} new activities for athlete {athlete_id}")
        return jsonify({
            'message': f'Successfully synced {activities_synced} activities',
            'activities_synced': activities_synced
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error syncing activities for athlete {athlete_id}: {str(e)}")
        return jsonify({'error': 'Failed to sync activities'}), 500

@api_bp.route('/community/overview')
def get_community_overview():
    """Get community overview data for the home page dashboard"""
    try:
        logger.debug("Fetching community overview data")
        
        # Get all active athletes
        athletes = ReplitAthlete.query.filter_by(is_active=True).all()
        
        if not athletes:
            return jsonify({
                'kpis': {
                    'totalAthletes': 0,
                    'totalDistance': 0,
                    'totalActivities': 0,
                    'avgPace': 0
                },
                'leaderboard': [],
                'trainingLoadDistribution': {'labels': [], 'data': []},
                'communityTrends': {'labels': [], 'datasets': []}
            })
        
        # Calculate community KPIs
        from datetime import datetime, timedelta
        from app.models import Activity
        
        # Different date ranges for different metrics
        start_date_30d = datetime.now() - timedelta(days=30)  # Last 30 days for KPIs
        start_date_7d = datetime.now() - timedelta(days=7)   # Last 7 days for leaderboard
        
        # Get all activities for 30-day KPIs and apply duplicate filtering
        all_activities_30d_raw = Activity.query.filter(
            Activity.start_date >= start_date_30d
        ).all()
        
        # Filter duplicates from 30-day data
        filtered_activities_30d = []
        seen_activities_30d = set()
        
        for activity in all_activities_30d_raw:
            time_bucket = int(activity.start_date.timestamp() // 300)  # 5-minute buckets
            distance = round(float(activity.distance or 0) / 100) * 100  # Round to nearest 100m
            unique_key = (activity.athlete_id, time_bucket, distance)
            
            if unique_key not in seen_activities_30d:
                seen_activities_30d.add(unique_key)
                filtered_activities_30d.append(activity)
        
        # Get activities for 7-day leaderboard and apply duplicate filtering
        all_activities_7d_raw = Activity.query.filter(
            Activity.start_date >= start_date_7d
        ).all()
        
        filtered_activities_7d = []
        seen_activities_7d = set()
        
        for activity in all_activities_7d_raw:
            time_bucket = int(activity.start_date.timestamp() // 300)  # 5-minute buckets
            distance = round(float(activity.distance or 0) / 100) * 100  # Round to nearest 100m
            unique_key = (activity.athlete_id, time_bucket, distance)
            
            if unique_key not in seen_activities_7d:
                seen_activities_7d.add(unique_key)
                filtered_activities_7d.append(activity)
        
        # Use filtered data for all calculations
        all_activities_30d = filtered_activities_30d
        all_activities_7d = filtered_activities_7d
        
        # Safe calculation with null checks for 30-day KPIs
        total_distance = sum((a.distance or 0) for a in all_activities_30d if a.distance is not None) / 1000  # km
        total_activities = len(all_activities_30d)
        active_athletes = len(set(a.athlete_id for a in all_activities_30d if a.athlete_id))
        
        # Calculate community average pace from 30-day data
        valid_activities = [a for a in all_activities_30d if a.distance and a.moving_time and a.distance > 0]
        if valid_activities:
            total_time = sum(a.moving_time for a in valid_activities)
            total_distance_m = sum(a.distance for a in valid_activities)
            avg_pace = (total_time / 60) / (total_distance_m / 1000) if total_distance_m > 0 else 0
        else:
            avg_pace = 0
        
        # Generate leaderboard from 30-day data (top performers by distance)
        athlete_stats = {}
        for activity in all_activities_30d:
            athlete_id = activity.athlete_id
            if athlete_id not in athlete_stats:
                athlete = ReplitAthlete.query.get(athlete_id)
                athlete_stats[athlete_id] = {
                    'id': athlete_id,
                    'name': athlete.name if athlete else f"Athlete {athlete_id}",
                    'email': athlete.email if athlete else "",
                    'distance': 0,
                    'activities': 0,
                    'avg_pace': 0,
                    'avg_hr': 0
                }
            
            athlete_stats[athlete_id]['distance'] += (activity.distance or 0) / 1000
            athlete_stats[athlete_id]['activities'] += 1
        
        # Calculate average pace and HR for each athlete using 30-day data
        for athlete_id, stats in athlete_stats.items():
            athlete_activities = [a for a in all_activities_30d if a.athlete_id == athlete_id]
            if athlete_activities:
                # Calculate average pace
                valid_acts = [a for a in athlete_activities if a.distance and a.moving_time and a.distance > 0]
                if valid_acts:
                    total_time = sum(a.moving_time for a in valid_acts)
                    total_dist = sum(a.distance for a in valid_acts) / 1000
                    stats['avg_pace'] = (total_time / 60) / total_dist if total_dist > 0 else 0
                
                # Calculate average heart rate
                hr_activities = [a for a in athlete_activities if a.average_heartrate]
                if hr_activities:
                    stats['avg_hr'] = sum(a.average_heartrate for a in hr_activities) / len(hr_activities)
        
        # Sort leaderboard by distance
        leaderboard = sorted(athlete_stats.values(), key=lambda x: x['distance'], reverse=True)
        
        # Training load distribution by activity type (30-day authentic data)
        # Include all sports with their relevant metrics (distance, time, calories)
        activity_breakdown = {}
        for activity in all_activities_30d:
            sport = activity.sport_type or 'Other'
            
            # For distance-based sports (running, cycling, etc.)
            distance_km = (activity.distance or 0) / 1000
            # For time-based sports (tennis, strength training, etc.)
            duration_hours = (activity.moving_time or activity.elapsed_time or 0) / 3600
            # For calorie-based sports
            calories = activity.calories or 0
            
            # Include activity if it has any meaningful data
            has_meaningful_data = distance_km > 0 or duration_hours > 0.1 or calories > 0
            
            if has_meaningful_data:
                if sport not in activity_breakdown:
                    activity_breakdown[sport] = 0
                
                # Use distance for distance-based activities, duration for others
                if distance_km > 0:
                    activity_breakdown[sport] += distance_km
                else:
                    # Convert duration to equivalent "training load" for comparison
                    # 1 hour of non-distance activity = ~5km equivalent for display
                    activity_breakdown[sport] += duration_hours * 5
        
        training_load_labels = list(activity_breakdown.keys())
        training_load_data = [round(distance, 1) for distance in activity_breakdown.values()]
        
        # Enhanced community trends using advanced analytics
        from app.community_analytics import get_enhanced_community_trends
        enhanced_trends = get_enhanced_community_trends(days=7)
        
        # Extract enhanced metrics for backward compatibility
        trend_labels = enhanced_trends['labels']
        
        # Use TSS and active athletes as primary metrics (more meaningful than simple distance)
        community_tss = enhanced_trends['datasets'][0]['data']  # Community TSS
        active_athletes_trend = enhanced_trends['datasets'][1]['data']  # Active Athletes
        
        # Keep original variable names for frontend compatibility but with better data
        distance_trend = community_tss  # Now represents Training Stress Score
        activity_trend = active_athletes_trend  # Now represents active athlete count
        
        # Calculate enhanced KPIs
        avg_community_tss = np.mean([val for val in community_tss if val > 0]) if any(val > 0 for val in community_tss) else 0
        consistency_percentage = (sum(1 for val in active_athletes_trend if val > 0) / 7) * 100
        peak_training_day = max(community_tss) if community_tss else 0
        
        return jsonify({
            'kpis': {
                'totalAthletes': active_athletes,
                'totalDistance': round(total_distance, 1),
                'totalActivities': total_activities,
                'avgPace': round(avg_pace, 2) if avg_pace > 0 else 0,
                'avgCommunityTSS': round(avg_community_tss, 1),
                'consistencyRate': round(consistency_percentage, 1),
                'peakTrainingDay': round(peak_training_day, 1)
            },
            'leaderboard': leaderboard,
            'trainingLoadDistribution': {
                'labels': training_load_labels,
                'data': training_load_data
            },
            'communityTrends': {
                'labels': trend_labels,
                'datasets': [
                    {
                        'label': 'Community TSS (Training Stress)',
                        'data': distance_trend,
                        'borderColor': 'rgb(34, 197, 94)',
                        'backgroundColor': 'rgba(34, 197, 94, 0.1)',
                        'tension': 0.4
                    },
                    {
                        'label': 'Active Athletes',
                        'data': activity_trend,
                        'borderColor': 'rgb(99, 102, 241)',
                        'backgroundColor': 'rgba(99, 102, 241, 0.1)',
                        'tension': 0.4
                    }
                ],
                'insights': enhanced_trends.get('insights', [])
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching community overview: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Community Training Zones API
@api_bp.route('/community/training_zones', methods=['GET'])
def get_community_training_zones():
    """Get community training zone distribution"""
    try:
        logger.info("Fetching community training zone distribution")
        
        # Get all active athletes with recent activities
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Calculate training load zones for each athlete
        zones = {
            'Low': 0,
            'Moderate': 0, 
            'High': 0,
            'Overreaching': 0
        }
        
        # Store athlete details for each zone
        zone_athletes = {
            'Low': [],
            'Moderate': [],
            'High': [],
            'Overreaching': []
        }
        
        athletes = db.session.query(ReplitAthlete).filter_by(is_active=True).all()
        
        for athlete in athletes:
            # Calculate recent training load
            recent_activities = db.session.query(Activity).filter(
                Activity.athlete_id == athlete.id,
                Activity.start_date >= thirty_days_ago
            ).all()
            
            if not recent_activities:
                zones['Low'] += 1
                zone_athletes['Low'].append({
                    'name': athlete.name,
                    'weekly_distance': 0,
                    'weekly_hours': 0
                })
                continue
                
            # Calculate weekly training load
            total_distance = sum(float(a.distance or 0) / 1000 for a in recent_activities)  # Convert to km
            total_time = sum(int(a.moving_time or 0) for a in recent_activities)  # seconds
            
            # Weekly averages
            weekly_distance = total_distance / 4.3  # ~30 days / 7 days
            weekly_hours = (total_time / 3600) / 4.3
            
            athlete_data = {
                'name': athlete.name,
                'weekly_distance': round(weekly_distance, 1),
                'weekly_hours': round(weekly_hours, 1)
            }
            
            # Zone classification based on training volume
            if weekly_distance < 20 or weekly_hours < 2:
                zones['Low'] += 1
                zone_athletes['Low'].append(athlete_data)
            elif weekly_distance < 40 or weekly_hours < 4:
                zones['Moderate'] += 1
                zone_athletes['Moderate'].append(athlete_data)
            elif weekly_distance < 70 or weekly_hours < 7:
                zones['High'] += 1
                zone_athletes['High'].append(athlete_data)
            else:
                zones['Overreaching'] += 1
                zone_athletes['Overreaching'].append(athlete_data)
        
        # Calculate percentages
        total_athletes = sum(zones.values())
        if total_athletes > 0:
            zone_percentages = {
                zone: round((count / total_athletes) * 100, 1)
                for zone, count in zones.items()
            }
        else:
            zone_percentages = {zone: 0 for zone in zones.keys()}
        
        logger.info(f"Training zone distribution: {zone_percentages}")
        
        return jsonify({
            'zones': zones,
            'percentages': zone_percentages,
            'total_athletes': total_athletes,
            'zone_athletes': zone_athletes
        })
        
    except Exception as e:
        logger.error(f"Error fetching community training zones: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Community Activity Stream API
@api_bp.route('/community/activity-stream', methods=['GET'])
def get_community_activity_stream():
    """Get recent community activities and milestones"""
    try:
        logger.debug("Fetching community activity stream")
        
        # Get recent activities from all athletes
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        recent_activities = db.session.query(Activity, ReplitAthlete).join(
            ReplitAthlete, Activity.athlete_id == ReplitAthlete.id
        ).filter(
            Activity.start_date >= seven_days_ago,
            ReplitAthlete.is_active == True
        ).order_by(Activity.start_date.desc()).limit(50).all()  # Get more to filter duplicates
        
        # Filter duplicates: Remove activities with same athlete, distance, and start time within 5 minutes
        filtered_activities = []
        seen_activities = set()
        
        for activity, athlete in recent_activities:
            # Create a unique key for duplicate detection
            time_bucket = int(activity.start_date.timestamp() // 300)  # 5-minute buckets
            distance = round(float(activity.distance or 0) / 100) * 100  # Round to nearest 100m
            unique_key = (activity.athlete_id, time_bucket, distance)
            
            if unique_key not in seen_activities:
                seen_activities.add(unique_key)
                filtered_activities.append((activity, athlete))
        
        # Limit to 20 unique activities after filtering
        filtered_activities = filtered_activities[:20]
        
        activity_stream = []
        milestones = []
        
        for activity, athlete in filtered_activities:
            distance_km = float(activity.distance or 0) / 1000
            duration_minutes = (activity.moving_time or activity.elapsed_time or 0) / 60
            calories = activity.calories or 0
            
            # Calculate sport-specific display metrics
            if distance_km > 0:
                # Distance-based sports (running, cycling, etc.)
                pace_seconds = (activity.moving_time / distance_km) if activity.moving_time else 0
                pace_min_km = pace_seconds / 60
                primary_metric = f"{distance_km:.1f}km"
                secondary_metric = f"{int(pace_min_km)}:{int((pace_min_km % 1) * 60):02d}" if pace_min_km > 0 else "N/A"
            else:
                # Time-based sports (tennis, strength training, etc.)
                primary_metric = f"{int(duration_minutes)}min" if duration_minutes > 0 else "N/A"
                secondary_metric = f"{int(calories)} cal" if calories > 0 else "N/A"
            
            # Format activity entry with sport-appropriate metrics
            activity_entry = {
                'type': 'activity',
                'athlete_name': athlete.name,
                'activity_name': activity.name,
                'sport_type': activity.sport_type,
                'distance_km': round(distance_km, 2) if distance_km > 0 else 0,
                'duration_minutes': round(duration_minutes, 0) if duration_minutes > 0 else 0,
                'calories': int(calories) if calories > 0 else 0,
                'pace': secondary_metric,
                'primary_metric': primary_metric,
                'start_date': activity.start_date.isoformat(),
                'relative_time': _get_relative_time(activity.start_date)
            }
            activity_stream.append(activity_entry)
            
            # Check for milestones - including non-distance achievements
            if distance_km >= 21.0975 and distance_km <= 21.5:  # Half marathon
                milestones.append({
                    'type': 'milestone',
                    'athlete_name': athlete.name,
                    'achievement': 'Half Marathon Distance',
                    'details': f'{distance_km:.2f}km',
                    'date': activity.start_date.isoformat(),
                    'relative_time': _get_relative_time(activity.start_date)
                })
            elif distance_km >= 42.0 and distance_km <= 43.0:  # Marathon
                milestones.append({
                    'type': 'milestone',
                    'athlete_name': athlete.name,
                    'achievement': 'Marathon Distance',
                    'details': f'{distance_km:.2f}km',
                    'date': activity.start_date.isoformat(),
                    'relative_time': _get_relative_time(activity.start_date)
                })
            elif distance_km >= 10.0 and distance_km <= 10.5:  # 10K
                milestones.append({
                    'type': 'milestone',
                    'athlete_name': athlete.name,
                    'achievement': '10K Distance',
                    'details': f'{distance_km:.2f}km',
                    'date': activity.start_date.isoformat(),
                    'relative_time': _get_relative_time(activity.start_date)
                })
            # Add milestones for non-distance sports
            elif activity.sport_type == 'Tennis' and duration_minutes >= 60:
                milestones.append({
                    'type': 'milestone',
                    'athlete_name': athlete.name,
                    'achievement': 'Tennis Marathon',
                    'details': f'{int(duration_minutes)}min session',
                    'date': activity.start_date.isoformat(),
                    'relative_time': _get_relative_time(activity.start_date)
                })
            elif calories >= 500:  # High calorie burn
                milestones.append({
                    'type': 'milestone',
                    'athlete_name': athlete.name,
                    'achievement': 'High Intensity Session',
                    'details': f'{int(calories)} calories',
                    'date': activity.start_date.isoformat(),
                    'relative_time': _get_relative_time(activity.start_date)
                })
        
        # Sort combined stream by date
        combined_stream = sorted(
            activity_stream + milestones,
            key=lambda x: x.get('date', x.get('start_date', '')),
            reverse=True
        )[:15]  # Limit to 15 most recent items
        
        logger.info(f"Generated activity stream with {len(combined_stream)} items")
        
        return jsonify({
            'stream': combined_stream,
            'total_activities': len(activity_stream),
            'total_milestones': len(milestones)
        })
        
    except Exception as e:
        logger.error(f"Error fetching community activity stream: {str(e)}")
        return jsonify({'error': str(e)}), 500

def _get_relative_time(date):
    """Get human-readable relative time"""
    from datetime import datetime, timezone
    
    # Ensure we're working with timezone-aware datetime objects
    now = datetime.now(timezone.utc)
    
    # Convert date to UTC if it's naive
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    
    diff = now - date
    total_seconds = diff.total_seconds()
    
    if total_seconds < 60:
        return "Just now"
    elif total_seconds < 3600:
        minutes = int(total_seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif total_seconds < 86400:  # 24 hours
        hours = int(total_seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(total_seconds // 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"

@api_bp.route('/analytics/data')
def get_analytics_data():
    """Get analytics data for charts and metrics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get all athletes (for now, we'll aggregate data from all)
        athletes = ReplitAthlete.query.filter_by(is_active=True).all()
        
        if not athletes:
            return jsonify({
                'metrics': {
                    'totalDistance': 0,
                    'totalTime': 0,
                    'avgPace': 0,
                    'activityCount': 0
                },
                'charts': {
                    'trainingLoad': {'labels': [], 'data': []},
                    'activityTypes': {'labels': [], 'data': []},
                    'paceProgression': {'labels': [], 'data': []}
                },
                'activities': []
            })
        
        # For demonstration, we'll use the first athlete
        athlete = athletes[0]
        
        # Get activities from the last N days
        from datetime import datetime, timedelta
        from app.models import Activity
        
        start_date = datetime.now() - timedelta(days=days)
        activities = Activity.query.filter(
            Activity.athlete_id == athlete.id,
            Activity.start_date >= start_date
        ).order_by(Activity.start_date.desc()).all()
        
        # Calculate metrics
        total_distance = sum(a.distance or 0 for a in activities) / 1000  # Convert to km
        total_time = sum(a.moving_time or 0 for a in activities)
        activity_count = len(activities)
        
        # Calculate average pace and heart rate
        if total_distance > 0 and total_time > 0:
            avg_speed = (total_distance * 1000) / total_time  # m/s
        else:
            avg_speed = 0
        
        # Group activities by type
        activity_types = {}
        for activity in activities:
            sport_type = activity.sport_type or 'Unknown'
            activity_types[sport_type] = activity_types.get(sport_type, 0) + 1
        
        # Create sample chart data
        import calendar
        chart_labels = []
        chart_data = []
        pace_data = []
        
        # Generate last 7 days for charts
        for i in range(6, -1, -1):
            date = datetime.now() - timedelta(days=i)
            chart_labels.append(date.strftime('%m/%d'))
            
            # Get activities for this day
            day_activities = [a for a in activities if a.start_date.date() == date.date()]
            day_distance = sum(a.distance or 0 for a in day_activities) / 1000
            chart_data.append(day_distance)
            
            if day_activities:
                day_time = sum(a.moving_time or 0 for a in day_activities)
                if day_distance > 0 and day_time > 0:
                    day_pace = (day_time / 60) / day_distance  # min/km
                    pace_data.append(day_pace)
                else:
                    pace_data.append(None)
            else:
                pace_data.append(None)
        
        # Calculate average heart rate
        heart_rate_activities = [a for a in activities if a.average_heartrate]
        avg_heart_rate = sum(a.average_heartrate for a in heart_rate_activities) / len(heart_rate_activities) if heart_rate_activities else 0
        
        # Prepare comprehensive chart data
        heart_rate_data = prepare_heart_rate_analytics(activities)
        elevation_data = prepare_elevation_analytics(activities)
        pace_analytics = prepare_pace_analytics(activities)
        
        return jsonify({
            'metrics': {
                'totalDistance': total_distance,  # Keep in km as frontend expects
                'totalTime': total_time,
                'avgHeartRate': round(avg_heart_rate, 1) if avg_heart_rate else 0,
                'activityCount': activity_count
            },
            'heartRateData': heart_rate_data,
            'elevationData': elevation_data,
            'paceData': pace_analytics,
            'activityTypes': {
                'labels': list(activity_types.keys()),
                'values': list(activity_types.values())
            },
            'activities': [{
                'id': a.id,
                'name': a.name,
                'sport_type': a.sport_type,
                'start_date': a.start_date.isoformat(),
                'distance': a.distance,
                'moving_time': a.moving_time,
                'average_speed': a.average_speed,
                'average_heartrate': a.average_heartrate
            } for a in activities[:20]]  # Limit to 20 recent activities
        })
        
    except Exception as e:
        logger.error(f"Error fetching analytics data: {str(e)}")
        return jsonify({'error': 'Failed to fetch analytics data'}), 500


def prepare_heart_rate_analytics(activities):
    """Prepare heart rate zone analysis from real Strava activities"""
    try:
        # Filter activities with heart rate data
        hr_activities = [a for a in activities if a.average_heartrate and a.max_heartrate]
        
        if not hr_activities:
            return {'labels': [], 'avgHeartRate': [], 'maxHeartRate': []}
        
        # Group by week for trend analysis
        weekly_data = {}
        for activity in hr_activities:
            week_start = activity.start_date - timedelta(days=activity.start_date.weekday())
            week_key = week_start.strftime('%m/%d')
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {'avg_hr': [], 'max_hr': []}
            
            weekly_data[week_key]['avg_hr'].append(activity.average_heartrate)
            weekly_data[week_key]['max_hr'].append(activity.max_heartrate)
        
        # Calculate weekly averages
        labels = sorted(weekly_data.keys())
        avg_heart_rate = []
        max_heart_rate = []
        
        for week in labels:
            week_avg = sum(weekly_data[week]['avg_hr']) / len(weekly_data[week]['avg_hr'])
            week_max = max(weekly_data[week]['max_hr'])
            avg_heart_rate.append(round(week_avg, 1))
            max_heart_rate.append(week_max)
        
        return {
            'labels': labels,
            'avgHeartRate': avg_heart_rate,
            'maxHeartRate': max_heart_rate
        }
    
    except Exception as e:
        logger.error(f"Error in heart rate analytics: {str(e)}")
        return {'labels': [], 'avgHeartRate': [], 'maxHeartRate': []}


def prepare_elevation_analytics(activities):
    """Prepare elevation vs distance analysis from real Strava activities"""
    try:
        # Filter activities with elevation data
        elevation_activities = [a for a in activities if a.total_elevation_gain and a.distance]
        elevation_activities = sorted(elevation_activities, key=lambda x: x.start_date)
        
        if not elevation_activities:
            return {'labels': [], 'distance': [], 'elevation': []}
        
        # Take last 15 activities for readability
        recent_activities = elevation_activities[-15:]
        
        labels = [a.start_date.strftime('%m/%d') for a in recent_activities]
        distance = [round(a.distance / 1000, 2) for a in recent_activities]  # Convert to km
        elevation = [round(a.total_elevation_gain, 1) for a in recent_activities]
        
        return {
            'labels': labels,
            'distance': distance,
            'elevation': elevation
        }
    
    except Exception as e:
        logger.error(f"Error in elevation analytics: {str(e)}")
        return {'labels': [], 'distance': [], 'elevation': []}


def prepare_pace_analytics(activities):
    """Prepare pace progression analysis from real running activities"""
    try:
        # Filter running activities with speed data
        running_activities = [a for a in activities 
                            if a.sport_type == 'Run' and a.average_speed and a.average_speed > 0]
        running_activities = sorted(running_activities, key=lambda x: x.start_date)
        
        if not running_activities:
            return {'labels': [], 'pace': [], 'targetPace': []}
        
        # Take last 15 runs for readability
        recent_runs = running_activities[-15:]
        
        labels = [a.start_date.strftime('%m/%d') for a in recent_runs]
        pace = []
        
        for activity in recent_runs:
            # Convert speed (m/s) to pace (min/km)
            pace_min_km = 1000 / (activity.average_speed * 60)
            pace.append(round(pace_min_km, 2))
        
        # Target pace line (example: 5:30 min/km for marathon training)
        target_pace = [5.5] * len(labels)
        
        return {
            'labels': labels,
            'pace': pace,
            'targetPace': target_pace
        }
    
    except Exception as e:
        logger.error(f"Error in pace analytics: {str(e)}")
        return {'labels': [], 'pace': [], 'targetPace': []}

@api_bp.route('/athletes/<int:athlete_id>/volume-trend')
def get_volume_trend(athlete_id):
    """Get training volume trend data for charts"""
    try:
        days = int(request.args.get('days', 30))
        logger.info(f"Fetching volume trend for athlete {athlete_id} over {days} days")
        
        # Get recent activities
        cutoff_date = datetime.now() - timedelta(days=days)
        activities = Activity.query.filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= cutoff_date
        ).order_by(Activity.start_date).all()
        
        # Group by week for volume analysis
        weekly_data = {}
        for activity in activities:
            week_key = activity.start_date.strftime('%Y-W%U')
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    'distance': 0,
                    'start_date': activity.start_date
                }
            weekly_data[week_key]['distance'] += (activity.distance or 0) / 1000  # Convert to km
        
        # Sort by date and prepare chart data
        sorted_weeks = sorted(weekly_data.items(), key=lambda x: x[1]['start_date'])
        
        dates = [f"Week {item[0].split('-W')[1]}" for item in sorted_weeks]
        distances = [round(item[1]['distance'], 1) for item in sorted_weeks]
        
        return jsonify({
            'dates': dates,
            'distances': distances
        })
        
    except Exception as e:
        logger.error(f"Error fetching volume trend: {str(e)}")
        return jsonify({'dates': [], 'distances': []}), 500

@api_bp.route('/athletes/<int:athlete_id>/pace-analysis')
def get_pace_analysis(athlete_id):
    """Get pace analysis data for charts"""
    try:
        days = int(request.args.get('days', 30))
        logger.info(f"Fetching pace analysis for athlete {athlete_id} over {days} days")
        
        # Get recent running activities
        cutoff_date = datetime.now() - timedelta(days=days)
        activities = Activity.query.filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= cutoff_date,
            Activity.sport_type == 'Run',
            Activity.average_speed.isnot(None),
            Activity.average_speed > 0
        ).order_by(Activity.start_date).all()
        
        dates = []
        paces = []
        
        for activity in activities:
            dates.append(activity.start_date.strftime('%m/%d'))
            # Convert speed (m/s) to pace (min/km)
            pace_min_km = 1000 / (activity.average_speed * 60)
            paces.append(round(pace_min_km, 2))
        
        return jsonify({
            'dates': dates,
            'paces': paces
        })
        
    except Exception as e:
        logger.error(f"Error fetching pace analysis: {str(e)}")
        return jsonify({'dates': [], 'paces': []}), 500

@api_bp.route('/athletes/<int:athlete_id>/heart-rate-zones')
def get_heart_rate_zones(athlete_id):
    """Get heart rate zone distribution for charts"""
    try:
        days = int(request.args.get('days', 30))
        logger.info(f"Fetching heart rate zones for athlete {athlete_id} over {days} days")
        
        # Get recent activities with heart rate data
        cutoff_date = datetime.now() - timedelta(days=days)
        activities = Activity.query.filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= cutoff_date,
            Activity.average_heartrate.isnot(None)
        ).all()
        
        # Calculate zone distribution
        zones = {'Zone 1': 0, 'Zone 2': 0, 'Zone 3': 0, 'Zone 4': 0, 'Zone 5': 0}
        total_time = 0
        
        for activity in activities:
            hr = activity.average_heartrate
            time = activity.moving_time or 0
            total_time += time
            
            # Simple zone calculation (can be improved with athlete-specific zones)
            if hr < 120:
                zones['Zone 1'] += time
            elif hr < 140:
                zones['Zone 2'] += time
            elif hr < 160:
                zones['Zone 3'] += time
            elif hr < 180:
                zones['Zone 4'] += time
            else:
                zones['Zone 5'] += time
        
        # Convert to percentages
        if total_time > 0:
            for zone in zones:
                zones[zone] = round((zones[zone] / total_time) * 100, 1)
        
        return jsonify({'zones': zones})
        
    except Exception as e:
        logger.error(f"Error fetching heart rate zones: {str(e)}")
        return jsonify({'zones': {}}), 500

@api_bp.route('/athletes/<int:athlete_id>/training-load-metrics')
def get_training_load_metrics_api(athlete_id):
    """Get advanced training load metrics (CTL, ATL, TSB, TSS)"""
    try:
        days = int(request.args.get('days', 90))
        logger.info(f"Fetching training load metrics for athlete {athlete_id} over {days} days")
        
        # Get advanced training load metrics
        metrics = get_training_load_metrics(athlete_id, days)
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error getting training load metrics: {str(e)}")
        return jsonify({'error': 'Failed to get training load metrics'}), 500

@api_bp.route('/athletes/<int:athlete_id>/training-load')
def get_training_load(athlete_id):
    """Get training load trend data for charts"""
    try:
        days = int(request.args.get('days', 30))
        logger.info(f"Fetching training load for athlete {athlete_id} over {days} days")
        
        # Get recent activities
        cutoff_date = datetime.now() - timedelta(days=days)
        activities = Activity.query.filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= cutoff_date
        ).order_by(Activity.start_date).all()
        
        # Group by day and calculate training load
        daily_data = {}
        for activity in activities:
            day_key = activity.start_date.strftime('%Y-%m-%d')
            if day_key not in daily_data:
                daily_data[day_key] = {
                    'load': 0,
                    'date': activity.start_date
                }
            
            # Simple training load calculation
            load = 0
            if activity.moving_time and activity.distance:
                load = (activity.moving_time / 3600) * (activity.distance / 1000) * 10
            daily_data[day_key]['load'] += load
        
        # Sort by date and prepare chart data
        sorted_days = sorted(daily_data.items(), key=lambda x: x[1]['date'])
        
        dates = [item[1]['date'].strftime('%m/%d') for item in sorted_days]
        loads = [round(item[1]['load'], 1) for item in sorted_days]
        
        return jsonify({
            'dates': dates,
            'loads': loads
        })
        
    except Exception as e:
        logger.error(f"Error fetching training load: {str(e)}")
        return jsonify({'dates': [], 'loads': []}), 500

@main_bp.route('/api/ai_recommendations/<int:athlete_id>')
def get_ai_recommendations(athlete_id):
    """Get AI race recommendations for an athlete"""
    try:
        logger.info(f"Generating AI recommendations for athlete {athlete_id}")
        
        # Get athlete data
        athlete = ReplitAthlete.query.get_or_404(athlete_id)
        
        # Get recent activities for analysis
        recent_activities = Activity.query.filter_by(athlete_id=athlete_id)\
            .order_by(Activity.start_date.desc())\
            .limit(30).all()
        
        if not recent_activities:
            return jsonify({'recommendations': ['No recent activity data available for AI analysis']})
        
        # Calculate athlete metrics
        total_distance = sum(a.distance or 0 for a in recent_activities) / 1000  # Convert to km
        valid_pace_activities = [a for a in recent_activities if a.average_speed and a.average_speed > 0]
        valid_hr_activities = [a for a in recent_activities if a.average_heartrate and a.average_heartrate > 0]
        
        # Convert speed (m/s) to pace (min/km): pace = 1000 / (speed_m_s * 60)
        avg_pace = sum(1000 / (a.average_speed * 60) for a in valid_pace_activities) / len(valid_pace_activities) if valid_pace_activities else 6.5
        avg_hr = sum(a.average_heartrate for a in valid_hr_activities) / len(valid_hr_activities) if valid_hr_activities else 150
        
        athlete_data = {
            'metrics': {
                'total_distance': round(total_distance, 1),
                'total_activities': len(recent_activities),
                'avg_pace': round(avg_pace, 2),
                'avg_heart_rate': round(avg_hr, 1),
                'training_load': 850  # Estimated based on activities
            }
        }
        
        # Current activity (most recent)
        latest_activity = recent_activities[0]
        current_activity = {
            'distance': (latest_activity.distance or 0) / 1000,
            'heart_rate': latest_activity.average_heartrate or 150,
            'pace': 1000 / (latest_activity.average_speed * 60) if latest_activity.average_speed else 6.5
        }
        
        # Get AI recommendations
        from app.ai_race_advisor import get_race_recommendations
        recommendations = get_race_recommendations(athlete_data, current_activity)
        
        return jsonify({'recommendations': recommendations})
    
    except Exception as e:
        logger.error(f"Error generating AI recommendations: {str(e)}")
        return jsonify({'recommendations': ['AI recommendations temporarily unavailable. Please try again later.']})

# Race Performance Optimization Endpoints
@api_bp.route('/athletes/<int:athlete_id>/race-prediction', methods=['GET'])
def get_race_prediction(athlete_id):
    """Get race time prediction using industry-standard methodology"""
    try:
        # Parse parameters
        race_distance_param = request.args.get('distance', 'Half Marathon')
        weeks_to_race = int(request.args.get('weeks', 12))
        
        # Convert distance names to kilometers
        distance_map = {
            '5K': 5.0,
            '10K': 10.0,
            'Half Marathon': 21.0975,
            'Marathon': 42.195
        }
        
        race_distance_km = distance_map.get(race_distance_param, 21.0975)
        
        logger.info(f"Industry-standard prediction for athlete {athlete_id}: {race_distance_km}km in {weeks_to_race} weeks")
        
        # Use industry-standard race predictor
        prediction = predict_race_time_industry_standard(
            db.session, athlete_id, race_distance_km, weeks_to_race
        )
        
        # Format time for display
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            if hours > 0:
                return f"{hours}:{minutes:02d}:{secs:02d}"
            else:
                return f"{minutes}:{secs:02d}"
        
        # Enhanced response with industry standard details
        response = {
            'race_distance': race_distance_param,
            'race_distance_km': race_distance_km,
            'predicted_time_seconds': prediction['predicted_time_seconds'],
            'predicted_time_formatted': format_time(prediction['predicted_time_seconds']),
            'predicted_pace_per_km': prediction['predicted_pace_per_km'],
            'confidence_score': round(prediction['confidence_score'] * 100, 1),
            'methodology': prediction['methodology'],
            'sources': prediction['sources'],
            'weeks_to_race': weeks_to_race,
            'current_fitness': prediction['current_fitness'],
            'estimated_vdot': prediction['estimated_vdot'],
            'training_improvement_percent': round(prediction['training_improvement_percent'], 1)
        }
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in industry-standard race prediction: {str(e)}")
        logger.error(f"Full traceback: {error_details}")
        return jsonify({
            'error': 'Failed to predict race performance',
            'details': str(e),
            'type': type(e).__name__
        }), 500

@api_bp.route('/athletes/<int:athlete_id>/fitness-analysis', methods=['GET'])
def get_fitness_analysis(athlete_id):
    """Get comprehensive fitness analysis"""
    try:
        days = int(request.args.get('days', 90))
        logger.info(f"Analyzing fitness for athlete {athlete_id} over {days} days")
        
        from app.race_predictor_simple import SimpleRacePredictor
        predictor = SimpleRacePredictor()
        analysis = predictor.analyze_fitness(db.session, athlete_id, days)
        
        # Return analysis data directly (already formatted)
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing fitness: {str(e)}")
        return jsonify({'error': 'Failed to analyze fitness'}), 500

# Home route is already defined above



@api_bp.route('/api/community/sport-analytics')
def get_sport_analytics():
    """Get detailed sport-specific analytics"""
    try:
        current_app.logger.info("Fetching sport analytics")
        
        # Get sport breakdown from all activities
        sport_stats = db.session.query(
            Activity.sport_type,
            func.count(Activity.id).label('count'),
            func.avg(Activity.distance / 1000).label('avg_distance'),
            func.sum(Activity.distance / 1000).label('total_distance'),
            func.avg(Activity.moving_time / 60).label('avg_duration'),
            func.avg(Activity.average_heartrate).label('avg_hr')
        ).join(ReplitAthlete).filter(
            ReplitAthlete.is_active == True,
            Activity.distance > 0
        ).group_by(Activity.sport_type).all()
        
        analytics = []
        for stat in sport_stats:
            analytics.append({
                'sport': stat.sport_type,
                'count': stat.count,
                'avg_distance': round(float(stat.avg_distance or 0), 1),
                'total_distance': round(float(stat.total_distance or 0), 1),
                'avg_duration': round(float(stat.avg_duration or 0), 0),
                'avg_hr': round(float(stat.avg_hr or 0), 0) if stat.avg_hr else None
            })
        
        return jsonify({'sport_analytics': analytics})
        
    except Exception as e:
        current_app.logger.error(f"Error in sport analytics: {str(e)}")
        return jsonify({'error': 'Failed to load sport analytics'}), 500

@api_bp.route('/api/athletes/<int:athlete_id>/training-plan', methods=['POST'])
def get_training_plan(athlete_id):
    """Generate optimized training plan"""
    try:
        data = request.get_json()
        race_distance = data.get('race_distance', 'Half Marathon')
        race_date_str = data.get('race_date')
        
        if not race_date_str:
            return jsonify({'error': 'Race date is required'}), 400
        
        race_date = datetime.strptime(race_date_str, '%Y-%m-%d')
        
        logger.info(f"Generating training plan for athlete {athlete_id}, race: {race_distance}")
        
        from app.race_optimizer import RacePerformanceOptimizer
        optimizer = RacePerformanceOptimizer()
        training_plan = optimizer.optimize_race_strategy(athlete_id, race_distance)
        
        return jsonify(training_plan)
        
    except Exception as e:
        logger.error(f"Error generating training plan: {str(e)}")
        return jsonify({'error': 'Failed to generate training plan'}), 500

@api_bp.route('/injury-risk/<int:athlete_id>')
def get_injury_risk_api(athlete_id):
    """API endpoint for injury risk prediction"""
    try:
        logger.info(f"Predicting injury risk for athlete {athlete_id}")
        
        # Get injury risk prediction
        risk_prediction = predict_injury_risk(athlete_id)
        
        return jsonify(risk_prediction)
        
    except Exception as e:
        logger.error(f"Error in injury risk prediction API: {str(e)}")
        return jsonify({'error': 'Risk prediction failed'}), 500

@api_bp.route('/injury-prevention/<int:athlete_id>')
def get_injury_prevention_api(athlete_id):
    """API endpoint for injury prevention plan"""
    try:
        logger.info(f"Generating injury prevention plan for athlete {athlete_id}")
        
        # Get comprehensive prevention plan
        prevention_plan = get_injury_prevention_plan(athlete_id)
        
        return jsonify(prevention_plan)
        
    except Exception as e:
        logger.error(f"Error generating prevention plan: {str(e)}")
        return jsonify({'error': 'Prevention plan generation failed'}), 500

@api_bp.route('/athletes/<int:athlete_id>/fitness-analytics')
def get_fitness_analytics(athlete_id):
    """Get comprehensive fitness analytics for athlete dashboard"""
    try:
        # Get days parameter from query string, default to 90
        days = request.args.get('days', 90, type=int)
        logger.info(f"Generating fitness analytics for athlete {athlete_id} with {days} days of data")
        
        # Get athlete information
        athlete = db.session.query(ReplitAthlete).filter_by(id=athlete_id).first()
        if not athlete:
            return jsonify({'error': 'Athlete not found'}), 404
        
        # Helper function to format time
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            if hours > 0:
                return f"{hours}:{minutes:02d}:{secs:02d}"
            else:
                return f"{minutes}:{secs:02d}"
        
        # Get industry-standard race predictions for key distances
        race_predictions = {}
        race_distances = {'5K': 5.0, '10K': 10.0, 'Half Marathon': 21.0975, 'Marathon': 42.195}
        
        for race_name, distance_km in race_distances.items():
            try:
                prediction = predict_race_time_industry_standard(
                    db.session, athlete_id, distance_km, weeks_to_race=12
                )
                race_predictions[race_name] = {
                    'predicted_time_seconds': prediction['predicted_time_seconds'],
                    'predicted_time_formatted': format_time(prediction['predicted_time_seconds']),
                    'predicted_pace_per_km': prediction['predicted_pace_per_km'],
                    'confidence_score': round(prediction['confidence_score'] * 100, 1),
                    'methodology': prediction['methodology']
                }
            except Exception as e:
                logger.warning(f"Failed to predict {race_name} for athlete {athlete_id}: {str(e)}")
                race_predictions[race_name] = {
                    'error': 'Insufficient data for prediction',
                    'predicted_time_formatted': 'N/A',
                    'confidence_score': 0
                }
        
        # Get fitness analysis using industry-standard current fitness data
        try:
            current_fitness = predict_race_time_industry_standard(
                db.session, athlete_id, 21.0975, weeks_to_race=12
            )['current_fitness']
            
            fitness_data = {
                'fitness_metrics': {
                    'current_pace_per_km': current_fitness['current_pace_per_km'],
                    'weekly_volume_km': current_fitness['weekly_volume_km'],
                    'pace_trend': current_fitness['pace_trend'],
                    'training_consistency': current_fitness['training_consistency'],
                    'longest_recent_run_km': current_fitness['longest_recent_run_km']
                },
                'race_predictions': race_predictions
            }
        except Exception as e:
            logger.error(f"Error getting industry-standard fitness data: {str(e)}")
            # Fallback to basic fitness analysis
            fitness_data = {'fitness_metrics': {}, 'race_predictions': race_predictions}
        
        # Get injury risk assessment
        injury_risk = predict_injury_risk(athlete_id)
        
        # Get recent activities for trends using the same period
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_activities = db.session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= cutoff_date,
            Activity.sport_type.in_(['Run', 'VirtualRun'])
        ).order_by(Activity.start_date.desc()).all()
        
        # Calculate heart rate metrics from recent activities
        hr_activities = [a for a in recent_activities if a.average_heartrate and a.average_heartrate > 0]
        avg_heart_rate = sum(a.average_heartrate for a in hr_activities) / len(hr_activities) if hr_activities else 0
        
        # Create activity trend data
        activity_trends = []
        for activity in recent_activities[:10]:  # Last 10 activities
            if activity.distance and activity.moving_time:
                pace_per_km = (activity.moving_time / 60) / (activity.distance / 1000)
                activity_trends.append({
                    'date': activity.start_date.strftime('%Y-%m-%d'),
                    'distance': round(activity.distance / 1000, 2),
                    'pace': round(pace_per_km, 2),
                    'name': activity.name
                })
        
        # Combine all analytics and add heart rate data
        fitness_metrics = fitness_data.get('fitness_metrics', {})
        fitness_metrics['avg_heart_rate'] = round(avg_heart_rate, 1) if avg_heart_rate > 0 else 0
        
        analytics_data = {
            'fitness_metrics': fitness_metrics,
            'race_predictions': fitness_data.get('race_predictions', race_predictions),
            'injury_risk': injury_risk,
            'activity_trends': activity_trends,
            'summary': fitness_data.get('summary', {}),
            'athlete_id': athlete_id,
            'athlete_info': {
                'id': athlete.id,
                'name': athlete.name,
                'email': athlete.email
            }
        }
        
        return jsonify(analytics_data)
        
    except Exception as e:
        logger.error(f"Error generating fitness analytics for athlete {athlete_id}: {str(e)}")
        return jsonify({'error': 'Fitness analytics generation failed'}), 500



@api_bp.route('/athletes/<int:athlete_id>/race-optimization')
def get_race_optimization(athlete_id):
    """Get comprehensive race performance optimization for athlete"""
    try:
        logger.info(f"Generating race optimization for athlete {athlete_id}")
        
        race_distance = request.args.get('distance', 'Marathon')
        
        optimization = optimize_race_performance(db.session, athlete_id, race_distance)
        
        if 'error' in optimization:
            return jsonify(optimization), 400
        
        return jsonify(optimization)
        
    except Exception as e:
        logger.error(f"Error generating race optimization for athlete {athlete_id}: {str(e)}")
        return jsonify({'error': 'Failed to generate race optimization'}), 500

@api_bp.route('/athletes/<int:athlete_id>/pacing-strategy')
def get_athlete_pacing_strategy(athlete_id):
    """Get optimal pacing strategy for specific race distance"""
    try:
        logger.info(f"Generating pacing strategy for athlete {athlete_id}")
        
        race_distance = request.args.get('distance', 'Marathon')
        target_time = request.args.get('target_time')
        
        pacing_strategy = get_pacing_strategy(athlete_id, race_distance, target_time)
        
        if 'error' in pacing_strategy:
            return jsonify(pacing_strategy), 400
        
        return jsonify(pacing_strategy)
        
    except Exception as e:
        logger.error(f"Error generating pacing strategy for athlete {athlete_id}: {str(e)}")
        return jsonify({'error': 'Failed to generate pacing strategy'}), 500

@api_bp.route('/athletes/<int:athlete_id>/training-optimization')
def get_athlete_training_optimization(athlete_id):
    """Get training optimization recommendations for athlete"""
    try:
        logger.info(f"Generating training optimization for athlete {athlete_id}")
        
        race_distance = request.args.get('distance', 'Marathon')
        
        training_optimization = get_training_optimization(athlete_id, race_distance)
        
        if 'error' in training_optimization:
            return jsonify(training_optimization), 400
        
        return jsonify(training_optimization)
        
    except Exception as e:
        logger.error(f"Error generating training optimization for athlete {athlete_id}: {str(e)}")
        return jsonify({'error': 'Failed to generate training optimization'}), 500

@api_bp.route('/training-heatmap/<int:athlete_id>', methods=['GET'])
def get_training_heatmap_data(athlete_id):
    """Get training heatmap data for visualization"""
    try:
        logger.info(f"Getting training heatmap data for athlete {athlete_id}")
        
        # Get query parameters
        year = int(request.args.get('year', datetime.now().year))
        
        # Get athlete
        athlete = ReplitAthlete.query.filter_by(id=athlete_id, is_active=True).first()
        if not athlete:
            return jsonify({'error': 'Athlete not found'}), 404
        
        # Get activities for the specified year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)
        
        activities = Activity.query.filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= start_date,
            Activity.start_date <= end_date
        ).order_by(Activity.start_date).all()
        
        # Process daily data
        daily_data = {}
        
        for activity in activities:
            date_str = activity.start_date.strftime('%Y-%m-%d')
            
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'training_load': 0,
                    'distance': 0,
                    'duration': 0,
                    'activities': 0,
                    'activity_list': []
                }
            
            # Calculate training load for this activity
            activity_load = 0
            if activity.moving_time and activity.average_heartrate:
                duration_min = activity.moving_time / 60
                avg_hr = activity.average_heartrate
                hr_reserve_factor = max(0, (avg_hr - 60) / (190 - 60))
                activity_load = duration_min * hr_reserve_factor * 1.92
            elif activity.moving_time:
                # Fallback calculation based on duration and intensity estimate
                duration_min = activity.moving_time / 60
                activity_load = duration_min * 0.5  # Moderate intensity estimate
            
            daily_data[date_str]['training_load'] += activity_load
            daily_data[date_str]['distance'] += (activity.distance or 0) / 1000  # Convert to km
            daily_data[date_str]['duration'] += (activity.moving_time or 0) / 60  # Convert to minutes
            daily_data[date_str]['activities'] += 1
            daily_data[date_str]['activity_list'].append({
                'name': activity.name or 'Untitled Activity',
                'sport_type': activity.sport_type or 'Unknown',
                'distance': (activity.distance or 0) / 1000,
                'duration': (activity.moving_time or 0) / 60
            })
        
        # Calculate stats
        total_activities = len(activities)
        total_distance = sum((a.distance or 0) / 1000 for a in activities)
        total_load = sum(day['training_load'] for day in daily_data.values())
        avg_weekly_load = total_load / 52 if total_load > 0 else 0
        
        # Calculate longest streak
        longest_streak = 0
        current_streak = 0
        
        # Sort dates and check consecutive days
        sorted_dates = sorted(daily_data.keys())
        for i, date_str in enumerate(sorted_dates):
            if daily_data[date_str]['activities'] > 0:
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            else:
                current_streak = 0
        
        # Rename activity_list to activities for consistency
        for date_str in daily_data:
            daily_data[date_str]['activities'] = daily_data[date_str]['activity_list']
            del daily_data[date_str]['activity_list']
        
        return jsonify({
            'daily_data': daily_data,
            'stats': {
                'total_activities': total_activities,
                'total_distance': round(total_distance, 1),
                'avg_weekly_load': round(avg_weekly_load, 1),
                'longest_streak': longest_streak,
                'year': year
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting training heatmap data: {str(e)}")
        return jsonify({'error': 'Failed to get heatmap data'}), 500

# Achievement System API Endpoints
@api_bp.route('/athletes/<int:athlete_id>/achievements', methods=['GET'])
def get_athlete_achievements_api(athlete_id):
    """Get achievements for a specific athlete"""
    try:
        days_back = request.args.get('days_back', 90, type=int)
        achievements = get_athlete_achievements(athlete_id, days_back)
        
        logger.info(f"Retrieved {len(achievements)} achievements for athlete {athlete_id}")
        return jsonify({
            'achievements': achievements,
            'count': len(achievements)
        })
        
    except Exception as e:
        logger.error(f"Error getting achievements for athlete {athlete_id}: {str(e)}")
        return jsonify({'error': 'Failed to get achievements'}), 500

@api_bp.route('/athletes/<int:athlete_id>/achievement-stats', methods=['GET'])
def get_athlete_achievement_stats_api(athlete_id):
    """Get achievement statistics for a specific athlete"""
    try:
        stats = get_achievement_stats(athlete_id)
        
        logger.info(f"Retrieved achievement stats for athlete {athlete_id}: {stats['total_earned']}/{stats['total_possible']} earned")
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting achievement stats for athlete {athlete_id}: {str(e)}")
        return jsonify({'error': 'Failed to get achievement statistics'}), 500

# Analytics endpoints are defined above in lines 117-362
# All duplicate routes below this line have been removed to prevent Flask conflicts

# Removed duplicate training heatmap route - functionality integrated in athlete dashboard
