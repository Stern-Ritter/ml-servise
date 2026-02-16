import logging
from sqlalchemy.orm import Session

from .ml_service import MLService

from app.models.predict import (
    PredictTask,
    Predict
)

from app.models.user import (
    User
)

from app.models.enums import (
    PredictStatus
)

from app.exceptions import (
    NotFoundException,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictService:
    def __init__(self, db: Session, ml_service: MLService):
        self.db = db
        self.ml_service = ml_service

    def get_predict_task_by_id(self, task_id: int) -> PredictTask:
        task = self.db.get(PredictTask, task_id)
        if not task:
            raise NotFoundException(
                f"Prediction task with id {task_id} not found")
        return task

    def process_predict_task(self, task_id: int) -> Predict:
        task = self.get_predict_task_by_id(task_id)
        if not task:
            raise NotFoundException(
                f"Prediction task with id {task_id} not found")
        if not task.patient:
            raise NotFoundException(
                f"Patient for task with id {task_id} not found")

        patient_data = task.patient._to_dict()
        prediction_result = self.ml_service.predict(patient_data)

        predict = Predict(
            prediction=prediction_result["prediction"],
            probability=prediction_result["probability"],
            task_id=task.id
        )

        self.db.add(predict)
        task.status = PredictStatus.COMPLETED
        self.db.flush()

        return predict
