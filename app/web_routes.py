from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
import logging
from app.models import ReplitAthlete, db
from app.strava_client import ReplitStravaClient
from app.config import Config

# Create blueprint for web routes
web_bp = Blueprint('main_routes', __name__)
logger = logging.getLogger(__name__)

@web_bp.route('/dashboard')
def athlete_dashboard():
    """Individual athlete dashboard page"""
    athlete_id = request.args.get('athlete_id', 1)
    return render_template('dashboard.html', athlete_id=athlete_id)

@web_bp.route('/athletes')
def athletes():
    """Athletes management page"""
    return render_template('athletes.html')

@web_bp.route('/analytics')
def analytics():
    """Analytics page"""
    return render_template('analytics.html')

@web_bp.route('/race-optimizer')
def race_optimizer():
    """Race Performance Optimizer page"""
    return render_template('race_optimizer.html')

@web_bp.route('/race-predictor')
def race_predictor():
    """Race Predictor page"""
    athlete_id = request.args.get('athlete_id', 1)
    return render_template('race_optimizer.html', athlete_id=athlete_id)

@web_bp.route('/injury-risk')
def injury_risk():
    """Injury Risk Assessment page"""
    return render_template('injury_risk.html')

@web_bp.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')

@web_bp.route('/auth/strava')
def strava_auth():
    """Redirect to Strava authorization"""
    strava_client = ReplitStravaClient(
        client_id=Config.STRAVA_CLIENT_ID,
        client_secret=Config.STRAVA_CLIENT_SECRET
    )
    
    redirect_uri = request.url_root.rstrip('/') + '/auth/strava/callback'
    auth_url = strava_client.get_authorization_url(redirect_uri)
    
    logger.info(f"Redirecting to Strava authorization: {auth_url}")
    return redirect(auth_url)

@web_bp.route('/auth/strava/callback', methods=['GET'])
def strava_callback():
    """Handle Strava OAuth callback"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        flash(f'Strava authorization failed: {error}', 'error')
        return redirect(url_for('main_routes.dashboard'))
    
    if not code:
        flash('No authorization code received from Strava', 'error')
        return redirect(url_for('main_routes.dashboard'))
    
    try:
        strava_client = ReplitStravaClient(
            client_id=Config.STRAVA_CLIENT_ID,
            client_secret=Config.STRAVA_CLIENT_SECRET
        )
        
        redirect_uri = request.url_root.rstrip('/') + '/auth/strava/callback'
        token_response = strava_client.exchange_token(code, redirect_uri)
        
        if not token_response:
            flash('Failed to exchange authorization code for access token', 'error')
            return redirect(url_for('main_routes.dashboard'))
        
        # Get athlete info from Strava
        athlete_data = strava_client.get_athlete_info(token_response['access_token'])
        
        if not athlete_data:
            flash('Failed to retrieve athlete information from Strava', 'error')
            return redirect(url_for('main_routes.dashboard'))
        
        # Check if athlete already exists
        existing_athlete = ReplitAthlete.query.filter_by(
            strava_athlete_id=athlete_data['id']
        ).first()
        
        if existing_athlete:
            # Update existing athlete
            existing_athlete.refresh_token = token_response['refresh_token']
            existing_athlete.access_token = token_response['access_token']
            existing_athlete.token_expires_at = token_response.get('expires_at')
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
                token_expires_at=token_response.get('expires_at'),
                is_active=True
            )
            db.session.add(athlete)
        
        db.session.commit()
        
        # Create JWT token for the athlete
        access_token = create_access_token(identity=athlete.id)
        
        # Store token in session or return it to frontend
        session['auth_token'] = access_token
        session['athlete_id'] = athlete.id
        
        flash(f'Successfully connected to Strava! Welcome, {athlete.name}', 'success')
        logger.info(f"Athlete {athlete.id} successfully authenticated via Strava")
        
        # Redirect to dashboard with token
        return render_template('auth_success.html', 
                             auth_token=access_token, 
                             athlete_name=athlete.name)
        
    except Exception as e:
        logger.error(f"Error during Strava callback: {str(e)}")
        flash('An error occurred during Strava authentication', 'error')
        return redirect(url_for('main_routes.dashboard'))

@web_bp.route('/auth/success')
def auth_success():
    """Display authentication success page"""
    athlete_id = request.args.get('athlete_id')
    athlete_name = request.args.get('athlete_name')
    
    return render_template('auth_success.html', 
                         athlete_id=athlete_id, 
                         athlete_name=athlete_name)

@web_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('main_routes.dashboard'))

@web_bp.route('/api/athlete-list')
def api_athlete_list():
    """API endpoint for getting athlete list (for Streamlit)"""
    try:
        athletes = ReplitAthlete.query.filter_by(is_active=True).all()
        athlete_list = [{'id': a.id, 'name': a.name} for a in athletes]
        return jsonify(athlete_list)
    except Exception as e:
        logger.error(f"Error getting athlete list: {str(e)}")
        return jsonify([])

@web_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Marathon Training Dashboard',
        'version': '1.0.0'
    })

@web_bp.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404

@web_bp.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return render_template('500.html'), 500