import asyncio
import os

from aiokafka.admin import NewTopic, AIOKafkaAdminClient
from fastapi import FastAPI
from dotenv import load_dotenv
from app.infrastructure.jms.kafka_consumer_service import KafkaConsumerService
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.infrastructure.container import Container
from app.infrastructure.handlers import Handlers
from app.infrastructure.handlers.listener import validate_match_message, \
    process_cv_message

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
            print("Kafka producer service stopped")

    @fast_api.on_event("startup")
    async def startup_event():
        sasl_username_kafka = os.getenv('KAFKA_UPSTAR_USER')
        sasl_password_kafka = os.getenv('KAFKA_UPSTAR_PASSWORD')
        bootstrap_servers_kafka = os.getenv('KAFKA_SERVER')

        # Crear un cliente de administración de Kafka
        admin_client = AIOKafkaAdminClient(
            bootstrap_servers=bootstrap_servers_kafka,
            # Configuración adicional si usas autenticación o SSL
            # security_protocol='SASL_SSL',
            # sasl_mechanism='PLAIN',
            # sasl_plain_username=sasl_username_kafka,
            # sasl_plain_password=sasl_password_kafka,
        )

        await admin_client.start()

        # Definir los tópicos necesarios
        topics_to_ensure = ['hojaDeVidaPublisherTopic', 'hojaDeVidaValidaPublisherTopic']

        # Obtener la lista de tópicos existentes
        existing_topics = await admin_client.list_topics()

        # Encontrar los tópicos que necesitan ser creados
        topics_to_create = []
        for topic in topics_to_ensure:
            if topic not in existing_topics:
                new_topic = NewTopic(
                    name=topic,
                    num_partitions=1,
                    replication_factor=1,  # Ajusta según tu configuración
                )
                topics_to_create.append(new_topic)

        # Crear los tópicos si es necesario
        if topics_to_create:
            await admin_client.create_topics(new_topics=topics_to_create)
            print(f"Tópicos creados: {[t.name for t in topics_to_create]}")
        else:
            print("Todos los tópicos ya existen")

        #await admin_client.stop()

        # Continuar con la configuración de productores y consumidores
        kafka_consumer_service = KafkaConsumerService('hojaDeVidaPublisherTopic',
                                                      sasl_username_kafka,
                                                      sasl_password_kafka,
                                                      bootstrap_servers_kafka)
        kafka_feedback_consumer_service = KafkaConsumerService('hojaDeVidaValidaPublisherTopic',
                                                               sasl_username_kafka,
                                                               sasl_password_kafka,
                                                               bootstrap_servers_kafka)

        global kafka_producer_service
        kafka_producer_service = KafkaProducerService(sasl_username_kafka,
                                                      sasl_password_kafka,
                                                      bootstrap_servers_kafka)

        await kafka_producer_service.start()
        print("Kafka producer service started")

        # Iniciar los consumidores de Kafka en tareas asíncronas separadas
        await asyncio.create_task(kafka_consumer_service.start())
        asyncio.create_task(kafka_feedback_consumer_service.start())
        asyncio.create_task(kafka_consumer_service.consume_messages(process_cv_message))
        asyncio.create_task(kafka_feedback_consumer_service.consume_messages(validate_match_message))

        print("Kafka consumer services started")

    return fast_api
