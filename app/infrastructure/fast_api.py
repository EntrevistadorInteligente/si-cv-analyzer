import asyncio
from fastapi import FastAPI
from app.application.services.kafka_consumer_service import KafkaConsumerService
from app.application.services.kafka_producer_service import KafkaProducerService
from app.infrastructure.container import Container
from app.infrastructure.handlers import Handlers
from app.infrastructure.handlers.listener import process_cv_message

kafka_producer_service = None


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
        kafka_consumer_service = KafkaConsumerService('kafkaTopic')
        # Registramos la tarea del consumidor para ejecutarse como una tarea de fondo.
        await asyncio.create_task(kafka_consumer_service.consume_messages(process_cv_message))

        global kafka_producer_service
        kafka_producer_service = KafkaProducerService('localhost:9092', 'resumeTopic')
        await kafka_producer_service.start()
    return fast_api
