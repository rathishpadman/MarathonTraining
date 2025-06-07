"""
Advanced ML-based Injury Risk Prediction System
Analyzes training patterns, biomechanical indicators, and performance metrics
to predict injury risk for marathon athletes.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib
import logging
from typing import Dict, List, Tuple, Optional
import json
from .models import ReplitAthlete, Activity, DailySummary, db

logger = logging.getLogger(__name__)

class InjuryRiskPredictor:
    """
    Advanced ML system for predicting injury risk in marathon athletes
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.is_trained = False
        
        # Risk thresholds
        self.risk_thresholds = {
            'low': 0.3,
            'moderate': 0.6,
            'high': 0.8
        }
        
        # Feature weights for different injury types
        self.injury_types = [
            'overuse',
            'acute',
            'biomechanical',
            'fatigue'
        ]
    
    def extract_features(self, athlete_id: int, days_lookback: int = 30) -> Dict:
        """
        Extract comprehensive features for injury prediction
        """
        try:
            athlete = db.session.query(ReplitAthlete).filter_by(id=athlete_id).first()
            if not athlete:
                return {}
            
            # Get recent activities
            cutoff_date = datetime.now() - timedelta(days=days_lookback)
            activities = db.session.query(Activity).filter(
                Activity.athlete_id == athlete_id,
                Activity.start_date >= cutoff_date
            ).order_by(Activity.start_date.desc()).all()
            
            if not activities:
                return {}
            
            # Extract training load features
            training_features = self._extract_training_load_features(activities)
            
            # Extract biomechanical features
            biomech_features = self._extract_biomechanical_features(activities)
            
            # Extract recovery features
            recovery_features = self._extract_recovery_features(activities)
            
            # Extract progression features
            progression_features = self._extract_progression_features(activities)
            
            # Extract physiological features
            physio_features = self._extract_physiological_features(activities, athlete)
            
            # Combine all features
            features = {
                **training_features,
                **biomech_features,
                **recovery_features,
                **progression_features,
                **physio_features
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features for athlete {athlete_id}: {str(e)}")
            return {}
    
    def _extract_training_load_features(self, activities: List[Activity]) -> Dict:
        """Extract training load and intensity features"""
        if not activities:
            return {}
        
        # Convert to DataFrame for easier processing
        data = []
        for activity in activities:
            if activity.distance and activity.moving_time:
                data.append({
                    'distance': activity.distance / 1000,  # Convert to km
                    'duration': activity.moving_time / 3600,  # Convert to hours
                    'date': activity.start_date,
                    'elevation': activity.total_elevation_gain or 0,
                    'avg_hr': activity.average_heartrate or 0,
                    'max_hr': activity.max_heartrate or 0,
                    'pace': (activity.moving_time / 60) / (activity.distance / 1000) if activity.distance > 0 else 0
                })
        
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        # Training load metrics
        total_distance = df['distance'].sum()
        total_duration = df['duration'].sum()
        avg_weekly_distance = total_distance * 7 / len(df) if len(df) > 0 else 0
        
        # Intensity distribution
        high_intensity_runs = len(df[df['avg_hr'] > 160]) if 'avg_hr' in df.columns else 0
        long_runs = len(df[df['distance'] > 15])
        
        # Training monotony (Bannister)
        daily_loads = df['distance'] * df['duration']
        training_monotony = daily_loads.mean() / daily_loads.std() if daily_loads.std() > 0 else 0
        
        # Training strain
        training_strain = daily_loads.sum() * training_monotony
        
        return {
            'total_distance_4w': total_distance,
            'avg_weekly_distance': avg_weekly_distance,
            'total_duration_4w': total_duration,
            'training_frequency': len(df),
            'high_intensity_ratio': high_intensity_runs / len(df) if len(df) > 0 else 0,
            'long_run_ratio': long_runs / len(df) if len(df) > 0 else 0,
            'training_monotony': training_monotony,
            'training_strain': training_strain,
            'avg_elevation_per_run': df['elevation'].mean(),
            'max_weekly_distance': df.groupby(df['date'].dt.isocalendar().week)['distance'].sum().max() if len(df) > 0 else 0
        }
    
    def _extract_biomechanical_features(self, activities: List[Activity]) -> Dict:
        """Extract biomechanical and gait-related features"""
        if not activities:
            return {}
        
        # Pace variability
        paces = []
        cadences = []
        hr_variabilities = []
        
        for activity in activities:
            if activity.distance and activity.moving_time and activity.distance > 0:
                pace = (activity.moving_time / 60) / (activity.distance / 1000)
                paces.append(pace)
                
                if activity.average_cadence:
                    cadences.append(activity.average_cadence)
                
                # HR variability proxy
                if activity.average_heartrate and activity.max_heartrate:
                    hr_var = (activity.max_heartrate - activity.average_heartrate) / activity.average_heartrate
                    hr_variabilities.append(hr_var)
        
        pace_cv = np.std(paces) / np.mean(paces) if paces and np.mean(paces) > 0 else 0
        cadence_avg = np.mean(cadences) if cadences else 0
        cadence_cv = np.std(cadences) / np.mean(cadences) if cadences and np.mean(cadences) > 0 else 0
        hr_variability_avg = np.mean(hr_variabilities) if hr_variabilities else 0
        
        return {
            'pace_variability': pace_cv,
            'avg_cadence': cadence_avg,
            'cadence_variability': cadence_cv,
            'hr_variability': hr_variability_avg,
            'biomech_efficiency_score': 1 / (1 + pace_cv + cadence_cv) if (pace_cv + cadence_cv) > 0 else 1
        }
    
    def _extract_recovery_features(self, activities: List[Activity]) -> Dict:
        """Extract recovery and rest pattern features"""
        if len(activities) < 2:
            return {}
        
        # Sort activities by date
        sorted_activities = sorted(activities, key=lambda x: x.start_date)
        
        # Calculate rest days between activities
        rest_periods = []
        consecutive_days = 0
        max_consecutive = 0
        
        for i in range(1, len(sorted_activities)):
            days_between = (sorted_activities[i].start_date - sorted_activities[i-1].start_date).days
            
            if days_between == 1:
                consecutive_days += 1
                max_consecutive = max(max_consecutive, consecutive_days)
            else:
                consecutive_days = 0
                if days_between > 1:
                    rest_periods.append(days_between - 1)
        
        avg_rest_period = np.mean(rest_periods) if rest_periods else 0
        rest_variability = np.std(rest_periods) if rest_periods else 0
        
        # Recovery quality indicators
        recovery_runs = len([a for a in activities if a.distance and a.distance < 5000])  # Easy runs < 5km
        recovery_ratio = recovery_runs / len(activities) if activities else 0
        
        return {
            'avg_rest_days': avg_rest_period,
            'rest_variability': rest_variability,
            'max_consecutive_days': max_consecutive,
            'recovery_run_ratio': recovery_ratio,
            'adequate_recovery_score': 1 / (1 + max_consecutive / 7) if max_consecutive > 0 else 1
        }
    
    def _extract_progression_features(self, activities: List[Activity]) -> Dict:
        """Extract training progression and load changes"""
        if len(activities) < 8:  # Need at least 2 weeks of data
            return {}
        
        # Sort by date
        sorted_activities = sorted(activities, key=lambda x: x.start_date)
        
        # Split into weeks
        weeks = {}
        for activity in sorted_activities:
            week_key = activity.start_date.isocalendar()[1]
            if week_key not in weeks:
                weeks[week_key] = []
            weeks[week_key].append(activity)
        
        if len(weeks) < 2:
            return {}
        
        # Calculate weekly loads
        weekly_distances = []
        weekly_durations = []
        
        for week_activities in weeks.values():
            week_distance = sum(a.distance / 1000 for a in week_activities if a.distance)
            week_duration = sum(a.moving_time / 3600 for a in week_activities if a.moving_time)
            weekly_distances.append(week_distance)
            weekly_durations.append(week_duration)
        
        # Progression metrics
        distance_trend = np.polyfit(range(len(weekly_distances)), weekly_distances, 1)[0] if len(weekly_distances) > 1 else 0
        
        # Weekly load changes
        weekly_changes = []
        for i in range(1, len(weekly_distances)):
            if weekly_distances[i-1] > 0:
                change = (weekly_distances[i] - weekly_distances[i-1]) / weekly_distances[i-1]
                weekly_changes.append(abs(change))
        
        avg_weekly_change = np.mean(weekly_changes) if weekly_changes else 0
        max_weekly_increase = max([c for c in weekly_changes if c > 0] or [0])
        
        # 10% rule violation
        violates_10_percent_rule = max_weekly_increase > 0.1
        
        return {
            'weekly_distance_trend': distance_trend,
            'avg_weekly_load_change': avg_weekly_change,
            'max_weekly_increase': max_weekly_increase,
            'violates_10_percent_rule': int(violates_10_percent_rule),
            'progression_risk_score': min(max_weekly_increase * 10, 1.0)
        }
    
    def _extract_physiological_features(self, activities: List[Activity], athlete: ReplitAthlete) -> Dict:
        """Extract physiological and athlete-specific features"""
        if not activities:
            return {}
        
        # Heart rate zones analysis
        hr_zones = self._analyze_hr_zones(activities, athlete)
        
        # Performance trends
        recent_paces = []
        recent_hrs = []
        
        for activity in activities[-10:]:  # Last 10 activities
            if activity.distance and activity.moving_time and activity.distance > 0:
                pace = (activity.moving_time / 60) / (activity.distance / 1000)
                recent_paces.append(pace)
                
                if activity.average_heartrate:
                    recent_hrs.append(activity.average_heartrate)
        
        # Performance fatigue indicators
        pace_trend = np.polyfit(range(len(recent_paces)), recent_paces, 1)[0] if len(recent_paces) > 1 else 0
        hr_trend = np.polyfit(range(len(recent_hrs)), recent_hrs, 1)[0] if len(recent_hrs) > 1 else 0
        
        # Efficiency ratio (pace getting slower while HR increases = fatigue)
        efficiency_decline = pace_trend > 0 and hr_trend > 0
        
        return {
            **hr_zones,
            'pace_trend': pace_trend,
            'hr_trend': hr_trend,
            'efficiency_decline': int(efficiency_decline),
            'fatigue_indicator': pace_trend + (hr_trend / 100),  # Normalized combination
            'training_experience_days': (datetime.now() - athlete.created_at).days if athlete.created_at else 0
        }
    
    def _analyze_hr_zones(self, activities: List[Activity], athlete: ReplitAthlete) -> Dict:
        """Analyze heart rate zone distribution"""
        if not athlete.max_hr:
            return {
                'zone1_time_ratio': 0,
                'zone2_time_ratio': 0,
                'zone3_time_ratio': 0,
                'zone4_time_ratio': 0,
                'zone5_time_ratio': 0,
                'polarization_index': 0
            }
        
        max_hr = athlete.max_hr
        zones = {
            'zone1': (0, 0.6 * max_hr),      # Recovery
            'zone2': (0.6 * max_hr, 0.7 * max_hr),  # Aerobic base
            'zone3': (0.7 * max_hr, 0.8 * max_hr),  # Aerobic threshold
            'zone4': (0.8 * max_hr, 0.9 * max_hr),  # Lactate threshold
            'zone5': (0.9 * max_hr, max_hr)         # VO2 max
        }
        
        zone_times = {zone: 0 for zone in zones.keys()}
        total_time = 0
        
        for activity in activities:
            if activity.average_heartrate and activity.moving_time:
                hr = activity.average_heartrate
                duration = activity.moving_time / 60  # Convert to minutes
                total_time += duration
                
                for zone, (min_hr, max_hr_zone) in zones.items():
                    if min_hr <= hr < max_hr_zone:
                        zone_times[zone] += duration
                        break
        
        # Calculate ratios
        ratios = {}
        for zone in zones.keys():
            ratios[f'{zone}_time_ratio'] = zone_times[zone] / total_time if total_time > 0 else 0
        
        # Polarization index (80/20 rule)
        easy_intensity = ratios['zone1_time_ratio'] + ratios['zone2_time_ratio']
        hard_intensity = ratios['zone4_time_ratio'] + ratios['zone5_time_ratio']
        polarization_index = easy_intensity / (easy_intensity + hard_intensity) if (easy_intensity + hard_intensity) > 0 else 0
        
        ratios['polarization_index'] = polarization_index
        
        return ratios
    
    def predict_injury_risk(self, athlete_id: int) -> Dict:
        """
        Predict injury risk for a specific athlete
        """
        try:
            # Extract features
            features = self.extract_features(athlete_id)
            
            if not features:
                return {
                    'overall_risk': 0.0,
                    'risk_level': 'unknown',
                    'risk_factors': [],
                    'recommendations': ['Insufficient data for prediction'],
                    'confidence': 0.0
                }
            
            # Use rule-based system if ML models not trained
            if not self.is_trained:
                return self._rule_based_prediction(features)
            
            # Use trained ML models
            return self._ml_based_prediction(features)
            
        except Exception as e:
            logger.error(f"Error predicting injury risk for athlete {athlete_id}: {str(e)}")
            return {
                'overall_risk': 0.0,
                'risk_level': 'error',
                'risk_factors': ['Prediction error'],
                'recommendations': ['Unable to assess risk'],
                'confidence': 0.0
            }
    
    def _rule_based_prediction(self, features: Dict) -> Dict:
        """
        Rule-based injury risk prediction when ML models are not available
        """
        risk_score = 0.0
        risk_factors = []
        recommendations = []
        
        # Training load risks
        if features.get('violates_10_percent_rule', 0) > 0:
            risk_score += 0.3
            risk_factors.append('Rapid training load increase')
            recommendations.append('Limit weekly mileage increases to 10%')
        
        if features.get('training_monotony', 0) > 2.0:
            risk_score += 0.2
            risk_factors.append('High training monotony')
            recommendations.append('Add variety to training intensities')
        
        if features.get('max_consecutive_days', 0) > 6:
            risk_score += 0.25
            risk_factors.append('Insufficient recovery days')
            recommendations.append('Include at least one rest day per week')
        
        # Biomechanical risks
        if features.get('pace_variability', 0) > 0.3:
            risk_score += 0.15
            risk_factors.append('High pace variability')
            recommendations.append('Focus on consistent pacing during runs')
        
        if features.get('cadence_variability', 0) > 0.2:
            risk_score += 0.1
            risk_factors.append('Inconsistent running cadence')
            recommendations.append('Work on maintaining steady cadence around 180 steps/min')
        
        # Physiological risks
        if features.get('efficiency_decline', 0) > 0:
            risk_score += 0.2
            risk_factors.append('Declining running efficiency')
            recommendations.append('Consider reducing training intensity for recovery')
        
        if features.get('polarization_index', 0) < 0.8:
            risk_score += 0.15
            risk_factors.append('Inadequate easy running ratio')
            recommendations.append('Follow 80/20 rule: 80% easy, 20% hard training')
        
        # Recovery risks
        if features.get('recovery_run_ratio', 0) < 0.3:
            risk_score += 0.1
            risk_factors.append('Insufficient recovery runs')
            recommendations.append('Include more easy recovery runs in training')
        
        # Determine risk level
        if risk_score < self.risk_thresholds['low']:
            risk_level = 'low'
        elif risk_score < self.risk_thresholds['moderate']:
            risk_level = 'moderate'
        elif risk_score < self.risk_thresholds['high']:
            risk_level = 'high'
        else:
            risk_level = 'very_high'
        
        # Add general recommendations if no specific risks
        if not recommendations:
            recommendations = [
                'Maintain current training approach',
                'Continue monitoring training load progression',
                'Ensure adequate recovery between hard sessions'
            ]
        
        return {
            'overall_risk': min(risk_score, 1.0),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'confidence': 0.7,  # Rule-based confidence
            'prediction_method': 'rule_based',
            'feature_analysis': self._analyze_key_features(features)
        }
    
    def _analyze_key_features(self, features: Dict) -> Dict:
        """Analyze key features for detailed insights"""
        analysis = {}
        
        # Training load analysis
        weekly_distance = features.get('avg_weekly_distance', 0)
        if weekly_distance > 80:
            analysis['training_load'] = 'high'
        elif weekly_distance > 50:
            analysis['training_load'] = 'moderate'
        else:
            analysis['training_load'] = 'low'
        
        # Recovery analysis
        rest_days = features.get('avg_rest_days', 0)
        if rest_days < 1:
            analysis['recovery'] = 'insufficient'
        elif rest_days < 2:
            analysis['recovery'] = 'minimal'
        else:
            analysis['recovery'] = 'adequate'
        
        # Progression analysis
        if features.get('progression_risk_score', 0) > 0.5:
            analysis['progression'] = 'aggressive'
        elif features.get('progression_risk_score', 0) > 0.2:
            analysis['progression'] = 'moderate'
        else:
            analysis['progression'] = 'conservative'
        
        return analysis
    
    def get_injury_prevention_plan(self, athlete_id: int) -> Dict:
        """
        Generate personalized injury prevention plan
        """
        risk_assessment = self.predict_injury_risk(athlete_id)
        
        prevention_plan = {
            'risk_assessment': risk_assessment,
            'prevention_strategies': [],
            'monitoring_metrics': [],
            'warning_signs': [],
            'action_plan': {}
        }
        
        risk_level = risk_assessment['risk_level']
        
        # Base prevention strategies
        base_strategies = [
            'Gradual training progression (10% rule)',
            'Regular strength training 2-3x per week',
            'Proper warm-up and cool-down routines',
            'Adequate sleep (7-9 hours nightly)',
            'Proper nutrition and hydration'
        ]
        
        prevention_plan['prevention_strategies'].extend(base_strategies)
        
        # Risk-specific strategies
        if risk_level in ['high', 'very_high']:
            high_risk_strategies = [
                'Reduce weekly mileage by 20-30%',
                'Increase recovery runs and rest days',
                'Consider massage or physiotherapy',
                'Monitor heart rate variability',
                'Cross-training activities (swimming, cycling)'
            ]
            prevention_plan['prevention_strategies'].extend(high_risk_strategies)
        
        elif risk_level == 'moderate':
            moderate_risk_strategies = [
                'Maintain current training load',
                'Add extra rest day if consecutive training days > 5',
                'Focus on running form and efficiency',
                'Include preventive exercises'
            ]
            prevention_plan['prevention_strategies'].extend(moderate_risk_strategies)
        
        # Monitoring metrics
        prevention_plan['monitoring_metrics'] = [
            'Weekly training load',
            'Resting heart rate',
            'Sleep quality',
            'Perceived exertion levels',
            'Any pain or discomfort'
        ]
        
        # Warning signs
        prevention_plan['warning_signs'] = [
            'Persistent muscle soreness',
            'Elevated resting heart rate',
            'Declining performance despite training',
            'Sleep disturbances',
            'Loss of motivation',
            'Any sharp or persistent pain'
        ]
        
        # Action plan based on risk level
        if risk_level == 'low':
            prevention_plan['action_plan'] = {
                'frequency': 'Weekly monitoring',
                'actions': ['Continue current training', 'Monthly assessment']
            }
        elif risk_level == 'moderate':
            prevention_plan['action_plan'] = {
                'frequency': 'Daily monitoring',
                'actions': ['Adjust training if warning signs appear', 'Weekly assessment']
            }
        else:  # high or very_high
            prevention_plan['action_plan'] = {
                'frequency': 'Daily monitoring',
                'actions': [
                    'Immediate training adjustment',
                    'Consider professional consultation',
                    'Daily assessment until risk reduces'
                ]
            }
        
        return prevention_plan

# Global instance
injury_predictor = InjuryRiskPredictor()

def predict_injury_risk(athlete_id: int) -> Dict:
    """Global function for injury risk prediction"""
    return injury_predictor.predict_injury_risk(athlete_id)

def get_injury_prevention_plan(athlete_id: int) -> Dict:
    """Global function for injury prevention plan"""
    return injury_predictor.get_injury_prevention_plan(athlete_id)