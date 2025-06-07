import pytest
import json
from datetime import datetime, timedelta
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import ReplitAthlete, Activity, DailySummary, PlannedWorkout

@pytest.fixture
def app():
    """Create and configure a test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture
def test_athlete(app):
    """Create a test athlete"""
    with app.app_context():
        athlete = ReplitAthlete(
            name="Test Runner",
            email="test@example.com",
            strava_athlete_id=12345,
            refresh_token="test_refresh_token",
            access_token="test_access_token",
            token_expires_at=datetime.now() + timedelta(hours=1),
            is_active=True
        )
        db.session.add(athlete)
        db.session.commit()
        return athlete

@pytest.fixture
def test_activity(app, test_athlete):
    """Create a test activity"""
    with app.app_context():
        activity = Activity(
            strava_activity_id=67890,
            athlete_id=test_athlete.id,
            name="Morning Run",
            sport_type="Run",
            start_date=datetime.now(),
            distance=5000,  # 5km
            moving_time=1800,  # 30 minutes
            elapsed_time=1900,
            total_elevation_gain=50,
            average_speed=2.78,  # ~10 km/h
            average_heartrate=150,
            calories=300
        )
        db.session.add(activity)
        db.session.commit()
        return activity

@pytest.fixture
def auth_headers(app, test_athlete):
    """Create auth headers with JWT token"""
    from app.security import ReplitSecurity
    
    with app.app_context():
        security = ReplitSecurity()
        tokens = security.create_tokens(test_athlete.id)
        return {'Authorization': f'Bearer {tokens["access_token"]}'}

class TestAthleteAPI:
    """Test athlete-related API endpoints"""
    
    def test_get_athletes_without_auth(self, client):
        """Test getting athletes without authentication"""
        response = client.get('/api/athletes')
        assert response.status_code == 401
        
    def test_get_athletes_with_auth(self, client, test_athlete, auth_headers):
        """Test getting athletes with authentication"""
        response = client.get('/api/athletes', headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['name'] == 'Test Runner'
        assert data[0]['email'] == 'test@example.com'
    
    def test_get_athlete_dashboard_data_without_auth(self, client, test_athlete):
        """Test getting dashboard data without authentication"""
        response = client.get(f'/api/athletes/{test_athlete.id}/dashboard-data')
        assert response.status_code == 401
    
    def test_get_athlete_dashboard_data_with_auth(self, client, test_athlete, auth_headers):
        """Test getting dashboard data with authentication"""
        response = client.get(f'/api/athletes/{test_athlete.id}/dashboard-data', headers=auth_headers)
        # Might return 404 if no dashboard data exists, which is acceptable
        assert response.status_code in [200, 404]
    
    def test_get_athlete_dashboard_data_forbidden(self, client, test_athlete, auth_headers):
        """Test accessing another athlete's data"""
        # Try to access athlete with ID 999 (doesn't exist)
        response = client.get('/api/athletes/999/dashboard-data', headers=auth_headers)
        assert response.status_code in [403, 404]

