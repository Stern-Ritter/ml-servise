import pytest
import requests

from conftest import api_url


class TestUserRegistration:
    """Создание нового пользователя."""

    def test_signup_returns_201_and_user_id(self, signup_payload):
        r = requests.post(api_url("/auth/signup"),
                          json=signup_payload, timeout=10)
        assert r.status_code == 201
        data = r.json()
        assert "user_id" in data
        assert "message" in data
        assert int(data["user_id"]) > 0

    def test_signup_duplicate_login_returns_409(self, signup_payload):
        requests.post(api_url("/auth/signup"), json=signup_payload, timeout=10)
        r = requests.post(api_url("/auth/signup"),
                          json=signup_payload, timeout=10)
        assert r.status_code == 409


class TestUserAuth:
    """Авторизация пользователя."""

    def test_signin_returns_token_and_user_id(self, created_user):
        r = requests.post(
            api_url("/auth/signin"),
            json={"login": created_user["login"],
                  "password": created_user["password"]},
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data.get("token_type") == "bearer"
        assert data.get("user_id") == str(created_user["user_id"])
        assert "login" in data

    def test_repeated_signin_returns_new_token(self, created_user):
        r1 = requests.post(
            api_url("/auth/signin"),
            json={"login": created_user["login"],
                  "password": created_user["password"]},
            timeout=10,
        )
        r2 = requests.post(
            api_url("/auth/signin"),
            json={"login": created_user["login"],
                  "password": created_user["password"]},
            timeout=10,
        )
        assert r1.status_code == 200 and r2.status_code == 200
        t1 = r1.json().get("access_token")
        t2 = r2.json().get("access_token")
        assert t1 and t2
        for token in (t1, t2):
            me = requests.get(
                api_url("/auth/me"),
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            assert me.status_code == 200
            assert me.json().get("id") == created_user["user_id"]


class TestAuthErrors:
    """Обработка ошибок при неверных данных."""

    def test_signin_wrong_password_returns_401(self, created_user):
        r = requests.post(
            api_url("/auth/signin"),
            json={"login": created_user["login"], "password": "WrongPassword"},
            timeout=10,
        )
        assert r.status_code == 401

    def test_signin_nonexistent_login_returns_404(self):
        r = requests.post(
            api_url("/auth/signin"),
            json={"login": "nonexistent_user_xyz", "password": "any"},
            timeout=10,
        )
        assert r.status_code == 404

    def test_signup_invalid_email_returns_422(self, unique_login):
        r = requests.post(
            api_url("/auth/signup"),
            json={
                "login": unique_login,
                "email": "not-an-email",
                "display_name": "Test",
                "password": "pass123",
            },
            timeout=10,
        )
        assert r.status_code == 422
