import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from flask_socketio import emit, join_room, leave_room
from app import db, socketio
from app.models import ReplitAthlete, DailySummary, Activity, PlannedWorkout, SystemLog
from app.data_processor import get_athlete_performance_summary, get_team_overview
from app.race_predictor_simple import SimpleRacePredictor
from app.injury_predictor import predict_injury_risk, get_injury_prevention_plan
from app.race_optimizer import optimize_race_performance, get_pacing_strategy, get_training_optimization
from app.security import ReplitSecurity
from app.strava_client import ReplitStravaClient
from app.config import Config
from app.ai_race_advisor import get_race_recommendations

# Create blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Main routes blueprint
main_bp = Blueprint('main', __name__)

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

# Volume trend endpoint
@api_bp.route('/athletes/<int:athlete_id>/volume-trend', methods=['GET'])
def get_volume_trend(athlete_id):
    """Get training volume trend data"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        activities = db.session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= start_date
        ).order_by(Activity.start_date).all()
        
        # Group by date
        daily_volumes = {}
        for activity in activities:
            date_str = activity.start_date.strftime('%Y-%m-%d')
            if date_str not in daily_volumes:
                daily_volumes[date_str] = 0
            daily_volumes[date_str] += (activity.distance or 0) / 1000  # Convert to km
        
        # Fill missing dates with 0
        dates = []
        distances = []
        current_date = start_date
        while current_date <= datetime.now():
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(date_str)
            distances.append(daily_volumes.get(date_str, 0))
            current_date += timedelta(days=1)
        
        return jsonify({
            'dates': dates,
            'distances': distances
        })
        
    except Exception as e:
        logger.error(f"Error getting volume trend: {str(e)}")
        return jsonify({'error': 'Failed to get volume trend'}), 500

# Pace analysis endpoint
@api_bp.route('/athletes/<int:athlete_id>/pace-analysis', methods=['GET'])
def get_pace_analysis(athlete_id):
    """Get pace analysis data"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        activities = db.session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= start_date,
            Activity.sport_type == 'Run'
        ).order_by(Activity.start_date).all()
        
        dates = []
        paces = []
        
        for activity in activities:
            if activity.distance and activity.moving_time and activity.distance > 0:
                pace = (activity.moving_time / 60) / (activity.distance / 1000)  # min/km
                dates.append(activity.start_date.strftime('%Y-%m-%d'))
                paces.append(round(pace, 2))
        
        return jsonify({
            'dates': dates,
            'paces': paces
        })
        
    except Exception as e:
        logger.error(f"Error getting pace analysis: {str(e)}")
        return jsonify({'error': 'Failed to get pace analysis'}), 500

