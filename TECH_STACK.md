# Marathon Training Dashboard - Technology Stack

## Core Framework & Web Server
- **Flask** (3.1.1) - Core web framework
- **Gunicorn** (23.0.0) - WSGI HTTP Server for production deployment
- **Werkzeug** (3.1.3) - WSGI web application library
- **Jinja2** (3.1.6) - Template engine
- **click** (8.2.1) - Command line interface creation

## Database & ORM
- **SQLAlchemy** (2.0.41) - Database ORM
- **Flask-SQLAlchemy** (3.1.1) - Flask integration for SQLAlchemy
- **PostgreSQL** - Primary database (via DATABASE_URL)

## Authentication & Security
- **Flask-JWT-Extended** (4.7.1) - JWT token management
- **PyJWT** (2.10.1) - JSON Web Token implementation
- **cryptography** (45.0.3) - Cryptographic operations

## Real-time Communication (Currently Disabled)
- **Flask-SocketIO** (5.5.1) - Real-time bidirectional communication
- **python-socketio** (5.13.0) - Socket.IO client/server
- **python-engineio** (4.12.2) - Engine.IO server

## Background Processing
- **APScheduler** (3.11.0) - Advanced Python Scheduler for background tasks

## External API Integrations
- **stravalib** (2.3) - Strava API integration for athlete data
- **google-generativeai** (0.8.5) - Gemini AI for race recommendations
- **requests** (2.32.3) - HTTP library for API calls

## Data Science & Machine Learning
- **scikit-learn** (1.7.0) - Machine learning algorithms for injury prediction
- **numpy** (2.2.6) - Numerical computations
- **pandas** (2.3.0) - Data manipulation and analysis
- **joblib** (1.5.1) - Machine learning model persistence

## Configuration & Environment
- **python-dotenv** (1.1.0) - Environment variable management
- **python-dateutil** (2.9.0.post0) - Date/time utilities

## Testing
- **pytest** (8.4.0) - Testing framework

## Email Notifications
- **Built-in smtplib** - SMTP email sending (no external dependencies)

## Google AI Dependencies
- **google-ai-generativelanguage** (0.6.15) - Google AI language models
- **google-api-core** (2.25.0) - Google API client core library
- **google-auth** (2.40.3) - Google authentication library
- **googleapis-common-protos** (1.70.0) - Common protocol buffer types
- **grpcio** (1.72.1) - gRPC Python library
- **proto-plus** (1.26.1) - Beautiful, Pythonic protocol buffers
- **protobuf** (5.29.5) - Protocol buffer library

## HTTP & Networking
- **urllib3** (2.4.0) - HTTP client library
- **certifi** (2025.4.26) - Root certificates for validating SSL certificates
- **charset-normalizer** (3.4.2) - Character encoding normalizer
- **idna** (3.10) - Internationalized Domain Names

## Dependency Analysis

### Actually Used vs. Available
- **Current requirements.txt**: 113+ dependencies
- **Essential requirements-minimal.txt**: ~45 dependencies
- **Reduction**: 60% fewer dependencies for improved performance

### Removed Unused Dependencies
- **Streamlit** - Not used in the actual web interface
- **Plotly** - Charts implemented with Chart.js (client-side)
- **Flask-RESTX** - Removed to prevent routing conflicts
- **Flask-Caching** - Not implemented in current version
- **OpenAI** - Only Gemini AI is used for recommendations
- **Marshmallow** - Object serialization not needed
- **Email-validator** - Built-in validation used instead

## Key Features Enabled by This Stack

### 1. **AI-Powered Race Recommendations**
- Gemini AI integration for personalized training advice
- Real-time pace calculations and race time predictions
- Injury prevention recommendations

### 2. **Authentic Data Integration**
- Strava OAuth 2.0 authentication and activity sync
- Real athlete performance data analysis
- Scientific race prediction algorithms

### 3. **Machine Learning Capabilities**
- Scikit-learn for injury risk prediction
- NumPy/Pandas for statistical analysis
- Joblib for model persistence

### 4. **Production Architecture**
- PostgreSQL database with SQLAlchemy ORM
- JWT authentication for secure API access
- Gunicorn WSGI server for deployment
- Background task processing with APScheduler

### 5. **Modern Web Interface**
- Flask with Jinja2 templating
- Responsive glassmorphism design
- Client-side Chart.js for visualizations