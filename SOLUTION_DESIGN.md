# Marathon Training Dashboard - Solution Design Document

## 1. Application Overview

The Marathon Training Dashboard is a cutting-edge web application that empowers marathon athletes with advanced performance tracking, social connectivity, and personalized training insights through intelligent, user-centric design. The system integrates with Strava to provide authentic activity data and leverages Google Gemini AI to deliver personalized race recommendations and training optimization.

### Key Features
- **Strava OAuth 2.0 Integration**: Authentic athlete data from real training activities
- **AI-Powered Race Recommendations**: Google Gemini AI provides personalized race advice, optimal distances, training focus areas, and injury prevention guidance
- **Community Dashboard**: Real-time metrics showing total athletes, distance, activities, and performance trends
- **Race Predictor**: Scientific algorithms (VDOT, Jack Daniels, Riegel) for accurate race time predictions
- **Injury Risk Analysis**: ML-based prediction using training load patterns and biomechanical indicators
- **Performance Analytics**: Heart rate zones, pace analysis, training volume trends
- **Glassmorphism UI**: Modern dark theme with transparent elements and white text
- **Production-Ready Architecture**: Optimized dependencies and scalable design

## 2. Technology Stack

### Backend Framework (Essential Dependencies Only)
- **Flask 3.1.1**: Core web framework with blueprint architecture
- **SQLAlchemy 2.0.41**: Database ORM and Flask-SQLAlchemy integration
- **Gunicorn 23.0.0**: Production WSGI HTTP server
- **APScheduler 3.11.0**: Background job scheduling for data sync

### Authentication & Security
- **Flask-JWT-Extended 4.7.1**: JWT token management
- **PyJWT 2.10.1**: JSON Web Token implementation
- **cryptography 45.0.3**: Cryptographic operations for secure tokens

### AI & External Integrations
- **google-generativeai 0.8.5**: Gemini AI for personalized race recommendations
- **stravalib 2.3**: Strava API OAuth 2.0 and activity data sync
- **requests 2.32.3**: HTTP client for API communications

### Data Science & Machine Learning
- **scikit-learn 1.7.0**: ML algorithms for injury risk prediction
- **numpy 2.2.6**: Numerical computations for performance analysis
- **pandas 2.3.0**: Data manipulation and statistical analysis
- **joblib 1.5.1**: Machine learning model persistence

### Frontend Technologies
- **Jinja2 3.1.6**: Server-side template engine
- **Chart.js**: Client-side data visualization and charting
- **Vanilla JavaScript**: Interactive functionality and AJAX calls
- **Modern CSS**: Glassmorphism design with dark theme

### Database & Storage
- **PostgreSQL**: Primary production database via DATABASE_URL
- **SQLite**: Development fallback database

### Configuration & Environment
- **python-dotenv 1.1.0**: Environment variable management
- **python-dateutil 2.9.0**: Date/time utilities for activity processing

### Development & Deployment
- **pytest 8.4.0**: Testing framework
- **Replit Cloud Platform**: Hosting with automatic scaling

### Dependency Optimization
- **Reduced from 113+ to 45 packages**: 60% reduction for improved performance
- **Removed unused dependencies**: Streamlit, Plotly, Flask-RESTX, OpenAI, Marshmallow
- **Client-side optimizations**: Chart.js instead of server-side plotting

## 3. Project Structure

```
marathon-dashboard/
├── app/
│   ├── __init__.py              # Application factory with optimized configuration
│   ├── config.py                # Replit-optimized configuration management
│   ├── models.py                # SQLAlchemy database models
│   ├── simple_routes.py         # Main API routes and web endpoints
│   ├── ai_race_advisor.py       # Google Gemini AI integration for race recommendations
│   ├── race_predictor_simple.py # Scientific race prediction algorithms
│   ├── race_optimizer.py        # Training optimization and pacing strategies
│   ├── injury_predictor.py      # ML-based injury risk assessment
│   ├── data_processor.py        # Core performance analytics engine
│   ├── strava_client.py         # Strava OAuth 2.0 and API integration
│   ├── security.py              # Security utilities and token management
│   └── mail_notifier.py         # SMTP email notification service
├── templates/
│   ├── community_standalone.html # Main community dashboard with glassmorphism UI
│   ├── dashboard.html           # Individual athlete dashboard
│   ├── race_predictor.html      # AI-powered race prediction interface
│   ├── risk_analyser.html       # Injury risk analysis interface
│   └── auth_success.html        # Post-authentication success page
├── attached_assets/             # Project documentation and assets
├── data/                        # Training data and ML models
├── tests/                       # Unit and integration tests
├── .env                         # Environment variables and API keys
├── main.py                      # Application entry point
├── requirements.txt             # Full dependency list (113+ packages)
├── requirements-minimal.txt     # Optimized essential dependencies (45 packages)
├── TECH_STACK.md               # Technology stack documentation
└── SOLUTION_DESIGN.md          # This comprehensive solution design
```

