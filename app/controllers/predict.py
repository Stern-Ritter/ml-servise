from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional

from database import get_session
from services.predict_service import PredictService, PatientService
from models.predict import PatientCreate, PatientUpdate, PredictTaskCreate, PredictTaskFilter
from models.user import User
from models.enums import PredictStatus
from exceptions import (
    NotFoundException,
    BadRequestException,
    InsufficientFundsException,
    ConflictException,
    InternalServerErrorException
)
from security import get_current_user

router = APIRouter()

DEFAULT_COST = 100


def get_predict_service(db: Session = Depends(get_session)):
    patient_service = PatientService(db)
    return PredictService(db, patient_service)


def get_patient_service(db: Session = Depends(get_session)):
    return PatientService(db)


@router.post(
    "/patient",
    status_code=status.HTTP_201_CREATED,
    summary="Create Patient",
    description="Create a new patient record for medical predictions",
    response_description="Confirmation of patient creation with patient ID",
    responses={
        201: {"description": "Patient created successfully"},
        400: {"description": "Invalid patient data"},
        500: {"description": "Internal server error"}
    }
)
async def create_patient(
    patient_data: PatientCreate,
    patient_service: PatientService = Depends(get_patient_service)
) -> Dict:
    """
    Создание записи пациента для медицинских предсказаний.

    Создает новую запись пациента с медицинскими данными, которые будут
    использоваться для ML-предсказаний. Все поля должны быть валидными
    и соответствовать медицинским стандартам.

    Args:
        patient_data: Медицинские данные пациента, включая:
            - age: Возраст пациента (должен быть положительным числом)
            - gender: Пол пациента (MALE/FEMALE)
            - bmi: Индекс массы тела
            - physical_activity_days_per_week: Количество дней физической активности в неделю
            - stress_level: Уровень стресса (от 1 до 10)

    Returns:
        Dict с сообщением об успехе и ID созданного пациента

    Raises:
        HTTPException 400: Если данные пациента некорректны
        HTTPException 500: При внутренних ошибках сервера
    """
    try:
        patient = patient_service.create_patient(patient_data)
        return {
            "message": "Patient created successfully",
            "patient_id": str(patient.id)
        }
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/patient/{patient_id}",
    summary="Get Patient Information",
    description="Retrieve detailed information about a specific patient",
    response_description="Patient details including medical data",
    responses={
        200: {"description": "Patient information retrieved successfully"},
        404: {"description": "Patient not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_patient(
    patient_id: int,
    patient_service: PatientService = Depends(get_patient_service)
) -> Dict:
    """
    Получение детальной информации о пациенте.

    Возвращает полную медицинскую информацию о пациенте, включая
    все сохраненные параметры для ML-предсказаний.

    Args:
        patient_id: Идентификатор пациента

    Returns:
        Dict с медицинской информацией о пациенте:
            - id: ID пациента
            - age: Возраст пациента
            - gender: Пол пациента
            - bmi: Индекс массы тела
            - physical_activity_days_per_week: Количество дней активности в неделю
            - stress_level: Уровень стресса
            - created_at: Дата создания записи

    Raises:
        HTTPException 404: Если пациент с указанным ID не найден
        HTTPException 500: При внутренних ошибках сервера
    """
    try:
        patient = patient_service.get_patient_by_id(patient_id)
        return {
            "id": str(patient.id),
            "age": patient.age,
            "gender": patient.gender,
            "physical_activity_days_per_week": patient.physical_activity_days_per_week,
            "stress_level": patient.stress_level,
            "bmi": patient.bmi,
            "exercise_hours_per_week": patient.exercise_hours_per_week,
            "sedentary_hours_per_day": patient.sedentary_hours_per_day,
            "sleep_hours_per_day": patient.sleep_hours_per_day,
            "heart_rate": patient.heart_rate,
            "cholesterol": patient.cholesterol,
            "blood_sugar": patient.blood_sugar,
            "triglycerides": patient.triglycerides,
            "smoking": patient.smoking,
            "alcohol_consumption": patient.alcohol_consumption,
            "diabetes": patient.diabetes,
            "obesity": patient.obesity,
            "family_history": patient.family_history
        }
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


@router.put(
    "/patient/{patient_id}",
    summary="Update Patient Information",
    description="Update patient's medical data",
    response_description="Confirmation of successful patient update",
    responses={
        200: {"description": "Patient updated successfully"},
        400: {"description": "Invalid patient data"},
        404: {"description": "Patient not found"},
        500: {"description": "Internal server error"}
    }
)
async def update_patient(
    patient_id: int,
    update_data: PatientUpdate,
    patient_service: PatientService = Depends(get_patient_service)
) -> Dict:
    """
    Обновление медицинских данных пациента.

    Позволяет обновить медицинские параметры пациента. Поддерживается
    частичное обновление полей.

    Args:
        patient_id: Идентификатор пациента для обновления
        update_data: Новые медицинские данные пациента

    Returns:
        Dict с сообщением об успешном обновлении и ID пациента

    Raises:
        HTTPException 400: Если данные пациента некорректны
        HTTPException 404: Если пациент не найден
        HTTPException 500: При внутренних ошибках сервера
    """
    try:
        patient = patient_service.update_patient(patient_id, update_data)
        return {
            "message": "Patient updated successfully",
            "patient_id": str(patient.id)
        }
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
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


@router.delete(
    "/patient/{patient_id}",
    summary="Delete Patient",
    description="Permanently delete a patient record",
    response_description="Confirmation of successful patient deletion",
    responses={
        200: {"description": "Patient deleted successfully"},
        404: {"description": "Patient not found"},
        409: {"description": "Patient has associated prediction tasks"},
        500: {"description": "Internal server error"}
    }
)
async def delete_patient(
    patient_id: int,
    patient_service: PatientService = Depends(get_patient_service)
) -> Dict:
    """
    Удаление записи пациента.

    Удаляет пациента из системы. Операция невозможна, если у пациента
    есть связанные задачи предсказания.

    Args:
        patient_id: Идентификатор пациента для удаления

    Returns:
        Dict с сообщением об успешном удалении

    Raises:
        HTTPException 404: Если пациент не найден
        HTTPException 409: Если у пациента есть связанные задачи предсказания
        HTTPException 500: При внутренних ошибках сервера
    """
    try:
        patient_service.delete_patient(patient_id)
        return {"message": "Patient deleted successfully"}
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.detail)
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/task",
    status_code=status.HTTP_201_CREATED,
    summary="Create Prediction Task",
    description="Create a new ML prediction task for a patient",
    response_description="Confirmation of task creation with task ID",
    responses={
        201: {"description": "Prediction task created successfully"},
        400: {"description": "Invalid task data or user/patient not found"},
        404: {"description": "User or patient not found"},
        500: {"description": "Internal server error"}
    }
)
async def create_predict_task(
    task_data: PredictTaskCreate,
    predict_service: PredictService = Depends(get_predict_service),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Создание задачи ML-предсказания.

    Создает новую задачу предсказания для указанного пациента и текущего пользователя (JWT).
    user_id в теле запроса игнорируется — используется идентификатор из токена.

    Args:
        task_data: Данные для создания задачи (patient_id; user_id игнорируется).

    Returns:
        Dict с результатом создания:
            - message: Сообщение об успехе
            - task_id: ID созданной задачи
            - status: Текущий статус задачи

    Raises:
        HTTPException 400: Если данные задачи некорректны или пользователь деактивирован
        HTTPException 404: Если пользователь или пациент не найдены
        HTTPException 500: При внутренних ошибках сервера
    """
    task_data_owned = PredictTaskCreate(
        patient_id=task_data.patient_id,
        user_id=current_user.id
    )
    try:
        task = predict_service.create_predict_task(task_data_owned)
        return {
            "message": "Prediction task created successfully",
            "task_id": str(task.id),
            "status": task.status.value
        }
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
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


@router.post(
    "/task/{task_id}/process",
    summary="Process Prediction Task",
    description="Execute ML prediction task and deduct cost from user's balance",
    response_description="Prediction results including medical prediction and probability",
    responses={
        200: {"description": "Prediction completed successfully"},
        400: {"description": "Invalid task status, invalid cost or insufficient funds"},
        404: {"description": "Prediction task not found"},
        500: {"description": "Internal server error or ML service failure"}
    }
)
async def process_predict_task(
    task_id: int,
    predict_service: PredictService = Depends(get_predict_service),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Обработка задачи ML-предсказания.

    Выполняет ML-предсказание на основе данных пациента, списывает указанную
    стоимость с баланса пользователя и возвращает результаты предсказания.
    Только задачи в статусе PENDING могут быть обработаны.

    Args:
        task_id: Идентификатор задачи предсказания
        cost: Стоимость предсказания (должна быть положительной)

    Returns:
        Dict с результатами предсказания:
            - message: Сообщение об успехе
            - task_id: ID обработанной задачи
            - prediction: Результат предсказания (медицинский диагноз/прогноз)
            - probability: Вероятность предсказания (от 0 до 1)
            - cost: Стоимость операции

    Raises:
        HTTPException 400: Если задача не в статусе PENDING, стоимость не положительна
        HTTPException 400: Если недостаточно средств на балансе пользователя
        HTTPException 403: Если задача принадлежит другому пользователю
        HTTPException 404: Если задача предсказания не найдена
        HTTPException 500: При ошибках ML-сервиса или внутренних ошибках сервера
    """
    try:
        task = predict_service.get_predict_task_with_details_by_id(task_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.detail)
        )
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: cannot process another user's task"
        )
    try:
        processed_task_id = predict_service.process_predict_task(
            task_id, DEFAULT_COST)

        return {
            "message": "Task accepted for processing",
            "task_id": str(processed_task_id),
            "status": "processing"
        }

    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
    except InsufficientFundsException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.detail)
        )
    except InternalServerErrorException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/task/{task_id}",
    summary="Get Prediction Task Details",
    description="Retrieve detailed information about a specific prediction task",
    response_description="Complete task details including prediction results if available",
    responses={
        200: {"description": "Task information retrieved successfully"},
        404: {"description": "Prediction task not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_predict_task(
    task_id: int,
    predict_service: PredictService = Depends(get_predict_service),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Получение детальной информации о задаче предсказания.

    Возвращает полную информацию о задаче ML-предсказания, включая
    статус, стоимость, связанные данные пациента и результаты предсказания
    (если задача уже обработана).

    Args:
        task_id: Идентификатор задачи предсказания

    Returns:
        Dict с информацией о задаче:
            - task_id: ID задачи
            - status: Статус задачи (PENDING/COMPLETED/FAILED)
            - cost: Стоимость предсказания
            - created_at: Дата создания задачи
            - user_id: ID пользователя
            - patient_id: ID пациента
            - prediction: Результат предсказания (только для COMPLETED задач)
            - probability: Вероятность предсказания (только для COMPLETED задач)

    Raises:
        HTTPException 403: Если задача принадлежит другому пользователю
        HTTPException 404: Если задача предсказания не найдена
        HTTPException 500: При внутренних ошибках сервера
    """
    try:
        task = predict_service.get_predict_task_with_details_by_id(task_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.detail)
        )
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: cannot view another user's task"
        )
    result = {
        "task_id": str(task.id),
        "status": task.status.value,
        "cost": task.cost,
        "created_at": task.created_at,
        "user_id": task.user_id,
        "patient_id": task.patient_id
    }
    if task.predict:
        result.update({
            "prediction": task.predict.prediction,
            "probability": task.predict.probability
        })
    return result


@router.get(
    "/tasks/{user_id}",
    summary="Get User Prediction Tasks",
    description="Retrieve user's prediction task history with filtering options",
    response_description="List of prediction tasks matching the filter criteria",
    responses={
        200: {"description": "Task history retrieved successfully"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_predict_tasks(
    user_id: int,
    current_user: User = Depends(get_current_user),
    status: Optional[PredictStatus] = Query(
        None, description="Filter by task status"),
    min_cost: Optional[float] = Query(
        None, ge=0, description="Minimum task cost"),
    max_cost: Optional[float] = Query(
        None, ge=0, description="Maximum task cost"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for date range filter"),
    end_date: Optional[datetime] = Query(
        None, description="End date for date range filter"),
    limit: int = Query(
        100, le=1000, description="Maximum number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    predict_service: PredictService = Depends(get_predict_service)
) -> List[Dict]:
    """
    Получение истории задач ML-предсказаний пользователя.

    Возвращает список задач предсказания пользователя с возможностью фильтрации
    по статусу, стоимости и дате. Задачи сортируются по дате создания в порядке убывания.

    Args:
        user_id: Идентификатор пользователя
        status: Фильтр по статусу задачи (PENDING/COMPLETED/FAILED)
        min_cost: Минимальная стоимость задачи
        max_cost: Максимальная стоимость задачи
        start_date: Начальная дата для фильтрации по дате создания
        end_date: Конечная дата для фильтрации по дате создания
        limit: Максимальное количество возвращаемых задач (по умолчанию 100, максимум 1000)
        offset: Количество пропускаемых задач (для пагинации)

    Returns:
        List[Dict] с информацией о задачах предсказания, каждая задача содержит:
            - task_id: ID задачи
            - status: Статус задачи
            - cost: Стоимость задачи
            - created_at: Дата и время создания задачи
            - user_id: ID пользователя
            - patient_id: ID пациента
            - prediction: Результат предсказания (только для COMPLETED задач)
            - probability: Вероятность предсказания (только для COMPLETED задач)

    Raises:
        HTTPException 403: Если запрашиваются задачи другого пользователя
        HTTPException 404: Если пользователь не найден
        HTTPException 500: При внутренних ошибках сервера
    """
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: cannot view another user's tasks"
        )
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
