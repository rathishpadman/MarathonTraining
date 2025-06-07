import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

def create_metric_card(title, value, icon="📊"):
    """Create a glassmorphism metric card"""
    return f"""
    <div class="metric-card">
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
            <span style="font-size: 1.5rem; margin-right: 8px;">{icon}</span>
        </div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{title}</div>
    </div>
    """

def create_status_badge(status):
    """Create a status badge with appropriate styling"""
    status_lower = status.lower()
    
    if "on track" in status_lower or "excellent" in status_lower:
        badge_class = "status-on-track"
    elif "warning" in status_lower or "under" in status_lower or "mostly" in status_lower:
        badge_class = "status-warning"
    else:
        badge_class = "status-alert"
    
    return f'<span class="{badge_class}">{status}</span>'

def create_performance_chart(df):
    """Create a performance chart showing distance and pace trends"""
    if df.empty:
        # Return empty chart
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Distance Over Time', 'Training Load'),
        vertical_spacing=0.1,
        specs=[[{"secondary_y": False}],
               [{"secondary_y": False}]]
    )
    
    # Distance chart
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['distance_km'],
            mode='lines+markers',
            name='Distance (km)',
            line=dict(color='#4ade80', width=3),
            marker=dict(size=8, color='#22c55e')
        ),
        row=1, col=1
    )
    
    # Training load chart if available
    if 'training_load' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['training_load'],
                name='Training Load',
                marker_color='#667eea',
                opacity=0.7
            ),
            row=2, col=1
        )
    
    # Update layout with glassmorphism styling
    fig.update_layout(
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Inter'),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(255,255,255,0.1)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1
        )
    )
    
    # Update axes
    fig.update_xaxes(
        gridcolor='rgba(255,255,255,0.2)',
        showgrid=True,
        zeroline=False
    )
    fig.update_yaxes(
        gridcolor='rgba(255,255,255,0.2)',
        showgrid=True,
        zeroline=False
    )
    
    return fig

def create_pace_distribution_chart(df):
    """Create a pace distribution histogram"""
    if df.empty or 'pace' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="No pace data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color='white')
        )
        return fig
    
    # Filter out invalid pace data
    valid_pace = df[df['pace'].notna() & (df['pace'] > 0)]['pace']
    
    if valid_pace.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No valid pace data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color='white')
        )
        return fig
    
    # Convert pace to minutes per km for readability
    pace_min_per_km = valid_pace / 60
    
    fig = go.Figure(data=[
        go.Histogram(
            x=pace_min_per_km,
            nbinsx=20,
            marker_color='#667eea',
            opacity=0.7,
            name='Pace Distribution'
        )
    ])
    
    fig.update_layout(
        title='Pace Distribution',
        xaxis_title='Pace (min/km)',
        yaxis_title='Frequency',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Inter')
    )
    
    fig.update_xaxes(
        gridcolor='rgba(255,255,255,0.2)',
        showgrid=True,
        zeroline=False
    )
    fig.update_yaxes(
        gridcolor='rgba(255,255,255,0.2)',
        showgrid=True,
        zeroline=False
    )
    
    return fig

