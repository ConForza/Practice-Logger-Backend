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

- Role-based access for student, teacher, and admin users
- Task CRUD for student users
- Teacher-assigned tasks
- Teacher-assigned tasks store internal teacher-student ownership data
- Start and end timed practice sessions
- Multi-task practice sessions with one current task at a time
- Explicit open/completed task lifecycle with task reopening
- Active practice session lookup
- Session history
- Teacher endpoint for listing assigned students
- Teacher endpoint for viewing selected assigned student practice sessions
- Teacher endpoint for assigning tasks to assigned students
- Teacher weekly practice summaries for assigned students
- Admin user listing
- Admin role management
- Admin user activation/deactivation
- Admin password reset
- Admin-managed teacher-student assignments
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

The main tables are:

- `users`
- `tasks`
- `sessions`
- `session_tasks`
- `teacher_student_links`

Teacher-student links control which students a teacher can access. Teacher-assigned tasks can also store a `teacher_student_link_id`, allowing the frontend to distinguish teacher-assigned tasks from student-created tasks. SQLAlchemy is used for model definitions, relationships, and database queries.

On startup, the backend runs an idempotent schema upgrade that adds the
multi-task session columns, creates `session_tasks`, and backfills existing
sessions from their legacy `task_id` ownership. Back up the production
database before the first deployment of this version and verify the migration
through the health endpoint and session history before switching the frontend.

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
PATCH  /api/v1/tasks/{task_id}/status
```

### Practice sessions

```txt
POST /api/v1/sessions/start
POST /api/v1/sessions/{session_id}/current-task
DELETE /api/v1/sessions/{session_id}/current-task
POST /api/v1/sessions/{session_id}/end
GET  /api/v1/sessions
GET  /api/v1/sessions/active
GET  /api/v1/sessions/{session_id}
DELETE /api/v1/sessions/{session_id}

# Temporary compatibility routes for the pre-migration frontend
POST /api/v1/sessions/start/{task_id}
POST /api/v1/sessions/end/{task_id}
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
GET    /api/v1/admin/status
GET    /api/v1/admin/users
PATCH  /api/v1/admin/users/{user_id}/role
PATCH  /api/v1/admin/users/{user_id}/status
GET    /api/v1/admin/teacher-student-links
POST   /api/v1/admin/teacher-student-links
DELETE /api/v1/admin/teacher-student-links/{link_id}
```

### User account management

```txt
PATCH /api/v1/users/me/password
PATCH /api/v1/users/{user_id}/password
```

## Deployment

The backend is deployed on Railway with a Railway PostgreSQL database.
The React frontend is deployed separately on Netlify and connects to this API using a `VITE_API_BASE_URL` environment variable.

## Project status

The core student, teacher, and admin workflows are functional and deployed.
Students can create tasks, complete teacher-assigned tasks, and log timed practice sessions. Teachers can view only students assigned to them, review session history, assign tasks, and view weekly practice summaries. Admins can manage user accounts and teacher-student assignments from the admin workflow.

## Planned improvements

- More detailed progress analytics
- Refresh-token support

## Related project

Frontend:

[Practice Logger UI](https://github.com/ConForza/Practice-Logger-UI)
