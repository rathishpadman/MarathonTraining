"""
Simplified Race Performance Predictor using authentic Strava data
Implements proven algorithms for race time prediction based on training history
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.models import Activity, ReplitAthlete
from sqlalchemy.orm import Session

class SimpleRacePredictor:
    """
    Simplified race predictor using Jack Daniels VDOT and McMillan equivalent methods
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Race distances in kilometers
        self.race_distances = {
            '5K': 5.0,
            '10K': 10.0,
            'Half Marathon': 21.0975,
            'Marathon': 42.195
        }
    
    def predict_race_time(self, db_session: Session, athlete_id: int, race_distance: str) -> Dict:
        """
        Predict race time using authentic training data
        """
        self.logger.info(f"Predicting {race_distance} for athlete {athlete_id}")
        
        if race_distance not in self.race_distances:
            raise ValueError(f"Unsupported race distance: {race_distance}")
        
        distance_km = self.race_distances[race_distance]
        
        # Get recent running activities (last 90 days)
        cutoff_date = datetime.now() - timedelta(days=90)
        activities = db_session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= cutoff_date,
            Activity.sport_type.in_(['Run', 'VirtualRun']),
            Activity.distance > 1000  # At least 1km
        ).order_by(Activity.start_date.desc()).all()
        
        if not activities:
            raise ValueError("No recent running activities found")
        
        # Calculate fitness metrics
        fitness_score = self._calculate_fitness_score(activities)
        vo2_max = self._estimate_vo2_max(activities)
        
        # Predict race time using multiple methods
        predictions = []
        
        # Method 1: Best recent pace extrapolation
        pace_prediction = self._predict_from_pace_analysis(activities, distance_km)
        if pace_prediction:
            predictions.append(pace_prediction)
        
        # Method 2: VDOT equivalent
        vdot_prediction = self._predict_from_vdot(vo2_max, distance_km)
        if vdot_prediction:
            predictions.append(vdot_prediction)
        
        # Method 3: Training volume based
        volume_prediction = self._predict_from_volume(activities, distance_km)
        if volume_prediction:
            predictions.append(volume_prediction)
        
        if not predictions:
            # Fallback prediction based on average pace from all activities
            all_paces = []
            for activity in activities:
                if activity.distance and activity.moving_time and activity.distance > 1000:
                    activity_km = activity.distance / 1000
                    pace = activity.moving_time / activity_km
                    if 200 < pace < 800:
                        all_paces.append(pace)
            
            if all_paces:
                avg_pace = sum(all_paces) / len(all_paces)
                # Conservative pace adjustment for race distance
                if distance_km <= 5:
                    race_pace = avg_pace * 0.98
                elif distance_km <= 10:
                    race_pace = avg_pace * 1.02
                elif distance_km <= 21.1:
                    race_pace = avg_pace * 1.08
                else:  # Marathon
                    race_pace = avg_pace * 1.15
                
                final_prediction = race_pace * distance_km
                confidence = 0.6  # Lower confidence for fallback
            else:
                # Ultimate fallback based on race distance
                fallback_paces = {'5K': 300, '10K': 315, 'Half Marathon': 330, 'Marathon': 345}  # seconds per km
                race_pace = fallback_paces.get(race_distance, 330)
                final_prediction = race_pace * distance_km
                confidence = 0.4  # Very low confidence
        else:
            # Use median of predictions for stability
            final_prediction = sorted(predictions)[len(predictions) // 2]
            # Calculate confidence based on data quality
            confidence = self._calculate_confidence(activities, predictions)
        
        # Generate training recommendations
        recommendations = self._generate_recommendations(activities, race_distance, fitness_score)
        
        # Generate pacing strategy
        pacing_strategy = self._generate_pacing_strategy(final_prediction, distance_km)
        
        return {
            'race_distance': race_distance,
            'predicted_time_seconds': final_prediction,
            'predicted_time_formatted': self._format_time(final_prediction),
            'confidence_score': round(confidence * 100, 1),
            'fitness_score': round(fitness_score, 1),
            'aerobic_capacity': round(vo2_max, 1),
            'pacing_strategy': pacing_strategy,
            'training_recommendations': recommendations
        }
    
    def analyze_fitness(self, db_session: Session, athlete_id: int, days: int = 90) -> Dict:
        """
        Analyze current fitness level using authentic training data
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        activities = db_session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= cutoff_date,
            Activity.sport_type.in_(['Run', 'VirtualRun'])
        ).all()
        
        if not activities:
            return self._empty_fitness_analysis()
        
        # Calculate metrics
        total_distance = sum(a.distance or 0 for a in activities) / 1000  # km
        total_time = sum(a.moving_time or 0 for a in activities) / 3600  # hours
        avg_pace = self._calculate_average_pace(activities)
        
        fitness_score = self._calculate_fitness_score(activities)
        vo2_max = self._estimate_vo2_max(activities)
        consistency = self._calculate_consistency(activities)
        
        # Get actual injury risk from injury predictor for consistency
        from app.injury_predictor import predict_injury_risk
        injury_assessment = predict_injury_risk(athlete_id)
        actual_injury_risk = injury_assessment.get('risk_percentage', 0)
        
        # Calculate heart rate based metrics if available
        hr_activities = [a for a in activities if a.average_heartrate and a.average_heartrate > 0]
        avg_hr = sum(a.average_heartrate for a in hr_activities) / len(hr_activities) if hr_activities else 0
        
        # Calculate actual Training Stress Score (TSS) based on real activity data
        actual_tss = self._calculate_training_stress_score(activities)
        
        # Calculate realistic SpO2 - only show if no actual data available
        # Note: SpO2 should be measured, not calculated from running data
        spo2_estimate = None  # Don't estimate without proper measurement
        
        return {
            'fitness_metrics': {
                'current_fitness': {
                    'value': round(fitness_score, 1),
                    'tooltip': 'Overall fitness score (0-100) based on training volume, frequency, and intensity over the last 4 weeks'
                },
                'aerobic_capacity': {
                    'value': round(vo2_max, 1),
                    'tooltip': 'Estimated VO2 Max (ml/kg/min) calculated from best recent pace performances across different distances'
                },
                'lactate_threshold_pace': {
                    'value': self._format_pace(avg_pace * 1.05),
                    'tooltip': 'Estimated lactate threshold pace - the fastest pace you can sustain for 60+ minutes'
                },
                'training_load': {
                    'value': round(actual_tss, 1),
                    'tooltip': 'Training Stress Score (TSS) calculated from activity duration, intensity, and athlete threshold pace'
                },
                'consistency_score': {
                    'value': round(consistency, 1),
                    'tooltip': 'Training consistency (0-100%) based on regular activity frequency and weekly volume stability'
                },
                'injury_risk': {
                    'value': round(actual_injury_risk, 1),
                    'tooltip': 'Injury risk percentage based on training load progression, recovery patterns, and biomechanical indicators'
                },
                'weekly_distance': {
                    'value': round(total_distance / (days / 7), 1),
                    'tooltip': 'Average weekly running distance (km) calculated from total distance over analysis period'
                },
                'heart_rate_zones': {
                    'value': round(avg_hr, 0) if avg_hr > 0 else 'N/A',
                    'tooltip': 'Average heart rate (bpm) across all recorded activities - indicates cardiovascular fitness level'
                }
            },
            'summary': {
                'total_activities': len(activities),
                'total_distance_km': round(total_distance, 1),
                'analysis_period_days': days
            }
        }
    
    def _calculate_fitness_score(self, activities: List[Activity]) -> float:
        """Calculate fitness score (0-100) based on recent training"""
        if not activities:
            return 0.0
        
        # Recent 4 weeks
        recent_cutoff = datetime.now() - timedelta(days=28)
        recent_activities = [a for a in activities if a.start_date >= recent_cutoff]
        
        if not recent_activities:
            return 0.0
        
        # Volume component (distance)
        total_distance = sum(a.distance or 0 for a in recent_activities) / 1000  # km
        volume_score = min(100, total_distance * 2)  # 50km = 100 points
        
        # Frequency component
        frequency_score = min(100, len(recent_activities) * 8)  # 12+ activities = 100 points
        
        # Intensity component (based on pace variation)
        paces = []
        for activity in recent_activities:
            if activity.distance and activity.moving_time and activity.distance > 0:
                pace = activity.moving_time / (activity.distance / 1000)  # seconds per km
                if 200 < pace < 800:  # Reasonable pace range
                    paces.append(pace)
        
        intensity_score = 50  # Default
        if len(paces) >= 3:
            pace_range = max(paces) - min(paces)
            intensity_score = min(100, pace_range / 2)  # Variety in paces
        
        # Weighted average
        fitness_score = volume_score * 0.5 + frequency_score * 0.3 + intensity_score * 0.2
        return max(0, min(100, fitness_score))
    
    def _estimate_vo2_max(self, activities: List[Activity]) -> float:
        """Estimate VO2 max from best recent performances using Jack Daniels formula"""
        if not activities:
            return 40.0  # Conservative baseline
        
        # Find best running performance for VO2 max estimation
        best_vdot = 0
        
        for activity in activities:
            if not (activity.distance and activity.moving_time and activity.distance > 1000):
                continue
            
            distance_km = activity.distance / 1000
            pace_per_km = activity.moving_time / distance_km  # seconds per km
            
            # Only use reasonable paces (3:20 to 13:20 per km)
            if not (200 <= pace_per_km <= 800):
                continue
            
            # Convert to speed in m/min for Jack Daniels VDOT calculation
            speed_mmin = 60000 / pace_per_km  # meters per minute
            
            # Jack Daniels VDOT formula based on distance and time
            # VDOT = -4.6 + 0.182258 * speed + 0.000104 * speed^2
            if 3.0 <= distance_km <= 42.2:  # Valid racing distances
                percent_max = self._get_percent_max_for_distance(distance_km)
                if percent_max > 0:
                    vdot = (-4.6 + 0.182258 * speed_mmin + 0.000104 * speed_mmin * speed_mmin) / (percent_max / 100)
                    if vdot > best_vdot:
                        best_vdot = vdot
        
        # Return realistic VO2 max range (30-70 ml/kg/min)
        if best_vdot == 0:
            return 40.0
        
        return max(30.0, min(70.0, best_vdot))
    
    def _get_percent_max_for_distance(self, distance_km: float) -> float:
        """Get percentage of VO2 max typically used for different distances"""
        if distance_km <= 1.5:  # 1500m
            return 100.0
        elif distance_km <= 3.2:  # 3K
            return 97.0
        elif distance_km <= 5.0:  # 5K
            return 95.0
        elif distance_km <= 10.0:  # 10K
            return 90.0
        elif distance_km <= 15.0:  # 15K
            return 85.0
        elif distance_km <= 21.1:  # Half marathon
            return 80.0
        elif distance_km <= 30.0:  # 30K
            return 75.0
        elif distance_km <= 42.2:  # Marathon
            return 70.0
        else:
            return 65.0
    
    def _calculate_average_pace(self, activities: List[Activity]) -> float:
        """Calculate average pace in seconds per km"""
        valid_paces = []
        
        for activity in activities:
            if activity.distance and activity.moving_time and activity.distance > 1000:
                pace = activity.moving_time / (activity.distance / 1000)
                if 200 < pace < 800:  # Reasonable pace range
                    valid_paces.append(pace)
        
        return sum(valid_paces) / len(valid_paces) if valid_paces else 360.0
    
    def _calculate_consistency(self, activities: List[Activity]) -> float:
        """Calculate training consistency (0-100)"""
        if not activities:
            return 0.0
        
        # Group activities by week
        weekly_counts = {}
        for activity in activities:
            week_key = activity.start_date.isocalendar()[:2]  # (year, week)
            weekly_counts[week_key] = weekly_counts.get(week_key, 0) + 1
        
        if len(weekly_counts) < 2:
            return 50.0
        
        weekly_values = list(weekly_counts.values())
        mean_weekly = sum(weekly_values) / len(weekly_values)
        
        # Calculate coefficient of variation
        if mean_weekly == 0:
            return 0.0
        
        variance = sum((x - mean_weekly) ** 2 for x in weekly_values) / len(weekly_values)
        std_dev = variance ** 0.5
        cv = std_dev / mean_weekly
        
        # Convert to consistency score (lower CV = higher consistency)
        consistency = max(0, 100 - cv * 50)
        return min(100, consistency)
    
    def _calculate_training_stress_score(self, activities: List[Activity]) -> float:
        """Calculate Training Stress Score (TSS) from actual activity data"""
        total_tss = 0.0
        
        # Calculate athlete's threshold pace for intensity factor calculation
        threshold_pace = self._calculate_average_pace(activities) * 1.05  # Conservative LT pace
        
        for activity in activities:
            if not (activity.distance and activity.moving_time and activity.distance > 1000):
                continue
            
            distance_km = activity.distance / 1000
            pace_per_km = activity.moving_time / distance_km
            
            # Skip unrealistic paces
            if not (200 <= pace_per_km <= 800):
                continue
            
            # Calculate Intensity Factor (IF) - ratio of pace to threshold pace
            # Note: Faster pace = lower seconds/km, so invert the ratio
            intensity_factor = min(threshold_pace / pace_per_km, 1.2)  # Cap at 1.2
            
            # Calculate Normalized Power equivalent for running
            # TSS = (Training Time in hours × IF² × 100)
            duration_hours = activity.moving_time / 3600
            activity_tss = duration_hours * (intensity_factor ** 2) * 100
            
            total_tss += activity_tss
        
        return total_tss
    
    def _predict_from_pace_analysis(self, activities: List[Activity], distance_km: float) -> Optional[float]:
        """Predict race time based on recent pace analysis"""
        # Get recent good performances
        recent_cutoff = datetime.now() - timedelta(days=60)
        recent_activities = [a for a in activities if a.start_date >= recent_cutoff]
        
        if not recent_activities:
            return None
        
        # Find activities similar to race distance
        similar_activities = []
        for activity in recent_activities:
            if not (activity.distance and activity.moving_time):
                continue
            
            activity_km = activity.distance / 1000
            if activity_km >= distance_km * 0.3:  # At least 30% of race distance
                pace = activity.moving_time / activity_km
                if 200 < pace < 800:
                    similar_activities.append((activity_km, pace))
        
        if not similar_activities:
            return None
        
        # Use best recent pace and adjust for race distance
        best_pace = min(pace for _, pace in similar_activities)
        
        # Distance-based pace adjustment
        if distance_km <= 5:
            race_pace = best_pace * 0.98  # Slightly faster for short races
        elif distance_km <= 10:
            race_pace = best_pace * 1.01
        elif distance_km <= 21.1:
            race_pace = best_pace * 1.05
        else:  # Marathon
            race_pace = best_pace * 1.12
        
        return race_pace * distance_km
    
    def _predict_from_vdot(self, vo2_max: float, distance_km: float) -> Optional[float]:
        """Predict using VDOT equivalent method"""
        if vo2_max < 35:
            return None
        
        # Jack Daniels VDOT race time predictions (simplified)
        if distance_km <= 5:
            pace_factor = 0.90
        elif distance_km <= 10:
            pace_factor = 0.92
        elif distance_km <= 21.1:
            pace_factor = 0.95
        else:  # Marathon
            pace_factor = 1.00
        
        # Convert VO2 max to predicted pace
        base_pace = 600 - (vo2_max - 35) * 6  # Simplified relationship
        race_pace = base_pace * pace_factor
        
        return race_pace * distance_km
    
    def _predict_from_volume(self, activities: List[Activity], distance_km: float) -> Optional[float]:
        """Predict based on training volume and fitness"""
        recent_cutoff = datetime.now() - timedelta(days=60)
        recent_activities = [a for a in activities if a.start_date >= recent_cutoff]
        
        if not recent_activities:
            return None
        
        # Calculate recent weekly volume
        total_distance = sum(a.distance or 0 for a in recent_activities) / 1000
        weeks = (datetime.now() - recent_cutoff).days / 7
        weekly_volume = total_distance / weeks if weeks > 0 else 0
        
        # Volume-based pace estimation
        if weekly_volume >= 50:
            base_pace = 300  # 5:00/km for high volume
        elif weekly_volume >= 30:
            base_pace = 330  # 5:30/km for moderate volume
        elif weekly_volume >= 15:
            base_pace = 360  # 6:00/km for low volume
        else:
            base_pace = 420  # 7:00/km for very low volume
        
        # Adjust for race distance
        if distance_km <= 5:
            race_pace = base_pace * 0.95
        elif distance_km <= 10:
            race_pace = base_pace * 0.98
        elif distance_km <= 21.1:
            race_pace = base_pace * 1.05
        else:  # Marathon
            race_pace = base_pace * 1.15
        
        return race_pace * distance_km
    
    def _calculate_confidence(self, activities: List[Activity], predictions: List[float]) -> float:
        """Calculate prediction confidence (0-1)"""
        # Base confidence on data quality
        data_quality = min(1.0, len(activities) / 20)  # Full confidence at 20+ activities
        
        # Confidence from prediction agreement
        if len(predictions) > 1:
            avg_prediction = sum(predictions) / len(predictions)
            max_deviation = max(abs(p - avg_prediction) / avg_prediction for p in predictions)
            agreement = max(0.0, 1.0 - max_deviation)
        else:
            agreement = 0.7  # Moderate confidence for single prediction
        
        return (data_quality * 0.6 + agreement * 0.4)
    
    def _generate_recommendations(self, activities: List[Activity], race_distance: str, fitness_score: float) -> List[str]:
        """Generate training recommendations"""
        recommendations = []
        
        recent_count = len([a for a in activities if a.start_date >= datetime.now() - timedelta(days=30)])
        
        if fitness_score < 30:
            recommendations.append("Build aerobic base with easy-paced runs")
            recommendations.append("Gradually increase weekly mileage (10% rule)")
        elif fitness_score < 60:
            recommendations.append("Add one tempo run per week")
            recommendations.append("Include weekly long runs")
        else:
            recommendations.append("Incorporate interval training")
            recommendations.append("Practice race pace segments")
        
        if recent_count < 12:
            recommendations.append("Increase training frequency to 4-5 runs per week")
        
        if race_distance == 'Marathon':
            recommendations.append("Build long runs up to 32-35km")
            recommendations.append("Practice marathon pace in long runs")
        elif race_distance == 'Half Marathon':
            recommendations.append("Include 15-20km runs at moderate effort")
            recommendations.append("Practice half marathon pace segments")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _generate_pacing_strategy(self, predicted_time: float, distance_km: float) -> Dict[str, float]:
        """Generate kilometer pacing strategy"""
        target_pace = predicted_time / distance_km
        strategy = {}
        
        for km in range(1, int(distance_km) + 1):
            if distance_km <= 10:
                # Even pacing for shorter races
                strategy[f'km_{km}'] = target_pace
            else:
                # Conservative start for longer races
                if km <= 3:
                    strategy[f'km_{km}'] = target_pace * 1.03
                elif km <= distance_km * 0.8:
                    strategy[f'km_{km}'] = target_pace
                else:
                    strategy[f'km_{km}'] = target_pace * 0.98
        
        return strategy
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _format_pace(self, pace_seconds: float) -> str:
        """Format pace to MM:SS format"""
        minutes = int(pace_seconds // 60)
        seconds = int(pace_seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    def _empty_fitness_analysis(self) -> Dict:
        """Return empty fitness analysis structure"""
        return {
            'fitness_metrics': {
                'current_fitness': 0.0,
                'aerobic_capacity': 35.0,
                'lactate_threshold_pace': '6:00',
                'training_load': 0.0,
                'consistency_score': 0.0,
                'injury_risk': 0.0,
                'fatigue_level': 0.0
            },
            'summary': {
                'total_activities': 0,
                'total_distance_km': 0.0,
                'analysis_period_days': 90
            }
        }