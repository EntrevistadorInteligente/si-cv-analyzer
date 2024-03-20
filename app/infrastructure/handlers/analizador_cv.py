from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends
from app.infrastructure.container import Container
from app.application.services.procesar_pdf_service import ProcesarPdfService
from app.infrastructure.schemas.hoja_de_vida_dto import HojaDeVidaDto, PreparacionEntrevistaDto

router = APIRouter(
    prefix='/analizador',
    tags=['analizador']
)


@router.post('/procesar-cv', response_model=HojaDeVidaDto)
@inject
async def procesar_cv(
        contenido: PreparacionEntrevistaDto,
        procesar_pdf_service: ProcesarPdfService = Depends(Provide[Container.procesar_pdf_service])) -> HojaDeVidaDto:
    return procesar_pdf_service.execute(contenido.hoja_de_vida)
