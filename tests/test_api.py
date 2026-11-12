from contextlib import closing
import sqlite3

from fastapi.testclient import TestClient
import pytest

from app.db import connect_read_only, initialize_database
from app.main import create_app


def client_for(tmp_path):
    app = create_app(tmp_path / "test_company.db")
    return TestClient(app)


def test_health_is_healthy(tmp_path):
    with client_for(tmp_path) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_demo_page_is_served_by_the_api_app(tmp_path):
    with client_for(tmp_path) as client:
        response = client.get("/demo/")
    assert response.status_code == 200
    assert "GROUNDED COMPANY Q&amp;A" in response.text


def test_employee_count_is_read_from_database(tmp_path):
    with client_for(tmp_path) as client:
        response = client.post("/api/v1/ask", json={"question": "How many employees do we have?"})
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "employee_count"
    assert body["data"] == [{"employee_count": 6}]
    assert body["sources"] == [{"table": "employees", "query_id": "employee_count", "row_count": 1}]
    assert "6 employees" in body["answer"]
    assert body["trace"][1]["component"] == "data_agent"


def test_department_question_routes_to_bound_parameter_query(tmp_path):
    with client_for(tmp_path) as client:
        response = client.post("/api/v1/ask", json={"question": "Who works in Engineering?"})
    body = response.json()
    assert response.status_code == 200
    assert body["intent"] == "department_employees"
    assert len(body["data"]) == 3
    assert {row["department"] for row in body["data"]} == {"Engineering"}


def test_arabic_open_tasks_question_is_supported(tmp_path):
    with client_for(tmp_path) as client:
        response = client.post("/api/v1/ask", json={"question": "ما هي المهام المفتوحة؟"})
    body = response.json()
    assert response.status_code == 200
    assert body["intent"] == "open_tasks"
    assert len(body["data"]) == 3


def test_unsupported_question_does_not_invent_data_or_query_database(tmp_path):
    with client_for(tmp_path) as client:
        response = client.post("/api/v1/ask", json={"question": "What is our customer churn rate?"})
    body = response.json()
    assert response.status_code == 200
    assert body["intent"] == "unsupported"
    assert body["data"] == []
    assert body["sources"] == []
    assert body["trace"][1]["status"] == "skipped"


def test_too_short_question_is_rejected(tmp_path):
    with client_for(tmp_path) as client:
        response = client.post("/api/v1/ask", json={"question": "?"})
    assert response.status_code == 422


def test_agent_database_connection_rejects_writes(tmp_path):
    database_path = tmp_path / "read_only.db"
    initialize_database(database_path)
    with closing(connect_read_only(database_path)) as connection:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("DELETE FROM employees")
