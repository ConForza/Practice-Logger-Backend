import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

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
from main import app
from repositories.session_repository import SessionRepository


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

    def test_multitask_session_and_explicit_task_lifecycle(self):
        scales = self.create_task("Scales")
        sonata = self.create_task("Sonata")

        started = self.client.post(
            "/api/v1/sessions/start",
            headers=self.headers,
        )
        self.assertEqual(started.status_code, 200, started.text)
        session_id = started.json()["id"]
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
            old_start = datetime.now() - timedelta(minutes=2)
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


if __name__ == "__main__":
    unittest.main()
