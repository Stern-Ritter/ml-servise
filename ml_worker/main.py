import logging
import pika
import time

from config import get_settings
from services.ml_service import MLService
from worker import Worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    settings = get_settings()
    ml_service = MLService()
    worker = Worker(ml_service)

    connection_parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        virtual_host='/',
        credentials=pika.PlainCredentials(
            username=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASSWORD
        ),
        heartbeat=30,
        blocked_connection_timeout=2
    )

    while True:
        try:
            connection = pika.BlockingConnection(connection_parameters)
            channel = connection.channel()
            channel.queue_declare(queue=settings.QUEUE_NAME, durable=True)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=settings.QUEUE_NAME,
                on_message_callback=worker.callback,
                auto_ack=False
            )

            logger.info(
                f"Worker started, waiting for messages in queue '{settings.QUEUE_NAME}'"
            )
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            logger.error(
                f"RabbitMQ connection error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Stopped by user")
            break
        finally:
            try:
                connection.close()
            except:
                pass


if __name__ == '__main__':
    main()
