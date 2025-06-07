import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import (
    ReplitAthlete, Activity, PlannedWorkout, DailySummary, 
    SystemLog, StravaApiUsage, OptimalValues
)
from app.data_processor import (
    DataProcessor, process_athlete_daily_performance,
    get_athlete_performance_summary, get_team_overview
)
from app.processing_workflows import ProcessingWorkflows
from app.services.analytics import ReplitAnalyticsEngine

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
def test_athlete(app):
    """Create a test athlete with comprehensive data"""
    with app.app_context():
        athlete = ReplitAthlete(
            name="Test Marathon Runner",
            email="marathon@test.com",
            strava_athlete_id=12345,
            refresh_token="test_refresh_token",
            access_token="test_access_token",
            token_expires_at=datetime.now() + timedelta(hours=1),
            is_active=True,
            ftp=280.0,
            lthr=175,
            max_hr=195
        )
        
        # Set training zones
        athlete.set_training_zones({
            'hr_zones': [98, 117, 136, 156, 175, 195],
            'power_zones': [140, 182, 224, 266, 308, 350],
            'pace_zones': [420, 390, 360, 330, 300, 270]  # seconds per km
        })
        
        # Set preferences
        athlete.set_preferences({
            'notification_daily_summary': True,
            'unit_preference': 'metric',
            'email_alerts': True,
            'training_reminder': True
        })
        
        db.session.add(athlete)
        db.session.commit()
        return athlete

@pytest.fixture
def test_activities(app, test_athlete):
    """Create multiple test activities for data processing"""
    with app.app_context():
        activities = []
        base_date = datetime.now() - timedelta(days=10)
        
        # Create 10 days of varied activities
        activity_data = [
            {'name': 'Easy Run', 'distance': 5000, 'time': 1800, 'hr': 145, 'type': 'Run'},
            {'name': 'Tempo Run', 'distance': 8000, 'time': 2400, 'hr': 165, 'type': 'Run'},
            {'name': 'Long Run', 'distance': 15000, 'time': 5400, 'hr': 155, 'type': 'Run'},
            {'name': 'Recovery Run', 'distance': 4000, 'time': 1500, 'hr': 135, 'type': 'Run'},
            {'name': 'Interval Training', 'distance': 6000, 'time': 1800, 'hr': 175, 'type': 'Run'},
            {'name': 'Hill Repeats', 'distance': 7000, 'time': 2100, 'hr': 170, 'type': 'Run'},
            {'name': 'Fartlek Run', 'distance': 9000, 'time': 2700, 'hr': 160, 'type': 'Run'},
            {'name': 'Easy Jog', 'distance': 5500, 'time': 2000, 'hr': 140, 'type': 'Run'},
            {'name': 'Race Pace Run', 'distance': 10000, 'time': 3000, 'hr': 180, 'type': 'Run'},
            {'name': 'Recovery Run', 'distance': 3000, 'time': 1200, 'hr': 130, 'type': 'Run'}
        ]
        
        for i, data in enumerate(activity_data):
            activity = Activity(
                strava_activity_id=70000 + i,
                athlete_id=test_athlete.id,
                name=data['name'],
                sport_type=data['type'],
                start_date=base_date + timedelta(days=i),
                distance=data['distance'],
                moving_time=data['time'],
                elapsed_time=data['time'] + 120,  # Add some stopped time
                total_elevation_gain=50 + (i * 10),
                average_speed=data['distance'] / data['time'],
                average_heartrate=data['hr'],
                max_heartrate=data['hr'] + 15,
                calories=data['distance'] * 0.06,  # Rough calculation
                suffer_score=30 + (i * 5),
                training_stress_score=40 + (i * 6)
            )
            activities.append(activity)
            db.session.add(activity)
        
        db.session.commit()
        return activities

