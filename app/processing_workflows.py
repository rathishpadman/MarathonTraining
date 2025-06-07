import logging
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models import ReplitAthlete, db
from app.data_processor import process_athlete_daily_performance
from app.mail_notifier import MailNotifier
from app.config import Config

class ProcessingWorkflows:
    """
    Advanced processing workflows for multi-athlete data processing
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
    
    def get_athletes_in_chunks(self, db_session_factory, chunk_size=50):
        """
        Fetch active athletes in memory-managed chunks for scalability
        """
        try:
            self.logger.info(f"Fetching athletes in chunks of {chunk_size}")
            
            # Create a new session for this operation
            session = db_session_factory()
            
            try:
                # Get total count
                total_athletes = session.query(ReplitAthlete).filter_by(is_active=True).count()
                self.logger.info(f"Total active athletes: {total_athletes}")
                
                # Yield athletes in chunks
                offset = 0
                while offset < total_athletes:
                    athletes = session.query(ReplitAthlete).filter_by(is_active=True)\
                                    .offset(offset).limit(chunk_size).all()
                    
                    if not athletes:
                        break
                    
                    # Convert to dictionaries to avoid ORM session issues across threads
                    athlete_dicts = []
                    for athlete in athletes:
                        athlete_dicts.append({
                            'id': athlete.id,
                            'name': athlete.name,
                            'email': athlete.email,
                            'strava_athlete_id': athlete.strava_athlete_id,
                            'preferences': athlete.get_preferences()
                        })
                    
                    self.logger.info(f"Yielding chunk of {len(athlete_dicts)} athletes (offset: {offset})")
                    yield athlete_dicts
                    
                    offset += chunk_size
                    
            finally:
                session.close()
                
        except Exception as e:
            self.logger.error(f"Error fetching athletes in chunks: {str(e)}")
            raise
    
    def process_single_athlete_workflow(self, athlete_data, processing_date, mail_notifier):
        """
        Process a single athlete's data workflow.
        This function runs independently in a ThreadPoolExecutor.
        """
        athlete_id = athlete_data['id']
        athlete_name = athlete_data['name']
        athlete_email = athlete_data['email']
        preferences = athlete_data['preferences']
        
        # Create a new database session for this thread
        engine = create_engine(self.config.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db_session = Session()
        
        try:
            self.logger.info(f"Starting workflow for athlete {athlete_id} ({athlete_name})")
            
            # Process daily performance
            daily_summary = process_athlete_daily_performance(
                db_session, athlete_id, processing_date
            )
            
            if daily_summary:
                self.logger.info(f"Daily summary created for athlete {athlete_id}: {daily_summary.status}")
                
                # Check if athlete wants daily summary notifications
                if preferences.get('notification_daily_summary', False):
                    self.logger.info(f"Sending daily summary notification to athlete {athlete_id}")
                    
                    # Prepare summary data for email
                    summary_data = {
                        'date': processing_date.strftime('%Y-%m-%d'),
                        'total_distance': daily_summary.total_distance,
                        'total_moving_time': daily_summary.total_moving_time,
                        'activity_count': daily_summary.activity_count,
                        'training_load': daily_summary.training_load,
                        'status': daily_summary.status,
                        'insights': daily_summary.get_insights()
                    }
                    
                    # Send email notification
                    try:
                        email_sent = mail_notifier.send_daily_summary(
                            athlete_id=athlete_id,
                            recipient_email=athlete_email,
                            summary_data=summary_data
                        )
                        
                        if email_sent:
                            self.logger.info(f"Daily summary email sent to athlete {athlete_id}")
                        else:
                            self.logger.warning(f"Failed to send daily summary email to athlete {athlete_id}")
                            
                    except Exception as email_error:
                        self.logger.error(f"Error sending email to athlete {athlete_id}: {str(email_error)}")
                
                else:
                    self.logger.info(f"Athlete {athlete_id} has email notifications disabled")
            
            else:
                self.logger.warning(f"No daily summary created for athlete {athlete_id}")
            
            # Log successful completion
            from app.models import SystemLog
            success_log = SystemLog(
                level='INFO',
                message=f"Workflow completed successfully for athlete {athlete_name}",
                module='processing_workflows',
                athlete_id=athlete_id
            )
            success_log.set_context({
                'processing_date': processing_date.isoformat(),
                'summary_created': daily_summary is not None,
                'email_enabled': preferences.get('notification_daily_summary', False)
            })
            
            db_session.add(success_log)
            db_session.commit()
            
            return {
                'athlete_id': athlete_id,
                'status': 'success',
                'summary_created': daily_summary is not None
            }
            
        except Exception as e:
            self.logger.error(f"Error processing athlete {athlete_id} ({athlete_name}): {str(e)}")
            
            # Rollback any database changes
            db_session.rollback()
            
            # Log error to database
            try:
                from app.models import SystemLog
                error_log = SystemLog(
                    level='ERROR',
                    message=f"Workflow error for athlete {athlete_name}: {str(e)}",
                    module='processing_workflows',
                    athlete_id=athlete_id
                )
                error_log.set_context({
                    'processing_date': processing_date.isoformat(),
                    'error_type': type(e).__name__,
                    'error_details': str(e)
                })
                
                db_session.add(error_log)
                db_session.commit()
                
            except Exception as log_error:
                self.logger.error(f"Failed to log error for athlete {athlete_id}: {str(log_error)}")
            
            return {
                'athlete_id': athlete_id,
                'status': 'error',
                'error': str(e)
            }
            
        finally:
            # Always close the database session
            db_session.close()
    
    def replit_daily_processing(self, processing_date):
        """
        Orchestrate daily processing for all active athletes using parallel processing
        """
        try:
            self.logger.info(f"Starting daily processing for {processing_date}")
            
            # Initialize mail notifier once
            mail_notifier = MailNotifier(
                smtp_server=self.config.MAIL_SMTP_SERVER,
                smtp_port=self.config.MAIL_SMTP_PORT,
                smtp_user=self.config.MAIL_SMTP_USER,
                smtp_password=self.config.MAIL_SMTP_PASSWORD
            )
            
            # Test mail connection
            if not mail_notifier.test_connection():
                self.logger.warning("Mail connection test failed - notifications may not work")
            
            # Create database session factory
            engine = create_engine(self.config.DATABASE_URL)
            SessionFactory = sessionmaker(bind=engine)
            
            # Determine number of workers based on CPU count
            max_workers = min(os.cpu_count() or 4, 10)  # Cap at 10 workers
            self.logger.info(f"Using {max_workers} worker threads for processing")
            
            processed_count = 0
            success_count = 0
            error_count = 0
            
            # Process athletes in chunks to manage memory
            for athlete_chunk in self.get_athletes_in_chunks(SessionFactory, chunk_size=50):
                self.logger.info(f"Processing chunk of {len(athlete_chunk)} athletes")
                
                # Use ThreadPoolExecutor for parallel processing
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all athlete processing tasks
                    future_to_athlete = {
                        executor.submit(
                            self.process_single_athlete_workflow,
                            athlete_data,
                            processing_date,
                            mail_notifier
                        ): athlete_data['id'] for athlete_data in athlete_chunk
                    }
                    
                    # Process completed tasks
                    for future in as_completed(future_to_athlete):
                        athlete_id = future_to_athlete[future]
                        processed_count += 1
                        
                        try:
                            result = future.result()
                            if result['status'] == 'success':
                                success_count += 1
                                self.logger.info(f"Successfully processed athlete {athlete_id}")
                            else:
                                error_count += 1
                                self.logger.error(f"Failed to process athlete {athlete_id}: {result.get('error', 'Unknown error')}")
                                
                        except Exception as e:
                            error_count += 1
                            self.logger.error(f"Exception processing athlete {athlete_id}: {str(e)}")
            
            # Log final results
            self.logger.info(f"Daily processing completed for {processing_date}")
            self.logger.info(f"Total processed: {processed_count}, Success: {success_count}, Errors: {error_count}")
            
            # Log completion to database
            session = SessionFactory()
            try:
                from app.models import SystemLog
                completion_log = SystemLog(
                    level='INFO',
                    message=f"Daily processing completed",
                    module='processing_workflows',
                    athlete_id=None
                )
                completion_log.set_context({
                    'processing_date': processing_date.isoformat(),
                    'total_processed': processed_count,
                    'success_count': success_count,
                    'error_count': error_count,
                    'workers_used': max_workers
                })
                
                session.add(completion_log)
                session.commit()
                
            finally:
                session.close()
            
            return {
                'status': 'completed',
                'total_processed': processed_count,
                'success_count': success_count,
                'error_count': error_count
            }
            
        except Exception as e:
            self.logger.error(f"Critical error in daily processing: {str(e)}")
            
            # Log critical error
            session = SessionFactory()
            try:
                from app.models import SystemLog
                critical_log = SystemLog(
                    level='ERROR',
                    message=f"Critical error in daily processing: {str(e)}",
                    module='processing_workflows',
                    athlete_id=None
                )
                critical_log.set_context({
                    'processing_date': processing_date.isoformat(),
                    'error_type': type(e).__name__
                })
                
                session.add(critical_log)
                session.commit()
                
            finally:
                session.close()
            
            raise

# Global function for APScheduler
def replit_daily_processing(processing_date):
    """Global function to be called by APScheduler"""
    workflows = ProcessingWorkflows()
    return workflows.replit_daily_processing(processing_date)