## 4. Core Modules Analysis

### 4.1 Application Factory (`app/__init__.py`)

**Purpose**: Centralizes application configuration and initialization

**Key Components**:
- Flask application factory pattern
- Database initialization with SQLAlchemy
- Blueprint registration for modular routing
- Error handling and logging configuration
- Background scheduler setup for automated tasks

**Database Models**:
- `ReplitAthlete`: Core athlete profile data
- `Activity`: Strava activity records
- `DailySummary`: Aggregated daily performance metrics
- `PlannedWorkout`: Training plan data
- `ProcessingLog`: System operation tracking
- `NotificationLog`: Communication history

### 4.2 Configuration Management (`app/config.py`)

**Purpose**: Centralized configuration with environment-based settings

**Configuration Areas**:
- Database connection strings
- Strava API credentials (CLIENT_ID, CLIENT_SECRET, CALLBACK_URL)
- JWT security keys
- SMTP email settings
- Logging levels and formats
- Replit-optimized logging for cloud deployment

### 4.3 API Routes (`app/simple_routes.py`)

**Purpose**: RESTful API endpoints and web route handling

**Route Categories**:

#### Authentication Routes
- `GET /api/auth/strava/authorize`: Generate Strava OAuth URL
- `GET /api/auth/strava/callback`: Handle OAuth callback
- `GET /auth/success`: Post-authentication success page

#### Community Dashboard Routes
- `GET /`: Main community dashboard
- `GET /api/community/overview`: Community statistics and metrics
- `GET /api/analytics/data`: Analytics data for charts

#### Athlete Management Routes
- `GET /api/athletes`: List all athletes
- `GET /api/athletes/<id>/summary`: Individual athlete summary
- `POST /api/athletes/<id>/sync`: Sync Strava activities

#### Performance Analytics Routes
- `GET /api/athletes/<id>/volume-trend`: Training volume analysis
- `GET /api/athletes/<id>/pace-analysis`: Pace progression data
- `GET /api/athletes/<id>/heart-rate-zones`: HR zone distribution
- `GET /api/athletes/<id>/training-load`: Training load metrics

#### Optimization Routes
- `GET /api/athletes/<id>/race-prediction`: Race time predictions
- `GET /api/athletes/<id>/injury-risk`: Injury risk assessment
- `GET /api/athletes/<id>/training-optimization`: Training recommendations

#### WebSocket Events
- `join_dashboard_room`: Real-time dashboard updates
- `disconnect`: Client disconnection handling

### 4.4 Strava Integration (`app/strava_client.py`)

**Purpose**: Comprehensive Strava API wrapper

**Key Functions**:
- OAuth 2.0 flow implementation
- Token management and refresh
- Activity data fetching and parsing
- Athlete profile synchronization
- Rate limiting and error handling
- Data transformation for internal models

**API Endpoints Used**:
- `/oauth/authorize`: User authorization
- `/oauth/token`: Token exchange and refresh
- `/athlete`: Profile information
- `/athlete/activities`: Activity data

### 4.5 Data Processing Engine (`app/data_processor.py`)

**Purpose**: Core analytics and performance calculation engine

**Processing Functions**:
- `process_athlete_daily_performance()`: Daily metric aggregation
- `get_athlete_performance_summary()`: Historical analysis
- `get_team_overview()`: Community-wide statistics

**Calculated Metrics**:
- Training load and intensity
- Pace analysis and trends
- Distance and duration aggregations
- Compliance with planned workouts
- Performance status determination
- AI-powered training insights

