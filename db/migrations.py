from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from db.database import Base
from db.models import SessionDB, SessionTaskDB


def _table_exists(connection, table_name: str) -> bool:
    return table_name in inspect(connection).get_table_names()


def _column_names(connection, table_name: str) -> set[str]:
    return {
        column["name"]
        for column in inspect(connection).get_columns(table_name)
    }


def _add_column(connection, table_name: str, column_name: str, definition: str):
    connection.execute(
        text(
            f'ALTER TABLE "{table_name}" '
            f'ADD COLUMN "{column_name}" {definition}'
        )
    )


def _rebuild_sqlite_sessions_table(connection):
    """Make the legacy task_id column nullable without losing session history."""
    if not _table_exists(connection, "sessions"):
        return

    columns = inspect(connection).get_columns("sessions")
    task_id_column = next(
        column for column in columns if column["name"] == "task_id"
    )
    if not task_id_column["nullable"]:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        session_task_rows = []
        if _table_exists(connection, "session_tasks"):
            session_task_rows = connection.execute(
                text("SELECT id, session_id, task_id FROM session_tasks")
            ).mappings().all()
            connection.execute(text("DROP TABLE session_tasks"))

        connection.execute(text("ALTER TABLE sessions RENAME TO sessions_legacy"))
        SessionDB.__table__.create(connection, checkfirst=False)
        connection.execute(
            text(
                """
                INSERT INTO sessions (id, duration, notes, timestamp, task_id)
                SELECT id, duration, notes, timestamp, task_id
                FROM sessions_legacy
                """
            )
        )
        connection.execute(text("DROP TABLE sessions_legacy"))

        SessionTaskDB.__table__.create(connection, checkfirst=False)
        for row in session_task_rows:
            connection.execute(
                text(
                    """
                    INSERT OR IGNORE INTO session_tasks (id, session_id, task_id)
                    VALUES (:id, :session_id, :task_id)
                    """
                ),
                row,
            )
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


def _add_missing_columns(connection):
    dialect = connection.dialect.name
    datetime_type = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"

    task_columns = _column_names(connection, "tasks")
    if "completed_at" not in task_columns:
        _add_column(connection, "tasks", "completed_at", datetime_type)

    session_columns = _column_names(connection, "sessions")
    missing_columns = {
        "user_id": "INTEGER",
        "started_at": datetime_type,
        "ended_at": datetime_type,
        "current_task_id": "INTEGER",
    }
    for column_name, definition in missing_columns.items():
        if column_name not in session_columns:
            _add_column(connection, "sessions", column_name, definition)

    if dialect == "postgresql":
        task_id_column = next(
            column
            for column in inspect(connection).get_columns("sessions")
            if column["name"] == "task_id"
        )
        if not task_id_column["nullable"]:
            connection.execute(
                text("ALTER TABLE sessions ALTER COLUMN task_id DROP NOT NULL")
            )


def _backfill_data(connection):
    dialect = connection.dialect.name

    connection.execute(
        text(
            """
            UPDATE tasks
            SET status = 'open'
            WHERE status IS NULL
               OR status IN ('pending', 'in progress', 'ongoing')
            """
        )
    )
    connection.execute(
        text(
            """
            UPDATE sessions
            SET started_at = timestamp
            WHERE started_at IS NULL
            """
        )
    )
    connection.execute(
        text(
            """
            UPDATE sessions
            SET user_id = (
                SELECT user_id
                FROM tasks
                WHERE tasks.id = sessions.task_id
            )
            WHERE user_id IS NULL
            """
        )
    )

    if dialect == "postgresql":
        connection.execute(
            text(
                """
                UPDATE sessions
                SET ended_at = started_at + (duration * INTERVAL '1 minute')
                WHERE ended_at IS NULL AND duration > 0
                """
            )
        )
    else:
        connection.execute(
            text(
                """
                UPDATE sessions
                SET ended_at = datetime(
                    started_at,
                    printf('+%d minutes', duration)
                )
                WHERE ended_at IS NULL AND duration > 0
                """
            )
        )

    connection.execute(
        text(
            """
            UPDATE sessions
            SET current_task_id = task_id
            WHERE current_task_id IS NULL
              AND ended_at IS NULL
              AND task_id IS NOT NULL
            """
        )
    )
    connection.execute(
        text(
            """
            UPDATE tasks
            SET completed_at = (
                SELECT MAX(ended_at)
                FROM sessions
                WHERE sessions.task_id = tasks.id
                  AND sessions.ended_at IS NOT NULL
            )
            WHERE tasks.status = 'completed'
              AND tasks.completed_at IS NULL
            """
        )
    )

    if dialect == "postgresql":
        connection.execute(
            text(
                """
                INSERT INTO session_tasks (session_id, task_id)
                SELECT id, task_id
                FROM sessions
                WHERE task_id IS NOT NULL
                ON CONFLICT (session_id, task_id) DO NOTHING
                """
            )
        )
    else:
        connection.execute(
            text(
                """
                INSERT OR IGNORE INTO session_tasks (session_id, task_id)
                SELECT id, task_id
                FROM sessions
                WHERE task_id IS NOT NULL
                """
            )
        )


def initialize_database(engine: Engine):
    """Create the current schema and safely upgrade the pre-migration schema."""
    with engine.begin() as connection:
        if engine.dialect.name == "sqlite":
            _rebuild_sqlite_sessions_table(connection)

        Base.metadata.create_all(bind=connection)
        _add_missing_columns(connection)
        _backfill_data(connection)
