import os
import requests
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class ReplitStravaClient:
    """Strava API client for Marathon Training Dashboard"""
    
    def __init__(self, client_id=None, client_secret=None):
        self.client_id = client_id or os.environ.get('STRAVA_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('STRAVA_CLIENT_SECRET')
        self.base_url = "https://www.strava.com/api/v3"
        self.auth_url = "https://www.strava.com/oauth/authorize"
        self.token_url = "https://www.strava.com/oauth/token"
        
        if not self.client_id or not self.client_secret:
            logger.error("Strava client ID and secret are required")
    
    def get_authorization_url(self, redirect_uri, scope="read,activity:read"):
        """Generate Strava authorization URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': scope,
            'approval_prompt': 'auto'
        }
        
        auth_url = f"{self.auth_url}?{urlencode(params)}"
        logger.info(f"Generated Strava auth URL: {auth_url}")
        return auth_url
    
    def exchange_token(self, code, redirect_uri):
        """Exchange authorization code for access token"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            }
            
            response = requests.post(self.token_url, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            logger.info("Successfully exchanged code for tokens")
            
            return {
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'expires_at': token_data.get('expires_at')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error exchanging token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in token exchange: {str(e)}")
            return None
    
    def get_athlete_info(self, access_token):
        """Get athlete information from Strava"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(f"{self.base_url}/athlete", headers=headers, timeout=30)
            response.raise_for_status()
            
            athlete_data = response.json()
            logger.info(f"Retrieved athlete info for ID: {athlete_data.get('id')}")
            
            return athlete_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting athlete info: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting athlete info: {str(e)}")
            return None
    
    def get_activities(self, access_token, per_page=30, page=1):
        """Get athlete activities from Strava"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            params = {'per_page': per_page, 'page': page}
            
            response = requests.get(
                f"{self.base_url}/athlete/activities", 
                headers=headers, 
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            activities = response.json()
            logger.info(f"Retrieved {len(activities)} activities")
            
            return activities
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting activities: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting activities: {str(e)}")
            return []
    
    def refresh_access_token(self, refresh_token):
        """Refresh access token using refresh token"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(self.token_url, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            logger.info("Successfully refreshed access token")
            
            return {
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'expires_at': token_data.get('expires_at')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error refreshing token: {str(e)}")
            return None