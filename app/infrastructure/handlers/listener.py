from fastapi import Depends, APIRouter

from app.application.services.validar_match_service import ValidarMatch
from app.application.services.procesar_pdf_service import ProcesarPdfService
from app.infrastructure.container import Container
from dependency_injector.wiring import Provide, inject
import json


from app.infrastructure.schemas.hoja_de_vida_dto import PreparacionEntrevistaDto, ProcesoEntrevistaDto, \
    EstadoProcesoEnum, FormularioDto

router = APIRouter(
    prefix='/analizador2',
    tags=['analizador']
)


@router.get('/', response_model=str)
@inject
async def process_cv_message(message,
                             procesar_pdf_service: ProcesarPdfService =
                             Depends(Provide[Container.procesar_pdf_service])):
    data = json.loads(message.value.decode('utf-8'))
    await procesar_pdf_service.execute(data.get('username'),
                                       data.get('hoja_de_vida'))


@router.get('/2', response_model=str)
@inject
async def validate_match_message(message, validar_match: ValidarMatch = Depends(Provide[Container.validar_match])):

    data = json.loads(message.value.decode('utf-8'))
    id_hoja_de_vida_rag = data.get('id_hoja_de_vida_rag')
    id_entrevista= data.get('id_entrevista')

    await validar_match.execute(id_hoja_de_vida_rag, id_entrevista,  FormularioDto(**data.get('formulario')))


