from dependency_injector import containers, providers
from app.application.services.extraer_pdf import ExtraerPdf
from app.application.services.generar_modelo_contexto_pdf import GenerarModeloContextoPdf
from app.application.services.kafka_consumer_service import KafkaConsumerService
from app.application.services.kafka_producer_service import KafkaProducerService
from app.application.services.procesar_pdf_service import ProcesarPdfService
from app.infrastructure.handlers import Handlers
from app.infrastructure.jms import Jms


class Container(containers.DeclarativeContainer):
    # loads all handlers where @injects are set
    wiring_config = containers.WiringConfiguration(modules=Handlers.modules())
    wiring_config2 = containers.WiringConfiguration(modules=Jms.modules())

    # Dependencias
    extraer_pdf_service = providers.Factory(ExtraerPdf)
    generar_modelo_contexto_pdf = providers.Factory(GenerarModeloContextoPdf)

    # Servicio que depende de las anteriores
    procesar_pdf_service = providers.Factory(
        ProcesarPdfService,
        extraer_pdf_service=extraer_pdf_service,
        generar_modelo_contexto_pdf=generar_modelo_contexto_pdf
    )

    process_cv_message = providers.Factory(
        # Pasa las dependencias requeridas por process_cv_message aquí, como:
        procesar_pdf_service=procesar_pdf_service
    )

    kafka_consumer_service = providers.Singleton(
        KafkaConsumerService,
        topic='hojaDeVidaPublisherTopic',
        # Pasa las dependencias necesarias, si las hay.
    )

    kafka_producer_service = providers.Singleton(
        KafkaProducerService,
        bootstrap_servers='localhost:9092',
        topic='hojaDeVidaListenerTopic',
        # Pasa las dependencias necesarias, si las hay.
    )