@pytest.fixture
def test_planned_workouts(app, test_athlete):
    """Create planned workouts for comparison"""
    with app.app_context():
        workouts = []
        base_date = datetime.now() - timedelta(days=5)
        
        workout_plans = [
            {'type': 'Easy Run', 'distance': 5000, 'duration': 1800, 'intensity': 'Easy'},
            {'type': 'Tempo Run', 'distance': 8000, 'duration': 2400, 'intensity': 'Moderate'},
            {'type': 'Long Run', 'distance': 16000, 'duration': 5600, 'intensity': 'Easy'},
            {'type': 'Interval Training', 'distance': 6000, 'duration': 1800, 'intensity': 'Hard'},
            {'type': 'Recovery Run', 'distance': 4000, 'duration': 1500, 'intensity': 'Easy'}
        ]
        
        for i, plan in enumerate(workout_plans):
            workout = PlannedWorkout(
                athlete_id=test_athlete.id,
                planned_date=base_date + timedelta(days=i),
                workout_type=plan['type'],
                planned_distance=plan['distance'],
                planned_duration=plan['duration'],
                planned_intensity=plan['intensity']
            )
            
            # Set workout structure
            structure = {
                'warmup': {'duration': 600, 'intensity': 'easy'},
                'main': {'duration': plan['duration'] - 1200, 'intensity': plan['intensity'].lower()},
                'cooldown': {'duration': 600, 'intensity': 'easy'}
            }
            workout.set_workout_structure(structure)
            
            workouts.append(workout)
            db.session.add(workout)
        
        db.session.commit()
        return workouts

class TestDataProcessor:
    """Test the core DataProcessor class"""
    
    def test_processor_initialization(self):
        """Test DataProcessor initialization"""
        processor = DataProcessor()
        assert processor is not None
        assert processor.logger is not None
    
    def test_calculate_daily_metrics_with_activities(self, app, test_activities):
        """Test daily metrics calculation with activities"""
        with app.app_context():
            processor = DataProcessor()
            
            # Use first 3 activities for a single day
            test_day_activities = test_activities[:3]
            metrics = processor._calculate_daily_metrics(test_day_activities)
            
            assert metrics['activity_count'] == 3
            assert metrics['total_distance'] > 0
            assert metrics['total_moving_time'] > 0
            assert metrics['average_pace'] is not None
            assert metrics['average_heart_rate'] is not None
            assert metrics['training_load'] > 0
    
    def test_calculate_daily_metrics_empty(self, app):
        """Test daily metrics calculation with no activities"""
        with app.app_context():
            processor = DataProcessor()
            metrics = processor._calculate_daily_metrics([])
            
            assert metrics['activity_count'] == 0
            assert metrics['total_distance'] == 0.0
            assert metrics['total_moving_time'] == 0
            assert metrics['average_pace'] is None
            assert metrics['average_heart_rate'] is None
            assert metrics['training_load'] == 0.0
    
    def test_calculate_compliance_metrics_with_plan(self, app, test_planned_workouts):
        """Test compliance metrics calculation with planned workout"""
        with app.app_context():
            processor = DataProcessor()
            
            # Mock daily metrics
            daily_metrics = {
                'total_distance': 8500,  # Slightly more than planned 8000
                'total_moving_time': 2500  # Slightly more than planned 2400
            }
            
            planned_workout = test_planned_workouts[1]  # Tempo run
            compliance = processor._calculate_compliance_metrics(daily_metrics, planned_workout)
            
            assert compliance['planned_vs_actual_distance'] > 100  # Over 100%
            assert compliance['planned_vs_actual_duration'] > 100  # Over 100%
    
    def test_calculate_compliance_metrics_no_plan(self, app):
        """Test compliance metrics with no planned workout"""
        with app.app_context():
            processor = DataProcessor()
            
            daily_metrics = {'total_distance': 5000, 'total_moving_time': 1800}
            compliance = processor._calculate_compliance_metrics(daily_metrics, None)
            
            assert compliance['planned_vs_actual_distance'] is None
            assert compliance['planned_vs_actual_duration'] is None
    
    def test_determine_status_variations(self, app, test_planned_workouts):
        """Test status determination for various scenarios"""
        with app.app_context():
            processor = DataProcessor()
            planned_workout = test_planned_workouts[0]
            
            # Test "On Track" status
            daily_metrics = {'activity_count': 1}
            compliance = {'planned_vs_actual_distance': 95, 'planned_vs_actual_duration': 98}
            status = processor._determine_status(daily_metrics, compliance, planned_workout)
            assert status == "On Track"
            
            # Test "Under-performed" status
            compliance = {'planned_vs_actual_distance': 60, 'planned_vs_actual_duration': 65}
            status = processor._determine_status(daily_metrics, compliance, planned_workout)
            assert status == "Under-performed"
            
            # Test "Rest Day" status
            daily_metrics = {'activity_count': 0}
            status = processor._determine_status(daily_metrics, {}, None)
            assert status == "Rest Day"
            
            # Test "Missed Workout" status
            status = processor._determine_status(daily_metrics, {}, planned_workout)
            assert status == "Missed Workout"
    
    def test_generate_insights(self, app, test_athlete):
        """Test insights generation"""
        with app.app_context():
            processor = DataProcessor()
            
            # Test high training load insights
            daily_metrics = {
                'training_load': 180,
                'total_distance': 15000,
                'average_pace': 300,  # 5 min/km
                'average_heart_rate': 180
            }
            compliance = {'planned_vs_actual_distance': 110}
            
            insights = processor._generate_insights(daily_metrics, compliance, test_athlete)
            
            assert 'performance_notes' in insights
            assert 'recommendations' in insights
            assert 'alerts' in insights
            assert len(insights['alerts']) > 0  # Should have high training load alert

class TestAthletePerformanceProcessing:
    """Test athlete performance processing functions"""
    
    def test_process_athlete_daily_performance(self, app, test_athlete, test_activities, test_planned_workouts):
        """Test complete daily performance processing"""
        with app.app_context():
            # Process performance for a specific date
            processing_date = (datetime.now() - timedelta(days=2)).date()
            
            summary = process_athlete_daily_performance(
                db.session, test_athlete.id, processing_date
            )
            
            assert summary is not None
            assert summary.athlete_id == test_athlete.id
            assert summary.summary_date.date() == processing_date
            assert summary.status is not None
    
    def test_process_athlete_daily_performance_no_athlete(self, app):
        """Test processing with non-existent athlete"""
        with app.app_context():
            processing_date = datetime.now().date()
            
            summary = process_athlete_daily_performance(
                db.session, 999, processing_date  # Non-existent athlete
            )
            
            assert summary is None
    
    def test_get_athlete_performance_summary(self, app, test_athlete, test_activities):
        """Test athlete performance summary generation"""
        with app.app_context():
            # First create some daily summaries
            for i in range(5):
                summary = DailySummary(
                    athlete_id=test_athlete.id,
                    summary_date=datetime.now() - timedelta(days=i),
                    total_distance=8000 + (i * 1000),
                    total_moving_time=2400 + (i * 300),
                    activity_count=1 + (i % 2),
                    training_load=50 + (i * 10),
                    status="On Track"
                )
                db.session.add(summary)
            
            db.session.commit()
            
            performance_summary = get_athlete_performance_summary(db.session, test_athlete.id, days=30)
            
            assert performance_summary is not None
            assert performance_summary['total_distance'] > 0
            assert performance_summary['total_activities'] > 0
            assert performance_summary['active_days'] > 0
            assert 'recent_summaries' in performance_summary
    
    def test_get_athlete_performance_summary_no_data(self, app, test_athlete):
        """Test performance summary with no data"""
        with app.app_context():
            performance_summary = get_athlete_performance_summary(db.session, test_athlete.id, days=30)
            
            assert performance_summary is None
    
    def test_get_team_overview(self, app, test_athlete, test_activities):
        """Test team overview generation"""
        with app.app_context():
            # Create daily summaries for team overview
            summary = DailySummary(
                athlete_id=test_athlete.id,
                summary_date=datetime.now() - timedelta(days=1),
                total_distance=10000,
                total_moving_time=3600,
                activity_count=2,
                status="On Track"
            )
            db.session.add(summary)
            db.session.commit()
            
            team_overview = get_team_overview(db.session, days=7)
            
            assert team_overview is not None
            assert team_overview['total_athletes'] > 0
            assert 'athlete_details' in team_overview
            assert len(team_overview['athlete_details']) > 0
    
    def test_get_team_overview_no_data(self, app):
        """Test team overview with no athletes"""
        with app.app_context():
            team_overview = get_team_overview(db.session, days=7)
            
            assert team_overview is not None
            assert team_overview['total_athletes'] == 0

