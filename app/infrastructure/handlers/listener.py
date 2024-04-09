from fastapi import Depends, APIRouter

from app.application.services.obtener_hoja_de_vida import ObtenerHojaDeVida
from app.application.services.validar_match_service import ValidarMatch
from app.domain.repositories.hoja_de_vida_rag import HojaDeVidaRepository
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.application.services.procesar_pdf_service import ProcesarPdfService
from app.infrastructure.container import Container
from dependency_injector.wiring import Provide, inject
import json


from app.infrastructure.schemas.hoja_de_vida_dto import PreparacionEntrevistaDto, ProcesoEntrevistaDto, EstadoProcesoEnum

router = APIRouter(
    prefix='/analizador2',
    tags=['analizador']
)


@router.get('/', response_model=str)
@inject
async def process_cv_message(message,
                             procesar_pdf_service: ProcesarPdfService =
                             Depends(Provide[Container.procesar_pdf_service]),
                             kafka_producer_service: KafkaProducerService =
                             Depends(Provide[Container.kafka_producer_service])
                             ):
    data = json.loads(message.value.decode('utf-8'))
    # Suponiendo que data contiene la clave 'hoja_de_vida' con la información necesaria.
    id_entrevista = data.get('id_entrevista')
    preparacion_entrevista_dto = PreparacionEntrevistaDto(
        id_entrevista=id_entrevista,
        evento_entrevista_id=data.get('evento_entrevista_id'),
        hoja_de_vida=data.get('hoja_de_vida')   # Esto no deberia estar aqui no?
    )

    await procesar_pdf_service.execute(preparacion_entrevista_dto.id_entrevista,
                                       preparacion_entrevista_dto.hoja_de_vida)


@router.get('/2', response_model=str)
@inject
async def validate_match_message(message,
                                 validar_match: ValidarMatch = Depends(Provide[Container.validar_match]),
                                 kafka_producer_service: KafkaProducerService =
                                 Depends(Provide[Container.kafka_producer_service])
                                 ):
    data = json.loads(message.value.decode('utf-8'))    # Que tenemos que sacar de data?
    id_entrevista = data.get('id_entrevista')

    '''
    preparacion_entrevista_dto = PreparacionEntrevistaDto(
        id_entrevista=id_entrevista,
        evento_entrevista_id=data.get('evento_entrevista_id'),
        hoja_de_vida=data.get('hoja_de_vida')
    )
    '''

    await validar_match.execute(id_entrevista, )


