import pytest
import requests

from conftest import api_url, valid_patient_payload, wait_for_task_completion


class TestTransactionHistory:
    """История транзакций."""

    def test_transaction_history_after_deposit(self, authenticated_user):
        user_id = authenticated_user["user"]["user_id"]
        headers = authenticated_user["headers"]

        requests.post(
            api_url("/balance/deposit"),
            headers=headers,
            json={
                "user_id": user_id,
                "amount": 100,
                "currency": "RUB",
                "description": "History test",
            },
            timeout=10,
        )

        r = requests.get(
            api_url(f"/history/transactions/{user_id}"),
            headers=headers,
            params={"limit": 50},
            timeout=10,
        )
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        deposit_entries = [t for t in items if t.get("type") == "deposit"]
        assert len(deposit_entries) >= 1
        last = deposit_entries[0]
        assert "amount" in last
        assert "currency" in last
        assert "created_at" in last
        assert last["amount"] == 100


class TestPredictHistory:
    """История ML-запросов и корректное отображение."""

    def test_predict_history_after_ml_request(self, authenticated_user):
        user_id = authenticated_user["user"]["user_id"]
        headers = authenticated_user["headers"]

        # Пополнение и один ML-запрос
        requests.post(
            api_url("/balance/deposit"),
            headers=headers,
            json={"user_id": user_id, "amount": 200, "currency": "RUB"},
            timeout=10,
        )
        pc = requests.post(
            api_url("/predict/patient"),
            headers=headers,
            json=valid_patient_payload(),
            timeout=10,
        )
        assert pc.status_code == 201
        patient_id = int(pc.json()["patient_id"])
        tc = requests.post(
            api_url("/predict/task"),
            headers=headers,
            json={"patient_id": patient_id, "user_id": user_id},
            timeout=10,
        )
        assert tc.status_code == 201
        task_id = int(tc.json()["task_id"])
        requests.post(
            api_url(f"/predict/task/{task_id}/process"),
            headers=headers,
            timeout=10,
        )
        wait_for_task_completion(task_id, headers)

        r = requests.get(
            api_url(f"/history/predicts/{user_id}"),
            headers=headers,
            params={"limit": 50},
            timeout=10,
        )
        assert r.status_code == 200
        tasks = r.json()
        assert isinstance(tasks, list)
        our = [t for t in tasks if str(t.get("task_id")) == str(task_id)]
        assert len(our) == 1
        t = our[0]
        assert "status" in t
        assert "cost" in t
        assert "created_at" in t
        assert t["status"] in ("completed", "failed", "processing", "pending")

    def test_history_contains_date_type_amount_status(self, authenticated_user):
        user_id = authenticated_user["user"]["user_id"]
        headers = authenticated_user["headers"]

        r_tx = requests.get(
            api_url(f"/history/transactions/{user_id}"),
            headers=headers,
            timeout=10,
        )
        r_pr = requests.get(
            api_url(f"/history/predicts/{user_id}"),
            headers=headers,
            timeout=10,
        )
        assert r_tx.status_code == 200 and r_pr.status_code == 200

        for t in r_tx.json():
            assert "created_at" in t
            assert "type" in t
            assert "amount" in t
        for p in r_pr.json():
            assert "created_at" in p
            assert "status" in p
            assert "cost" in p
