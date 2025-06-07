import smtplib
import logging
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime
from app.models import NotificationLog, db

class MailNotifier:
    """
    Email notification service for sending daily summaries and alerts to athletes
    """
    
    def __init__(self, smtp_server, smtp_port, smtp_user, smtp_password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.logger = logging.getLogger(__name__)
    
    def send_daily_summary(self, athlete_id, recipient_email, summary_data):
        """
        Send personalized daily summary email to an athlete
        """
        try:
            self.logger.info(f"Preparing daily summary email for athlete {athlete_id}")
            
            # Create email content
            subject = f"Marathon Training Daily Summary - {summary_data.get('date', 'Today')}"
            html_content = self._create_daily_summary_html(summary_data)
            text_content = self._create_daily_summary_text(summary_data)
            
            # Send email
            success = self._send_email(
                recipient_email=recipient_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            # Log notification attempt
            self._log_notification(
                athlete_id=athlete_id,
                notification_type='email',
                subject=subject,
                message=text_content[:500],  # First 500 characters
                status='sent' if success else 'failed',
                error_message=None if success else "Failed to send email"
            )
            
            if success:
                self.logger.info(f"Daily summary email sent successfully to athlete {athlete_id}")
            else:
                self.logger.error(f"Failed to send daily summary email to athlete {athlete_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary to athlete {athlete_id}: {str(e)}")
            
            # Log failed notification
            self._log_notification(
                athlete_id=athlete_id,
                notification_type='email',
                subject=subject if 'subject' in locals() else "Daily Summary",
                message="",
                status='failed',
                error_message=str(e)
            )
            
            return False
    
    def send_alert_notification(self, athlete_id, recipient_email, alert_type, alert_message):
        """
        Send alert notification to an athlete
        """
        try:
            self.logger.info(f"Sending alert notification to athlete {athlete_id}: {alert_type}")
            
            subject = f"Marathon Training Alert - {alert_type}"
            html_content = self._create_alert_html(alert_type, alert_message)
            text_content = self._create_alert_text(alert_type, alert_message)
            
            success = self._send_email(
                recipient_email=recipient_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            # Log notification attempt
            self._log_notification(
                athlete_id=athlete_id,
                notification_type='email_alert',
                subject=subject,
                message=alert_message,
                status='sent' if success else 'failed',
                error_message=None if success else "Failed to send alert"
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending alert to athlete {athlete_id}: {str(e)}")
            return False
    
    def _send_email(self, recipient_email, subject, html_content, text_content):
        """
        Send email using SMTP with comprehensive error handling
        """
        try:
            # Create message
            msg = MimeMultipart('alternative')
            msg['From'] = self.smtp_user
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Attach text and HTML parts
            text_part = MimeText(text_content, 'plain')
            html_part = MimeText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable encryption
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP authentication failed: {str(e)}")
            return False
            
        except smtplib.SMTPRecipientsRefused as e:
            self.logger.error(f"Recipient refused: {str(e)}")
            return False
            
        except smtplib.SMTPConnectError as e:
            self.logger.error(f"SMTP connection error: {str(e)}")
            return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error sending email: {str(e)}")
            return False
    
    def _create_daily_summary_html(self, summary_data):
        """Create HTML content for daily summary email"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 20px; border-radius: 10px; text-align: center; }}
                .metrics {{ display: flex; flex-wrap: wrap; gap: 15px; margin: 20px 0; }}
                .metric {{ background: #f8f9fa; padding: 15px; border-radius: 8px; flex: 1; min-width: 150px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                .metric-label {{ font-size: 14px; color: #666; }}
                .status {{ padding: 10px; border-radius: 5px; margin: 15px 0; }}
                .status.on-track {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
                .status.warning {{ background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }}
                .status.alert {{ background: #f8d7da; border: 1px solid #f1c0c7; color: #721c24; }}
                .insights {{ background: #e9ecef; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏃‍♀️ Daily Training Summary</h1>
                    <p>{summary_data.get('date', datetime.now().strftime('%Y-%m-%d'))}</p>
                </div>
                
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{summary_data.get('total_distance', 0) / 1000:.1f}</div>
                        <div class="metric-label">Distance (km)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{summary_data.get('total_moving_time', 0) // 60}</div>
                        <div class="metric-label">Time (min)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{summary_data.get('activity_count', 0)}</div>
                        <div class="metric-label">Activities</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{summary_data.get('training_load', 0):.0f}</div>
                        <div class="metric-label">Training Load</div>
                    </div>
                </div>
                
                <div class="status {'on-track' if summary_data.get('status') == 'On Track' else 'warning' if 'Under' in summary_data.get('status', '') else 'alert'}">
                    <strong>Status:</strong> {summary_data.get('status', 'Unknown')}
                </div>
                
                <div class="insights">
                    <h3>Today's Insights</h3>
                    <ul>
        """
        
        # Add insights if available
        insights = summary_data.get('insights', {})
        for note in insights.get('performance_notes', []):
            html += f"<li>{note}</li>"
        for recommendation in insights.get('recommendations', []):
            html += f"<li><strong>Recommendation:</strong> {recommendation}</li>"
        for alert in insights.get('alerts', []):
            html += f"<li><strong>Alert:</strong> {alert}</li>"
        
        html += """
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p>Keep up the great work! 💪</p>
                    <p><small>Marathon Training Dashboard</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_daily_summary_text(self, summary_data):
        """Create plain text content for daily summary email"""
        text = f"""
Marathon Training Daily Summary
{summary_data.get('date', datetime.now().strftime('%Y-%m-%d'))}
===============================================

Training Metrics:
- Distance: {summary_data.get('total_distance', 0) / 1000:.1f} km
- Time: {summary_data.get('total_moving_time', 0) // 60} minutes
- Activities: {summary_data.get('activity_count', 0)}
- Training Load: {summary_data.get('training_load', 0):.0f}

Status: {summary_data.get('status', 'Unknown')}

Today's Insights:
"""
        
        insights = summary_data.get('insights', {})
        for note in insights.get('performance_notes', []):
            text += f"• {note}\n"
        for recommendation in insights.get('recommendations', []):
            text += f"• Recommendation: {recommendation}\n"
        for alert in insights.get('alerts', []):
            text += f"• Alert: {alert}\n"
        
        text += "\nKeep up the great work!\nMarathon Training Dashboard"
        
        return text
    
    def _create_alert_html(self, alert_type, alert_message):
        """Create HTML content for alert email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .alert-header {{ background: #dc3545; color: white; padding: 20px; border-radius: 10px; text-align: center; }}
                .alert-content {{ background: #f8d7da; border: 1px solid #f1c0c7; color: #721c24; 
                                padding: 20px; border-radius: 8px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="alert-header">
                    <h1>⚠️ Training Alert</h1>
                    <p>{alert_type}</p>
                </div>
                <div class="alert-content">
                    <p>{alert_message}</p>
                </div>
                <p><small>Marathon Training Dashboard</small></p>
            </div>
        </body>
        </html>
        """
    
    def _create_alert_text(self, alert_type, alert_message):
        """Create plain text content for alert email"""
        return f"""
Marathon Training Alert
{alert_type}
========================

{alert_message}

Marathon Training Dashboard
        """
    
    def _log_notification(self, athlete_id, notification_type, subject, message, status, error_message=None):
        """Log notification attempt to database"""
        try:
            notification_log = NotificationLog(
                athlete_id=athlete_id,
                notification_type=notification_type,
                subject=subject,
                message=message,
                status=status,
                error_message=error_message
            )
            
            db.session.add(notification_log)
            db.session.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to log notification: {str(e)}")
    
    def test_connection(self):
        """Test SMTP connection and authentication"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
            
            self.logger.info("SMTP connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP connection test failed: {str(e)}")
            return False
