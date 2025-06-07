import time
import logging
from datetime import datetime, timedelta
from stravalib.client import Client
from stravalib.exc import RateLimitExceeded, AccessUnauthorized
from app.models import StravaApiUsage, SystemLog, db

class ReplitStravaClient:
    """
    Strava API client optimized for Replit environment with comprehensive error handling
    """
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_client = Client()
        self.logger = logging.getLogger(__name__)
    
    def get_authorization_url(self, redirect_uri, scope=['read', 'activity:read']):
        """
        Generate Strava OAuth authorization URL
        """
        try:
            auth_url = self.base_client.authorization_url(
                client_id=self.client_id,
                redirect_uri=redirect_uri,
                scope=scope
            )
            
            self.logger.info(f"Generated authorization URL for redirect_uri: {redirect_uri}")
            return auth_url
            
        except Exception as e:
            self.logger.error(f"Failed to generate authorization URL: {str(e)}")
            raise
    
    def exchange_code_for_token(self, code):
        """
        Exchange authorization code for access tokens
        """
        try:
            token_response = self.base_client.exchange_code_for_token(
                client_id=self.client_id,
                client_secret=self.client_secret,
                code=code
            )
            
            self.logger.info("Successfully exchanged code for tokens")
            
            return {
                'access_token': token_response['access_token'],
                'refresh_token': token_response['refresh_token'],
                'expires_at': datetime.fromtimestamp(token_response['expires_at']),
                'athlete_id': token_response['athlete']['id']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to exchange code for token: {str(e)}")
            raise
    
    def refresh_access_token(self, refresh_token):
        """
        Refresh expired access token using refresh token
        """
        try:
            token_response = self.base_client.refresh_access_token(
                client_id=self.client_id,
                client_secret=self.client_secret,
                refresh_token=refresh_token
            )
            
            self.logger.info("Successfully refreshed access token")
            
            return {
                'access_token': token_response['access_token'],
                'refresh_token': token_response['refresh_token'],
                'expires_at': datetime.fromtimestamp(token_response['expires_at'])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to refresh access token: {str(e)}")
            raise
    
    def get_activities(self, access_token, athlete_id, start_date=None, end_date=None, limit=200):
        """
        Fetch activities for an athlete with comprehensive error handling and rate limiting
        """
        try:
            # Create authenticated client
            athlete_client = Client(access_token=access_token)
            
            # Set default date range if not provided
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            self.logger.info(f"Fetching activities for athlete {athlete_id} from {start_date} to {end_date}")
            
            activities = []
            page_count = 0
            
            try:
                # Use stravalib's iterator with pagination
                for activity in athlete_client.get_activities(
                    before=end_date,
                    after=start_date,
                    limit=limit
                ):
                    activities.append(activity)
                    
                    # Rate limiting delay
                    time.sleep(0.1)
                    
                    # Log progress every 50 activities
                    if len(activities) % 50 == 0:
                        self.logger.info(f"Fetched {len(activities)} activities for athlete {athlete_id}")
                    
                    # Break if we've reached the limit
                    if len(activities) >= limit:
                        break
                
                # Log API usage
                self._log_api_usage(athlete_id, 'get_activities', 200, f"{len(activities)} activities fetched")
                
                self.logger.info(f"Successfully fetched {len(activities)} activities for athlete {athlete_id}")
                return activities
                
            except RateLimitExceeded as e:
                self.logger.warning(f"Rate limit exceeded for athlete {athlete_id}: {str(e)}")
                self._log_api_usage(athlete_id, 'get_activities', 429, "Rate limit exceeded")
                
                # Wait for rate limit reset
                if hasattr(e, 'timeout'):
                    self.logger.info(f"Waiting {e.timeout} seconds for rate limit reset")
                    time.sleep(e.timeout)
                else:
                    # Default wait time
                    time.sleep(900)  # 15 minutes
                
                raise
                
            except AccessUnauthorized as e:
                self.logger.error(f"Access unauthorized for athlete {athlete_id}: {str(e)}")
                self._log_api_usage(athlete_id, 'get_activities', 401, "Access unauthorized")
                raise
                
        except Exception as e:
            self.logger.error(f"Failed to get activities for athlete {athlete_id}: {str(e)}")
            self._log_api_usage(athlete_id, 'get_activities', 500, f"Error: {str(e)}")
            raise
    
    def get_activity_details(self, access_token, activity_id, athlete_id):
        """
        Get detailed information for a specific activity
        """
        try:
            athlete_client = Client(access_token=access_token)
            
            activity = athlete_client.get_activity(activity_id)
            
            # Rate limiting delay
            time.sleep(0.1)
            
            self.logger.info(f"Fetched detailed activity {activity_id} for athlete {athlete_id}")
            self._log_api_usage(athlete_id, 'get_activity_details', 200, f"Activity {activity_id}")
            
            return activity
            
        except Exception as e:
            self.logger.error(f"Failed to get activity details {activity_id} for athlete {athlete_id}: {str(e)}")
            self._log_api_usage(athlete_id, 'get_activity_details', 500, f"Error: {str(e)}")
            raise
    
    def get_athlete_stats(self, access_token, athlete_id):
        """
        Get athlete statistics from Strava
        """
        try:
            athlete_client = Client(access_token=access_token)
            
            stats = athlete_client.get_athlete_stats(athlete_id)
            
            # Rate limiting delay
            time.sleep(0.1)
            
            self.logger.info(f"Fetched stats for athlete {athlete_id}")
            self._log_api_usage(athlete_id, 'get_athlete_stats', 200, "Stats fetched")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get stats for athlete {athlete_id}: {str(e)}")
            self._log_api_usage(athlete_id, 'get_athlete_stats', 500, f"Error: {str(e)}")
            raise
    
    def _log_api_usage(self, athlete_id, endpoint, response_code, details):
        """
        Log API usage for monitoring and debugging
        """
        try:
            api_log = StravaApiUsage(
                athlete_id=athlete_id,
                endpoint=endpoint,
                response_code=response_code,
                rate_limit_usage=details
            )
            db.session.add(api_log)
            db.session.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to log API usage: {str(e)}")
    
    def validate_token(self, access_token):
        """
        Validate if the access token is still valid
        """
        try:
            client = Client(access_token=access_token)
            athlete = client.get_athlete()
            
            self.logger.info(f"Token validation successful for athlete {athlete.id}")
            return True, athlete
            
        except AccessUnauthorized:
            self.logger.warning("Token validation failed: unauthorized")
            return False, None
            
        except Exception as e:
            self.logger.error(f"Token validation error: {str(e)}")
            return False, None