### 4.6 AI Race Advisor (`app/ai_race_advisor.py`)

**Purpose**: Google Gemini AI integration for personalized race recommendations

**Key Features**:
- **Gemini 1.5 Flash Model**: Advanced AI analysis of training data
- **Personalized Recommendations**: Optimal race distances, training focus areas, predicted times
- **Injury Prevention Guidance**: Recovery advice and training load management
- **Long-term Goal Planning**: Marathon readiness assessment and progression strategies
- **Fallback Logic**: Rule-based recommendations when AI is unavailable

**AI-Generated Insights**:
- Optimal race distance for next 4-6 weeks (e.g., "10K race is ideal")
- Training focus areas (tempo runs, interval training, weekly mileage)
- Predicted race times (sub-40 minute 10K, 17-18 minute 5K)
- Recovery and injury prevention advice
- Long-term marathon training progression

### 4.7 Race Predictor (`app/race_predictor_simple.py`)

**Purpose**: Scientific race prediction algorithms using authentic data

**Prediction Models**:
- **VDOT Algorithm**: VO2 max estimation from recent activity performance
- **Jack Daniels Formula**: Training pace calculations based on recent times
- **Riegel Formula**: Race time extrapolation across distances
- **McMillan Calculator**: Performance equivalency predictions
- **Pace-based Analysis**: Recent performance trend analysis

**Features**:
- Multiple distance predictions (5K, 10K, Half Marathon, Marathon)
- Recent activity performance analysis (last 30-90 days)
- Realistic time predictions based on authentic Strava data
- Performance confidence scoring
- Training pace recommendations

### 4.8 Race Optimizer (`app/race_optimizer.py`)

**Purpose**: Advanced training optimization and pacing strategies

**Optimization Features**:
- Detailed pacing strategy for marathon races
- Heart rate target zones based on athlete profile
- Split-by-split race strategy recommendations
- Training load analysis and optimization scores
- Performance trend analysis with improvement potential

### 4.9 Injury Predictor (`app/injury_predictor.py`)

**Purpose**: ML-based injury risk assessment and prevention using authentic training data

**Feature Extraction from Real Activities**:
- Training load patterns and weekly progression spikes
- Biomechanical indicators from pace and cadence data
- Recovery time analysis between hard sessions
- Progressive overload monitoring from distance/intensity
- Heart rate zone distribution patterns

**Risk Assessment Models**:
- Rule-based prediction using established sports science principles
- Multi-factor risk scoring (training load, progression rate, recovery)
- Feature analysis including weekly mileage increases, consecutive training days
- Personalized risk thresholds based on athlete history

**Prevention Recommendations**:
- Training modification suggestions (reduce intensity/volume)
- Recovery protocol recommendations (rest days, cross-training)
- Progressive loading advice (10% rule compliance)
- Heart rate zone distribution optimization

### 4.10 Data Processor (`app/data_processor.py`)

**Purpose**: Core analytics engine for authentic performance calculation

**Processing Functions**:
- `process_athlete_daily_performance()`: Real activity data aggregation
- `get_athlete_performance_summary()`: Historical trend analysis from Strava data
- `get_team_overview()`: Community-wide statistics from actual activities

**Calculated Metrics from Real Data**:
- TRIMP (Training Impulse) from heart rate and duration
- Pace progression analysis from recent activities
- Training load distribution from actual workout intensities
- Performance status based on planned vs. actual metrics
- Weekly/monthly trend analysis using authentic timestamps

### 4.11 Notification System (`app/mail_notifier.py`)

**Purpose**: SMTP-based email communication system

**Notification Types**:
- Daily training summaries with real performance data
- Performance alerts based on actual metric thresholds
- Injury risk notifications from ML analysis
- Achievement celebrations for distance/pace milestones
- Training plan compliance updates

**Technical Features**:
- Built-in Python smtplib (no external dependencies)
- HTML and plain text email templates
- SMTP authentication and TLS encryption
- Delivery status tracking in database
- Error handling with retry logic

## 5. Frontend Architecture

### 5.1 Community Dashboard (`templates/community_standalone.html`)

**Purpose**: Main application interface with modern glassmorphism design and real-time metrics

