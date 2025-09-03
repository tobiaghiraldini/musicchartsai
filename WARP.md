# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Essential Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install Python dependencies  
pip install -r requirements.txt

# Install Node dependencies
npm install

# Copy environment file
cp env.sample .env
```

### Development Server
```bash
# Start Django development server
python manage.py runserver

# Run frontend build (development with watch)
npm run dev

# Build Tailwind CSS
npx tailwindcss -i ./static/assets/style.css -o ./static/dist/css/output.css --watch
```

### Database Operations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --no-input
```

### Background Tasks (Celery)
```bash
# Start Celery worker with beat scheduler
celery -A home worker -l info -B

# Start Redis (required for Celery)
redis-server

# Or use Docker Redis
docker run -p 6379:6379 -d redis:7.0.12
```

### Data Management Commands
```bash
# Fetch track metadata from Soundcharts API
python manage.py fetch_track_metadata --all

# Fetch audience data for specific track
python manage.py fetch_audience_data --track-uuid <uuid> --platform spotify

# Process all tracks audience data
python manage.py fetch_audience_data --all-tracks --limit 100
```

### Testing & Build
```bash
# Run single test
python manage.py test apps.soundcharts.tests.TestAudienceDataProcessor

# Build for production
./build.sh

# Production build with webpack
npm run build
```

### Docker Operations
```bash
# Build and start all services
docker-compose up --build

# Start only specific service
docker-compose up appseed-app

# View logs
docker-compose logs -f celery
```

## Architecture Overview

### Project Structure
This is a Django 5.2 project with a modular app-based architecture:

- **config/**: Django project configuration, settings, and URL routing
- **apps/**: Modular Django applications for specific functionality
- **templates/**: Jinja2 templates with Tailwind CSS styling
- **static/**: Frontend assets (CSS, JS, images)
- **tasks_scripts/**: Python scripts for Celery background tasks
- **cli/**: Command-line interface helpers and utilities

### Key Django Apps

1. **apps/soundcharts**: Core music data integration
   - Models: Track, Artist, Platform, Chart, ChartRanking, TrackAudience
   - Management commands for data fetching
   - API integration with Soundcharts and ACRCloud

2. **apps/charts**: Chart visualization and ranking system
   - Handles chart data processing and display

3. **apps/tasks**: Celery task management interface
   - Web UI for monitoring background tasks
   - Task execution and cancellation

4. **apps/users**: Extended user management
   - User profiles with roles (admin/user)
   - Authentication and authorization

5. **apps/pages**: Main application pages and views
   - Dashboard and landing pages
   - Celery task definitions

6. **apps/dyn_dt & apps/dyn_api**: Dynamic data tables and API
   - Configurable data visualization
   - RESTful API endpoints

### Technology Stack

**Backend:**
- Django 5.2 with Python 3.13
- Celery for background task processing
- Redis as message broker and cache
- SQLite (default) or PostgreSQL/MySQL
- Django REST Framework for APIs

**Frontend:**
- Tailwind CSS with Flowbite components
- Webpack for asset bundling
- ApexCharts for data visualization
- Node.js 22.0.0 for build tools

**External APIs:**
- Soundcharts API for music chart data
- ACRCloud API for music recognition

### Data Flow Architecture

1. **Data Ingestion**: Background Celery tasks fetch data from external APIs (Soundcharts, ACRCloud)
2. **Data Processing**: Raw API data is processed and stored in normalized Django models
3. **Data Presentation**: Web dashboard displays processed data with charts and tables
4. **Task Management**: Admin interface for monitoring and controlling background tasks

### Key Configuration Files

- **config/settings.py**: Django settings, database config, Celery setup, API keys
- **docker-compose.yml**: Multi-service Docker setup with Redis and Nginx
- **tailwind.config.js**: Tailwind CSS configuration with Flowbite integration
- **webpack.config.js**: Frontend asset bundling configuration

### Background Task System

The project uses Celery with Redis for asynchronous task processing:
- **Task Scripts**: Located in `tasks_scripts/` directory
- **Web Interface**: Available at `/tasks/` for monitoring
- **Management Commands**: Django commands for data fetching operations
- **Task Storage**: Results stored in database via django-celery-results

### Development Patterns

**Model Relationships:**
- Track ↔ Artist (many-to-many through credit_name)
- Track → Platform (audience data per platform)
- Chart → Platform (charts belong to specific platforms)
- ChartRanking → Track (tracks in chart positions)

**API Integration Pattern:**
- Service classes handle external API communication
- Processor classes handle data transformation and storage
- Management commands provide CLI interface
- Celery tasks for background processing

**Frontend Pattern:**
- Tailwind utility classes for styling
- Flowbite components for UI consistency
- ApexCharts for data visualization
- HTMX-style interactions for dynamic content

## Development Guidelines

### From Cursor Rules
- Follow Django MVT pattern strictly
- Use class-based views for complex logic, function-based for simple operations
- Leverage Django ORM, avoid raw SQL unless performance-critical
- Implement proper error handling and validation
- Use Django's security best practices (CSRF, XSS, SQL injection protection)
- Document implementation details in `/docs` folder per feature

### Multi-Agent Development
- The project uses a multi-agent development workflow with Planner/Executor roles
- Use virtual environment in `./venv` for Python operations
- Include debugging information in program output
- Update development progress in `docs/development-log.md`

### API Key Management
Environment variables for sensitive data:
- `SOUNDCHARTS_API_KEY` and `SOUNDCHARTS_APP_ID`
- `ACR_CLOUD_API_KEY` and `ACR_CLOUD_API_SECRET`
- `SECRET_KEY` for Django
- `CELERY_BROKER_URL` for Redis connection

### Database Considerations
- Default: SQLite for development
- Production: Configure PostgreSQL/MySQL via environment variables
- Models use UUIDs for external service integration
- Time-series data optimized with database indexes
- Unique constraints prevent duplicate chart entries
