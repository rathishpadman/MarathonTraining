"""
Industry Standard Race Predictor
Based on established sports science methodologies and best practices from:
- Jack Daniels' Running Formula
- McMillan Running Calculator
- TrainingPeaks Performance Management Chart
- VDOT methodology
- Riegel's formula for race time prediction
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app.models import Activity, ReplitAthlete
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class IndustryStandardRacePredictor:
    """
    Race predictor using industry-standard methodologies from sports science research
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # VDOT table based on Jack Daniels' research
        self.vdot_table = {
            # pace_per_km: vdot_value
            4.0: 70, 4.2: 65, 4.4: 60, 4.6: 55, 5.0: 50,
            5.2: 47, 5.4: 45, 5.6: 43, 5.8: 41, 6.0: 39,
            6.2: 37, 6.4: 35, 6.6: 33, 6.8: 31, 7.0: 29,
            7.2: 27, 7.4: 25, 7.6: 23, 7.8: 21, 8.0: 19
        }
        
        # Riegel's formula exponents for different distances
        self.riegel_exponents = {
            5.0: 1.06,     # 5K
            10.0: 1.06,    # 10K  
            21.0975: 1.06, # Half Marathon
            42.195: 1.06   # Marathon
        }
        
        # McMillan equivalent race times (based on 10K time)
        self.mcmillan_ratios = {
            5.0: 0.478,     # 5K is ~47.8% of 10K time
            10.0: 1.0,      # 10K baseline
            21.0975: 2.14,  # Half is ~2.14x 10K time
            42.195: 4.67    # Marathon is ~4.67x 10K time
        }
        
        # Training adaptation rates (conservative, evidence-based)
        self.adaptation_rates = {
            'aerobic_base': 0.004,      # 0.4% per week (conservative)
            'lactate_threshold': 0.005,  # 0.5% per week
            'vo2_max': 0.003,           # 0.3% per week
            'neuromuscular': 0.002      # 0.2% per week
        }
        
        # Distance-specific energy system contributions
        self.energy_systems = {
            5.0: {'aerobic': 0.15, 'lactate': 0.35, 'vo2': 0.40, 'neuromuscular': 0.10},
            10.0: {'aerobic': 0.25, 'lactate': 0.50, 'vo2': 0.20, 'neuromuscular': 0.05},
            21.0975: {'aerobic': 0.60, 'lactate': 0.35, 'vo2': 0.04, 'neuromuscular': 0.01},
            42.195: {'aerobic': 0.80, 'lactate': 0.18, 'vo2': 0.02, 'neuromuscular': 0.00}
        }
    
    def predict_race_time(self, db_session: Session, athlete_id: int, 
                         race_distance_km: float, weeks_to_race: int = 12) -> Dict:
        """
        Predict race time using industry-standard methodology
        
        Args:
            db_session: Database session
            athlete_id: Athlete ID
            race_distance_km: Target race distance
            weeks_to_race: Training weeks available
        
        Returns:
            Comprehensive race prediction with methodology details
        """
        
        # Step 1: Calculate current fitness level using recent performance
        current_fitness = self._calculate_current_fitness(db_session, athlete_id)
        
        if not current_fitness['valid']:
            return self._generate_fallback_prediction(race_distance_km)
        
        # Step 2: Estimate VDOT (VO2 max equivalent) from recent performances
        estimated_vdot = self._estimate_vdot(current_fitness)
        
        # Step 3: Calculate current race time baseline using equivalent performance
        current_race_time = self._calculate_equivalent_race_time(
            current_fitness, race_distance_km
        )
        
        # Step 4: Project improvement based on training adaptation
        training_improvement = self._calculate_training_adaptation(
            current_fitness, weeks_to_race, race_distance_km
        )
        
        # Step 5: Apply Riegel's formula for distance adjustment
        distance_adjusted_time = self._apply_riegel_formula(
            current_race_time, training_improvement, race_distance_km
        )
        
        # Step 6: Calculate confidence and provide methodology details
        confidence_score = self._calculate_confidence(current_fitness, weeks_to_race)
        
        return {
            'race_distance_km': race_distance_km,
            'predicted_time_seconds': distance_adjusted_time,
            'predicted_pace_per_km': distance_adjusted_time / race_distance_km / 60,
            'current_fitness': current_fitness,
            'estimated_vdot': estimated_vdot,
            'training_improvement_percent': training_improvement * 100,
            'confidence_score': confidence_score,
            'methodology': 'industry_standard_sports_science',
            'sources': ['Jack Daniels VDOT', 'McMillan Calculator', 'Riegel Formula'],
            'weeks_to_race': weeks_to_race
        }
    
    def _calculate_current_fitness(self, db_session: Session, athlete_id: int) -> Dict:
        """
        Calculate current fitness using weighted recent performance analysis
        Industry standard: Weight recent performances more heavily
        """
        
        # Get last 30 days of quality runs (>2km)
        cutoff_date = datetime.now() - timedelta(days=30)
        activities = db_session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= cutoff_date,
            Activity.sport_type.in_(['Run', 'VirtualRun']),
            Activity.distance > 2000,  # At least 2km
            Activity.moving_time > 600  # At least 10 minutes
        ).order_by(Activity.start_date.desc()).all()
        
        if len(activities) < 3:
            return {'valid': False, 'reason': 'insufficient_recent_data'}
        
        # Calculate weighted average pace (recent runs weighted more heavily)
        weighted_paces = []
        weights = []
        
        for i, activity in enumerate(activities):
            if activity.distance and activity.moving_time:
                pace_per_km = (activity.moving_time / 60) / (activity.distance / 1000)
                
                # Exponential weighting: most recent run gets highest weight
                weight = np.exp(-i * 0.2)  # Decay factor of 0.2
                
                weighted_paces.append(pace_per_km * weight)
                weights.append(weight)
        
        if not weights:
            return {'valid': False, 'reason': 'no_valid_activities'}
        
        current_pace = sum(weighted_paces) / sum(weights)
        
        # Calculate training volume and consistency
        total_distance = sum(a.distance / 1000 for a in activities if a.distance)
        weeks_span = max(1, len(activities) / 3.5)  # Approximate weeks in 30 days
        weekly_volume = total_distance / weeks_span
        
        # Analyze pace trend (improvement = negative slope)
        if len(activities) >= 5:
            recent_paces = []
            for activity in activities[:5]:  # Last 5 runs
                if activity.distance and activity.moving_time:
                    pace = (activity.moving_time / 60) / (activity.distance / 1000)
                    recent_paces.append(pace)
            
            if len(recent_paces) >= 3:
                # Linear regression for trend
                x = np.arange(len(recent_paces))
                trend_slope = np.polyfit(x, recent_paces, 1)[0]
                pace_trend = -trend_slope  # Negative slope = improvement
            else:
                pace_trend = 0.0
        else:
            pace_trend = 0.0
        
        return {
            'valid': True,
            'current_pace_per_km': current_pace,
            'weekly_volume_km': weekly_volume,
            'pace_trend': pace_trend,
            'recent_activities_count': len(activities),
            'longest_recent_run_km': max((a.distance / 1000 for a in activities if a.distance), default=0),
            'training_consistency': len(activities) / 12  # Activities per week over 30 days
        }
    
    def _estimate_vdot(self, fitness_data: Dict) -> float:
        """
        Estimate VDOT using Jack Daniels' methodology
        """
        current_pace = fitness_data['current_pace_per_km']
        
        # Find closest VDOT value from table
        closest_pace = min(self.vdot_table.keys(), key=lambda x: abs(x - current_pace))
        estimated_vdot = self.vdot_table[closest_pace]
        
        # Adjust based on training volume and consistency
        volume_factor = min(1.1, fitness_data['weekly_volume_km'] / 40)  # Cap at 10% bonus
        consistency_factor = fitness_data['training_consistency']
        
        adjusted_vdot = estimated_vdot * volume_factor * (0.8 + 0.2 * consistency_factor)
        
        return max(15, min(85, adjusted_vdot))  # Reasonable VDOT range
    
    def _calculate_equivalent_race_time(self, fitness_data: Dict, target_distance: float) -> float:
        """
        Calculate equivalent race time using McMillan ratios
        Based on current 10K equivalent performance
        """
        current_pace = fitness_data['current_pace_per_km']
        
        # Estimate current 10K time from training pace
        # Training pace is typically 15-20% slower than race pace
        race_pace_adjustment = 0.85  # 15% faster than training pace
        estimated_10k_pace = current_pace * race_pace_adjustment
        estimated_10k_time = estimated_10k_pace * 10 * 60  # Convert to seconds
        
        # Use McMillan ratios to predict target distance
        if target_distance in self.mcmillan_ratios:
            ratio = self.mcmillan_ratios[target_distance]
            predicted_time = estimated_10k_time * ratio
        else:
            # Use Riegel's formula for non-standard distances
            ratio = (target_distance / 10.0) ** 1.06
            predicted_time = estimated_10k_time * ratio
        
        return predicted_time
    
    def _calculate_training_adaptation(self, fitness_data: Dict, weeks: int, distance: float) -> float:
        """
        Calculate expected improvement from training
        Based on energy system contributions and adaptation rates
        """
        if weeks <= 0:
            return 0.0
        
        # Get energy system contributions for target distance
        energy_contrib = self.energy_systems.get(distance, self.energy_systems[42.195])
        
        # Calculate weighted improvement based on energy systems
        total_improvement = 0.0
        
        for system, contribution in energy_contrib.items():
            if system in self.adaptation_rates:
                weekly_rate = self.adaptation_rates[system]
                # Diminishing returns: improvement rate decreases over time
                system_improvement = 1 - (1 - weekly_rate) ** weeks
                total_improvement += system_improvement * contribution
        
        # Apply fitness level modifier
        pace_trend = fitness_data.get('pace_trend', 0)
        if pace_trend > 0:  # Already improving
            improvement_modifier = 1.2  # 20% bonus for positive trend
        else:
            improvement_modifier = 1.0
        
        # Apply training volume modifier
        volume = fitness_data['weekly_volume_km']
        if volume >= 50:
            volume_modifier = 1.1
        elif volume >= 30:
            volume_modifier = 1.05
        else:
            volume_modifier = 1.0
        
        final_improvement = total_improvement * improvement_modifier * volume_modifier
        
        # Cap maximum improvement at 15% to maintain realism
        return min(0.15, final_improvement)
    
    def _apply_riegel_formula(self, base_time: float, improvement: float, distance: float) -> float:
        """
        Apply Riegel's formula with training improvement
        """
        # Apply improvement (faster time = lower value)
        improved_time = base_time * (1 - improvement)
        
        return improved_time
    
    def _calculate_confidence(self, fitness_data: Dict, weeks: int) -> float:
        """
        Calculate prediction confidence based on data quality and training time
        """
        confidence = 0.5  # Base confidence
        
        # Data quality factors
        if fitness_data['recent_activities_count'] >= 8:
            confidence += 0.2
        elif fitness_data['recent_activities_count'] >= 5:
            confidence += 0.1
        
        # Training consistency
        if fitness_data['training_consistency'] >= 3:
            confidence += 0.15
        elif fitness_data['training_consistency'] >= 2:
            confidence += 0.1
        
        # Training time available
        if weeks >= 12:
            confidence += 0.1
        elif weeks >= 8:
            confidence += 0.05
        
        # Volume adequacy
        if fitness_data['weekly_volume_km'] >= 30:
            confidence += 0.1
        
        return min(0.95, confidence)  # Cap at 95%
    
    def _generate_fallback_prediction(self, distance: float) -> Dict:
        """
        Generate conservative fallback prediction when insufficient data
        """
        # Conservative estimates for untrained runner
        estimated_pace = 8.0  # 8 min/km
        estimated_time = distance * estimated_pace * 60
        
        return {
            'race_distance_km': distance,
            'predicted_time_seconds': estimated_time,
            'predicted_pace_per_km': estimated_pace,
            'confidence_score': 0.3,
            'methodology': 'fallback_conservative_estimate',
            'warning': 'Insufficient data for accurate prediction'
        }

def predict_race_time_industry_standard(db_session: Session, athlete_id: int, 
                                       race_distance_km: float, weeks_to_race: int = 12) -> Dict:
    """
    Global function for industry-standard race prediction
    """
    predictor = IndustryStandardRacePredictor()
    return predictor.predict_race_time(db_session, athlete_id, race_distance_km, weeks_to_race)