**UI Design Features**:
- **Glassmorphism Theme**: Dark background with semi-transparent elements and white text
- **Responsive Layout**: Bootstrap-based grid system optimized for all devices
- **Modern Typography**: Clean, readable fonts with proper contrast ratios

**Interactive Components**:
- **KPI Cards**: Total athletes (1), distance (104.7km), activities (14), average pace (7:13 min/km)
- **Performance Leaderboard**: Real-time ranking by distance and average pace from authentic Strava data
- **Training Load Distribution**: Doughnut chart showing sport type breakdown (100% running)
- **Community Trends**: 7-day line chart tracking daily distance and activity count
- **Activity Stream**: Live feed of recent activities with achievement milestones
- **Strava Connect**: OAuth integration button for new athlete onboarding

**Technical Implementation**:
- Vanilla JavaScript with fetch API for asynchronous data loading
- Chart.js integration for interactive visualizations
- Error handling with user-friendly fallback messages
- Auto-refresh every 30 seconds for live updates
- Optimized DOM manipulation for performance

### 5.2 Race Predictor (`templates/race_predictor.html`)

**Purpose**: AI-powered race prediction interface with scientific algorithms

**Core Features**:
- **Distance Selection**: Dropdown for 5K, 10K, Half Marathon, Marathon predictions
- **AI Recommendations Panel**: Prominent display of Google Gemini insights with styled formatting
- **Scientific Predictions**: VDOT, Jack Daniels, and Riegel formula calculations
- **Performance Metrics**: Current pace analysis and confidence scoring

**AI Integration Display**:
- Real-time Gemini API responses with personalized advice
- Formatted recommendations including optimal race distances, training focus, predicted times
- Injury prevention guidance and long-term goal planning
- Fallback to rule-based recommendations if AI unavailable

**Technical Features**:
- Dynamic athlete selection with real Strava data
- Dual API calls (prediction algorithms + AI recommendations)
- Responsive design with glassmorphism styling
- Loading states and error handling for both prediction types

### 5.3 Risk Analyser (`templates/risk_analyser.html`)

**Purpose**: ML-based injury risk assessment interface

**Risk Assessment Display**:
- **Risk Score Visualization**: Color-coded risk levels (Low, Moderate, High, Very High)
- **Key Risk Factors**: Analysis of training load, progression rate, recovery patterns
- **Prevention Recommendations**: Personalized advice for training modifications
- **Trend Analysis**: Historical risk progression from authentic activity data

**Interactive Elements**:
- Athlete selection dropdown with real performance data
- Risk factor breakdown with detailed explanations
- Prevention plan generator based on ML analysis
- Training load optimization suggestions

### 5.4 Individual Dashboard (`templates/dashboard.html`)

**Purpose**: Personal athlete performance analytics interface

**Analytics Components**:
- **Performance Overview**: Key metrics from recent activities
- **Heart Rate Analysis**: Zone distribution from actual Strava data
- **Pace Progression**: Trend analysis over selectable time periods
- **Training Volume**: Weekly/monthly distance and activity tracking
- **Goal Tracking**: Progress toward personal targets

**Data Visualization**:
- Interactive Chart.js implementations
- Real-time data updates from Strava API
- Historical trend analysis with authentic timestamps
- Performance comparison tools

### 5.5 Authentication Success (`templates/auth_success.html`)

**Purpose**: Post-Strava OAuth success page with onboarding guidance

**User Experience Features**:
- Personalized welcome message with authenticated athlete name
- Quick navigation to main dashboard and analytics pages
- Success confirmation with next steps guidance
- Privacy and data usage information

## 6. Database Schema (PostgreSQL Production)

### 6.1 Core Tables with Authentic Data Storage

#### ReplitAthlete (Primary athlete profiles from Strava OAuth)
```sql
- id: Integer primary key
- name: VARCHAR(100) - Full name from Strava profile
- email: VARCHAR(255) UNIQUE - Contact email from Strava
- strava_athlete_id: BIGINT UNIQUE - Strava user ID for API calls
- access_token: TEXT - OAuth access token (encrypted)
- refresh_token: TEXT - OAuth refresh token (encrypted)
- token_expires_at: TIMESTAMP - Token expiration for refresh logic
- is_active: BOOLEAN DEFAULT TRUE - Account status
- ftp: FLOAT - Functional Threshold Power (if available)
- lthr: INTEGER - Lactate Threshold Heart Rate
- max_hr: INTEGER - Maximum Heart Rate
- training_zones: TEXT - JSON string for HR/pace zones
- preferences: TEXT - JSON string for user preferences
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
- last_sync: TIMESTAMP - Last successful Strava sync
```

