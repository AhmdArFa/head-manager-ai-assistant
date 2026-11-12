from dataclasses import dataclass
from contextlib import closing
import re
import sqlite3
from typing import Any

from app.db import connect_read_only


@dataclass(frozen=True)
class QuerySpec:
    query_id: str
    table: str
    sql: str


QUERY_CATALOG = {
    "employee_count": QuerySpec(
        "employee_count", "employees", "SELECT COUNT(*) AS employee_count FROM employees"
    ),
    "employee_directory": QuerySpec(
        "employee_directory",
        "employees",
        "SELECT id, name, department, title FROM employees ORDER BY department, name LIMIT 100",
    ),
    "department_employees": QuerySpec(
        "department_employees",
        "employees",
        "SELECT id, name, department, title FROM employees WHERE department = ? ORDER BY name LIMIT 100",
    ),
    "project_status": QuerySpec(
        "project_status",
        "projects",
        "SELECT id, name, status, owner_department FROM projects ORDER BY id LIMIT 100",
    ),
    "open_tasks": QuerySpec(
        "open_tasks",
        "tasks",
        "SELECT id, title, status, project_id, assigned_to FROM tasks WHERE status IN ('open', 'in_progress') ORDER BY id LIMIT 100",
    ),
}

DEPARTMENTS = {
    "engineering": "Engineering",
    "operations": "Operations",
    "sales": "Sales",
    "finance": "Finance",
}

EMPLOYEE_TERMS = ("employee", "employees", "staff", "people", "team", "موظف", "موظفين", "العاملين", "فريق")
COUNT_TERMS = ("how many", "number of", "count", "headcount", "عدد", "كام")
PROJECT_TERMS = ("project", "projects", "مشروع", "المشاريع", "المشروع")
TASK_TERMS = ("task", "tasks", "مهام", "المهام")


@dataclass
class DataResult:
    intent: str
    answer: str
    data: list[dict[str, Any]]
    source: dict[str, Any] | None


class DataAgent:
    """Executes only fixed, reviewed queries against a read-only database connection."""

    def __init__(self, database_path: str):
        self.database_path = database_path

    def answer_question(self, question: str) -> DataResult:
        intent, parameter = self._route(question)
        if intent == "unsupported":
            return DataResult(
                intent=intent,
                answer=(
                    "مش قادر أجاوب على السؤال ده من البيانات المتاحة عندي. "
                    "جرّب تسأل عن عدد الموظفين أو الأقسام، حالة المشاريع، أو المهام المفتوحة."
                ),
                data=[],
                source=None,
            )

        spec = QUERY_CATALOG[intent]
        self._validate_catalog_query(spec.sql)
        with closing(connect_read_only(self.database_path)) as connection:
            if parameter is None:
                rows = connection.execute(spec.sql).fetchall()
            else:
                rows = connection.execute(spec.sql, (parameter,)).fetchall()
        data = [dict(row) for row in rows]
        return DataResult(
            intent=intent,
            answer=self._format_answer(intent, data, parameter),
            data=data,
            source={"table": spec.table, "query_id": spec.query_id, "row_count": len(data)},
        )

    @staticmethod
    def _route(question: str) -> tuple[str, str | None]:
        text = question.casefold()
        if any(term in text for term in TASK_TERMS):
            return "open_tasks", None
        if any(term in text for term in PROJECT_TERMS):
            return "project_status", None

        department = next(
            (name for key, name in DEPARTMENTS.items() if re.search(rf"\b{re.escape(key)}\b", text)),
            None,
        )
        has_employee_term = any(term in text for term in EMPLOYEE_TERMS)
        if department and (has_employee_term or any(term in text for term in COUNT_TERMS) or "who" in text or "مين" in text):
            return "department_employees", department
        if has_employee_term and any(term in text for term in COUNT_TERMS):
            return "employee_count", None
        if has_employee_term:
            return "employee_directory", None
        return "unsupported", None

    @staticmethod
    def _validate_catalog_query(sql: str) -> None:
        # Defense in depth: the catalog is internal and user input is always a bound parameter.
        normalized = sql.strip().casefold()
        if not normalized.startswith("select ") or ";" in normalized or any(
            blocked in normalized for blocked in (" insert ", " update ", " delete ", " drop ", " pragma ", " attach ")
        ):
            raise ValueError("Only a single reviewed SELECT query is allowed")

    @staticmethod
    def _format_answer(intent: str, rows: list[dict[str, Any]], parameter: str | None) -> str:
        if intent == "employee_count":
            count = rows[0]["employee_count"]
            return f"البيانات المسجلة عندي فيها {count} موظف."
        if intent in ("employee_directory", "department_employees"):
            if not rows:
                return f"ملقتش موظفين في قسم {parameter}." if parameter else "ملقتش أي موظفين في البيانات."
            names = ", ".join(f"{row['name']} ({row['title']}, {row['department']})" for row in rows)
            if intent == "department_employees":
                return f"لقيت {len(rows)} موظف في قسم {parameter}: {names}."
            return f"دي بيانات {len(rows)} موظف لقيتهم: {names}."
        if intent == "project_status":
            if not rows:
                return "ملقتش أي مشاريع مسجلة في قاعدة البيانات."
            statuses = "; ".join(f"{row['name']}: {row['status']}" for row in rows)
            return f"لقيت {len(rows)} مشروع. حالتهم: {statuses}."
        if intent == "open_tasks":
            if not rows:
                return "مفيش مهام مفتوحة أو لسه شغالة في قاعدة البيانات."
            tasks = "; ".join(f"{row['title']} ({row['status']})" for row in rows)
            return f"لقيت {len(rows)} مهمة مفتوحة أو لسه شغالة: {tasks}."
        return "مش متاح عندي إجابة للسؤال ده."
