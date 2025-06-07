import datetime
import json
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, BigInteger, Text, ForeignKey
from sqlalchemy.orm import relationship
from app import db

class ReplitAthlete(db.Model):
    """
    Optimized for Replit's SQLite/PostgreSQL, handling multiple athletes.
    Includes fields for personalized settings and performance benchmarks.
    """
    __tablename__ = 'athletes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    strava_athlete_id = Column(BigInteger, unique=True, nullable=False)
    refresh_token = Column(Text, nullable=False)
    access_token = Column(Text)
    token_expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Performance metrics
    ftp = Column(Float)  # Functional Threshold Power
    lthr = Column(Integer)  # Lactate Threshold Heart Rate
    max_hr = Column(Integer)  # Maximum Heart Rate
    
    # JSON fields stored as TEXT for SQLite compatibility
    training_zones = Column(Text)  # JSON string
    preferences = Column(Text)  # JSON string
    
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Relationships
    activities = relationship("Activity", back_populates="athlete")
    planned_workouts = relationship("PlannedWorkout", back_populates="athlete")
    daily_summaries = relationship("DailySummary", back_populates="athlete")
    
    def get_preferences(self):
        """Parse JSON preferences"""
        if self.preferences:
            try:
                return json.loads(self.preferences)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_preferences(self, prefs_dict):
        """Set JSON preferences"""
        self.preferences = json.dumps(prefs_dict)
    
    def get_training_zones(self):
        """Parse JSON training zones"""
        if self.training_zones:
            try:
                return json.loads(self.training_zones)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_training_zones(self, zones_dict):
        """Set JSON training zones"""
        self.training_zones = json.dumps(zones_dict)
    
    def __repr__(self):
        return f"<ReplitAthlete(id={self.id}, name='{self.name}', strava_id={self.strava_athlete_id})>"

class Activity(db.Model):
    """Enhanced Activity model for detailed data points"""
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True)
    strava_activity_id = Column(BigInteger, unique=True, nullable=False)
    athlete_id = Column(Integer, ForeignKey('athletes.id'), nullable=False)
    
    # Basic metrics
    name = Column(String(255), nullable=False)
    sport_type = Column(String(50), nullable=False)
    start_date = Column(DateTime, nullable=False)
    distance = Column(Float)  # in meters
    moving_time = Column(Integer)  # in seconds
    elapsed_time = Column(Integer)  # in seconds
    total_elevation_gain = Column(Float)  # in meters
    
    # Performance metrics
    average_speed = Column(Float)  # m/s
    max_speed = Column(Float)  # m/s
    average_cadence = Column(Float)
    average_heartrate = Column(Float)
    max_heartrate = Column(Float)
    calories = Column(Float)
    
    # Training metrics
    suffer_score = Column(Float)
    training_stress_score = Column(Float)
    intensity_factor = Column(Float)
    
    # Additional data as JSON
    detailed_data = Column(Text)  # JSON string for streams data
    
    created_at = Column(DateTime, default=datetime.datetime.now)
    
    # Relationships
    athlete = relationship("ReplitAthlete", back_populates="activities")
    
    def get_detailed_data(self):
        """Parse JSON detailed data"""
        if self.detailed_data:
            try:
                return json.loads(self.detailed_data)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_detailed_data(self, data_dict):
        """Set JSON detailed data"""
        self.detailed_data = json.dumps(data_dict)
    
    def __repr__(self):
        return f"<Activity(id={self.id}, name='{self.name}', athlete_id={self.athlete_id})>"

class PlannedWorkout(db.Model):
    """Planned workout model for comparison with actual activities"""
    __tablename__ = 'planned_workouts'
    
    id = Column(Integer, primary_key=True)
    athlete_id = Column(Integer, ForeignKey('athletes.id'), nullable=False)
    
    planned_date = Column(DateTime, nullable=False)
    workout_type = Column(String(50), nullable=False)
    planned_distance = Column(Float)  # in meters
    planned_duration = Column(Integer)  # in seconds
    planned_intensity = Column(String(20))  # Easy, Moderate, Hard, etc.
    
    # Detailed workout structure as JSON
    workout_structure = Column(Text)  # JSON string
    
    # Completion tracking
    is_completed = Column(Boolean, default=False)
    completed_activity_id = Column(Integer, ForeignKey('activities.id'))
    
    created_at = Column(DateTime, default=datetime.datetime.now)
    
    # Relationships
    athlete = relationship("ReplitAthlete", back_populates="planned_workouts")
    completed_activity = relationship("Activity")
    
    def get_workout_structure(self):
        """Parse JSON workout structure"""
        if self.workout_structure:
            try:
                return json.loads(self.workout_structure)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_workout_structure(self, structure_dict):
        """Set JSON workout structure"""
        self.workout_structure = json.dumps(structure_dict)
    
    def __repr__(self):
        return f"<PlannedWorkout(id={self.id}, athlete_id={self.athlete_id}, date={self.planned_date})>"