#### Activity (Authentic Strava activity data)
```sql
- id: Integer primary key
- athlete_id: INTEGER FOREIGN KEY → ReplitAthlete.id
- strava_activity_id: BIGINT UNIQUE - Strava activity ID
- name: VARCHAR(255) - Activity title from Strava
- sport_type: VARCHAR(50) - Run, Ride, Swim, etc.
- start_date: TIMESTAMP - Activity start time (UTC)
- distance: FLOAT - Distance in meters
- moving_time: INTEGER - Active time in seconds
- elapsed_time: INTEGER - Total time including stops
- total_elevation_gain: FLOAT - Elevation gain in meters
- average_speed: FLOAT - Speed in m/s
- max_speed: FLOAT - Maximum speed in m/s
- average_cadence: FLOAT - Steps/minute for running
- average_heartrate: FLOAT - Average HR during activity
- max_heartrate: FLOAT - Maximum HR during activity
- calories: FLOAT - Estimated calories burned
- suffer_score: FLOAT - Strava relative effort score
- training_stress_score: FLOAT - TSS calculation
- intensity_factor: FLOAT - IF calculation
- detailed_data: TEXT - JSON string for streams data (pace, HR zones)
- created_at: TIMESTAMP DEFAULT NOW()
```

#### DailySummary (Aggregated performance metrics)
```sql
- id: Integer primary key
- athlete_id: INTEGER FOREIGN KEY → ReplitAthlete.id
- summary_date: DATE - Date of performance summary
- total_distance: FLOAT DEFAULT 0.0 - Daily distance sum
- total_moving_time: INTEGER DEFAULT 0 - Daily active time
- total_elevation_gain: FLOAT DEFAULT 0.0 - Daily elevation
- activity_count: INTEGER DEFAULT 0 - Number of activities
- average_pace: FLOAT - Weighted average pace (min/km)
- average_heart_rate: FLOAT - Session average HR
- training_load: FLOAT - TRIMP calculation from HR data
- planned_vs_actual_distance: FLOAT - Compliance percentage
- planned_vs_actual_duration: FLOAT - Compliance percentage
- status: VARCHAR(50) - "On Track", "Under-performed", etc.
- insights: TEXT - JSON string for AI-generated insights
- created_at: TIMESTAMP DEFAULT NOW()
```

#### PlannedWorkout (Training plan data)
```sql
- id: Integer primary key
- athlete_id: INTEGER FOREIGN KEY → ReplitAthlete.id
- planned_date: DATE - Scheduled workout date
- workout_type: VARCHAR(50) - Easy, Tempo, Intervals, Long Run
- planned_distance: FLOAT - Target distance in meters
- planned_duration: INTEGER - Target duration in seconds
- planned_intensity: VARCHAR(20) - Easy, Moderate, Hard, Recovery
- workout_structure: TEXT - JSON string for detailed structure
- is_completed: BOOLEAN DEFAULT FALSE
- completed_activity_id: INTEGER FOREIGN KEY → Activity.id
- created_at: TIMESTAMP DEFAULT NOW()
```

#### SystemLog (Application monitoring and debugging)
```sql
- id: Integer primary key
- timestamp: TIMESTAMP DEFAULT NOW()
- level: VARCHAR(10) - DEBUG, INFO, WARNING, ERROR
- message: TEXT - Log message content
- module: VARCHAR(100) - Source module (e.g., ai_race_advisor)
- athlete_id: INTEGER FOREIGN KEY → ReplitAthlete.id (optional)
- context: TEXT - JSON string for additional context
```

#### NotificationLog (Email communication tracking)
```sql
- id: Integer primary key
- athlete_id: INTEGER FOREIGN KEY → ReplitAthlete.id
- notification_type: VARCHAR(50) - email, alert, summary
- subject: VARCHAR(255) - Email subject line
- message: TEXT - Email content
- sent_at: TIMESTAMP DEFAULT NOW()
- status: VARCHAR(20) DEFAULT 'pending' - pending, sent, failed
- error_message: TEXT - Error details if failed
```

