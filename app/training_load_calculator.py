"""
Advanced Training Load Metrics Calculator
Calculates CTL, ATL, TSB, and TSS using real athlete data
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
from app.models import Activity, ReplitAthlete

logger = logging.getLogger(__name__)

class TrainingLoadCalculator:
    """
    Calculate advanced training load metrics from real athlete data
    """
    
    def __init__(self):
        # Exponential decay constants
        self.CTL_DAYS = 42  # Chronic Training Load (fitness) - 42 day decay
        self.ATL_DAYS = 7   # Acute Training Load (fatigue) - 7 day decay
        
        # Decay factors for exponential weighted moving averages (rounded for consistency)
        self.ctl_decay = round(2.0 / (self.CTL_DAYS + 1), 6)  # 0.046512
        self.atl_decay = round(2.0 / (self.ATL_DAYS + 1), 6)  # 0.25
    
    def calculate_tss(self, activity: Activity, athlete: ReplitAthlete) -> float:
        """
        Calculate Training Stress Score for an activity
        Uses heart rate zones or pace zones based on available data
        Enhanced with elevation gain for comprehensive training load assessment
        """
        if not activity.moving_time or activity.moving_time <= 0:
            return 0.0
        
        duration_hours = activity.moving_time / 3600
        base_tss = 0.0
        
        # Method 1: Heart Rate based TSS (preferred if available)
        if activity.average_heartrate and athlete.max_hr and athlete.lthr:
            base_tss = self._calculate_hr_tss(activity, athlete, duration_hours)
        
        # Method 2: Pace based TSS for running activities
        elif activity.sport_type == 'Run' and activity.distance and activity.distance > 0:
            base_tss = self._calculate_pace_tss(activity, athlete, duration_hours)
        
        # Method 3: Simple duration-based TSS (fallback)
        else:
            base_tss = self._calculate_duration_tss(duration_hours)
        
        # Apply elevation adjustment multiplier
        elevation_adjusted_tss = self._apply_elevation_adjustment(base_tss, activity)
        
        return max(0.0, elevation_adjusted_tss)
    
    def _calculate_hr_tss(self, activity: Activity, athlete: ReplitAthlete, duration_hours: float) -> float:
        """Calculate TSS based on heart rate zones"""
        if not athlete.max_hr or not athlete.rest_hr:
            return 0.0
        
        avg_hr = activity.average_heartrate
        max_hr = athlete.max_hr
        rest_hr = athlete.rest_hr
        
        # Calculate heart rate reserve percentage
        hr_reserve = max_hr - rest_hr
        if hr_reserve <= 0:
            return 0.0
        
        # Normalized heart rate (percentage of HR reserve)
        hr_percent = (avg_hr - rest_hr) / hr_reserve
        hr_percent = max(0.0, min(1.0, hr_percent))  # Clamp between 0-1
        
        # Heart rate zone intensity factors
        if hr_percent < 0.6:      # Zone 1 (Active Recovery)
            intensity_factor = 0.5
        elif hr_percent < 0.7:    # Zone 2 (Aerobic Base)
            intensity_factor = 0.65
        elif hr_percent < 0.8:    # Zone 3 (Aerobic Threshold)
            intensity_factor = 0.8
        elif hr_percent < 0.9:    # Zone 4 (Lactate Threshold)
            intensity_factor = 0.95
        else:                     # Zone 5 (VO2 Max+)
            intensity_factor = 1.2
        
        # TSS = Duration (hours) × Intensity Factor² × 100
        tss = duration_hours * (intensity_factor ** 2) * 100
        return round(tss, 1)
    
    def _calculate_pace_tss(self, activity: Activity, athlete: ReplitAthlete, duration_hours: float) -> float:
        """Calculate TSS based on running pace zones"""
        if not activity.distance or activity.distance <= 0:
            return 0.0
        
        # Calculate pace (minutes per km)
        pace_min_per_km = (activity.moving_time / 60) / (activity.distance / 1000)
        
        # Estimate threshold pace (assume around 6:30/km for average runner)
        # In real implementation, this would come from athlete's threshold tests
        estimated_threshold_pace = 6.5  # minutes per km
        
        # Calculate pace intensity factor
        pace_ratio = pace_min_per_km / estimated_threshold_pace
        
        # Intensity factor based on pace zones
        if pace_ratio > 1.2:      # Easy/Recovery pace
            intensity_factor = 0.6
        elif pace_ratio > 1.05:   # Aerobic base pace
            intensity_factor = 0.75
        elif pace_ratio > 0.95:   # Threshold pace
            intensity_factor = 1.0
        elif pace_ratio > 0.85:   # VO2 Max pace
            intensity_factor = 1.15
        else:                     # Faster than VO2 Max
            intensity_factor = 1.3
        
        # TSS calculation
        tss = duration_hours * (intensity_factor ** 2) * 100
        return round(tss, 1)
    
    def _calculate_duration_tss(self, activity: Activity, duration_hours: float) -> float:
        """Simple duration-based TSS calculation (fallback method)"""
        # Sport-specific base intensity factors
        sport_factors = {
            'Run': 70,
            'Ride': 60,
            'Swim': 80,
            'Tennis': 65,
            'Soccer': 75,
            'Basketball': 70,
            'Workout': 60
        }
        
        base_factor = sport_factors.get(activity.sport_type, 60)
        tss = duration_hours * base_factor
        return round(tss, 1)
    
    def calculate_training_metrics(self, athlete_id: int, days_back: int = 90) -> Dict:
        """
        Calculate CTL, ATL, TSB for an athlete over the specified period
        """
        try:
            from app import db
            
            # Get athlete data
            athlete = db.session.query(ReplitAthlete).filter_by(id=athlete_id).first()
            if not athlete:
                return self._empty_metrics()
            
            # Get activities for the specified period
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            activities = db.session.query(Activity).filter(
                Activity.athlete_id == athlete_id,
                Activity.start_date >= start_date,
                Activity.start_date <= end_date
            ).order_by(Activity.start_date).all()
            
            if not activities:
                return self._empty_metrics()
            
            # Calculate daily TSS values
            daily_tss = self._calculate_daily_tss(activities, athlete, start_date, end_date)
            
            # Calculate CTL, ATL, TSB over time
            metrics_timeline = self._calculate_load_timeline(daily_tss)
            
            # Get current values (last calculated values)
            current_metrics = metrics_timeline[-1] if metrics_timeline else self._empty_current_metrics()
            
            # Calculate trend analysis
            trend_analysis = self._analyze_trends(metrics_timeline)
            
            return {
                'current': current_metrics,
                'timeline': metrics_timeline[-30:],  # Last 30 days for charting
                'trends': trend_analysis,
                'total_activities': len(activities),
                'avg_weekly_tss': current_metrics.get('weekly_tss', 0)
            }
            
        except Exception as e:
            logger.error(f"Error calculating training metrics for athlete {athlete_id}: {str(e)}")
            return self._empty_metrics()
    
    def _calculate_daily_tss(self, activities: List[Activity], athlete: ReplitAthlete, 
                           start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate TSS for each day in the period"""
        daily_tss = {}
        
        # Initialize all days with 0 TSS
        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            daily_tss[date_key] = 0.0
            current_date += timedelta(days=1)
        
        # Add TSS for days with activities
        for activity in activities:
            date_key = activity.start_date.strftime('%Y-%m-%d')
            tss = self.calculate_tss(activity, athlete)
            daily_tss[date_key] += tss
        
        return daily_tss
    
    def _apply_elevation_adjustment(self, base_tss: float, activity: Activity) -> float:
        """
        Apply elevation gain adjustment to TSS calculation
        Critical for marathon training where elevation significantly impacts training stress
        """
        if not activity.total_elevation_gain or not activity.distance:
            return base_tss
        
        # Calculate elevation gain per kilometer
        elevation_per_km = activity.total_elevation_gain / (activity.distance / 1000)
        
        # Elevation adjustment factors based on sports science research
        # Every 100m of elevation gain per km adds approximately 8-12% training stress
        if elevation_per_km <= 10:  # Flat terrain
            elevation_multiplier = 1.0
        elif elevation_per_km <= 30:  # Rolling hills
            elevation_multiplier = 1.05 + (elevation_per_km - 10) * 0.003  # 1.05-1.11
        elif elevation_per_km <= 60:  # Hilly terrain
            elevation_multiplier = 1.11 + (elevation_per_km - 30) * 0.005  # 1.11-1.26
        elif elevation_per_km <= 100:  # Very hilly
            elevation_multiplier = 1.26 + (elevation_per_km - 60) * 0.007  # 1.26-1.54
        else:  # Mountain terrain
            elevation_multiplier = min(2.0, 1.54 + (elevation_per_km - 100) * 0.003)  # Cap at 2.0x
        
        # Additional adjustment for downhill impact (negative elevation change increases eccentric stress)
        # Note: Strava total_elevation_gain only includes positive elevation, but we account for overall terrain stress
        if elevation_per_km > 50:  # Significant elevation suggests both up and down
            eccentric_factor = 1.05  # 5% additional stress for downhill eccentric loading
            elevation_multiplier *= eccentric_factor
        
        adjusted_tss = base_tss * elevation_multiplier
        
        # Log significant elevation adjustments for transparency
        if elevation_multiplier > 1.15:
            logger.info(f"Applied elevation adjustment: {elevation_per_km:.1f}m/km elevation gain, "
                       f"multiplier: {elevation_multiplier:.2f}, TSS: {base_tss:.1f} → {adjusted_tss:.1f}")
        
        return adjusted_tss
    
    def _calculate_load_timeline(self, daily_tss: Dict[str, float]) -> List[Dict]:
        """Calculate CTL, ATL, TSB over time using exponential weighted moving averages"""
        timeline = []
        ctl = 0.0  # Start with 0 fitness
        atl = 0.0  # Start with 0 fatigue
        
        # Sort dates to ensure chronological order
        sorted_dates = sorted(daily_tss.keys())
        
        for date_str in sorted_dates:
            tss = daily_tss[date_str]
            
            # Update CTL (Chronic Training Load) - 42-day exponential decay
            ctl = round((tss * self.ctl_decay) + (ctl * (1 - self.ctl_decay)), 1)
            
            # Update ATL (Acute Training Load) - 7-day exponential decay
            atl = round((tss * self.atl_decay) + (atl * (1 - self.atl_decay)), 1)
            
            # Calculate TSB (Training Stress Balance)
            tsb = ctl - atl
            
            # Calculate weekly TSS (rolling 7-day sum)
            week_start = datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=6)
            weekly_tss = sum(
                daily_tss.get((week_start + timedelta(days=i)).strftime('%Y-%m-%d'), 0)
                for i in range(7)
            )
            
            timeline.append({
                'date': date_str,
                'tss': round(tss, 1),
                'ctl': round(ctl, 1),
                'atl': round(atl, 1),
                'tsb': round(tsb, 1),
                'weekly_tss': round(weekly_tss, 1)
            })
        
        return timeline
    
    def _analyze_trends(self, timeline: List[Dict]) -> Dict:
        """Analyze trends in training load metrics"""
        if len(timeline) < 7:
            return {'status': 'insufficient_data'}
        
        recent = timeline[-7:]  # Last 7 days
        previous = timeline[-14:-7] if len(timeline) >= 14 else timeline[:-7]
        
        # Calculate averages
        recent_ctl = np.mean([day['ctl'] for day in recent])
        recent_atl = np.mean([day['atl'] for day in recent])
        recent_tsb = np.mean([day['tsb'] for day in recent])
        
        prev_ctl = np.mean([day['ctl'] for day in previous]) if previous else recent_ctl
        prev_atl = np.mean([day['atl'] for day in previous]) if previous else recent_atl
        prev_tsb = np.mean([day['tsb'] for day in previous]) if previous else recent_tsb
        
        # Calculate changes
        ctl_change = recent_ctl - prev_ctl
        atl_change = recent_atl - prev_atl
        tsb_change = recent_tsb - prev_tsb
        
        # Determine training phase
        if recent_tsb < -10:
            phase = 'building'
            phase_description = 'Building fitness through consistent training'
        elif recent_tsb > 10:
            phase = 'peaked'
            phase_description = 'Well-rested and ready for peak performance'
        elif recent_tsb > 0:
            phase = 'tapering'
            phase_description = 'Reducing training load for recovery'
        else:
            phase = 'maintaining'
            phase_description = 'Maintaining current fitness level'
        
        return {
            'fitness_trend': 'increasing' if ctl_change > 1 else 'decreasing' if ctl_change < -1 else 'stable',
            'fatigue_trend': 'increasing' if atl_change > 1 else 'decreasing' if atl_change < -1 else 'stable',
            'form_trend': 'improving' if tsb_change > 1 else 'declining' if tsb_change < -1 else 'stable',
            'training_phase': phase,
            'phase_description': phase_description,
            'recommendations': self._generate_recommendations(recent_ctl, recent_atl, recent_tsb)
        }
    
    def _generate_recommendations(self, ctl: float, atl: float, tsb: float) -> List[str]:
        """Generate training recommendations based on current metrics"""
        recommendations = []
        
        if tsb < -20:
            recommendations.append("Consider reducing training intensity - high fatigue detected")
        elif tsb < -10:
            recommendations.append("Monitor recovery closely - approaching high fatigue zone")
        elif tsb > 15:
            recommendations.append("Consider increasing training load - well-recovered state")
        elif tsb > 5:
            recommendations.append("Good time for quality training sessions")
        
        if ctl < 40:
            recommendations.append("Focus on building aerobic base with consistent training")
        elif ctl > 100:
            recommendations.append("High fitness level - maintain with varied intensity")
        
        if atl > 80:
            recommendations.append("Very high acute load - prioritize recovery")
        elif atl < 20:
            recommendations.append("Low recent training stress - opportunity to increase volume")
        
        if not recommendations:
            recommendations.append("Training load appears well-balanced")
        
        return recommendations
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics structure"""
        return {
            'current': self._empty_current_metrics(),
            'timeline': [],
            'trends': {'status': 'no_data'},
            'total_activities': 0,
            'avg_weekly_tss': 0
        }
    
    def _empty_current_metrics(self) -> Dict:
        """Return empty current metrics"""
        return {
            'ctl': 0,
            'atl': 0,
            'tsb': 0,
            'weekly_tss': 0,
            'daily_tss': 0
        }

# Global instance
training_load_calculator = TrainingLoadCalculator()

def get_training_load_metrics(athlete_id: int, days_back: int = 90) -> Dict:
    """Get training load metrics for an athlete"""
    return training_load_calculator.calculate_training_metrics(athlete_id, days_back)