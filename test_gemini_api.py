#!/usr/bin/env python3
"""
Test script to demonstrate Gemini API interaction
"""

import sys
import os
sys.path.append('.')

from app.ai_race_advisor import AIRaceAdvisor

def test_gemini_api():
    print("Testing Gemini API interaction...")
    
    # Initialize AI advisor
    advisor = AIRaceAdvisor()
    
    # Sample athlete data
    athlete_data = {
        'metrics': {
            'total_distance': 156.3,
            'total_activities': 12,
            'avg_pace': 6.5,
            'avg_heart_rate': 145,
            'training_load': 850
        },
        'performance_summary': {
            'activities': [
                {'distance': 10.2, 'pace': 6.2},
                {'distance': 15.5, 'pace': 6.8},
                {'distance': 8.1, 'pace': 6.0}
            ]
        }
    }
    
    # Current activity
    current_activity = {
        'distance': 12.5,
        'heart_rate': 148,
        'pace': 6.3
    }
    
    print("\n=== INPUT TO GEMINI API ===")
    print(f"Athlete Metrics: {athlete_data['metrics']}")
    print(f"Current Activity: {current_activity}")
    
    # Generate recommendations
    recommendations = advisor.generate_race_recommendations(athlete_data, current_activity)
    
    print("\n=== OUTPUT FROM GEMINI API ===")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    return recommendations

if __name__ == "__main__":
    test_gemini_api()