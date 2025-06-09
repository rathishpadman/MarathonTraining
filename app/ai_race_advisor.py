"""
AI-Powered Race Recommendation System using Google Gemini API
Provides intelligent race recommendations based on training data, performance metrics, and physiological indicators.
"""

import os
import json
import logging
import hashlib
from typing import Dict, List, Optional
from google import genai
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

class AIRaceAdvisor:
    """
    AI-powered race recommendation system using Google Gemini API
    """
    
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            logger.warning("GEMINI_API_KEY not found, AI recommendations will use fallback logic")
            self.client = None
        
        # Cache for AI recommendations to ensure consistency
        self._recommendation_cache = {}
        self._cache_duration = timedelta(hours=24)  # Cache for 6 hours
    
    def _create_data_fingerprint(self, athlete_data: Dict, current_activity: Dict) -> str:
        """Create a hash fingerprint of the training data for cache key"""
        try:
            # Create a simplified representation focusing on key metrics
            cache_data = {
                'total_distance': athlete_data.get('metrics', {}).get('total_distance', 0),
                'total_activities': athlete_data.get('metrics', {}).get('total_activities', 0),
                'avg_pace': athlete_data.get('metrics', {}).get('avg_pace', 0),
                'avg_heart_rate': athlete_data.get('metrics', {}).get('avg_heart_rate', 0),
                'current_distance': current_activity.get('distance', 0),
                'current_pace': current_activity.get('pace', 0)
            }
            
            # Create hash of the data
            data_string = json.dumps(cache_data, sort_keys=True)
            return hashlib.md5(data_string.encode()).hexdigest()
        except Exception:
            # If fingerprinting fails, return current timestamp to avoid cache hits
            return str(datetime.now().timestamp())

    def generate_race_recommendations(self, athlete_data: Dict, current_activity: Dict) -> List[str]:
        """
        Generate AI-powered race recommendations based on athlete data and current activity
        
        Args:
            athlete_data: Dictionary containing athlete metrics and performance data
            current_activity: Dictionary containing current activity data (distance, HR, pace)
            
        Returns:
            List of recommendation strings for tooltip display
        """
        try:
            # Create cache key based on data fingerprint
            data_fingerprint = self._create_data_fingerprint(athlete_data, current_activity)
            cache_key = f"recommendations_{data_fingerprint}"
            
            # Check cache first
            if cache_key in self._recommendation_cache:
                cached_entry = self._recommendation_cache[cache_key]
                cache_time = cached_entry['timestamp']
                
                # Check if cache is still valid
                if datetime.now() - cache_time < self._cache_duration:
                    logger.info("Returning cached AI recommendations")
                    return cached_entry['recommendations']
                else:
                    # Cache expired, remove entry
                    del self._recommendation_cache[cache_key]
            
            logger.info(f"Generating new AI recommendations for athlete data")
            
            if self.client:
                # Try AI-powered recommendations first
                recommendations = self._generate_ai_recommendations(athlete_data, current_activity)
                if recommendations:
                    # Cache the successful AI recommendations
                    self._recommendation_cache[cache_key] = {
                        'recommendations': recommendations,
                        'timestamp': datetime.now()
                    }
                    return recommendations
            
            # Fallback to rule-based recommendations
            fallback_recommendations = self._generate_fallback_recommendations(athlete_data, current_activity)
            
            # Cache fallback recommendations with shorter duration
            self._recommendation_cache[cache_key] = {
                'recommendations': fallback_recommendations,
                'timestamp': datetime.now()
            }
            
            return fallback_recommendations
            
        except Exception as e:
            logger.error(f"Error generating race recommendations: {str(e)}")
            return self._generate_fallback_recommendations(athlete_data, current_activity)
    
    def _generate_ai_recommendations(self, athlete_data: Dict, current_activity: Dict) -> List[str]:
        """Generate recommendations using Gemini AI"""
        try:
            # Prepare training context
            metrics = athlete_data.get('metrics', {})
            activities = athlete_data.get('performance_summary', {}).get('activities', [])
            
            # Create comprehensive training profile
            training_profile = {
                'total_distance_30days': metrics.get('total_distance', 0),
                'total_activities_30days': metrics.get('total_activities', 0),
                'avg_pace_min_per_km': metrics.get('avg_pace', 0),
                'avg_heart_rate': metrics.get('avg_heart_rate', 0),
                'training_load': metrics.get('training_load', 0),
                'current_activity': {
                    'distance_km': current_activity.get('distance', 0),
                    'heart_rate': current_activity.get('heart_rate', 0),
                    'estimated_pace': current_activity.get('pace', metrics.get('avg_pace', 7.0))
                },
                'recent_activities_count': len(activities),
                'weekly_avg_distance': metrics.get('total_distance', 0) / 4.3  # Convert monthly to weekly
            }
            
            # Create AI prompt for race recommendations
            prompt = f"""
            As an enthusiastic marathon coach, analyze this runner's data and provide encouraging, personalized race recommendations.
            
            Training Profile:
            - Total distance (30 days): {training_profile['total_distance_30days']:.1f} km
            - Activities (30 days): {training_profile['total_activities_30days']}
            - Average pace: {training_profile['avg_pace_min_per_km']:.2f} min/km
            - Average heart rate: {training_profile['avg_heart_rate']:.0f} bpm
            - Training load: {training_profile['training_load']:.0f}
            - Weekly average: {training_profile['weekly_avg_distance']:.1f} km/week
            
            Current Activity:
            - Distance: {training_profile['current_activity']['distance_km']:.1f} km
            - Heart rate: {training_profile['current_activity']['heart_rate']:.0f} bpm
            - Pace: {training_profile['current_activity']['estimated_pace']:.2f} min/km
            
            Provide 4-6 encouraging and specific recommendations:
            1. Optimal race distance for next 4-6 weeks
            2. Training focus areas  
            3. Predicted race times (be encouraging but realistic)
            4. Recovery and injury prevention advice
            5. Long-term goals
            6. Next training phase recommendations
            
            Keep each recommendation to 1-2 sentences, actionable, and motivating.
            Use emojis strategically for visual appeal.
            Be enthusiastic and supportive while staying data-driven.
            """
            
            # Log the prompt being sent to Gemini
            logger.info(f"Sending prompt to Gemini API: {prompt[:200]}...")
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            
            # Log the full response from Gemini
            logger.info(f"Gemini API Response: {response.text if response else 'No response'}")
            
            # Parse AI response into list of recommendations
            recommendations = []
            if response and response.text:
                lines = response.text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Clean up numbered list formatting
                        if line[0].isdigit() and '.' in line[:3]:
                            line = line[line.find('.') + 1:].strip()
                        if line:
                            recommendations.append(line)
            
            # Ensure we have at least 3 recommendations
            if len(recommendations) < 3:
                return self._generate_fallback_recommendations(athlete_data, current_activity)
            
            return recommendations[:6]  # Limit to 6 recommendations for tooltip
            
        except Exception as e:
            logger.error(f"Error with Gemini AI recommendations: {str(e)}")
            return self._generate_fallback_recommendations(athlete_data, current_activity)
    
    def _generate_fallback_recommendations(self, athlete_data: Dict, current_activity: Dict) -> List[str]:
        """Generate recommendations using rule-based logic when AI is unavailable"""
        metrics = athlete_data.get('metrics', {})
        recommendations = []
        
        # Calculate readiness metrics
        weekly_distance = metrics.get('total_distance', 0) / 4.3
        avg_pace = metrics.get('avg_pace', 7.0)
        training_load = metrics.get('training_load', 0)
        current_distance = current_activity.get('distance', 0)
        current_hr = current_activity.get('heart_rate', metrics.get('avg_heart_rate', 150))
        
        # Race distance recommendations
        if weekly_distance >= 50 and avg_pace <= 5.5:
            recommendations.append("🏆 Marathon ready! Consider 42.2K race within 8-12 weeks")
        elif weekly_distance >= 35 and avg_pace <= 6.0:
            recommendations.append("🏃‍♂️ Half Marathon optimal (21.1K) - excellent fitness base")
        elif weekly_distance >= 20 and avg_pace <= 7.0:
            recommendations.append("🎯 10K race ready - perfect distance for current fitness")
        else:
            recommendations.append("⚡ 5K focus recommended - build weekly volume first")
        
        # Training intensity analysis
        max_hr_estimated = 220 - 30  # Assume 30 years old
        hr_intensity = (current_hr / max_hr_estimated) * 100
        
        if hr_intensity < 70:
            recommendations.append("💚 Excellent aerobic efficiency - maintain this zone")
        elif hr_intensity < 85:
            recommendations.append("🟡 Moderate intensity - good for tempo training")
        else:
            recommendations.append("🔴 High intensity detected - ensure adequate recovery")
        
        # Performance predictions
        predicted_5k = self._predict_race_time(5, avg_pace)
        predicted_10k = self._predict_race_time(10, avg_pace)
        
        recommendations.append(f"🎯 Predicted times: 5K {predicted_5k}, 10K {predicted_10k}")
        
        # Training load assessment
        if training_load > 800:
            recommendations.append("📈 High training load - consider recovery week")
        elif training_load > 400:
            recommendations.append("🔄 Solid training volume - maintain consistency")
        else:
            recommendations.append("📊 Build training volume gradually for better fitness")
        
        return recommendations
    
    def _predict_race_time(self, distance_km: float, avg_pace_min_km: float) -> str:
        """Predict race time based on training pace and distance"""
        # Apply race effort factor (races are typically faster than training pace)
        race_factor = 1.0 - (0.02 * min(distance_km / 5, 4))  # Up to 8% faster for shorter races
        race_pace = avg_pace_min_km * race_factor
        
        total_minutes = race_pace * distance_km
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        seconds = int((total_minutes % 1) * 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

# Global instance
ai_race_advisor = AIRaceAdvisor()

def get_race_recommendations(athlete_data: Dict, current_activity: Dict) -> List[str]:
    """
    Global function to get AI race recommendations
    
    Args:
        athlete_data: Complete athlete data including metrics and activities
        current_activity: Current activity data (distance, heart_rate, pace)
        
    Returns:
        List of recommendation strings
    """
    return ai_race_advisor.generate_race_recommendations(athlete_data, current_activity)