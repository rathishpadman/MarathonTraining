import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
import pandas as pd
from app.models import ReplitAthlete, Activity, PlannedWorkout, DailySummary, SystemLog, db

class DataProcessor:
    """
    Core data processing logic for athlete performance analysis
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_athlete_daily_performance(self, db_session, athlete_id, processing_date):
        """
        Process daily performance for a specific athlete.
        This is the core logic for analyzing athlete data.
        """
        try:
            self.logger.info(f"Processing daily performance for athlete {athlete_id} on {processing_date}")
            
            # Get athlete
            athlete = db_session.query(ReplitAthlete).filter_by(id=athlete_id).first()
            if not athlete:
                self.logger.error(f"Athlete {athlete_id} not found")
                return None
            
            # Get activities for the processing date
            start_date = datetime.combine(processing_date, datetime.min.time())
            end_date = start_date + timedelta(days=1)
            
            activities = db_session.query(Activity).filter(
                Activity.athlete_id == athlete_id,
                Activity.start_date >= start_date,
                Activity.start_date < end_date
            ).all()
            
            self.logger.info(f"Found {len(activities)} activities for athlete {athlete_id} on {processing_date}")
            
            # Get planned workout for the date
            planned_workout = db_session.query(PlannedWorkout).filter(
                PlannedWorkout.athlete_id == athlete_id,
                func.date(PlannedWorkout.planned_date) == processing_date
            ).first()
            
            # Calculate daily metrics
            daily_metrics = self._calculate_daily_metrics(activities)
            
            # Compare with planned workout
            compliance_metrics = self._calculate_compliance_metrics(daily_metrics, planned_workout)
            
            # Determine status and generate insights
            status = self._determine_status(daily_metrics, compliance_metrics, planned_workout)
            insights = self._generate_insights(daily_metrics, compliance_metrics, athlete)
            
            # Update or create daily summary
            existing_summary = db_session.query(DailySummary).filter(
                DailySummary.athlete_id == athlete_id,
                func.date(DailySummary.summary_date) == processing_date
            ).first()
            
            if existing_summary:
                # Update existing summary
                self._update_daily_summary(existing_summary, daily_metrics, compliance_metrics, status, insights)
                self.logger.info(f"Updated existing daily summary for athlete {athlete_id}")
            else:
                # Create new summary
                new_summary = self._create_daily_summary(
                    athlete_id, processing_date, daily_metrics, compliance_metrics, status, insights
                )
                db_session.add(new_summary)
                self.logger.info(f"Created new daily summary for athlete {athlete_id}")
            
            db_session.commit()
            
            # Log successful processing
            self._log_processing_event(db_session, athlete_id, 'daily_processing_success', {
                'processing_date': processing_date.isoformat(),
                'activities_count': len(activities),
                'status': status
            })
            
            return new_summary if not existing_summary else existing_summary
            
        except Exception as e:
            self.logger.error(f"Failed to process daily performance for athlete {athlete_id}: {str(e)}")
            db_session.rollback()
            
            # Log processing error
            self._log_processing_event(db_session, athlete_id, 'daily_processing_error', {
                'processing_date': processing_date.isoformat(),
                'error': str(e)
            })
            
            raise
    
    def _calculate_daily_metrics(self, activities):
        """Calculate aggregated metrics for the day's activities"""
        if not activities:
            return {
                'total_distance': 0.0,
                'total_moving_time': 0,
                'total_elevation_gain': 0.0,
                'activity_count': 0,
                'average_pace': None,
                'average_heart_rate': None,
                'training_load': 0.0
            }
        
        # Convert to pandas DataFrame for easier calculation
        activity_data = []
        for activity in activities:
            activity_data.append({
                'distance': activity.distance or 0,
                'moving_time': activity.moving_time or 0,
                'elevation_gain': activity.total_elevation_gain or 0,
                'average_heartrate': activity.average_heartrate,
                'suffer_score': activity.suffer_score or 0
            })
        
        df = pd.DataFrame(activity_data)
        
        # Calculate metrics
        total_distance = df['distance'].sum()
        total_moving_time = df['moving_time'].sum()
        total_elevation_gain = df['elevation_gain'].sum()
        activity_count = len(activities)
        
        # Calculate average pace (if distance and time available)
        average_pace = None
        if total_distance > 0 and total_moving_time > 0:
            average_pace = total_moving_time / (total_distance / 1000)  # seconds per km
        
        # Calculate average heart rate (weighted by time)
        average_heart_rate = None
        if not df['average_heartrate'].isna().all():
            # Weight by moving time
            hr_weighted_sum = (df['average_heartrate'] * df['moving_time']).sum()
            if total_moving_time > 0:
                average_heart_rate = hr_weighted_sum / total_moving_time
        
        # Calculate training load (sum of suffer scores)
        training_load = df['suffer_score'].sum()
        
        return {
            'total_distance': total_distance,
            'total_moving_time': total_moving_time,
            'total_elevation_gain': total_elevation_gain,
            'activity_count': activity_count,
            'average_pace': average_pace,
            'average_heart_rate': average_heart_rate,
            'training_load': training_load
        }
    
    def _calculate_compliance_metrics(self, daily_metrics, planned_workout):
        """Calculate compliance between planned and actual performance"""
        if not planned_workout:
            return {
                'planned_vs_actual_distance': None,
                'planned_vs_actual_duration': None
            }
        
        # Distance compliance
        distance_compliance = None
        if planned_workout.planned_distance and daily_metrics['total_distance'] > 0:
            distance_compliance = (daily_metrics['total_distance'] / planned_workout.planned_distance) * 100
        
        # Duration compliance
        duration_compliance = None
        if planned_workout.planned_duration and daily_metrics['total_moving_time'] > 0:
            duration_compliance = (daily_metrics['total_moving_time'] / planned_workout.planned_duration) * 100
        
        return {
            'planned_vs_actual_distance': distance_compliance,
            'planned_vs_actual_duration': duration_compliance
        }
    
    def _determine_status(self, daily_metrics, compliance_metrics, planned_workout):
        """Determine overall status for the day"""
        if daily_metrics['activity_count'] == 0:
            return "Rest Day" if not planned_workout else "Missed Workout"
        
        if not planned_workout:
            return "Unplanned Training"
        
        # Check compliance
        distance_compliance = compliance_metrics.get('planned_vs_actual_distance')
        duration_compliance = compliance_metrics.get('planned_vs_actual_duration')
        
        if distance_compliance and duration_compliance:
            avg_compliance = (distance_compliance + duration_compliance) / 2
            
            if avg_compliance >= 90:
                return "On Track"
            elif avg_compliance >= 70:
                return "Mostly Compliant"
            elif avg_compliance >= 50:
                return "Under-performed"
            else:
                return "Significantly Off Track"
        
        return "Partially Completed"
    
    def _generate_insights(self, daily_metrics, compliance_metrics, athlete):
        """Generate AI-powered insights for the athlete"""
        insights = {
            'performance_notes': [],
            'recommendations': [],
            'alerts': []
        }
        
        # Performance analysis
        if daily_metrics['training_load'] > 0:
            if daily_metrics['training_load'] > 150:
                insights['alerts'].append("High training load detected - consider recovery")
            elif daily_metrics['training_load'] < 50:
                insights['performance_notes'].append("Low training load - good for recovery")
        
        # Distance analysis
        if daily_metrics['total_distance'] > 0:
            distance_km = daily_metrics['total_distance'] / 1000
            if distance_km > 25:
                insights['performance_notes'].append("Long distance session completed")
            
            # Pace analysis
            if daily_metrics['average_pace']:
                pace_min_per_km = daily_metrics['average_pace'] / 60
                insights['performance_notes'].append(f"Average pace: {pace_min_per_km:.2f} min/km")
        
        # Heart rate analysis
        if daily_metrics['average_heart_rate'] and athlete.max_hr:
            hr_percentage = (daily_metrics['average_heart_rate'] / athlete.max_hr) * 100
            if hr_percentage > 85:
                insights['alerts'].append("High intensity session - ensure adequate recovery")
            elif hr_percentage < 65:
                insights['performance_notes'].append("Easy/recovery pace maintained")
        
        # Compliance analysis
        distance_compliance = compliance_metrics.get('planned_vs_actual_distance')
        if distance_compliance:
            if distance_compliance < 80:
                insights['recommendations'].append("Consider completing planned distance in future sessions")
            elif distance_compliance > 120:
                insights['alerts'].append("Exceeded planned distance - monitor fatigue levels")
        
        return insights
    
    def _create_daily_summary(self, athlete_id, processing_date, daily_metrics, compliance_metrics, status, insights):
        """Create a new daily summary record"""
        summary = DailySummary(
            athlete_id=athlete_id,
            summary_date=processing_date,
            total_distance=daily_metrics['total_distance'],
            total_moving_time=daily_metrics['total_moving_time'],
            total_elevation_gain=daily_metrics['total_elevation_gain'],
            activity_count=daily_metrics['activity_count'],
            average_pace=daily_metrics['average_pace'],
            average_heart_rate=daily_metrics['average_heart_rate'],
            training_load=daily_metrics['training_load'],
            planned_vs_actual_distance=compliance_metrics.get('planned_vs_actual_distance'),
            planned_vs_actual_duration=compliance_metrics.get('planned_vs_actual_duration'),
            status=status
        )
        
        summary.set_insights(insights)
        return summary
    
    def _update_daily_summary(self, summary, daily_metrics, compliance_metrics, status, insights):
        """Update an existing daily summary record"""
        summary.total_distance = daily_metrics['total_distance']
        summary.total_moving_time = daily_metrics['total_moving_time']
        summary.total_elevation_gain = daily_metrics['total_elevation_gain']
        summary.activity_count = daily_metrics['activity_count']
        summary.average_pace = daily_metrics['average_pace']
        summary.average_heart_rate = daily_metrics['average_heart_rate']
        summary.training_load = daily_metrics['training_load']
        summary.planned_vs_actual_distance = compliance_metrics.get('planned_vs_actual_distance')
        summary.planned_vs_actual_duration = compliance_metrics.get('planned_vs_actual_duration')
        summary.status = status
        summary.set_insights(insights)
    
    def _log_processing_event(self, db_session, athlete_id, event_type, context):
        """Log processing events for debugging and monitoring"""
        try:
            log_entry = SystemLog(
                level='INFO' if 'success' in event_type else 'ERROR',
                message=f"Data processing event: {event_type}",
                module='data_processor',
                athlete_id=athlete_id
            )
            log_entry.set_context(context)
            
            db_session.add(log_entry)
            db_session.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to log processing event: {str(e)}")
    
    def get_athlete_performance_summary(self, db_session, athlete_id, days=30):
        """
        Get aggregated performance summary for an athlete over the specified number of days
        """
        try:
            self.logger.info(f"Fetching performance summary for athlete {athlete_id} over {days} days")
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Get activities for the period directly
            activities = db_session.query(Activity).filter(
                Activity.athlete_id == athlete_id,
                func.date(Activity.start_date) >= start_date,
                func.date(Activity.start_date) <= end_date
            ).order_by(Activity.start_date.desc()).all()
            
            if not activities:
                self.logger.warning(f"No activities found for athlete {athlete_id}")
                return None
            
            # Calculate totals from activities
            total_distance = sum(activity.distance or 0 for activity in activities) / 1000  # Convert to km
            total_moving_time = sum(activity.moving_time or 0 for activity in activities)
            total_elevation_gain = sum(activity.total_elevation_gain or 0 for activity in activities)
            activity_count = len(activities)
            
            # Calculate averages
            avg_heart_rate = None
            heart_rates = [activity.average_heartrate for activity in activities if activity.average_heartrate]
            if heart_rates:
                avg_heart_rate = sum(heart_rates) / len(heart_rates)
            
            # Calculate average pace (min/km)
            avg_pace = None
            if total_distance > 0 and total_moving_time > 0:
                pace_seconds_per_km = (total_moving_time / (total_distance))
                avg_pace = pace_seconds_per_km / 60  # Convert to minutes per km
            
            # Training load estimation
            training_load = activity_count * 50  # Simple estimation
            
            return {
                'total_distance': round(total_distance, 2),
                'total_moving_time': total_moving_time,
                'total_elevation_gain': round(total_elevation_gain, 1),
                'activity_count': activity_count,
                'average_pace': round(avg_pace, 2) if avg_pace else None,
                'average_heart_rate': round(avg_heart_rate, 1) if avg_heart_rate else None,
                'training_load': training_load,
                'activities': activities[:10]  # Return recent 10 activities
            }
        
        except Exception as e:
            self.logger.error(f"Error getting athlete performance summary: {str(e)}")
            return None
    
    def get_team_overview(self, db_session, days=7):
        """
        Get aggregated team overview data for all active athletes
        """
        try:
            self.logger.info(f"Fetching team overview for last {days} days")
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Get all active athletes
            active_athletes = db_session.query(ReplitAthlete).filter_by(is_active=True).all()
            
            team_data = []
            for athlete in active_athletes:
                # Get recent summaries for this athlete
                summaries = db_session.query(DailySummary).filter(
                    DailySummary.athlete_id == athlete.id,
                    func.date(DailySummary.summary_date) >= start_date,
                    func.date(DailySummary.summary_date) <= end_date
                ).all()
                
                if summaries:
                    athlete_metrics = {
                        'athlete_id': athlete.id,
                        'athlete_name': athlete.name,
                        'total_distance': sum(s.total_distance for s in summaries),
                        'total_activities': sum(s.activity_count for s in summaries),
                        'active_days': len([s for s in summaries if s.activity_count > 0]),
                        'latest_status': summaries[-1].status if summaries else 'No Data'
                    }
                    team_data.append(athlete_metrics)
            
            # Calculate team aggregates
            if team_data:
                team_overview = {
                    'period': f"{start_date} to {end_date}",
                    'total_athletes': len(team_data),
                    'total_team_distance': sum(a['total_distance'] for a in team_data),
                    'total_team_activities': sum(a['total_activities'] for a in team_data),
                    'average_distance_per_athlete': sum(a['total_distance'] for a in team_data) / len(team_data),
                    'most_active_athlete': max(team_data, key=lambda x: x['total_distance'])['athlete_name'],
                    'athlete_details': team_data
                }
            else:
                team_overview = {
                    'period': f"{start_date} to {end_date}",
                    'total_athletes': 0,
                    'message': 'No active athletes found'
                }
            
            self.logger.info(f"Team overview calculated for {len(team_data)} athletes")
            return team_overview
            
        except Exception as e:
            self.logger.error(f"Failed to get team overview: {str(e)}")
            raise

# Convenience functions for backward compatibility
def process_athlete_daily_performance(db_session, athlete_id, processing_date):
    processor = DataProcessor()
    return processor.process_athlete_daily_performance(db_session, athlete_id, processing_date)

def get_athlete_performance_summary(db_session, athlete_id, days=30):
    processor = DataProcessor()
    return processor.get_athlete_performance_summary(db_session, athlete_id, days)

def get_team_overview(db_session, days=7):
    processor = DataProcessor()
    return processor.get_team_overview(db_session, days)
