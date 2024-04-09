from app.application.services.generar_modelo_contexto_pdf import GenerarModeloContextoPdf
from app.application.services.obtener_hoja_de_vida import ObtenerHojaDeVida
from app.infrastructure.schemas.hoja_de_vida_dto import HojaDeVidaDto, ProcesoEntrevistaDto, EstadoProcesoEnum, Match
from fastapi import HTTPException
import re

predefined_questions = [        # ARREGLAR PROMPT!
        "Analiza la siguiente hoja de vida e identifica si es adecuada para el puesto de "
        "trabajo al que se intenta aplicar. Indica con 'True' en caso que sea adecuado y False en caso contrario. "
        "Entrega una muy breve razon de porque es o no adecuada (10 palabras). "
        "Limita tu respuesta a estas dos parametros. "
        "Ejemplo: "
        "Validar Puesto Match: True"
        "Razón validación: *Motivo*"
]

class ValidarMatch:
    def __init__(self, obtener_hoja_de_vida: ObtenerHojaDeVida,
                 generar_modelo_contexto_pdf: GenerarModeloContextoPdf,
                 kafka_producer_service):
        self.obtener_hoja_de_vida = obtener_hoja_de_vida
        self.generar_modelo_contexto_pdf = generar_modelo_contexto_pdf
        self.kafka_producer_service = kafka_producer_service

    async def execute(self, id_entrevista: str, contents: bytes):
        text_chunks = await self.obtener_hoja_de_vida.ejecutar(id_entrevista)
        conversation_chain = self.generar_modelo_contexto_pdf.ejecutar(text_chunks) # Esto no es asi!!

        response = conversation_chain({'question': predefined_questions[0]})
        respuesta_ia = response['chat_history'][-1].content if response['chat_history'] else ""

        # Comprobar si se extrajo algún texto
        if not respuesta_ia:
            raise HTTPException(status_code=400, detail="No se pudo generar analisis cv")

        # Patrones de expresiones regulares para cada sección
        patrones = {
            "validar_puesto_match": r"Validar puesto match: ([^\n]+)",
            "razon_validacion": r"Razón validación: ([^\n]+)"
        }

        # Extraer la información usando expresiones regulares
        datos = {key: re.search(pattern, respuesta_ia).group(1) for key, pattern in patrones.items() if
                 re.search(pattern, respuesta_ia)}

        validar_puesto_match = datos.get('validar_puesto_match', '')

        # Genera boolianos de la respuesta
        if validar_puesto_match.lower() == "True":
            match_valido = True

        else:
            match_valido = False

        validacion_match = Match(
            id_entrevista=id_entrevista,
            match_valido=match_valido
        )
        # Revisar
        await self.kafka_producer_service.send_message(validacion_match, 'hojaDeVidaValidaTopic')