### 6.2 Database Relationships and Indexes
```sql
-- Primary relationships
ReplitAthlete 1→N Activity
ReplitAthlete 1→N DailySummary  
ReplitAthlete 1→N PlannedWorkout
ReplitAthlete 1→N NotificationLog
PlannedWorkout 1→1 Activity (completed_activity_id)

-- Performance indexes
CREATE INDEX idx_activity_athlete_date ON Activity(athlete_id, start_date);
CREATE INDEX idx_activity_strava_id ON Activity(strava_activity_id);
CREATE INDEX idx_daily_summary_athlete_date ON DailySummary(athlete_id, summary_date);
CREATE INDEX idx_athlete_strava_id ON ReplitAthlete(strava_athlete_id);
CREATE INDEX idx_system_log_timestamp ON SystemLog(timestamp);
```

### 6.3 Data Integrity and Constraints
- All timestamps stored in UTC for consistency
- Strava IDs enforced as unique to prevent duplicate imports
- Foreign key constraints ensure referential integrity
- JSON fields validated at application level for structure
- Token fields encrypted at rest for security

## 7. Security Implementation

### 7.1 Authentication & Authorization
- **Strava OAuth 2.0**: Secure user authentication with scope-limited access
- **JWT Token Management**: Flask-JWT-Extended for session handling and API access
- **Token Refresh Logic**: Automatic refresh of expired Strava tokens
- **Secure Token Storage**: Encrypted access/refresh tokens in PostgreSQL
- **API Rate Limiting**: Respect Strava API limits with usage tracking

### 7.2 Data Protection & Privacy
- **Environment Variables**: All secrets managed via .env and Replit Secrets
- **HTTPS Enforcement**: TLS encryption for all external API communications
- **Input Validation**: SQLAlchemy ORM prevents SQL injection attacks
- **Data Minimization**: Only essential Strava data collected (activities, profile)
- **User Consent**: Clear data usage disclosure during OAuth flow

### 7.3 Security Module (`app/security.py`)
```python
class ReplitSecurity:
    def encrypt_token(self, token: str) -> str:
        # Token encryption for database storage
    
    def decrypt_token(self, encrypted_token: str) -> str:
        # Token decryption for API calls
    
    def validate_strava_token(self, athlete_id: int) -> bool:
        # Token validation and refresh logic
```

## 8. Performance Optimization & Architecture

### 8.1 Dependency Optimization (60% Reduction)
- **Original**: 113+ packages in requirements.txt
- **Optimized**: 45 essential packages in requirements-minimal.txt
- **Removed Unused**: Streamlit, Plotly, Flask-RESTX, OpenAI, Marshmallow
- **Performance Impact**: Faster startup, reduced memory footprint, improved deployment speed

### 8.2 Database Optimization
- **Indexed Queries**: Foreign keys and date ranges for fast joins
- **Connection Pooling**: SQLAlchemy engine optimization for concurrent access
- **Query Patterns**: Optimized joins for athlete-activity relationships
- **Background Processing**: APScheduler for heavy data sync operations
- **UTC Timestamps**: Consistent timezone handling for global users

### 8.3 Frontend Performance
- **Client-Side Charts**: Chart.js instead of server-side Plotly rendering
- **Async Data Loading**: Fetch API with loading states and error handling
- **Minimal DOM Updates**: Efficient JavaScript for real-time dashboard updates
- **Glassmorphism CSS**: Optimized styling with hardware acceleration

### 8.4 API Optimization
- **Rate Limit Respect**: Strava API usage tracking to prevent throttling
- **Token Management**: Automatic refresh prevents authentication failures
- **Error Handling**: Graceful degradation when external services unavailable
- **Authentic Data Priority**: Real-time Strava sync over cached data

## 9. Background Processing & Real-time Features

