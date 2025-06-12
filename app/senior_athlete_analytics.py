"""
Advanced Analytics for Senior Athletes (35+)
Focuses on recovery, cardiovascular health, and injury prevention
Using industry-standard methodologies and real training data
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics
from sqlalchemy.orm import Session
from app.models import Activity, ReplitAthlete

logger = logging.getLogger(__name__)

class SeniorAthleteAnalyzer:
    """
    Advanced analytics specifically designed for athletes 35+ years old
    Focuses on age-specific physiological changes and training adaptations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_recovery_metrics(self, db_session: Session, athlete_id: int, days: int = 30) -> Dict:
        """
        Analyze recovery patterns critical for senior athletes
        
        Returns:
            Dict containing recovery score, rest day analysis, and recommendations
        """
        try:
            athlete = db_session.query(ReplitAthlete).filter_by(id=athlete_id).first()
            if not athlete:
                return None
                
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            activities = db_session.query(Activity).filter(
                Activity.athlete_id == athlete_id,
                Activity.start_date >= start_date,
                Activity.start_date <= end_date
            ).order_by(Activity.start_date).all()
            
            if len(activities) < 5:  # Need minimum data
                return None
                
            # Calculate recovery metrics
            rest_day_analysis = self._analyze_rest_patterns(activities)
            hr_recovery_trends = self._analyze_hr_recovery(activities)
            training_stress_balance = self._calculate_stress_balance(activities)
            
            # Generate recovery score (0-100)
            recovery_score = self._calculate_recovery_score(
                rest_day_analysis, hr_recovery_trends, training_stress_balance
            )
            
            return {
                'recovery_score': round(recovery_score, 1),
                'rest_day_ratio': rest_day_analysis['rest_ratio'],
                'avg_rest_between_hard': rest_day_analysis['avg_rest_between_hard'],
                'hr_recovery_trend': hr_recovery_trends['trend'],
                'recommended_rest_days': self._recommend_rest_days(recovery_score, athlete.age if athlete.age else 40),
                'stress_balance': training_stress_balance,
                'recommendations': self._generate_recovery_recommendations(recovery_score, rest_day_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing recovery metrics for athlete {athlete_id}: {str(e)}")
            return None
    
    def analyze_cardiovascular_health(self, db_session: Session, athlete_id: int, days: int = 30) -> Dict:
        """
        Monitor cardiovascular health indicators important for 35+ athletes
        
        Returns:
            Dict containing RHR trends, HR efficiency, and cardiac health indicators
        """
        try:
            athlete = db_session.query(ReplitAthlete).filter_by(id=athlete_id).first()
            if not athlete:
                return None
                
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            activities = db_session.query(Activity).filter(
                Activity.athlete_id == athlete_id,
                Activity.start_date >= start_date,
                Activity.start_date <= end_date,
                Activity.average_heartrate.isnot(None),
                Activity.average_heartrate > 100  # Valid HR data
            ).order_by(Activity.start_date).all()
            
            if len(activities) < 5:  # Need minimum data
                return None
                
            # Calculate cardiovascular metrics
            rhr_analysis = self._analyze_resting_hr_trends(activities, athlete)
            hr_efficiency = self._calculate_hr_efficiency(activities)
            cardiac_drift = self._analyze_cardiac_drift(activities)
            
            # Age-adjusted max HR and zones
            age = athlete.age if athlete.age else 40
            max_hr_estimated = 220 - age  # Basic formula
            hr_reserve = max_hr_estimated - rhr_analysis['current_rhr']
            
            return {
                'rhr_trend': rhr_analysis['trend'],
                'current_rhr': rhr_analysis['current_rhr'],
                'rhr_change_30d': rhr_analysis['change_30d'],
                'hr_efficiency_score': round(hr_efficiency, 1),
                'cardiac_drift_avg': round(cardiac_drift, 1),
                'hr_reserve': hr_reserve,
                'aerobic_efficiency': self._calculate_aerobic_efficiency(activities),
                'cardiovascular_age': self._estimate_cardiovascular_age(rhr_analysis, hr_efficiency, age),
                'health_status': self._assess_cardiovascular_health(rhr_analysis, hr_efficiency)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing cardiovascular health for athlete {athlete_id}: {str(e)}")
            return None
    
    def analyze_injury_prevention(self, db_session: Session, athlete_id: int, days: int = 30) -> Dict:
        """
        Analyze injury risk factors specific to senior athletes
        
        Returns:
            Dict containing injury risk score and prevention recommendations
        """
        try:
            athlete = db_session.query(ReplitAthlete).filter_by(id=athlete_id).first()
            if not athlete:
                return None
                
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            activities = db_session.query(Activity).filter(
                Activity.athlete_id == athlete_id,
                Activity.start_date >= start_date,
                Activity.start_date <= end_date
            ).order_by(Activity.start_date).all()
            
            if len(activities) < 5:  # Need minimum data
                return None
                
            # Calculate injury risk factors
            training_load_progression = self._analyze_load_progression(activities)
            biomechanical_stress = self._assess_biomechanical_stress(activities)
            recovery_adequacy = self._assess_recovery_adequacy(activities)
            
            # Age-specific risk factors
            age = athlete.age if athlete.age else 40
            age_risk_multiplier = self._calculate_age_risk_multiplier(age)
            
            # Overall injury risk score (0-100, higher = more risk)
            injury_risk_score = self._calculate_injury_risk_score(
                training_load_progression, biomechanical_stress, 
                recovery_adequacy, age_risk_multiplier
            )
            
            return {
                'injury_risk_score': round(injury_risk_score, 1),
                'load_progression_risk': training_load_progression['risk_level'],
                'weekly_load_increase': training_load_progression['weekly_increase_pct'],
                'biomechanical_stress': round(biomechanical_stress, 1),
                'recovery_adequacy': round(recovery_adequacy, 1),
                'primary_risk_factors': self._identify_primary_risks(
                    training_load_progression, biomechanical_stress, recovery_adequacy, age
                ),
                'prevention_recommendations': self._generate_injury_prevention_plan(
                    injury_risk_score, age, training_load_progression
                ),
                'risk_category': self._categorize_risk_level(injury_risk_score)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing injury prevention for athlete {athlete_id}: {str(e)}")
            return None
    
    # Recovery Analysis Helper Methods
    def _analyze_rest_patterns(self, activities: List[Activity]) -> Dict:
        """Analyze rest day patterns and recovery time between hard efforts"""
        if not activities:
            return {'rest_ratio': 0, 'avg_rest_between_hard': 0}
            
        # Create daily activity map
        daily_activities = {}
        for activity in activities:
            date_key = activity.start_date.date()
            if date_key not in daily_activities:
                daily_activities[date_key] = []
            daily_activities[date_key].append(activity)
        
        # Calculate rest days
        total_days = (activities[-1].start_date.date() - activities[0].start_date.date()).days + 1
        active_days = len(daily_activities)
        rest_days = total_days - active_days
        rest_ratio = rest_days / total_days if total_days > 0 else 0
        
        # Find hard efforts (>75% of max effort or >45min duration)
        hard_efforts = []
        for activity in activities:
            is_hard = (
                (activity.moving_time and activity.moving_time > 2700) or  # >45 min
                (activity.average_heartrate and activity.average_heartrate > 150) or  # High HR
                (activity.distance and activity.distance > 15000)  # Long distance (>15km)
            )
            if is_hard:
                hard_efforts.append(activity.start_date.date())
        
        # Calculate average rest between hard efforts
        avg_rest_between_hard = 0
        if len(hard_efforts) > 1:
            rest_periods = []
            for i in range(1, len(hard_efforts)):
                days_between = (hard_efforts[i] - hard_efforts[i-1]).days
                rest_periods.append(days_between)
            avg_rest_between_hard = statistics.mean(rest_periods) if rest_periods else 0
        
        return {
            'rest_ratio': round(rest_ratio, 2),
            'avg_rest_between_hard': round(avg_rest_between_hard, 1),
            'total_rest_days': rest_days,
            'hard_efforts_count': len(hard_efforts)
        }
    
    def _analyze_hr_recovery(self, activities: List[Activity]) -> Dict:
        """Analyze heart rate recovery trends"""
        hr_activities = [a for a in activities if a.average_heartrate and a.average_heartrate > 100]
        
        if len(hr_activities) < 3:
            return {'trend': 'insufficient_data', 'avg_hr': 0}
        
        # Calculate trend in average heart rate (should decrease with better fitness)
        hrs = [a.average_heartrate for a in hr_activities[-10:]]  # Last 10 activities
        avg_hr = statistics.mean(hrs)
        
        # Simple trend analysis
        if len(hrs) >= 5:
            first_half = statistics.mean(hrs[:len(hrs)//2])
            second_half = statistics.mean(hrs[len(hrs)//2:])
            if second_half < first_half - 2:
                trend = 'improving'
            elif second_half > first_half + 2:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'avg_hr': round(avg_hr, 1),
            'hr_variability': round(statistics.stdev(hrs) if len(hrs) > 1 else 0, 1)
        }
    
    def _calculate_stress_balance(self, activities: List[Activity]) -> float:
        """Calculate training stress balance for recovery assessment"""
        if not activities:
            return 50.0  # Neutral
            
        # Simple stress calculation based on activity frequency and intensity
        recent_activities = activities[-7:]  # Last week
        weekly_stress = 0
        
        for activity in recent_activities:
            duration_hours = (activity.moving_time or 0) / 3600
            intensity_factor = 1.0
            
            if activity.average_heartrate:
                if activity.average_heartrate > 160:
                    intensity_factor = 1.5
                elif activity.average_heartrate > 140:
                    intensity_factor = 1.2
            
            activity_stress = duration_hours * intensity_factor * 10
            weekly_stress += activity_stress
        
        # Balance score: lower = better recovery
        balance_score = min(100, weekly_stress * 2)  # Scale to 0-100
        return round(balance_score, 1)
    
    def _calculate_recovery_score(self, rest_analysis: Dict, hr_analysis: Dict, stress_balance: float) -> float:
        """Calculate overall recovery score (0-100, higher = better recovery)"""
        score = 50  # Start neutral
        
        # Rest day component (40% of score)
        rest_ratio = rest_analysis.get('rest_ratio', 0)
        if rest_ratio >= 0.3:  # 30%+ rest days is good for seniors
            score += 20
        elif rest_ratio >= 0.2:
            score += 10
        else:
            score -= 10
        
        # Average rest between hard efforts (30% of score)
        avg_rest = rest_analysis.get('avg_rest_between_hard', 0)
        if avg_rest >= 2:  # 2+ days between hard efforts
            score += 15
        elif avg_rest >= 1:
            score += 5
        else:
            score -= 15
        
        # HR trend component (30% of score)
        hr_trend = hr_analysis.get('trend', 'stable')
        if hr_trend == 'improving':
            score += 15
        elif hr_trend == 'stable':
            score += 5
        else:
            score -= 10
        
        # Stress balance component
        if stress_balance < 30:
            score += 10
        elif stress_balance > 70:
            score -= 10
        
        return max(0, min(100, score))
    
    def _recommend_rest_days(self, recovery_score: float, age: int) -> int:
        """Recommend number of rest days per week based on recovery score and age"""
        base_rest = 2 if age < 45 else 3  # More rest for 45+
        
        if recovery_score < 40:
            return base_rest + 2
        elif recovery_score < 60:
            return base_rest + 1
        else:
            return base_rest
    
    def _generate_recovery_recommendations(self, recovery_score: float, rest_analysis: Dict) -> List[str]:
        """Generate personalized recovery recommendations"""
        recommendations = []
        
        if recovery_score < 50:
            recommendations.append("Increase rest days - your recovery score indicates elevated fatigue")
            
        if rest_analysis.get('avg_rest_between_hard', 0) < 1.5:
            recommendations.append("Allow 2+ days between hard training sessions")
            
        if rest_analysis.get('rest_ratio', 0) < 0.25:
            recommendations.append("Aim for at least 2-3 complete rest days per week")
            
        if recovery_score >= 80:
            recommendations.append("Excellent recovery! You can maintain current training load")
        elif recovery_score >= 60:
            recommendations.append("Good recovery patterns - monitor for any decline")
        
        return recommendations[:3]  # Limit to top 3
    
    # Cardiovascular Health Helper Methods
    def _analyze_resting_hr_trends(self, activities: List[Activity], athlete: ReplitAthlete) -> Dict:
        """Analyze resting heart rate trends"""
        # Use lowest HR from activities as proxy for RHR
        hr_activities = [a for a in activities if a.average_heartrate and a.average_heartrate > 100]
        
        if not hr_activities:
            return {'trend': 'no_data', 'current_rhr': 70, 'change_30d': 0}
        
        # Estimate RHR as 85% of lowest recorded exercise HR
        exercise_hrs = [a.average_heartrate for a in hr_activities]
        min_exercise_hr = min(exercise_hrs)
        estimated_rhr = round(min_exercise_hr * 0.85)
        
        # Calculate trend over time
        if len(hr_activities) >= 10:
            first_week_hrs = [a.average_heartrate for a in hr_activities[:len(hr_activities)//3]]
            last_week_hrs = [a.average_heartrate for a in hr_activities[-len(hr_activities)//3:]]
            
            avg_first = statistics.mean(first_week_hrs)
            avg_last = statistics.mean(last_week_hrs)
            change = avg_last - avg_first
            
            if change < -3:
                trend = 'improving'
            elif change > 3:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
            change = 0
        
        return {
            'trend': trend,
            'current_rhr': estimated_rhr,
            'change_30d': round(change, 1)
        }
    
    def _calculate_hr_efficiency(self, activities: List[Activity]) -> float:
        """Calculate heart rate efficiency (pace per heart rate)"""
        valid_activities = [
            a for a in activities 
            if a.average_heartrate and a.average_heartrate > 100 
            and a.distance and a.distance > 1000 
            and a.moving_time and a.moving_time > 300
        ]
        
        if not valid_activities:
            return 50.0
        
        efficiency_scores = []
        for activity in valid_activities:
            pace_per_km = (activity.moving_time / 60) / (activity.distance / 1000)  # min/km
            hr_efficiency = 300 / (pace_per_km * activity.average_heartrate / 150)  # Normalized score
            efficiency_scores.append(hr_efficiency)
        
        return statistics.mean(efficiency_scores) if efficiency_scores else 50.0
    
    def _analyze_cardiac_drift(self, activities: List[Activity]) -> float:
        """Analyze cardiac drift during longer efforts"""
        long_activities = [
            a for a in activities 
            if a.moving_time and a.moving_time > 2400  # >40 minutes
            and a.average_heartrate and a.max_heartrate
        ]
        
        if not long_activities:
            return 0.0
        
        drift_values = []
        for activity in long_activities:
            # Estimate drift as difference between max and average HR
            drift = activity.max_heartrate - activity.average_heartrate
            drift_values.append(drift)
        
        return statistics.mean(drift_values) if drift_values else 0.0
    
    def _calculate_aerobic_efficiency(self, activities: List[Activity]) -> float:
        """Calculate aerobic efficiency for senior athletes"""
        aerobic_activities = [
            a for a in activities 
            if a.average_heartrate and 120 <= a.average_heartrate <= 150  # Aerobic zone
            and a.distance and a.moving_time
        ]
        
        if not aerobic_activities:
            return 50.0
        
        # Calculate pace at aerobic heart rates
        paces = []
        for activity in aerobic_activities:
            pace_per_km = (activity.moving_time / 60) / (activity.distance / 1000)
            paces.append(pace_per_km)
        
        avg_aerobic_pace = statistics.mean(paces)
        # Score based on pace (lower = better efficiency)
        efficiency_score = max(0, 100 - (avg_aerobic_pace - 5) * 20)
        return min(100, efficiency_score)
    
    def _estimate_cardiovascular_age(self, rhr_analysis: Dict, hr_efficiency: float, chronological_age: int) -> int:
        """Estimate cardiovascular age based on metrics"""
        cv_age = chronological_age
        
        # Adjust based on RHR
        rhr = rhr_analysis.get('current_rhr', 70)
        if rhr < 50:
            cv_age -= 5
        elif rhr < 60:
            cv_age -= 2
        elif rhr > 80:
            cv_age += 5
        elif rhr > 70:
            cv_age += 2
        
        # Adjust based on HR efficiency
        if hr_efficiency > 70:
            cv_age -= 3
        elif hr_efficiency > 60:
            cv_age -= 1
        elif hr_efficiency < 40:
            cv_age += 3
        
        # Adjust based on trend
        if rhr_analysis.get('trend') == 'improving':
            cv_age -= 2
        elif rhr_analysis.get('trend') == 'declining':
            cv_age += 2
        
        return max(25, min(80, cv_age))
    
    def _assess_cardiovascular_health(self, rhr_analysis: Dict, hr_efficiency: float) -> str:
        """Assess overall cardiovascular health status"""
        score = 0
        
        # RHR component
        rhr = rhr_analysis.get('current_rhr', 70)
        if rhr < 60:
            score += 2
        elif rhr > 75:
            score -= 2
        
        # Efficiency component
        if hr_efficiency > 60:
            score += 2
        elif hr_efficiency < 40:
            score -= 2
        
        # Trend component
        trend = rhr_analysis.get('trend', 'stable')
        if trend == 'improving':
            score += 1
        elif trend == 'declining':
            score -= 1
        
        if score >= 3:
            return 'excellent'
        elif score >= 1:
            return 'good'
        elif score >= -1:
            return 'fair'
        else:
            return 'needs_attention'
    
    # Injury Prevention Helper Methods
    def _analyze_load_progression(self, activities: List[Activity]) -> Dict:
        """Analyze training load progression for injury risk"""
        if len(activities) < 14:  # Need 2+ weeks
            return {'risk_level': 'insufficient_data', 'weekly_increase_pct': 0}
        
        # Calculate weekly loads
        weekly_loads = {}
        for activity in activities:
            week_start = activity.start_date.date() - timedelta(days=activity.start_date.weekday())
            if week_start not in weekly_loads:
                weekly_loads[week_start] = 0
            
            # Simple load calculation
            duration_hours = (activity.moving_time or 0) / 3600
            distance_km = (activity.distance or 0) / 1000
            load = duration_hours * 10 + distance_km * 2
            weekly_loads[week_start] += load
        
        if len(weekly_loads) < 2:
            return {'risk_level': 'insufficient_data', 'weekly_increase_pct': 0}
        
        # Calculate week-to-week changes
        sorted_weeks = sorted(weekly_loads.keys())
        increases = []
        
        for i in range(1, len(sorted_weeks)):
            prev_load = weekly_loads[sorted_weeks[i-1]]
            curr_load = weekly_loads[sorted_weeks[i]]
            
            if prev_load > 0:
                increase_pct = ((curr_load - prev_load) / prev_load) * 100
                increases.append(increase_pct)
        
        if not increases:
            return {'risk_level': 'insufficient_data', 'weekly_increase_pct': 0}
        
        avg_increase = statistics.mean(increases)
        max_increase = max(increases) if increases else 0
        
        # Assess risk level
        if max_increase > 30:  # >30% weekly increase is high risk
            risk_level = 'high'
        elif max_increase > 15:
            risk_level = 'moderate'
        elif avg_increase > 10:
            risk_level = 'moderate'
        else:
            risk_level = 'low'
        
        return {
            'risk_level': risk_level,
            'weekly_increase_pct': round(avg_increase, 1),
            'max_weekly_increase': round(max_increase, 1)
        }
    
    def _assess_biomechanical_stress(self, activities: List[Activity]) -> float:
        """Assess biomechanical stress factors"""
        running_activities = [a for a in activities if a.sport_type == 'Run']
        
        if not running_activities:
            return 0.0
        
        stress_score = 0
        
        # High mileage stress
        total_distance = sum((a.distance or 0) for a in running_activities)
        weekly_distance = total_distance / 1000 / 4  # Approx weekly km
        
        if weekly_distance > 80:  # High mileage for seniors
            stress_score += 30
        elif weekly_distance > 60:
            stress_score += 20
        elif weekly_distance > 40:
            stress_score += 10
        
        # Long run stress
        long_runs = [a for a in running_activities if (a.distance or 0) > 20000]  # >20km
        if len(long_runs) > len(running_activities) * 0.3:  # >30% are long runs
            stress_score += 20
        
        # Back-to-back stress
        activity_dates = [a.start_date.date() for a in running_activities]
        consecutive_days = 0
        max_consecutive = 0
        
        sorted_dates = sorted(set(activity_dates))
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                consecutive_days += 1
                max_consecutive = max(max_consecutive, consecutive_days + 1)
            else:
                consecutive_days = 0
        
        if max_consecutive > 3:  # >3 consecutive days
            stress_score += 15
        
        return min(100, stress_score)
    
    def _assess_recovery_adequacy(self, activities: List[Activity]) -> float:
        """Assess recovery adequacy between training sessions"""
        if len(activities) < 5:
            return 50.0
        
        # Calculate rest periods between activities
        rest_periods = []
        activity_dates = sorted([a.start_date.date() for a in activities])
        
        for i in range(1, len(activity_dates)):
            days_between = (activity_dates[i] - activity_dates[i-1]).days
            rest_periods.append(days_between)
        
        if not rest_periods:
            return 50.0
        
        avg_rest = statistics.mean(rest_periods)
        
        # Score recovery adequacy (higher = better recovery)
        if avg_rest >= 1.5:  # 1.5+ days average rest
            return 80.0
        elif avg_rest >= 1.0:
            return 60.0
        elif avg_rest >= 0.5:
            return 40.0
        else:
            return 20.0
    
    def _calculate_age_risk_multiplier(self, age: int) -> float:
        """Calculate age-based injury risk multiplier"""
        if age < 35:
            return 1.0
        elif age < 45:
            return 1.2
        elif age < 55:
            return 1.4
        else:
            return 1.6
    
    def _calculate_injury_risk_score(self, load_progression: Dict, biomech_stress: float, 
                                   recovery_adequacy: float, age_multiplier: float) -> float:
        """Calculate overall injury risk score"""
        base_score = 20  # Base risk
        
        # Load progression risk
        load_risk = load_progression.get('weekly_increase_pct', 0)
        if load_risk > 20:
            base_score += 30
        elif load_risk > 10:
            base_score += 15
        elif load_risk > 5:
            base_score += 5
        
        # Biomechanical stress
        base_score += biomech_stress * 0.3
        
        # Recovery adequacy (inverse relationship)
        base_score += (100 - recovery_adequacy) * 0.2
        
        # Apply age multiplier
        final_score = base_score * age_multiplier
        
        return min(100, max(0, final_score))
    
    def _identify_primary_risks(self, load_progression: Dict, biomech_stress: float, 
                              recovery_adequacy: float, age: int) -> List[str]:
        """Identify primary injury risk factors"""
        risks = []
        
        if load_progression.get('weekly_increase_pct', 0) > 15:
            risks.append("Rapid training load increases")
        
        if biomech_stress > 50:
            risks.append("High biomechanical stress from volume/intensity")
        
        if recovery_adequacy < 40:
            risks.append("Insufficient recovery between sessions")
        
        if age >= 45:
            risks.append("Age-related tissue adaptation slower")
        
        return risks[:3]  # Top 3 risks
    
    def _generate_injury_prevention_plan(self, risk_score: float, age: int, 
                                       load_progression: Dict) -> List[str]:
        """Generate injury prevention recommendations"""
        recommendations = []
        
        if risk_score > 70:
            recommendations.append("HIGH RISK: Reduce training volume by 20-30% this week")
            recommendations.append("Focus on recovery: extra sleep, gentle stretching, massage")
        elif risk_score > 50:
            recommendations.append("MODERATE RISK: Limit training increases to <10% per week")
            recommendations.append("Add 1-2 extra rest days to current schedule")
        
        if age >= 45:
            recommendations.append("Include 2-3 strength training sessions per week")
            recommendations.append("Prioritize 15+ minutes of dynamic warm-up before runs")
        
        if load_progression.get('weekly_increase_pct', 0) > 10:
            recommendations.append("Follow 10% rule: increase weekly volume by max 10%")
        
        return recommendations[:4]  # Limit to 4 recommendations
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize injury risk level"""
        if risk_score < 30:
            return 'low'
        elif risk_score < 60:
            return 'moderate'
        else:
            return 'high'


# Global functions for easy access
def analyze_senior_athlete_recovery(db_session: Session, athlete_id: int, days: int = 30) -> Dict:
    """Global function for recovery analysis"""
    analyzer = SeniorAthleteAnalyzer()
    return analyzer.analyze_recovery_metrics(db_session, athlete_id, days)

def analyze_senior_athlete_cardiovascular(db_session: Session, athlete_id: int, days: int = 30) -> Dict:
    """Global function for cardiovascular analysis"""
    analyzer = SeniorAthleteAnalyzer()
    return analyzer.analyze_cardiovascular_health(db_session, athlete_id, days)

def analyze_senior_athlete_injury_prevention(db_session: Session, athlete_id: int, days: int = 30) -> Dict:
    """Global function for injury prevention analysis"""
    analyzer = SeniorAthleteAnalyzer()
    return analyzer.analyze_injury_prevention(db_session, athlete_id, days)