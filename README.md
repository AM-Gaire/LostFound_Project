# Lost & Found Project

A full-stack Django web application for managing lost and found items on campus. Students can report lost or found items, search the database, and submit claims, while staff and admins review claims and track activity through an audit log.

## Features

- **Role-based accounts** (Student, Staff, Admin) with registration, login, logout, and password reset
- **Item reporting** for both lost and found items, with category, location, date, and optional image upload
- **Search and filter** for found items by keyword and category
- **Claims workflow**: students submit identity verification answers to claim a found item; staff/admin review, approve, reject, or request more info
- **Admin dashboard** for managing users and marking items as collected
- **Audit log** for tracking key actions across the system
- **Automated tests** covering reporting permissions, form validation, and search behavior

## Tech Stack

- **Backend:** Django 6.0
- **Database:** PostgreSQL (via psycopg2-binary)
- **Image handling:** Pillow
- **Config:** python-decouple (environment variables)
- **Frontend:** Django templates (HTML)

## Getting Started

### Prerequisites
- Python 3.x
- PostgreSQL

### Installation

```bash
# Clone the repository
git clone https://github.com/AM-Gaire/LostFound_Project.git
cd LostFound_Project

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your database credentials and secret key

# Run migrations
python manage.py migrate

# Create a superuser (optional, for admin access)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

### Running Tests

```bash
python manage.py test
```

## Project Structure

```
LostFound_Project/
├── accounts/          # User model, auth, registration, user management
├── items/             # Item reporting and search
├── claims/            # Claims workflow and audit log
├── lostfound_system/  # Project settings and URL configuration
└── templates/         # HTML templates
```

## License

This project currently has no license specified.
