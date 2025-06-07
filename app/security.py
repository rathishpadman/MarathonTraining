import jwt
import logging
from datetime import datetime, timedelta
from flask import jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

class ReplitSecurity:
    """Security utilities for JWT authentication and authorization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def setup_jwt_handlers(self, jwt_manager):
        """Configure JWT error handlers"""
        
        @jwt_manager.unauthorized_loader
        def unauthorized_callback(callback):
            self.logger.warning("Unauthorized access attempt")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Missing or invalid authentication token'
            }), 401
        
        @jwt_manager.invalid_token_loader
        def invalid_token_callback(callback):
            self.logger.warning(f"Invalid token: {callback}")
            return jsonify({
                'error': 'Invalid Token',
                'message': 'The provided token is invalid'
            }), 401
        
        @jwt_manager.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            self.logger.warning("Expired token used")
            return jsonify({
                'error': 'Token Expired',
                'message': 'The authentication token has expired'
            }), 401
        
        @jwt_manager.revoked_token_loader
        def revoked_token_callback(jwt_header, jwt_payload):
            self.logger.warning("Revoked token used")
            return jsonify({
                'error': 'Token Revoked',
                'message': 'The authentication token has been revoked'
            }), 401
    
    def create_tokens(self, athlete_id):
        """Generate access and refresh tokens for an athlete"""
        try:
            access_token = create_access_token(
                identity=athlete_id,
                expires_delta=timedelta(hours=1)
            )
            refresh_token = create_refresh_token(
                identity=athlete_id,
                expires_delta=timedelta(days=30)
            )
            
            self.logger.info(f"Tokens created for athlete {athlete_id}")
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': 3600  # 1 hour in seconds
            }
        except Exception as e:
            self.logger.error(f"Failed to create tokens for athlete {athlete_id}: {str(e)}")
            raise
    
    def verify_token_identity(self, token, expected_athlete_id):
        """
        Verify token identity matches expected athlete ID.
        Critical for WebSocket authentication.
        """
        try:
            # Decode the token without verification (we'll verify manually)
            decoded_token = decode_token(token)
            token_athlete_id = decoded_token.get('sub')  # 'sub' is the identity claim
            
            if str(token_athlete_id) == str(expected_athlete_id):
                self.logger.info(f"Token verification successful for athlete {expected_athlete_id}")
                return True
            else:
                self.logger.warning(f"Token identity mismatch: expected {expected_athlete_id}, got {token_athlete_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Token verification failed: {str(e)}")
            return False
    
    def validate_athlete_access(self, current_user_id, requested_athlete_id, is_admin=False):
        """
        Validate that the current user can access the requested athlete's data.
        Returns True if access is allowed, False otherwise.
        """
        if is_admin:
            self.logger.info(f"Admin user {current_user_id} accessing athlete {requested_athlete_id}")
            return True
        
        if str(current_user_id) == str(requested_athlete_id):
            self.logger.info(f"Athlete {current_user_id} accessing own data")
            return True
        
        self.logger.warning(f"Access denied: athlete {current_user_id} tried to access athlete {requested_athlete_id}")
        return False
    
    def log_security_event(self, event_type, athlete_id=None, details=None):
        """Log security-related events for monitoring"""
        log_data = {
            'event_type': event_type,
            'athlete_id': athlete_id,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        self.logger.info(f"Security event: {event_type}", extra={'athlete_id': athlete_id})
        
        # In a production environment, you might want to send this to a
        # security monitoring service or store in a separate security log table
