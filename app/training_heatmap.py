"""
Interactive Training Progress Heatmap
Provides visual heatmap representation of training intensity, patterns, and progress over time
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models import Activity, ReplitAthlete
from app import db

logger = logging.getLogger(__name__)

class TrainingProgressHeatmap:
    """
    Advanced training heatmap system for visualizing training patterns and intensity
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.TrainingProgressHeatmap')
    
    def generate_yearly_heatmap(self, athlete_id: int, year: Optional[int] = None) -> Dict:
        """
        Generate yearly training heatmap data
        
        Args:
            athlete_id: Athlete ID
            year: Target year (defaults to current year)
            
        Returns:
            Comprehensive heatmap data with intensity levels and metrics
        """
        try:
            if year is None:
                year = datetime.now().year
                
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)
            
            # Get athlete info
            athlete = db.session.query(ReplitAthlete).filter_by(id=athlete_id).first()
            if not athlete:
                return self._get_empty_heatmap(year)
            
            # Get all activities for the year
            activities = db.session.query(Activity).filter(
                and_(
                    Activity.athlete_id == athlete_id,
                    Activity.start_date >= start_date,
                    Activity.start_date <= end_date
                )
            ).all()
            
            if not activities:
                return self._get_empty_heatmap(year)
            
            # Generate daily intensity map
            daily_data = self._calculate_daily_intensity(activities, year)
            
            # Calculate statistics
            stats = self._calculate_heatmap_stats(daily_data, activities, athlete)
            
            # Generate insights
            insights = self._generate_heatmap_insights(daily_data, stats, athlete)
            
            return {
                'athlete_id': athlete_id,
                'athlete_name': athlete.name,
                'year': year,
                'daily_data': daily_data,
                'statistics': stats,
                'insights': insights,
                'legend': self._get_intensity_legend(),
                'calendar_data': self._format_calendar_data(daily_data, year)
            }
                
        except Exception as e:
            self.logger.error(f"Error generating heatmap for athlete {athlete_id}: {str(e)}")
            return self._get_empty_heatmap(year)
    
    def _calculate_daily_intensity(self, activities: List[Activity], year: int) -> Dict:
        """Calculate daily training intensity scores"""
        daily_data = {}
        
        # Initialize all days of the year
        start_date = datetime(year, 1, 1)
        days_in_year = 366 if year % 4 == 0 else 365
        
        for day_offset in range(days_in_year):
            date = start_date + timedelta(days=day_offset)
            date_str = date.strftime('%Y-%m-%d')
            daily_data[date_str] = {
                'intensity': 0,
                'activities': 0,
                'total_distance': 0,
                'total_duration': 0,
                'avg_hr': 0,
                'tss': 0,
                'activity_types': set()
            }
        
        # Process activities
        for activity in activities:
            date_str = activity.start_date.strftime('%Y-%m-%d')
            if date_str not in daily_data:
                continue
            
            day_data = daily_data[date_str]
            day_data['activities'] += 1
            day_data['total_distance'] += activity.distance or 0
            day_data['total_duration'] += activity.moving_time or 0
            day_data['activity_types'].add(activity.sport_type or 'Other')
            
            # Calculate Training Stress Score (TSS)
            activity_tss = self._calculate_activity_tss(activity)
            day_data['tss'] += activity_tss
            
            # Update average heart rate
            if activity.average_heartrate:
                if day_data['avg_hr'] == 0:
                    day_data['avg_hr'] = activity.average_heartrate
                else:
                    day_data['avg_hr'] = (day_data['avg_hr'] + activity.average_heartrate) / 2
        
        # Calculate intensity levels (0-4 scale)
        for date_str, data in daily_data.items():
            data['activity_types'] = list(data['activity_types'])
            data['intensity'] = self._calculate_intensity_level(data)
        
        return daily_data
    
    def _calculate_activity_tss(self, activity: Activity) -> float:
        """Calculate Training Stress Score for an activity"""
        if not activity.moving_time:
            return 0
        
        # Base TSS calculation
        duration_hours = activity.moving_time / 3600
        base_tss = duration_hours * 50  # Base 50 TSS per hour
        
        # Adjust for intensity indicators
        intensity_multiplier = 1.0
        
        # Heart rate intensity
        if activity.average_heartrate and activity.max_heartrate:
            hr_ratio = activity.average_heartrate / activity.max_heartrate
            if hr_ratio > 0.85:
                intensity_multiplier *= 1.4
            elif hr_ratio > 0.75:
                intensity_multiplier *= 1.2
            elif hr_ratio > 0.65:
                intensity_multiplier *= 1.1
        
        # Pace intensity (for running activities)
        if activity.sport_type == 'Run' and activity.distance and activity.moving_time:
            pace_min_km = (activity.moving_time / 60) / activity.distance
            if pace_min_km < 4.0:  # Very fast pace
                intensity_multiplier *= 1.3
            elif pace_min_km < 5.0:  # Fast pace
                intensity_multiplier *= 1.15
        
        # Elevation gain intensity
        if activity.total_elevation_gain and activity.total_elevation_gain > 100:
            elevation_factor = min(activity.total_elevation_gain / 500, 1.5)
            intensity_multiplier *= (1 + elevation_factor * 0.2)
        
        return base_tss * intensity_multiplier
    
    def _calculate_intensity_level(self, day_data: Dict) -> int:
        """Calculate intensity level (0-4) for a day"""
        if day_data['activities'] == 0:
            return 0
        
        tss = day_data['tss']
        activities = day_data['activities']
        
        # Multi-factor intensity calculation
        if tss >= 150 or activities >= 3:
            return 4  # Very High
        elif tss >= 100 or activities >= 2:
            return 3  # High
        elif tss >= 50:
            return 2  # Medium
        elif tss > 0:
            return 1  # Low
        else:
            return 0  # Rest
    
    def _calculate_heatmap_stats(self, daily_data: Dict, activities: List[Activity], athlete: ReplitAthlete) -> Dict:
        """Calculate comprehensive heatmap statistics"""
        active_days = sum(1 for data in daily_data.values() if data['intensity'] > 0)
        total_days = len(daily_data)
        
        intensity_distribution = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        total_tss = 0
        total_distance = 0
        total_duration = 0
        
        for data in daily_data.values():
            intensity_distribution[data['intensity']] += 1
            total_tss += data['tss']
            total_distance += data['total_distance']
            total_duration += data['total_duration']
        
        # Calculate streaks
        current_streak, longest_streak = self._calculate_training_streaks(daily_data)
        
        # Weekly patterns
        weekly_pattern = self._analyze_weekly_patterns(daily_data)
        
        # Monthly trends
        monthly_trends = self._analyze_monthly_trends(daily_data)
        
        return {
            'total_days': total_days,
            'active_days': active_days,
            'rest_days': total_days - active_days,
            'consistency_rate': round((active_days / total_days) * 100, 1),
            'total_activities': len(activities),
            'total_distance': round(total_distance, 1),
            'total_duration_hours': round(total_duration / 3600, 1),
            'total_tss': round(total_tss, 1),
            'avg_daily_tss': round(total_tss / total_days, 1),
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'intensity_distribution': intensity_distribution,
            'weekly_pattern': weekly_pattern,
            'monthly_trends': monthly_trends
        }
    
    def _calculate_training_streaks(self, daily_data: Dict) -> tuple:
        """Calculate current and longest training streaks"""
        dates = sorted(daily_data.keys())
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        # Calculate from most recent date backwards for current streak
        today = datetime.now().strftime('%Y-%m-%d')
        current_date_idx = len(dates) - 1
        
        # Find current streak
        for i in range(len(dates) - 1, -1, -1):
            if daily_data[dates[i]]['intensity'] > 0:
                current_streak += 1
            else:
                break
        
        # Calculate longest streak
        for date in dates:
            if daily_data[date]['intensity'] > 0:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
        
        return current_streak, longest_streak
    
    def _analyze_weekly_patterns(self, daily_data: Dict) -> Dict:
        """Analyze training patterns by day of week"""
        weekly_pattern = {
            'Monday': {'total': 0, 'active': 0, 'avg_intensity': 0},
            'Tuesday': {'total': 0, 'active': 0, 'avg_intensity': 0},
            'Wednesday': {'total': 0, 'active': 0, 'avg_intensity': 0},
            'Thursday': {'total': 0, 'active': 0, 'avg_intensity': 0},
            'Friday': {'total': 0, 'active': 0, 'avg_intensity': 0},
            'Saturday': {'total': 0, 'active': 0, 'avg_intensity': 0},
            'Sunday': {'total': 0, 'active': 0, 'avg_intensity': 0}
        }
        
        for date_str, data in daily_data.items():
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            day_name = date_obj.strftime('%A')
            
            weekly_pattern[day_name]['total'] += 1
            if data['intensity'] > 0:
                weekly_pattern[day_name]['active'] += 1
            weekly_pattern[day_name]['avg_intensity'] += data['intensity']
        
        # Calculate averages
        for day_data in weekly_pattern.values():
            if day_data['total'] > 0:
                day_data['avg_intensity'] = round(day_data['avg_intensity'] / day_data['total'], 2)
                day_data['activity_rate'] = round((day_data['active'] / day_data['total']) * 100, 1)
            else:
                day_data['activity_rate'] = 0
        
        return weekly_pattern
    
    def _analyze_monthly_trends(self, daily_data: Dict) -> Dict:
        """Analyze training trends by month"""
        monthly_trends = {}
        
        for date_str, data in daily_data.items():
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            month_key = date_obj.strftime('%Y-%m')
            month_name = date_obj.strftime('%B')
            
            if month_key not in monthly_trends:
                monthly_trends[month_key] = {
                    'month_name': month_name,
                    'total_days': 0,
                    'active_days': 0,
                    'total_tss': 0,
                    'total_distance': 0,
                    'activities': 0
                }
            
            monthly_trends[month_key]['total_days'] += 1
            if data['intensity'] > 0:
                monthly_trends[month_key]['active_days'] += 1
            monthly_trends[month_key]['total_tss'] += data['tss']
            monthly_trends[month_key]['total_distance'] += data['total_distance']
            monthly_trends[month_key]['activities'] += data['activities']
        
        # Calculate monthly averages and rates
        for month_data in monthly_trends.values():
            total_days = month_data['total_days']
            month_data['consistency_rate'] = round((month_data['active_days'] / total_days) * 100, 1)
            month_data['avg_daily_tss'] = round(month_data['total_tss'] / total_days, 1)
            month_data['total_distance'] = round(month_data['total_distance'], 1)
        
        return monthly_trends
    
    def _generate_heatmap_insights(self, daily_data: Dict, stats: Dict, athlete: ReplitAthlete) -> List[str]:
        """Generate AI-powered insights from heatmap data"""
        insights = []
        
        # Consistency insights
        consistency = stats['consistency_rate']
        if consistency >= 80:
            insights.append(f"Excellent consistency at {consistency}% - maintaining strong training discipline")
        elif consistency >= 60:
            insights.append(f"Good consistency at {consistency}% - room for improvement in training regularity")
        else:
            insights.append(f"Consistency at {consistency}% needs attention - focus on building routine")
        
        # Streak insights
        current_streak = stats['current_streak']
        longest_streak = stats['longest_streak']
        if current_streak >= 7:
            insights.append(f"Strong current streak of {current_streak} days - excellent momentum")
        if longest_streak >= 14:
            insights.append(f"Impressive longest streak of {longest_streak} days shows dedication")
        
        # Weekly pattern insights
        weekly_pattern = stats['weekly_pattern']
        weekend_activity = (weekly_pattern['Saturday']['activity_rate'] + weekly_pattern['Sunday']['activity_rate']) / 2
        weekday_activity = sum(weekly_pattern[day]['activity_rate'] for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']) / 5
        
        if weekend_activity > weekday_activity + 20:
            insights.append("Weekend warrior pattern detected - consider spreading training throughout the week")
        elif weekday_activity > weekend_activity + 20:
            insights.append("Strong weekday training routine - excellent work-life-fitness balance")
        
        # Intensity insights
        intensity_dist = stats['intensity_distribution']
        high_intensity_days = intensity_dist[3] + intensity_dist[4]
        total_active_days = sum(intensity_dist[i] for i in range(1, 5))
        
        if total_active_days > 0:
            high_intensity_rate = (high_intensity_days / total_active_days) * 100
            if high_intensity_rate > 30:
                insights.append("High proportion of intense training - ensure adequate recovery")
            elif high_intensity_rate < 10:
                insights.append("Consider adding more high-intensity sessions for performance gains")
        
        # Monthly trend insights
        monthly_trends = stats['monthly_trends']
        if len(monthly_trends) >= 2:
            months = sorted(monthly_trends.keys())
            recent_month = monthly_trends[months[-1]]
            previous_month = monthly_trends[months[-2]] if len(months) >= 2 else None
            
            if previous_month:
                tss_change = recent_month['total_tss'] - previous_month['total_tss']
                if tss_change > 20:
                    insights.append("Training load increasing - positive progression trend")
                elif tss_change < -20:
                    insights.append("Training load decreasing - consider reasons for reduction")
        
        return insights[:5]  # Limit to top 5 insights
    
    def _get_intensity_legend(self) -> Dict:
        """Get intensity level legend for the heatmap"""
        return {
            0: {'label': 'Rest', 'color': '#f3f4f6', 'description': 'No training activity'},
            1: {'label': 'Light', 'color': '#dcfce7', 'description': 'Easy training session'},
            2: {'label': 'Moderate', 'color': '#bbf7d0', 'description': 'Standard training day'},
            3: {'label': 'High', 'color': '#86efac', 'description': 'Intense training session'},
            4: {'label': 'Very High', 'color': '#22c55e', 'description': 'Maximum effort training'}
        }
    
    def _format_calendar_data(self, daily_data: Dict, year: int) -> List[Dict]:
        """Format data for calendar visualization"""
        calendar_data = []
        
        for date_str, data in daily_data.items():
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            calendar_data.append({
                'date': date_str,
                'day': date_obj.day,
                'month': date_obj.month,
                'weekday': date_obj.weekday(),
                'intensity': data['intensity'],
                'activities': data['activities'],
                'tss': round(data['tss'], 1),
                'distance': round(data['total_distance'], 1),
                'duration_minutes': round(data['total_duration'] / 60, 0),
                'activity_types': data['activity_types']
            })
        
        return calendar_data
    
    def _get_empty_heatmap(self, year: int) -> Dict:
        """Return empty heatmap structure"""
        return {
            'athlete_id': None,
            'athlete_name': 'Unknown',
            'year': year,
            'daily_data': {},
            'statistics': {
                'total_days': 0,
                'active_days': 0,
                'rest_days': 0,
                'consistency_rate': 0,
                'total_activities': 0,
                'total_distance': 0,
                'total_duration_hours': 0,
                'total_tss': 0,
                'current_streak': 0,
                'longest_streak': 0,
                'intensity_distribution': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0},
                'weekly_pattern': {},
                'monthly_trends': {}
            },
            'insights': ['No training data available for the selected period'],
            'legend': self._get_intensity_legend(),
            'calendar_data': []
        }

def generate_training_heatmap(athlete_id: int, year: Optional[int] = None) -> Dict:
    """
    Global function to generate training progress heatmap
    
    Args:
        athlete_id: Athlete ID
        year: Target year (defaults to current year)
        
    Returns:
        Comprehensive heatmap data
    """
    heatmap_generator = TrainingProgressHeatmap()
    return heatmap_generator.generate_yearly_heatmap(athlete_id, year)