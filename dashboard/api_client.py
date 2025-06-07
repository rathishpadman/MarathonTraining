import requests
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import streamlit as st

class APIClient:
    """
    Client for communicating with the Flask backend API
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
        # Set up session headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to the API with error handling
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Log request details
            self.logger.info(f"{method} {url} - Status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json() if response.content else {}
            elif response.status_code == 401:
                self.logger.warning("Authentication required")
                return {'error': 'Authentication required', 'status_code': 401}
            elif response.status_code == 403:
                self.logger.warning("Access forbidden")
                return {'error': 'Access forbidden', 'status_code': 403}
            elif response.status_code == 404:
                self.logger.warning(f"Endpoint not found: {url}")
                return {'error': 'Not found', 'status_code': 404}
            else:
                self.logger.error(f"API request failed: {response.status_code}")
                try:
                    error_data = response.json()
                    return {'error': error_data.get('message', 'Unknown error'), 'status_code': response.status_code}
                except:
                    return {'error': f'HTTP {response.status_code}', 'status_code': response.status_code}
        
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Connection error to {url}")
            return {'error': 'Connection error - Backend may not be running', 'status_code': 0}
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout error for {url}")
            return {'error': 'Request timeout', 'status_code': 0}
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return {'error': f'Unexpected error: {str(e)}', 'status_code': 0}
    
    def get_athlete_list(self) -> List[str]:
        """
        Get list of athlete names for dropdown selection
        """
        try:
            # First try to get from API
            response = self._make_request('GET', '/api/athletes')
            
            if 'error' not in response and isinstance(response, list):
                athlete_names = ["Team Overview"]  # Always include team overview
                for athlete in response:
                    if isinstance(athlete, dict) and 'name' in athlete:
                        athlete_names.append(athlete['name'])
                return athlete_names
            
            # Fallback: Return default options if API is not available
            self.logger.warning("Using fallback athlete list")
            return ["Team Overview", "Demo Athlete 1", "Demo Athlete 2"]
            
        except Exception as e:
            self.logger.error(f"Error getting athlete list: {str(e)}")
            return ["Team Overview"]
    
    def get_athlete_id_by_name(self, athlete_name: str) -> Optional[int]:
        """
        Get athlete ID by name
        """
        try:
            response = self._make_request('GET', '/api/athletes')
            
            if 'error' not in response and isinstance(response, list):
                for athlete in response:
                    if isinstance(athlete, dict) and athlete.get('name') == athlete_name:
                        return athlete.get('id')
            
            # For demo purposes, return a mock ID
            self.logger.warning(f"Athlete '{athlete_name}' not found, using demo ID")
            return 1
            
        except Exception as e:
            self.logger.error(f"Error getting athlete ID: {str(e)}")
            return None
    
    def get_athlete_dashboard_data(self, athlete_id: int) -> Dict[str, Any]:
        """
        Get dashboard data for a specific athlete
        """
        try:
            response = self._make_request('GET', f'/api/athletes/{athlete_id}/dashboard-data')
            
            if 'error' in response:
                self.logger.warning(f"Error getting dashboard data: {response['error']}")
                return {}
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data for athlete {athlete_id}: {str(e)}")
            return {}
    
    def get_athlete_performance_summary(self, athlete_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get performance summary for an athlete
        """
        try:
            # Try to get real data from API
            response = self._make_request('GET', f'/api/athletes/{athlete_id}/dashboard-data')
            
            if 'error' not in response and response:
                # Process the dashboard data into performance summary format
                return self._process_dashboard_data_to_summary(response, days)
            
            # Fallback: Return empty structure if no real data
            self.logger.warning(f"No performance data available for athlete {athlete_id}")
            return {
                'period': f"Last {days} days",
                'total_distance': 0,
                'total_activities': 0,
                'total_training_time': 0,
                'average_weekly_distance': 0,
                'average_pace': None,
                'total_elevation_gain': 0,
                'training_load': 0,
                'active_days': 0,
                'recent_summaries': []
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {str(e)}")
            return {}
    
    def get_team_overview(self, days: int = 7) -> Dict[str, Any]:
        """
        Get team overview data
        """
        try:
            # Try to get athletes list first
            athletes_response = self._make_request('GET', '/api/athletes')
            
            if 'error' not in athletes_response and isinstance(athletes_response, list):
                # Process team data
                team_data = {
                    'period': f"Last {days} days",
                    'total_athletes': len(athletes_response),
                    'total_team_distance': 0,
                    'total_team_activities': 0,
                    'average_distance_per_athlete': 0,
                    'athlete_details': []
                }
                
                total_distance = 0
                total_activities = 0
                
                for athlete in athletes_response:
                    athlete_id = athlete.get('id')
                    athlete_name = athlete.get('name')
                    
                    # Get individual athlete data
                    athlete_summary = self.get_athlete_performance_summary(athlete_id, days)
                    
                    athlete_detail = {
                        'athlete_id': athlete_id,
                        'athlete_name': athlete_name,
                        'total_distance': athlete_summary.get('total_distance', 0),
                        'total_activities': athlete_summary.get('total_activities', 0),
                        'active_days': athlete_summary.get('active_days', 0),
                        'latest_status': 'Active' if athlete_summary.get('total_activities', 0) > 0 else 'No Recent Activity'
                    }
                    
                    team_data['athlete_details'].append(athlete_detail)
                    total_distance += athlete_detail['total_distance']
                    total_activities += athlete_detail['total_activities']
                
                team_data['total_team_distance'] = total_distance
                team_data['total_team_activities'] = total_activities
                team_data['average_distance_per_athlete'] = total_distance / len(athletes_response) if athletes_response else 0
                
                if team_data['athlete_details']:
                    most_active = max(team_data['athlete_details'], key=lambda x: x['total_distance'])
                    team_data['most_active_athlete'] = most_active['athlete_name']
                
                return team_data
            
            # Fallback team data
            self.logger.warning("Using fallback team data")
            return {
                'period': f"Last {days} days",
                'total_athletes': 0,
                'message': 'No team data available - Backend may not be running'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting team overview: {str(e)}")
            return {
                'period': f"Last {days} days",
                'total_athletes': 0,
                'message': f'Error loading team data: {str(e)}'
            }
    
    def get_upcoming_workouts(self, athlete_id: int) -> List[Dict[str, Any]]:
        """
        Get upcoming workouts for an athlete
        """
        try:
            # This would be a real API call in production
            response = self._make_request('GET', f'/api/athletes/{athlete_id}/workouts')
            
            if 'error' not in response and isinstance(response, list):
                return response
            
            # Fallback: Return empty list
            self.logger.warning(f"No upcoming workouts found for athlete {athlete_id}")
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting upcoming workouts: {str(e)}")
            return []
    
    def get_real_time_data(self, athlete_id: int) -> Dict[str, Any]:
        """
        Get real-time data for an athlete
        """
        try:
            response = self._make_request('GET', f'/api/realtime/dashboard')
            
            if 'error' not in response:
                return response
            
            # Return empty real-time data if API not available
            return {
                'timestamp': datetime.now().isoformat(),
                'athlete_id': athlete_id,
                'performance': {},
                'upcoming': [],
                'notifications': []
            }
            
        except Exception as e:
            self.logger.error(f"Error getting real-time data: {str(e)}")
            return {}
    
    def authenticate_strava(self, code: str) -> Dict[str, Any]:
        """
        Authenticate with Strava using authorization code
        """
        try:
            payload = {'code': code}
            response = self._make_request('POST', '/api/auth/strava/callback', json=payload)
            
            if 'error' not in response:
                # Store authentication tokens if needed
                if 'tokens' in response:
                    self._store_auth_tokens(response['tokens'])
                return response
            
            return {'error': response.get('error', 'Authentication failed')}
            
        except Exception as e:
            self.logger.error(f"Error during Strava authentication: {str(e)}")
            return {'error': f'Authentication error: {str(e)}'}
    
    def get_strava_auth_url(self, redirect_uri: str = None) -> str:
        """
        Get Strava authorization URL
        """
        try:
            params = {}
            if redirect_uri:
                params['redirect_uri'] = redirect_uri
            
            response = self._make_request('GET', '/api/auth/strava/authorize', params=params)
            
            if 'error' not in response and 'authorization_url' in response:
                return response['authorization_url']
            
            # Return fallback URL
            return "https://strava.com/oauth/authorize"
            
        except Exception as e:
            self.logger.error(f"Error getting Strava auth URL: {str(e)}")
            return "https://strava.com/oauth/authorize"
    
    def _process_dashboard_data_to_summary(self, dashboard_data: List[Dict], days: int) -> Dict[str, Any]:
        """
        Process dashboard data into performance summary format
        """
        if not dashboard_data:
            return {}
        
        try:
            # Calculate aggregated metrics from dashboard data
            total_distance = sum(item.get('total_distance', 0) for item in dashboard_data)
            total_activities = sum(item.get('activity_count', 0) for item in dashboard_data)
            total_time = sum(item.get('total_moving_time', 0) for item in dashboard_data)
            total_load = sum(item.get('training_load', 0) for item in dashboard_data if item.get('training_load'))
            
            # Count active days
            active_days = len([item for item in dashboard_data if item.get('activity_count', 0) > 0])
            
            # Calculate average pace
            pace_values = [item.get('average_pace') for item in dashboard_data if item.get('average_pace')]
            avg_pace = sum(pace_values) / len(pace_values) if pace_values else None
            
            # Prepare recent summaries (last 7 days)
            recent_summaries = []
            for item in dashboard_data[:7]:  # Take first 7 items
                summary = {
                    'date': item.get('summary_date', datetime.now().isoformat()),
                    'distance': item.get('total_distance', 0),
                    'moving_time': item.get('total_moving_time', 0),
                    'activity_count': item.get('activity_count', 0),
                    'training_load': item.get('training_load', 0),
                    'status': item.get('status', 'Unknown'),
                    'pace': item.get('average_pace')
                }
                recent_summaries.append(summary)
            
            return {
                'period': f"Last {days} days",
                'total_distance': total_distance,
                'total_activities': total_activities,
                'total_training_time': total_time,
                'average_weekly_distance': total_distance * 7 / days if days > 0 else 0,
                'average_pace': avg_pace,
                'total_elevation_gain': 0,  # Not available in current data
                'training_load': total_load,
                'active_days': active_days,
                'recent_summaries': recent_summaries
            }
            
        except Exception as e:
            self.logger.error(f"Error processing dashboard data: {str(e)}")
            return {}
    
    def _store_auth_tokens(self, tokens: Dict[str, str]):
        """
        Store authentication tokens in Streamlit session state
        """
        try:
            if 'auth_tokens' not in st.session_state:
                st.session_state.auth_tokens = {}
            
            st.session_state.auth_tokens.update(tokens)
            
            # Update session headers with access token
            if 'access_token' in tokens:
                self.session.headers['Authorization'] = f"Bearer {tokens['access_token']}"
            
            self.logger.info("Authentication tokens stored successfully")
            
        except Exception as e:
            self.logger.error(f"Error storing auth tokens: {str(e)}")
    
    def set_auth_token(self, token: str):
        """
        Set authentication token for API requests
        """
        self.session.headers['Authorization'] = f"Bearer {token}"
    
    def check_backend_health(self) -> bool:
        """
        Check if the backend is healthy and responding
        """
        try:
            response = self._make_request('GET', '/api/athletes')
            return 'error' not in response or response.get('status_code') != 0
        except:
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get connection status information
        """
        try:
            is_healthy = self.check_backend_health()
            return {
                'connected': is_healthy,
                'status': 'Connected' if is_healthy else 'Disconnected',
                'backend_url': self.base_url,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'connected': False,
                'status': 'Error',
                'error': str(e),
                'backend_url': self.base_url,
                'timestamp': datetime.now().isoformat()
            }
