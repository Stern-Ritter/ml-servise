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
            message = json.loads(body)
            task_id = message.get('task_id')
            if not task_id:
                logger.error(f"Invalid message: missing task_id: {message}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

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