### 9.1 APScheduler Integration (`app/__init__.py`)
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=send_athlete_update,
    trigger="interval",
    minutes=5,
    id='athlete_updates'
)
scheduler.start()
```

### 9.2 Scheduled Tasks (Every 5 Minutes)
- **Athlete Data Sync**: Fetch latest Strava activities for all active athletes
- **Performance Processing**: Calculate daily metrics, training load, TRIMP scores
- **Community Updates**: Refresh leaderboard and KPI calculations
- **Token Maintenance**: Refresh expired Strava OAuth tokens automatically

### 9.3 Real-time Dashboard Features
- **Live Data Updates**: 30-second auto-refresh for community metrics
- **Activity Stream**: Real-time feed of recent activities with achievements
- **Performance Notifications**: Immediate display of new PRs and milestones
- **Error Handling**: Graceful degradation when sync fails

### 9.4 Background Processing Functions (`app/simple_routes.py`)
```python
def send_athlete_update():
    """Process updates for all connected athletes"""
    active_athletes = db.session.query(ReplitAthlete).filter_by(is_active=True).all()
    for athlete in active_athletes:
        update_data = get_lightweight_update(athlete.id)
        # Process performance metrics and sync latest activities
```

## 10. Error Handling & Monitoring

### 10.1 Comprehensive Error Management
- **API Failure Handling**: Graceful degradation when Strava or Gemini APIs unavailable
- **Token Refresh**: Automatic handling of expired OAuth tokens with user notification
- **Database Errors**: Transaction rollback and recovery for data integrity
- **User-Friendly Messages**: Clear error communication without exposing system details

### 10.2 Replit-Optimized Logging (`app/config.py`)
```python
def configure_replit_logging(app):
    """Configure logging optimized for Replit environment"""
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        athlete_id = getattr(record, 'athlete_id', 'N/A')
        record.msg = f"[{record.module}] [athlete_id:{athlete_id}] {record.msg}"
        return record
```

### 10.3 Structured Logging Examples
```
2025-06-09 04:27:22,232 INFO [app.ai_race_advisor] [athlete_id:N/A] Sending prompt to Gemini API
2025-06-09 04:27:24,960 INFO [app.ai_race_advisor] [athlete_id:N/A] Gemini API Response: Based on the provided data...
2025-06-09 04:29:30,587 INFO [app.simple_routes] [athlete_id:N/A] Fetching community overview data
```

### 10.4 Error Recovery Mechanisms
- **AI Fallback**: Rule-based recommendations when Gemini API fails
- **Data Validation**: Input sanitization and type checking for all user inputs
- **Rate Limit Handling**: Exponential backoff for Strava API rate limits
- **Database Backup**: Automatic data persistence with transaction safety

## 11. Deployment Architecture

### 11.1 Replit Production Configuration
```python
# main.py - Application entry point
from app import create_app
app = create_app()

# .replit - Deployment configuration
run = "gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app"
```

### 11.2 Environment Management
- **Production Database**: PostgreSQL via DATABASE_URL environment variable
- **Secret Management**: Strava API keys, Gemini API key via Replit Secrets
- **Auto-scaling**: Gunicorn worker processes with reuse-port optimization
- **Health Monitoring**: Background scheduler status and API connectivity checks

### 11.3 Production Features
- **Dependency Optimization**: 45 essential packages for faster deployment
- **Error Logging**: Comprehensive monitoring with athlete context
- **Token Security**: Encrypted OAuth tokens with automatic refresh
- **API Rate Limiting**: Strava usage tracking to prevent service interruption

## 12. API Documentation & Routes

### 12.1 Authentication Endpoints
```
GET /api/auth/strava/authorize
- Generates Strava OAuth authorization URL with proper scopes
- Response: {"authorization_url": "https://www.strava.com/oauth/authorize?..."}

GET /api/auth/strava/callback?code={code}&scope={scope}
- Processes OAuth callback, exchanges code for tokens, creates athlete account
- Redirects to /auth/success with athlete information
- Creates initial ReplitAthlete record with encrypted tokens
```

### 12.2 Community Dashboard Endpoints
```
GET /
- Main community dashboard with glassmorphism UI
- Template: community_standalone.html

GET /api/community/overview
- Real-time community statistics from authentic Strava data
- Response: {
    kpis: {totalAthletes, totalDistance, totalActivities, avgPace},
    leaderboard: [{id, name, distance, avg_pace, activities, avg_hr}],
    trainingLoadDistribution: {data: [distance_by_sport], labels: [sport_types]},
    communityTrends: {datasets: [daily_distance, daily_activities], labels: [dates]}
  }