# Heart rate zones endpoint
@api_bp.route('/athletes/<int:athlete_id>/heart-rate-zones', methods=['GET'])
def get_heart_rate_zones(athlete_id):
    """Get heart rate zones distribution"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        activities = db.session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= start_date,
            Activity.average_heartrate.isnot(None)
        ).all()
        
        # Simplified heart rate zones (assuming max HR of 190)
        zones = [0, 0, 0, 0, 0]  # Zone 1-5
        
        for activity in activities:
            hr = activity.average_heartrate
            if hr < 114:  # Zone 1: <60% max HR
                zones[0] += 1
            elif hr < 133:  # Zone 2: 60-70% max HR
                zones[1] += 1
            elif hr < 152:  # Zone 3: 70-80% max HR
                zones[2] += 1
            elif hr < 171:  # Zone 4: 80-90% max HR
                zones[3] += 1
            else:  # Zone 5: >90% max HR
                zones[4] += 1
        
        return jsonify({
            'zones': zones
        })
        
    except Exception as e:
        logger.error(f"Error getting heart rate zones: {str(e)}")
        return jsonify({'error': 'Failed to get heart rate zones'}), 500

# Training load endpoint
@api_bp.route('/athletes/<int:athlete_id>/training-load', methods=['GET'])
def get_training_load(athlete_id):
    """Get training load trend"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        activities = db.session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= start_date
        ).order_by(Activity.start_date).all()
        
        # Group by date and calculate training load
        daily_loads = {}
        for activity in activities:
            date_str = activity.start_date.strftime('%Y-%m-%d')
            if date_str not in daily_loads:
                daily_loads[date_str] = 0
            
            # TRIMP-based training load calculation
            if activity.moving_time and activity.average_heartrate:
                duration_min = activity.moving_time / 60
                avg_hr = activity.average_heartrate
                hr_reserve_factor = max(0, (avg_hr - 60) / (190 - 60))
                load = duration_min * hr_reserve_factor * 1.92
                daily_loads[date_str] += load
        
        # Fill missing dates with 0
        dates = []
        loads = []
        current_date = start_date
        while current_date <= datetime.now():
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(date_str)
            loads.append(round(daily_loads.get(date_str, 0), 1))
            current_date += timedelta(days=1)
        
        return jsonify({
            'dates': dates,
            'loads': loads
        })
        
    except Exception as e:
        logger.error(f"Error getting training load: {str(e)}")
        return jsonify({'error': 'Failed to get training load'}), 500

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
        
        # Calculate metrics
        total_distance_km = sum(a.distance or 0 for a in recent_activities) / 1000
        total_activities = len(recent_activities)
        total_time = sum(a.moving_time or 0 for a in recent_activities)
        
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
        logger.info("Fetching community overview data")
        
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
        
        start_date = datetime.now() - timedelta(days=30)
        
        # Get all recent activities for community analysis
        all_activities = Activity.query.filter(
            Activity.start_date >= start_date
        ).all()
        
        # Safe calculation with null checks
        total_distance = sum((a.distance or 0) for a in all_activities if a.distance is not None) / 1000  # km
        total_activities = len(all_activities)
        active_athletes = len(set(a.athlete_id for a in all_activities if a.athlete_id))
        
        # Calculate community average pace
        valid_activities = [a for a in all_activities if a.distance and a.moving_time and a.distance > 0]
        if valid_activities:
            total_time = sum(a.moving_time for a in valid_activities)
            total_distance_m = sum(a.distance for a in valid_activities)
            avg_pace = (total_time / 60) / (total_distance_m / 1000) if total_distance_m > 0 else 0
        else:
            avg_pace = 0
        
        # Generate leaderboard (top performers by distance)
        athlete_stats = {}
        for activity in all_activities:
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
        
        # Calculate average pace and HR for each athlete
        for athlete_id, stats in athlete_stats.items():
            athlete_activities = [a for a in all_activities if a.athlete_id == athlete_id]
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
        
        # Training load distribution by athlete
        training_load_labels = []
        training_load_data = []
        for athlete_data in leaderboard[:5]:  # Top 5 athletes
            training_load_labels.append(athlete_data['name'])
            training_load_data.append(round(athlete_data['distance'], 1))
        
        # Community trends (last 7 days)
        trend_labels = []
        distance_trend = []
        activity_trend = []
        
        for i in range(6, -1, -1):
            date = datetime.now() - timedelta(days=i)
            trend_labels.append(date.strftime('%m/%d'))
            
            day_activities = [a for a in all_activities if a.start_date and a.start_date.date() == date.date()]
            day_distance = sum(a.distance or 0 for a in day_activities) / 1000
            day_count = len(day_activities)
            
            distance_trend.append(round(day_distance, 1))
            activity_trend.append(day_count)
        
        return jsonify({
            'kpis': {
                'totalAthletes': active_athletes,
                'totalDistance': round(total_distance, 1),
                'totalActivities': total_activities,
                'avgPace': round(avg_pace, 2) if avg_pace > 0 else 0
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
                        'label': 'Daily Distance (km)',
                        'data': distance_trend,
                        'borderColor': 'rgb(75, 192, 192)',
                        'backgroundColor': 'rgba(75, 192, 192, 0.2)'
                    },
                    {
                        'label': 'Daily Activities',
                        'data': activity_trend,
                        'borderColor': 'rgb(255, 99, 132)',
                        'backgroundColor': 'rgba(255, 99, 132, 0.2)'
                    }
                ]
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
@api_bp.route('/community/activity_stream', methods=['GET'])
def get_community_activity_stream():
    """Get recent community activities and milestones"""
    try:
        logger.info("Fetching community activity stream")
        
        # Get recent activities from all athletes
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        recent_activities = db.session.query(Activity, ReplitAthlete).join(
            ReplitAthlete, Activity.athlete_id == ReplitAthlete.id
        ).filter(
            Activity.start_date >= seven_days_ago,
            ReplitAthlete.is_active == True
        ).order_by(Activity.start_date.desc()).limit(20).all()
        
        activity_stream = []
        milestones = []
        
        for activity, athlete in recent_activities:
            distance_km = float(activity.distance or 0) / 1000
            pace_min_km = 0
            
            if activity.moving_time and distance_km > 0:
                pace_seconds = (activity.moving_time / distance_km)
                pace_min_km = pace_seconds / 60
            
            # Format activity entry
            activity_entry = {
                'type': 'activity',
                'athlete_name': athlete.name,
                'activity_name': activity.name,
                'sport_type': activity.sport_type,
                'distance_km': round(distance_km, 2),
                'pace': f"{int(pace_min_km)}:{int((pace_min_km % 1) * 60):02d}" if pace_min_km > 0 else "N/A",
                'start_date': activity.start_date.isoformat(),
                'relative_time': _get_relative_time(activity.start_date)
            }
            activity_stream.append(activity_entry)
            
            # Check for milestones
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
    now = datetime.now()
    diff = now - date
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

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

# Race Performance Optimization Endpoints
@api_bp.route('/athletes/<int:athlete_id>/race-prediction', methods=['GET'])
def get_race_prediction(athlete_id):
    """Get race time prediction for specific distance"""
    try:
        race_distance = request.args.get('distance', 'Half Marathon')
        logger.info(f"Predicting {race_distance} performance for athlete {athlete_id}")
        
        predictor = SimpleRacePredictor()
        prediction = predictor.predict_race_time(db.session, athlete_id, race_distance)
        
        # Return prediction data directly (already formatted)
        return jsonify(prediction)
        
    except Exception as e:
        logger.error(f"Error predicting race performance: {str(e)}")
        return jsonify({'error': 'Failed to predict race performance'}), 500

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

# Home page route
@main_bp.route('/')
def home():
    """Community dashboard home page"""
    from flask import render_template
    return render_template('community_dashboard.html')

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

@api_bp.route('/athletes/<int:athlete_id>/race-optimization')
def get_race_optimization(athlete_id):
    """Get comprehensive race performance optimization for athlete"""
    try:
        logger.info(f"Generating race optimization for athlete {athlete_id}")
        
        race_distance = request.args.get('distance', 'Marathon')
        target_time = request.args.get('target_time')
        
        optimization = optimize_race_performance(athlete_id, race_distance, target_time)
        
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

# Analytics endpoints are defined above in lines 117-362
# All duplicate routes below this line have been removed to prevent Flask conflicts
