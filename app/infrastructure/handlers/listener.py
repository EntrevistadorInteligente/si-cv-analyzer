from fastapi import Depends, APIRouter

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
        hoja_de_vida=data.get('hoja_de_vida')
    )
    hoja_de_vida_dto = await procesar_pdf_service.execute(preparacion_entrevista_dto.id_entrevista,
                                                          preparacion_entrevista_dto.hoja_de_vida)

    proceso_entrevista = ProcesoEntrevistaDto(
        uuid=preparacion_entrevista_dto.evento_entrevista_id,
        estado=EstadoProcesoEnum.FN,
        fuente="ANALIZADOR"
    )

    await kafka_producer_service.send_message({
        "proceso_entrevista": proceso_entrevista.dict(),
        "id_entrevista": id_entrevista,
        "hoja_de_vida": hoja_de_vida_dto.dict()})



