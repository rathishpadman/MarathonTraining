# Marathon Training Dashboard - Solution Design Document

## 1. Application Overview

The Marathon Training Dashboard is a comprehensive web application that integrates with Strava to provide advanced performance analytics, social training insights, and personalized athlete tracking for marathon runners. The system serves as a community platform where athletes can monitor their training progress, analyze performance metrics, predict race times, and assess injury risks.

### Key Features
- Strava OAuth integration for athlete authentication
- Real-time community dashboard with KPI metrics
- Advanced performance analytics and visualizations
- ML-based injury risk prediction
- Race time prediction algorithms
- Training optimization recommendations
- Email notifications and alerts
- Real-time WebSocket updates

## 2. Technology Stack

### Backend Framework
- **Flask 2.x**: Primary web framework with blueprint architecture
- **Flask-SQLAlchemy**: ORM for database operations
- **Flask-JWT-Extended**: JWT token authentication
- **Flask-SocketIO**: WebSocket support for real-time updates
- **Flask-Caching**: Response caching for performance
- **Flask-RESTx**: API documentation and validation

### Frontend Technologies
- **Bootstrap 5.1.3**: Responsive UI framework
- **Chart.js**: Data visualization and charting
- **Feather Icons**: Icon library
- **Vanilla JavaScript**: Client-side functionality
- **WebSocket**: Real-time communication

### Database & Storage
- **SQLite**: Primary database (configurable to PostgreSQL)
- **SQLAlchemy Models**: Data persistence layer

### External Integrations
- **Strava API**: Activity data sync and OAuth authentication
- **SMTP**: Email notifications

### Development & Deployment
- **Python 3.11**: Runtime environment
- **Gunicorn**: WSGI HTTP server
- **APScheduler**: Background job scheduling
- **Replit**: Cloud hosting platform

## 3. Project Structure

