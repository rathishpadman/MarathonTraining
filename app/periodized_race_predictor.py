"""
Advanced Periodized Race Predictor
Incorporates training duration, progression patterns, and global performance data
for accurate marathon and race time predictions
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app.models import Activity, ReplitAthlete
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class PeriodizedRacePredictor:
    """
    Advanced race predictor that accounts for training periodization,
    progressive improvement, and time-to-race considerations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Global performance benchmarks (conservative, realistic rates)
        self.global_improvement_rates = {
            'beginner': {'weekly': 0.008, 'monthly': 0.03, 'seasonal': 0.12},
            'intermediate': {'weekly': 0.005, 'monthly': 0.02, 'seasonal': 0.08},
            'advanced': {'weekly': 0.003, 'monthly': 0.01, 'seasonal': 0.04}
        }
        
        # Training adaptation curves (conservative, realistic improvements)
        self.adaptation_curves = {
            'aerobic_base': {4: 0.03, 8: 0.07, 12: 0.10, 16: 0.13, 20: 0.15},
            'lactate_threshold': {2: 0.02, 4: 0.05, 6: 0.07, 8: 0.09, 12: 0.11},
            'vo2_max': {1: 0.01, 2: 0.03, 4: 0.05, 6: 0.06, 8: 0.07}
        }
        
        # Race distance factors (based on McMillan/Daniels research)
        self.race_distance_factors = {
            5.0: {'aerobic': 0.15, 'lactate': 0.35, 'vo2': 0.50},
            10.0: {'aerobic': 0.25, 'lactate': 0.55, 'vo2': 0.20},
            21.0975: {'aerobic': 0.60, 'lactate': 0.35, 'vo2': 0.05},
            42.195: {'aerobic': 0.80, 'lactate': 0.18, 'vo2': 0.02}
        }
    
    def predict_race_performance_with_training_duration(
        self, 
        db_session: Session, 
        athlete_id: int, 
        race_distance_km: float, 
        weeks_to_race: int = 12,
        target_improvement_percent: float = None
    ) -> Dict:
        """
        Predict race performance accounting for training duration and progression
        
        Args:
            athlete_id: Athlete identifier
            race_distance_km: Target race distance in kilometers
            weeks_to_race: Training weeks available before race
            target_improvement_percent: Optional target improvement (e.g., 0.20 for 20%)
        """
        
        self.logger.info(f"Predicting race performance for athlete {athlete_id}, "
                        f"distance: {race_distance_km}km, training time: {weeks_to_race} weeks")
        
        # Get athlete's current fitness baseline
        baseline_fitness = self._calculate_current_fitness_baseline(db_session, athlete_id)
        
        if not baseline_fitness['valid']:
            return self._generate_fallback_prediction(race_distance_km, weeks_to_race)
        
        # Analyze training history to determine athlete level
        athlete_level = self._classify_athlete_level(db_session, athlete_id, baseline_fitness)
        
        # Calculate progressive improvement potential
        improvement_potential = self._calculate_improvement_potential(
            athlete_level, weeks_to_race, baseline_fitness, target_improvement_percent
        )
        
        # Generate periodized training plan simulation
        training_adaptation = self._simulate_training_adaptation(
            weeks_to_race, athlete_level, race_distance_km
        )
        
        # Predict final race performance
        race_prediction = self._calculate_periodized_race_time(
            baseline_fitness, improvement_potential, training_adaptation, race_distance_km
        )
        
        # Generate progressive milestones
        milestones = self._generate_training_milestones(
            baseline_fitness, race_prediction, weeks_to_race
        )
        
        return {
            'race_distance_km': race_distance_km,
            'weeks_to_race': weeks_to_race,
            'baseline_fitness': baseline_fitness,
            'athlete_level': athlete_level,
            'predicted_race_time_seconds': race_prediction['race_time'],
            'predicted_race_pace_per_km': race_prediction['pace_per_km'],
            'improvement_potential': improvement_potential,
            'training_adaptation': training_adaptation,
            'progressive_milestones': milestones,
            'confidence_score': race_prediction['confidence'],
            'methodology': 'periodized_training_analysis'
        }
    
    def _calculate_current_fitness_baseline(self, db_session: Session, athlete_id: int) -> Dict:
        """Calculate athlete's current fitness baseline from recent activities"""
        
        # Get last 60 days of activities for baseline
        cutoff_date = datetime.now() - timedelta(days=60)
        activities = db_session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= cutoff_date,
            Activity.sport_type.in_(['Run', 'VirtualRun']),
            Activity.distance > 1000  # At least 1km
        ).order_by(Activity.start_date.desc()).all()
        
        if len(activities) < 5:
            return {'valid': False, 'reason': 'insufficient_data'}
        
        # Calculate key fitness metrics
        total_distance = sum(a.distance / 1000 for a in activities if a.distance)
        total_time = sum(a.moving_time for a in activities if a.moving_time)
        
        avg_pace_per_km = (total_time / 60) / total_distance if total_distance > 0 else 0
        
        # Calculate weekly volume: recent activities averaged over actual weeks
        if len(activities) >= 4:  # Need at least 4 activities for reliable calculation
            # Get the actual date range of activities
            activity_dates = [a.start_date for a in activities if a.start_date]
            if activity_dates:
                earliest_date = min(activity_dates)
                latest_date = max(activity_dates)
                actual_weeks = max(1, (latest_date - earliest_date).days / 7)
                weekly_volume = total_distance / actual_weeks
            else:
                weekly_volume = total_distance / 8.57  # Default to ~60 days / 7
        else:
            weekly_volume = total_distance / 8.57  # Default calculation
        
        # Analyze pace distribution for different distances
        short_runs = [a for a in activities if a.distance and a.distance < 8000]
        medium_runs = [a for a in activities if a.distance and 8000 <= a.distance < 15000]
        long_runs = [a for a in activities if a.distance and a.distance >= 15000]
        
        # Calculate threshold pace estimate (from tempo/medium runs)
        if medium_runs:
            threshold_pace_estimates = []
            for run in medium_runs:
                if run.distance and run.moving_time:
                    pace = (run.moving_time / 60) / (run.distance / 1000)
                    threshold_pace_estimates.append(pace)
            threshold_pace = np.median(threshold_pace_estimates) if threshold_pace_estimates else avg_pace_per_km
        else:
            threshold_pace = avg_pace_per_km * 0.95  # Estimate threshold as 5% faster than average
        
        return {
            'valid': True,
            'avg_pace_per_km': avg_pace_per_km,
            'threshold_pace_per_km': threshold_pace,
            'weekly_volume_km': weekly_volume,
            'total_activities': len(activities),
            'long_run_capability': max((a.distance / 1000 for a in activities if a.distance), default=0),
            'training_consistency': len(activities) / 8.6,  # Activities per week over 60 days
            'recent_form_trend': self._calculate_recent_trend(activities)
        }
    
    def _calculate_recent_trend(self, activities: List[Activity]) -> float:
        """Calculate recent performance trend (positive = improving)"""
        if len(activities) < 6:
            return 0.0
        
        # Split into first and second half of period
        mid_point = len(activities) // 2
        recent_activities = activities[:mid_point]
        older_activities = activities[mid_point:]
        
        def avg_pace_for_period(acts):
            total_time = sum(a.moving_time for a in acts if a.moving_time)
            total_distance = sum(a.distance / 1000 for a in acts if a.distance)
            return (total_time / 60) / total_distance if total_distance > 0 else 0
        
        recent_pace = avg_pace_for_period(recent_activities)
        older_pace = avg_pace_for_period(older_activities)
        
        # Negative trend means getting faster (improvement)
        return (older_pace - recent_pace) / older_pace if older_pace > 0 else 0.0
    
    def _classify_athlete_level(self, db_session: Session, athlete_id: int, baseline: Dict) -> str:
        """Classify athlete as beginner, intermediate, or advanced"""
        
        # Get total training history
        all_activities = db_session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.sport_type.in_(['Run', 'VirtualRun'])
        ).count()
        
        weekly_volume = baseline['weekly_volume_km']
        pace = baseline['avg_pace_per_km']
        long_run_distance = baseline['long_run_capability']
        
        # Classification based on multiple factors
        score = 0
        
        # Volume factor
        if weekly_volume >= 50: score += 2
        elif weekly_volume >= 30: score += 1
        
        # Experience factor
        if all_activities >= 100: score += 2
        elif all_activities >= 50: score += 1
        
        # Long run capability
        if long_run_distance >= 20: score += 2
        elif long_run_distance >= 15: score += 1
        
        # Pace factor (rough estimates)
        if pace <= 4.5: score += 2  # Sub-4:30/km (competitive level)
        elif pace <= 5.5: score += 1  # Sub-5:30/km (good recreational)
        
        if score >= 5:
            return 'advanced'
        elif score >= 2:
            return 'intermediate'
        else:
            return 'beginner'
    
    def _calculate_improvement_potential(
        self, 
        athlete_level: str, 
        weeks_to_race: int, 
        baseline: Dict,
        target_improvement: Optional[float] = None
    ) -> Dict:
        """Calculate realistic improvement potential over training period"""
        
        rates = self.global_improvement_rates[athlete_level]
        
        # Base improvement potential from training duration
        if weeks_to_race <= 4:
            base_improvement = rates['weekly'] * weeks_to_race
        elif weeks_to_race <= 16:
            base_improvement = rates['monthly'] * (weeks_to_race / 4)
        else:
            base_improvement = rates['seasonal'] * min(weeks_to_race / 20, 1.5)
        
        # Adjust for current form and consistency
        form_factor = 1.0 + baseline['recent_form_trend']  # If already improving, potential is higher
        consistency_factor = min(baseline['training_consistency'], 1.2)  # Cap at 20% bonus
        
        adjusted_improvement = base_improvement * form_factor * consistency_factor
        
        # Apply target improvement if specified (but cap at realistic limits)
        if target_improvement:
            max_realistic = adjusted_improvement * 1.5  # 50% above calculated potential
            final_improvement = min(target_improvement, max_realistic)
        else:
            final_improvement = adjusted_improvement
        
        return {
            'base_improvement_percent': base_improvement,
            'adjusted_improvement_percent': adjusted_improvement,
            'final_improvement_percent': final_improvement,
            'form_factor': form_factor,
            'consistency_factor': consistency_factor,
            'athlete_level': athlete_level
        }
    
    def _simulate_training_adaptation(
        self, 
        weeks_to_race: int, 
        athlete_level: str, 
        race_distance_km: float
    ) -> Dict:
        """Simulate training adaptations over the available time period"""
        
        # Get race-specific adaptation needs
        distance_factors = self.race_distance_factors.get(race_distance_km, 
                                                         self.race_distance_factors[42.195])
        
        # Calculate adaptation for each energy system
        adaptations = {}
        
        for system, curve in self.adaptation_curves.items():
            # Find the closest time point in our curve
            available_weeks = min(weeks_to_race, max(curve.keys()))
            
            # Interpolate if needed
            if available_weeks in curve:
                base_adaptation = curve[available_weeks]
            else:
                # Linear interpolation between curve points
                lower_week = max(w for w in curve.keys() if w <= available_weeks)
                upper_week = min(w for w in curve.keys() if w >= available_weeks)
                
                if lower_week == upper_week:
                    base_adaptation = curve[lower_week]
                else:
                    weight = (available_weeks - lower_week) / (upper_week - lower_week)
                    base_adaptation = curve[lower_week] + weight * (curve[upper_week] - curve[lower_week])
            
            # Weight by race distance requirements and athlete level
            level_multiplier = {'beginner': 1.2, 'intermediate': 1.0, 'advanced': 0.8}[athlete_level]
            race_weight = distance_factors.get(system.split('_')[0], 0.33)
            
            adaptations[system] = base_adaptation * level_multiplier * race_weight
        
        return {
            'aerobic_adaptation': adaptations.get('aerobic_base', 0),
            'lactate_adaptation': adaptations.get('lactate_threshold', 0),
            'vo2_adaptation': adaptations.get('vo2_max', 0),
            'total_fitness_gain': sum(adaptations.values()),
            'weeks_analyzed': weeks_to_race
        }
    
    def _calculate_periodized_race_time(
        self, 
        baseline: Dict, 
        improvement: Dict, 
        adaptation: Dict, 
        race_distance_km: float
    ) -> Dict:
        """Calculate final race time prediction incorporating all factors"""
        
        # Start with threshold pace as base
        base_threshold_pace = baseline['threshold_pace_per_km']
        
        # Apply improvement from training
        improvement_factor = 1 - improvement['final_improvement_percent']
        improved_threshold = base_threshold_pace * improvement_factor
        
        # Apply training adaptations
        adaptation_factor = 1 - (adaptation['total_fitness_gain'] * 0.5)  # Conservative application
        final_threshold = improved_threshold * adaptation_factor
        
        # Convert threshold pace to race pace based on distance
        if race_distance_km <= 5:
            race_pace = final_threshold * 0.95  # 5% faster than threshold for 5K
        elif race_distance_km <= 10:
            race_pace = final_threshold * 0.98  # 2% faster than threshold for 10K
        elif race_distance_km <= 21.1:
            race_pace = final_threshold * 1.05  # 5% slower than threshold for half
        else:  # Marathon
            race_pace = final_threshold * 1.15  # 15% slower than threshold for marathon
        
        race_time_seconds = race_pace * 60 * race_distance_km
        
        # Calculate confidence based on data quality and time available
        confidence = min(
            baseline['total_activities'] / 20,  # More activities = higher confidence
            improvement['consistency_factor'],   # Consistent training = higher confidence
            1.0
        ) * 0.85  # Cap at 85% confidence
        
        return {
            'race_time': race_time_seconds,
            'pace_per_km': race_pace,
            'threshold_pace_improved': final_threshold,
            'confidence': confidence
        }
    
    def _generate_training_milestones(
        self, 
        baseline: Dict, 
        race_prediction: Dict, 
        weeks_to_race: int
    ) -> List[Dict]:
        """Generate progressive training milestones"""
        
        milestones = []
        current_pace = baseline['threshold_pace_per_km']
        target_pace = race_prediction['threshold_pace_improved']
        
        # Create milestones every 2-4 weeks
        milestone_intervals = [4, 8, 12, 16, 20]
        applicable_intervals = [w for w in milestone_intervals if w <= weeks_to_race]
        
        for week in applicable_intervals:
            progress_ratio = week / weeks_to_race
            milestone_pace = current_pace - (current_pace - target_pace) * progress_ratio
            
            milestones.append({
                'week': week,
                'target_threshold_pace': milestone_pace,
                'expected_improvement': f"{((current_pace - milestone_pace) / current_pace * 100):.1f}%",
                'fitness_benchmark': f"Sustain {milestone_pace:.2f} min/km for 20-30 minutes"
            })
        
        return milestones
    
    def _generate_fallback_prediction(self, race_distance_km: float, weeks_to_race: int) -> Dict:
        """Generate basic prediction when insufficient data"""
        
        # Very basic estimates for new runners
        base_paces = {5.0: 6.5, 10.0: 7.0, 21.0975: 7.5, 42.195: 8.0}
        base_pace = base_paces.get(race_distance_km, 7.5)
        
        # Apply modest improvement for training time
        improvement = min(weeks_to_race * 0.01, 0.2)  # 1% per week, max 20%
        predicted_pace = base_pace * (1 - improvement)
        
        return {
            'race_distance_km': race_distance_km,
            'weeks_to_race': weeks_to_race,
            'predicted_race_time_seconds': predicted_pace * 60 * race_distance_km,
            'predicted_race_pace_per_km': predicted_pace,
            'confidence_score': 0.3,
            'methodology': 'fallback_estimate',
            'note': 'Prediction based on limited data - more training history needed for accuracy'
        }

# Global instance
periodized_predictor = PeriodizedRacePredictor()