"""
Advanced Race Optimization Engine
Provides detailed training insights, pacing strategies, and performance optimization 
recommendations based on authentic athlete data analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app.models import Activity, ReplitAthlete
from sqlalchemy.orm import Session
from collections import defaultdict
import statistics

class RaceOptimizer:
    """
    Advanced race optimization system providing comprehensive training insights
    and performance enhancement recommendations based on authentic data
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Training zones based on heart rate percentage
        self.hr_zones = {
            'Zone 1 (Recovery)': (0.50, 0.60),
            'Zone 2 (Aerobic Base)': (0.60, 0.70),
            'Zone 3 (Aerobic)': (0.70, 0.80),
            'Zone 4 (Lactate Threshold)': (0.80, 0.90),
            'Zone 5 (VO2 Max)': (0.90, 1.00)
        }
        
        # Pace zones relative to threshold pace
        self.pace_zones = {
            'Easy': 1.20,      # 20% slower than threshold
            'Moderate': 1.10,   # 10% slower than threshold
            'Threshold': 1.00,  # Threshold pace
            'Tempo': 0.95,     # 5% faster than threshold
            'VO2 Max': 0.90    # 10% faster than threshold
        }
    
    def generate_race_optimization_plan(self, db_session: Session, athlete_id: int, race_distance: str, days_analysis: int = 90) -> Dict:
        """
        Generate comprehensive race optimization plan with detailed insights
        """
        self.logger.info(f"Generating race optimization plan for athlete {athlete_id}, distance: {race_distance}")
        
        try:
            # Get athlete and activities
            athlete = db_session.query(ReplitAthlete).filter_by(id=athlete_id).first()
            if not athlete:
                raise ValueError(f"Athlete {athlete_id} not found")
            
            # Get recent activities for analysis
            cutoff_date = datetime.now() - timedelta(days=days_analysis)
            activities = db_session.query(Activity).filter(
                Activity.athlete_id == athlete_id,
                Activity.start_date >= cutoff_date,
                Activity.sport_type.in_(['Run', 'VirtualRun']),
                Activity.distance > 1000  # At least 1km
            ).order_by(Activity.start_date.desc()).all()
            
            if not activities:
                return self._empty_optimization_plan(race_distance)
            
            # Analyze training patterns
            training_analysis = self._analyze_training_patterns(activities)
            
            # Analyze performance trends
            performance_trends = self._analyze_performance_trends(activities)
            
            # Generate pacing strategy
            pacing_strategy = self._generate_detailed_pacing_strategy(activities, race_distance)
            
            # Generate training recommendations
            training_recommendations = self._generate_training_recommendations(activities, race_distance, training_analysis)
            
            # Analyze strengths and weaknesses
            strengths_weaknesses = self._analyze_strengths_weaknesses(activities, training_analysis)
            
            # Generate race day strategy
            race_day_strategy = self._generate_race_day_strategy(race_distance, pacing_strategy)
            
            # Calculate optimization metrics
            optimization_metrics = self._calculate_optimization_metrics(activities, training_analysis)
            
            return {
                'athlete_name': athlete.name,
                'race_distance': race_distance,
                'analysis_period_days': days_analysis,
                'total_activities_analyzed': len(activities),
                'training_analysis': training_analysis,
                'performance_trends': performance_trends,
                'pacing_strategy': pacing_strategy,
                'training_recommendations': training_recommendations,
                'strengths_weaknesses': strengths_weaknesses,
                'race_day_strategy': race_day_strategy,
                'optimization_metrics': optimization_metrics,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating race optimization plan: {str(e)}")
            raise
    
    def _analyze_training_patterns(self, activities: List[Activity]) -> Dict:
        """Analyze training patterns from authentic activity data"""
        if not activities:
            return {}
        
        # Weekly training volume analysis
        weekly_volumes = defaultdict(float)
        weekly_activities = defaultdict(int)
        weekly_avg_pace = defaultdict(list)
        
        for activity in activities:
            if not (activity.distance and activity.moving_time and activity.start_date):
                continue
            
            week_start = activity.start_date - timedelta(days=activity.start_date.weekday())
            week_key = week_start.strftime('%Y-%W')
            
            distance_km = activity.distance / 1000
            pace_per_km = activity.moving_time / distance_km
            
            weekly_volumes[week_key] += distance_km
            weekly_activities[week_key] += 1
            
            if 200 <= pace_per_km <= 800:  # Reasonable pace range
                weekly_avg_pace[week_key].append(pace_per_km)
        
        # Calculate training consistency
        volume_values = list(weekly_volumes.values())
        volume_consistency = self._calculate_consistency(volume_values)
        
        # Calculate average weekly metrics
        avg_weekly_volume = statistics.mean(volume_values) if volume_values else 0
        avg_weekly_activities = statistics.mean(list(weekly_activities.values())) if weekly_activities else 0
        
        # Analyze intensity distribution
        intensity_distribution = self._analyze_intensity_distribution(activities)
        
        # Analyze workout types
        workout_types = self._analyze_workout_types(activities)
        
        return {
            'avg_weekly_volume_km': round(avg_weekly_volume, 1),
            'avg_weekly_activities': round(avg_weekly_activities, 1),
            'volume_consistency_score': round(volume_consistency, 1),
            'total_weeks_analyzed': len(weekly_volumes),
            'intensity_distribution': intensity_distribution,
            'workout_types': workout_types,
            'weekly_volume_trend': self._calculate_trend(volume_values)
        }
    
    def _analyze_performance_trends(self, activities: List[Activity]) -> Dict:
        """Analyze performance trends over time"""
        if not activities:
            return {}
        
        # Sort activities by date
        sorted_activities = sorted(activities, key=lambda x: x.start_date or datetime.min)
        
        # Analyze pace trends
        pace_trend = self._analyze_pace_trend(sorted_activities)
        
        # Analyze distance trends
        distance_trend = self._analyze_distance_trend(sorted_activities)
        
        # Analyze heart rate trends (if available)
        hr_trend = self._analyze_heart_rate_trend(sorted_activities)
        
        # Calculate fitness progression
        fitness_progression = self._calculate_fitness_progression(sorted_activities)
        
        return {
            'pace_trend': pace_trend,
            'distance_trend': distance_trend,
            'heart_rate_trend': hr_trend,
            'fitness_progression': fitness_progression,
            'improvement_rate': self._calculate_improvement_rate(sorted_activities)
        }
    
    def _generate_detailed_pacing_strategy(self, activities: List[Activity], race_distance: str) -> Dict:
        """Generate detailed pacing strategy based on training data"""
        if not activities:
            return {}
        
        # Calculate threshold pace from training data
        threshold_pace = self._estimate_threshold_pace(activities)
        
        # Get race distance in km
        distance_km = self._get_race_distance_km(race_distance)
        
        # Calculate target race pace based on distance
        target_pace = self._calculate_target_race_pace(threshold_pace, distance_km)
        
        # Generate split pacing strategy
        splits = self._generate_split_strategy(target_pace, distance_km, race_distance)
        
        # Generate heart rate targets
        hr_targets = self._generate_hr_targets(activities, race_distance)
        
        return {
            'target_pace_per_km': self._format_pace(target_pace),
            'target_pace_seconds': round(target_pace),
            'threshold_pace_per_km': self._format_pace(threshold_pace),
            'estimated_finish_time': self._format_time(target_pace * distance_km),
            'splits': splits,
            'heart_rate_targets': hr_targets,
            'pacing_advice': self._generate_pacing_advice(race_distance)
        }
    
    def _generate_training_recommendations(self, activities: List[Activity], race_distance: str, training_analysis: Dict) -> List[Dict]:
        """Generate specific training recommendations"""
        recommendations = []
        
        # Analyze current training gaps
        volume = training_analysis.get('avg_weekly_volume_km', 0)
        consistency = training_analysis.get('volume_consistency_score', 0)
        intensity_dist = training_analysis.get('intensity_distribution', {})
        
        # Volume recommendations
        if volume < 30:
            recommendations.append({
                'category': 'Volume',
                'priority': 'High',
                'recommendation': 'Gradually increase weekly mileage to 30-40km for better endurance base',
                'implementation': 'Add 10% more distance per week, focus on easy-paced runs',
                'timeline': '4-6 weeks'
            })
        
        # Consistency recommendations
        if consistency < 70:
            recommendations.append({
                'category': 'Consistency',
                'priority': 'High',
                'recommendation': 'Improve training consistency with regular weekly schedule',
                'implementation': 'Aim for 3-4 runs per week, maintain consistent weekly volume',
                'timeline': '2-4 weeks'
            })
        
        # Intensity recommendations
        easy_percentage = intensity_dist.get('easy_percentage', 0)
        if easy_percentage < 70:
            recommendations.append({
                'category': 'Intensity Balance',
                'priority': 'Medium',
                'recommendation': 'Increase easy-paced training to 70-80% of total volume',
                'implementation': 'Run majority of miles at conversational pace, limit hard efforts to 2 per week',
                'timeline': '2-3 weeks'
            })
        
        # Race-specific recommendations
        race_specific = self._generate_race_specific_recommendations(race_distance, training_analysis)
        recommendations.extend(race_specific)
        
        return recommendations
    
    def _analyze_strengths_weaknesses(self, activities: List[Activity], training_analysis: Dict) -> Dict:
        """Analyze athlete's strengths and weaknesses"""
        strengths = []
        weaknesses = []
        
        # Analyze volume consistency
        consistency = training_analysis.get('volume_consistency_score', 0)
        if consistency > 80:
            strengths.append('Excellent training consistency')
        elif consistency < 60:
            weaknesses.append('Inconsistent training pattern')
        
        # Analyze weekly volume
        volume = training_analysis.get('avg_weekly_volume_km', 0)
        if volume > 40:
            strengths.append('Strong weekly training volume')
        elif volume < 25:
            weaknesses.append('Low weekly training volume')
        
        # Analyze pace distribution
        pace_analysis = self._analyze_pace_distribution(activities)
        if pace_analysis.get('pace_variety_score', 0) > 75:
            strengths.append('Good pace variety in training')
        elif pace_analysis.get('pace_variety_score', 0) < 50:
            weaknesses.append('Limited pace variety')
        
        # Analyze recent performance trend
        recent_activities = activities[:10]  # Last 10 activities
        if self._is_improving_trend(recent_activities):
            strengths.append('Positive performance trend')
        elif self._is_declining_trend(recent_activities):
            weaknesses.append('Recent performance decline')
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses,
            'overall_assessment': self._generate_overall_assessment(strengths, weaknesses)
        }
    
    def _generate_race_day_strategy(self, race_distance: str, pacing_strategy: Dict) -> Dict:
        """Generate race day execution strategy"""
        target_pace = pacing_strategy.get('target_pace_seconds', 300)
        
        strategy = {
            'pre_race': [
                'Warm up with 10-15 minutes easy jogging',
                'Include 4-6 strides at race pace',
                'Stay hydrated but avoid overdrinking',
                'Start 15-20 seconds slower than target pace'
            ],
            'early_race': [
                f'Maintain {self._format_pace(target_pace + 15)} for first 25% of race',
                'Focus on relaxed breathing and form',
                'Stay patient and avoid early surges'
            ],
            'mid_race': [
                f'Settle into target pace of {self._format_pace(target_pace)}',
                'Monitor effort level and adjust if needed',
                'Stay mentally engaged and positive'
            ],
            'late_race': [
                'Increase effort if feeling strong in final 25%',
                'Focus on form and cadence maintenance',
                'Use mental strategies to push through fatigue'
            ],
            'nutrition_hydration': self._generate_nutrition_strategy(race_distance)
        }
        
        return strategy
    
    def _calculate_optimization_metrics(self, activities: List[Activity], training_analysis: Dict) -> Dict:
        """Calculate key optimization metrics"""
        if not activities:
            return {}
        
        # Training load score
        training_load = self._calculate_training_load_score(activities)
        
        # Fitness trend score
        fitness_trend = self._calculate_fitness_trend_score(activities)
        
        # Readiness score
        readiness_score = self._calculate_readiness_score(activities, training_analysis)
        
        # Potential improvement estimate
        improvement_potential = self._estimate_improvement_potential(activities, training_analysis)
        
        return {
            'training_load_score': round(training_load, 1),
            'fitness_trend_score': round(fitness_trend, 1),
            'race_readiness_score': round(readiness_score, 1),
            'improvement_potential_percent': round(improvement_potential, 1),
            'overall_optimization_score': round((training_load + fitness_trend + readiness_score) / 3, 1)
        }
    
    # Helper methods
    def _calculate_consistency(self, values: List[float]) -> float:
        """Calculate consistency score from 0-100"""
        if len(values) < 2:
            return 0
        
        mean_val = statistics.mean(values)
        if mean_val == 0:
            return 0
        
        variance = statistics.variance(values)
        cv = (variance ** 0.5) / mean_val
        consistency = max(0, 100 - (cv * 50))
        return min(100, consistency)
    
    def _analyze_intensity_distribution(self, activities: List[Activity]) -> Dict:
        """Analyze training intensity distribution"""
        easy_count = moderate_count = hard_count = 0
        
        # Estimate threshold pace
        threshold_pace = self._estimate_threshold_pace(activities)
        
        for activity in activities:
            if not (activity.distance and activity.moving_time):
                continue
            
            pace = activity.moving_time / (activity.distance / 1000)
            
            if pace > threshold_pace * 1.15:  # Easy pace
                easy_count += 1
            elif pace > threshold_pace * 1.05:  # Moderate pace
                moderate_count += 1
            else:  # Hard pace
                hard_count += 1
        
        total = easy_count + moderate_count + hard_count
        if total == 0:
            return {}
        
        return {
            'easy_percentage': round((easy_count / total) * 100, 1),
            'moderate_percentage': round((moderate_count / total) * 100, 1),
            'hard_percentage': round((hard_count / total) * 100, 1)
        }
    
    def _analyze_workout_types(self, activities: List[Activity]) -> Dict:
        """Analyze workout type distribution"""
        # Simplified workout type analysis based on distance and pace
        short_runs = medium_runs = long_runs = 0
        
        for activity in activities:
            if not activity.distance:
                continue
            
            distance_km = activity.distance / 1000
            
            if distance_km < 5:
                short_runs += 1
            elif distance_km < 12:
                medium_runs += 1
            else:
                long_runs += 1
        
        total = short_runs + medium_runs + long_runs
        if total == 0:
            return {}
        
        return {
            'short_runs_percentage': round((short_runs / total) * 100, 1),
            'medium_runs_percentage': round((medium_runs / total) * 100, 1),
            'long_runs_percentage': round((long_runs / total) * 100, 1)
        }
    
    def _estimate_threshold_pace(self, activities: List[Activity]) -> float:
        """Estimate lactate threshold pace from training data"""
        valid_paces = []
        
        for activity in activities:
            if not (activity.distance and activity.moving_time):
                continue
            
            distance_km = activity.distance / 1000
            if distance_km >= 5:  # Use longer runs for threshold estimation
                pace = activity.moving_time / distance_km
                if 200 <= pace <= 600:  # Reasonable pace range
                    valid_paces.append(pace)
        
        if not valid_paces:
            return 360  # Default 6:00/km
        
        # Use median of faster efforts as threshold estimate
        valid_paces.sort()
        threshold_index = int(len(valid_paces) * 0.3)  # 30th percentile (faster efforts)
        return valid_paces[threshold_index]
    
    def _get_race_distance_km(self, race_distance: str) -> float:
        """Get race distance in kilometers"""
        distances = {
            '5K': 5.0,
            '10K': 10.0,
            'Half Marathon': 21.0975,
            'Marathon': 42.195
        }
        return distances.get(race_distance, 21.0975)
    
    def _calculate_target_race_pace(self, threshold_pace: float, distance_km: float) -> float:
        """Calculate target race pace based on distance"""
        if distance_km <= 5:
            return threshold_pace * 0.95  # 5% faster than threshold
        elif distance_km <= 10:
            return threshold_pace * 0.98  # 2% faster than threshold
        elif distance_km <= 21.1:
            return threshold_pace * 1.02  # 2% slower than threshold
        else:  # Marathon
            return threshold_pace * 1.08  # 8% slower than threshold
    
    def _format_pace(self, pace_seconds: float) -> str:
        """Format pace to MM:SS format"""
        minutes = int(pace_seconds // 60)
        seconds = int(pace_seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    def _format_time(self, total_seconds: float) -> str:
        """Format time to HH:MM:SS format"""
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    
    def _empty_optimization_plan(self, race_distance: str) -> Dict:
        """Return empty optimization plan when no data available"""
        return {
            'error': 'Insufficient training data',
            'message': 'Need at least 2 weeks of running activities to generate optimization plan',
            'race_distance': race_distance
        }
    
    # Additional helper methods for comprehensive analysis
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 3:
            return 'insufficient_data'
        
        recent_avg = statistics.mean(values[-3:])
        earlier_avg = statistics.mean(values[:-3]) if len(values) > 3 else statistics.mean(values[:3])
        
        if recent_avg > earlier_avg * 1.05:
            return 'increasing'
        elif recent_avg < earlier_avg * 0.95:
            return 'decreasing'
        else:
            return 'stable'
    
    def _analyze_pace_trend(self, activities: List[Activity]) -> Dict:
        """Analyze pace improvement trend"""
        paces = []
        dates = []
        
        for activity in activities:
            if not (activity.distance and activity.moving_time and activity.start_date):
                continue
            
            distance_km = activity.distance / 1000
            if distance_km >= 3:  # Use runs of 3km or longer
                pace = activity.moving_time / distance_km
                if 200 <= pace <= 600:
                    paces.append(pace)
                    dates.append(activity.start_date)
        
        if len(paces) < 5:
            return {'trend': 'insufficient_data'}
        
        # Calculate correlation between date and pace (negative = improving)
        # Simplified trend analysis
        recent_paces = paces[:len(paces)//3]  # Recent third
        earlier_paces = paces[len(paces)//3:]  # Earlier activities
        
        recent_avg = statistics.mean(recent_paces)
        earlier_avg = statistics.mean(earlier_paces)
        
        improvement_seconds = earlier_avg - recent_avg
        
        return {
            'trend': 'improving' if improvement_seconds > 5 else 'stable' if abs(improvement_seconds) <= 5 else 'declining',
            'improvement_seconds_per_km': round(improvement_seconds, 1),
            'recent_avg_pace': self._format_pace(recent_avg),
            'earlier_avg_pace': self._format_pace(earlier_avg)
        }
    
    def _analyze_distance_trend(self, activities: List[Activity]) -> Dict:
        """Analyze distance/volume trends"""
        weekly_volumes = []
        current_week_volume = 0
        current_week_start = None
        
        for activity in sorted(activities, key=lambda x: x.start_date or datetime.min):
            if not (activity.distance and activity.start_date):
                continue
            
            week_start = activity.start_date - timedelta(days=activity.start_date.weekday())
            
            if current_week_start != week_start:
                if current_week_start is not None:
                    weekly_volumes.append(current_week_volume)
                current_week_volume = 0
                current_week_start = week_start
            
            current_week_volume += activity.distance / 1000
        
        if current_week_volume > 0:
            weekly_volumes.append(current_week_volume)
        
        if len(weekly_volumes) < 3:
            return {'trend': 'insufficient_data'}
        
        trend = self._calculate_trend(weekly_volumes)
        
        return {
            'trend': trend,
            'avg_weekly_volume': round(statistics.mean(weekly_volumes), 1),
            'recent_weekly_avg': round(statistics.mean(weekly_volumes[-3:]), 1),
            'volume_consistency': round(self._calculate_consistency(weekly_volumes), 1)
        }
    
    def _analyze_heart_rate_trend(self, activities: List[Activity]) -> Dict:
        """Analyze heart rate trends if data available"""
        hr_values = []
        
        for activity in activities:
            if activity.average_heartrate and activity.average_heartrate > 100:
                hr_values.append(activity.average_heartrate)
        
        if len(hr_values) < 5:
            return {'trend': 'insufficient_data', 'message': 'Heart rate data not available'}
        
        trend = self._calculate_trend(hr_values)
        
        return {
            'trend': trend,
            'avg_heart_rate': round(statistics.mean(hr_values), 1),
            'recent_avg_hr': round(statistics.mean(hr_values[:len(hr_values)//3]), 1),
            'data_availability': 'good'
        }
    
    def _calculate_fitness_progression(self, activities: List[Activity]) -> Dict:
        """Calculate overall fitness progression score"""
        if len(activities) < 10:
            return {'score': 0, 'message': 'Insufficient data for progression analysis'}
        
        # Analyze multiple fitness indicators
        pace_scores = []
        volume_scores = []
        
        # Split activities into time periods
        mid_point = len(activities) // 2
        recent_activities = activities[:mid_point]
        earlier_activities = activities[mid_point:]
        
        # Compare pace improvements
        recent_paces = []
        earlier_paces = []
        
        for activity in recent_activities:
            if activity.distance and activity.moving_time and activity.distance > 3000:
                pace = activity.moving_time / (activity.distance / 1000)
                if 200 <= pace <= 600:
                    recent_paces.append(pace)
        
        for activity in earlier_activities:
            if activity.distance and activity.moving_time and activity.distance > 3000:
                pace = activity.moving_time / (activity.distance / 1000)
                if 200 <= pace <= 600:
                    earlier_paces.append(pace)
        
        if recent_paces and earlier_paces:
            recent_avg_pace = statistics.mean(recent_paces)
            earlier_avg_pace = statistics.mean(earlier_paces)
            pace_improvement = (earlier_avg_pace - recent_avg_pace) / earlier_avg_pace * 100
        else:
            pace_improvement = 0
        
        # Calculate overall progression score
        progression_score = max(0, min(100, 50 + pace_improvement * 10))
        
        return {
            'score': round(progression_score, 1),
            'pace_improvement_percent': round(pace_improvement, 2),
            'trend': 'improving' if pace_improvement > 1 else 'stable' if pace_improvement > -1 else 'declining'
        }
    
    def _calculate_improvement_rate(self, activities: List[Activity]) -> Dict:
        """Calculate rate of improvement over time"""
        if len(activities) < 15:
            return {'rate': 0, 'message': 'Need more activities for improvement rate calculation'}
        
        # Use time-based improvement analysis
        # Split into 3 periods and compare
        period_size = len(activities) // 3
        
        periods = [
            activities[:period_size],          # Most recent
            activities[period_size:period_size*2],  # Middle
            activities[period_size*2:]         # Earliest
        ]
        
        period_paces = []
        
        for period in periods:
            paces = []
            for activity in period:
                if activity.distance and activity.moving_time and activity.distance > 3000:
                    pace = activity.moving_time / (activity.distance / 1000)
                    if 200 <= pace <= 600:
                        paces.append(pace)
            
            if paces:
                period_paces.append(statistics.mean(paces))
        
        if len(period_paces) < 3:
            return {'rate': 0, 'message': 'Insufficient pace data'}
        
        # Calculate improvement rate (seconds per km per month)
        total_improvement = period_paces[-1] - period_paces[0]  # Earliest - Recent
        months_analyzed = len(activities) * 7 / 30  # Approximate months
        
        monthly_improvement = total_improvement / months_analyzed if months_analyzed > 0 else 0
        
        return {
            'rate': round(monthly_improvement, 2),
            'unit': 'seconds_per_km_per_month',
            'trend': 'improving' if monthly_improvement > 2 else 'stable' if monthly_improvement > -2 else 'declining'
        }
    
    def _generate_split_strategy(self, target_pace: float, distance_km: float, race_distance: str) -> List[Dict]:
        """Generate detailed split strategy"""
        splits = []
        
        if race_distance == '5K':
            # 5K split strategy
            splits.append({'km': 1, 'target_pace': self._format_pace(target_pace + 10), 'strategy': 'Start conservatively'})
            splits.append({'km': 2, 'target_pace': self._format_pace(target_pace + 5), 'strategy': 'Settle into rhythm'})
            splits.append({'km': 3, 'target_pace': self._format_pace(target_pace), 'strategy': 'Target pace'})
            splits.append({'km': 4, 'target_pace': self._format_pace(target_pace), 'strategy': 'Stay strong'})
            splits.append({'km': 5, 'target_pace': self._format_pace(target_pace - 5), 'strategy': 'Final push'})
        
        elif race_distance == '10K':
            # 10K split strategy
            for km in range(1, 11):
                if km <= 2:
                    pace = target_pace + 8
                    strategy = 'Conservative start'
                elif km <= 7:
                    pace = target_pace
                    strategy = 'Target pace'
                else:
                    pace = target_pace - 3
                    strategy = 'Pick up pace'
                
                splits.append({'km': km, 'target_pace': self._format_pace(pace), 'strategy': strategy})
        
        elif race_distance == 'Half Marathon':
            # Half Marathon split strategy (5K segments)
            segments = [
                {'km': '0-5', 'target_pace': self._format_pace(target_pace + 10), 'strategy': 'Conservative start'},
                {'km': '5-10', 'target_pace': self._format_pace(target_pace + 5), 'strategy': 'Settle in'},
                {'km': '10-15', 'target_pace': self._format_pace(target_pace), 'strategy': 'Target pace'},
                {'km': '15-21', 'target_pace': self._format_pace(target_pace), 'strategy': 'Stay strong to finish'}
            ]
            splits = segments
        
        else:  # Marathon
            # Marathon split strategy (10K segments)
            segments = [
                {'km': '0-10', 'target_pace': self._format_pace(target_pace + 15), 'strategy': 'Very conservative start'},
                {'km': '10-20', 'target_pace': self._format_pace(target_pace + 8), 'strategy': 'Gradual progression'},
                {'km': '20-30', 'target_pace': self._format_pace(target_pace), 'strategy': 'Target pace'},
                {'km': '30-42', 'target_pace': self._format_pace(target_pace + 5), 'strategy': 'Maintain effort, accept slower pace'}
            ]
            splits = segments
        
        return splits
    
    def _generate_hr_targets(self, activities: List[Activity], race_distance: str) -> Dict:
        """Generate heart rate targets if data available"""
        hr_values = [a.average_heartrate for a in activities if a.average_heartrate and a.average_heartrate > 100]
        
        if not hr_values:
            return {'message': 'Heart rate data not available for target calculation'}
        
        avg_hr = statistics.mean(hr_values)
        max_hr_estimate = avg_hr * 1.15  # Rough estimate
        
        if race_distance == '5K':
            target_hr_percent = 0.90
        elif race_distance == '10K':
            target_hr_percent = 0.85
        elif race_distance == 'Half Marathon':
            target_hr_percent = 0.80
        else:  # Marathon
            target_hr_percent = 0.75
        
        target_hr = max_hr_estimate * target_hr_percent
        
        return {
            'target_hr': round(target_hr),
            'target_hr_range': [round(target_hr - 5), round(target_hr + 5)],
            'avg_training_hr': round(avg_hr),
            'estimated_max_hr': round(max_hr_estimate)
        }
    
    def _generate_pacing_advice(self, race_distance: str) -> List[str]:
        """Generate race-specific pacing advice"""
        if race_distance == '5K':
            return [
                'Start 10-15 seconds slower than target pace',
                'Gradually increase pace after 2km',
                'Save energy for strong final kilometer',
                'Focus on maintaining turnover in final 1km'
            ]
        elif race_distance == '10K':
            return [
                'Start conservatively, 8-10 seconds slower than target',
                'Settle into target pace by 3km mark',
                'Begin gradual progression after 7km',
                'Maintain strong effort through finish'
            ]
        elif race_distance == 'Half Marathon':
            return [
                'Very conservative first 5km - 10+ seconds slower',
                'Gradually work down to target pace by 10km',
                'Focus on maintaining pace through 15km',
                'Stay mentally strong in final 6km'
            ]
        else:  # Marathon
            return [
                'Ultra-conservative first 10km - 15+ seconds slower',
                'Gradually progress to target pace by halfway',
                'Focus on maintaining effort (not pace) after 30km',
                'Break race into smaller segments mentally'
            ]
    
    def _generate_race_specific_recommendations(self, race_distance: str, training_analysis: Dict) -> List[Dict]:
        """Generate race-distance specific training recommendations"""
        recommendations = []
        
        if race_distance in ['5K', '10K']:
            recommendations.append({
                'category': 'Speed Work',
                'priority': 'High',
                'recommendation': 'Include weekly interval training at race pace',
                'implementation': f'4-6 x 1km at {race_distance} pace with 2-3min recovery',
                'timeline': '6-8 weeks'
            })
            
            recommendations.append({
                'category': 'VO2 Max',
                'priority': 'Medium',
                'recommendation': 'Add VO2 max intervals for speed development',
                'implementation': '5 x 3min at 5K pace with 3min recovery',
                'timeline': '4-6 weeks'
            })
        
        else:  # Half Marathon, Marathon
            recommendations.append({
                'category': 'Long Runs',
                'priority': 'High',
                'recommendation': 'Build weekly long run progressively',
                'implementation': f'Work up to {18 if race_distance == "Half Marathon" else 32}km long runs',
                'timeline': '8-12 weeks'
            })
            
            recommendations.append({
                'category': 'Tempo Work',
                'priority': 'High',
                'recommendation': 'Include weekly tempo runs at lactate threshold',
                'implementation': '20-40min at comfortably hard effort',
                'timeline': '6-10 weeks'
            })
        
        return recommendations
    
    def _analyze_pace_distribution(self, activities: List[Activity]) -> Dict:
        """Analyze variety in training paces"""
        paces = []
        
        for activity in activities:
            if activity.distance and activity.moving_time:
                pace = activity.moving_time / (activity.distance / 1000)
                if 200 <= pace <= 600:
                    paces.append(pace)
        
        if len(paces) < 5:
            return {'pace_variety_score': 0}
        
        # Calculate pace variety (coefficient of variation)
        pace_cv = (statistics.stdev(paces) / statistics.mean(paces)) * 100
        variety_score = min(100, pace_cv * 2)  # Scale to 0-100
        
        return {
            'pace_variety_score': round(variety_score, 1),
            'fastest_pace': self._format_pace(min(paces)),
            'slowest_pace': self._format_pace(max(paces)),
            'avg_pace': self._format_pace(statistics.mean(paces))
        }
    
    def _is_improving_trend(self, activities: List[Activity]) -> bool:
        """Check if recent activities show improvement"""
        if len(activities) < 5:
            return False
        
        paces = []
        for activity in activities:
            if activity.distance and activity.moving_time and activity.distance > 3000:
                pace = activity.moving_time / (activity.distance / 1000)
                if 200 <= pace <= 600:
                    paces.append(pace)
        
        if len(paces) < 5:
            return False
        
        # Check if recent paces are faster than earlier ones
        recent_avg = statistics.mean(paces[:len(paces)//2])
        earlier_avg = statistics.mean(paces[len(paces)//2:])
        
        return recent_avg < earlier_avg * 0.98  # 2% improvement threshold
    
    def _is_declining_trend(self, activities: List[Activity]) -> bool:
        """Check if recent activities show decline"""
        if len(activities) < 5:
            return False
        
        paces = []
        for activity in activities:
            if activity.distance and activity.moving_time and activity.distance > 3000:
                pace = activity.moving_time / (activity.distance / 1000)
                if 200 <= pace <= 600:
                    paces.append(pace)
        
        if len(paces) < 5:
            return False
        
        # Check if recent paces are slower than earlier ones
        recent_avg = statistics.mean(paces[:len(paces)//2])
        earlier_avg = statistics.mean(paces[len(paces)//2:])
        
        return recent_avg > earlier_avg * 1.02  # 2% decline threshold
    
    def _generate_overall_assessment(self, strengths: List[str], weaknesses: List[str]) -> str:
        """Generate overall training assessment"""
        if len(strengths) > len(weaknesses):
            return 'Strong overall training foundation with room for specific improvements'
        elif len(weaknesses) > len(strengths):
            return 'Several areas for improvement identified - focus on consistency and volume'
        else:
            return 'Balanced training profile with both strengths and development areas'
    
    def _generate_nutrition_strategy(self, race_distance: str) -> List[str]:
        """Generate race nutrition strategy"""
        if race_distance == '5K':
            return [
                'No nutrition needed during race',
                'Stay hydrated before race',
                'Light breakfast 2-3 hours before'
            ]
        elif race_distance == '10K':
            return [
                'Small sip of water at halfway if very hot',
                'No solid nutrition needed',
                'Normal pre-race meal 2-3 hours before'
            ]
        elif race_distance == 'Half Marathon':
            return [
                'Water at aid stations as needed',
                'Sports drink after 10km if desired',
                'Carbohydrate breakfast 3 hours before',
                'Consider energy gel at 15km if race over 1:45'
            ]
        else:  # Marathon
            return [
                'Water and sports drink at regular intervals',
                'Start fueling by 90 minutes into race',
                'Aim for 30-60g carbs per hour after hour 1',
                'Practice race nutrition in training',
                'Larger carbohydrate meal night before and morning of'
            ]
    
    def _calculate_training_load_score(self, activities: List[Activity]) -> float:
        """Calculate training load score 0-100"""
        if not activities:
            return 0
        
        total_distance = sum(a.distance or 0 for a in activities) / 1000
        total_time = sum(a.moving_time or 0 for a in activities) / 3600  # hours
        
        # Normalize based on number of weeks
        weeks = len(activities) * 7 / len(activities) if activities else 1
        weekly_distance = total_distance / weeks * 7
        weekly_hours = total_time / weeks * 7
        
        # Score based on training volume
        distance_score = min(100, weekly_distance * 2)  # Peak at 50km/week
        time_score = min(100, weekly_hours * 20)  # Peak at 5 hours/week
        
        return (distance_score + time_score) / 2
    
    def _calculate_fitness_trend_score(self, activities: List[Activity]) -> float:
        """Calculate fitness trend score 0-100"""
        if len(activities) < 10:
            return 50  # Neutral score
        
        # Analyze pace trend over time
        paces = []
        for activity in activities:
            if activity.distance and activity.moving_time and activity.distance > 3000:
                pace = activity.moving_time / (activity.distance / 1000)
                if 200 <= pace <= 600:
                    paces.append(pace)
        
        if len(paces) < 5:
            return 50
        
        # Compare recent vs earlier paces
        mid_point = len(paces) // 2
        recent_avg = statistics.mean(paces[:mid_point])
        earlier_avg = statistics.mean(paces[mid_point:])
        
        improvement_percent = (earlier_avg - recent_avg) / earlier_avg * 100
        
        # Convert to 0-100 score
        score = 50 + (improvement_percent * 10)  # 1% improvement = 10 points
        return max(0, min(100, score))
    
    def _calculate_readiness_score(self, activities: List[Activity], training_analysis: Dict) -> float:
        """Calculate race readiness score 0-100"""
        if not activities:
            return 0
        
        # Factors for readiness
        consistency = training_analysis.get('volume_consistency_score', 0)
        volume = training_analysis.get('avg_weekly_volume_km', 0)
        
        # Recent activity frequency
        recent_activities = [a for a in activities[:14] if a.start_date and 
                           a.start_date >= datetime.now() - timedelta(days=14)]
        frequency_score = min(100, len(recent_activities) * 20)  # Peak at 5 activities/2 weeks
        
        # Volume adequacy
        volume_score = min(100, volume * 3)  # Peak at ~33km/week
        
        # Weighted combination
        readiness = (consistency * 0.3 + volume_score * 0.3 + frequency_score * 0.4)
        return max(0, min(100, readiness))
    
    def _estimate_improvement_potential(self, activities: List[Activity], training_analysis: Dict) -> float:
        """Estimate potential for improvement as percentage"""
        if not activities:
            return 0
        
        consistency = training_analysis.get('volume_consistency_score', 0)
        volume = training_analysis.get('avg_weekly_volume_km', 0)
        
        # Areas for improvement
        consistency_gap = max(0, 90 - consistency) / 90 * 100
        volume_gap = max(0, 50 - volume) / 50 * 100  # Assume 50km/week as high volume
        
        # Average improvement potential
        potential = (consistency_gap + volume_gap) / 2
        
        # Cap at reasonable improvement levels
        return min(25, potential * 0.25)  # Max 25% improvement potential


def generate_race_optimization_plan(db_session: Session, athlete_id: int, race_distance: str, days_analysis: int = 90) -> Dict:
    """
    Global function to generate race optimization plan
    """
    optimizer = RaceOptimizer()
    return optimizer.generate_race_optimization_plan(db_session, athlete_id, race_distance, days_analysis)

def optimize_race_performance(db_session: Session, athlete_id: int, race_distance: str) -> Dict:
    """
    Optimize race performance with comprehensive analysis
    """
    optimizer = RaceOptimizer()
    return optimizer.generate_race_optimization_plan(db_session, athlete_id, race_distance, 90)

def get_pacing_strategy(db_session: Session, athlete_id: int, race_distance: str) -> Dict:
    """
    Get detailed pacing strategy for race
    """
    optimizer = RaceOptimizer()
    full_plan = optimizer.generate_race_optimization_plan(db_session, athlete_id, race_distance, 90)
    return full_plan.get('pacing_strategy', {})

def get_training_optimization(db_session: Session, athlete_id: int, race_distance: str) -> Dict:
    """
    Get training optimization recommendations
    """
    optimizer = RaceOptimizer()
    full_plan = optimizer.generate_race_optimization_plan(db_session, athlete_id, race_distance, 90)
    return {
        'training_recommendations': full_plan.get('training_recommendations', []),
        'strengths_weaknesses': full_plan.get('strengths_weaknesses', {}),
        'training_analysis': full_plan.get('training_analysis', {})
    }

class RacePerformanceOptimizer:
    """
    Legacy compatibility class
    """
    def __init__(self):
        self.optimizer = RaceOptimizer()
    
    def optimize_performance(self, db_session: Session, athlete_id: int, race_distance: str) -> Dict:
        return self.optimizer.generate_race_optimization_plan(db_session, athlete_id, race_distance, 90)