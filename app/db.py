import os
from pathlib import Path
import sqlite3
from typing import Any
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_PATH = Path("data/company_demo.db")


def is_mssql_configured() -> bool:
    db_type = os.getenv("DB_TYPE", "").lower()
    return db_type == "mssql" or bool(os.getenv("SQL_SERVER"))


def configured_database_path() -> Path:
    raw_path = os.getenv("DATABASE_PATH", str(DEFAULT_DATABASE_PATH))
    return Path(raw_path).expanduser()


def initialize_database(database_path: str | Path) -> None:
    path = Path(database_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                title TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                owner_department TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                project_id INTEGER REFERENCES projects(id),
                assigned_to INTEGER REFERENCES employees(id)
            );
            """
        )
        employee_count = connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        if employee_count == 0:
            connection.executemany(
                "INSERT INTO employees (id, name, department, title) VALUES (?, ?, ?, ?)",
                [
                    (1, "Nour Hassan", "Engineering", "Backend Engineer"),
                    (2, "Omar Adel", "Engineering", "Data Engineer"),
                    (3, "Mariam Fathy", "Operations", "Operations Lead"),
                    (4, "Salma Nabil", "Sales", "Account Manager"),
                    (5, "Karim Samir", "Finance", "Financial Analyst"),
                    (6, "Youssef Tarek", "Engineering", "Platform Engineer"),
                ],
            )
            connection.executemany(
                "INSERT INTO projects (id, name, status, owner_department) VALUES (?, ?, ?, ?)",
                [
                    (1, "Customer Portal", "in_progress", "Engineering"),
                    (2, "Data Quality Upgrade", "planned", "Engineering"),
                    (3, "Quarterly Reporting", "completed", "Finance"),
                ],
            )
            connection.executemany(
                "INSERT INTO tasks (id, title, status, project_id, assigned_to) VALUES (?, ?, ?, ?, ?)",
                [
                    (1, "Review API access controls", "open", 1, 1),
                    (2, "Validate migration checklist", "in_progress", 2, 2),
                    (3, "Publish monthly report", "completed", 3, 5),
                    (4, "Confirm customer feedback", "open", 1, 4),
                ],
            )


def connect_read_only(database_path: str | Path) -> sqlite3.Connection:
    path = Path(database_path).expanduser().resolve()
    uri = f"file:{quote(str(path), safe='/')}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=3)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def get_mssql_connection_string() -> str:
    server = os.getenv("SQL_SERVER", "")
    database = os.getenv("SQL_DATABASE", "")
    user = os.getenv("SQL_USER", "")
    password = os.getenv("SQL_PASSWORD", "")
    driver = os.getenv("SQL_DRIVER", "ODBC Driver 17 for SQL Server")
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
        f"Encrypt=no;"
        f"Connection Timeout=10;"
    )


def connect_mssql_read_only():
    import pyodbc
    conn_str = get_mssql_connection_string()
    return pyodbc.connect(conn_str)


class DatabaseBackend:
    """Unified read-only database client for SQLite and MS SQL Server."""

    def __init__(self, backend_type: str = "sqlite", database_path: str | Path | None = None):
        self.backend_type = backend_type
        self.database_path = Path(database_path) if database_path else None

    def execute_query(self, sql: str, params: tuple | list | None = None) -> list[dict[str, Any]]:
        if self.backend_type == "mssql":
            conn = connect_mssql_read_only()
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                cols = [c[0] for c in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(cols, row)) for row in rows]
            finally:
                conn.close()
        else:
            path = self.database_path or configured_database_path()
            with connect_read_only(path) as connection:
                if params:
                    rows = connection.execute(sql, params).fetchall()
                else:
                    rows = connection.execute(sql).fetchall()
                return [dict(row) for row in rows]
