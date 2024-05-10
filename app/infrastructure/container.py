import os

from dependency_injector import containers, providers
from dotenv import load_dotenv

from app.application.services.extraer_pdf import ExtraerPdf
from app.application.services.generar_modelo_contexto import GenerarModeloContextoPdf
from app.infrastructure.jms.kafka_consumer_service import KafkaConsumerService
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.application.services.procesar_pdf_service import ProcesarPdfService
from app.application.services.validar_match_service import ValidarMatch
from app.domain.entities.hoja_de_vida import HojaDeVidaFactory
from app.infrastructure.handlers import Handlers
from app.infrastructure.jms import Jms
from app.infrastructure.repositories.hoja_de_vida_rag import HojaDeVidaMongoRepository

# Carga las variables de entorno al inicio
load_dotenv()


class Container(containers.DeclarativeContainer):
    # loads all handlers where @injects are set
    wiring_config = containers.WiringConfiguration(modules=Handlers.modules())
    wiring_config2 = containers.WiringConfiguration(modules=Jms.modules())

    # Dependencias
    generar_modelo_contexto = providers.Factory(GenerarModeloContextoPdf)

    # Factories
    hoja_de_vida_factory = providers.Factory(HojaDeVidaFactory)

    # Repositories
    # Obtener la URL de MongoDB desde las variables de entorno
    mongo_url = os.getenv('MONGO_URI')
    sasl_username_kafka = os.getenv('KAFKA_UPSTAR_USER')
    sasl_password_kafka = os.getenv('KAFKA_UPSTAR_PASSWORD')
    bootstrap_servers_kafka = os.getenv('KAFKA_UPSTAR_SERVER_URL')

    # MONGO_URI no esté definida
    if mongo_url is None:
        raise ValueError("MONGO_URI environment variable is not set.")

    hoja_de_vida_rag_repository = providers.Factory(
        HojaDeVidaMongoRepository,
        mongo_url=mongo_url
    )

    # Servicio que depende de las anteriores
    extraer_pdf_service = providers.Factory(
        ExtraerPdf,
        hoja_de_vida_rag_repository=hoja_de_vida_rag_repository
    )

    kafka_consumer_service = providers.Singleton(
        KafkaConsumerService,
    )

    kafka_producer_service = providers.Singleton(
        KafkaProducerService,
        sasl_username=sasl_username_kafka,
        sasl_password=sasl_password_kafka,
        bootstrap_servers=bootstrap_servers_kafka
    )

    # Servicio que depende de las anteriores
    procesar_pdf_service = providers.Factory(
        ProcesarPdfService,
        extraer_pdf_service=extraer_pdf_service,
        generar_modelo_contexto=generar_modelo_contexto,
        kafka_producer_service=kafka_producer_service
    )

    process_cv_message = providers.Factory(
        procesar_pdf_service=procesar_pdf_service
    )

    validar_match = providers.Factory(
        ValidarMatch,
        hoja_de_vida_rag_repository=hoja_de_vida_rag_repository,
        generar_modelo_contexto=generar_modelo_contexto,
        kafka_producer_service=kafka_producer_service
    )

    validate_match_message = providers.Factory(
        validar_match=validar_match
    )

