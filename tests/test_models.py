import pytest
import json
from datetime import datetime, timedelta
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import (
    ReplitAthlete, Activity, PlannedWorkout, DailySummary, 
    SystemLog, StravaApiUsage, OptimalValues, NotificationLog
)

@pytest.fixture
def app():
    """Create and configure a test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

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
            is_active=True,
            ftp=250.0,
            lthr=165,
            max_hr=190
        )
        
        # Set training zones
        athlete.set_training_zones({
            'hr_zones': [95, 114, 133, 152, 171, 190],
            'power_zones': [125, 162, 200, 237, 275, 312]
        })
        
        # Set preferences
        athlete.set_preferences({
            'notification_daily_summary': True,
            'unit_preference': 'metric',
            'email_alerts': True
        })
        
        db.session.add(athlete)
        db.session.commit()
        return athlete

class TestReplitAthleteModel:
    """Test the ReplitAthlete model"""
    
    def test_athlete_creation(self, app, test_athlete):
        """Test basic athlete creation"""
        with app.app_context():
            athlete = db.session.query(ReplitAthlete).filter_by(id=test_athlete.id).first()
            
            assert athlete is not None
            assert athlete.name == "Test Runner"
            assert athlete.email == "test@example.com"
            assert athlete.strava_athlete_id == 12345
            assert athlete.is_active is True
            assert athlete.ftp == 250.0
            assert athlete.lthr == 165
            assert athlete.max_hr == 190
    
    def test_preferences_json_handling(self, app, test_athlete):
        """Test JSON preferences handling"""
        with app.app_context():
            athlete = db.session.query(ReplitAthlete).filter_by(id=test_athlete.id).first()
            
            # Test getting preferences
            prefs = athlete.get_preferences()
            assert isinstance(prefs, dict)
            assert prefs['notification_daily_summary'] is True
            assert prefs['unit_preference'] == 'metric'
            assert prefs['email_alerts'] is True
            
            # Test setting new preferences
            new_prefs = {
                'notification_daily_summary': False,
                'unit_preference': 'imperial',
                'theme': 'dark'
            }
            athlete.set_preferences(new_prefs)
            db.session.commit()
            
            # Verify changes
            updated_prefs = athlete.get_preferences()
            assert updated_prefs['notification_daily_summary'] is False
            assert updated_prefs['unit_preference'] == 'imperial'
            assert updated_prefs['theme'] == 'dark'
    
    def test_training_zones_json_handling(self, app, test_athlete):
        """Test JSON training zones handling"""
        with app.app_context():
            athlete = db.session.query(ReplitAthlete).filter_by(id=test_athlete.id).first()
            
            # Test getting training zones
            zones = athlete.get_training_zones()
            assert isinstance(zones, dict)
            assert 'hr_zones' in zones
            assert 'power_zones' in zones
            assert len(zones['hr_zones']) == 6
            assert len(zones['power_zones']) == 6
            
            # Test setting new zones
            new_zones = {
                'hr_zones': [100, 120, 140, 160, 180, 200],
                'pace_zones': [300, 270, 240, 210, 180, 150]  # seconds per km
            }
            athlete.set_training_zones(new_zones)
            db.session.commit()
            
            # Verify changes
            updated_zones = athlete.get_training_zones()
            assert updated_zones['hr_zones'][0] == 100
            assert 'pace_zones' in updated_zones
            assert len(updated_zones['pace_zones']) == 6
    
    def test_athlete_repr(self, app, test_athlete):
        """Test athlete string representation"""
        with app.app_context():
            athlete = db.session.query(ReplitAthlete).filter_by(id=test_athlete.id).first()
            repr_str = repr(athlete)
            
            assert "ReplitAthlete" in repr_str
            assert str(athlete.id) in repr_str
            assert athlete.name in repr_str
            assert str(athlete.strava_athlete_id) in repr_str

class TestActivityModel:
    """Test the Activity model"""
    
    def test_activity_creation(self, app, test_athlete):
        """Test basic activity creation"""
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
                max_speed=3.33,
                average_cadence=180,
                average_heartrate=150,
                max_heartrate=165,
                calories=300,
                suffer_score=45,
                training_stress_score=55,
                intensity_factor=0.75
            )
            
            db.session.add(activity)
            db.session.commit()
            
            # Verify creation
            saved_activity = db.session.query(Activity).filter_by(id=activity.id).first()
            assert saved_activity is not None
            assert saved_activity.name == "Morning Run"
            assert saved_activity.sport_type == "Run"
            assert saved_activity.distance == 5000
            assert saved_activity.athlete_id == test_athlete.id
    
    def test_activity_detailed_data_json(self, app, test_athlete):
        """Test activity detailed data JSON handling"""
        with app.app_context():
            activity = Activity(
                strava_activity_id=67891,
                athlete_id=test_athlete.id,
                name="Interval Training",
                sport_type="Run",
                start_date=datetime.now(),
                distance=8000,
                moving_time=2400
            )
            
            # Set detailed data
            detailed_data = {
                'heart_rate_stream': [140, 145, 150, 155, 160, 150, 145],
                'pace_stream': [300, 290, 280, 270, 280, 290, 300],
                'elevation_stream': [100, 102, 105, 103, 101, 99, 98],
                'cadence_stream': [170, 175, 180, 185, 180, 175, 170]
            }
            activity.set_detailed_data(detailed_data)
            
            db.session.add(activity)
            db.session.commit()
            
            # Verify detailed data
            saved_activity = db.session.query(Activity).filter_by(id=activity.id).first()
            retrieved_data = saved_activity.get_detailed_data()
            
            assert isinstance(retrieved_data, dict)
            assert 'heart_rate_stream' in retrieved_data
            assert len(retrieved_data['heart_rate_stream']) == 7
            assert retrieved_data['pace_stream'][3] == 270
    
    def test_activity_athlete_relationship(self, app, test_athlete):
        """Test activity-athlete relationship"""
        with app.app_context():
            activity = Activity(
                strava_activity_id=67892,
                athlete_id=test_athlete.id,
                name="Recovery Run",
                sport_type="Run",
                start_date=datetime.now(),
                distance=3000,
                moving_time=1200
            )
            
            db.session.add(activity)
            db.session.commit()
            
            # Test relationship from activity to athlete
            assert activity.athlete.name == test_athlete.name
            
            # Test relationship from athlete to activities
            athlete = db.session.query(ReplitAthlete).filter_by(id=test_athlete.id).first()
            assert len(athlete.activities) > 0
            assert activity in athlete.activities

class TestPlannedWorkoutModel:
    """Test the PlannedWorkout model"""
    
    def test_planned_workout_creation(self, app, test_athlete):
        """Test planned workout creation"""
        with app.app_context():
            workout = PlannedWorkout(
                athlete_id=test_athlete.id,
                planned_date=datetime.now() + timedelta(days=1),
                workout_type="Tempo Run",
                planned_distance=8000,
                planned_duration=2400,
                planned_intensity="Moderate"
            )
            
            # Set workout structure
            structure = {
                'warmup': {'duration': 600, 'intensity': 'easy'},
                'main': {'duration': 1200, 'intensity': 'tempo'},
                'cooldown': {'duration': 600, 'intensity': 'easy'}
            }
            workout.set_workout_structure(structure)
            
            db.session.add(workout)
            db.session.commit()
            
            # Verify creation
            saved_workout = db.session.query(PlannedWorkout).filter_by(id=workout.id).first()
            assert saved_workout is not None
            assert saved_workout.workout_type == "Tempo Run"
            assert saved_workout.planned_distance == 8000
            assert saved_workout.is_completed is False
            
            # Verify workout structure
            retrieved_structure = saved_workout.get_workout_structure()
            assert 'warmup' in retrieved_structure
            assert retrieved_structure['main']['intensity'] == 'tempo'

class TestDailySummaryModel:
    """Test the DailySummary model"""
    
    def test_daily_summary_creation(self, app, test_athlete):
        """Test daily summary creation"""
        with app.app_context():
            summary = DailySummary(
                athlete_id=test_athlete.id,
                summary_date=datetime.now(),
                total_distance=10000,
                total_moving_time=3600,
                total_elevation_gain=100,
                activity_count=2,
                average_pace=360,  # 6 min/km
                average_heart_rate=155,
                training_load=75,
                planned_vs_actual_distance=95.0,
                planned_vs_actual_duration=98.0,
                status="On Track"
            )
            
            # Set insights
            insights = {
                'performance_notes': ['Good pace consistency', 'Heart rate in target zone'],
                'recommendations': ['Consider adding strength training'],
                'alerts': []
            }
            summary.set_insights(insights)
            
            db.session.add(summary)
            db.session.commit()
            
            # Verify creation
            saved_summary = db.session.query(DailySummary).filter_by(id=summary.id).first()
            assert saved_summary is not None
            assert saved_summary.total_distance == 10000
            assert saved_summary.status == "On Track"
            
            # Verify insights
            retrieved_insights = saved_summary.get_insights()
            assert len(retrieved_insights['performance_notes']) == 2
            assert len(retrieved_insights['recommendations']) == 1
            assert len(retrieved_insights['alerts']) == 0

class TestSystemLogModel:
    """Test the SystemLog model"""
    
    def test_system_log_creation(self, app, test_athlete):
        """Test system log creation"""
        with app.app_context():
            log_entry = SystemLog(
                level='INFO',
                message='Daily processing completed',
                module='data_processor',
                athlete_id=test_athlete.id
            )
            
            # Set context
            context = {
                'processing_date': datetime.now().isoformat(),
                'activities_processed': 3,
                'duration_seconds': 45.2
            }
            log_entry.set_context(context)
            
            db.session.add(log_entry)
            db.session.commit()
            
            # Verify creation
            saved_log = db.session.query(SystemLog).filter_by(id=log_entry.id).first()
            assert saved_log is not None
            assert saved_log.level == 'INFO'
            assert saved_log.module == 'data_processor'
            
            # Verify context
            retrieved_context = saved_log.get_context()
            assert retrieved_context['activities_processed'] == 3
            assert retrieved_context['duration_seconds'] == 45.2

class TestStravaApiUsageModel:
    """Test the StravaApiUsage model"""
    
    def test_api_usage_logging(self, app, test_athlete):
        """Test Strava API usage logging"""
        with app.app_context():
            api_usage = StravaApiUsage(
                athlete_id=test_athlete.id,
                endpoint='get_activities',
                response_code=200,
                rate_limit_usage='150/1000'
            )
            
            db.session.add(api_usage)
            db.session.commit()
            
            # Verify creation
            saved_usage = db.session.query(StravaApiUsage).filter_by(id=api_usage.id).first()
            assert saved_usage is not None
            assert saved_usage.endpoint == 'get_activities'
            assert saved_usage.response_code == 200
            assert saved_usage.rate_limit_usage == '150/1000'

class TestOptimalValuesModel:
    """Test the OptimalValues model"""
    
    def test_optimal_values_creation(self, app, test_athlete):
        """Test optimal values creation"""
        with app.app_context():
            optimal = OptimalValues(
                athlete_id=test_athlete.id,
                weekly_distance_target=50000,  # 50km
                weekly_elevation_target=500,   # 500m
                target_race_pace=300,          # 5 min/km
                target_long_run_pace=360,      # 6 min/km
                optimal_rest_days_per_week=2,
                max_consecutive_training_days=5,
                aerobic_threshold_pace=390,     # 6.5 min/km
                anaerobic_threshold_pace=330,   # 5.5 min/km
                vo2_max_pace=270               # 4.5 min/km
            )
            
            db.session.add(optimal)
            db.session.commit()
            
            # Verify creation
            saved_optimal = db.session.query(OptimalValues).filter_by(id=optimal.id).first()
            assert saved_optimal is not None
            assert saved_optimal.weekly_distance_target == 50000
            assert saved_optimal.optimal_rest_days_per_week == 2

class TestNotificationLogModel:
    """Test the NotificationLog model"""
    
    def test_notification_log_creation(self, app, test_athlete):
        """Test notification log creation"""
        with app.app_context():
            notification = NotificationLog(
                athlete_id=test_athlete.id,
                notification_type='email',
                subject='Daily Training Summary',
                message='Your daily training summary is ready',
                status='sent'
            )
            
            db.session.add(notification)
            db.session.commit()
            
            # Verify creation
            saved_notification = db.session.query(NotificationLog).filter_by(id=notification.id).first()
            assert saved_notification is not None
            assert saved_notification.notification_type == 'email'
            assert saved_notification.status == 'sent'

class TestModelRelationships:
    """Test relationships between models"""
    
    def test_athlete_activities_relationship(self, app, test_athlete):
        """Test athlete-activities relationship"""
        with app.app_context():
            # Create multiple activities
            for i in range(3):
                activity = Activity(
                    strava_activity_id=70000 + i,
                    athlete_id=test_athlete.id,
                    name=f"Run {i+1}",
                    sport_type="Run",
                    start_date=datetime.now() - timedelta(days=i),
                    distance=5000 + (i * 1000),
                    moving_time=1800 + (i * 300)
                )
                db.session.add(activity)
            
            db.session.commit()
            
            # Test relationship
            athlete = db.session.query(ReplitAthlete).filter_by(id=test_athlete.id).first()
            assert len(athlete.activities) == 3
            
            # Test that activities are properly linked
            for activity in athlete.activities:
                assert activity.athlete_id == test_athlete.id
                assert activity.athlete.name == test_athlete.name
    
    def test_athlete_summaries_relationship(self, app, test_athlete):
        """Test athlete-daily summaries relationship"""
        with app.app_context():
            # Create multiple daily summaries
            for i in range(5):
                summary = DailySummary(
                    athlete_id=test_athlete.id,
                    summary_date=datetime.now() - timedelta(days=i),
                    total_distance=8000 + (i * 1000),
                    total_moving_time=2400 + (i * 300),
                    activity_count=1 + i,
                    status="On Track"
                )
                db.session.add(summary)
            
            db.session.commit()
            
            # Test relationship
            athlete = db.session.query(ReplitAthlete).filter_by(id=test_athlete.id).first()
            assert len(athlete.daily_summaries) == 5
            
            # Test that summaries are properly linked
            for summary in athlete.daily_summaries:
                assert summary.athlete_id == test_athlete.id

if __name__ == '__main__':
    pytest.main([__file__])