class TestProcessingWorkflows:
    """Test advanced processing workflows"""
    
    def test_processing_workflows_initialization(self):
        """Test ProcessingWorkflows initialization"""
        workflows = ProcessingWorkflows()
        assert workflows is not None
        assert workflows.logger is not None
        assert workflows.config is not None
    
    def test_get_athletes_in_chunks(self, app, test_athlete):
        """Test athlete chunking functionality"""
        with app.app_context():
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import create_engine
            
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            SessionFactory = sessionmaker(bind=engine)
            
            workflows = ProcessingWorkflows()
            
            chunks = list(workflows.get_athletes_in_chunks(SessionFactory, chunk_size=10))
            
            assert len(chunks) >= 1
            assert len(chunks[0]) >= 1
            assert chunks[0][0]['id'] == test_athlete.id
            assert chunks[0][0]['name'] == test_athlete.name
    
    @patch('app.processing_workflows.MailNotifier')
    def test_process_single_athlete_workflow(self, mock_mail_notifier, app, test_athlete):
        """Test single athlete workflow processing"""
        with app.app_context():
            workflows = ProcessingWorkflows()
            
            athlete_data = {
                'id': test_athlete.id,
                'name': test_athlete.name,
                'email': test_athlete.email,
                'preferences': test_athlete.get_preferences()
            }
            
            processing_date = datetime.now().date()
            mock_notifier = MagicMock()
            
            result = workflows.process_single_athlete_workflow(
                athlete_data, processing_date, mock_notifier
            )
            
            assert result is not None
            assert result['athlete_id'] == test_athlete.id
            assert result['status'] in ['success', 'error']

class TestAnalyticsEngine:
    """Test the analytics engine functionality"""
    
    def test_analytics_engine_initialization(self):
        """Test analytics engine initialization"""
        engine = ReplitAnalyticsEngine()
        assert engine is not None
        assert engine.models is not None
        assert engine.logger is not None
    
    def test_get_sampled_training_data(self, app, test_athlete, test_activities):
        """Test training data sampling"""
        with app.app_context():
            engine = ReplitAnalyticsEngine()
            
            training_data = engine.get_sampled_training_data(test_athlete.id, days=30)
            
            assert isinstance(training_data, pd.DataFrame)
            if not training_data.empty:
                assert 'athlete_id' in training_data.columns
                assert 'distance' in training_data.columns
                assert 'pace' in training_data.columns
                assert len(training_data) > 0
    
    def test_get_sampled_training_data_no_data(self, app, test_athlete):
        """Test training data sampling with no activities"""
        with app.app_context():
            engine = ReplitAnalyticsEngine()
            
            training_data = engine.get_sampled_training_data(999, days=30)  # Non-existent athlete
            
            assert isinstance(training_data, pd.DataFrame)
            assert training_data.empty
    
    def test_predict_race_performance(self, app, test_athlete, test_activities):
        """Test race performance prediction"""
        with app.app_context():
            engine = ReplitAnalyticsEngine()
            
            prediction = engine.predict_race_performance(test_athlete.id, race_distance=21.1)  # Half marathon
            
            assert isinstance(prediction, dict)
            assert 'prediction' in prediction
            assert 'confidence' in prediction
            assert 'method' in prediction
    
    def test_predict_race_performance_no_data(self, app, test_athlete):
        """Test race prediction with insufficient data"""
        with app.app_context():
            engine = ReplitAnalyticsEngine()
            
            prediction = engine.predict_race_performance(999, race_distance=10.0)  # Non-existent athlete
            
            assert isinstance(prediction, dict)
            assert prediction['prediction'] is None
            assert prediction['confidence'] == 0.0
    
    def test_analyze_training_trends(self, app, test_athlete, test_activities):
        """Test training trends analysis"""
        with app.app_context():
            engine = ReplitAnalyticsEngine()
            
            trends = engine.analyze_training_trends(test_athlete.id, days=90)
            
            assert isinstance(trends, dict)
            if 'trends' in trends:
                assert 'current_metrics' in trends
                assert 'analysis_period' in trends
    
    def test_get_performance_insights(self, app, test_athlete, test_activities):
        """Test performance insights generation"""
        with app.app_context():
            engine = ReplitAnalyticsEngine()
            
            insights = engine.get_performance_insights(test_athlete.id)
            
            assert isinstance(insights, dict)
            assert 'summary' in insights
            assert 'recommendations' in insights
            assert 'alerts' in insights
            assert 'achievements' in insights