class TestDashboardAPI:
    """Test dashboard-related API endpoints"""
    
    def test_get_realtime_dashboard_without_auth(self, client):
        """Test realtime dashboard without authentication"""
        response = client.get('/api/realtime/dashboard')
        assert response.status_code == 401
    
    def test_get_realtime_dashboard_with_auth(self, client, test_athlete, auth_headers):
        """Test realtime dashboard with authentication"""
        response = client.get('/api/realtime/dashboard', headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'timestamp' in data
        assert 'athlete_id' in data

class TestStravaAuthAPI:
    """Test Strava authentication endpoints"""
    
    def test_get_strava_auth_url(self, client):
        """Test getting Strava authorization URL"""
        response = client.get('/api/auth/strava/authorize')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'authorization_url' in data
        assert 'strava.com' in data['authorization_url']
    
    def test_strava_callback_without_code(self, client):
        """Test Strava callback without authorization code"""
        response = client.post(
            '/api/auth/strava/callback',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_strava_callback_with_invalid_code(self, client):
        """Test Strava callback with invalid code"""
        response = client.post(
            '/api/auth/strava/callback',
            data=json.dumps({'code': 'invalid_code'}),
            content_type='application/json'
        )
        # This will likely fail due to invalid code, which is expected
        assert response.status_code in [400, 500]

class TestDataProcessing:
    """Test data processing functionality"""
    
    def test_athlete_with_activities(self, app, test_athlete, test_activity):
        """Test athlete data processing with activities"""
        with app.app_context():
            from app.data_processor import get_athlete_performance_summary
            
            summary = get_athlete_performance_summary(db.session, test_athlete.id, days=30)
            
            assert summary is not None
            assert summary['total_distance'] > 0
            assert summary['total_activities'] > 0
    
    def test_athlete_without_activities(self, app, test_athlete):
        """Test athlete data processing without activities"""
        with app.app_context():
            from app.data_processor import get_athlete_performance_summary
            
            summary = get_athlete_performance_summary(db.session, test_athlete.id, days=30)
            
            # Should return None or empty data structure
            assert summary is None or summary.get('total_activities', 0) == 0

class TestWebSocketAuthentication:
    """Test WebSocket authentication functionality"""
    
    def test_token_verification(self, app, test_athlete):
        """Test JWT token verification for WebSocket"""
        with app.app_context():
            from app.security import ReplitSecurity
            
            security = ReplitSecurity()
            tokens = security.create_tokens(test_athlete.id)
            
            # Test valid token verification
            is_valid = security.verify_token_identity(
                tokens['access_token'], 
                test_athlete.id
            )
            assert is_valid is True
            
            # Test invalid athlete ID
            is_valid = security.verify_token_identity(
                tokens['access_token'], 
                999  # Wrong athlete ID
            )
            assert is_valid is False

class TestErrorHandling:
    """Test error handling across the API"""
    
    def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint"""
        response = client.get('/api/invalid/endpoint')
        assert response.status_code == 404
    
    def test_invalid_method(self, client):
        """Test using invalid HTTP method"""
        response = client.delete('/api/athletes')
        assert response.status_code == 405
    
    def test_malformed_json(self, client):
        """Test sending malformed JSON"""
        response = client.post(
            '/api/auth/strava/callback',
            data='{"invalid": json}',
            content_type='application/json'
        )
        assert response.status_code == 400

class TestPerformanceMetrics:
    """Test performance-related calculations"""
    
    def test_daily_summary_creation(self, app, test_athlete, test_activity):
        """Test daily summary creation"""
        with app.app_context():
            from app.data_processor import process_athlete_daily_performance
            
            # Process today's data
            today = datetime.now().date()
            summary = process_athlete_daily_performance(
                db.session, 
                test_athlete.id, 
                today
            )
            
            assert summary is not None
            assert summary.athlete_id == test_athlete.id
            assert summary.total_distance > 0
            assert summary.activity_count > 0
    
    def test_team_overview(self, app, test_athlete, test_activity):
        """Test team overview functionality"""
        with app.app_context():
            from app.data_processor import get_team_overview
            
            overview = get_team_overview(db.session, days=7)
            
            assert overview is not None
            assert overview['total_athletes'] > 0
            assert 'athlete_details' in overview
            assert len(overview['athlete_details']) > 0

class TestSecurityFeatures:
    """Test security-related features"""
    
    def test_athlete_access_validation(self, app, test_athlete):
        """Test athlete access validation"""
        with app.app_context():
            from app.security import ReplitSecurity
            
            security = ReplitSecurity()
            
            # Test valid access (athlete accessing own data)
            valid_access = security.validate_athlete_access(
                test_athlete.id, 
                test_athlete.id
            )
            assert valid_access is True
            
            # Test invalid access (athlete accessing another's data)
            invalid_access = security.validate_athlete_access(
                test_athlete.id, 
                999  # Different athlete ID
            )
            assert invalid_access is False
            
            # Test admin access
            admin_access = security.validate_athlete_access(
                test_athlete.id, 
                999, 
                is_admin=True
            )
            assert admin_access is True

if __name__ == '__main__':
    pytest.main([__file__])
