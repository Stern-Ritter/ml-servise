import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ.get("BASE_URL", "http://localhost").rstrip("/")
API_PREFIX = os.environ.get("API_PREFIX", "/api/1.0").rstrip("/")


def api_url(path: str) -> str:
    path = path if path.startswith("/") else f"/{path}"
    return f"{BASE_URL}{API_PREFIX}{path}"


@pytest.fixture(scope="module")
def api_base():
    """Базовый URL API."""
    return api_url("")


@pytest.fixture
def unique_login():
    """Уникальный логин для изоляции тестов."""
    return f"user_{uuid.uuid4().hex[:12]}"


@pytest.fixture
def unique_email(unique_login):
    return f"{unique_login}@test.example.com"


@pytest.fixture
def user_password():
    return "top_secret"


@pytest.fixture
def signup_payload(unique_login, unique_email, user_password):
    return {
        "login": unique_login,
        "email": unique_email,
        "display_name": f"Test {unique_login}",
        "password": user_password,
    }


@pytest.fixture
def created_user(signup_payload):
    """Создаёт пользователя через API, возвращает (user_id, login, password, email)."""
    r = requests.post(api_url("/auth/signup"), json=signup_payload, timeout=10)
    assert r.status_code == 201, (r.status_code, r.text)
    data = r.json()
    user_id = data["user_id"]
    return {
        "user_id": int(user_id),
        "login": signup_payload["login"],
        "password": signup_payload["password"],
        "email": signup_payload["email"],
        "display_name": signup_payload["display_name"],
    }


@pytest.fixture
def auth_headers(created_user):
    """Авторизация и заголовки с JWT для запросов."""
    r = requests.post(
        api_url("/auth/signin"),
        json={"login": created_user["login"],
              "password": created_user["password"]},
        timeout=10,
    )
    assert r.status_code == 200, (r.status_code, r.text)
    data = r.json()
    token = data.get("access_token")
    assert token, data
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture
def authenticated_user(created_user, auth_headers):
    """Пользователь + заголовки с JWT."""
    return {"user": created_user, "headers": auth_headers}


def wait_for_task_completion(task_id: int, headers: dict, max_wait: float = 60.0):
    """Ожидание завершения задачи (completed или failed)."""
    url = api_url(f"/predict/task/{task_id}")
    start = time.monotonic()
    while time.monotonic() - start < max_wait:
        r = requests.get(url, headers=headers, timeout=10)
        assert r.status_code == 200, (r.status_code, r.text)
        data = r.json()
        if data.get("status") in ("completed", "failed"):
            return data
        time.sleep(1.0)
    raise TimeoutError(f"Task {task_id} did not complete in {max_wait}s")


def valid_patient_payload():
    """Корректные данные одного пациента для ML."""
    return {
        "age": 45,
        "gender": "male",
        "physical_activity_days_per_week": 3,
        "stress_level": 5,
        "bmi": 24.5,
        "exercise_hours_per_week": 2.5,
        "sedentary_hours_per_day": 8.0,
        "sleep_hours_per_day": 7.0,
        "heart_rate": 72.0,
        "cholesterol": 180.0,
        "blood_sugar": 90.0,
        "triglycerides": 140.0,
        "smoking": False,
        "alcohol_consumption": False,
        "diabetes": False,
        "obesity": False,
        "family_history": True,
    }
