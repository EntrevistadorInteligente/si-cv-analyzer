import logging

from fastapi import Depends, APIRouter

from app.application.services.validar_match_service import ValidarMatch
from app.application.services.procesar_pdf_service import ProcesarPdfService
from app.infrastructure.container import Container
from dependency_injector.wiring import Provide, inject
import json


from app.infrastructure.schemas.hoja_de_vida_dto import FormularioDto

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix='/analizador2',
    tags=['analizador']
)


@router.get('/', response_model=str)
@inject
async def process_cv_message(message,
                             procesar_pdf_service: ProcesarPdfService =
                             Depends(Provide[Container.procesar_pdf_service])):
    try:
        data = json.loads(message.decode('utf-8'))
        usuario = data.get('username')
        await procesar_pdf_service.execute(usuario,
                                           data.get('hoja_de_vida'))
        logger.info(f"Procesamiento completado para la cv del usuaio {usuario}.")

    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}. Mensaje recibido")
    except Exception as e:
        logger.error(f"Error inesperado durante el procesamiento de la entrevista: {e}")


@router.get('/2', response_model=str)
@inject
async def validate_match_message(message, validar_match: ValidarMatch = Depends(Provide[Container.validar_match])):

    try:
        data = json.loads(message.decode('utf-8'))
        id_hoja_de_vida_rag = data.get('id_hoja_de_vida_rag')
        id_entrevista = data.get('id_entrevista')

        await validar_match.execute(id_hoja_de_vida_rag, id_entrevista, FormularioDto(**data.get('formulario')))
        logger.info(f"Procesamiento completado para la entrevista ID {data.get('id_entrevista')}.")

    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}. Mensaje recibido: {message}")
    except Exception as e:
        logger.error(f"Error inesperado durante el procesamiento de la entrevista: {e}")


