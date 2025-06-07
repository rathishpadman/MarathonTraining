import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from dashboard.components import (
    create_performance_chart, create_pace_distribution_chart,
    create_weekly_summary_chart, create_heart_rate_zones_chart,
    create_progress_gauge, create_insights_panel, create_metric_card
)

def display_performance_analytics(performance_summary, athlete_id):
    """Display comprehensive performance analytics for an athlete"""
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.subheader("📊 Performance Analytics")
    
    if not performance_summary:
        st.warning("No performance data available for analytics")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Key performance indicators
    display_performance_kpis(performance_summary)
    
    # Performance trends
    display_performance_trends(performance_summary)
    
    # Advanced analytics
    display_advanced_analytics(performance_summary, athlete_id)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_performance_kpis(performance_summary):
    """Display key performance indicators"""
    st.markdown("### 🎯 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Total distance
    with col1:
        total_distance = performance_summary.get('total_distance', 0) / 1000
        st.markdown(create_metric_card(
            "Total Distance",
            f"{total_distance:.1f} km",
            "🏃‍♀️"
        ), unsafe_allow_html=True)
    
    # Average pace
    with col2:
        avg_pace = performance_summary.get('average_pace')
        if avg_pace:
            pace_min_per_km = avg_pace / 60
            pace_text = f"{pace_min_per_km:.2f} min/km"
        else:
            pace_text = "N/A"
        
        st.markdown(create_metric_card(
            "Average Pace",
            pace_text,
            "⚡"
        ), unsafe_allow_html=True)
    
    # Training consistency
    with col3:
        active_days = performance_summary.get('active_days', 0)
        period_days = 30  # Assuming 30-day period
        consistency = (active_days / period_days) * 100
        
        st.markdown(create_metric_card(
            "Consistency",
            f"{consistency:.1f}%",
            "📅"
        ), unsafe_allow_html=True)
    
    # Weekly average
    with col4:
        weekly_avg = performance_summary.get('average_weekly_distance', 0) / 1000
        st.markdown(create_metric_card(
            "Weekly Average",
            f"{weekly_avg:.1f} km",
            "📈"
        ), unsafe_allow_html=True)

def display_performance_trends(performance_summary):
    """Display performance trends and charts"""
    st.markdown("### 📈 Performance Trends")
    
    recent_summaries = performance_summary.get('recent_summaries', [])
    if not recent_summaries:
        st.info("No recent activity data available for trend analysis")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(recent_summaries)
    if df.empty:
        st.info("No data available for trend analysis")
        return
    
    # Ensure proper data types
    df['date'] = pd.to_datetime(df['date'])
    df['distance_km'] = df['distance'] / 1000
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🏃‍♀️ Pace Analysis", "📅 Weekly Summary", "❤️ Heart Rate"])
    
    with tab1:
        # Main performance chart
        chart = create_performance_chart(df)
        st.plotly_chart(chart, use_container_width=True)
        
        # Performance summary table
        st.markdown("**Recent Activities Summary:**")
        display_df = df[['date', 'distance_km', 'moving_time', 'status']].copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        display_df['moving_time'] = display_df['moving_time'].apply(lambda x: f"{x//60} min" if pd.notna(x) else "N/A")
        display_df.columns = ['Date', 'Distance (km)', 'Duration', 'Status']
        st.dataframe(display_df, use_container_width=True)
    
    with tab2:
        # Pace distribution and trends
        if 'pace' in df.columns:
            pace_chart = create_pace_distribution_chart(df)
            st.plotly_chart(pace_chart, use_container_width=True)
            
            # Pace trend analysis
            valid_pace = df[df['pace'].notna() & (df['pace'] > 0)]
            if not valid_pace.empty:
                # Calculate pace trend
                pace_trend = np.polyfit(range(len(valid_pace)), valid_pace['pace'], 1)[0]
                
                col1, col2 = st.columns(2)
                with col1:
                    if pace_trend < 0:
                        st.success("🚀 Pace is improving over time!")
                    elif pace_trend > 0:
                        st.warning("📈 Pace is slowing - consider speed work")
                    else:
                        st.info("➡️ Pace is stable")
                
                with col2:
                    avg_pace_min = valid_pace['pace'].mean() / 60
                    best_pace_min = valid_pace['pace'].min() / 60
                    st.metric("Average Pace", f"{avg_pace_min:.2f} min/km")
                    st.metric("Best Pace", f"{best_pace_min:.2f} min/km")
        else:
            st.info("No pace data available for analysis")
    
    with tab3:
        # Weekly summary
        weekly_chart = create_weekly_summary_chart(df)
        st.plotly_chart(weekly_chart, use_container_width=True)
        
        # Weekly statistics
        df['week'] = df['date'].dt.to_period('W')
        weekly_stats = df.groupby('week').agg({
            'distance_km': ['sum', 'mean', 'count'],
            'moving_time': 'sum'
        }).round(2)
        
        if not weekly_stats.empty:
            st.markdown("**Weekly Statistics:**")
            weekly_display = weekly_stats.copy()
            weekly_display.columns = ['Total Distance', 'Avg Distance', 'Activities', 'Total Time']
            weekly_display['Total Time'] = weekly_display['Total Time'].apply(lambda x: f"{x//60:.0f}h {x%60:.0f}m")
            st.dataframe(weekly_display, use_container_width=True)
    
    with tab4:
        # Heart rate analysis
        hr_chart = create_heart_rate_zones_chart(df)
        st.plotly_chart(hr_chart, use_container_width=True)
        
        # Heart rate statistics
        if 'average_heartrate' in df.columns:
            hr_data = df[df['average_heartrate'].notna() & (df['average_heartrate'] > 0)]
            if not hr_data.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    avg_hr = hr_data['average_heartrate'].mean()
                    st.metric("Average HR", f"{avg_hr:.0f} bpm")
                with col2:
                    max_hr = hr_data['average_heartrate'].max()
                    st.metric("Max Recorded HR", f"{max_hr:.0f} bpm")
                with col3:
                    # HR variability (simplified)
                    hr_std = hr_data['average_heartrate'].std()
                    st.metric("HR Variability", f"{hr_std:.1f} bpm")
        else:
            st.info("No heart rate data available")

def display_advanced_analytics(performance_summary, athlete_id):
    """Display advanced analytics and predictions"""
    st.markdown("### 🔬 Advanced Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Training load analysis
        st.markdown("**Training Load Analysis**")
        
        total_load = performance_summary.get('training_load', 0)
        target_load = 1000  # Example target
        
        load_gauge = create_progress_gauge(
            current_value=total_load,
            target_value=target_load,
            title="Training Load Progress"
        )
        st.plotly_chart(load_gauge, use_container_width=True)
        
        # Load recommendations
        if total_load < target_load * 0.7:
            st.info("💡 Consider increasing training intensity")
        elif total_load > target_load * 1.2:
            st.warning("⚠️ High training load - ensure recovery")
        else:
            st.success("✅ Training load is well balanced")
    
    with col2:
        # Performance prediction
        st.markdown("**Performance Predictions**")
        
        # Simple race time predictions based on current pace
        avg_pace = performance_summary.get('average_pace')
        if avg_pace:
            race_predictions = calculate_race_predictions(avg_pace)
            
            for distance, time_prediction in race_predictions.items():
                st.metric(f"{distance} Prediction", time_prediction)
        else:
            st.info("Insufficient data for race predictions")
        
        # Training recommendations
        st.markdown("**AI Recommendations**")
        recommendations = generate_ai_recommendations(performance_summary)
        for rec in recommendations:
            st.info(f"💡 {rec}")

def display_team_overview(team_data):
    """Display team overview analytics"""
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.subheader("👥 Team Analytics")
    
    if not team_data or 'athlete_details' not in team_data:
        st.warning("No team data available")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    athlete_details = team_data['athlete_details']
    
    # Team performance comparison
    st.markdown("### 📊 Team Performance Comparison")
    
    # Create DataFrame for visualization
    team_df = pd.DataFrame(athlete_details)
    
    if not team_df.empty:
        # Distance comparison chart
        fig = px.bar(
            team_df,
            x='athlete_name',
            y='total_distance',
            title='Total Distance by Athlete',
            color='total_distance',
            color_continuous_scale='viridis'
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Inter'),
            xaxis_title='Athlete',
            yaxis_title='Distance (m)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Team statistics table
        st.markdown("### 📈 Team Statistics")
        
        # Calculate team statistics
        total_team_distance = team_df['total_distance'].sum() / 1000
        avg_distance_per_athlete = team_df['total_distance'].mean() / 1000
        most_active = team_df.loc[team_df['total_distance'].idxmax(), 'athlete_name']
        total_activities = team_df['total_activities'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Team Distance", f"{total_team_distance:.1f} km")
        with col2:
            st.metric("Average per Athlete", f"{avg_distance_per_athlete:.1f} km")
        with col3:
            st.metric("Most Active", most_active)
        with col4:
            st.metric("Total Activities", str(total_activities))
        
        # Detailed team table
        st.markdown("### 📋 Detailed Team Performance")
        display_team_df = team_df.copy()
        display_team_df['total_distance'] = display_team_df['total_distance'] / 1000
        display_team_df.columns = ['Athlete ID', 'Name', 'Distance (km)', 'Activities', 'Active Days', 'Status']
        display_team_df = display_team_df[['Name', 'Distance (km)', 'Activities', 'Active Days', 'Status']]
        
        st.dataframe(display_team_df, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_athlete_comparison(athletes_data):
    """Display comparison between multiple athletes"""
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.subheader("⚖️ Athlete Comparison")
    
    if not athletes_data or len(athletes_data) < 2:
        st.info("Select at least 2 athletes for comparison")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Create comparison charts
    comparison_df = pd.DataFrame(athletes_data)
    
    # Multi-metric comparison
    metrics = ['total_distance', 'total_activities', 'active_days']
    
    fig = make_subplots(
        rows=1, cols=len(metrics),
        subplot_titles=[m.replace('_', ' ').title() for m in metrics]
    )
    
    for i, metric in enumerate(metrics):
        fig.add_trace(
            go.Bar(
                x=comparison_df['athlete_name'],
                y=comparison_df[metric],
                name=metric.replace('_', ' ').title(),
                showlegend=False
            ),
            row=1, col=i+1
        )
    
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Inter')
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_training_trends(performance_summary, athlete_id):
    """Display training trends and patterns"""
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.subheader("📈 Training Trends & Patterns")
    
    if not performance_summary:
        st.warning("No performance data available for trend analysis")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    recent_summaries = performance_summary.get('recent_summaries', [])
    if not recent_summaries:
        st.info("No recent data available for trend analysis")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    df = pd.DataFrame(recent_summaries)
    df['date'] = pd.to_datetime(df['date'])
    df['distance_km'] = df['distance'] / 1000
    
    # Trend analysis
    st.markdown("### 🔍 Trend Analysis")
    
    # Calculate trends
    if len(df) >= 5:  # Need minimum data points for trend analysis
        distance_trend = calculate_trend(df['distance_km'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            trend_direction = "📈 Increasing" if distance_trend > 0 else "📉 Decreasing" if distance_trend < 0 else "➡️ Stable"
            st.metric("Distance Trend", trend_direction)
        
        with col2:
            # Training frequency trend
            df['week'] = df['date'].dt.to_period('W')
            weekly_activity_count = df.groupby('week')['activity_count'].sum()
            if len(weekly_activity_count) >= 3:
                frequency_trend = calculate_trend(weekly_activity_count.values)
                freq_direction = "📈 Increasing" if frequency_trend > 0 else "📉 Decreasing" if frequency_trend < 0 else "➡️ Stable"
                st.metric("Frequency Trend", freq_direction)
        
        with col3:
            # Consistency score
            consistency = calculate_consistency_score(df)
            st.metric("Consistency Score", f"{consistency:.1f}%")
    
    # Pattern recognition
    st.markdown("### 🎯 Training Patterns")
    
    # Day of week analysis
    if len(df) >= 7:
        df['day_of_week'] = df['date'].dt.day_name()
        daily_patterns = df.groupby('day_of_week')['distance_km'].mean().reindex([
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
        ])
        
        fig = go.Figure(data=[
            go.Bar(
                x=daily_patterns.index,
                y=daily_patterns.values,
                marker_color='#667eea',
                opacity=0.8
            )
        ])
        
        fig.update_layout(
            title='Average Distance by Day of Week',
            xaxis_title='Day of Week',
            yaxis_title='Average Distance (km)',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Inter')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Find preferred training days
        top_day = daily_patterns.idxmax()
        st.info(f"💡 Most active training day: {top_day}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def calculate_trend(data):
    """Calculate trend slope using linear regression"""
    if len(data) < 2:
        return 0
    
    x = np.arange(len(data))
    trend = np.polyfit(x, data, 1)[0]
    return trend

def calculate_consistency_score(df):
    """Calculate training consistency score"""
    if df.empty:
        return 0
    
    # Calculate based on how regularly the athlete trains
    total_days = (df['date'].max() - df['date'].min()).days + 1
    active_days = len(df[df['activity_count'] > 0])
    
    if total_days == 0:
        return 0
    
    consistency = (active_days / total_days) * 100
    return min(consistency, 100)

def calculate_race_predictions(avg_pace_seconds_per_meter):
    """Calculate race time predictions based on current pace"""
    # Convert pace to more manageable format
    pace_per_km = avg_pace_seconds_per_meter * 1000
    
    # Race distance predictions with pace adjustments
    races = {
        "5K": 5000,
        "10K": 10000,
        "Half Marathon": 21097,
        "Marathon": 42195
    }
    
    predictions = {}
    
    for race_name, distance in races.items():
        # Apply pace adjustments based on distance
        if distance <= 5000:
            adjustment = 0.9  # Faster pace for shorter distances
        elif distance <= 10000:
            adjustment = 0.95
        elif distance <= 21097:
            adjustment = 1.05
        else:
            adjustment = 1.15  # Slower pace for marathon
        
        adjusted_pace = pace_per_km * adjustment
        race_time_seconds = (distance / 1000) * adjusted_pace
        
        # Convert to readable format
        hours = int(race_time_seconds // 3600)
        minutes = int((race_time_seconds % 3600) // 60)
        seconds = int(race_time_seconds % 60)
        
        if hours > 0:
            time_str = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{minutes}:{seconds:02d}"
        
        predictions[race_name] = time_str
    
    return predictions

def generate_ai_recommendations(performance_summary):
    """Generate AI-powered training recommendations"""
    recommendations = []
    
    total_distance = performance_summary.get('total_distance', 0) / 1000
    active_days = performance_summary.get('active_days', 0)
    avg_weekly = performance_summary.get('average_weekly_distance', 0) / 1000
    
    # Distance-based recommendations
    if total_distance < 50:
        recommendations.append("Focus on building base mileage with easy runs")
    elif total_distance > 200:
        recommendations.append("Consider adding more recovery days to prevent overtraining")
    
    # Frequency-based recommendations
    if active_days < 15:
        recommendations.append("Try to increase training frequency for better consistency")
    elif active_days > 25:
        recommendations.append("Excellent consistency! Consider varying workout intensity")
    
    # Weekly distance recommendations
    if avg_weekly < 30:
        recommendations.append("Gradually increase weekly distance by 10% each week")
    elif avg_weekly > 80:
        recommendations.append("Monitor fatigue levels and include adequate recovery")
    
    # General recommendations
    recommendations.extend([
        "Include strength training 2-3 times per week",
        "Add one tempo run per week to improve pace",
        "Schedule regular rest days for recovery"
    ])
    
    return recommendations[:5]  # Return top 5 recommendations
