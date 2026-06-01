# Practice Logger API

FastAPI backend for a music practice tracking application.

This API supports user authentication, practice task management, practice session tracking, active session restore, and role-aware access for future student, teacher, and admin workflows.

It is designed to work with the React frontend:

[Practice Logger UI] (https://github.com/ConForza/Practice-Logger-UI)

## Current features

- User registration
- User login with JWT authentication
- Current user endpoint via `/auth/me`
- Protected routes
- Task CRUD
- Start and end practice sessions
- Active practice session lookup
- Session history
- Role-aware user state
- Teacher/admin role-check dependencies
- Protected teacher/admin test routes
- Validation to prevent deleting tasks with active sessions
- Teacher endpoint for listing student users

## Tech stack

- Python
- FastAPI
- SQLAlchemy
- SQLite for local development
- Pydantic
- JWT authentication
- Pytest

## Getting started

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file based on your local settings.

Example:

```env
jwt_secret_key=your-development-secret-key
algorithm=HS256
```

Run the development server:

```bash
uvicorn main:app --reload
```

The API will be available at:

```txt
http://127.0.0.1:8000
```

Interactive API docs:

```txt
http://127.0.0.1:8000/docs
```

## Main endpoints

### Auth

```txt
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

### Tasks

```txt
GET    /api/v1/tasks
POST   /api/v1/tasks
DELETE /api/v1/tasks/{task_id}
```

### Practice sessions

```txt
POST /api/v1/tasks/{task_id}/sessions/start
POST /api/v1/tasks/{task_id}/sessions/end
GET  /api/v1/sessions
GET  /api/v1/sessions/active
```

### Teacher

```txt
GET /api/v1/teacher/status
GET /api/v1/teacher/students
```

### Admin

```txt
GET /api/v1/admin/status
```

## Project status

The student-facing API is functional. Teacher and admin role infrastructure has been added, but full teacher/admin features are still planned.

## Planned improvements

- Teacher view of student practice history
- Teacher task assignment
- Admin user management
- Role management
- PostgreSQL support
- Alembic migrations
- Expanded automated tests
- Deployment configuration

## Related project

Frontend:

[Practice Logger UI](https://github.com/ConForza/Practice-Logger-UI)
