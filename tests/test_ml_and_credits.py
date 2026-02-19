import pytest
import requests

from conftest import (
    api_url,
    valid_patient_payload,
    wait_for_task_completion,
)


class TestMLSuccessAndCreditDeduction:
    """Успешный ML-запрос и списание кредитов."""

    def test_full_ml_flow_and_balance_deduction(self, authenticated_user):
        headers = authenticated_user["headers"]
        user_id = authenticated_user["user"]["user_id"]

        # Пополняем баланс
        dep = requests.post(
            api_url("/balance/deposit"),
            headers=headers,
            json={"user_id": user_id, "amount": 500, "currency": "RUB"},
            timeout=10,
        )
        assert dep.status_code == 200
        balance_after_deposit = dep.json()["new_balance"]

        # Создаём пациента
        pc = requests.post(
            api_url("/predict/patient"),
            headers=headers,
            json=valid_patient_payload(),
            timeout=10,
        )
        assert pc.status_code == 201
        patient_id = int(pc.json()["patient_id"])

        # Создаём задачу
        tc = requests.post(
            api_url("/predict/task"),
            headers=headers,
            json={"patient_id": patient_id, "user_id": user_id},
            timeout=10,
        )
        assert tc.status_code == 201
        task_id = int(tc.json()["task_id"])

        # Запускаем обработку
        pr = requests.post(
            api_url(f"/predict/task/{task_id}/process"),
            headers=headers,
            timeout=10,
        )
        assert pr.status_code == 200

        # Ждём завершения
        task = wait_for_task_completion(task_id, headers)
        assert task["status"] in ("completed", "failed")

        # Проверяем списание: баланс должен уменьшиться на стоимость (100)
        bal = requests.get(
            api_url(f"/balance/{user_id}"), headers=headers, timeout=10)
        assert bal.status_code == 200
        new_balance = bal.json()["value"]
        if task["status"] == "completed":
            assert new_balance == balance_after_deposit - 100
            assert "prediction" in task
            assert "probability" in task
        else:
            assert new_balance == balance_after_deposit


class TestInsufficientBalance:
    """Запрет списания при недостаточном балансе."""

    def test_process_task_with_zero_balance_returns_400(self, authenticated_user):
        headers = authenticated_user["headers"]
        user_id = authenticated_user["user"]["user_id"]
        # Баланс новый пользователя = 0

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

        pr = requests.post(
            api_url(f"/predict/task/{task_id}/process"),
            headers=headers,
            timeout=10,
        )
        assert pr.status_code == 400
        assert "insufficient" in pr.text.lower(
        ) or "balance" in pr.text.lower() or "funds" in pr.text.lower()


class TestInvalidPatientData:
    """Обработка некорректных входных данных."""

    def test_create_patient_invalid_gender_returns_400(self, authenticated_user):
        headers = authenticated_user["headers"]
        payload = valid_patient_payload()
        payload["gender"] = "invalid_gender"
        r = requests.post(
            api_url("/predict/patient"),
            headers=headers,
            json=payload,
            timeout=10,
        )
        assert r.status_code == 422
