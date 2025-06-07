import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import json
import asyncio
import websocket
import threading
from dashboard.api_client import APIClient
from dashboard.components import (
    create_metric_card, create_performance_chart, create_status_badge,
    create_training_calendar, create_insights_panel
)
from dashboard.analytics_display import (
    display_performance_analytics, display_team_overview,
    display_athlete_comparison, display_training_trends
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="🏃‍♀️ Marathon AI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🏃‍♀️"
)

# Initialize API client
@st.cache_resource
def get_api_client():
    """Initialize and cache API client"""
    return APIClient()

# Glassmorphism CSS styling
def apply_glassmorphism_style():
    """Apply glassmorphism CSS styling to the Streamlit app"""
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Glass Container Styles */
    .glass-container {
        background: rgba(25, 25, 35, 0.5);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    /* Replit Card Styles */
    .replit-card {
        background: rgba(30, 30, 40, 0.7);
        backdrop-filter: blur(15px);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px 0 rgba(31, 38, 135, 0.2);
    }
    
    .replit-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px 0 rgba(31, 38, 135, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Metric Card Styles */
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        background: rgba(255, 255, 255, 0.15);
        transform: scale(1.02);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.8);
        margin: 5px 0 0 0;
        font-weight: 500;
    }
    
    /* Status Badge Styles */
    .status-on-track {
        background: linear-gradient(135deg, #4ade80, #22c55e);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
    }
    
    .status-warning {
        background: linear-gradient(135deg, #fbbf24, #f59e0b);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
    }
    
    .status-alert {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(220, 38, 38, 0.3);
    }
    
    /* Sidebar Styles */
    .css-1d391kg {
        background: rgba(25, 25, 35, 0.8);
        backdrop-filter: blur(10px);
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Selectbox Styles */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
    }
    
    /* Text Styles */
    .main-title {
        color: white;
        text-align: center;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 2rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .section-title {
        color: white;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    /* Connection Status */
    .connection-status {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
        padding: 8px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .connected {
        background: linear-gradient(135deg, #4ade80, #22c55e);
        color: white;
    }
    
    .disconnected {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# WebSocket connection management
class WebSocketManager:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.last_data = None
    
    def connect(self, athlete_id, jwt_token):
        """Connect to WebSocket for real-time updates"""
        try:
            if self.ws:
                self.ws.close()
            
            # WebSocket URL (adjust based on your Flask-SocketIO setup)
            ws_url = "ws://localhost:5000/socket.io/?EIO=4&transport=websocket"
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    if data.get('type') == 'dashboard_refresh':
                        self.last_data = data.get('data')
                        st.rerun()  # Trigger Streamlit rerun
                except Exception as e:
                    logger.error(f"WebSocket message error: {e}")
            
            def on_error(ws, error):
                logger.error(f"WebSocket error: {error}")
                self.connected = False
            
            def on_close(ws, close_status_code, close_msg):
                logger.info("WebSocket connection closed")
                self.connected = False
            
            def on_open(ws):
                logger.info("WebSocket connection opened")
                self.connected = True
                # Send join room message
                join_message = {
                    "type": "join_dashboard_room",
                    "data": {
                        "athlete_id": athlete_id,
                        "jwt_token": jwt_token
                    }
                }
                ws.send(json.dumps(join_message))
            
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            
            # Run WebSocket in a separate thread
            def run_websocket():
                self.ws.run_forever()
            
            threading.Thread(target=run_websocket, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            self.connected = False

# Initialize WebSocket manager
@st.cache_resource
def get_websocket_manager():
    return WebSocketManager()

def display_connection_status(ws_manager):
    """Display connection status indicator"""
    status_class = "connected" if ws_manager.connected else "disconnected"
    status_text = "🟢 Connected" if ws_manager.connected else "🔴 Disconnected"
    
    st.markdown(f"""
    <div class="connection-status {status_class}">
        {status_text}
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main application function"""
    # Apply styling
    apply_glassmorphism_style()
    
    # Initialize components
    api_client = get_api_client()
    ws_manager = get_websocket_manager()
    
    # Display connection status
    display_connection_status(ws_manager)
    
    # Main title
    st.markdown('<h1 class="main-title">🏃‍♀️ Marathon AI Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar configuration
    st.sidebar.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.sidebar.header("🎯 Navigation")
    
    # Athlete selection
    try:
        athlete_list = api_client.get_athlete_list()
        if not athlete_list:
            athlete_list = ["Team Overview"]
        
        selected_athlete = st.sidebar.selectbox(
            "Select Athlete",
            athlete_list,
            key="athlete_selector"
        )
        
        # Dashboard view selection
        view_options = ["Dashboard", "Analytics", "Training Plan", "Performance Trends"]
        selected_view = st.sidebar.selectbox(
            "Select View",
            view_options,
            key="view_selector"
        )
        
        # Real-time updates toggle
        real_time_enabled = st.sidebar.checkbox(
            "🔄 Real-time Updates",
            value=True,
            help="Enable real-time dashboard updates via WebSocket"
        )
        
        # Date range selector
        st.sidebar.subheader("📅 Date Range")
        date_range = st.sidebar.slider(
            "Days to analyze",
            min_value=7,
            max_value=365,
            value=30,
            help="Select the number of days to include in analysis"
        )
        
    except Exception as e:
        st.sidebar.error(f"Failed to load navigation: {str(e)}")
        selected_athlete = "Team Overview"
        selected_view = "Dashboard"
        real_time_enabled = False
        date_range = 30
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Main content area
    if selected_athlete == "Team Overview":
        display_team_dashboard(api_client, date_range)
    else:
        display_athlete_dashboard(api_client, selected_athlete, selected_view, date_range, ws_manager, real_time_enabled)

def display_team_dashboard(api_client, date_range):
    """Display team overview dashboard"""
    st.markdown('<h2 class="section-title">📊 Team Performance Overview</h2>', unsafe_allow_html=True)
    
    try:
        # Get team overview data
        team_data = api_client.get_team_overview(days=date_range)
        
        if not team_data or 'athlete_details' not in team_data:
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            st.warning("No team data available. Please ensure athletes are properly configured.")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Team metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                "Total Athletes",
                str(team_data.get('total_athletes', 0)),
                "👥"
            ), unsafe_allow_html=True)
        
        with col2:
            total_distance = team_data.get('total_team_distance', 0) / 1000  # Convert to km
            st.markdown(create_metric_card(
                "Team Distance",
                f"{total_distance:.1f} km",
                "🏃‍♀️"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(create_metric_card(
                "Total Activities",
                str(team_data.get('total_team_activities', 0)),
                "📈"
            ), unsafe_allow_html=True)
        
        with col4:
            avg_distance = team_data.get('average_distance_per_athlete', 0) / 1000
            st.markdown(create_metric_card(
                "Avg per Athlete",
                f"{avg_distance:.1f} km",
                "⚡"
            ), unsafe_allow_html=True)
        
        # Team analytics
        display_team_overview(team_data)
        
    except Exception as e:
        st.error(f"Failed to load team dashboard: {str(e)}")
        logger.error(f"Team dashboard error: {e}")

def display_athlete_dashboard(api_client, athlete_name, view, date_range, ws_manager, real_time_enabled):
    """Display individual athlete dashboard"""
    st.markdown(f'<h2 class="section-title">🎽 {athlete_name}\'s Training Dashboard</h2>', unsafe_allow_html=True)
    
    try:
        # Get athlete ID from name
        athlete_id = api_client.get_athlete_id_by_name(athlete_name)
        if not athlete_id:
            st.error(f"Athlete '{athlete_name}' not found")
            return
        
        # Connect WebSocket if real-time is enabled
        if real_time_enabled and not ws_manager.connected:
            # For demo purposes, we'll simulate JWT token
            # In production, this would come from proper authentication
            jwt_token = "demo_jwt_token"
            ws_manager.connect(athlete_id, jwt_token)
        
        # Get athlete dashboard data
        dashboard_data = api_client.get_athlete_dashboard_data(athlete_id)
        performance_summary = api_client.get_athlete_performance_summary(athlete_id, days=date_range)
        
        if view == "Dashboard":
            display_main_dashboard(dashboard_data, performance_summary, athlete_id)
        elif view == "Analytics":
            display_performance_analytics(performance_summary, athlete_id)
        elif view == "Training Plan":
            display_training_plan(api_client, athlete_id)
        elif view == "Performance Trends":
            display_training_trends(performance_summary, athlete_id)
        
    except Exception as e:
        st.error(f"Failed to load athlete dashboard: {str(e)}")
        logger.error(f"Athlete dashboard error: {e}")

def display_main_dashboard(dashboard_data, performance_summary, athlete_id):
    """Display main athlete dashboard"""
    if not dashboard_data and not performance_summary:
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.warning("No data available for this athlete. Please check if they have completed any activities.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Recent performance metrics
    if performance_summary:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            distance = performance_summary.get('total_distance', 0) / 1000
            st.markdown(create_metric_card(
                "Total Distance",
                f"{distance:.1f} km",
                "🏃‍♀️"
            ), unsafe_allow_html=True)
        
        with col2:
            activities = performance_summary.get('total_activities', 0)
            st.markdown(create_metric_card(
                "Activities",
                str(activities),
                "📊"
            ), unsafe_allow_html=True)
        
        with col3:
            time_minutes = performance_summary.get('total_training_time', 0) // 60
            st.markdown(create_metric_card(
                "Training Time",
                f"{time_minutes} min",
                "⏱️"
            ), unsafe_allow_html=True)
        
        with col4:
            active_days = performance_summary.get('active_days', 0)
            st.markdown(create_metric_card(
                "Active Days",
                str(active_days),
                "📅"
            ), unsafe_allow_html=True)
    
    # Recent activity summary
    if dashboard_data:
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.subheader("📈 Recent Activity Summary")
        
        # Create DataFrame from recent summaries
        recent_summaries = performance_summary.get('recent_summaries', [])
        if recent_summaries:
            df = pd.DataFrame(recent_summaries)
            df['date'] = pd.to_datetime(df['date'])
            df['distance_km'] = df['distance'] / 1000
            
            # Performance chart
            chart = create_performance_chart(df)
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.info("No recent activity data available")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Advanced Analytics Section - Race Predictor and Risk Analyser
    display_advanced_analytics(athlete_id)
    
    # Training insights
    display_training_insights(performance_summary)

def display_training_insights(performance_summary):
    """Display training insights and recommendations"""
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.subheader("🧠 Training Insights")
    
    if not performance_summary:
        st.info("No performance data available for insights")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Calculate insights
    total_distance = performance_summary.get('total_distance', 0) / 1000
    active_days = performance_summary.get('active_days', 0)
    avg_weekly_distance = performance_summary.get('average_weekly_distance', 0) / 1000
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Performance Highlights:**")
        if total_distance > 100:
            st.success("🎉 Excellent distance coverage this period!")
        elif total_distance > 50:
            st.info("👍 Good progress on distance goals")
        else:
            st.warning("📈 Consider increasing weekly distance gradually")
        
        if active_days >= 20:
            st.success("🔥 Outstanding training consistency!")
        elif active_days >= 15:
            st.info("✅ Good training frequency")
        else:
            st.warning("📅 Try to maintain more consistent training")
    
    with col2:
        st.markdown("**Recommendations:**")
        
        if avg_weekly_distance < 30:
            st.info("🎯 Focus on building base mileage")
        elif avg_weekly_distance > 80:
            st.warning("⚠️ Monitor for overtraining - ensure adequate recovery")
        else:
            st.success("✅ Good weekly distance balance")
        
        # Add more personalized recommendations
        st.info("💡 Consider adding strength training sessions")
        st.info("🧘 Include recovery and stretching in your routine")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_advanced_analytics(athlete_id):
    """Display Race Predictor and Risk Analyser side by side with perfect alignment"""
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.subheader("🔬 Advanced Performance Analytics")
    
    # Create two equal columns for perfect alignment
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚡ Race Predictor")
        try:
            # Fetch race prediction data
            import requests
            race_response = requests.get(f"http://localhost:5000/api/athletes/{athlete_id}/race-prediction?distance=Marathon")
            if race_response.status_code == 200:
                race_data = race_response.json()
                
                # Display marathon prediction
                st.markdown("**Marathon Prediction:**")
                
                time_str = race_data.get('predicted_time_formatted', 'N/A')
                confidence = race_data.get('confidence_score', 0) / 100
                distance = race_data.get('race_distance', 'Marathon')
                
                # Color coding based on confidence
                if confidence > 0.8:
                    confidence_color = "🟢"
                elif confidence > 0.6:
                    confidence_color = "🟡"
                else:
                    confidence_color = "🔴"
                
                st.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.2); padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #10b981;">
                    <h4 style="margin: 0; color: #10b981;">{distance}</h4>
                    <h2 style="margin: 5px 0; color: white;">{time_str}</h2>
                    <small>{confidence_color} Confidence: {confidence:.0%}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Fetch additional race distances
                other_distances = ['5K', '10K', 'Half Marathon']
                for dist in other_distances:
                    try:
                        dist_response = requests.get(f"http://localhost:5000/api/athletes/{athlete_id}/race-prediction?distance={dist}")
                        if dist_response.status_code == 200:
                            dist_data = dist_response.json()
                            dist_time = dist_data.get('predicted_time_formatted', 'N/A')
                            dist_conf = dist_data.get('confidence_score', 0) / 100
                            
                            conf_color = "🟢" if dist_conf > 0.8 else "🟡" if dist_conf > 0.6 else "🔴"
                            
                            st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.1); padding: 8px; border-radius: 6px; margin: 3px 0;">
                                <strong>{dist}:</strong> {dist_time} <small>{conf_color} {dist_conf:.0%}</small>
                            </div>
                            """, unsafe_allow_html=True)
                    except:
                        pass
                
                # Training recommendations
                recommendations = race_data.get('training_recommendations', [])
                if recommendations:
                    st.markdown("**Training Focus:**")
                    for rec in recommendations[:3]:
                        st.markdown(f"• {rec}")
                        
            else:
                st.warning("Race prediction data unavailable")
                
        except Exception as e:
            st.error(f"Unable to load race predictor: {str(e)}")
    
    with col2:
        st.markdown("### 🛡️ Risk Analyser")
        try:
            # Fetch injury risk data
            risk_response = requests.get(f"http://localhost:5000/api/injury-risk/{athlete_id}")
            if risk_response.status_code == 200:
                risk_data = risk_response.json()
                
                # Display risk assessment
                risk_assessment = risk_data.get('risk_assessment', {})
                overall_risk = risk_assessment.get('overall_risk', 0)
                risk_level = risk_assessment.get('risk_level', 'unknown')
                
                # Risk level visualization
                risk_color = {
                    'low': '#10b981',
                    'moderate': '#f59e0b', 
                    'high': '#ef4444'
                }.get(risk_level, '#6b7280')
                
                st.markdown(f"""
                <div style="background: {risk_color}; padding: 15px; border-radius: 10px; text-align: center; color: white; margin: 10px 0;">
                    <h4 style="margin: 0; color: white;">Risk Level: {risk_level.upper()}</h4>
                    <h2 style="margin: 5px 0; color: white;">{overall_risk:.0%}</h2>
                </div>
                """, unsafe_allow_html=True)
                
                # Key risk factors
                risk_factors = risk_assessment.get('risk_factors', [])
                if risk_factors:
                    st.markdown("**Key Risk Factors:**")
                    for factor in risk_factors[:3]:
                        st.markdown(f"⚠️ {factor}")
                
                # Top prevention strategies
                prevention = risk_data.get('prevention_strategies', [])
                if prevention:
                    st.markdown("**Prevention Focus:**")
                    for strategy in prevention[:3]:
                        st.markdown(f"✅ {strategy}")
                        
            else:
                st.warning("Risk analysis data unavailable")
                
        except Exception as e:
            st.error(f"Unable to load risk analyser: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_training_plan(api_client, athlete_id):
    """Display training plan view"""
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.subheader("📋 Training Plan")
    
    try:
        # Get upcoming workouts
        upcoming_workouts = api_client.get_upcoming_workouts(athlete_id)
        
        if upcoming_workouts:
            st.markdown("**Upcoming Workouts:**")
            for workout in upcoming_workouts:
                workout_date = datetime.fromisoformat(workout['date']).strftime('%Y-%m-%d')
                distance = workout.get('distance', 0) / 1000 if workout.get('distance') else 0
                
                with st.expander(f"{workout_date} - {workout['type']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Distance:** {distance:.1f} km")
                        st.write(f"**Type:** {workout['type']}")
                    with col2:
                        if workout.get('duration'):
                            duration_min = workout['duration'] // 60
                            st.write(f"**Duration:** {duration_min} minutes")
                        st.write(f"**Status:** Planned")
        else:
            st.info("No upcoming workouts scheduled")
        
        # Training calendar visualization
        st.subheader("📅 Training Calendar")
        calendar_component = create_training_calendar(upcoming_workouts)
        st.plotly_chart(calendar_component, use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to load training plan: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
