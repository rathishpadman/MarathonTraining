"""
Personalized Training Achievement Stickers System
Generates dynamic achievement stickers based on athlete performance, training consistency, and milestones.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from app.models import ReplitAthlete, Activity, db
from app.training_load_calculator import get_training_load_metrics

logger = logging.getLogger(__name__)

class AchievementSystem:
    """
    Advanced achievement system that recognizes training patterns, milestones, and improvements
    """
    
    def __init__(self):
        self.achievement_categories = {
            'distance': 'Distance Milestones',
            'consistency': 'Training Consistency', 
            'performance': 'Performance Improvements',
            'variety': 'Training Variety',
            'endurance': 'Endurance Achievements',
            'speed': 'Speed Achievements',
            'recovery': 'Recovery & Health',
            'special': 'Special Milestones'
        }
        
        # Achievement definitions with requirements and sticker designs
        self.achievements = {
            # Distance Milestones
            'first_5k': {
                'name': '🏃‍♂️ First 5K',
                'description': 'Completed your first 5K run',
                'category': 'distance',
                'emoji': '🏃‍♂️',
                'color': '#4CAF50',
                'requirement': 'single_distance',
                'threshold': 5.0
            },
            'first_10k': {
                'name': '🏃‍♀️ First 10K',
                'description': 'Conquered the 10K distance',
                'category': 'distance', 
                'emoji': '🏃‍♀️',
                'color': '#2196F3',
                'requirement': 'single_distance',
                'threshold': 10.0
            },
            'half_marathon': {
                'name': '🎽 Half Marathon Hero',
                'description': 'Completed a half marathon distance',
                'category': 'distance',
                'emoji': '🎽',
                'color': '#FF9800',
                'requirement': 'single_distance',
                'threshold': 21.1
            },
            'marathon_warrior': {
                'name': '🏆 Marathon Warrior',
                'description': 'Conquered the full marathon distance',
                'category': 'distance',
                'emoji': '🏆',
                'color': '#9C27B0',
                'requirement': 'single_distance',
                'threshold': 42.2
            },
            'century_runner': {
                'name': '💯 Century Runner',
                'description': 'Ran 100km in a single week',
                'category': 'distance',
                'emoji': '💯',
                'color': '#E91E63',
                'requirement': 'weekly_distance',
                'threshold': 100.0
            },
            
            # Consistency Achievements
            'streak_warrior_7': {
                'name': '🔥 Week Warrior',
                'description': '7-day training streak',
                'category': 'consistency',
                'emoji': '🔥',
                'color': '#FF5722',
                'requirement': 'streak',
                'threshold': 7
            },
            'streak_warrior_30': {
                'name': '⚡ Month Master',
                'description': '30-day training streak',
                'category': 'consistency',
                'emoji': '⚡',
                'color': '#FFC107',
                'requirement': 'streak',
                'threshold': 30
            },
            'early_bird': {
                'name': '🌅 Early Bird',
                'description': '10 morning runs before 7 AM',
                'category': 'consistency',
                'emoji': '🌅',
                'color': '#03DAC6',
                'requirement': 'early_runs',
                'threshold': 10
            },
            
            # Performance Improvements
            'speed_demon': {
                'name': '💨 Speed Demon',
                'description': 'Improved 5K pace by 30 seconds',
                'category': 'performance',
                'emoji': '💨',
                'color': '#FF4081',
                'requirement': 'pace_improvement',
                'threshold': 30
            },
            'endurance_elite': {
                'name': '🚀 Endurance Elite',
                'description': 'Increased weekly distance by 50%',
                'category': 'performance',
                'emoji': '🚀',
                'color': '#3F51B5',
                'requirement': 'distance_improvement',
                'threshold': 0.5
            },
            
            # Training Variety
            'multi_sport': {
                'name': '🤹‍♂️ Multi-Sport Athlete',
                'description': 'Completed 3 different sport types',
                'category': 'variety',
                'emoji': '🤹‍♂️',
                'color': '#607D8B',
                'requirement': 'sport_variety',
                'threshold': 3
            },
            
            # Special Achievements
            'tennis_marathon': {
                'name': '🎾 Tennis Marathon',
                'description': 'Played tennis for 90+ minutes',
                'category': 'special',
                'emoji': '🎾',
                'color': '#8BC34A',
                'requirement': 'tennis_duration',
                'threshold': 90
            },
            'heart_rate_hero': {
                'name': '❤️ Heart Rate Hero',
                'description': 'Maintained target heart rate zone',
                'category': 'recovery',
                'emoji': '❤️',
                'color': '#F44336',
                'requirement': 'heart_rate_zone',
                'threshold': 80
            }
        }
    
    def get_athlete_achievements(self, athlete_id: int, days_back: int = 90) -> List[Dict]:
        """
        Get all achievements earned by an athlete
        """
        try:
            # Get athlete activities
            cutoff_date = datetime.now() - timedelta(days=days_back)
            activities = db.session.query(Activity).filter(
                Activity.athlete_id == athlete_id,
                Activity.start_date >= cutoff_date
            ).order_by(Activity.start_date.desc()).all()
            
            if not activities:
                return []
            
            earned_achievements = []
            
            # Check each achievement type
            for achievement_id, achievement in self.achievements.items():
                if self._check_achievement(achievement, activities, athlete_id):
                    earned_achievements.append({
                        'id': achievement_id,
                        'name': achievement['name'],
                        'description': achievement['description'],
                        'category': achievement['category'],
                        'emoji': achievement['emoji'],
                        'color': achievement['color'],
                        'earned_date': self._get_achievement_date(achievement, activities),
                        'sticker_data': self._generate_sticker_svg(achievement)
                    })
            
            # Sort by earned date (most recent first)
            earned_achievements.sort(key=lambda x: x['earned_date'], reverse=True)
            
            logger.info(f"Generated {len(earned_achievements)} achievements for athlete {athlete_id}")
            return earned_achievements
            
        except Exception as e:
            logger.error(f"Error getting achievements for athlete {athlete_id}: {str(e)}")
            return []
    
    def _check_achievement(self, achievement: Dict, activities: List[Activity], athlete_id: int) -> bool:
        """Check if an achievement has been earned"""
        requirement = achievement['requirement']
        threshold = achievement['threshold']
        
        try:
            if requirement == 'single_distance':
                # Check if any single activity meets distance threshold
                return any(
                    (activity.distance or 0) / 1000 >= threshold 
                    for activity in activities
                )
            
            elif requirement == 'weekly_distance':
                # Check weekly distance totals
                return self._check_weekly_distance(activities, threshold)
            
            elif requirement == 'streak':
                # Check consecutive training days
                return self._calculate_max_streak(activities) >= threshold
            
            elif requirement == 'early_runs':
                # Check morning runs before 7 AM
                early_runs = sum(
                    1 for activity in activities 
                    if activity.start_date and activity.start_date.hour < 7
                    and activity.sport_type == 'Run'
                )
                return early_runs >= threshold
            
            elif requirement == 'pace_improvement':
                # Check 5K pace improvement
                return self._check_pace_improvement(activities, threshold)
            
            elif requirement == 'distance_improvement':
                # Check weekly distance improvement
                return self._check_distance_improvement(activities, threshold)
            
            elif requirement == 'sport_variety':
                # Check number of different sports
                sports = set(activity.sport_type for activity in activities if activity.sport_type)
                return len(sports) >= threshold
            
            elif requirement == 'tennis_duration':
                # Check tennis session duration
                return any(
                    activity.sport_type == 'Tennis' and (activity.moving_time or 0) >= threshold * 60
                    for activity in activities
                )
            
            elif requirement == 'heart_rate_zone':
                # Check heart rate zone consistency
                hr_activities = [a for a in activities if a.average_heartrate and a.average_heartrate > 0]
                if len(hr_activities) < 5:
                    return False
                avg_hr = sum(a.average_heartrate for a in hr_activities) / len(hr_activities)
                return avg_hr >= threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking achievement {achievement.get('name', 'unknown')}: {str(e)}")
            return False
    
    def _check_weekly_distance(self, activities: List[Activity], threshold: float) -> bool:
        """Check if any week meets distance threshold"""
        # Group activities by week
        weekly_totals = {}
        
        for activity in activities:
            if not activity.start_date or not activity.distance:
                continue
                
            # Get Monday of the week
            week_start = activity.start_date - timedelta(days=activity.start_date.weekday())
            week_key = week_start.strftime('%Y-%W')
            
            if week_key not in weekly_totals:
                weekly_totals[week_key] = 0
            
            weekly_totals[week_key] += activity.distance / 1000  # Convert to km
        
        return any(total >= threshold for total in weekly_totals.values())
    
    def _calculate_max_streak(self, activities: List[Activity]) -> int:
        """Calculate maximum consecutive training days"""
        if not activities:
            return 0
        
        # Get unique training days
        training_days = set()
        for activity in activities:
            if activity.start_date:
                training_days.add(activity.start_date.date())
        
        if not training_days:
            return 0
        
        # Sort training days
        sorted_days = sorted(training_days)
        
        max_streak = 1
        current_streak = 1
        
        for i in range(1, len(sorted_days)):
            if (sorted_days[i] - sorted_days[i-1]).days == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1
        
        return max_streak
    
    def _check_pace_improvement(self, activities: List[Activity], threshold_seconds: int) -> bool:
        """Check if 5K pace has improved by threshold seconds"""
        # Find 5K-ish runs (4.5km to 6km)
        relevant_runs = [
            a for a in activities 
            if a.sport_type == 'Run' 
            and a.distance 
            and 4500 <= a.distance <= 6000
            and a.moving_time
            and a.moving_time > 0
        ]
        
        if len(relevant_runs) < 2:
            return False
        
        # Sort by date
        relevant_runs.sort(key=lambda x: x.start_date)
        
        # Calculate paces (seconds per km)
        first_pace = (relevant_runs[0].moving_time) / (relevant_runs[0].distance / 1000)
        best_pace = min(
            (run.moving_time) / (run.distance / 1000) 
            for run in relevant_runs[-5:]  # Check last 5 runs
        )
        
        improvement = first_pace - best_pace
        return improvement >= threshold_seconds
    
    def _check_distance_improvement(self, activities: List[Activity], threshold_percentage: float) -> bool:
        """Check if weekly distance has improved by threshold percentage"""
        weekly_totals = {}
        
        for activity in activities:
            if not activity.start_date or not activity.distance:
                continue
                
            week_start = activity.start_date - timedelta(days=activity.start_date.weekday())
            week_key = week_start.strftime('%Y-%W')
            
            if week_key not in weekly_totals:
                weekly_totals[week_key] = 0
            
            weekly_totals[week_key] += activity.distance / 1000
        
        if len(weekly_totals) < 2:
            return False
        
        # Compare recent weeks to earlier weeks
        sorted_weeks = sorted(weekly_totals.items())
        if len(sorted_weeks) >= 4:
            early_avg = sum(dist for _, dist in sorted_weeks[:2]) / 2
            recent_avg = sum(dist for _, dist in sorted_weeks[-2:]) / 2
            
            if early_avg > 0:
                improvement = (recent_avg - early_avg) / early_avg
                return improvement >= threshold_percentage
        
        return False
    
    def _get_achievement_date(self, achievement: Dict, activities: List[Activity]) -> datetime:
        """Get the date when achievement was earned"""
        requirement = achievement['requirement']
        threshold = achievement['threshold']
        
        # For single distance achievements, find the first qualifying activity
        if requirement == 'single_distance':
            for activity in reversed(activities):  # Check oldest first
                if (activity.distance or 0) / 1000 >= threshold:
                    return activity.start_date
        
        # For other achievements, return most recent activity date
        return activities[0].start_date if activities else datetime.now()
    
    def _generate_sticker_svg(self, achievement: Dict) -> str:
        """Generate SVG sticker data for achievement"""
        emoji = achievement['emoji']
        color = achievement['color']
        
        return f'''
        <svg width="80" height="80" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="gradient-{achievement['emoji']}" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                    <stop offset="100%" style="stop-color:{self._darken_color(color)};stop-opacity:1" />
                </linearGradient>
                <filter id="shadow-{achievement['emoji']}" x="-50%" y="-50%" width="200%" height="200%">
                    <feDropShadow dx="2" dy="2" stdDeviation="3" flood-color="rgba(0,0,0,0.3)"/>
                </filter>
            </defs>
            <circle cx="40" cy="40" r="35" fill="url(#gradient-{achievement['emoji']})" 
                    filter="url(#shadow-{achievement['emoji']})" stroke="white" stroke-width="3"/>
            <text x="40" y="50" text-anchor="middle" font-size="24" fill="white">{emoji}</text>
            <circle cx="40" cy="40" r="35" fill="none" stroke="white" stroke-width="2" opacity="0.6"/>
        </svg>
        '''
    
    def _darken_color(self, hex_color: str) -> str:
        """Darken a hex color by 20% for gradient effect"""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r, g, b = int(r * 0.8), int(g * 0.8), int(b * 0.8)
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return '#333333'
    
    def get_achievement_stats(self, athlete_id: int) -> Dict:
        """Get achievement statistics for an athlete"""
        achievements = self.get_athlete_achievements(athlete_id)
        
        # Group by category
        by_category = {}
        for achievement in achievements:
            category = achievement['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(achievement)
        
        total_possible = len(self.achievements)
        earned_count = len(achievements)
        completion_rate = (earned_count / total_possible) * 100 if total_possible > 0 else 0
        
        return {
            'total_earned': earned_count,
            'total_possible': total_possible,
            'completion_rate': round(completion_rate, 1),
            'by_category': by_category,
            'recent_achievements': achievements[:3]  # Last 3 earned
        }

# Global function for easy access
def get_athlete_achievements(athlete_id: int, days_back: int = 90) -> List[Dict]:
    """Get achievements for an athlete"""
    system = AchievementSystem()
    return system.get_athlete_achievements(athlete_id, days_back)

def get_achievement_stats(athlete_id: int) -> Dict:
    """Get achievement statistics for an athlete"""
    system = AchievementSystem()
    return system.get_achievement_stats(athlete_id)