class DailySummary(db.Model):
    """Daily performance summary for each athlete"""
    __tablename__ = 'daily_summaries'
    
    id = Column(Integer, primary_key=True)
    athlete_id = Column(Integer, ForeignKey('athletes.id'), nullable=False)
    summary_date = Column(DateTime, nullable=False)
    
    # Activity metrics
    total_distance = Column(Float, default=0.0)
    total_moving_time = Column(Integer, default=0)
    total_elevation_gain = Column(Float, default=0.0)
    activity_count = Column(Integer, default=0)
    
    # Performance metrics
    average_pace = Column(Float)
    average_heart_rate = Column(Float)
    training_load = Column(Float)
    
    # Compliance metrics
    planned_vs_actual_distance = Column(Float)  # percentage
    planned_vs_actual_duration = Column(Float)  # percentage
    
    # Status and insights
    status = Column(String(50))  # "On Track", "Under-performed", etc.
    insights = Column(Text)  # JSON string for AI insights
    
    created_at = Column(DateTime, default=datetime.datetime.now)
    
    # Relationships
    athlete = relationship("ReplitAthlete", back_populates="daily_summaries")
    
    def get_insights(self):
        """Parse JSON insights"""
        if self.insights:
            try:
                return json.loads(self.insights)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_insights(self, insights_dict):
        """Set JSON insights"""
        self.insights = json.dumps(insights_dict)
    
    def __repr__(self):
        return f"<DailySummary(id={self.id}, athlete_id={self.athlete_id}, date={self.summary_date})>"

class SystemLog(db.Model):
    """System logging model for debugging and monitoring"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    level = Column(String(10), nullable=False)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    module = Column(String(100))
    athlete_id = Column(Integer, ForeignKey('athletes.id'))
    
    # Additional context as JSON
    context = Column(Text)  # JSON string
    
    def get_context(self):
        """Parse JSON context"""
        if self.context:
            try:
                return json.loads(self.context)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_context(self, context_dict):
        """Set JSON context"""
        self.context = json.dumps(context_dict)
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level={self.level}, module={self.module})>"

class StravaApiUsage(db.Model):
    """Track Strava API usage for rate limiting"""
    __tablename__ = 'strava_api_usage'
    
    id = Column(Integer, primary_key=True)
    athlete_id = Column(Integer, ForeignKey('athletes.id'), nullable=False)
    endpoint = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    response_code = Column(Integer)
    rate_limit_usage = Column(String(50))  # e.g., "100/1000"
    
    def __repr__(self):
        return f"<StravaApiUsage(id={self.id}, athlete_id={self.athlete_id}, endpoint={self.endpoint})>"

class OptimalValues(db.Model):
    """Store optimal training values and targets for each athlete"""
    __tablename__ = 'optimal_values'
    
    id = Column(Integer, primary_key=True)
    athlete_id = Column(Integer, ForeignKey('athletes.id'), nullable=False)
    
    # Optimal training targets
    weekly_distance_target = Column(Float)
    weekly_elevation_target = Column(Float)
    target_race_pace = Column(Float)  # seconds per km
    target_long_run_pace = Column(Float)  # seconds per km
    
    # Recovery metrics
    optimal_rest_days_per_week = Column(Integer)
    max_consecutive_training_days = Column(Integer)
    
    # Performance thresholds
    aerobic_threshold_pace = Column(Float)
    anaerobic_threshold_pace = Column(Float)
    vo2_max_pace = Column(Float)
    
    last_updated = Column(DateTime, default=datetime.datetime.now)
    
    def __repr__(self):
        return f"<OptimalValues(id={self.id}, athlete_id={self.athlete_id})>"

class NotificationLog(db.Model):
    """Log all notifications sent to athletes"""
    __tablename__ = 'notification_logs'
    
    id = Column(Integer, primary_key=True)
    athlete_id = Column(Integer, ForeignKey('athletes.id'), nullable=False)
    notification_type = Column(String(50), nullable=False)  # email, push, etc.
    subject = Column(String(255))
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.datetime.now)
    status = Column(String(20), default='pending')  # pending, sent, failed
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<NotificationLog(id={self.id}, athlete_id={self.athlete_id}, type={self.notification_type})>"
