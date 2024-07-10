import logging

from fastapi import Depends, APIRouter
from app.application.services.procesar_pdf_service import ProcesarPdfService
from app.infrastructure.container import Container
from dependency_injector.wiring import Provide, inject
import json

from app.infrastructure.schemas.hoja_de_vida_dto import SolicitudHojaDeVidaDto, HojaDeVidaDto

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/v1/analizador',
    tags=['analizador']
)


@router.post('/hojas-de-vida/generar', response_model=HojaDeVidaDto)
@inject
async def process_cv_message(message: SolicitudHojaDeVidaDto,
                             procesar_pdf_service: ProcesarPdfService =
                             Depends(Provide[Container.procesar_pdf_service])) -> HojaDeVidaDto:
    try:
        hoja_de_vida_dto = await procesar_pdf_service.execute(message.username, message.hoja_de_vida)
        logger.info(f"Procesamiento completado para la cv del usuario {message.username}.")
        return hoja_de_vida_dto
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}. Mensaje recibido")
    except Exception as e:
        logger.error(f"Error inesperado durante el procesamiento de la entrevista: {e}")

