from datetime import datetime, timezone
import json
import pika
import logging
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from models.predict import (
    Patient,
    PredictTask,
    PatientCreate,
    PatientUpdate,
    PredictTaskCreate,
    PredictTaskFilter
)
from models.user import User
from models.finance import Transaction
from models.enums import Currency, PredictStatus, TransactionType
from exceptions import (
    NotFoundException,
    BadRequestException,
    InsufficientFundsException,
    InternalServerErrorException
)

from config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PatientService:
    def __init__(self, db: Session):
        self.db = db

    def get_patient_by_id(self, patient_id: int) -> Patient:
        patient = self.db.get(Patient, patient_id)
        if not patient:
            raise NotFoundException(f"Patient with id {patient_id} not found")
        return patient

    def create_patient(self, patient_data: PatientCreate) -> Patient:
        patient = Patient(**patient_data.model_dump())

        self.db.add(patient)
        self.db.flush()

        return patient

    def update_patient(self, patient_id: int, update_data: PatientUpdate) -> Optional[Patient]:
        patient = self.get_patient_by_id(patient_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(patient, field, value)

        patient.update_timestamp()
        self.db.flush()
        self.db.refresh(patient)

        return patient

    def delete_patient(self, patient_id: int) -> bool:
        patient = self.get_patient_by_id(patient_id)

        self.db.delete(patient)
        return True


class PredictService:
    def __init__(self, db: Session, patient_service: PatientService):
        self.db = db
        self.settings = get_settings()
        self.connection_params = pika.ConnectionParameters(
            host=self.settings.RABBITMQ_HOST,
            port=self.settings.RABBITMQ_PORT,
            virtual_host='/',
            credentials=pika.PlainCredentials(
                username=self.settings.RABBITMQ_USER,
                password=self.settings.RABBITMQ_PASSWORD
            ),
            heartbeat=30,
            blocked_connection_timeout=2
        )
        self.patient_service = patient_service

    def get_predict_task_by_id(self, task_id: int) -> PredictTask:
        task = self.db.get(PredictTask, task_id)
        if not task:
            raise NotFoundException(
                f"Prediction task with id {task_id} not found")
        return task

    def get_predict_task_with_details_by_id(self, task_id: int) -> PredictTask:
        stmt = (
            select(PredictTask)
            .options(
                joinedload(PredictTask.patient),
                joinedload(PredictTask.user),
                joinedload(PredictTask.predict)
            )
            .where(PredictTask.id == task_id)
        )
        task = self.db.scalar(stmt)
        if not task:
            raise NotFoundException(
                f"Prediction task with id {task_id} not found")

        return task

    def create_predict_task(self, task_data: PredictTaskCreate) -> PredictTask:
        try:
            self.patient_service.get_patient_by_id(task_data.patient_id)
        except NotFoundException:
            raise BadRequestException(
                f"Patient with id {task_data.patient_id} not found")

        user = self.db.get(User, task_data.user_id)

        if not user:
            raise NotFoundException(
                f"User with id {task_data.user_id} not found")

        if not user.is_active:
            raise BadRequestException(
                f"User with id {task_data.user_id} is deactivated")

        if not user.balance:
            raise BadRequestException(
                f"User with id {task_data.user_id} has no balance")

        task = PredictTask(
            patient_id=task_data.patient_id,
            user_id=task_data.user_id,
            status=PredictStatus.PENDING
        )

        self.db.add(task)
        self.db.flush()

        return task

    def process_predict_task(self, task_id: int, cost: float) -> int:
        task = self.get_predict_task_with_details_by_id(task_id)

        if task.status != PredictStatus.PENDING:
            raise BadRequestException(
                f"Cannot process task in {task.status.value} status. Only 'PENDING' tasks can be processed."
            )

        if cost <= 0:
            raise BadRequestException("Cost of predict task must be positive")

        task.start_processing(cost)
        self.db.flush()

        try:
            if task.user.balance.value < cost:
                task.status = PredictStatus.FAILED
                self.db.flush()
                raise InsufficientFundsException(
                    f"Insufficient funds. Required: {cost}, Available: {task.user.balance.value}"
                )

            task.user.balance.withdraw(cost)
            transaction = Transaction(
                type=TransactionType.WITHDRAWAL,
                amount=cost,
                currency=Currency.RUB,
                description="Withdraw for predict task",
                user_id=task.user_id
            )
            self.db.add(transaction)

            self._publish_predict_task(task)

            self.db.flush()
            return task.id

        except InsufficientFundsException:
            raise
        except Exception as e:
            task.status = PredictStatus.FAILED
            if hasattr(task, 'cost') and task.cost > 0:
                task.user.balance.deposit(task.cost)
            self.db.flush()

            raise InternalServerErrorException(
                f"Failed to process prediction task: {str(e)}"
            )

    def get_user_predict_tasks(
        self,
        user_id: int,
        filters: Optional[PredictTaskFilter] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PredictTask]:
        user = self.db.get(User, user_id)
        if not user:
            raise NotFoundException(f"User with id {user_id} not found")

        stmt = (
            select(PredictTask)
            .where(PredictTask.user_id == user_id)
            .options(
                joinedload(PredictTask.patient),
                joinedload(PredictTask.user),
                joinedload(PredictTask.predict)
            )
        )

        if filters:
            if filters.status:
                stmt = stmt.where(PredictTask.status == filters.status)
            if filters.min_cost:
                stmt = stmt.where(PredictTask.cost >= filters.min_cost)
            if filters.max_cost:
                stmt = stmt.where(PredictTask.cost <= filters.max_cost)
            if filters.start_date:
                stmt = stmt.where(PredictTask.created_at >= filters.start_date)
            if filters.end_date:
                stmt = stmt.where(PredictTask.created_at <= filters.end_date)
        stmt = stmt.order_by(PredictTask.created_at.desc()
                             ).limit(limit).offset(offset)

        return list(self.db.scalars(stmt).all())

    def _publish_predict_task(self, task: PredictTask):
        try:
            patient = task.patient
            if not patient:
                raise ValueError(f"Task {task.id} has no associated patient")

            features = patient._to_dict()
            message = {
                "task_id": str(task.id),
                "features": features,
                "model": "demo_model",
                "timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds') + "Z"
            }

            connection = pika.BlockingConnection(self.connection_params)
            channel = connection.channel()
            channel.queue_declare(queue=self.settings.QUEUE_NAME, durable=True)

            channel.basic_publish(
                exchange='',
                routing_key=self.settings.QUEUE_NAME,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            connection.close()

            logger.info(
                f"Task with id {task.id} published to queue {self.settings.QUEUE_NAME}"
            )
        except Exception as e:
            logger.error(f"Failed to publish task with id {task.id}: {e}")
            raise
