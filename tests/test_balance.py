import pytest
import requests

from conftest import api_url


class TestBalance:
    """Получение и пополнение баланса."""

    def test_get_balance_returns_value_and_currency(self, authenticated_user):
        user_id = authenticated_user["user"]["user_id"]
        headers = authenticated_user["headers"]
        r = requests.get(
            api_url(f"/balance/{user_id}"), headers=headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "value" in data
        assert "currency" in data
        assert "user_id" in data
        assert data["user_id"] == user_id
        assert data["value"] >= 0

    def test_deposit_increases_balance(self, authenticated_user):
        user_id = authenticated_user["user"]["user_id"]
        headers = authenticated_user["headers"]
        get_before = requests.get(
            api_url(f"/balance/{user_id}"), headers=headers, timeout=10
        )
        assert get_before.status_code == 200
        value_before = get_before.json()["value"]

        deposit_amount = 500.0
        r = requests.post(
            api_url("/balance/deposit"),
            headers=headers,
            json={
                "user_id": user_id,
                "amount": deposit_amount,
                "currency": "RUB",
                "description": "E2E test deposit",
            },
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("new_balance") == value_before + deposit_amount

        get_after = requests.get(
            api_url(f"/balance/{user_id}"), headers=headers, timeout=10
        )
        assert get_after.status_code == 200
        assert get_after.json()["value"] == value_before + deposit_amount

    def test_get_balance_without_token_returns_401(self, created_user):
        r = requests.get(
            api_url(f"/balance/{created_user['user_id']}"),
            timeout=10,
        )
        assert r.status_code == 401
