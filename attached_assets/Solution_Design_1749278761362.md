# Marathon Training Dashboard \- Enhanced Solution Design Document

## Table of Contents

1. [Executive Summary](#bookmark=id.r3uz372t6tl)  
2. [Enhanced System Architecture](#bookmark=id.3wqalwm78cvt)  
3. [Futuristic UI/UX Design](#bookmark=id.38mpg2ntubz3)  
4. [Enhanced Component Design](#bookmark=id.ftgx54b00kgg)  
5. [Advanced Data Models](#bookmark=id.6nyjv4mbxooq)  
6. [Improved API Design](#bookmark=id.etuxdavd9utf)  
7. [Security & Authentication Best Practices](#bookmark=id.arnvhb6ue7h)  
8. [Enhanced Database Design](#bookmark=id.lzhdp9ptcv6c)  
9. [External Integrations](#bookmark=id.97iiuscdst37)  
10. [Advanced Processing Workflows](#bookmark=id.uduk182ff1iy)  
11. [Production-Ready Deployment](#bookmark=id.80z3gr12oqm)  
12. [Performance & Monitoring](#bookmark=id.3g24fk2x178b)  
13. [Error Handling & Observability](#bookmark=id.201i545ff9uh)  
14. [Future Enhancements](#bookmark=id.3mjc8jxgjyd7)

## Executive Summary

The enhanced Marathon Training Dashboard leverages your Flask \+ Streamlit \+ pandas \+ stravalib stack while incorporating industry best practices for scalability, security, and user experience. The solution features a futuristic, immersive dashboard design with real-time analytics, predictive insights, and enterprise-grade reliability optimized for Replit deployment. **Crucially, the design emphasizes robust multi-athlete support, ensuring error-free operation and future-proofing for a growing user base.**

### Key Enhancements

* **Futuristic Streamlit UI**: Glassmorphism design with 3D visualizations, **designed to effectively display individual and team-level insights for multiple athletes.**  
* **AI-Powered Analytics**: Predictive modeling using pandas and scikit-learn, **scalable to analyze data across many athletes.**  
* **Real-time Processing**: WebSocket integration for live updates, **with athlete-specific data pushing.**  
* **Enhanced Security**: JWT authentication with refresh tokens, **ensuring secure access for each athlete.**  
* **Replit-Optimized**: Single-platform deployment with efficient resource usage, **considering shared resources for multi-athlete operations.**  
* **Smart Notifications**: Personalized AI-driven recommendations, **delivered via email, configured per athlete.**  
* **Robust Multi-Athlete Handling**: Explicit design for parallel data processing, isolated error handling, and personalized experiences for each user.

## Enhanced System Architecture

### Replit-Optimized Architecture

┌──────────────────────────────┐    ┌──────────────────────────────┐  
│      Streamlit Dashboard     │◄──►│        Flask Backend         │  
│ (Port 8501 \- Replit proxy)   │    │ (Port 5000 \- API & Auth)     │  
└───────────────┬──────────────┘    └───────────────┬──────────────┘  
                │                                   │  
┌───────────────▼──────────────┐    ┌───────────────▼──────────────┐  
│        Replit Platform       │    │       External Services      │  
│  \- SQLite/PostgreSQL         │    │  \- Strava API (stravalib)    │  
│  \- Ephemeral storage         │    │  \- Weather API               │  
│  \- Mail Service (SMTP)       │    │  \- Mail Service (SMTP)       │  
└──────────────────────────────┘    └──────────────────────────────┘

### Technology Stack

\# Core Framework (Replit-compatible)  
BACKEND\_STACK \= {  
    "framework": "Flask 3.0+",  
    "database": "SQLite/PostgreSQL via SQLAlchemy 2.0+",  
    "data\_processing": "pandas 2.0+",  
    "ui\_framework": "Streamlit 1.28+",  
    "api\_client": "stravalib 1.0+"  
}

\# Enhanced Dependencies (Replit-compatible)  
ENHANCED\_STACK \= {  
    "security": \["flask-jwt-extended", "cryptography"\],  
    "caching": \["flask-caching"\],  
    "ml\_analytics": \["scikit-learn", "numpy"\],  
    "real\_time": \["flask-socketio"\],  
    "validation": \["marshmallow"\], \# Added for robust input validation  
    "async\_tasks": \["apscheduler", "concurrent.futures"\], \# concurrent.futures for ThreadPoolExecutor  
    "testing": \["pytest"\]  
}

## Futuristic UI/UX Design

### Replit-Optimized Streamlit Components

def create\_replit\_dashboard():  
    st.set\_page\_config(  
        page\_title="🏃‍♀️ Marathon AI Dashboard",  
        layout="wide",  
        initial\_sidebar\_state="expanded"  
    )  
      
    \# Glassmorphism CSS optimized for Replit  
    st.markdown("""  
    \<style\>  
    .glass-container {  
        background: rgba(25, 25, 35, 0.5);  
        backdrop-filter: blur(10px);  
        border-radius: 15px;  
        border: 1px solid rgba(255, 255, 255, 0.1);  
        padding: 15px;  
        margin: 10px 0;  
    }  
    .replit-card {  
        background: rgba(30, 30, 40, 0.7);  
        border-radius: 12px;  
        padding: 15px;  
        transition: transform 0.3s;  
    }  
    .replit-card:hover {  
        transform: translateY(-5px);  
    }  
    \</style\>  
    """, unsafe\_allow\_html=True)

    \# Sidebar for athlete selection and navigation  
    st.sidebar.header("Athlete Selection")  
    \# This dropdown will be populated dynamically from the Flask backend via API  
    athlete\_names \= get\_athlete\_list\_from\_api() \# Placeholder function  
    selected\_athlete \= st.sidebar.selectbox("Select Athlete", athlete\_names)

    \# Display individual athlete data or team-level aggregated data  
    if selected\_athlete \== "Team Overview": \# Example for a team view  
        st.title("Team Performance Dashboard")  
        \# Logic to fetch and display aggregated team data using pandas  
        \# ...  
    else:  
        st.title(f"{selected\_athlete}'s Training Dashboard")  
        \# Logic to fetch and display individual athlete data using pandas  
        \# Real-time metrics display \- fetches data specific to selected\_athlete  
        col1, col2, col3, col4 \= st.columns(4)  
        with col1:  
            st.markdown("""\<div class="replit-card glass-container"\>...\</div\>""",   
                       unsafe\_allow\_html=True)  
        \# Add more components for detailed individual analytics, charts, etc.

## Enhanced Component Design

### Replit-Optimized Analytics Engine

import joblib  
import pandas as pd  
from typing import Dict, Any

class ReplitAnalyticsEngine:  
    """  
    Memory-efficient analytics for Replit environment, designed for multi-athlete data.  
    Utilizes pandas for efficient in-memory data manipulation.  
    """  
      
    def \_\_init\_\_(self):  
        self.models \= self.load\_lightweight\_models()  
          
    def load\_lightweight\_models(self) \-\> Dict\[str, Any\]:  
        """  
        Load optimized ML models for Replit.  
        Models should be pre-trained and saved in a lightweight format (e.g., joblib).  
        """  
        try:  
            \# Ensure models directory exists and models are available  
            return {  
                'performance\_predictor': joblib.load('data/models/light\_perf\_model.pkl'),  
                'injury\_risk\_model': joblib.load('data/models/light\_risk\_model.pkl')  
            }  
        except FileNotFoundError:  
            logging.error("ML model files not found. Ensure they are in 'data/models/'")  
            \# Fallback or raise error, depending on criticality  
            return {}  
      
    def get\_sampled\_training\_data(self, athlete\_id: int) \-\> pd.DataFrame:  
        """  
        Efficiently retrieve and sample training data for a specific athlete.  
        This prevents loading all historical data into memory at once for prediction.  
        """  
        \# Placeholder: In a real app, this would query the database  
        \# and convert the results to a pandas DataFrame.  
        \# For large datasets, consider sampling or loading only relevant data.  
        \# Example: Fetch last N activities or activities within a specific date range.  
        \# For simplicity, returning dummy data:  
        data \= {  
            'distance': \[10, 12, 8, 15, 9\],  
            'pace': \[5.0, 5.1, 5.2, 4.8, 5.3\],  
            'heart\_rate': \[150, 155, 148, 160, 152\]  
        }  
        df \= pd.DataFrame(data)  
        \# Add athlete\_id for context if the model is general  
        df\['athlete\_id'\] \= athlete\_id  
        return df \# Or a subset for sampling

    def predict\_race\_performance(self, athlete\_id: int, race\_distance: float) \-\> float:  
        """  
        Predict race performance for a specific athlete using their training data.  
        Assumes the 'performance\_predictor' model is designed to handle per-athlete data.  
        """  
        if 'performance\_predictor' not in self.models:  
            logging.warning("Performance predictor model not loaded. Cannot make prediction.")  
            return \-1.0 \# Or raise an appropriate error

        training\_data \= self.get\_sampled\_training\_data(athlete\_id)  
        \# Ensure the input features for prediction match the model's expected format  
        \# This might involve feature engineering on \`training\_data\`  
          
        \# Dummy prediction for demonstration  
        if not training\_data.empty:  
            avg\_pace \= training\_data\['pace'\].mean()  
            \# A very simplistic model: prediction based on average pace and race distance  
            predicted\_time \= avg\_pace \* race\_distance  
            return predicted\_time  
        return float('nan') \# Return NaN if no data

## Advanced Data Models

import datetime  
from sqlalchemy.ext.declarative import declarative\_base  
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, BigInteger, Text, ForeignKey  
from sqlalchemy.orm import relationship  
from sqlalchemy.dialects.postgresql import JSONB \# Use JSONB for PostgreSQL, JSON for SQLite

\# Assuming db is already initialized with SQLAlchemy Base  
Base \= declarative\_base() \# This would typically be passed from \_\_init\_\_.py

class ReplitAthlete(Base):  
    """  
    Optimized for Replit's SQLite/PostgreSQL, handling multiple athletes.  
    Includes fields for personalized settings and performance benchmarks.  
    """  
    \_\_tablename\_\_ \= 'athletes'  
      
    id \= Column(Integer, primary\_key=True)  
    name \= Column(String(100), nullable=False)  
    email \= Column(String(255), unique=True, nullable=False) \# For email notifications  
    strava\_athlete\_id \= Column(BigInteger, unique=True, nullable=False)  
    refresh\_token \= Column(Text, nullable=False)  
    access\_token \= Column(Text) \# Can be null if not current  
    token\_expires\_at \= Column(DateTime)  
    is\_active \= Column(Boolean, default=True) \# Flag for active/inactive athletes  
      
    \# Performance metrics (personalized benchmarks)  
    ftp \= Column(Float) \# Functional Threshold Power  
    lthr \= Column(Integer) \# Lactate Threshold Heart Rate  
    max\_hr \= Column(Integer) \# Maximum Heart Rate  
      
    \# Replit-optimized JSON fields for flexible, non-indexed data  
    \# Use JSONB for PostgreSQL for better performance with JSON queries  
    \# For SQLite, SQLAlchemy's JSON type stores as TEXT  
    training\_zones \= Column(Text) \# e.g., {'hr\_zones': \[..\], 'power\_zones': \[..\]} (JSON string for SQLite)  
    preferences \= Column(Text) \# e.g., {'notification\_daily\_summary': True, 'unit\_preference': 'km'} (JSON string for SQLite)

    created\_at \= Column(DateTime, default=datetime.datetime.now)  
    updated\_at \= Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def \_\_repr\_\_(self):  
        return f"\<ReplitAthlete(id={self.id}, name='{self.name}', strava\_id={self.strava\_athlete\_id})\>"

\# Example of an enhanced Activity Model for more detailed data points  
class Activity(Base):  
    \_\_tablename\_\_ \= 'activities'

    id \= Column(Integer, primary\_key=True)  
    strava\_activity\_id \= Column(BigInteger, unique=True, nullable=False)  
    athlete\_id \= Column(Integer, ForeignKey('athletes.id'), nullable=False)  
    \# Basic metrics  
    name \= Column(String(255), nullable=False)  
    activity\_type \= Column(String(50)) \# e.g., 'Run', 'Ride'  
    start\_date \= Column(DateTime, nullable=False)  
    distance\_km \= Column(Float)  
    moving\_time\_seconds \= Column(Integer)  
    pace\_min\_per\_km \= Column(Float)  
    average\_speed \= Column(Float)  
    total\_elevation\_gain \= Column(Float)

    \# Detailed metrics for advanced analytics  
    average\_heartrate \= Column(Float)  
    max\_heartrate \= Column(Float)  
    average\_cadence \= Column(Float)  
    average\_watts \= Column(Float) \# For cycling power  
    \# Consider adding a JSON field for raw Strava streams if detailed analysis needed  
    raw\_stream\_data \= Column(Text) \# e.g., { 'latlng': \[\[..\]\], 'altitude': \[..\] } (JSON string for SQLite)

    created\_at \= Column(DateTime, default=datetime.datetime.now)

    athlete \= relationship("ReplitAthlete", backref="activities") \# Relationship

    def \_\_repr\_\_(self):  
        return f"\<Activity(id={self.id}, athlete\_id={self.athlete\_id}, type='{self.activity\_type}', date={self.start\_date})\>"

\# Consider a dedicated Notifications model to track sent emails and user preferences  
class NotificationLog(Base):  
    \_\_tablename\_\_ \= 'notification\_logs'  
    id \= Column(Integer, primary\_key=True)  
    athlete\_id \= Column(Integer, ForeignKey('athletes.id'))  
    notification\_type \= Column(String(50), nullable=False) \# e.g., 'daily\_summary', 'performance\_alert'  
    status \= Column(String(20), nullable=False) \# 'sent', 'failed', 'queued'  
    message \= Column(Text)  
    timestamp \= Column(DateTime, default=datetime.datetime.now)

    athlete \= relationship("ReplitAthlete", backref="notification\_logs")

    def \_\_repr\_\_(self):  
        return f"\<NotificationLog(id={self.id}, athlete\_id={self.athlete\_id}, type='{self.notification\_type}', status='{self.status}')\>"

\# Note: All models should be part of the same declarative base and correctly imported  
\# into your Flask application's database setup.

## Improved API Design

### Replit-Compatible API Endpoints

from flask import jsonify, request  
from flask\_restx import Api, Resource, fields  
from flask\_jwt\_extended import jwt\_required, get\_jwt\_identity, decode\_token  
from flask\_socketio import SocketIO, emit, join\_room, leave\_room  
import logging  
import sys  
\# Assuming models are in a relative path within the 'app' directory  
from app.models import ReplitAthlete, DailySummary, NotificationLog   
\# Assuming data\_processor is in a relative path within the 'app' directory  
from app.data\_processor import get\_athlete\_performance\_summary, get\_team\_overview 

\# Flask-RESTx API with JWT  
api \= Api(title='Marathon API', version='2.0', doc='/api/docs/',  
          description='API for Marathon Training Dashboard, optimized for multi-athlete data.')

\# Define API models for better documentation and validation  
athlete\_model \= api.model('Athlete', {  
    'id': fields.Integer(readOnly=True, description='The unique identifier of an athlete'),  
    'name': fields.String(required=True, description='The athlete\\'s name'),  
    'email': fields.String(required=True, description='The athlete\\'s email for notifications'),  
    'strava\_athlete\_id': fields.Integer(description='Strava Athlete ID'),  
    'is\_active': fields.Boolean(description='Is the athlete active in the system?'),  
    \# Add other fields as needed for exposure via API  
})

daily\_summary\_model \= api.model('DailySummary', {  
    'summary\_date': fields.Date(description='Date of the summary'),  
    'actual\_distance\_km': fields.Float(description='Actual distance covered'),  
    'planned\_distance\_km': fields.Float(description='Planned distance'),  
    'distance\_variance\_percent': fields.Float(description='Variance in distance'),  
    'status': fields.String(description='Performance status (e.g., On Track, Under-performed)'),  
})

@api.route('/api/athletes')  
class AthletesList(Resource):  
    @jwt\_required()  
    @api.doc(security='Bearer')  
    @api.marshal\_list\_of(athlete\_model)  
    def get(self):  
        """Get a list of all active athletes (admin/team lead view) or current athlete."""  
        current\_user\_id \= get\_jwt\_identity()  
        \# In a multi-athlete system, this endpoint might return all athletes for an admin  
        \# or just the current athlete for a regular user.  
        \# Add authorization logic here to differentiate.  
        \# For now, assuming it returns all active athletes for simplicity or based on role  
        athletes \= ReplitAthlete.query.filter\_by(is\_active=True).all()  
        return athletes, 200

@api.route('/api/athlete/\<int:athlete\_id\>/dashboard-data')  
class AthleteDashboardData(Resource):  
    @jwt\_required()  
    @api.doc(security='Bearer')  
    @api.marshal\_with(daily\_summary\_model, as\_list=True) \# Assuming list of daily summaries  
    def get(self, athlete\_id):  
        """  
        Get dashboard data for a specific athlete.  
        Ensures an athlete can only access their own data unless admin.  
        """  
        current\_user\_id \= get\_jwt\_identity()  
        \# In a real application, you'd fetch the user's role or check if they are an admin  
        \# For simplicity, enforce strict personal data access unless specifically allowed.  
        if current\_user\_id \!= athlete\_id:  
            api.abort(403, "Forbidden: You can only access your own data or data you are authorized for.")

        \# Fetch data using optimized functions (e.g., from data\_processor)  
        \# This will need access to the SQLAlchemy session  
        \# from app import db\_session \# Assuming db\_session is available globally or passed  
        \# summary\_data \= get\_athlete\_performance\_summary(db\_session, athlete\_id)   
        \# For placeholder, return dummy data  
        summary\_data \= \[{"summary\_date": "2025-06-06", "actual\_distance\_km": 10.5,   
                         "planned\_distance\_km": 10.0, "distance\_variance\_percent": 5.0, "status": "On Track"}\]  
        return summary\_data, 200

@api.route('/api/realtime-dashboard')  
class RealtimeDashboard(Resource):  
    @jwt\_required()  
    @api.doc(security='Bearer')  
    def get(self):  
        """Get lightweight dashboard data for Replit."""  
        current\_user\_id \= get\_jwt\_identity()  
        \# Data fetched will be specific to the current\_user\_id  
        return {  
            'performance': get\_cached\_performance(current\_user\_id), \# Cache per-athlete  
            'upcoming': get\_upcoming\_workouts(current\_user\_id),  
            'notifications': get\_recent\_notifications(current\_user\_id)  
        }, 200

\# WebSocket for real-time updates (Streamlit connection)  
socketio \= SocketIO(cors\_allowed\_origins="\*") \# Configure CORS for Replit environment for local development/testing

@socketio.on('join\_dashboard\_room')  
def on\_join\_dashboard\_room(data):  
    """  
    Allows a client (Streamlit dashboard) to join a room specific to an athlete.  
    This enables targeted real-time updates for individual dashboards.  
    Data should contain 'athlete\_id' and a 'jwt\_token' for authentication.  
    """  
    athlete\_id \= data.get('athlete\_id')  
    jwt\_token \= data.get('jwt\_token')

    if not athlete\_id or not jwt\_token:  
        emit('error', {'message': 'Missing athlete\_id or token'})  
        return

    try:  
        \# Verify JWT token to ensure the client is authorized for this athlete\_id  
        \# This is a crucial security step.  
        \# The JWTManager must be initialized in your Flask app instance (app/\_\_init\_\_.py)  
        \# and its secret key must match the one used for token creation.  
        \# For the WebSocket context, you might need a helper method from ReplitSecurity  
        \# or \`flask\_jwt\_extended.decode\_token\` directly.  
        decoded\_token \= decode\_token(jwt\_token)  
        identity \= decoded\_token.get('sub') \# 'sub' is the default identity key in JWT  
          
        if identity \!= athlete\_id:  
            logging.warning(f"Unauthorized WebSocket join attempt for athlete {athlete\_id} by identity {identity}")  
            emit('error', {'message': 'Unauthorized access: Token does not match athlete ID'})  
            return

        room\_name \= f'athlete\_{athlete\_id}'  
        join\_room(room\_name)  
        logging.info(f"Client joined room: {room\_name}")  
        emit('status', {'message': f'Joined dashboard for athlete {athlete\_id}'}, room=room\_name)

        \# Send initial data upon joining  
        initial\_data \= get\_lightweight\_update(athlete\_id) \# Per-athlete update  
        emit('dashboard\_refresh', initial\_data, room=room\_name)

    except Exception as e:  
        logging.error(f"Failed to join room for athlete {athlete\_id} due to: {e}", exc\_info=True)  
        emit('error', {'message': f'Authentication or server error: {e}'})

@socketio.on('disconnect')  
def on\_disconnect():  
    logging.info("Client disconnected from WebSocket.")

\# Example function to send real-time update to a specific athlete's dashboard  
def send\_athlete\_update(athlete\_id: int, data: Dict):  
    """Sends a real-time update to a specific athlete's dashboard."""  
    room\_name \= f'athlete\_{athlete\_id}'  
    logging.info(f"Emitting update to room: {room\_name} with data: {data}")  
    socketio.emit('dashboard\_refresh', data, room=room\_name)

\# Example: Periodically push data using APScheduler (configured in Flask app's \_\_init\_\_.py)  
\# from apscheduler.schedulers.background import BackgroundScheduler  
\# scheduler \= BackgroundScheduler()  
\# scheduler.add\_job(lambda: send\_athlete\_update(1, get\_lightweight\_update(1)), 'interval', seconds=60)  
\# scheduler.start()

\# Placeholder for functions that fetch cached/lightweight data for a specific athlete  
def get\_cached\_performance(athlete\_id: int) \-\> Dict:  
    \# Retrieve performance data for a specific athlete, potentially from a cache  
    \# In a real app, this would query the DB for the athlete's latest performance metrics  
    return {"current\_pace": 4.5, "distance\_this\_week": 50.0, "athlete\_id": athlete\_id}

def get\_upcoming\_workouts(athlete\_id: int) \-\> List\[Dict\]:  
    \# Retrieve upcoming workouts for a specific athlete  
    \# In a real app, this would query PlannedWorkout model for the athlete  
    return \[{"date": "2025-06-10", "type": "Long Run"}, {"date": "2025-06-12", "type": "Intervals"}\]

def get\_recent\_notifications(athlete\_id: int) \-\> List\[Dict\]:  
    \# Retrieve recent notifications for a specific athlete  
    \# In a real app, this would query NotificationLog model for the athlete  
    return \[{"message": "Great run yesterday\!", "timestamp": "2025-06-06T10:00:00Z"}\]

def get\_lightweight\_update(athlete\_id: int) \-\> Dict:  
    """Consolidates data for a lightweight, per-athlete dashboard update."""  
    return {  
        'performance\_metrics': get\_cached\_performance(athlete\_id),  
        'notifications\_feed': get\_recent\_notifications(athlete\_id)  
    }

def get\_athlete\_list\_from\_api() \-\> List\[str\]:  
    """  
    Placeholder: In Streamlit, this would call /api/athletes to get the list.  
    This function simulates that API call for the UI component.  
    """  
    \# This would typically be a fetch call in the Streamlit app to the Flask backend  
    \# Example: response \= requests.get(FLASK\_API\_URL \+ '/api/athletes', headers={'Authorization': 'Bearer ' \+ st.session\_state.jwt\_token})  
    \# For now, dummy data  
    return \["Team Overview", "Alice", "Bob", "Charlie"\]

## Security & Authentication Best Practices

### Replit-Optimized Security

from flask import jsonify  
from flask\_jwt\_extended import JWTManager, create\_access\_token, create\_refresh\_token, jwt\_required, get\_jwt\_identity, decode\_token  
from datetime import timedelta  
import secrets  
import logging  
from typing import Dict, Any

class ReplitSecurity:  
    """  
    JWT implementation for Replit environment, handling multi-user authentication.  
    Ensures secure token generation and management.  
    """  
      
    def \_\_init\_\_(self, app):  
        app.config\['JWT\_SECRET\_KEY'\] \= secrets.token\_urlsafe(64) \# Generate a strong secret key for production  
        app.config\['JWT\_ACCESS\_TOKEN\_EXPIRES'\] \= timedelta(minutes=15) \# Short-lived access token  
        app.config\['JWT\_REFRESH\_TOKEN\_EXPIRES'\] \= timedelta(days=30) \# Longer-lived refresh token  
        \# Ensure JWTManager is initialized only once per app instance  
        self.jwt \= JWTManager(app)

        \# Register custom error handlers for JWT for more descriptive responses  
        @self.jwt.unauthorized\_loader  
        def unauthorized\_response(callback: str) \-\> tuple\[dict, int\]:  
            logging.warning(f"Unauthorized access attempt: {callback}")  
            return jsonify({"message": "Missing or invalid token. Please log in.", "error": "unauthorized"}), 401

        @self.jwt.invalid\_token\_loader  
        def invalid\_token\_response(callback: str) \-\> tuple\[dict, int\]:  
            logging.warning(f"Invalid token: {callback}")  
            return jsonify({"message": "Token signature verification failed or token is malformed.", "error": "invalid\_token"}), 401

        @self.jwt.expired\_token\_loader  
        def expired\_token\_response(jwt\_header: dict, jwt\_payload: dict) \-\> tuple\[dict, int\]:  
            logging.warning(f"Expired token. Expiration: {jwt\_payload\['exp'\]}")  
            return jsonify({"message": "Your session has expired. Please refresh your token or re-authenticate.", "error": "token\_expired"}), 401

        @self.jwt.revoked\_token\_loader  
        def revoked\_token\_response(jwt\_header: dict, jwt\_payload: dict) \-\> tuple\[dict, int\]:  
            logging.warning(f"Revoked token detected: {jwt\_payload\['jti'\]}")  
            return jsonify({"message": "This token has been revoked.", "error": "token\_revoked"}), 401  
      
    def create\_tokens(self, athlete\_id: int) \-\> Dict\[str, str\]:  
        """  
        Create access and refresh tokens for a given athlete.  
        The \`identity\` in JWT will be the athlete\_id, allowing per-user access control.  
        """  
        access\_token \= create\_access\_token(identity=athlete\_id, fresh=True)  
        refresh\_token \= create\_refresh\_token(identity=athlete\_id)  
        logging.info(f"Tokens created for athlete\_id: {athlete\_id}")  
        return {  
            'access\_token': access\_token,  
            'refresh\_token': refresh\_token  
        }

    @staticmethod  
    def verify\_token\_identity(token: str, expected\_athlete\_id: int) \-\> bool:  
        """  
        Verifies a JWT token and checks if its identity matches the expected athlete ID.  
        This is particularly useful for WebSocket connections where \`@jwt\_required\`  
        decorators are not directly applicable or for manual token validation.  
        """  
        try:  
            \# Decode token without necessarily validating expiration etc. if using a fresh token check  
            \# For strict validation, JWTManager's internal functions or full token verify might be better.  
            decoded\_token \= decode\_token(token)  
            identity \= decoded\_token.get('sub') \# 'sub' is the default identity claim

            if identity \== expected\_athlete\_id:  
                return True  
            logging.warning(f"Token identity mismatch: Expected {expected\_athlete\_id}, Got {identity} for token {token\[:10\]}...")  
            return False  
        except Exception as e:  
            logging.error(f"Token verification failed for token {token\[:10\]}...: {e}", exc\_info=True)  
            return False

## Enhanced Database Design

### Replit-Optimized Schema

\-- Optimized indexes for Replit's SQLite/PostgreSQL, critical for multi-athlete performance  
\-- These indexes help in quickly querying data specific to an athlete or date range.  
CREATE INDEX idx\_activity\_athlete\_date ON activities(athlete\_id, start\_date DESC); \-- Added DESC for common time-series queries  
CREATE INDEX idx\_daily\_summary\_athlete\_date ON daily\_summaries(athlete\_id, summary\_date DESC);  
CREATE INDEX idx\_daily\_summary\_date ON daily\_summaries(summary\_date DESC);  
CREATE INDEX idx\_activity\_strava\_id ON activities(strava\_activity\_id);  
CREATE UNIQUE INDEX idx\_athletes\_email ON athletes(email); \-- Ensure unique emails for notification  
CREATE UNIQUE INDEX idx\_planned\_workout\_athlete\_date ON planned\_workouts(athlete\_id, workout\_date); \-- Ensure one plan per athlete per day  
CREATE UNIQUE INDEX idx\_daily\_summary\_athlete\_date\_unique ON daily\_summaries(athlete\_id, summary\_date); \-- Ensure one summary per athlete per day  
CREATE UNIQUE INDEX idx\_optimal\_values\_athlete\_id ON optimal\_values(athlete\_id); \-- One optimal values record per athlete

\-- Memory-efficient table definitions (from Advanced Data Models section)  
\-- Using TEXT for JSON fields when using SQLite (as JSONB is PostgreSQL specific)  
CREATE TABLE IF NOT EXISTS athletes (  
    id INTEGER PRIMARY KEY AUTOINCREMENT, \-- AUTOINCREMENT for SQLite  
    name TEXT NOT NULL,  
    email TEXT UNIQUE NOT NULL,  
    strava\_athlete\_id INTEGER UNIQUE NOT NULL,  
    refresh\_token TEXT NOT NULL,  
    access\_token TEXT,  
    token\_expires\_at DATETIME,  
    is\_active BOOLEAN DEFAULT 1,  
    ftp REAL,  
    lthr INTEGER,  
    max\_hr INTEGER,  
    training\_zones TEXT, \-- Stored as JSON string  
    preferences TEXT,   \-- Stored as JSON string  
    created\_at DATETIME DEFAULT CURRENT\_TIMESTAMP,  
    updated\_at DATETIME DEFAULT CURRENT\_TIMESTAMP  
);

CREATE TABLE IF NOT EXISTS activities (  
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    strava\_activity\_id INTEGER UNIQUE NOT NULL,  
    athlete\_id INTEGER NOT NULL,  
    name TEXT NOT NULL,  
    activity\_type TEXT,  
    start\_date DATETIME NOT NULL,  
    distance\_km REAL,  
    moving\_time\_seconds INTEGER,  
    pace\_min\_per\_km REAL,  
    average\_speed REAL,  
    total\_elevation\_gain REAL,  
    average\_heartrate REAL,  
    max\_heartrate REAL,  
    average\_cadence REAL,  
    average\_watts REAL,  
    raw\_stream\_data TEXT, \-- Stored as JSON string  
    created\_at DATETIME DEFAULT CURRENT\_TIMESTAMP,  
    FOREIGN KEY (athlete\_id) REFERENCES athletes(id)  
);

CREATE TABLE IF NOT EXISTS planned\_workouts (  
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    athlete\_id INTEGER NOT NULL,  
    workout\_date DATETIME NOT NULL,  
    planned\_distance\_km REAL,  
    planned\_pace\_min\_per\_km REAL,  
    workout\_type TEXT,  
    notes TEXT,  
    created\_at DATETIME DEFAULT CURRENT\_TIMESTAMP,  
    UNIQUE(athlete\_id, workout\_date), \-- Ensures one plan per athlete per day  
    FOREIGN KEY (athlete\_id) REFERENCES athletes(id)  
);

CREATE TABLE IF NOT EXISTS daily\_summaries (  
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    athlete\_id INTEGER NOT NULL,  
    summary\_date DATETIME NOT NULL,  
    actual\_distance\_km REAL,  
    planned\_distance\_km REAL,  
    actual\_pace\_min\_per\_km REAL,  
    planned\_pace\_min\_per\_km REAL,  
    distance\_variance\_percent REAL,  
    pace\_variance\_percent REAL,  
    status TEXT,  
    notes TEXT,  
    created\_at DATETIME DEFAULT CURRENT\_TIMESTAMP,  
    UNIQUE(athlete\_id, summary\_date), \-- Ensures one summary per athlete per day  
    FOREIGN KEY (athlete\_id) REFERENCES athletes(id)  
);

CREATE TABLE IF NOT EXISTS system\_logs (  
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    log\_date DATETIME DEFAULT CURRENT\_TIMESTAMP,  
    log\_type TEXT NOT NULL,  
    message TEXT NOT NULL,  
    details TEXT,  
    athlete\_id INTEGER, \-- Optional: Link log to a specific athlete if applicable  
    FOREIGN KEY (athlete\_id) REFERENCES athletes(id)  
);

CREATE TABLE IF NOT EXISTS strava\_api\_usage (  
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    date DATETIME UNIQUE NOT NULL,  
    requests\_count\_15min INTEGER DEFAULT 0,  
    requests\_count\_daily INTEGER DEFAULT 0,  
    last\_reset\_15min DATETIME,  
    last\_reset\_daily DATETIME  
);

CREATE TABLE IF NOT EXISTS optimal\_values (  
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    athlete\_id INTEGER UNIQUE NOT NULL,  
    optimal\_metrics TEXT, \-- Stored as JSON string  
    created\_at DATETIME DEFAULT CURRENT\_TIMESTAMP,  
    updated\_at DATETIME DEFAULT CURRENT\_TIMESTAMP,  
    FOREIGN KEY (athlete\_id) REFERENCES athletes(id)  
);

CREATE TABLE IF NOT EXISTS notification\_logs (  
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    athlete\_id INTEGER NOT NULL,  
    notification\_type TEXT NOT NULL,  
    status TEXT NOT NULL,  
    message TEXT,  
    timestamp DATETIME DEFAULT CURRENT\_TIMESTAMP,  
    FOREIGN KEY (athlete\_id) REFERENCES athletes(id)  
);

## External Integrations

### Replit-Compatible Strava Integration

import datetime  
import logging  
import time  
import secrets \# For state parameter in OAuth  
from typing import Dict, Any, List

from stravalib.client import Client  
from stravalib.exc import RateLimitExceeded, OAuthError

class ReplitStravaClient:  
    """  
    Strava client optimized for Replit resource limits and multi-athlete API calls.  
    Handles rate limiting and robust error recovery.  
    """  
      
    def \_\_init\_\_(self, client\_id: str, client\_secret: str):  
        self.client\_id \= client\_id  
        self.client\_secret \= client\_secret  
        \# The base client is used for OAuth flows, per-athlete client for activity fetching  
        self.base\_client \= Client(client\_id=self.client\_id, client\_secret=self.client\_secret)  
      
    def get\_authorization\_url(self, redirect\_uri: str, scope: str \= 'activity:read\_all,profile:read\_all') \-\> str:  
        """Generates the Strava OAuth authorization URL."""  
        return self.base\_client.authorization\_url(  
            client\_id=self.client\_id,  
            redirect\_uri=redirect\_uri,  
            scope=scope,  
            \# Add state parameter for CSRF protection  
            state=secrets.token\_urlsafe(16)  
        )

    def exchange\_code\_for\_token(self, code: str) \-\> Dict\[str, Any\]:  
        """Exchanges an authorization code for access and refresh tokens."""  
        try:  
            token\_data \= self.base\_client.exchange\_code\_for\_token(code=code)  
            logging.info("Successfully exchanged code for Strava tokens.")  
            return token\_data  
        except OAuthError as e:  
            logging.error(f"Error exchanging Strava code for token: {e}")  
            raise \# Re-raise for Flask to handle  
        except Exception as e:  
            logging.error(f"Unexpected error during token exchange: {e}")  
            raise

    def refresh\_access\_token(self, refresh\_token: str) \-\> Dict\[str, Any\]:  
        """Refreshes an expired access token using the refresh token."""  
        try:  
            refresh\_data \= self.base\_client.refresh\_access\_token(refresh\_token=refresh\_token)  
            logging.info("Successfully refreshed Strava access token.")  
            return refresh\_data  
        except OAuthError as e:  
            logging.error(f"Error refreshing Strava token: {e}")  
            raise  
        except Exception as e:  
            logging.error(f"Unexpected error during token refresh: {e}")  
            raise

    def get\_activities(self, access\_token: str, start\_date: datetime.datetime, end\_date: datetime.datetime \= None) \-\> List\[Dict\[str, Any\]\]:  
        """  
        Fetch activities for a given athlete with efficient pagination and retry logic.  
        Optimized for Replit resource limits by limiting fetch size.  
        """  
        athlete\_client \= Client(access\_token=access\_token)  
        all\_activities\_data \= \[\]  
          
        \# Define the 'after' and 'before' timestamps for the activity fetch  
        after\_timestamp \= start\_date.timestamp()  
        before\_timestamp \= end\_date.timestamp() if end\_date else datetime.datetime.now().timestamp()

        \# Stravalib's \`iter\_activities\` is generally more efficient for pagination  
        \# It handles internal pagination and rate limiting itself.  
        try:  
            \# Iterating through activities; stravalib will handle subsequent API calls  
            for activity in athlete\_client.iter\_activities(after=after\_timestamp, before=before\_timestamp):  
                all\_activities\_data.append(activity.to\_dict())  
                \# Add a small delay if fetching many activities for multiple athletes  
                \# This helps in being polite to the API and preventing hitting rate limits quickly  
                time.sleep(0.1) \# Small delay per activity

        except RateLimitExceeded as e:  
            logging.warning(f"Strava API Rate Limit Exceeded for {athlete\_client.get\_athlete().id}. Retrying after {e.timeout} seconds.")  
            time.sleep(e.timeout \+ 5\) \# Add a buffer before re-attempting  
            \# In a real system, you might queue this athlete for a later retry  
        except OAuthError as e:  
            logging.error(f"Strava OAuth error for athlete {athlete\_client.get\_athlete().id}: {e}. Token might be invalid.")  
            \# Mark athlete as inactive or require re-authentication  
        except Exception as e:  
            logging.error(f"General error fetching Strava activities for athlete: {e}", exc\_info=True)

        return all\_activities\_data

## Advanced Processing Workflows

### Replit-Optimized Daily Processing

import os  
import datetime  
import logging  
import pandas as pd  
from concurrent.futures import ThreadPoolExecutor, as\_completed  
from sqlalchemy.orm import sessionmaker  
from sqlalchemy import create\_engine  
import json \# For handling JSON fields from DB models

\# Assuming models are in 'app.models' and mail\_notifier in 'app.mail\_notifier'  
from app.models import ReplitAthlete, Activity, DailySummary, NotificationLog  
from app.mail\_notifier import MailNotifier  
from app.data\_processor import process\_athlete\_daily\_performance as core\_process\_athlete\_daily\_performance \# Main processing logic

\# Define database engine and session for use in workers  
\# Ensure DATABASE\_URL is loaded from environment variables in your Flask app's config.py  
\# and passed to this module or accessed via os.environ.  
DATABASE\_URL \= os.environ.get('DATABASE\_URL', 'sqlite:///marathon.db')  
engine \= create\_engine(DATABASE\_URL)   
Session \= sessionmaker(bind=engine)

def get\_athletes\_in\_chunks(db\_session\_factory, chunk\_size: int \= 10\) \-\> List\[List\[ReplitAthlete\]\]:  
    """  
    Fetches active athletes from the database in chunks to manage memory.  
    This is crucial for scaling to many athletes.  
    """  
    db\_session \= db\_session\_factory()  
    try:  
        \# Fetch only necessary columns to reduce memory footprint if Athlete objects are large  
        athletes \= db\_session.query(ReplitAthlete).filter(ReplitAthlete.is\_active \== True).all()  
        chunks \= \[athletes\[i:i \+ chunk\_size\] for i in range(0, len(athletes), chunk\_size)\]  
        return chunks  
    except Exception as e:  
        logging.error(f"Error fetching athletes in chunks: {e}", exc\_info=True)  
        return \[\]  
    finally:  
        db\_session.close() \# Always close session

def process\_single\_athlete\_workflow(  
    athlete\_data: Dict, \# Pass athlete data as dict to avoid SQLAlchemy object issues across threads  
    processing\_date: datetime.date,   
    mail\_notifier: MailNotifier  
):  
    """  
    Workflow for processing a single athlete's daily performance.  
    Designed to be independent and robust against individual athlete errors.  
    Receives athlete data as a dictionary.  
    """  
    athlete\_id \= athlete\_data\['id'\]  
    athlete\_name \= athlete\_data\['name'\]  
    athlete\_email \= athlete\_data\['email'\]  
    athlete\_preferences \= json.loads(athlete\_data\['preferences'\]) if athlete\_data\['preferences'\] else {}

    logging.info(f"Starting daily processing for athlete: {athlete\_name} (ID: {athlete\_id}) on {processing\_date}")  
    db\_session \= Session() \# Each worker gets its own session  
    try:  
        \# Step 1: Sync activities (this typically runs before daily processing or can be integrated here)  
        \# Assuming ReplitStravaClient instance is available or created within this context  
        \# For this function, let's assume activities are fetched and stored separately,  
        \# and process\_athlete\_daily\_performance reads from the DB.  
          
        \# Step 2: Process performance analytics using pandas  
        \# core\_process\_athlete\_daily\_performance needs a session, athlete\_id, and date  
        summary\_data \= core\_process\_athlete\_daily\_performance(db\_session, athlete\_id, processing\_date)  
          
        if summary\_data:  
            logging.info(f"Processed summary for {athlete\_name}: {summary\_data.get('status')}", extra={'athlete\_id': athlete\_id})  
              
            \# Step 3: Send personalized notification if subscribed  
            if athlete\_preferences.get('notification\_daily\_summary'):  
                mail\_notifier.send\_daily\_summary(athlete\_email, summary\_data)  
                \# Log successful notification  
                notification\_log \= NotificationLog(  
                    athlete\_id=athlete\_id,   
                    notification\_type='daily\_summary',   
                    status='sent',   
                    message=f"Daily summary sent for {processing\_date}"  
                )  
                db\_session.add(notification\_log)  
                logging.info(f"Sent daily summary email to {athlete\_name}.", extra={'athlete\_id': athlete\_id})  
            else:  
                logging.info(f"Athlete {athlete\_name} not subscribed for daily summaries.", extra={'athlete\_id': athlete\_id})  
        else:  
            logging.info(f"No summary generated for {athlete\_name} on {processing\_date}. Skipping notification.", extra={'athlete\_id': athlete\_id})

        db\_session.commit() \# Commit changes for this athlete  
    except Exception as e:  
        db\_session.rollback() \# Rollback changes for this athlete on error  
        logging.error(f"Error processing athlete {athlete\_name} (ID: {athlete\_id}): {e}", exc\_info=True, extra={'athlete\_id': athlete\_id})  
        \# Log this error to SystemLog model for persistent error tracking  
        error\_message \= f"Daily processing failed for {athlete\_name}: {e}"  
        \# db\_session.add(SystemLog(log\_type='ERROR', message=error\_message, details=str(e), athlete\_id=athlete\_id))  
        \# db\_session.commit() \# Commit log even if main transaction failed  
    finally:  
        db\_session.close() \# Always close the session

def replit\_daily\_processing(processing\_date: datetime.date \= None):  
    """  
    Memory-efficient, concurrent daily processing for all active athletes on Replit.  
    Uses ThreadPoolExecutor to parallelize athlete processing.  
    """  
    if processing\_date is None:  
        processing\_date \= datetime.date.today() \- datetime.timedelta(days=1) \# Process yesterday's data

    logging.info(f"Starting daily batch processing for all athletes for date: {processing\_date}")  
      
    \# Initialize MailNotifier once for all workers to reuse SMTP connection  
    \# Ensure mail settings are loaded from environment variables (Config)  
    mail\_notifier \= MailNotifier(  
        smtp\_server=os.environ.get('MAIL\_SMTP\_SERVER'),  
        smtp\_port=int(os.environ.get('MAIL\_SMTP\_PORT')),  
        smtp\_user=os.environ.get('MAIL\_SMTP\_USER'),  
        smtp\_password=os.environ.get('MAIL\_SMTP\_PASSWORD')  
    )

    \# Fetch athlete data as dictionaries to avoid ORM session issues across threads  
    db\_session\_initial \= Session()  
    try:  
        athletes\_raw\_data \= \[  
            {  
                'id': a.id, 'name': a.name, 'email': a.email,   
                'preferences': a.preferences \# This will be JSON string, parse in worker  
            }   
            for a in db\_session\_initial.query(ReplitAthlete).filter(ReplitAthlete.is\_active \== True).all()  
        \]  
    finally:  
        db\_session\_initial.close()

    \# Determine max workers based on available CPU cores to prevent oversubscription  
    max\_workers \= os.cpu\_count() or 2   
    logging.info(f"Using {max\_workers} worker threads for daily processing.")

    with ThreadPoolExecutor(max\_workers=max\_workers) as executor:   
        futures \= \[\]  
        for athlete\_data in athletes\_raw\_data:  
            future \= executor.submit(process\_single\_athlete\_workflow, athlete\_data, processing\_date, mail\_notifier)  
            futures.append(future)  
          
        for future in as\_completed(futures):  
            try:  
                future.result() \# This will re-raise any exceptions that occurred in the worker  
            except Exception as e:  
                logging.error(f"A worker process for an athlete failed during daily processing: {e}", exc\_info=True)  
                \# The individual athlete's error is already logged in process\_single\_athlete\_workflow  
      
    logging.info(f"Daily batch processing completed for date: {processing\_date}")

\# You would call replit\_daily\_processing from your APScheduler job,  
\# configured in app/\_\_init\_\_.py or a separate scheduler script.  
\# Example: scheduler.add\_job(replit\_daily\_processing, 'cron', hour=3, minute=0)

## Production-Ready Deployment

### Replit Deployment Configuration

\# .replit configuration  
\# This configuration orchestrates how your application runs on Replit.  
\# It assumes 'main.py' is the entry point which will manage starting Flask and Streamlit.  
run \= "python main.py" 

\# Example \`main.py\` for starting both Flask (via Gunicorn) and Streamlit.  
\# This requires robust process management to ensure both stay alive.  
\# A more production-ready approach on Replit for complex setups might involve  
\# Replit's always-on or deployment features, possibly with a custom \`wsgi.py\`  
\# or a specific \`Procfile\` if using \`replit web\` advanced capabilities.

\# import subprocess  
\# import sys  
\# import os  
\# import time  
\# import threading

\# def start\_flask\_app():  
\#     """Starts the Flask application using Gunicorn."""  
\#     \# Use gunicorn to serve the Flask app. Adjust workers based on Replit resources.  
\#     \# Assuming your Flask app instance is named 'app' in 'app/\_\_init\_\_.py'  
\#     flask\_command \= \["gunicorn", "-w", "2", "app:app", "-b", "0.0.0.0:5000", "--log-level", "info"\]  
\#     try:  
\#         \# Use subprocess.run for blocking call if you want to wait, or Popen for non-blocking  
\#         subprocess.run(flask\_command, check=True, stdout=sys.stdout, stderr=sys.stderr)  
\#     except subprocess.CalledProcessError as e:  
\#         logging.error(f"Flask Gunicorn process exited with error: {e}", exc\_info=True)  
\#     except Exception as e:  
\#         logging.error(f"Failed to start Flask app: {e}", exc\_info=True)

\# def start\_streamlit\_app():  
\#     """Starts the Streamlit application."""  
\#     \# Streamlit's default port is 8501\. Replit typically exposes this.  
\#     streamlit\_command \= \[  
\#         "streamlit", "run", "dashboard/streamlit\_app.py",  
\#         "--server.port", "8501",   
\#         "--server.enableCORS", "false", \# Be cautious with CORS in production  
\#         "--server.enableXsrfProtection", "false", \# Be cautious with XSRF in production  
\#         "--server.headless", "true" \# Run Streamlit without opening a browser  
\#     \]  
\#     try:  
\#         subprocess.run(streamlit\_command, check=True, stdout=sys.stdout, stderr=sys.stderr)  
\#     except subprocess.CalledProcessError as e:  
\#         logging.error(f"Streamlit process exited with error: {e}", exc\_info=True)  
\#     except Exception as e:  
\#         logging.error(f"Failed to start Streamlit app: {e}", exc\_info=True)

\# if \_\_name\_\_ \== "\_\_main\_\_":  
\#     \# Ensure logging is configured before starting threads  
\#     \# from app.config import configure\_logging \# Assuming you have this function  
\#     \# configure\_logging() 

\#     logging.info("Starting Flask and Streamlit applications...")  
      
\#     \# Start Flask in a separate thread/process  
\#     flask\_thread \= threading.Thread(target=start\_flask\_app)  
\#     flask\_thread.daemon \= True \# Allow main program to exit if threads are still running  
\#     flask\_thread.start()

\#     \# Give Flask a moment to start up before Streamlit tries to connect  
\#     time.sleep(5) 

\#     \# Start Streamlit in a separate thread/process  
\#     streamlit\_thread \= threading.Thread(target=start\_streamlit\_app)  
\#     streamlit\_thread.daemon \= True  
\#     streamlit\_thread.start()

\#     \# Keep the main thread alive indefinitely to allow background threads to run.  
\#     \# In a Replit environment, the 'run' command will keep the container alive  
\#     \# as long as the main process is running. If \`main.py\` exits, the Repl stops.  
\#     \# A simple infinite loop or Flask app main loop can serve this purpose.  
\#     try:  
\#         while True:  
\#             time.sleep(3600) \# Sleep for an hour, or until interrupted  
\#     except KeyboardInterrupt:  
\#         logging.info("Application stopped by user.")  
\#     except Exception as e:  
\#         logging.error(f"Main orchestrator failed: {e}", exc\_info=True)

\# Replit environment variables \- CRITICAL for secure and error-free operation  
\# These should be configured in Replit's "Secrets" tab.  
\# DO NOT hardcode sensitive information directly in code or .replit file.  
.env:  
  STRAVA\_CLIENT\_ID="your\_strava\_client\_id\_here"  
  STRAVA\_CLIENT\_SECRET="your\_strava\_client\_secret\_here"  
  JWT\_SECRET="YOUR\_VERY\_STRONG\_RANDOM\_JWT\_SECRET" \# Generate a truly random one using secrets.token\_urlsafe(64)  
  DATABASE\_URL="sqlite:///marathon.db" \# Example: sqlite:///marathon.db for SQLite or "postgresql://user:pass@host:port/dbname" for PostgreSQL  
  MAIL\_SMTP\_SERVER="smtp.example.com" \# Your SMTP server for sending emails  
  MAIL\_SMTP\_PORT="587" \# Port for SMTP (e.g., 587 for TLS, 465 for SSL)  
  MAIL\_SMTP\_USER="your\_email@example.com" \# Email address for sending notifications  
  MAIL\_SMTP\_PASSWORD="your\_email\_app\_password" \# App-specific password for email account (HIGHLY RECOMMENDED)  
  LOG\_LEVEL="INFO" \# Set to DEBUG for more verbose logging in development

### Application Structure for Replit

├── .replit                 \# Replit configuration for running the app  
├── main.py                 \# Orchestrates Flask and Streamlit launch  
├── app/                    \# Flask application directory  
│   ├── \_\_init\_\_.py         \# Flask app initialization, database setup, JWTManager init, scheduler  
│   ├── routes.py           \# API endpoints (Flask-RESTx resources)  
│   ├── models.py           \# SQLAlchemy database models  
│   ├── strava\_client.py    \# Strava API integration logic (using stravalib)  
│   ├── data\_processor.py   \# Core data processing logic (using pandas)  
│   ├── mail\_notifier.py    \# Email notification sending logic  
│   ├── config.py           \# Centralized configuration loading from environment variables  
│   └── services/           \# Optional: Directory for other services like caching, ML model wrappers  
│       ├── \_\_init\_\_.py  
│       └── analytics.py    \# Contains ReplitAnalyticsEngine and ML model loading  
├── dashboard/              \# Streamlit components directory  
│   ├── streamlit\_app.py    \# Main Streamlit dashboard file  
│   ├── components.py       \# Reusable Streamlit UI widgets/cards (e.g., custom glassmorphism cards)  
│   ├── analytics\_display.py\# Streamlit specific analytics visualization logic (charts, tables)  
│   └── api\_client.py       \# Utility for Streamlit to call Flask APIs (e.g., using \`requests\`)  
├── requirements.txt        \# Python dependencies (generated via \`pip freeze \> requirements.txt\`)  
├── data/                   \# Directory for static data, e.g., pre-trained ML models, excel templates  
│   └── models/  
│       └── light\_perf\_model.pkl \# Example pre-trained lightweight ML model  
├── tests/                  \# Unit and integration tests  
│   ├── test\_api.py         \# Tests for Flask API endpoints  
│   ├── test\_models.py      \# Tests for SQLAlchemy models  
│   └── test\_data\_processing.py \# Tests for pandas-based data processing  
└── .env                    \# Example environment variables for local development (NOT deployed to production)

## Performance & Monitoring

### Replit-Optimized Monitoring

import psutil  
import os  
import sqlite3 \# Standard library for SQLite interaction  
import logging  
\# For PostgreSQL, you'd typically use psycopg2 or sqlalchemy's engine connection  
\# import psycopg2 

\# Assume 'app' Flask instance is available or passed if this is a separate module  
\# from app import app, db \# If you have a global db object for SQLAlchemy

@app.route('/replit\_metrics')  
def replit\_metrics():  
    """  
    Resource monitoring endpoint for Replit.  
    Provides insights into CPU, memory, database size, and active connections.  
    Crucial for identifying bottlenecks with multiple concurrent athletes.  
    """  
    \# Get database URL from environment  
    db\_url \= os.environ.get('DATABASE\_URL', 'sqlite:///marathon.db')  
      
    def get\_db\_size():  
        """Get database size in MB."""  
        if db\_url.startswith('sqlite:///'):  
            db\_path \= db\_url.replace('sqlite:///', '')  
            try:  
                if os.path.exists(db\_path):  
                    return os.path.getsize(db\_path) / (1024 \* 1024\) \# Size in MB  
                else:  
                    logging.warning(f"SQLite database file not found at {db\_path}")  
                    return 0.0  
            except Exception as e:  
                logging.error(f"Error getting SQLite database size: {e}", exc\_info=True)  
                return float('nan')  
        elif db\_url.startswith('postgresql://'):  
            \# Implement PostgreSQL specific size query.  
            \# This requires a database connection. Example (conceptual):  
            \# conn \= psycopg2.connect(db\_url)  
            \# cursor \= conn.cursor()  
            \# cursor.execute("SELECT pg\_database\_size(current\_database());")  
            \# size\_bytes \= cursor.fetchone()\[0\]  
            \# cursor.close(); conn.close()  
            \# return size\_bytes / (1024 \* 1024\)  
            logging.info("PostgreSQL database size monitoring not implemented yet.")  
            return float('nan')  
        return float('nan')  
              
    def count\_db\_connections():  
        """  
        Count active database connections.  
        For SQLite, this is less relevant as it's file-based and connections are light.  
        For PostgreSQL, this would query pg\_stat\_activity view.  
        """  
        if db\_url.startswith('sqlite:///'):  
            \# For SQLite, a simple indicator is whether the file exists and is accessible.  
            \# Actual concurrent connections are managed by OS/DB driver.  
            return 1 if os.path.exists(db\_url.replace('sqlite:///', '')) else 0  
        elif db\_url.startswith('postgresql://'):  
            \# Implement PostgreSQL specific connection count query. Example (conceptual):  
            \# conn \= psycopg2.connect(db\_url)  
            \# cursor \= conn.cursor()  
            \# cursor.execute("SELECT count(\*) FROM pg\_stat\_activity WHERE datname \= current\_database();")  
            \# count \= cursor.fetchone()\[0\]  
            \# cursor.close(); conn.close()  
            \# return count  
            logging.info("PostgreSQL active connections monitoring not implemented yet.")  
            return 0  
        return 0

    return jsonify({  
        'memory\_percent': psutil.virtual\_memory().percent, \# System-wide memory usage percentage  
        'cpu\_percent': psutil.cpu\_percent(interval=1),   \# System-wide CPU usage percentage over 1 second  
        'database\_size\_mb': get\_db\_size(),             \# Database file size in MB  
        'active\_db\_connections': count\_db\_connections(), \# Number of active DB connections  
        'process\_count': len(psutil.pids()) \# Total number of running processes on the system  
    })

## Error Handling & Observability

### Replit-Optimized Logging

import logging  
import os  
import sys  
import traceback \# For getting full traceback info  
from logging.handlers import RotatingFileHandler  
from flask import jsonify \# Assuming this function is part of a Flask app context

\# This function should be called early in your Flask app's \_\_init\_\_.py  
def configure\_replit\_logging(app):  
    """  
    Configures structured logging for Replit console and file,  
    ensuring comprehensive error capture for multi-athlete operations.  
    Logs can be filtered by athlete\_id for debugging.  
    """  
    log\_file\_path \= 'app.log' \# Log file in the root directory of the Repl  
      
    \# Create logs directory if it doesn't exist (if you wanted to store logs in a subdir)  
    log\_dir \= os.path.dirname(log\_file\_path)  
    if log\_dir and not os.path.exists(log\_dir):  
        os.makedirs(log\_dir, exist\_ok=True) \# exist\_ok avoids error if already exists

    \# Remove default Flask handlers to avoid duplicate logs if setting up custom ones  
    for handler in app.logger.handlers:  
        app.logger.removeHandler(handler)

    \# Basic configuration for console output (important for Replit's console)  
    console\_handler \= logging.StreamHandler(sys.stdout)  
    console\_formatter \= logging.Formatter(  
        '%(asctime)s %(levelname)s \[%(name)s\] \[%(athlete\_id)s\] %(message)s' \# Added athlete\_id  
    )  
    console\_handler.setFormatter(console\_formatter)  
    app.logger.addHandler(console\_handler)

    \# Add a rotating file handler for persistent logs (optional on Replit's ephemeral storage, but good practice)  
    file\_handler \= RotatingFileHandler(  
        log\_file\_path,   
        maxBytes=1024 \* 1024 \* 5, \# 5 MB per log file  
        backupCount=5 \# Keep 5 backup logs  
    )  
    file\_formatter \= logging.Formatter(  
        '%(asctime)s %(levelname)s \[%(name)s\] \[%(athlete\_id)s\] %(message)s' \# Added athlete\_id  
    )  
    file\_handler.setFormatter(file\_formatter)  
    app.logger.addHandler(file\_handler)

    \# Set the logging level from environment variable, default to INFO  
    app.logger.setLevel(os.environ.get('LOG\_LEVEL', 'INFO').upper())  
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING) \# Suppress noisy SQLAlchemy logs

    \# Custom Log Record Factory to inject 'athlete\_id' into log records  
    \# This allows formatting to use '%(athlete\_id)s' even if not explicitly passed.  
    old\_factory \= logging.getLogRecordFactory()  
    def record\_factory(\*args, \*\*kwargs):  
        record \= old\_factory(\*args, \*\*kwargs)  
        \# Attempt to get athlete\_id from Flask's g object (if in request context)  
        \# or from \`extra\` dict passed to logger.  
        from flask import g \# Import inside to avoid circular dependency if app isn't ready  
        record.athlete\_id \= getattr(g, 'athlete\_id', 'N/A') \# Default to 'N/A'  
        return record  
    logging.setLogRecordFactory(record\_factory)

    \# Centralized error handling for all unhandled exceptions in Flask  
    @app.errorhandler(Exception)  
    def handle\_exception(e):  
        \# Log the error with full traceback  
        \# Use exc\_info=True to include traceback in logs  
        app.logger.error(f"Unhandled application error: {e}", exc\_info=True)  
          
        \# Log to SystemLog model for persistent error tracking  
        \# You would need to import db\_session and SystemLog model here  
        \# from app.models import SystemLog \# Ensure this import is correct relative to app  
        \# from app import db\_session \# Ensure you have a mechanism to get a DB session  
        \# try:  
        \#     session \= db\_session() \# Get a new session  
        \#     log\_entry \= SystemLog(  
        \#         log\_type='ERROR',   
        \#         message=str(e),   
        \#         details=traceback.format\_exc(),  
        \#         athlete\_id=getattr(g, 'athlete\_id', None) \# Log athlete\_id if available  
        \#     )  
        \#     session.add(log\_entry)  
        \#     session.commit()  
        \# except Exception as db\_log\_e:  
        \#     app.logger.error(f"Failed to log error to database: {db\_log\_e}", exc\_info=True)  
        \#     session.rollback() \# Ensure rollback on log error  
        \# finally:  
        \#     session.close()

        \# Return a generic error response to the client  
        return jsonify({"message": "An internal server error occurred. Please try again later.", "error": str(e)}), 500

\# Example usage in other modules after configure\_replit\_logging is called for the app:  
\# import logging  
\# logger \= logging.getLogger(\_\_name\_\_) \# Get a logger instance for the current module  
\#  
\# def some\_function\_processing\_athlete(athlete\_id: int):  
\#     \# When logging, pass athlete\_id via 'extra' dictionary if outside request context  
\#     logger.info("Processing started for athlete.", extra={'athlete\_id': athlete\_id})  
\#     try:  
\#         \# ... complex logic ...  
\#         if some\_condition\_fails:  
\#             raise ValueError("Data inconsistency detected.")  
\#     except Exception as e:  
\#         logger.error("Processing failed for athlete.", extra={'athlete\_id': athlete\_id}, exc\_info=True)  
\#         \# You might re-raise the exception or handle it gracefully  
\#

## Future Enhancements

1. **Replit Teams Integration**: Collaborative training features, allowing team leaders to oversee multiple athletes and share insights.  
2. **Predictive Scaling**: Auto-adjust resources based on usage patterns, **potentially leveraging Replit's auto-scaling features (if available) or external monitoring tools for intelligent workload distribution across multiple athlete processes.**  
3. **Mobile Optimization**: Progressive Web App (PWA) support, **ensuring a responsive and smooth experience for athletes on various devices.**  
4. **AI Coaching Assistant**: Chat-based training guidance, **personalized for each athlete using their historical data and ML models.**  
5. **Integration Expansion**: Garmin, Fitbit, Apple Health, **to broaden data sources and cater to more athletes.**  
6. **Replit Template**: Shareable training dashboard template, **making it easier for other teams to adopt and use the system.**  
7. **Advanced User Management**: Implement roles (Athlete, Coach, Admin) with granular permissions, crucial for managing a large multi-athlete system.  
8. **Data Archiving/Pruning**: Strategy for managing old data (e.g., older than 2 years) to keep database size manageable and improve query performance for active data.  
9. **Database Sharding/Clustering**: For extremely large datasets with hundreds or thousands of athletes, explore horizontal scaling strategies for the database (beyond basic PostgreSQL).

**Note**: This enhanced design maintains compatibility with Replit's platform constraints while incorporating advanced features like real-time updates, predictive analytics, and professional-grade security. All components are optimized for efficient resource usage within Replit's execution environment, with a strong focus on **error-free operation and seamless handling of multiple athletes**.