```
marathon-dashboard/
├── app/
│   ├── __init__.py              # Application factory and configuration
│   ├── config.py                # Configuration management
│   ├── models.py                # Database models
│   ├── simple_routes.py         # Main API routes and endpoints
│   ├── strava_client.py         # Strava API integration
│   ├── data_processor.py        # Core data processing logic
│   ├── race_optimizer.py        # Race prediction algorithms
│   ├── injury_predictor.py      # ML-based injury risk assessment
│   └── mail_notifier.py         # Email notification service
├── templates/
│   ├── community_dashboard.html # Main community dashboard
│   ├── analytics.html           # Individual athlete analytics
│   ├── race_optimizer.html      # Race optimization interface
│   └── auth_success.html        # Post-authentication success page
├── data/                        # Training data and models
├── tests/                       # Unit and integration tests
├── .env                         # Environment variables
├── main.py                      # Application entry point
└── pyproject.toml              # Python dependencies
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

### 4.6 Race Optimization (`app/race_optimizer.py`)

**Purpose**: Advanced race prediction and optimization algorithms

**Prediction Models**:
- **VDOT Algorithm**: VO2 max estimation from race times
- **Jack Daniels Formula**: Training pace calculations
- **Riegel Formula**: Race time extrapolation
- **McMillan Calculator**: Performance equivalency
- **Power-based predictions**: Advanced physiological modeling

**Features**:
- Multiple distance predictions (5K, 10K, Half Marathon, Marathon)
- Pacing strategy optimization
- Training zone recommendations
- Performance progression tracking
- Race readiness assessment

### 4.7 Injury Prediction (`app/injury_predictor.py`)

**Purpose**: ML-based injury risk assessment and prevention

**Feature Extraction**:
- Training load patterns and spikes
- Biomechanical indicators from activity data
- Recovery time analysis
- Progression rate monitoring
- Heart rate variability assessment

**Risk Assessment**:
- Rule-based prediction algorithms
- Multi-factor risk scoring
- Personalized prevention recommendations
- Training modification suggestions
- Recovery protocol recommendations

### 4.8 Notification System (`app/mail_notifier.py`)

**Purpose**: Automated email communication system

**Notification Types**:
- Daily training summaries
- Performance alerts and warnings
- Injury risk notifications
- Achievement celebrations
- Training plan updates

**Features**:
- HTML and plain text email templates
- SMTP integration with authentication
- Delivery status tracking
- Personalized content generation
- Error handling and retry logic

## 5. Frontend Architecture

### 5.1 Community Dashboard (`templates/community_dashboard.html`)

**Purpose**: Main application interface with real-time community metrics

**Components**:
- **KPI Cards**: Total athletes, distance, activities, average pace
- **Leaderboard**: Top performers by distance and performance
- **Training Load Chart**: Doughnut chart of athlete distribution
- **Community Trends**: Line chart of daily progress
- **Strava Connect Button**: New athlete registration

**JavaScript Features**:
- Asynchronous data loading with fetch API
- Real-time chart updates using Chart.js
- Error handling with user-friendly messages
- Auto-refresh functionality
- WebSocket integration for live updates

### 5.2 Analytics Dashboard (`templates/analytics.html`)

**Purpose**: Individual athlete performance analysis interface

**Visualization Components**:
- Heart rate zone distribution (doughnut chart)
- Elevation vs distance analysis (scatter plot)
- Pace progression over time (line chart)
- Training volume trends
- Performance insights and recommendations

**Interactive Features**:
- Time period selection (7, 30, 90 days)
- Dynamic chart rendering
- Athlete selection dropdown
- Export functionality for data

### 5.3 Race Optimizer (`templates/race_optimizer.html`)

**Purpose**: Race prediction and training optimization interface

**Features**:
- Race time prediction calculator
- Training pace recommendations
- Performance goal setting
- Pacing strategy visualization
- Training plan generation

### 5.4 Authentication Success (`templates/auth_success.html`)

**Purpose**: Post-Strava authentication landing page

**Features**:
- Welcome message with athlete name
- Navigation to dashboard and analytics
- Auto-redirect functionality
- Security and privacy information

## 6. Database Schema

### 6.1 Core Tables

#### ReplitAthlete
```sql
- id: Primary key
- name: Full name
- email: Contact email
- strava_athlete_id: Strava user ID
- access_token: OAuth access token
- refresh_token: OAuth refresh token
- token_expires_at: Token expiration
- is_active: Account status
- created_at: Registration date
- last_sync: Last data sync
```

#### Activity
```sql
- id: Primary key
- athlete_id: Foreign key to ReplitAthlete
- strava_activity_id: Strava activity ID
- name: Activity title
- distance: Distance in meters
- moving_time: Active time in seconds
- elapsed_time: Total time in seconds
- total_elevation_gain: Elevation in meters
- type: Activity type (Run, Ride, etc.)
- start_date: Activity start time
- average_speed: Speed in m/s
- max_speed: Maximum speed
- average_heartrate: Average HR
- max_heartrate: Maximum HR
- suffer_score: Strava relative effort
```

#### DailySummary
```sql
- id: Primary key
- athlete_id: Foreign key to ReplitAthlete
- summary_date: Date of summary
- total_distance: Daily distance
- total_duration: Total active time
- activity_count: Number of activities
- avg_pace: Average pace
- training_load: Calculated load
- status: Performance status
- insights: AI-generated insights
```

### 6.2 Relationships
- One-to-many: ReplitAthlete → Activity
- One-to-many: ReplitAthlete → DailySummary
- One-to-many: ReplitAthlete → PlannedWorkout

## 7. Security Implementation

### 7.1 Authentication & Authorization
- Strava OAuth 2.0 for user authentication
- JWT tokens for session management
- Secure token storage and refresh mechanisms
- API rate limiting and request validation

### 7.2 Data Protection
- Environment-based secret management
- HTTPS enforcement for external communications
- Input validation and sanitization
- SQL injection prevention through ORM

### 7.3 Privacy Compliance
- Minimal data collection from Strava
- Secure token storage
- User consent for data processing
- Data retention policies

## 8. Performance Optimization

### 8.1 Caching Strategy
- Flask-Caching for response caching
- Database query optimization
- Static asset caching
- API response caching for expensive operations

### 8.2 Database Optimization
- Indexed foreign keys for fast joins
- Optimized query patterns
- Connection pooling
- Background processing for heavy operations

### 8.3 Frontend Optimization
- Asynchronous JavaScript loading
- Chart.js performance tuning
- Minimal DOM manipulation
- Efficient event handling

## 9. Background Processing

### 9.1 Scheduled Tasks
- **Daily Summary Generation**: Aggregate athlete data
- **Activity Sync**: Fetch new Strava activities
- **Notification Dispatch**: Send email alerts
- **Data Cleanup**: Archive old processing logs

### 9.2 Real-time Updates
- WebSocket connections for live dashboard updates
- Event-driven architecture for data changes
- Efficient broadcasting to connected clients

## 10. Error Handling & Monitoring

### 10.1 Error Management
- Comprehensive exception handling
- User-friendly error messages
- Fallback mechanisms for API failures
- Graceful degradation for missing data

### 10.2 Logging & Monitoring
- Replit-optimized logging configuration
- Structured logging with athlete ID context
- Performance metric tracking
- Error rate monitoring

## 11. Deployment Architecture

### 11.1 Replit Configuration
- Gunicorn WSGI server with auto-reload
- Port binding on 0.0.0.0:5000
- Environment variable management
- Automatic dependency installation

### 11.2 Environment Management
- Development, staging, and production configurations
- Feature flags for A/B testing
- Database migration handling
- Secret management through environment variables

## 12. Testing Strategy

### 12.1 Unit Testing
- Model validation testing
- API endpoint testing
- Data processing algorithm testing
- Utility function testing

### 12.2 Integration Testing
- Strava API integration testing
- Database operation testing
- Email notification testing
- WebSocket functionality testing

## 13. Future Enhancements

### 13.1 Planned Features
- Mobile application development
- Advanced ML models for performance prediction
- Social features and athlete interactions
- Training plan marketplace
- Wearable device integrations

### 13.2 Scalability Considerations
- Database migration to PostgreSQL for production
- Microservices architecture for large scale
- CDN integration for static assets
- Load balancing for high availability

## 14. API Documentation

### 14.1 Authentication Endpoints
```
GET /api/auth/strava/authorize
- Returns Strava OAuth authorization URL
- Response: {"authorization_url": "https://strava.com/oauth/..."}

GET /api/auth/strava/callback?code=...
- Handles OAuth callback and creates athlete account
- Redirects to success page with athlete information
```

### 14.2 Community Endpoints
```
GET /api/community/overview
- Returns community-wide statistics and trends
- Response: {kpis, leaderboard, trainingLoadDistribution, communityTrends}

GET /api/analytics/data?days=30
- Returns analytics data for specified time period
- Response: {heartRateZones, elevationAnalysis, paceAnalysis, period_days}
```

### 14.3 Athlete Endpoints
```
GET /api/athletes
- Returns list of all active athletes
- Response: [{id, name, email, last_sync}, ...]

GET /api/athletes/{id}/summary
- Returns comprehensive athlete performance summary
- Response: {athlete, activities, performance_metrics, insights}
```

This solution design document provides a comprehensive overview of the Marathon Training Dashboard application architecture, covering all modules, technologies, and implementation details. The system is designed for scalability, maintainability, and extensibility while providing a rich user experience for marathon training analysis and community engagement.