GET /api/community/activity-stream
- Live activity feed with achievements and milestones
- Response: {stream: [{type, athlete_name, activity_name, distance_km, pace, relative_time}]}
```

### 12.3 AI & Prediction Endpoints
```
GET /race_predictor?athlete_id={id}
- AI-powered race prediction interface with Gemini integration
- Template: race_predictor.html

GET /api/athletes/{id}/ai-recommendations
- Google Gemini AI personalized race recommendations
- Response: {recommendations: [optimal_distance, training_focus, predicted_times, recovery_advice]}

GET /api/athletes/{id}/race-prediction?distance={distance}
- Scientific race prediction using VDOT, Jack Daniels, Riegel algorithms
- Response: {predicted_time, confidence_score, training_paces, methodology}

GET /api/athletes/{id}/race-optimization?distance={distance}
- Advanced pacing strategy and training optimization
- Response: {pacing_strategy, heart_rate_targets, splits, optimization_metrics}
```

### 12.4 Risk Analysis Endpoints
```
GET /risk_analyser?athlete_id={id}
- ML-based injury risk assessment interface
- Template: risk_analyser.html

GET /api/athletes/{id}/injury-risk
- Injury risk prediction from training load analysis
- Response: {risk_score, risk_level, key_factors, confidence}

GET /api/athletes/{id}/injury-prevention
- Personalized injury prevention recommendations
- Response: {prevention_plan, training_modifications, recovery_protocols}
```

### 12.5 Performance Analytics Endpoints
```
GET /dashboard?athlete_id={id}
- Individual athlete performance dashboard
- Template: dashboard.html

GET /api/athletes/{id}/summary
- Comprehensive athlete performance summary with authentic data
- Response: {athlete, recent_activities, performance_metrics, training_trends}

GET /api/analytics/data?athlete_id={id}&days={period}
- Time-series analytics data for visualizations
- Response: {heartRateZones, elevationAnalysis, paceAnalysis, trainingVolume}
```

## 13. Current Production Status

### 13.1 Live Implementation Features
- **Community Dashboard**: Real-time metrics from 1 active athlete (104.7km total distance)
- **AI Race Recommendations**: Google Gemini providing personalized advice (sub-40 minute 10K predictions)
- **Authentic Strava Data**: 4 recent activities with actual pace analysis (7:13 min/km average)
- **Performance Analytics**: Heart rate zones, training load, TRIMP calculations
- **Injury Risk Assessment**: ML-based analysis of training patterns
- **Background Sync**: 5-minute intervals for automatic data updates

### 13.2 Production Metrics (Live Data)
```
Active Athletes: 1
Total Distance: 104.7 km (30 days)
Total Activities: 14
Average Pace: 7:13 min/km
Recent Performance: 10.05km at 7:00 min/km pace
Training Load Distribution: 100% Running
```

### 13.3 Technical Architecture Status
- **Dependencies**: Optimized from 113+ to 45 essential packages (60% reduction)
- **Database**: PostgreSQL production with encrypted token storage
- **APIs**: Strava OAuth 2.0 + Google Gemini AI integration active
- **Security**: Token encryption, rate limiting, comprehensive error handling
- **Monitoring**: Structured logging with athlete context and performance tracking

## 14. Future Enhancements

### 14.1 Immediate Roadmap
- **Multi-athlete Scaling**: Support for larger training communities
- **Advanced ML Models**: Enhanced injury prediction with more training data
- **Mobile Optimization**: Progressive Web App (PWA) capabilities
- **Social Features**: Athlete interactions, group challenges, training partnerships

### 14.2 Long-term Vision
- **Wearable Integration**: Garmin, Polar, Suunto device connectivity
- **Coach Portal**: Training plan management and athlete monitoring tools
- **Marketplace**: Training plans, nutrition guides, equipment recommendations
- **Performance Insights**: Advanced analytics with predictive modeling

This comprehensive solution design document reflects the current state of the Marathon Training Dashboard - a production-ready application with authentic Strava data integration, AI-powered insights, and modern glassmorphism UI design optimized for performance and scalability.