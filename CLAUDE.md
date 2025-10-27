# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based student and teacher information management system (学生教师信息管理系统) that provides web interfaces for managing school data. The system supports user authentication, role-based access control, and bulk import/export functionality for student and teacher records.

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Database Management
```bash
# Initialize database (first time only)
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Admin User Setup
```bash
# Create/update admin user (uses .env file for credentials)
python create_admin.py
```

### Development Server
```bash
# Run development server
python stu-list.py
# OR
flask run
```

### Production Deployment
```bash
# Start with Gunicorn (for production)
gunicorn --workers 3 --bind unix:/tmp/stu-list.sock -m 007 wsgi:app
```

## Architecture Overview

### Application Structure
- **Flask Application**: Main application factory in [`app/__init__.py`](app/__init__.py)
- **Database Models**: SQLAlchemy models in [`app/models.py`](app/models.py) - User, Student, Teacher
- **Routes**: Web endpoints and business logic in [`app/routes.py`](app/routes.py)
- **Forms**: WTForms for form handling in [`app/forms.py`](app/forms.py)
- **Authentication**: Login system with role-based access in [`app/auth.py`](app/auth.py)
- **Templates**: Bootstrap 5 templates in [`app/templates/`](app/templates/)

### Key Components

#### Database Models
- **User**: Authentication users with admin flags and school associations
- **Student**: Student records with exam types, subjects, and school info
- **Teacher**: Teacher records with roles, subjects, and teaching assignments

#### Authentication & Authorization
- Flask-Login for session management
- Role-based access control (admin vs regular users)
- Custom `@admin_required` decorator for admin-only routes

#### Data Import/Export
- Excel-based bulk import using pandas and openpyxl
- Support for student and teacher data imports
- Error handling and validation for imported data

### Configuration
- Environment variables loaded from `.env` file
- Database: SQLite (stu-list.db)
- Admin credentials configurable via environment variables
- See [`config.py`](config.py) for configuration structure

### Key Routes
- `/` - Login page and main redirect
- `/admin` - Admin panel (admin only)
- `/user` - User panel for regular users
- `/import/students`, `/import/teachers` - Bulk import functionality
- `/search/*` - Search and edit capabilities

## Dependencies

Main dependencies from [`requirements.txt`](requirements.txt):
- **Flask 3.1.2** - Web framework
- **Flask-SQLAlchemy 3.1.1** - ORM
- **Flask-Login 0.6.3** - User authentication
- **Flask-Migrate 4.0.7** - Database migrations
- **Flask-Bootstrap5 2.4.0** - UI framework
- **pandas 2.3.3** - Data processing for imports
- **openpyxl 3.1.5** - Excel file handling
- **gunicorn 23.0.0** - Production server

## File Processing

The system handles Excel imports for student and teacher data with specific column mappings and validation. Import functionality includes error handling and detailed feedback for invalid data.

## Logging

Custom logging utilities in [`app/log_utils.py`](app/log_utils.py) for application-level logging and audit trails.