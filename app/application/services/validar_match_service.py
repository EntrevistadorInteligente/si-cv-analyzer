from app.application.services.generar_modelo_contexto_pdf import GenerarModeloContextoPdf
from app.infrastructure.schemas.hoja_de_vida_dto import HojaDeVidaDto, ProcesoEntrevistaDto, EstadoProcesoEnum, Match
from fastapi import HTTPException
import re

predefined_questions = [
    "AGREGAR PROMPT PROPIO"
]

class ValidarMatch:
    def __init__(self,
                 hoja_de_vida_repository,
                 generar_modelo_contexto_pdf: GenerarModeloContextoPdf,
                 kafka_producer_service):

        self.generar_modelo_contexto_pdf = generar_modelo_contexto_pdf
        self.hoja_de_vida_repository = hoja_de_vida_repository
        self.kafka_producer_service = kafka_producer_service

    async def execute(self, id_entrevista: str, contents: bytes) -> HojaDeVidaDto:
        text_chunks, hoja_de_vida, = await self.hoja_de_vida_repository.obtener_por_id('id_entrevista')
        #text_chunks, id_hoja_de_vida = await self.extraer_pdf_service.ejecutar(id_entrevista, contents)
        conversation_chain = self.generar_modelo_contexto_pdf.ejecutar(text_chunks)

        response = conversation_chain({'question': predefined_questions[0]})
        respuesta_ia = response['chat_history'][-1].content if response['chat_history'] else ""

        # Comprobar si se extrajo algún texto
        if not respuesta_ia:
            raise HTTPException(status_code=400, detail="No se pudo generar analisis cv")

        # Patrones de expresiones regulares para cada sección
        patrones = {
            "validar_puesto_match": r"Validar puesto match: ([^\n]+)"
        }

        # Extraer la información usando expresiones regulares
        datos = {key: re.search(pattern, respuesta_ia).group(1) for key, pattern in patrones.items() if
                 re.search(pattern, respuesta_ia)}

        validar_puesto_match = datos.get('hoja_de_vida_valida', '')

        # Genera boolianos de la respuesta
        if validar_puesto_match.lower() == "True":
            match_valido = True

        else:
            match_valido = False


        try:
            hoja_de_vida_dto = HojaDeVidaDto(**datos)
        except HTTPException as e:
            print("Error al validar la información extraída:", e)
            # Manejar el error o crear una respuesta por defecto si es necesario
            hoja_de_vida_dto = HojaDeVidaDto()

            proceso_entrevista = ProcesoEntrevistaDto(
                uuid=preparacion_entrevista_dto.evento_entrevista_id,
                estado=EstadoProcesoEnum.FN,
                fuente="ANALIZADOR"
            )

            validacion_match = Match(
                id_entrevista=id_entrevista,
                match_valido=match_valido
            )

            await self.kafka_producer_service.send_message(validacion_match, 'hojaDeVidaValidaTopic')  # No estoy seguro de esta parte
