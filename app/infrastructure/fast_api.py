import asyncio
import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.infrastructure.jms.kafka_consumer_service import KafkaConsumerService
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.infrastructure.container import Container
from app.infrastructure.handlers import Handlers
from app.infrastructure.handlers.listener import validate_match_message, process_cv_message

kafka_producer_service = None
load_dotenv()


def create_app():
    fast_api = FastAPI()
    fast_api.container = Container()
    for handler in Handlers.iterator():
        fast_api.include_router(handler.router)

    @fast_api.on_event("shutdown")
    async def shutdown_event():
        global kafka_producer_service
        if kafka_producer_service:
            await kafka_producer_service.stop()

    @fast_api.on_event("startup")
    async def startup_event():
        sasl_username_kafka = os.getenv('KAFKA_UPSTAR_USER')
        sasl_password_kafka = os.getenv('KAFKA_UPSTAR_PASSWORD')
        bootstrap_servers_kafka = os.getenv('KAFKA_UPSTAR_SERVER_URL')

        kafka_consumer_service = KafkaConsumerService('hojaDeVidaPublisherTopic',
                                                      sasl_username_kafka,
                                                      sasl_password_kafka,
                                                      bootstrap_servers_kafka)
        await kafka_consumer_service.start()

        kafka_hoja_vida_valida_consumer_service = KafkaConsumerService('hojaDeVidaValidaPublisherTopic',
                                                                       sasl_username_kafka,
                                                                       sasl_password_kafka,
                                                                       bootstrap_servers_kafka)
        await kafka_hoja_vida_valida_consumer_service.start()

        global kafka_producer_service
        kafka_producer_service = KafkaProducerService(sasl_username_kafka,
                                                      sasl_password_kafka,
                                                      bootstrap_servers_kafka)

        await kafka_producer_service.start()

        # Crear tareas para los consumidores de manera que no bloqueen el inicio de uno a otro.
        task1 = asyncio.create_task(kafka_hoja_vida_valida_consumer_service.consume_messages(validate_match_message))
        task2 = asyncio.create_task(kafka_consumer_service.consume_messages(process_cv_message))

        # Opcional: Esperar a que ambas tareas estén corriendo
        await asyncio.gather(task1, task2)
    return fast_api

