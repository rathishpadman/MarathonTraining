import joblib
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.models import ReplitAthlete, Activity, DailySummary
from app import db

class ReplitAnalyticsEngine:
    """
    Memory-efficient analytics engine for Replit environment, designed for multi-athlete data.
    Utilizes pandas for efficient in-memory data manipulation and lightweight ML models.
    """
    
    def __init__(self):
        self.models = self.load_lightweight_models()
        self.logger = logging.getLogger(__name__)
    
    def load_lightweight_models(self) -> Dict[str, Any]:
        """
        Load optimized ML models for Replit.
        Models should be pre-trained and saved in a lightweight format (e.g., joblib).
        """
        try:
            models = {}
            
            # Attempt to load performance prediction model
            try:
                models['performance_predictor'] = joblib.load('data/models/light_perf_model.pkl')
                self.logger.info("Performance prediction model loaded successfully")
            except FileNotFoundError:
                self.logger.warning("Performance prediction model not found at data/models/light_perf_model.pkl")
            
            # Attempt to load injury risk model
            try:
                models['injury_risk_model'] = joblib.load('data/models/light_risk_model.pkl')
                self.logger.info("Injury risk model loaded successfully")
            except FileNotFoundError:
                self.logger.warning("Injury risk model not found at data/models/light_risk_model.pkl")
            
            if not models:
                self.logger.warning("No ML models loaded. Using fallback prediction methods.")
                
            return models
            
        except Exception as e:
            self.logger.error(f"Error loading ML models: {str(e)}")
            return {}
    
    def get_sampled_training_data(self, athlete_id: int, days: int = 90) -> pd.DataFrame:
        """
        Efficiently retrieve and sample training data for a specific athlete.
        This prevents loading all historical data into memory at once for prediction.
        """
        try:
            self.logger.info(f"Fetching training data for athlete {athlete_id} (last {days} days)")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Query activities for the athlete within the date range
            activities = db.session.query(Activity).filter(
                Activity.athlete_id == athlete_id,
                Activity.start_date >= start_date,
                Activity.start_date <= end_date
            ).order_by(Activity.start_date.desc()).limit(500).all()  # Limit to prevent memory issues
            
            if not activities:
                self.logger.warning(f"No training data found for athlete {athlete_id}")
                return pd.DataFrame()
            
            # Convert to pandas DataFrame for efficient processing
            activity_data = []
            for activity in activities:
                # Calculate derived metrics
                pace = None
                if activity.distance and activity.moving_time and activity.distance > 0:
                    pace = activity.moving_time / (activity.distance / 1000)  # seconds per km
                
                activity_data.append({
                    'athlete_id': athlete_id,
                    'date': activity.start_date,
                    'distance': activity.distance or 0,
                    'moving_time': activity.moving_time or 0,
                    'pace': pace,
                    'average_speed': activity.average_speed or 0,
                    'elevation_gain': activity.total_elevation_gain or 0,
                    'average_heartrate': activity.average_heartrate,
                    'max_heartrate': activity.max_heartrate,
                    'suffer_score': activity.suffer_score or 0,
                    'sport_type': activity.sport_type
                })
            
            df = pd.DataFrame(activity_data)
            
            # Add derived features for ML models
            if not df.empty:
                df = self._add_derived_features(df)
            
            self.logger.info(f"Retrieved {len(df)} training records for athlete {athlete_id}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching training data for athlete {athlete_id}: {str(e)}")
            return pd.DataFrame()
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features for ML model input"""
        try:
            # Ensure date column is datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Sort by date for time-series features
            df = df.sort_values('date')
            
            # Add rolling averages (7-day window)
            df['distance_7d_avg'] = df['distance'].rolling(window=7, min_periods=1).mean()
            df['pace_7d_avg'] = df['pace'].rolling(window=7, min_periods=1).mean()
            df['hr_7d_avg'] = df['average_heartrate'].rolling(window=7, min_periods=1).mean()
            
            # Add rolling sums
            df['distance_7d_sum'] = df['distance'].rolling(window=7, min_periods=1).sum()
            df['training_load_7d'] = df['suffer_score'].rolling(window=7, min_periods=1).sum()
            
            # Add day of week
            df['day_of_week'] = df['date'].dt.dayofweek
            
            # Add training intensity categories
            df['training_intensity'] = pd.cut(
                df['suffer_score'], 
                bins=[0, 50, 100, 150, float('inf')], 
                labels=['Easy', 'Moderate', 'Hard', 'Very Hard']
            )
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error adding derived features: {str(e)}")
            return df
    
    def predict_race_performance(self, athlete_id: int, race_distance: float) -> Dict[str, Any]:
        """
        Predict race performance for a specific athlete using their training data.
        """
        try:
            self.logger.info(f"Predicting race performance for athlete {athlete_id}, distance: {race_distance}km")
            
            # Get training data
            training_data = self.get_sampled_training_data(athlete_id)
            
            if training_data.empty:
                return {
                    'prediction': None,
                    'confidence': 0.0,
                    'message': 'Insufficient training data for prediction'
                }
            
            # Check if we have a trained model
            if 'performance_predictor' in self.models:
                prediction = self._ml_race_prediction(training_data, race_distance)
            else:
                prediction = self._heuristic_race_prediction(training_data, race_distance)
            
            self.logger.info(f"Race prediction completed for athlete {athlete_id}: {prediction['prediction']:.2f} minutes")
            return prediction
            
        except Exception as e:
            self.logger.error(f"Error predicting race performance for athlete {athlete_id}: {str(e)}")
            return {
                'prediction': None,
                'confidence': 0.0,
                'message': f'Prediction failed: {str(e)}'
            }
    
    def _ml_race_prediction(self, training_data: pd.DataFrame, race_distance: float) -> Dict[str, Any]:
        """Use ML model for race prediction"""
        try:
            model = self.models['performance_predictor']
            
            # Prepare features for the model
            # This would depend on how the model was trained
            # For now, using a simplified feature set
            recent_data = training_data.head(30)  # Last 30 activities
            
            features = [
                recent_data['distance'].mean(),
                recent_data['pace'].mean(),
                recent_data['distance_7d_avg'].iloc[-1] if len(recent_data) > 0 else 0,
                recent_data['pace_7d_avg'].iloc[-1] if len(recent_data) > 0 else 0,
                race_distance
            ]
            
            # Make prediction
            prediction = model.predict([features])[0]
            
            # Calculate confidence based on data quality
            confidence = min(len(training_data) / 50.0, 1.0)  # Max confidence at 50+ activities
            
            return {
                'prediction': prediction,
                'confidence': confidence,
                'method': 'ML Model',
                'features_used': len(features)
            }
            
        except Exception as e:
            self.logger.error(f"ML prediction failed: {str(e)}")
            # Fallback to heuristic method
            return self._heuristic_race_prediction(training_data, race_distance)
    
    def _heuristic_race_prediction(self, training_data: pd.DataFrame, race_distance: float) -> Dict[str, Any]:
        """
        Heuristic-based race prediction when ML models are not available.
        Based on training pace and distance patterns.
        """
        try:
            # Filter running activities for pace calculation
            running_data = training_data[training_data['sport_type'] == 'Run'].copy()
            
            if running_data.empty:
                # Use all activities if no running data
                running_data = training_data.copy()
            
            # Get recent pace data (last 30 days)
            recent_date = training_data['date'].max() - timedelta(days=30)
            recent_running = running_data[running_data['date'] >= recent_date]
            
            if recent_running.empty:
                recent_running = running_data.tail(10)  # Last 10 activities
            
            # Calculate average pace for different distance ranges
            short_runs = recent_running[recent_running['distance'] < 8000]  # < 8km
            medium_runs = recent_running[(recent_running['distance'] >= 8000) & (recent_running['distance'] < 15000)]
            long_runs = recent_running[recent_running['distance'] >= 15000]  # >= 15km
            
            # Determine base pace based on race distance
            if race_distance <= 5:
                # Use short run pace for 5K and shorter
                base_pace = short_runs['pace'].median() if not short_runs.empty else recent_running['pace'].median()
                pace_adjustment = 0.9  # Slightly faster than training pace
            elif race_distance <= 10:
                # Use medium run pace for 10K
                base_pace = medium_runs['pace'].median() if not medium_runs.empty else recent_running['pace'].median()
                pace_adjustment = 0.95
            elif race_distance <= 21:
                # Use long run pace for half marathon
                base_pace = long_runs['pace'].median() if not long_runs.empty else recent_running['pace'].median()
                pace_adjustment = 1.05
            else:
                # Use long run pace with adjustment for marathon+
                base_pace = long_runs['pace'].median() if not long_runs.empty else recent_running['pace'].median()
                pace_adjustment = 1.15
            
            if pd.isna(base_pace):
                return {
                    'prediction': None,
                    'confidence': 0.0,
                    'message': 'No valid pace data found'
                }
            
            # Calculate predicted time
            adjusted_pace = base_pace * pace_adjustment
            predicted_time_minutes = (adjusted_pace * race_distance) / 60
            
            # Calculate confidence based on data quality
            confidence = min(len(recent_running) / 20.0, 0.8)  # Max 80% confidence for heuristic
            
            return {
                'prediction': predicted_time_minutes,
                'confidence': confidence,
                'method': 'Heuristic',
                'base_pace': base_pace,
                'adjustment_factor': pace_adjustment,
                'data_points': len(recent_running)
            }
            
        except Exception as e:
            self.logger.error(f"Heuristic prediction failed: {str(e)}")
            return {
                'prediction': None,
                'confidence': 0.0,
                'message': f'Heuristic prediction failed: {str(e)}'
            }
    
    def analyze_training_trends(self, athlete_id: int, days: int = 90) -> Dict[str, Any]:
        """
        Analyze training trends for an athlete over the specified period
        """
        try:
            self.logger.info(f"Analyzing training trends for athlete {athlete_id}")
            
            training_data = self.get_sampled_training_data(athlete_id, days)
            
            if training_data.empty:
                return {
                    'message': 'No training data available for trend analysis'
                }
            
            # Calculate weekly aggregates
            training_data['week'] = training_data['date'].dt.to_period('W')
            weekly_stats = training_data.groupby('week').agg({
                'distance': 'sum',
                'moving_time': 'sum',
                'suffer_score': 'sum',
                'pace': 'mean'
            }).reset_index()
            
            # Calculate trends
            trends = {}
            
            if len(weekly_stats) >= 4:  # Need at least 4 weeks for trend analysis
                # Distance trend
                x = np.arange(len(weekly_stats))
                distance_trend = np.polyfit(x, weekly_stats['distance'], 1)[0]
                trends['distance_trend'] = 'increasing' if distance_trend > 0 else 'decreasing'
                trends['distance_change_per_week'] = distance_trend
                
                # Pace trend
                pace_trend = np.polyfit(x, weekly_stats['pace'].fillna(0), 1)[0]
                trends['pace_trend'] = 'improving' if pace_trend < 0 else 'declining'
                trends['pace_change_per_week'] = pace_trend
                
                # Training load trend
                load_trend = np.polyfit(x, weekly_stats['suffer_score'], 1)[0]
                trends['training_load_trend'] = 'increasing' if load_trend > 0 else 'decreasing'
                trends['load_change_per_week'] = load_trend
            
            # Current performance metrics
            recent_4_weeks = weekly_stats.tail(4)
            current_metrics = {
                'avg_weekly_distance': recent_4_weeks['distance'].mean(),
                'avg_weekly_time': recent_4_weeks['moving_time'].mean(),
                'avg_weekly_training_load': recent_4_weeks['suffer_score'].mean(),
                'current_pace': recent_4_weeks['pace'].mean()
            }
            
            return {
                'trends': trends,
                'current_metrics': current_metrics,
                'analysis_period': f"{days} days",
                'weeks_analyzed': len(weekly_stats)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing training trends for athlete {athlete_id}: {str(e)}")
            return {
                'message': f'Trend analysis failed: {str(e)}'
            }
    
    def get_performance_insights(self, athlete_id: int) -> Dict[str, Any]:
        """
        Generate comprehensive performance insights for an athlete
        """
        try:
            self.logger.info(f"Generating performance insights for athlete {athlete_id}")
            
            # Get training data and trends
            training_data = self.get_sampled_training_data(athlete_id)
            trends = self.analyze_training_trends(athlete_id)
            
            insights = {
                'summary': {},
                'recommendations': [],
                'alerts': [],
                'achievements': []
            }
            
            if training_data.empty:
                insights['summary']['message'] = 'No training data available'
                return insights
            
            # Performance summary
            recent_30_days = training_data[training_data['date'] >= (datetime.now() - timedelta(days=30))]
            
            insights['summary'] = {
                'total_activities': len(training_data),
                'recent_activities': len(recent_30_days),
                'total_distance': training_data['distance'].sum() / 1000,  # Convert to km
                'avg_pace': training_data['pace'].mean() if 'pace' in training_data.columns else None,
                'consistency_score': len(recent_30_days) / 30.0 * 100  # Activities per day percentage
            }
            
            # Generate recommendations based on trends
            if 'trends' in trends:
                trend_data = trends['trends']
                
                if trend_data.get('distance_trend') == 'decreasing':
                    insights['recommendations'].append("Consider gradually increasing your weekly distance")
                
                if trend_data.get('pace_trend') == 'declining':
                    insights['recommendations'].append("Focus on speed work to improve your pace")
                
                if trend_data.get('training_load_trend') == 'increasing':
                    insights['alerts'].append("High training load trend detected - ensure adequate recovery")
            
            # Consistency insights
            consistency_score = insights['summary']['consistency_score']
            if consistency_score > 80:
                insights['achievements'].append("Excellent training consistency!")
            elif consistency_score < 40:
                insights['recommendations'].append("Try to maintain more consistent training schedule")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights for athlete {athlete_id}: {str(e)}")
            return {
                'summary': {},
                'recommendations': [],
                'alerts': [f"Insight generation failed: {str(e)}"],
                'achievements': []
            }
