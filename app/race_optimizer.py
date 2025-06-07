"""
Advanced Race Performance Optimization System
Provides intelligent pacing strategies, training optimization, and performance maximization algorithms
for marathon athletes based on physiological data and training history.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func
from app.models import ReplitAthlete, Activity, OptimalValues, DailySummary

logger = logging.getLogger(__name__)

class RacePerformanceOptimizer:
    """
    Advanced race performance optimization system providing:
    - Optimal pacing strategies
    - Training load optimization
    - Performance prediction models
    - Race day recommendations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def optimize_race_strategy(self, athlete_id: int, race_distance: str, target_time: Optional[str] = None) -> Dict:
        """
        Generate comprehensive race optimization strategy
        """
        try:
            from app import db
            
            athlete = ReplitAthlete.query.get(athlete_id)
            if not athlete:
                return {'error': 'Athlete not found'}
            
            # Get recent training data (last 12 weeks)
            recent_activities = Activity.query.filter(
                Activity.athlete_id == athlete_id,
                Activity.start_date >= datetime.now() - timedelta(weeks=12),
                Activity.sport_type.in_(['Run', 'Running'])
            ).order_by(Activity.start_date.desc()).all()
            
            if not recent_activities:
                return {'error': 'Insufficient training data for optimization'}
            
            # Calculate current fitness metrics
            fitness_metrics = self._calculate_fitness_metrics(recent_activities, athlete)
            
            # Generate optimal pacing strategy
            pacing_strategy = self._generate_pacing_strategy(
                race_distance, fitness_metrics, target_time
            )
            
            # Create training optimization plan
            training_optimization = self._generate_training_optimization(
                athlete_id, race_distance, fitness_metrics
            )
            
            # Performance predictions with confidence intervals
            performance_prediction = self._predict_race_performance(
                fitness_metrics, race_distance, pacing_strategy
            )
            
            # Race day recommendations
            race_day_recommendations = self._generate_race_day_recommendations(
                athlete, race_distance, fitness_metrics, pacing_strategy
            )
            
            # Nutrition and hydration strategy
            nutrition_strategy = self._generate_nutrition_strategy(
                race_distance, performance_prediction['predicted_time_seconds'], athlete
            )
            
            return {
                'athlete_id': athlete_id,
                'race_distance': race_distance,
                'optimization_date': datetime.now().isoformat(),
                'fitness_metrics': fitness_metrics,
                'pacing_strategy': pacing_strategy,
                'training_optimization': training_optimization,
                'performance_prediction': performance_prediction,
                'race_day_recommendations': race_day_recommendations,
                'nutrition_strategy': nutrition_strategy,
                'confidence_score': self._calculate_optimization_confidence(fitness_metrics, recent_activities)
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing race strategy for athlete {athlete_id}: {str(e)}")
            return {'error': f'Optimization failed: {str(e)}'}
    
    def _calculate_fitness_metrics(self, activities: List[Activity], athlete: ReplitAthlete) -> Dict:
        """Calculate comprehensive fitness metrics from training data"""
        if not activities:
            return {}
        
        # Training load analysis
        total_distance = sum(getattr(a, 'distance', 0) or 0 for a in activities) / 1000  # km
        total_time = sum(getattr(a, 'moving_time', 0) or 0 for a in activities) / 3600  # hours
        
        # Pace analysis
        running_activities = [a for a in activities if getattr(a, 'distance', 0) and getattr(a, 'moving_time', 0)]
        if running_activities:
            avg_pace_per_km = sum(
                (getattr(a, 'moving_time', 0) / 60) / (getattr(a, 'distance', 0) / 1000)
                for a in running_activities
            ) / len(running_activities)
        else:
            avg_pace_per_km = 0
        
        # Long run analysis
        long_runs = [a for a in activities if getattr(a, 'distance', 0) and getattr(a, 'distance', 0) > 15000]  # 15km+
        max_distance = max((getattr(a, 'distance', 0) or 0) / 1000 for a in activities) if activities else 0
        
        # Weekly volume analysis
        weekly_volumes = self._calculate_weekly_volumes(activities)
        avg_weekly_volume = sum(weekly_volumes) / len(weekly_volumes) if weekly_volumes else 0
        peak_weekly_volume = max(weekly_volumes) if weekly_volumes else 0
        
        # Speed work analysis
        speed_activities = [a for a in activities if getattr(a, 'average_speed', 0) and getattr(a, 'average_speed', 0) > 4.0]  # >14.4 km/h
        speed_percentage = (len(speed_activities) / len(activities)) * 100 if activities else 0
        
        # Heart rate analysis
        hr_activities = [a for a in activities if getattr(a, 'average_heartrate', 0)]
        if hr_activities and athlete.max_hr:
            avg_hr_intensity = sum(getattr(a, 'average_heartrate', 0) for a in hr_activities) / len(hr_activities)
            hr_intensity_percentage = (avg_hr_intensity / athlete.max_hr) * 100
        else:
            hr_intensity_percentage = 0
        
        # Calculate VDOT (running fitness index)
        vdot = self._calculate_vdot(avg_pace_per_km, hr_intensity_percentage)
        
        # Training consistency
        training_days = len(set(a.start_date.date() for a in activities))
        total_days = (max(a.start_date for a in activities) - min(a.start_date for a in activities)).days + 1
        consistency_score = (training_days / total_days) * 100 if total_days > 0 else 0
        
        return {
            'total_distance_km': round(total_distance, 1),
            'total_training_hours': round(total_time, 1),
            'avg_pace_per_km_minutes': round(avg_pace_per_km, 2),
            'max_distance_km': round(max_distance, 1),
            'long_runs_count': len(long_runs),
            'avg_weekly_volume_km': round(avg_weekly_volume, 1),
            'peak_weekly_volume_km': round(peak_weekly_volume, 1),
            'speed_work_percentage': round(speed_percentage, 1),
            'hr_intensity_percentage': round(hr_intensity_percentage, 1),
            'vdot_score': round(vdot, 1),
            'training_consistency': round(consistency_score, 1),
            'activities_analyzed': len(activities),
            'training_period_weeks': round(total_days / 7, 1) if total_days > 0 else 0
        }
    
    def _calculate_weekly_volumes(self, activities: List[Activity]) -> List[float]:
        """Calculate weekly training volumes"""
        if not activities:
            return []
        
        weekly_volumes = {}
        for activity in activities:
            week_key = activity.start_date.strftime('%Y-W%U')
            distance_km = (getattr(activity, 'distance', 0) or 0) / 1000
            weekly_volumes[week_key] = weekly_volumes.get(week_key, 0) + distance_km
        
        return list(weekly_volumes.values())
    
    def _calculate_vdot(self, avg_pace_minutes: float, hr_intensity: float) -> float:
        """Calculate VDOT running fitness score"""
        if avg_pace_minutes <= 0:
            return 30.0  # Default baseline
        
        # Simplified VDOT calculation based on pace and heart rate
        # Real VDOT uses specific race times, this is an approximation
        base_vdot = 15.0 + (480 / avg_pace_minutes)  # Base calculation
        
        # Adjust for heart rate intensity
        if hr_intensity > 0:
            hr_adjustment = (85 - hr_intensity) * 0.2  # Optimal around 85% max HR
            base_vdot += hr_adjustment
        
        return max(min(base_vdot, 85.0), 25.0)  # Clamp between 25-85
    
    def _generate_pacing_strategy(self, race_distance: str, fitness_metrics: Dict, target_time: Optional[str]) -> Dict:
        """Generate optimal pacing strategy for the race"""
        distance_km = self._get_race_distance_km(race_distance)
        
        if target_time:
            target_seconds = self._parse_time_to_seconds(target_time)
            target_pace_per_km = target_seconds / distance_km
        else:
            # Predict optimal pace based on fitness
            target_pace_per_km = self._predict_optimal_pace(fitness_metrics, distance_km)
            target_seconds = target_pace_per_km * distance_km
        
        # Generate split strategy
        splits = self._generate_race_splits(distance_km, target_pace_per_km, fitness_metrics)
        
        # Pacing zones
        easy_pace = target_pace_per_km * 1.15
        tempo_pace = target_pace_per_km * 0.95
        threshold_pace = target_pace_per_km * 0.90
        
        return {
            'race_distance_km': distance_km,
            'target_time_formatted': self._format_seconds_to_time(target_seconds),
            'target_time_seconds': int(target_seconds),
            'target_pace_per_km': round(target_pace_per_km, 2),
            'target_pace_formatted': self._format_pace(target_pace_per_km),
            'splits': splits,
            'pacing_zones': {
                'easy_pace': self._format_pace(easy_pace),
                'tempo_pace': self._format_pace(tempo_pace),
                'threshold_pace': self._format_pace(threshold_pace),
                'target_pace': self._format_pace(target_pace_per_km)
            },
            'negative_split_recommended': distance_km >= 21.0,  # For half marathon and longer
            'strategy_type': self._determine_pacing_strategy(distance_km, fitness_metrics)
        }
    
    def _predict_optimal_pace(self, fitness_metrics: Dict, distance_km: float) -> float:
        """Predict optimal race pace based on current fitness"""
        base_pace = fitness_metrics.get('avg_pace_per_km_minutes', 6.0) * 60  # Convert to seconds
        
        # Adjust for race distance
        if distance_km <= 5:
            pace_factor = 0.85  # 5K pace
        elif distance_km <= 10:
            pace_factor = 0.90  # 10K pace
        elif distance_km <= 21.1:
            pace_factor = 0.95  # Half marathon pace
        else:
            pace_factor = 1.00  # Marathon pace
        
        # Adjust for fitness level (VDOT)
        vdot = fitness_metrics.get('vdot_score', 40)
        if vdot > 60:
            fitness_factor = 0.90
        elif vdot > 50:
            fitness_factor = 0.95
        elif vdot > 40:
            fitness_factor = 1.00
        else:
            fitness_factor = 1.10
        
        optimal_pace = base_pace * pace_factor * fitness_factor
        return max(optimal_pace, 180)  # Minimum 3:00/km pace
    
    def _generate_race_splits(self, distance_km: float, target_pace: float, fitness_metrics: Dict) -> List[Dict]:
        """Generate detailed race splits with pacing strategy"""
        splits = []
        
        if distance_km <= 10:
            # Short distance - even splits
            split_distance = 1.0
            num_splits = int(distance_km)
            split_pace = target_pace
        elif distance_km <= 21.1:
            # Half marathon - slight negative split
            split_distance = 5.0
            num_splits = int(distance_km / split_distance)
            split_pace = target_pace
        else:
            # Marathon - conservative start, negative split
            split_distance = 5.0
            num_splits = int(distance_km / split_distance)
            split_pace = target_pace
        
        cumulative_distance = 0
        cumulative_time = 0
        
        for i in range(num_splits):
            current_distance = min(split_distance, distance_km - cumulative_distance)
            
            # Adjust pace for different portions of the race
            if distance_km >= 42.0:  # Marathon pacing strategy
                if i == 0:  # First 5km - conservative
                    pace_adjustment = 1.05
                elif i < 6:  # Next 25km - target pace
                    pace_adjustment = 1.00
                elif i < 8:  # Last 10km - push if feeling good
                    pace_adjustment = 0.98
                else:  # Final stretch
                    pace_adjustment = 0.95
            else:
                pace_adjustment = 1.00  # Even pacing for shorter distances
            
            adjusted_pace = split_pace * pace_adjustment
            split_time = adjusted_pace * current_distance
            cumulative_distance += current_distance
            cumulative_time += split_time
            
            splits.append({
                'split_number': i + 1,
                'distance_km': round(current_distance, 1),
                'cumulative_distance_km': round(cumulative_distance, 1),
                'pace_per_km': round(adjusted_pace, 2),
                'pace_formatted': self._format_pace(adjusted_pace),
                'split_time_seconds': int(split_time),
                'split_time_formatted': self._format_seconds_to_time(split_time),
                'cumulative_time_seconds': int(cumulative_time),
                'cumulative_time_formatted': self._format_seconds_to_time(cumulative_time)
            })
        
        return splits
    
    def _generate_training_optimization(self, athlete_id: int, race_distance: str, fitness_metrics: Dict) -> Dict:
        """Generate training optimization recommendations"""
        distance_km = self._get_race_distance_km(race_distance)
        
        # Calculate current weekly volume
        current_volume = fitness_metrics.get('avg_weekly_volume_km', 0)
        
        # Recommend optimal weekly volume based on race distance
        if distance_km <= 10:
            optimal_volume = max(current_volume * 1.1, 40)
        elif distance_km <= 21.1:
            optimal_volume = max(current_volume * 1.2, 60)
        else:  # Marathon
            optimal_volume = max(current_volume * 1.3, 80)
        
        # Training distribution
        easy_percentage = 80
        tempo_percentage = 15
        speed_percentage = 5
        
        return {
            'current_weekly_volume_km': fitness_metrics.get('avg_weekly_volume_km', 0),
            'recommended_weekly_volume_km': round(optimal_volume, 1),
            'volume_increase_needed': round(optimal_volume - current_volume, 1),
            'training_distribution': {
                'easy_runs_percentage': easy_percentage,
                'tempo_runs_percentage': tempo_percentage,
                'speed_work_percentage': speed_percentage,
                'easy_volume_km': round(optimal_volume * easy_percentage / 100, 1),
                'tempo_volume_km': round(optimal_volume * tempo_percentage / 100, 1),
                'speed_volume_km': round(optimal_volume * speed_percentage / 100, 1)
            },
            'key_workouts': self._generate_key_workouts(race_distance, fitness_metrics),
            'long_run_recommendations': self._generate_long_run_plan(race_distance, fitness_metrics),
            'recovery_recommendations': self._generate_recovery_plan(optimal_volume, fitness_metrics)
        }
    
    def _generate_key_workouts(self, race_distance: str, fitness_metrics: Dict) -> List[Dict]:
        """Generate race-specific key workout recommendations"""
        distance_km = self._get_race_distance_km(race_distance)
        target_pace = self._predict_optimal_pace(fitness_metrics, distance_km)
        
        workouts = []
        
        if distance_km <= 10:
            # 5K/10K workouts
            workouts.extend([
                {
                    'name': 'VO2 Max Intervals',
                    'description': '6 x 800m at 5K pace with 400m recovery',
                    'pace_target': self._format_pace(target_pace * 0.85),
                    'frequency': 'Weekly'
                },
                {
                    'name': 'Tempo Run',
                    'description': '20-25 minutes at comfortably hard pace',
                    'pace_target': self._format_pace(target_pace * 0.92),
                    'frequency': 'Weekly'
                }
            ])
        elif distance_km <= 21.1:
            # Half marathon workouts
            workouts.extend([
                {
                    'name': 'Threshold Intervals',
                    'description': '3 x 2km at half marathon pace with 90s recovery',
                    'pace_target': self._format_pace(target_pace),
                    'frequency': 'Bi-weekly'
                },
                {
                    'name': 'Progressive Long Run',
                    'description': '16-18km with last 6km at half marathon pace',
                    'pace_target': self._format_pace(target_pace),
                    'frequency': 'Every 3 weeks'
                }
            ])
        else:
            # Marathon workouts
            workouts.extend([
                {
                    'name': 'Marathon Pace Run',
                    'description': '16-20km at goal marathon pace',
                    'pace_target': self._format_pace(target_pace),
                    'frequency': 'Every 2 weeks'
                },
                {
                    'name': 'Long Run with Surges',
                    'description': '28-32km with 3 x 3km surges at marathon pace',
                    'pace_target': self._format_pace(target_pace),
                    'frequency': 'Every 3 weeks'
                }
            ])
        
        return workouts
    
    def _generate_long_run_plan(self, race_distance: str, fitness_metrics: Dict) -> Dict:
        """Generate long run progression plan"""
        distance_km = self._get_race_distance_km(race_distance)
        current_max = fitness_metrics.get('max_distance_km', 0)
        
        if distance_km <= 10:
            target_long_run = 15
        elif distance_km <= 21.1:
            target_long_run = 22
        else:
            target_long_run = 35
        
        weekly_increase = 2.0  # km per week
        weeks_needed = max(0, (target_long_run - current_max) / weekly_increase)
        
        return {
            'current_long_run_km': current_max,
            'target_long_run_km': target_long_run,
            'weekly_increase_km': weekly_increase,
            'weeks_to_target': int(weeks_needed),
            'long_run_pace': self._format_pace(self._predict_optimal_pace(fitness_metrics, distance_km) * 1.15),
            'frequency': 'Weekly',
            'cutback_week_frequency': 'Every 4th week'
        }
    
    def _generate_recovery_plan(self, weekly_volume: float, fitness_metrics: Dict) -> Dict:
        """Generate recovery and rest recommendations"""
        training_days = int(weekly_volume / 8)  # Approximate 8km per training day
        rest_days = 7 - training_days
        
        return {
            'recommended_training_days': min(training_days, 6),
            'recommended_rest_days': max(rest_days, 1),
            'easy_run_percentage': 80,
            'sleep_hours_minimum': 8,
            'cross_training_sessions': 1 if weekly_volume > 50 else 0,
            'massage_frequency': 'Bi-weekly' if weekly_volume > 60 else 'Monthly',
            'stretching_minutes_daily': 15
        }
    
    def _predict_race_performance(self, fitness_metrics: Dict, race_distance: str, pacing_strategy: Dict) -> Dict:
        """Predict race performance with confidence intervals"""
        distance_km = self._get_race_distance_km(race_distance)
        base_time = pacing_strategy['target_time_seconds']
        
        # Confidence factors
        volume_factor = min(fitness_metrics.get('avg_weekly_volume_km', 0) / (distance_km * 2), 1.0)
        consistency_factor = fitness_metrics.get('training_consistency', 0) / 100
        experience_factor = min(fitness_metrics.get('long_runs_count', 0) / 10, 1.0)
        
        confidence = (volume_factor + consistency_factor + experience_factor) / 3
        
        # Performance range
        best_case = base_time * 0.97  # 3% faster
        worst_case = base_time * 1.08  # 8% slower
        
        return {
            'predicted_time_seconds': int(base_time),
            'predicted_time_formatted': self._format_seconds_to_time(base_time),
            'best_case_seconds': int(best_case),
            'best_case_formatted': self._format_seconds_to_time(best_case),
            'worst_case_seconds': int(worst_case),
            'worst_case_formatted': self._format_seconds_to_time(worst_case),
            'confidence_percentage': round(confidence * 100, 1),
            'performance_factors': {
                'training_volume': round(volume_factor * 100, 1),
                'consistency': round(consistency_factor * 100, 1),
                'experience': round(experience_factor * 100, 1)
            }
        }
    
    def _generate_race_day_recommendations(self, athlete: ReplitAthlete, race_distance: str, 
                                         fitness_metrics: Dict, pacing_strategy: Dict) -> Dict:
        """Generate comprehensive race day recommendations"""
        distance_km = self._get_race_distance_km(race_distance)
        
        return {
            'warm_up': {
                'duration_minutes': 15 if distance_km >= 21 else 20,
                'structure': 'Easy jog + dynamic stretches + 3 x 100m strides',
                'timing': '30-45 minutes before race start'
            },
            'pacing_guidance': {
                'start_strategy': 'Conservative' if distance_km >= 21 else 'Controlled aggressive',
                'first_mile_target': pacing_strategy['target_pace_formatted'],
                'middle_section': 'Maintain steady effort, monitor heart rate',
                'final_section': 'Increase effort if feeling strong'
            },
            'mental_strategy': {
                'focus_points': ['Relaxed breathing', 'Efficient form', 'Positive self-talk'],
                'mile_markers': 'Break race into 3-4 segments',
                'mantras': ['Stay strong', 'Trust your training', 'One step at a time']
            },
            'gear_recommendations': {
                'shoes': 'Tested racing shoes with 50+ miles',
                'clothing': 'Lightweight, moisture-wicking fabrics',
                'accessories': 'GPS watch, tested nutrition items only'
            },
            'weather_adjustments': {
                'hot_weather': 'Start 5-10s/km slower, increase hydration',
                'cold_weather': 'Extended warm-up, layer appropriately',
                'windy_conditions': 'Draft when possible, adjust effort on headwinds'
            }
        }
    
    def _generate_nutrition_strategy(self, race_distance: str, race_time_seconds: int, athlete: ReplitAthlete) -> Dict:
        """Generate race nutrition and hydration strategy"""
        distance_km = self._get_race_distance_km(race_distance)
        race_hours = race_time_seconds / 3600
        
        if distance_km <= 10:
            # Short races - minimal nutrition needed
            return {
                'pre_race': {
                    'timing': '2-3 hours before',
                    'foods': ['Banana', 'Toast with honey', 'Coffee if habitual'],
                    'fluids': '400-500ml water'
                },
                'during_race': {
                    'nutrition': 'Water only at aid stations',
                    'strategy': 'No solid foods needed'
                },
                'post_race': {
                    'timing': 'Within 30 minutes',
                    'foods': ['Recovery drink', 'Protein + carbs'],
                    'fluids': 'Replace 150% of fluid lost'
                }
            }
        else:
            # Long races - comprehensive nutrition strategy
            carb_grams_per_hour = 60 if race_hours <= 2.5 else 90
            fluid_ml_per_hour = 500 if race_hours <= 3 else 750
            
            return {
                'pre_race': {
                    'timing': '3-4 hours before',
                    'foods': ['Oatmeal with banana', 'Toast with jam', 'Coffee if habitual'],
                    'fluids': '500-750ml water + electrolytes',
                    'avoid': ['High fiber', 'High fat', 'New foods']
                },
                'during_race': {
                    'carb_grams_per_hour': carb_grams_per_hour,
                    'fluid_ml_per_hour': fluid_ml_per_hour,
                    'start_fueling': 'After 45-60 minutes',
                    'frequency': 'Every 15-20 minutes',
                    'options': ['Sports drink', 'Gels', 'Bananas at aid stations'],
                    'electrolytes': 'Include sodium in longer races'
                },
                'aid_station_strategy': {
                    'approach': 'Slow down slightly, don\'t stop',
                    'practice': 'Train drinking while running',
                    'backup_plan': 'Carry backup gel/nutrition'
                },
                'post_race': {
                    'timing': 'Within 30-60 minutes',
                    'carb_protein_ratio': '3:1 or 4:1',
                    'fluids': 'Replace 150% of weight lost',
                    'foods': ['Recovery shake', 'Chocolate milk', 'Sandwich']
                }
            }
    
    def _calculate_optimization_confidence(self, fitness_metrics: Dict, activities: List[Activity]) -> float:
        """Calculate confidence score for optimization recommendations"""
        factors = []
        
        # Data quantity factor
        activity_count = len(activities)
        if activity_count >= 50:
            factors.append(1.0)
        elif activity_count >= 20:
            factors.append(0.8)
        else:
            factors.append(0.5)
        
        # Training consistency factor
        consistency = fitness_metrics.get('training_consistency', 0) / 100
        factors.append(consistency)
        
        # Training volume factor
        volume = fitness_metrics.get('avg_weekly_volume_km', 0)
        if volume >= 60:
            factors.append(1.0)
        elif volume >= 30:
            factors.append(0.8)
        else:
            factors.append(0.6)
        
        # Long run experience factor
        long_runs = fitness_metrics.get('long_runs_count', 0)
        if long_runs >= 10:
            factors.append(1.0)
        elif long_runs >= 5:
            factors.append(0.8)
        else:
            factors.append(0.6)
        
        return sum(factors) / len(factors)
    
    def _determine_pacing_strategy(self, distance_km: float, fitness_metrics: Dict) -> str:
        """Determine optimal pacing strategy type"""
        if distance_km <= 5:
            return 'Even pacing with strong finish'
        elif distance_km <= 10:
            return 'Slightly negative split'
        elif distance_km <= 21.1:
            return 'Conservative start, negative split'
        else:
            return 'Conservative first half, controlled second half'
    
    def _get_race_distance_km(self, race_distance: str) -> float:
        """Convert race distance string to kilometers"""
        distances = {
            '5K': 5.0,
            '10K': 10.0,
            'Half Marathon': 21.0975,
            'Marathon': 42.195
        }
        return distances.get(race_distance, 10.0)
    
    def _parse_time_to_seconds(self, time_str: str) -> int:
        """Parse time string (HH:MM:SS or MM:SS) to seconds"""
        try:
            parts = time_str.split(':')
            if len(parts) == 2:  # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except ValueError:
            pass
        return 0
    
    def _format_seconds_to_time(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS or MM:SS"""
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def _format_pace(self, pace_seconds: float) -> str:
        """Format pace in seconds per km to MM:SS format"""
        minutes = int(pace_seconds // 60)
        seconds = int(pace_seconds % 60)
        return f"{minutes}:{seconds:02d}"


# Global functions for API endpoints
def optimize_race_performance(athlete_id: int, race_distance: str, target_time: Optional[str] = None) -> Dict:
    """Global function for race performance optimization"""
    optimizer = RacePerformanceOptimizer()
    return optimizer.optimize_race_strategy(athlete_id, race_distance, target_time)

def get_pacing_strategy(athlete_id: int, race_distance: str, target_time: Optional[str] = None) -> Dict:
    """Get pacing strategy specifically"""
    result = optimize_race_performance(athlete_id, race_distance, target_time)
    return result.get('pacing_strategy', {})

def get_training_optimization(athlete_id: int, race_distance: str) -> Dict:
    """Get training optimization recommendations"""
    result = optimize_race_performance(athlete_id, race_distance)
    return result.get('training_optimization', {})