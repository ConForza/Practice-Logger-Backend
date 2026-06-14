# Practice Logger API

FastAPI backend for **Practice Logger**, a full-stack music practice tracking application for students, teachers, and administrators.

This API supports user authentication, practice task management, timed practice sessions, active session restore, teacher-assigned tasks, weekly student progress tracking, and admin user management.

It is designed to work with the React frontend:

[Practice Logger UI](https://github.com/ConForza/Practice-Logger-UI)

## Live project

- Frontend app: https://practice-logger.netlify.app/
- API root: https://practice-logger-backend-production.up.railway.app/
- API docs: https://practice-logger-backend-production.up.railway.app/docs

## Current features

- User registration
- User login with JWT authentication
- Current user endpoint via `/auth/me`
- Hashed password authentication
- Role-based access for student, teacher, and admin users
- Task CRUD for student users
- Start and end timed practice sessions
- Active practice session lookup
- Session history
- Validation to prevent deleting tasks with active sessions
- Teacher endpoint for listing student users
- Teacher endpoint for viewing selected student practice sessions
- Teacher endpoint for assigning tasks to students
- Teacher weekly student progress ranking
- Admin user listing
- Admin role management
- Admin user activation/deactivation
- Protection against accidental admin self-demotion or self-deactivation

## Tech stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- JWT authentication
- OAuth2 password flow
- Pytest
- Railway

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
JWT_SECRET_KEY=your-development-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/practice_logger_dev
CORS_ORIGINS=http://localhost:5173
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

## Database

The application uses PostgreSQL for production and local development.

The main tables are:

- `users`
- `tasks`
- `sessions`

SQLAlchemy is used for model definitions, relationships, and database queries.

## Main endpoints

### Root / health

```txt
GET /     
GET /health
```

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
PUT    /api/v1/tasks/{task_id}
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
GET  /api/v1/teacher/status
GET  /api/v1/teacher/students
GET  /api/v1/teacher/students/{student_id}/sessions
POST /api/v1/teacher/students/{student_id}/tasks
GET  /api/v1/teacher/progress/weekly
```

### Admin

```txt
GET   /api/v1/admin/status
GET   /api/v1/admin/users
PATCH /api/v1/admin/users/{user_id}/role
PATCH /api/v1/admin/users/{user_id}/status
```

## Deployment

The backend is deployed on Railway with a Railway PostgreSQL database.

The React frontend is deployed separately on Netlify and connects to this API using a `VITE_API_BASE_URL` environment variable.

## Project status

The core student, teacher, and admin workflows are functional and deployed.

Students can create tasks and log timed practice sessions. Teachers can assign tasks, view student sessions, and monitor weekly progress. Admins can manage user accounts, roles, and account status.

## Planned improvements

- Admin password reset
- Teacher assignment overview
- Teacher-student ownership relationships
- Multiple tasks within a single practice session
- PWA support for students and teachers
- Alembic migrations
- Expanded automated tests
- More detailed progress analytics

## Related project

Frontend:

[Practice Logger UI](https://github.com/ConForza/Practice-Logger-UI)
