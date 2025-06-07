"""
Race Performance Optimization Algorithms for Marathon Training Dashboard

This module implements advanced algorithms to analyze training data and optimize
race performance predictions based on authentic Strava activity data.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from app.models import Activity, ReplitAthlete, DailySummary
from sqlalchemy.orm import Session

@dataclass
class RacePrediction:
    """Race performance prediction result"""
    distance: float  # Race distance in km
    predicted_time: float  # Predicted time in seconds
    confidence_score: float  # Confidence level (0-1)
    pacing_strategy: Dict[str, float]  # Kilometer splits
    training_recommendations: List[str]
    fitness_score: float
    aerobic_capacity: float

@dataclass
class TrainingZone:
    """Training zone definition"""
    name: str
    min_pace: float  # seconds per km
    max_pace: float  # seconds per km
    percentage_range: Tuple[float, float]  # HR percentage range
    description: str

class RacePerformanceOptimizer:
    """
    Advanced race performance optimization using machine learning algorithms
    and physiological modeling based on authentic Strava training data.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Training zones based on scientific research
        self.training_zones = {
            'recovery': TrainingZone('Recovery', 420, 480, (50, 60), 'Active recovery and easy runs'),
            'aerobic_base': TrainingZone('Aerobic Base', 360, 420, (60, 70), 'Aerobic base building'),
            'tempo': TrainingZone('Tempo', 300, 360, (70, 80), 'Lactate threshold training'),
            'threshold': TrainingZone('Threshold', 270, 300, (80, 90), 'Anaerobic threshold'),
            'vo2_max': TrainingZone('VO2 Max', 240, 270, (90, 95), 'Maximum oxygen uptake'),
            'neuromuscular': TrainingZone('Neuromuscular', 180, 240, (95, 100), 'Speed and power')
        }
        
        # Race distance constants (in km)
        self.race_distances = {
            '5K': 5.0,
            '10K': 10.0,
            'Half Marathon': 21.0975,
            'Marathon': 42.195
        }
    
    def analyze_athlete_fitness(self, db_session: Session, athlete_id: int, days: int = 90) -> Dict:
        """
        Comprehensive fitness analysis using authentic training data
        """
        self.logger.info(f"Analyzing fitness for athlete {athlete_id} over {days} days")
        
        # Get recent activities
        cutoff_date = datetime.now() - timedelta(days=days)
        activities = db_session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= cutoff_date,
            Activity.sport_type.in_(['Run', 'VirtualRun'])
        ).order_by(Activity.start_date.desc()).all()
        
        if not activities:
            self.logger.warning(f"No running activities found for athlete {athlete_id}")
            return self._create_empty_analysis()
        
        # Convert to DataFrame for analysis
        df = self._activities_to_dataframe(activities)
        
        # Calculate key fitness metrics
        fitness_metrics = {
            'current_fitness': self._calculate_fitness_score(df),
            'aerobic_capacity': self._estimate_vo2_max(df),
            'lactate_threshold': self._estimate_lactate_threshold(df),
            'training_load': self._calculate_training_load(df),
            'consistency_score': self._calculate_consistency(df),
            'injury_risk': self._assess_injury_risk(df),
            'fatigue_level': self._calculate_fatigue(df)
        }
        
        # Training distribution analysis
        zone_distribution = self._analyze_training_zones(df)
        
        # Progress trends
        trends = self._analyze_trends(df)
        
        return {
            'fitness_metrics': fitness_metrics,
            'zone_distribution': zone_distribution,
            'trends': trends,
            'total_activities': len(activities),
            'total_distance': df['distance'].sum() / 1000,  # Convert to km
            'analysis_period': days
        }
    
    def predict_race_performance(self, db_session: Session, athlete_id: int, race_distance: str) -> RacePrediction:
        """
        Predict race performance using multiple algorithms and authentic training data
        """
        self.logger.info(f"Predicting {race_distance} performance for athlete {athlete_id}")
        
        # Validate race distance
        if race_distance not in self.race_distances:
            raise ValueError(f"Unsupported race distance: {race_distance}")
        
        distance_km = self.race_distances[race_distance]
        
        # Get fitness analysis
        fitness_analysis = self.analyze_athlete_fitness(db_session, athlete_id)
        
        # Get recent race-pace equivalent activities
        race_pace_activities = self._get_race_pace_activities(db_session, athlete_id, distance_km)
        
        # Apply multiple prediction models
        predictions = []
        
        # Model 1: Jack Daniels VDOT formula
        vdot_prediction = self._predict_via_vdot(fitness_analysis, distance_km)
        if vdot_prediction:
            predictions.append(vdot_prediction)
        
        # Model 2: McMillan Running Calculator equivalent
        mcmillan_prediction = self._predict_via_mcmillan(fitness_analysis, distance_km)
        if mcmillan_prediction:
            predictions.append(mcmillan_prediction)
        
        # Model 3: Training pace analysis
        pace_prediction = self._predict_via_pace_analysis(race_pace_activities, distance_km)
        if pace_prediction:
            predictions.append(pace_prediction)
        
        # Model 4: Physiological model
        physio_prediction = self._predict_via_physiological_model(fitness_analysis, distance_km)
        if physio_prediction:
            predictions.append(physio_prediction)
        
        if not predictions:
            raise ValueError("Insufficient data for race prediction")
        
        # Ensemble prediction with confidence weighting
        final_prediction = self._ensemble_predictions(predictions, fitness_analysis)
        
        # Generate pacing strategy
        pacing_strategy = self._generate_pacing_strategy(final_prediction, distance_km)
        
        # Generate training recommendations
        recommendations = self._generate_training_recommendations(fitness_analysis, race_distance)
        
        return RacePrediction(
            distance=distance_km,
            predicted_time=final_prediction,
            confidence_score=self._calculate_confidence(predictions, fitness_analysis),
            pacing_strategy=pacing_strategy,
            training_recommendations=recommendations,
            fitness_score=fitness_analysis['fitness_metrics']['current_fitness'],
            aerobic_capacity=fitness_analysis['fitness_metrics']['aerobic_capacity']
        )
    
    def optimize_training_plan(self, db_session: Session, athlete_id: int, 
                             race_distance: str, race_date: datetime) -> Dict:
        """
        Generate optimized training plan based on current fitness and race goals
        """
        self.logger.info(f"Optimizing training plan for athlete {athlete_id}")
        
        days_to_race = (race_date - datetime.now()).days
        
        if days_to_race < 7:
            return self._generate_taper_plan(db_session, athlete_id, days_to_race)
        elif days_to_race < 28:
            return self._generate_peak_plan(db_session, athlete_id, race_distance, days_to_race)
        else:
            return self._generate_build_plan(db_session, athlete_id, race_distance, days_to_race)
    
    def _activities_to_dataframe(self, activities: List[Activity]) -> pd.DataFrame:
        """Convert activities to pandas DataFrame for analysis"""
        data = []
        for activity in activities:
            # Calculate pace (seconds per km)
            pace = (activity.moving_time / (activity.distance / 1000)) if activity.distance > 0 else 0
            
            data.append({
                'date': activity.start_date,
                'distance': activity.distance,  # meters
                'moving_time': activity.moving_time,  # seconds
                'pace': pace,  # seconds per km
                'average_heartrate': activity.average_heartrate or 0,
                'elevation_gain': activity.total_elevation_gain or 0,
                'suffer_score': activity.suffer_score or 0
            })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        return df
    
    def _calculate_fitness_score(self, df: pd.DataFrame) -> float:
        """Calculate current fitness score (0-100)"""
        if df.empty:
            return 0.0
        
        # Recent 4 weeks weighted more heavily
        recent_df = df[df['date'] >= df['date'].max() - timedelta(days=28)]
        
        # Factors: volume, intensity, consistency
        volume_score = min(100, (recent_df['distance'].sum() / 1000) * 2)  # km * 2
        
        # Intensity based on pace distribution
        fast_runs = recent_df[recent_df['pace'] < recent_df['pace'].quantile(0.3)]
        intensity_score = min(100, len(fast_runs) * 10)
        
        # Consistency (activities per week)
        consistency_score = min(100, len(recent_df) * 5)
        
        # Weighted average
        fitness_score = (volume_score * 0.4 + intensity_score * 0.3 + consistency_score * 0.3)
        
        return max(0, min(100, fitness_score))
    
    def _estimate_vo2_max(self, df: pd.DataFrame) -> float:
        """Estimate VO2 max using pace and heart rate data"""
        if df.empty:
            return 35.0  # Default minimum
        
        # Use Jack Daniels formula with best recent performances
        recent_df = df[df['date'] >= df['date'].max() - timedelta(days=60)]
        
        # Find best pace for different distances
        best_performances = []
        
        # 5K equivalent (3-8km runs)
        medium_runs = recent_df[(recent_df['distance'] >= 3000) & (recent_df['distance'] <= 8000)]
        if not medium_runs.empty:
            best_5k_pace = medium_runs['pace'].min()
            vdot_5k = self._pace_to_vdot(best_5k_pace, 5.0)
            best_performances.append(vdot_5k)
        
        # 10K equivalent (8-15km runs)
        long_runs = recent_df[(recent_df['distance'] >= 8000) & (recent_df['distance'] <= 15000)]
        if not long_runs.empty:
            best_10k_pace = long_runs['pace'].min()
            vdot_10k = self._pace_to_vdot(best_10k_pace, 10.0)
            best_performances.append(vdot_10k)
        
        if best_performances:
            estimated_vo2_max = max(best_performances)
        else:
            # Fallback calculation based on average pace
            avg_pace = df['pace'].median()
            estimated_vo2_max = max(35.0, 60 - (avg_pace - 300) / 10)
        
        return min(80.0, max(35.0, estimated_vo2_max))
    
    def _pace_to_vdot(self, pace_seconds_per_km: float, distance_km: float) -> float:
        """Convert pace to VDOT using Jack Daniels formula approximation"""
        # Simplified VDOT calculation
        time_seconds = pace_seconds_per_km * distance_km
        time_minutes = time_seconds / 60
        
        # Jack Daniels VDOT approximation for common distances
        if distance_km <= 5:
            vdot = 15.3 * (1000 / time_seconds) ** 1.06
        elif distance_km <= 10:
            vdot = 15.3 * (600 / time_minutes) ** 1.06
        else:
            vdot = 15.3 * (482.5 / time_minutes) ** 1.06
        
        return max(30, min(85, vdot))
    
    def _estimate_lactate_threshold(self, df: pd.DataFrame) -> float:
        """Estimate lactate threshold pace"""
        if df.empty:
            return 360.0  # 6:00/km default
        
        # Tempo runs (20-60 minutes at comfortably hard effort)
        tempo_runs = df[
            (df['moving_time'] >= 1200) & 
            (df['moving_time'] <= 3600) &
            (df['distance'] >= 3000)
        ]
        
        if not tempo_runs.empty:
            # Average pace of fastest 20% of tempo runs
            threshold_pace = tempo_runs.nsmallest(max(1, len(tempo_runs) // 5), 'pace')['pace'].mean()
        else:
            # Estimate as 85% of 5K pace
            best_5k_pace = df[df['distance'] >= 3000]['pace'].min() if len(df[df['distance'] >= 3000]) > 0 else 300
            threshold_pace = best_5k_pace * 1.15
        
        return max(240, min(600, threshold_pace))
    
    def _calculate_training_load(self, df: pd.DataFrame) -> float:
        """Calculate training stress score"""
        if df.empty:
            return 0.0
        
        # Recent 7 days
        recent_df = df[df['date'] >= df['date'].max() - timedelta(days=7)]
        
        training_load = 0.0
        for _, row in recent_df.iterrows():
            # Base load from duration and distance
            duration_factor = row['moving_time'] / 3600  # hours
            intensity_factor = max(0.5, 400 / max(row['pace'], 200))  # pace-based intensity
            
            daily_load = duration_factor * intensity_factor * 100
            training_load += daily_load
        
        return min(1000, training_load)
    
    def _calculate_consistency(self, df: pd.DataFrame) -> float:
        """Calculate training consistency score (0-100)"""
        if df.empty:
            return 0.0
        
        # Last 8 weeks
        recent_df = df[df['date'] >= df['date'].max() - timedelta(days=56)]
        
        if len(recent_df) < 4:
            return 0.0
        
        # Group by week and count activities
        recent_df['week'] = recent_df['date'].dt.isocalendar().week
        weekly_counts = recent_df.groupby('week').size()
        
        # Consistency = how close weekly counts are to the mean
        if len(weekly_counts) < 2:
            return 50.0
        
        mean_weekly = weekly_counts.mean()
        std_weekly = weekly_counts.std()
        
        consistency = max(0, 100 - (std_weekly / max(mean_weekly, 1)) * 50)
        
        return min(100, consistency)
    
    def _assess_injury_risk(self, df: pd.DataFrame) -> float:
        """Assess injury risk based on training patterns (0-100, higher = more risk)"""
        if df.empty:
            return 0.0
        
        risk_factors = 0.0
        
        # Recent volume increase
        recent_df = df[df['date'] >= df['date'].max() - timedelta(days=14)]
        previous_df = df[
            (df['date'] >= df['date'].max() - timedelta(days=28)) &
            (df['date'] < df['date'].max() - timedelta(days=14))
        ]
        
        if not recent_df.empty and not previous_df.empty:
            recent_volume = recent_df['distance'].sum()
            previous_volume = previous_df['distance'].sum()
            
            if previous_volume > 0:
                volume_increase = (recent_volume - previous_volume) / previous_volume
                if volume_increase > 0.1:  # >10% increase
                    risk_factors += min(30, volume_increase * 100)
        
        # High intensity frequency
        if not recent_df.empty:
            fast_pace_threshold = recent_df['pace'].quantile(0.2)
            fast_runs = recent_df[recent_df['pace'] <= fast_pace_threshold]
            if len(fast_runs) > len(recent_df) * 0.4:  # >40% fast runs
                risk_factors += 20
        
        # Consecutive training days
        recent_df_sorted = recent_df.sort_values('date')
        consecutive_days = self._max_consecutive_days(recent_df_sorted['date'])
        if consecutive_days > 7:
            risk_factors += min(25, (consecutive_days - 7) * 3)
        
        return min(100, risk_factors)
    
    def _calculate_fatigue(self, df: pd.DataFrame) -> float:
        """Calculate fatigue level (0-100)"""
        if df.empty:
            return 0.0
        
        # Recent training load vs. average
        recent_load = self._calculate_training_load(df)
        
        # Historical average (last 12 weeks, excluding recent 2 weeks)
        historical_df = df[
            (df['date'] >= df['date'].max() - timedelta(days=84)) &
            (df['date'] < df['date'].max() - timedelta(days=14))
        ]
        
        if historical_df.empty:
            return 0.0
        
        historical_load = self._calculate_training_load(historical_df) * (2/10)  # Adjust for period
        
        if historical_load == 0:
            return 0.0
        
        fatigue_ratio = recent_load / historical_load
        fatigue_level = max(0, min(100, (fatigue_ratio - 0.8) * 100))
        
        return fatigue_level
    
    def _max_consecutive_days(self, dates: pd.Series) -> int:
        """Find maximum consecutive training days"""
        if dates.empty:
            return 0
        
        dates_unique = sorted(dates.dt.date.unique())
        max_consecutive = 1
        current_consecutive = 1
        
        for i in range(1, len(dates_unique)):
            if (dates_unique[i] - dates_unique[i-1]).days == 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
        
        return max_consecutive
    
    def _analyze_training_zones(self, df: pd.DataFrame) -> Dict:
        """Analyze time spent in different training zones"""
        if df.empty:
            return {}
        
        zone_time = {}
        total_time = df['moving_time'].sum()
        
        for zone_name, zone in self.training_zones.items():
            zone_activities = df[
                (df['pace'] >= zone.min_pace) & 
                (df['pace'] < zone.max_pace)
            ]
            zone_time[zone_name] = {
                'time_seconds': zone_activities['moving_time'].sum(),
                'percentage': (zone_activities['moving_time'].sum() / total_time * 100) if total_time > 0 else 0,
                'activities': len(zone_activities)
            }
        
        return zone_time
    
    def _analyze_trends(self, df: pd.DataFrame) -> Dict:
        """Analyze training trends over time"""
        if df.empty or len(df) < 4:
            return {}
        
        # Weekly aggregation
        df['week'] = df['date'].dt.isocalendar().week
        df['year'] = df['date'].dt.year
        
        weekly_stats = df.groupby(['year', 'week']).agg({
            'distance': 'sum',
            'moving_time': 'sum',
            'pace': 'mean'
        }).reset_index()
        
        if len(weekly_stats) < 2:
            return {}
        
        # Calculate trends
        weeks = range(len(weekly_stats))
        
        # Distance trend
        distance_trend = np.polyfit(weeks, weekly_stats['distance'], 1)[0] if len(weeks) > 1 else 0
        
        # Pace trend (negative = getting faster)
        pace_trend = np.polyfit(weeks, weekly_stats['pace'], 1)[0] if len(weeks) > 1 else 0
        
        return {
            'distance_trend': distance_trend,  # meters per week change
            'pace_trend': pace_trend,  # seconds per km per week change
            'weekly_stats': weekly_stats.to_dict('records')
        }
    
    def _create_empty_analysis(self) -> Dict:
        """Create empty analysis structure"""
        return {
            'fitness_metrics': {
                'current_fitness': 0.0,
                'aerobic_capacity': 35.0,
                'lactate_threshold': 360.0,
                'training_load': 0.0,
                'consistency_score': 0.0,
                'injury_risk': 0.0,
                'fatigue_level': 0.0
            },
            'zone_distribution': {},
            'trends': {},
            'total_activities': 0,
            'total_distance': 0.0,
            'analysis_period': 90
        }
    
    def _get_race_pace_activities(self, db_session: Session, athlete_id: int, distance_km: float) -> List[Activity]:
        """Get activities at similar pace to target race distance"""
        # This is a placeholder - would implement pace-based activity filtering
        cutoff_date = datetime.now() - timedelta(days=60)
        activities = db_session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= cutoff_date,
            Activity.sport_type.in_(['Run', 'VirtualRun']),
            Activity.distance >= distance_km * 500  # At least half race distance
        ).order_by(Activity.start_date.desc()).limit(10).all()
        
        return activities
    
    def _predict_via_vdot(self, fitness_analysis: Dict, distance_km: float) -> Optional[float]:
        """Predict race time using VDOT method"""
        vo2_max = fitness_analysis['fitness_metrics']['aerobic_capacity']
        
        if vo2_max < 35:
            return None
        
        # VDOT-based time prediction (simplified)
        if distance_km <= 5:
            predicted_time = (5000 / (vo2_max * 0.2)) * 60
        elif distance_km <= 10:
            predicted_time = (10000 / (vo2_max * 0.18)) * 60
        elif distance_km <= 21.1:
            predicted_time = (21100 / (vo2_max * 0.16)) * 60
        else:  # Marathon
            predicted_time = (42200 / (vo2_max * 0.14)) * 60
        
        return predicted_time
    
    def _predict_via_mcmillan(self, fitness_analysis: Dict, distance_km: float) -> Optional[float]:
        """Predict using McMillan-style equivalent performance"""
        threshold_pace = fitness_analysis['fitness_metrics']['lactate_threshold']
        
        if threshold_pace > 600:
            return None
        
        # McMillan equivalent times (simplified)
        if distance_km <= 5:
            race_pace = threshold_pace * 0.94
        elif distance_km <= 10:
            race_pace = threshold_pace * 0.97
        elif distance_km <= 21.1:
            race_pace = threshold_pace * 1.03
        else:  # Marathon
            race_pace = threshold_pace * 1.10
        
        predicted_time = race_pace * distance_km
        return predicted_time
    
    def _predict_via_pace_analysis(self, activities: List[Activity], distance_km: float) -> Optional[float]:
        """Predict based on recent pace analysis"""
        if not activities:
            return None
        
        # Analyze recent paces
        paces = []
        for activity in activities:
            if activity.distance > 0 and activity.moving_time > 0:
                pace = activity.moving_time / (activity.distance / 1000)
                paces.append(pace)
        
        if not paces:
            return None
        
        # Use median pace with distance adjustment
        median_pace = np.median(paces)
        
        # Adjust for race distance
        if distance_km <= 5:
            race_pace = median_pace * 0.98
        elif distance_km <= 10:
            race_pace = median_pace * 1.02
        elif distance_km <= 21.1:
            race_pace = median_pace * 1.08
        else:  # Marathon
            race_pace = median_pace * 1.15
        
        return race_pace * distance_km
    
    def _predict_via_physiological_model(self, fitness_analysis: Dict, distance_km: float) -> Optional[float]:
        """Predict using physiological model"""
        fitness_score = fitness_analysis['fitness_metrics']['current_fitness']
        vo2_max = fitness_analysis['fitness_metrics']['aerobic_capacity']
        
        if fitness_score < 10:
            return None
        
        # Physiological model based on fitness and VO2 max
        base_pace = 600 - (vo2_max - 35) * 8  # Base pace in seconds per km
        fitness_factor = (fitness_score / 100) * 0.9 + 0.1  # 0.1 to 1.0
        
        adjusted_pace = base_pace / fitness_factor
        
        # Distance-specific adjustments
        if distance_km <= 5:
            race_pace = adjusted_pace * 0.90
        elif distance_km <= 10:
            race_pace = adjusted_pace * 0.95
        elif distance_km <= 21.1:
            race_pace = adjusted_pace * 1.05
        else:  # Marathon
            race_pace = adjusted_pace * 1.20
        
        return race_pace * distance_km
    
    def _ensemble_predictions(self, predictions: List[float], fitness_analysis: Dict) -> float:
        """Combine multiple predictions with confidence weighting"""
        if not predictions:
            raise ValueError("No predictions to ensemble")
        
        # Simple weighted average for now
        # In practice, this would use more sophisticated ensemble methods
        weights = [1.0] * len(predictions)  # Equal weights
        
        weighted_sum = sum(p * w for p, w in zip(predictions, weights))
        total_weight = sum(weights)
        
        return weighted_sum / total_weight
    
    def _calculate_confidence(self, predictions: List[float], fitness_analysis: Dict) -> float:
        """Calculate prediction confidence score"""
        if not predictions:
            return 0.0
        
        # Base confidence on data quality and prediction agreement
        data_quality = min(1.0, fitness_analysis['total_activities'] / 20)
        
        if len(predictions) > 1:
            prediction_std = np.std(predictions)
            prediction_mean = np.mean(predictions)
            coefficient_of_variation = prediction_std / prediction_mean if prediction_mean > 0 else 1.0
            agreement_score = max(0.0, 1.0 - coefficient_of_variation)
        else:
            agreement_score = 0.7  # Moderate confidence for single prediction
        
        confidence = (data_quality * 0.6 + agreement_score * 0.4)
        return min(1.0, max(0.0, confidence))
    
    def _generate_pacing_strategy(self, predicted_time: float, distance_km: float) -> Dict[str, float]:
        """Generate kilometer-by-kilometer pacing strategy"""
        target_pace = predicted_time / distance_km
        
        strategy = {}
        
        if distance_km <= 10:
            # Negative split strategy for shorter races
            for km in range(1, int(distance_km) + 1):
                if km <= distance_km / 2:
                    strategy[f'km_{km}'] = target_pace * 1.02
                else:
                    strategy[f'km_{km}'] = target_pace * 0.98
        else:
            # Conservative start for longer races
            for km in range(1, int(distance_km) + 1):
                if km <= 5:
                    strategy[f'km_{km}'] = target_pace * 1.05
                elif km <= distance_km * 0.8:
                    strategy[f'km_{km}'] = target_pace
                else:
                    strategy[f'km_{km}'] = target_pace * 0.98
        
        return strategy
    
    def _generate_training_recommendations(self, fitness_analysis: Dict, race_distance: str) -> List[str]:
        """Generate personalized training recommendations"""
        recommendations = []
        
        fitness_score = fitness_analysis['fitness_metrics']['current_fitness']
        consistency = fitness_analysis['fitness_metrics']['consistency_score']
        injury_risk = fitness_analysis['fitness_metrics']['injury_risk']
        
        # Base recommendations on current fitness level
        if fitness_score < 30:
            recommendations.append("Focus on building aerobic base with easy-paced runs")
            recommendations.append("Increase weekly volume gradually (10% rule)")
        elif fitness_score < 60:
            recommendations.append("Add tempo runs once per week")
            recommendations.append("Include one long run per week")
        else:
            recommendations.append("Incorporate interval training for speed development")
            recommendations.append("Practice race pace segments during long runs")
        
        # Consistency-based recommendations
        if consistency < 50:
            recommendations.append("Prioritize consistency over intensity")
            recommendations.append("Aim for at least 3-4 runs per week")
        
        # Injury risk management
        if injury_risk > 50:
            recommendations.append("Reduce training volume by 20% for injury prevention")
            recommendations.append("Focus on recovery and cross-training")
        
        # Race-specific recommendations
        if race_distance == 'Marathon':
            recommendations.append("Build long runs up to 32-35km")
            recommendations.append("Practice marathon pace during 20-25km runs")
        elif race_distance == 'Half Marathon':
            recommendations.append("Include 15-20km runs at moderate effort")
            recommendations.append("Practice half marathon pace for 8-12km segments")
        
        return recommendations[:6]  # Limit to top 6 recommendations
    
    def _generate_taper_plan(self, db_session: Session, athlete_id: int, days_to_race: int) -> Dict:
        """Generate taper plan for final week before race"""
        return {
            'phase': 'taper',
            'duration_days': days_to_race,
            'weekly_volume_reduction': 40,
            'intensity_maintenance': 80,
            'key_workouts': [
                f"Day {days_to_race-3}: Easy 30-40 minutes with 4x100m strides",
                f"Day {days_to_race-1}: 20 minutes easy + race pace preview",
                f"Race day: Warm-up 15 minutes easy + 4x100m"
            ]
        }
    
    def _generate_peak_plan(self, db_session: Session, athlete_id: int, race_distance: str, days_to_race: int) -> Dict:
        """Generate peak phase training plan"""
        return {
            'phase': 'peak',
            'duration_days': days_to_race,
            'focus': 'race_specific_fitness',
            'weekly_structure': {
                'easy_runs': 3,
                'workout_days': 2,
                'long_run': 1,
                'rest_days': 1
            },
            'key_workouts': [
                f"Week 1: {race_distance} pace intervals",
                f"Week 2: Race simulation run",
                f"Week 3-4: Taper with pace maintenance"
            ]
        }
    
    def _generate_build_plan(self, db_session: Session, athlete_id: int, race_distance: str, days_to_race: int) -> Dict:
        """Generate build phase training plan"""
        weeks_to_race = days_to_race // 7
        
        return {
            'phase': 'build',
            'duration_weeks': weeks_to_race,
            'volume_progression': 'gradual_increase',
            'weekly_structure': {
                'easy_runs': 4,
                'workout_days': 2,
                'long_run': 1,
                'rest_days': 1
            },
            'progression': {
                'weeks_1_4': 'Base building with tempo runs',
                'weeks_5_8': 'Add interval training',
                'weeks_9_12': 'Race-specific training',
                'final_weeks': 'Peak and taper'
            }
        }