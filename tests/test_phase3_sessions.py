import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

os.environ.setdefault("JWT_SECRET_KEY", "phase-three-test-secret-key")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from db.database import Base
from db.migrations import initialize_database
from db.models import (
    SessionDB,
    SessionTaskDB,
    TaskDB,
    TeacherStudentLinkDB,
    UserDB,
)
from core.deps import get_db
from core.time import ensure_utc
from main import app
from repositories.session_repository import SessionRepository
from services.session_service import SessionService


TEST_DIRECTORY = tempfile.TemporaryDirectory()
TEST_DATABASE_PATH = Path(TEST_DIRECTORY.name) / "api.sqlite3"
TEST_ENGINE = create_engine(
    f"sqlite:///{TEST_DATABASE_PATH}",
    connect_args={"check_same_thread": False},
)
TEST_SESSION_LOCAL = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=TEST_ENGINE,
)


def override_get_db():
    db = TEST_SESSION_LOCAL()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class PhaseThreeSessionTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(bind=TEST_ENGINE)
        initialize_database(TEST_ENGINE)
        self.client = TestClient(app)
        register = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "student@example.com",
                "password": "test-password",
            },
        )
        self.assertEqual(register.status_code, 201, register.text)
        login = self.client.post(
            "/api/v1/auth/login",
            data={
                "username": "student@example.com",
                "password": "test-password",
            },
        )
        self.assertEqual(login.status_code, 200, login.text)
        self.headers = {
            "Authorization": f"Bearer {login.json()['access_token']}"
        }

    def tearDown(self):
        self.client.close()

    def create_task(self, title: str):
        response = self.client.post(
            "/api/v1/tasks",
            json={"title": title, "description": None},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def register_and_login(self, email: str):
        register = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "test-password"},
        )
        self.assertEqual(register.status_code, 201, register.text)
        login = self.client.post(
            "/api/v1/auth/login",
            data={
                "username": email,
                "password": "test-password",
            },
        )
        self.assertEqual(login.status_code, 200, login.text)
        return {
            "Authorization": f"Bearer {login.json()['access_token']}"
        }, register.json()

    def test_multitask_session_and_explicit_task_lifecycle(self):
        scales = self.create_task("Scales")
        sonata = self.create_task("Sonata")

        started = self.client.post(
            "/api/v1/sessions/start",
            headers=self.headers,
        )
        self.assertEqual(started.status_code, 200, started.text)
        session_id = started.json()["id"]
        started_at = started.json()["started_at"]
        self.assertTrue(started_at.endswith(("Z", "+00:00")))
        self.assertTrue(
            started.json()["start_time"].endswith(("Z", "+00:00"))
        )
        self.assertIsNone(started.json()["current_task_id"])

        selected_scales = self.client.post(
            f"/api/v1/sessions/{session_id}/current-task",
            json={"task_id": scales["id"]},
            headers=self.headers,
        )
        self.assertEqual(selected_scales.status_code, 200)

        selected_sonata = self.client.post(
            f"/api/v1/sessions/{session_id}/current-task",
            json={"task_id": sonata["id"]},
            headers=self.headers,
        )
        self.assertEqual(selected_sonata.status_code, 200)
        self.assertEqual(selected_sonata.json()["id"], session_id)
        self.assertEqual(selected_sonata.json()["started_at"], started_at)
        self.assertIsNone(selected_sonata.json()["ended_at"])
        self.assertEqual(selected_sonata.json()["current_task_id"], sonata["id"])
        self.assertEqual(
            [task["id"] for task in selected_sonata.json()["tasks"]],
            [scales["id"], sonata["id"]],
        )

        cleared = self.client.delete(
            f"/api/v1/sessions/{session_id}/current-task",
            headers=self.headers,
        )
        self.assertEqual(cleared.status_code, 200, cleared.text)
        self.assertIsNone(cleared.json()["current_task_id"])
        self.assertEqual(len(cleared.json()["tasks"]), 2)

        selected_sonata = self.client.post(
            f"/api/v1/sessions/{session_id}/current-task",
            json={"task_id": sonata["id"]},
            headers=self.headers,
        )
        self.assertEqual(selected_sonata.status_code, 200)

        completed = self.client.patch(
            f"/api/v1/tasks/{sonata['id']}/status",
            json={"status": "completed"},
            headers=self.headers,
        )
        self.assertEqual(completed.status_code, 200, completed.text)
        self.assertEqual(completed.json()["status"], "completed")
        self.assertIsNotNone(completed.json()["completed_at"])

        active = self.client.get(
            "/api/v1/sessions/active",
            headers=self.headers,
        )
        self.assertEqual(active.status_code, 200)
        self.assertIsNone(active.json()["current_task_id"])
        self.assertEqual(len(active.json()["tasks"]), 2)

        ended = self.client.post(
            f"/api/v1/sessions/{session_id}/end",
            json={"notes": "Worked on both tasks"},
            headers=self.headers,
        )
        self.assertEqual(ended.status_code, 200, ended.text)
        self.assertEqual(ended.json()["status"], "completed")
        self.assertEqual(ended.json()["duration"], 0)
        self.assertTrue(
            ended.json()["ended_at"].endswith(("Z", "+00:00"))
        )
        self.assertTrue(
            ended.json()["start_time"].endswith(("Z", "+00:00"))
        )

        tasks = self.client.get("/api/v1/tasks", headers=self.headers).json()
        statuses = {task["id"]: task["status"] for task in tasks}
        self.assertEqual(statuses[scales["id"]], "open")
        self.assertEqual(statuses[sonata["id"]], "completed")

        reopened = self.client.patch(
            f"/api/v1/tasks/{sonata['id']}/status",
            json={"status": "open"},
            headers=self.headers,
        )
        self.assertEqual(reopened.status_code, 200)
        self.assertEqual(reopened.json()["status"], "open")
        self.assertIsNone(reopened.json()["completed_at"])

        history = self.client.get("/api/v1/sessions", headers=self.headers)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.json()[0]["tasks"]), 2)

    def test_legacy_naive_timestamps_are_serialized_as_utc(self):
        started = self.client.post(
            "/api/v1/sessions/start",
            headers=self.headers,
        )
        self.assertEqual(started.status_code, 200, started.text)
        session_id = started.json()["id"]
        legacy_started = datetime(2026, 8, 14, 17, 37, 1, 123456)
        legacy_ended = datetime(2026, 8, 14, 17, 39, 1, 123456)

        with TEST_SESSION_LOCAL() as db:
            session = db.get(SessionDB, session_id)
            session.timestamp = legacy_started
            session.started_at = legacy_started
            session.ended_at = legacy_ended
            db.commit()

        history = self.client.get("/api/v1/sessions", headers=self.headers)
        self.assertEqual(history.status_code, 200, history.text)
        session_json = history.json()[0]
        self.assertEqual(
            session_json["started_at"], "2026-08-14T17:37:01.123456Z"
        )
        self.assertEqual(
            session_json["start_time"], "2026-08-14T17:37:01.123456Z"
        )
        self.assertEqual(
            session_json["ended_at"], "2026-08-14T17:39:01.123456Z"
        )

        ended = self.client.post(
            f"/api/v1/sessions/{session_id}/end",
            headers=self.headers,
        )
        self.assertEqual(ended.status_code, 400)

    def test_duration_normalizes_naive_and_aware_utc_values(self):
        naive_start = datetime.now(timezone.utc).replace(
            tzinfo=None
        ) - timedelta(minutes=2)
        aware_start = datetime.now(timezone.utc) - timedelta(minutes=2)

        naive_duration = SessionService.calculate_session_duration(naive_start)
        aware_duration = SessionService.calculate_session_duration(aware_start)

        self.assertGreaterEqual(naive_duration, 1)
        self.assertGreaterEqual(aware_duration, 1)
        self.assertLessEqual(naive_duration, 3)
        self.assertLessEqual(aware_duration, 3)
        self.assertEqual(
            ensure_utc(naive_start), naive_start.replace(tzinfo=timezone.utc)
        )

    def test_legacy_task_routes_still_work(self):
        task = self.create_task("Legacy task")
        started = self.client.post(
            f"/api/v1/sessions/start/{task['id']}",
            headers=self.headers,
        )
        self.assertEqual(started.status_code, 200, started.text)
        session_id = started.json()["id"]

        with TEST_SESSION_LOCAL() as db:
            session = db.get(SessionDB, session_id)
            old_start = datetime.now(timezone.utc).replace(
                tzinfo=None
            ) - timedelta(minutes=2)
            session.timestamp = old_start
            session.started_at = old_start
            db.commit()

        ended = self.client.post(
            f"/api/v1/sessions/end/{task['id']}",
            json={"notes": "Legacy route"},
            headers=self.headers,
        )
        self.assertEqual(ended.status_code, 200, ended.text)
        self.assertEqual(ended.json()["task_id"], task["id"])

        current_task = self.client.get(
            f"/api/v1/tasks",
            headers=self.headers,
        ).json()[0]
        self.assertEqual(current_task["status"], "completed")

    def test_legacy_end_prefers_current_task_after_switching(self):
        original_task = self.create_task("Legacy original task")
        switched_task = self.create_task("Legacy switched task")
        started = self.client.post(
            f"/api/v1/sessions/start/{original_task['id']}",
            headers=self.headers,
        )
        self.assertEqual(started.status_code, 200, started.text)
        session_id = started.json()["id"]

        with TEST_SESSION_LOCAL() as db:
            session = db.get(SessionDB, session_id)
            old_start = datetime.now(timezone.utc).replace(
                tzinfo=None
            ) - timedelta(minutes=2)
            session.timestamp = old_start
            session.started_at = old_start
            db.commit()

        switched = self.client.post(
            f"/api/v1/sessions/{session_id}/current-task",
            json={"task_id": switched_task["id"]},
            headers=self.headers,
        )
        self.assertEqual(switched.status_code, 200, switched.text)

        wrong_task_end = self.client.post(
            f"/api/v1/sessions/end/{original_task['id']}",
            json={"notes": "Should not end switched session"},
            headers=self.headers,
        )
        self.assertEqual(wrong_task_end.status_code, 404, wrong_task_end.text)

        active = self.client.get(
            "/api/v1/sessions/active",
            headers=self.headers,
        )
        self.assertEqual(active.status_code, 200)
        self.assertEqual(active.json()["id"], session_id)
        self.assertEqual(
            active.json()["current_task_id"], switched_task["id"]
        )

        ended = self.client.post(
            f"/api/v1/sessions/end/{switched_task['id']}",
            json={"notes": "End switched task"},
            headers=self.headers,
        )
        self.assertEqual(ended.status_code, 200, ended.text)
        self.assertEqual(ended.json()["task_id"], switched_task["id"])

        tasks = self.client.get("/api/v1/tasks", headers=self.headers).json()
        statuses = {task["id"]: task["status"] for task in tasks}
        self.assertEqual(statuses[original_task["id"]], "open")
        self.assertEqual(statuses[switched_task["id"]], "completed")

    def test_start_can_optionally_select_an_initial_task(self):
        task = self.create_task("Initial task")
        started = self.client.post(
            "/api/v1/sessions/start",
            json={"task_id": task["id"]},
            headers=self.headers,
        )
        self.assertEqual(started.status_code, 200, started.text)
        self.assertEqual(started.json()["current_task_id"], task["id"])
        self.assertEqual(started.json()["tasks"][0]["id"], task["id"])

        ended = self.client.post(
            f"/api/v1/sessions/{started.json()['id']}/end",
            headers=self.headers,
        )
        self.assertEqual(ended.status_code, 200, ended.text)

    def test_teacher_progress_uses_session_owner(self):
        now = datetime.now()
        with TEST_SESSION_LOCAL() as db:
            teacher = UserDB(
                email="teacher@example.com",
                hashed_password="x",
                is_active=True,
                role="teacher",
            )
            student = UserDB(
                email="linked-student@example.com",
                hashed_password="x",
                is_active=True,
                role="student",
            )
            db.add_all([teacher, student])
            db.flush()
            db.add(
                TeacherStudentLinkDB(
                    teacher_id=teacher.id,
                    student_id=student.id,
                    instrument="Piano",
                )
            )
            task = TaskDB(
                title="Assigned task",
                status="open",
                user_id=student.id,
            )
            db.add(task)
            db.flush()
            db.add_all(
                [
                    SessionDB(
                        user_id=student.id,
                        task_id=task.id,
                        current_task_id=None,
                        timestamp=now - timedelta(minutes=30),
                        started_at=now - timedelta(minutes=30),
                        ended_at=now - timedelta(minutes=10),
                        duration=20,
                    ),
                    SessionDB(
                        user_id=student.id,
                        task_id=None,
                        current_task_id=None,
                        timestamp=now - timedelta(minutes=8),
                        started_at=now - timedelta(minutes=8),
                        ended_at=now - timedelta(minutes=1),
                        duration=7,
                    ),
                ]
            )
            db.commit()

            progress = SessionRepository(db).get_weekly_student_progress(teacher.id)

        self.assertEqual(len(progress), 1)
        self.assertEqual(progress[0].total_duration, 27)
        self.assertEqual(progress[0].session_count, 2)

    def test_teacher_progress_includes_assigned_student_with_no_current_week_sessions(self):
        now = datetime.now()
        with TEST_SESSION_LOCAL() as db:
            teacher = UserDB(
                email="teacher-no-current-week@example.com",
                hashed_password="x",
                is_active=True,
                role="teacher",
            )
            student = UserDB(
                email="student-no-current-week@example.com",
                hashed_password="x",
                is_active=True,
                role="student",
            )
            db.add_all([teacher, student])
            db.flush()
            db.add(
                TeacherStudentLinkDB(
                    teacher_id=teacher.id,
                    student_id=student.id,
                    instrument="Piano",
                )
            )
            task = TaskDB(
                title="Older task",
                status="open",
                user_id=student.id,
            )
            db.add(task)
            db.flush()
            old_start = now - timedelta(days=14)
            db.add(
                SessionDB(
                    user_id=student.id,
                    task_id=task.id,
                    current_task_id=None,
                    timestamp=old_start,
                    started_at=old_start,
                    ended_at=old_start + timedelta(minutes=15),
                    duration=15,
                )
            )
            student_id = student.id
            db.commit()

            progress = SessionRepository(db).get_weekly_student_progress(
                teacher.id
            )

        self.assertEqual(len(progress), 1)
        self.assertEqual(progress[0].student_id, student_id)
        self.assertEqual(progress[0].total_duration, 0)
        self.assertEqual(progress[0].session_count, 0)

    def test_students_cannot_use_or_update_another_students_task(self):
        other_headers, _ = self.register_and_login(
            "other-student@example.com"
        )
        other_task = self.client.post(
            "/api/v1/tasks",
            json={"title": "Other student's task", "description": None},
            headers=other_headers,
        )
        self.assertEqual(other_task.status_code, 200, other_task.text)

        started = self.client.post(
            "/api/v1/sessions/start",
            headers=self.headers,
        )
        self.assertEqual(started.status_code, 200, started.text)
        session_id = started.json()["id"]

        attach = self.client.post(
            f"/api/v1/sessions/{session_id}/current-task",
            json={"task_id": other_task.json()["id"]},
            headers=self.headers,
        )
        self.assertEqual(attach.status_code, 404, attach.text)

        update = self.client.patch(
            f"/api/v1/tasks/{other_task.json()['id']}/status",
            json={"status": "completed"},
            headers=self.headers,
        )
        self.assertEqual(update.status_code, 404, update.text)

        other_tasks = self.client.get(
            "/api/v1/tasks", headers=other_headers
        )
        self.assertEqual(other_tasks.status_code, 200, other_tasks.text)
        self.assertEqual(other_tasks.json()[0]["status"], "open")

        self.client.post(
            f"/api/v1/sessions/{session_id}/end",
            headers=self.headers,
        )

    def test_teacher_access_requires_existing_link_and_preserves_assignment_link(self):
        teacher_register = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "teacher-access@example.com",
                "password": "test-password",
            },
        )
        self.assertEqual(teacher_register.status_code, 201, teacher_register.text)
        teacher_id = teacher_register.json()["id"]
        student_id = self.client.get(
            "/api/v1/auth/me", headers=self.headers
        ).json()["id"]
        with TEST_SESSION_LOCAL() as db:
            db.get(UserDB, teacher_id).role = "teacher"
            link = TeacherStudentLinkDB(
                teacher_id=teacher_id,
                student_id=student_id,
                instrument="Piano",
            )
            db.add(link)
            db.flush()
            link_id = link.id
            db.commit()

        teacher_login = self.client.post(
            "/api/v1/auth/login",
            data={
                "username": "teacher-access@example.com",
                "password": "test-password",
            },
        )
        self.assertEqual(teacher_login.status_code, 200, teacher_login.text)
        teacher_headers = {
            "Authorization": f"Bearer {teacher_login.json()['access_token']}"
        }
        assigned = self.client.post(
            f"/api/v1/teacher/students/{student_id}/tasks",
            json={"title": "Teacher assignment", "description": None},
            headers=teacher_headers,
        )
        self.assertEqual(assigned.status_code, 200, assigned.text)
        self.assertEqual(assigned.json()["teacher_student_link_id"], link_id)

        linked_sessions = self.client.get(
            f"/api/v1/teacher/students/{student_id}/sessions",
            headers=teacher_headers,
        )
        self.assertEqual(linked_sessions.status_code, 200, linked_sessions.text)

        other_headers, other_user = self.register_and_login(
            "unassigned-student@example.com"
        )
        other_started = self.client.post(
            "/api/v1/sessions/start",
            headers=other_headers,
        )
        self.assertEqual(other_started.status_code, 200, other_started.text)
        other_session_id = other_started.json()["id"]

        restricted_sessions = self.client.get(
            f"/api/v1/teacher/students/{other_user['id']}/sessions",
            headers=teacher_headers,
        )
        self.assertEqual(restricted_sessions.status_code, 403, restricted_sessions.text)

        with TEST_SESSION_LOCAL() as db:
            session = db.get(SessionDB, other_session_id)
            session.duration = 9
            session.ended_at = datetime.now()
            db.commit()

        progress = self.client.get(
            "/api/v1/teacher/progress/weekly",
            headers=teacher_headers,
        )
        self.assertEqual(progress.status_code, 200, progress.text)
        self.assertEqual(
            {row["student_id"] for row in progress.json()},
            {student_id},
        )