def create_weekly_summary_chart(df):
    """Create a weekly summary chart"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for weekly summary",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color='white')
        )
        return fig
    
    # Group by week
    df_copy = df.copy()
    df_copy['week'] = df_copy['date'].dt.to_period('W').dt.start_time
    
    weekly_summary = df_copy.groupby('week').agg({
        'distance_km': 'sum',
        'moving_time': 'sum',
        'activity_count': 'sum'
    }).reset_index()
    
    # Create multi-trace chart
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Weekly Distance', 'Weekly Activities'),
        vertical_spacing=0.15
    )
    
    # Weekly distance
    fig.add_trace(
        go.Bar(
            x=weekly_summary['week'],
            y=weekly_summary['distance_km'],
            name='Weekly Distance (km)',
            marker_color='#4ade80',
            opacity=0.8
        ),
        row=1, col=1
    )
    
    # Weekly activity count
    fig.add_trace(
        go.Bar(
            x=weekly_summary['week'],
            y=weekly_summary['activity_count'],
            name='Weekly Activities',
            marker_color='#667eea',
            opacity=0.8
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Inter'),
        showlegend=False
    )
    
    fig.update_xaxes(
        gridcolor='rgba(255,255,255,0.2)',
        showgrid=True,
        zeroline=False
    )
    fig.update_yaxes(
        gridcolor='rgba(255,255,255,0.2)',
        showgrid=True,
        zeroline=False
    )
    
    return fig

def create_training_calendar(workouts):
    """Create a training calendar visualization"""
    if not workouts:
        fig = go.Figure()
        fig.add_annotation(
            text="No upcoming workouts scheduled",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color='white')
        )
        return fig
    
    # Create calendar data
    dates = []
    workout_types = []
    distances = []
    
    for workout in workouts:
        workout_date = datetime.fromisoformat(workout['date'])
        dates.append(workout_date)
        workout_types.append(workout['type'])
        distances.append(workout.get('distance', 0) / 1000)
    
    # Create calendar chart
    fig = go.Figure(data=go.Scatter(
        x=dates,
        y=[1] * len(dates),  # All on same line
        mode='markers+text',
        marker=dict(
            size=[d * 2 + 10 for d in distances],  # Size based on distance
            color=distances,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Distance (km)")
        ),
        text=[f"{wt}<br>{d:.1f}km" for wt, d in zip(workout_types, distances)],
        textposition="top center",
        textfont=dict(color='white', size=10)
    ))
    
    fig.update_layout(
        title='Upcoming Training Calendar',
        xaxis_title='Date',
        yaxis=dict(visible=False),
        height=200,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Inter')
    )
    
    fig.update_xaxes(
        gridcolor='rgba(255,255,255,0.2)',
        showgrid=True,
        zeroline=False
    )
    
    return fig

def create_insights_panel(insights_data):
    """Create an insights panel with recommendations and alerts"""
    if not insights_data:
        return '<div class="glass-container"><p>No insights available</p></div>'
    
    html = '<div class="glass-container">'
    html += '<h3 style="color: white; margin-bottom: 1rem;">🧠 AI Insights</h3>'
    
    # Performance notes
    if 'performance_notes' in insights_data and insights_data['performance_notes']:
        html += '<div style="margin-bottom: 1rem;">'
        html += '<h4 style="color: #4ade80;">📈 Performance Notes</h4>'
        html += '<ul style="color: rgba(255,255,255,0.9);">'
        for note in insights_data['performance_notes']:
            html += f'<li>{note}</li>'
        html += '</ul></div>'
    
    # Recommendations
    if 'recommendations' in insights_data and insights_data['recommendations']:
        html += '<div style="margin-bottom: 1rem;">'
        html += '<h4 style="color: #fbbf24;">💡 Recommendations</h4>'
        html += '<ul style="color: rgba(255,255,255,0.9);">'
        for rec in insights_data['recommendations']:
            html += f'<li>{rec}</li>'
        html += '</ul></div>'
    
    # Alerts
    if 'alerts' in insights_data and insights_data['alerts']:
        html += '<div style="margin-bottom: 1rem;">'
        html += '<h4 style="color: #ef4444;">⚠️ Alerts</h4>'
        html += '<ul style="color: rgba(255,255,255,0.9);">'
        for alert in insights_data['alerts']:
            html += f'<li>{alert}</li>'
        html += '</ul></div>'
    
    html += '</div>'
    return html

def create_heart_rate_zones_chart(df):
    """Create heart rate zones analysis chart"""
    if df.empty or 'average_heartrate' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="No heart rate data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color='white')
        )
        return fig
    
    # Filter valid heart rate data
    hr_data = df[df['average_heartrate'].notna() & (df['average_heartrate'] > 0)]['average_heartrate']
    
    if hr_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No valid heart rate data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color='white')
        )
        return fig
    
    # Define HR zones (assuming max HR of 190 for demo)
    max_hr = 190
    zones = {
        'Zone 1 (Recovery)': (0.5 * max_hr, 0.6 * max_hr),
        'Zone 2 (Aerobic)': (0.6 * max_hr, 0.7 * max_hr),
        'Zone 3 (Tempo)': (0.7 * max_hr, 0.8 * max_hr),
        'Zone 4 (Threshold)': (0.8 * max_hr, 0.9 * max_hr),
        'Zone 5 (VO2 Max)': (0.9 * max_hr, 1.0 * max_hr)
    }
    
    # Categorize activities by zone
    zone_counts = {}
    for zone_name, (min_hr, max_hr_zone) in zones.items():
        count = len(hr_data[(hr_data >= min_hr) & (hr_data < max_hr_zone)])
        zone_counts[zone_name] = count
    
    # Create pie chart
    fig = go.Figure(data=[
        go.Pie(
            labels=list(zone_counts.keys()),
            values=list(zone_counts.values()),
            hole=0.4,
            marker_colors=['#22c55e', '#4ade80', '#fbbf24', '#f59e0b', '#ef4444']
        )
    ])
    
    fig.update_layout(
        title='Heart Rate Zone Distribution',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Inter'),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(255,255,255,0.1)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1
        )
    )
    
    return fig

def create_progress_gauge(current_value, target_value, title, unit=""):
    """Create a progress gauge chart"""
    if target_value == 0:
        progress_percentage = 0
    else:
        progress_percentage = min((current_value / target_value) * 100, 100)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=progress_percentage,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"{title}<br><span style='font-size:0.8em'>{current_value:.1f}{unit} / {target_value:.1f}{unit}</span>"},
        delta={'reference': 100},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "#667eea"},
            'steps': [
                {'range': [0, 50], 'color': "rgba(239, 68, 68, 0.3)"},
                {'range': [50, 80], 'color': "rgba(251, 191, 36, 0.3)"},
                {'range': [80, 100], 'color': "rgba(34, 197, 94, 0.3)"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Inter'),
        height=300
    )
    
    return fig