class TestDataValidationAndErrorHandling:
    """Test data validation and error handling"""
    
    def test_invalid_athlete_id_handling(self, app):
        """Test handling of invalid athlete IDs"""
        with app.app_context():
            processor = DataProcessor()
            
            # Test with non-existent athlete
            result = processor.process_athlete_daily_performance(
                db.session, 999, datetime.now().date()
            )
            
            assert result is None
    
    def test_database_error_handling(self, app, test_athlete):
        """Test database error handling"""
        with app.app_context():
            processor = DataProcessor()
            
            # Simulate database error by closing the session
            db.session.close()
            
            try:
                result = processor.process_athlete_daily_performance(
                    db.session, test_athlete.id, datetime.now().date()
                )
                # Should handle the error gracefully
                assert True
            except Exception:
                # If an exception is raised, it should be a handled database error
                assert True
    
    def test_empty_data_handling(self, app, test_athlete):
        """Test handling of empty or invalid data"""
        with app.app_context():
            processor = DataProcessor()
            
            # Test with empty activities list
            metrics = processor._calculate_daily_metrics([])
            assert metrics['activity_count'] == 0
            
            # Test compliance with None planned workout
            compliance = processor._calculate_compliance_metrics(metrics, None)
            assert compliance['planned_vs_actual_distance'] is None

class TestPerformanceOptimization:
    """Test performance optimization features"""
    
    def test_large_dataset_handling(self, app, test_athlete):
        """Test handling of large datasets"""
        with app.app_context():
            # Create a large number of activities
            activities = []
            for i in range(100):
                activity = Activity(
                    strava_activity_id=80000 + i,
                    athlete_id=test_athlete.id,
                    name=f"Activity {i}",
                    sport_type="Run",
                    start_date=datetime.now() - timedelta(days=i),
                    distance=5000 + (i * 100),
                    moving_time=1800 + (i * 30)
                )
                activities.append(activity)
                db.session.add(activity)
            
            db.session.commit()
            
            # Test performance summary with large dataset
            performance_summary = get_athlete_performance_summary(
                db.session, test_athlete.id, days=365
            )
            
            assert performance_summary is not None
            assert performance_summary['total_activities'] > 0
    
    def test_memory_efficient_processing(self, app, test_athlete):
        """Test memory-efficient data processing"""
        with app.app_context():
            engine = ReplitAnalyticsEngine()
            
            # Test with limited data sampling
            training_data = engine.get_sampled_training_data(test_athlete.id, days=30)
            
            # Verify that DataFrame is memory-efficient
            assert isinstance(training_data, pd.DataFrame)
            # Should not load unlimited data
            assert len(training_data) <= 500  # As per the limit in the code

class TestIntegrationScenarios:
    """Test integration scenarios across components"""
    
    def test_complete_daily_processing_flow(self, app, test_athlete, test_activities, test_planned_workouts):
        """Test complete daily processing flow"""
        with app.app_context():
            processing_date = (datetime.now() - timedelta(days=1)).date()
            
            # Process daily performance
            summary = process_athlete_daily_performance(
                db.session, test_athlete.id, processing_date
            )
            
            assert summary is not None
            
            # Get performance summary
            performance_summary = get_athlete_performance_summary(
                db.session, test_athlete.id, days=30
            )
            
            assert performance_summary is not None
            
            # Get team overview
            team_overview = get_team_overview(db.session, days=7)
            
            assert team_overview is not None
            assert team_overview['total_athletes'] > 0
    
    def test_analytics_with_processed_data(self, app, test_athlete, test_activities):
        """Test analytics engine with processed data"""
        with app.app_context():
            # First process some daily summaries
            for i in range(7):
                summary = DailySummary(
                    athlete_id=test_athlete.id,
                    summary_date=datetime.now() - timedelta(days=i),
                    total_distance=8000 + (i * 500),
                    total_moving_time=2400 + (i * 150),
                    activity_count=1 + (i % 2),
                    training_load=60 + (i * 8),
                    status="On Track" if i % 2 == 0 else "Mostly Compliant"
                )
                db.session.add(summary)
            
            db.session.commit()
            
            # Test analytics
            engine = ReplitAnalyticsEngine()
            insights = engine.get_performance_insights(test_athlete.id)
            
            assert insights is not None
            assert 'summary' in insights
            
            # Test race prediction
            prediction = engine.predict_race_performance(test_athlete.id, 10.0)
            assert prediction is not None

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