class MigrationTests(unittest.TestCase):
    def test_legacy_sessions_are_backfilled_and_migration_is_repeatable(self):
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR NOT NULL, "
                "hashed_password VARCHAR NOT NULL, is_active BOOLEAN NOT NULL, role VARCHAR NOT NULL)"
            )
            connection.exec_driver_sql(
                "CREATE TABLE teacher_student_links (id INTEGER PRIMARY KEY, teacher_id INTEGER NOT NULL, "
                "student_id INTEGER NOT NULL, instrument VARCHAR NOT NULL)"
            )
            connection.exec_driver_sql(
                "CREATE TABLE tasks (id INTEGER PRIMARY KEY, title VARCHAR NOT NULL, "
                "description VARCHAR, status VARCHAR NOT NULL, user_id INTEGER, teacher_student_link_id INTEGER)"
            )
            connection.exec_driver_sql(
                "CREATE TABLE sessions (id INTEGER PRIMARY KEY, duration INTEGER NOT NULL, "
                "notes VARCHAR, timestamp DATETIME NOT NULL, task_id INTEGER NOT NULL)"
            )
            connection.execute(
                text("INSERT INTO users VALUES (1, 'student@example.com', 'x', 1, 'student')")
            )
            connection.execute(
                text("INSERT INTO tasks VALUES (10, 'Active', NULL, 'in progress', 1, NULL)")
            )
            connection.execute(
                text("INSERT INTO tasks VALUES (12, 'Pending', NULL, 'pending', 1, NULL)")
            )
            connection.execute(
                text("INSERT INTO tasks VALUES (11, 'Completed', NULL, 'completed', 1, NULL)")
            )
            connection.execute(
                text(
                    "INSERT INTO sessions VALUES (20, 0, NULL, '2026-08-14 10:00:00', 10)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO sessions VALUES (21, 12, 'old', '2026-08-13 10:00:00', 11)"
                )
            )

        initialize_database(engine)
        initialize_database(engine)

        session_columns = {
            column["name"]: column["nullable"]
            for column in inspect(engine).get_columns("sessions")
        }
        self.assertTrue(session_columns["task_id"])

        with Session(engine) as db:
            active = db.get(SessionDB, 20)
            completed = db.get(SessionDB, 21)
            links = db.query(SessionTaskDB).order_by(SessionTaskDB.session_id).all()
            self.assertEqual(db.get(TaskDB, 10).status, "open")
            self.assertEqual(db.get(TaskDB, 12).status, "open")
            self.assertEqual(active.user_id, 1)
            self.assertEqual(active.current_task_id, 10)
            self.assertIsNone(active.ended_at)
            self.assertEqual(completed.user_id, 1)
            self.assertIsNotNone(completed.ended_at)
            self.assertEqual(
                [(link.session_id, link.task_id) for link in links],
                [(20, 10), (21, 11)],
            )

        engine.dispose()

    def test_postgresql_backfill_uses_interval_and_conflict_safe_insert(self):
        connection = Mock()
        connection.dialect.name = "postgresql"

        from db.migrations import _backfill_data

        _backfill_data(connection)

        statements = [
            call.args[0].text
            for call in connection.execute.call_args_list
        ]
        self.assertTrue(
            any("INTERVAL '1 minute'" in statement for statement in statements)
        )
        self.assertTrue(
            any(
                "ON CONFLICT (session_id, task_id) DO NOTHING" in statement
                for statement in statements
            )
        )
        self.assertFalse(
            any("INSERT OR IGNORE" in statement for statement in statements)
        )


if __name__ == "__main__":
    unittest.main()
