"""
Simplified Senior Athlete Analytics
Works with existing database structure without requiring age field
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from app.models import ReplitAthlete, Activity

logger = logging.getLogger(__name__)

def analyze_senior_athlete_recovery_simple(db_session: Session, athlete_id: int, days: int = 30) -> Dict:
    """
    Simplified recovery analysis that works with existing data
    """
    try:
        # Get activities for the period
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        activities = db_session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= start_date,
            Activity.start_date <= end_date
        ).order_by(Activity.start_date).all()
        
        if not activities:
            return None
        
        # Calculate recovery metrics
        total_days = days
        activity_days = len(set(activity.start_date.date() for activity in activities))
        rest_days = total_days - activity_days
        rest_day_ratio = rest_days / total_days if total_days > 0 else 0
        
        # Analyze rest between hard efforts (high intensity activities)
        hard_efforts = []
        for activity in activities:
            # Consider running activities > 5km or > 30min as hard efforts
            if (activity.sport_type == 'Run' and 
                ((activity.distance and activity.distance > 5000) or 
                 (activity.moving_time and activity.moving_time > 1800))):
                hard_efforts.append(activity.start_date.date())
        
        # Calculate average rest between hard efforts
        avg_rest_between_hard = 0
        if len(hard_efforts) > 1:
            rest_periods = []
            for i in range(1, len(hard_efforts)):
                days_between = (hard_efforts[i] - hard_efforts[i-1]).days
                rest_periods.append(days_between)
            avg_rest_between_hard = sum(rest_periods) / len(rest_periods)
        
        # Calculate recovery score (0-100)
        recovery_score = 50  # Base score
        
        # Adjust based on rest day ratio
        if rest_day_ratio >= 0.3:  # 30%+ rest days is good
            recovery_score += 20
        elif rest_day_ratio >= 0.2:  # 20-30% is moderate
            recovery_score += 10
        elif rest_day_ratio < 0.15:  # <15% is concerning
            recovery_score -= 15
        
        # Adjust based on rest between hard efforts
        if avg_rest_between_hard >= 2:  # 2+ days between hard efforts is good
            recovery_score += 15
        elif avg_rest_between_hard >= 1:  # 1-2 days is moderate
            recovery_score += 5
        elif avg_rest_between_hard < 1:  # <1 day is concerning
            recovery_score -= 20
        
        # Ensure score stays in 0-100 range
        recovery_score = max(0, min(100, recovery_score))
        
        # Generate recommendations
        recommendations = []
        if rest_day_ratio < 0.25:
            recommendations.append("Consider adding more rest days to your training schedule")
        if avg_rest_between_hard < 1.5:
            recommendations.append("Allow more recovery time between high-intensity sessions")
        if recovery_score >= 75:
            recommendations.append("Excellent recovery patterns - maintain current approach")
        elif recovery_score >= 50:
            recommendations.append("Good recovery balance with room for improvement")
        else:
            recommendations.append("Consider prioritizing recovery and reducing training intensity")
        
        return {
            'recovery_score': round(recovery_score),
            'rest_day_ratio': rest_day_ratio,
            'avg_rest_between_hard': avg_rest_between_hard,
            'recommendations': recommendations
        }
        
    except Exception as e:
        logger.error(f"Error in simplified recovery analysis for athlete {athlete_id}: {str(e)}")
        return None

def analyze_senior_athlete_cardiovascular_simple(db_session: Session, athlete_id: int, days: int = 30) -> Dict:
    """
    Simplified cardiovascular analysis using available data
    """
    try:
        # Get activities with heart rate data
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        activities = db_session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= start_date,
            Activity.start_date <= end_date,
            Activity.average_heartrate.isnot(None)
        ).order_by(Activity.start_date).all()
        
        if not activities:
            return None
        
        # Calculate metrics from available heart rate data
        avg_hr_values = [a.average_heartrate for a in activities if a.average_heartrate]
        max_hr_values = [a.max_heartrate for a in activities if a.max_heartrate]
        
        logger.info(f"Found {len(activities)} activities with HR data for athlete {athlete_id}")
        logger.info(f"Average HR values: {avg_hr_values}")
        
        if not avg_hr_values:
            return None
        
        # Estimate resting heart rate (lowest average HR from easy activities)
        easy_activities = [a for a in activities if a.average_heartrate and a.average_heartrate < 150]
        estimated_rhr = min(avg_hr_values) * 0.7 if avg_hr_values else 65  # Conservative estimate
        
        if easy_activities:
            estimated_rhr = min(a.average_heartrate for a in easy_activities) * 0.75
            logger.info(f"Estimated RHR from easy activities: {estimated_rhr}")
        else:
            logger.info(f"Estimated RHR from all activities: {estimated_rhr}")
        
        # Calculate HR efficiency (pace per heart rate for running activities)
        hr_efficiency_score = 50  # Base score
        running_activities = [a for a in activities if a.sport_type == 'Run' and a.distance and a.moving_time and a.average_heartrate]
        
        if running_activities:
            pace_hr_ratios = []
            for activity in running_activities:
                if activity.distance > 1000 and activity.moving_time > 300:  # Filter reasonable activities
                    pace_per_km = (activity.moving_time / 60) / (activity.distance / 1000)  # min/km
                    hr_efficiency = activity.average_heartrate / pace_per_km if pace_per_km > 0 else 0
                    pace_hr_ratios.append(hr_efficiency)
                    logger.info(f"Activity: {activity.distance/1000:.1f}km in {activity.moving_time/60:.1f}min, pace: {pace_per_km:.2f}min/km, avg HR: {activity.average_heartrate}, efficiency: {hr_efficiency:.2f}")
            
            if pace_hr_ratios:
                avg_efficiency = sum(pace_hr_ratios) / len(pace_hr_ratios)
                logger.info(f"Average HR efficiency: {avg_efficiency:.2f}")
                # Score based on efficiency (lower HR for same pace is better)
                if avg_efficiency < 20:
                    hr_efficiency_score = 85
                elif avg_efficiency < 25:
                    hr_efficiency_score = 70
                elif avg_efficiency < 30:
                    hr_efficiency_score = 55
                else:
                    hr_efficiency_score = 40
                logger.info(f"HR efficiency score: {hr_efficiency_score}")
        
        # Estimate cardiovascular age based on metrics
        chronological_age = 42  # Default assumption for senior athlete
        cv_age = chronological_age
        
        # Adjust based on estimated RHR (lower RHR = younger CV age)
        if estimated_rhr < 60:
            cv_age -= 5
        elif estimated_rhr < 70:
            cv_age -= 2
        elif estimated_rhr > 80:
            cv_age += 3
        
        # Adjust based on HR efficiency
        if hr_efficiency_score > 70:
            cv_age -= 3
        elif hr_efficiency_score < 50:
            cv_age += 2
        
        # Determine health status
        if estimated_rhr < 65 and hr_efficiency_score > 70:
            health_status = 'excellent'
        elif estimated_rhr < 75 and hr_efficiency_score > 55:
            health_status = 'good'
        elif estimated_rhr < 85 and hr_efficiency_score > 40:
            health_status = 'fair'
        else:
            health_status = 'needs_attention'
        
        return {
            'current_rhr': round(estimated_rhr),
            'hr_efficiency_score': round(hr_efficiency_score),
            'cardiovascular_age': int(cv_age),
            'health_status': health_status
        }
        
    except Exception as e:
        logger.error(f"Error in simplified cardiovascular analysis for athlete {athlete_id}: {str(e)}")
        return None

def analyze_senior_athlete_injury_prevention_simple(db_session: Session, athlete_id: int, days: int = 30) -> Dict:
    """
    Simplified injury prevention analysis
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        activities = db_session.query(Activity).filter(
            Activity.athlete_id == athlete_id,
            Activity.start_date >= start_date,
            Activity.start_date <= end_date
        ).order_by(Activity.start_date).all()
        
        if not activities:
            return None
        
        # Calculate weekly load progression
        weeks_data = {}
        for activity in activities:
            week_key = activity.start_date.strftime('%Y-W%U')
            if week_key not in weeks_data:
                weeks_data[week_key] = {'distance': 0, 'time': 0}
            
            if activity.distance:
                weeks_data[week_key]['distance'] += activity.distance / 1000  # Convert to km
            if activity.moving_time:
                weeks_data[week_key]['time'] += activity.moving_time / 3600  # Convert to hours
        
        # Calculate weekly load increase
        weekly_loads = list(weeks_data.values())
        weekly_load_increase = 0
        
        if len(weekly_loads) >= 2:
            recent_load = weekly_loads[-1]['distance'] + weekly_loads[-1]['time'] * 10  # Weight time
            previous_load = weekly_loads[-2]['distance'] + weekly_loads[-2]['time'] * 10
            
            if previous_load > 0:
                weekly_load_increase = ((recent_load - previous_load) / previous_load) * 100
        
        # Assess biomechanical stress based on consecutive training days
        consecutive_days = 0
        max_consecutive = 0
        prev_date = None
        
        activity_dates = sorted(set(a.start_date.date() for a in activities))
        
        for date in activity_dates:
            if prev_date and (date - prev_date).days == 1:
                consecutive_days += 1
            else:
                max_consecutive = max(max_consecutive, consecutive_days)
                consecutive_days = 1
            prev_date = date
        
        max_consecutive = max(max_consecutive, consecutive_days)
        
        # Calculate biomechanical stress score (0-100, lower is better)
        biomech_stress = 20  # Base stress
        
        if max_consecutive > 5:
            biomech_stress += 30
        elif max_consecutive > 3:
            biomech_stress += 15
        
        # Calculate injury risk score
        injury_risk_score = 25  # Base risk
        
        # Adjust based on load progression
        if weekly_load_increase > 20:
            injury_risk_score += 30
        elif weekly_load_increase > 10:
            injury_risk_score += 15
        elif weekly_load_increase < -10:
            injury_risk_score += 10  # Sudden drops can also be risky
        
        # Adjust based on biomechanical stress
        injury_risk_score += biomech_stress * 0.5
        
        # Ensure score stays in range
        injury_risk_score = max(0, min(100, injury_risk_score))
        
        # Generate prevention recommendations
        recommendations = []
        if weekly_load_increase > 15:
            recommendations.append("Consider reducing weekly training load increase to <10%")
        if max_consecutive > 4:
            recommendations.append("Include more rest days between training sessions")
        if injury_risk_score > 60:
            recommendations.append("High injury risk detected - consider consulting a sports medicine professional")
        elif injury_risk_score < 30:
            recommendations.append("Low injury risk - current training approach is sustainable")
        else:
            recommendations.append("Moderate injury risk - monitor training load and recovery")
        
        return {
            'injury_risk_score': round(injury_risk_score),
            'weekly_load_increase': weekly_load_increase,
            'biomechanical_stress': round(biomech_stress),
            'prevention_recommendations': recommendations
        }
        
    except Exception as e:
        logger.error(f"Error in simplified injury prevention analysis for athlete {athlete_id}: {str(e)}")
        return None

def get_senior_athlete_analytics_simple(db_session: Session, athlete_id: int, days: int = 30) -> Dict:
    """
    Get all senior athlete analytics using simplified approach
    """
    try:
        return {
            'athlete_id': athlete_id,
            'analysis_period_days': days,
            'generated_at': datetime.now().isoformat(),
            'recovery_metrics': analyze_senior_athlete_recovery_simple(db_session, athlete_id, days),
            'cardiovascular_health': analyze_senior_athlete_cardiovascular_simple(db_session, athlete_id, days),
            'injury_prevention': analyze_senior_athlete_injury_prevention_simple(db_session, athlete_id, days)
        }
    except Exception as e:
        logger.error(f"Error getting simplified senior athlete analytics for athlete {athlete_id}: {str(e)}")
        return {
            'error': 'Unable to analyze senior athlete data',
            'athlete_id': athlete_id,
            'analysis_period_days': days
        }