import json
import logging

from database import SessionLocal
from app.exceptions import (
    NotFoundException
)

from services.predict_service import PredictService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, ml_service):
        self.ml_service = ml_service

    def callback(self, ch, method, properties, body):
        session = SessionLocal()
        try:
            is_model_loaded = self.ml_service.model is not None
            is_preprocessing_pipeline_loaded = self.ml_service.preprocessing_pipeline is not None
            is_required_features_loaded = self.ml_service.required_features is not None
            if not (is_model_loaded and is_preprocessing_pipeline_loaded and is_required_features_loaded):
                logger.error(
                    f"ML model is loaded: {is_model_loaded}, preprocessing pipeline is loaded: {is_preprocessing_pipeline_loaded}, Features are loaded: {is_required_features_loaded}"
                )
                raise ValueError(
                    f"ML model is loaded: {is_model_loaded}, preprocessing pipeline is loaded: {is_preprocessing_pipeline_loaded}, Features are loaded: {is_required_features_loaded}")

            message = json.loads(body)
            task_id = message.get('task_id')
            if not task_id:
                logger.error(f"Invalid message: missing task_id: {message}")
                raise ValueError(
                    f"Invalid message: missing task_id: {message}")

            logger.info(f"Received task with id: {task_id}")

            predict_service = PredictService(session, self.ml_service)
            predict = predict_service.process_predict_task(task_id)

            session.commit()
            logger.info(f"Task {task_id} processed successfully: {predict}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Task {task_id} acknowledged")

        except NotFoundException as e:
            logger.exception(e.detail)
            session.rollback()
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            session.rollback()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            session.close()
