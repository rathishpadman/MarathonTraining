"""
Advanced Community Analytics for Marathon Training Dashboard
Provides sophisticated community-level metrics and insights
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy import func, and_
from app.models import Activity, ReplitAthlete, db
from app.training_load_calculator import TrainingLoadCalculator
import numpy as np

logger = logging.getLogger(__name__)

class CommunityAnalytics:
    """Advanced analytics for community-level training insights"""
    
    def __init__(self):
        self.training_calculator = TrainingLoadCalculator()
    
    def get_enhanced_community_trends(self, days: int = 7) -> Dict:
        """
        Calculate enhanced community training trends with better KPIs
        """
        try:
            # Calculate date range to include today's data
            today = datetime.now().date()
            start_date = today - timedelta(days=days-1)  # Include today as the last day
            cutoff_datetime = datetime.combine(start_date, datetime.min.time())
            
            # Get all active athletes with activities in the period
            athletes_with_activities = db.session.query(ReplitAthlete).join(Activity).filter(
                and_(
                    ReplitAthlete.is_active == True,
                    Activity.start_date >= cutoff_datetime
                )
            ).distinct().all()
            
            if not athletes_with_activities:
                return self._get_empty_trends(days)
            
            # Calculate daily community metrics - include today
            daily_metrics = {}
            date_range = [start_date + timedelta(days=i) for i in range(days)]
            
            for date in date_range:
                day_start = datetime.combine(date, datetime.min.time())
                day_end = day_start + timedelta(days=1)
                
                daily_metrics[date.strftime('%Y-%m-%d')] = self._calculate_daily_community_metrics(
                    day_start, day_end, athletes_with_activities
                )
            
            # Filter out zero-activity days for better chart representation
            filtered_data = []
            for date in date_range:
                date_str = date.strftime('%Y-%m-%d')
                metrics = daily_metrics[date_str]
                if metrics['active_athletes'] > 0 or metrics['avg_tss'] > 0:
                    filtered_data.append({
                        'label': date.strftime('%m/%d'),
                        'tss': metrics['avg_tss'],
                        'athletes': metrics['active_athletes'],
                        'intensity': metrics['avg_intensity'],
                        'consistency': metrics['consistency_score']
                    })
            
            # If no active days found, show last 7 days anyway to avoid empty chart
            if not filtered_data:
                filtered_data = [{
                    'label': date.strftime('%m/%d'),
                    'tss': daily_metrics[date.strftime('%Y-%m-%d')]['avg_tss'],
                    'athletes': daily_metrics[date.strftime('%Y-%m-%d')]['active_athletes'],
                    'intensity': daily_metrics[date.strftime('%Y-%m-%d')]['avg_intensity'],
                    'consistency': daily_metrics[date.strftime('%Y-%m-%d')]['consistency_score']
                } for date in date_range[-7:]]  # Show last 7 days as fallback
            
            # Extract data for chart
            labels = [item['label'] for item in filtered_data]
            community_tss = [item['tss'] for item in filtered_data]
            active_athletes = [item['athletes'] for item in filtered_data]
            avg_intensity = [item['intensity'] for item in filtered_data]
            consistency_score = [item['consistency'] for item in filtered_data]
            
            return {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Community TSS',
                        'data': community_tss,
                        'borderColor': 'rgb(34, 197, 94)',
                        'backgroundColor': 'rgba(34, 197, 94, 0.1)',
                        'tension': 0.4
                    },
                    {
                        'label': 'Active Athletes',
                        'data': active_athletes,
                        'borderColor': 'rgb(99, 102, 241)',
                        'backgroundColor': 'rgba(99, 102, 241, 0.1)',
                        'tension': 0.4
                    },
                    {
                        'label': 'Avg Intensity (%)',
                        'data': avg_intensity,
                        'borderColor': 'rgb(251, 146, 60)',
                        'backgroundColor': 'rgba(251, 146, 60, 0.1)',
                        'tension': 0.4
                    },
                    {
                        'label': 'Consistency Score',
                        'data': consistency_score,
                        'borderColor': 'rgb(168, 85, 247)',
                        'backgroundColor': 'rgba(168, 85, 247, 0.1)',
                        'tension': 0.4
                    }
                ],
                'insights': self._generate_community_insights(daily_metrics, athletes_with_activities)
            }
            
        except Exception as e:
            logger.error(f"Error calculating enhanced community trends: {str(e)}")
            return self._get_empty_trends(days)
    
    def _calculate_daily_community_metrics(self, day_start: datetime, day_end: datetime, athletes: List) -> Dict:
        """Calculate comprehensive metrics for a single day"""
        
        # Get all activities for the day
        daily_activities = db.session.query(Activity).filter(
            and_(
                Activity.start_date >= day_start,
                Activity.start_date < day_end,
                Activity.athlete_id.in_([a.id for a in athletes])
            )
        ).all()
        
        if not daily_activities:
            return {
                'avg_tss': 0,
                'active_athletes': 0,
                'avg_intensity': 0,
                'consistency_score': 0,
                'total_volume': 0,
                'workout_distribution': {}
            }
        
        # Calculate Training Stress Score (TSS) for each activity
        tss_values = []
        intensity_scores = []
        active_athlete_ids = set()
        workout_types = {}
        
        for activity in daily_activities:
            active_athlete_ids.add(activity.athlete_id)
            
            # Calculate TSS using our training load calculator
            tss = self._calculate_activity_tss(activity)
            if tss > 0:
                tss_values.append(tss)
            
            # Calculate intensity score (0-100 based on effort)
            intensity = self._calculate_intensity_score(activity)
            if intensity > 0:
                intensity_scores.append(intensity)
            
            # Track workout types
            workout_type = self._classify_workout_type(activity)
            workout_types[workout_type] = workout_types.get(workout_type, 0) + 1
        
        # Calculate consistency score (how many athletes trained vs total)
        total_athletes = len(athletes)
        active_count = len(active_athlete_ids)
        consistency_score = round((active_count / total_athletes) * 100, 1) if total_athletes > 0 else 0
        
        return {
            'avg_tss': round(np.mean(tss_values), 1) if tss_values else 0,
            'active_athletes': active_count,
            'avg_intensity': round(np.mean(intensity_scores), 1) if intensity_scores else 0,
            'consistency_score': consistency_score,
            'total_volume': sum(tss_values),
            'workout_distribution': workout_types
        }
    
    def _calculate_activity_tss(self, activity: Activity) -> float:
        """Calculate Training Stress Score for an activity"""
        try:
            duration_hours = (activity.moving_time or activity.elapsed_time or 0) / 3600
            
            if duration_hours <= 0:
                return 0
            
            # Heart rate based TSS (preferred)
            if activity.average_heartrate and activity.max_heartrate:
                hr_intensity = activity.average_heartrate / activity.max_heartrate
                return duration_hours * 100 * (hr_intensity ** 2)
            
            # Distance/pace based TSS for running
            elif activity.distance and activity.average_speed:
                pace_per_km = 1000 / (activity.average_speed * 60)  # min/km
                
                # Estimate intensity based on pace (assuming 5:00/km = threshold pace)
                threshold_pace = 5.0  # minutes per km
                intensity_factor = min(threshold_pace / pace_per_km, 1.2)
                
                return duration_hours * 100 * (intensity_factor ** 2)
            
            # Duration based TSS (fallback)
            else:
                # Base intensity for different sport types
                sport_intensities = {
                    'Run': 0.75,
                    'Ride': 0.70,
                    'Swim': 0.80,
                    'Tennis': 0.65,
                    'Strength': 0.60,
                    'Other': 0.50
                }
                
                sport_type = activity.sport_type or 'Other'
                base_intensity = sport_intensities.get(sport_type, 0.60)
                
                return duration_hours * 100 * (base_intensity ** 2)
                
        except Exception as e:
            logger.warning(f"Error calculating TSS for activity {activity.id}: {str(e)}")
            return 0
    
    def _calculate_intensity_score(self, activity: Activity) -> float:
        """Calculate intensity score (0-100) based on effort indicators"""
        try:
            intensity_indicators = []
            
            # Heart rate intensity
            if activity.average_heartrate and activity.max_heartrate:
                hr_percentage = (activity.average_heartrate / activity.max_heartrate) * 100
                intensity_indicators.append(min(hr_percentage, 100))
            
            # Pace intensity (for running)
            if activity.sport_type == 'Run' and activity.average_speed:
                pace_per_km = 1000 / (activity.average_speed * 60)
                
                # Relative to estimated easy pace (assume 6:30/km as moderate)
                easy_pace = 6.5
                pace_intensity = max(0, min(100, (easy_pace / pace_per_km) * 60))
                intensity_indicators.append(pace_intensity)
            
            # Duration intensity (longer = higher aerobic demand)
            duration_hours = (activity.moving_time or activity.elapsed_time or 0) / 3600
            duration_intensity = min(100, duration_hours * 25)  # 4 hours = 100%
            intensity_indicators.append(duration_intensity)
            
            # Return average of available indicators
            return round(np.mean(intensity_indicators), 1) if intensity_indicators else 50
            
        except Exception as e:
            logger.warning(f"Error calculating intensity for activity {activity.id}: {str(e)}")
            return 50
    
    def _classify_workout_type(self, activity: Activity) -> str:
        """Classify workout type based on activity characteristics"""
        try:
            duration_minutes = (activity.moving_time or activity.elapsed_time or 0) / 60
            distance_km = (activity.distance or 0) / 1000
            
            sport_type = activity.sport_type or 'Other'
            
            if sport_type == 'Run':
                if distance_km >= 15:
                    return 'Long Run'
                elif duration_minutes <= 30:
                    return 'Short Run'
                else:
                    return 'Base Run'
            elif sport_type in ['Tennis', 'Strength']:
                return 'Cross Training'
            elif sport_type == 'Ride':
                if duration_minutes >= 120:
                    return 'Long Ride'
                else:
                    return 'Bike Training'
            else:
                return 'Other Activity'
                
        except Exception:
            return 'Other Activity'
    
    def _generate_community_insights(self, daily_metrics: Dict, athletes: List) -> List[str]:
        """Generate AI-powered insights about community training patterns"""
        insights = []
        
        try:
            # Calculate trends
            tss_values = [metrics['avg_tss'] for metrics in daily_metrics.values()]
            consistency_values = [metrics['consistency_score'] for metrics in daily_metrics.values()]
            
            # TSS trend analysis
            if len(tss_values) >= 3:
                recent_avg = np.mean(tss_values[-3:])
                earlier_avg = np.mean(tss_values[:-3]) if len(tss_values) > 3 else recent_avg
                
                if recent_avg > earlier_avg * 1.1:
                    insights.append("Community training intensity is increasing - great momentum!")
                elif recent_avg < earlier_avg * 0.9:
                    insights.append("Community taking recovery focus - smart periodization")
            
            # Consistency analysis
            avg_consistency = np.mean(consistency_values)
            if avg_consistency >= 80:
                insights.append(f"Excellent community participation ({avg_consistency:.0f}% consistency)")
            elif avg_consistency >= 60:
                insights.append(f"Good community engagement ({avg_consistency:.0f}% active daily)")
            else:
                insights.append("Opportunity to increase community participation")
            
            # Peak training day analysis
            peak_day_idx = np.argmax(tss_values)
            peak_day_metrics = list(daily_metrics.values())[peak_day_idx]
            
            if peak_day_metrics['avg_tss'] > 50:
                insights.append(f"Peak training day: {peak_day_metrics['active_athletes']} athletes averaging {peak_day_metrics['avg_tss']:.0f} TSS")
            
            # Add variety insight
            total_athletes = len(athletes)
            if total_athletes > 1:
                insights.append(f"Community diversity: {total_athletes} active athletes with varied training approaches")
            
        except Exception as e:
            logger.warning(f"Error generating insights: {str(e)}")
            insights.append("Community training data analysis available")
        
        return insights[:4]  # Limit to top 4 insights
    
    def _get_empty_trends(self, days: int) -> Dict:
        """Return empty trends structure"""
        labels = [(datetime.now() - timedelta(days=days-1-i)).strftime('%m/%d') for i in range(days)]
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Community TSS',
                    'data': [0] * days,
                    'borderColor': 'rgb(34, 197, 94)',
                    'backgroundColor': 'rgba(34, 197, 94, 0.1)'
                }
            ],
            'insights': ['No community training data available for this period']
        }

def get_enhanced_community_trends(days: int = 7) -> Dict:
    """Global function for enhanced community trends"""
    analytics = CommunityAnalytics()
    return analytics.get_enhanced_community_trends(days)