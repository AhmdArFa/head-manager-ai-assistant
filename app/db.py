import os
import sqlite3
from pathlib import Path
from urllib.parse import quote


DEFAULT_DATABASE_PATH = Path("data/company_demo.db")


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
            # Synthetic records for local development only; replace via an approved integration.
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
    # URI mode=ro makes the request path read-only at the SQLite connection layer.
    uri = f"file:{quote(str(path), safe='/')}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=3)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection
