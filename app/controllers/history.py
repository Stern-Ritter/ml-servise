from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional

from database import get_session
from services.finance_service import FinanceService
from services.predict_service import PredictService, PatientService
from models.finance import TransactionFilter
from models.predict import PredictTaskFilter
from models.enums import TransactionType, Currency, PredictStatus
from exceptions import (
    NotFoundException
)
from datetime import datetime

router = APIRouter()


def get_finance_service(db: Session = Depends(get_session)):
    return FinanceService(db)


def get_predict_service(db: Session = Depends(get_session)):
    patient_service = PatientService(db)
    return PredictService(db, patient_service)


@router.get(
    "/transactions/{user_id}",
    summary="Get Comprehensive Transaction History",
    description="Retrieve user's complete transaction history with advanced filtering",
    response_description="List of transactions matching the filter criteria",
    responses={
        200: {"description": "Transaction history retrieved successfully"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_transaction_history(
    user_id: int,
    transaction_type: Optional[TransactionType] = Query(
        None, description="Filter by transaction type (DEPOSIT/WITHDRAWAL)"),
    currency: Optional[Currency] = Query(
        None, description="Filter by currency code"),
    min_amount: Optional[float] = Query(
        None, ge=0, description="Minimum transaction amount"),
    max_amount: Optional[float] = Query(
        None, ge=0, description="Maximum transaction amount"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for transaction filtering"),
    end_date: Optional[datetime] = Query(
        None, description="End date for transaction filtering"),
    description: Optional[str] = Query(
        None, description="Search in transaction description (case-insensitive)"),
    limit: int = Query(
        100, le=1000, description="Maximum number of transactions to return (1-1000)"),
    offset: int = Query(
        0, ge=0, description="Number of transactions to skip for pagination"),
    finance_service: FinanceService = Depends(get_finance_service)
) -> List[Dict]:
    """
    Получение полной истории транзакций пользователя.

    Предоставляет доступ к полной истории финансовых операций пользователя
    с расширенными возможностями фильтрации. Поддерживает пагинацию для
    работы с большими объемами данных.

    Args:
        user_id: Идентификатор пользователя
        transaction_type: Тип транзакции для фильтрации
        currency: Валюта транзакции для фильтрации
        min_amount: Минимальная сумма для фильтрации
        max_amount: Максимальная сумма для фильтрации
        start_date: Начальная дата диапазона фильтрации
        end_date: Конечная дата диапазона фильтрации
        description: Текст для поиска в описании транзакций
        limit: Ограничение количества возвращаемых записей
        offset: Смещение для пагинации

    Returns:
        List[Dict] с детальной информацией о транзакциях

    Raises:
        HTTPException 404: Если пользователь не найден
        HTTPException 500: При внутренних ошибках сервера
    """
    try:
        filters = TransactionFilter(
            type=transaction_type,
            currency=currency,
            min_amount=min_amount,
            max_amount=max_amount,
            start_date=start_date,
            end_date=end_date,
            description=description
        )

        transactions = finance_service.get_user_transactions(
            user_id, filters, limit, offset
        )

        return [
            {
                "id": str(t.id),
                "type": t.type.value,
                "amount": t.amount,
                "currency": t.currency.value,
                "description": t.description,
                "created_at": t.created_at,
                "user_id": t.user_id
            }
            for t in transactions
        ]
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/predicts/{user_id}",
    summary="Get ML Prediction History",
    description="Retrieve user's complete history of ML prediction requests",
    response_description="List of prediction tasks matching the filter criteria",
    responses={
        200: {"description": "Prediction history retrieved successfully"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_predict_history(
    user_id: int,
    status: Optional[PredictStatus] = Query(
        None, description="Filter by prediction task status"),
    min_cost: Optional[float] = Query(
        None, ge=0, description="Minimum cost of prediction"),
    max_cost: Optional[float] = Query(
        None, ge=0, description="Maximum cost of prediction"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for task creation filter"),
    end_date: Optional[datetime] = Query(
        None, description="End date for task creation filter"),
    limit: int = Query(
        100, le=1000, description="Maximum number of tasks to return (1-1000)"),
    offset: int = Query(
        0, ge=0, description="Number of tasks to skip for pagination"),
    predict_service: PredictService = Depends(get_predict_service)
) -> List[Dict]:
    """
    Получение полной истории ML-запросов пользователя.

    Предоставляет доступ ко всем задачам предсказания, инициированным пользователем,
    с возможностью фильтрации по статусу, стоимости и дате создания.
    Включает результаты предсказаний для завершенных задач.

    Args:
        user_id: Идентификатор пользователя
        status: Статус задачи для фильтрации
        min_cost: Минимальная стоимость для фильтрации
        max_cost: Максимальная стоимость для фильтрации
        start_date: Начальная дата диапазона фильтрации
        end_date: Конечная дата диапазона фильтрации
        limit: Ограничение количества возвращаемых записей
        offset: Смещение для пагинации

    Returns:
        List[Dict] с детальной информацией о задачах предсказания

    Raises:
        HTTPException 404: Если пользователь не найден
        HTTPException 500: При внутренних ошибках сервера
    """
    try:
        filters = PredictTaskFilter(
            status=status,
            min_cost=min_cost,
            max_cost=max_cost,
            start_date=start_date,
            end_date=end_date
        )

        tasks = predict_service.get_user_predict_tasks(
            user_id, filters, limit, offset
        )

        result = []
        for task in tasks:
            task_dict = {
                "task_id": str(task.id),
                "status": task.status.value,
                "cost": task.cost,
                "created_at": task.created_at,
                "user_id": task.user_id,
                "patient_id": task.patient_id
            }

            if task.predict:
                task_dict.update({
                    "prediction": task.predict.prediction,
                    "probability": task.predict.probability
                })

            result.append(task_dict)

        return result
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
