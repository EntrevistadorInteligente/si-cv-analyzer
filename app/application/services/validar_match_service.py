from app.application.services.generar_modelo_contexto import GenerarModeloContextoPdf
from app.domain.repositories.hoja_de_vida_rag import HojaDeVidaRepository
from app.infrastructure.jms.kafka_producer_service import KafkaProducerService
from app.infrastructure.schemas.hoja_de_vida_dto import Match, FormularioDto
from fastapi import HTTPException
import re


class ValidarMatch:
    def __init__(self, hoja_de_vida_rag_repository: HojaDeVidaRepository,
                 generar_modelo_contexto: GenerarModeloContextoPdf,
                 kafka_producer_service: KafkaProducerService):
        self.hoja_de_vida_rag_repository = hoja_de_vida_rag_repository
        self.generar_modelo_contexto = generar_modelo_contexto
        self.kafka_producer_service = kafka_producer_service

    async def execute(self, id_hoja_de_vida_rag: str, id_entrevista: str, formulario: FormularioDto):

        respuesta_ia = await self.extraer_informacion_hoja_de_vida(formulario, id_hoja_de_vida_rag)

        validacion_match = await self.generar_validacion_puesto(id_entrevista, respuesta_ia)
        # Revisar hojaDeVidaListenerTopic
        await self.kafka_producer_service.send_message(validacion_match.dict(), 'hojaDeVidaValidaListenerTopic')

    async def generar_validacion_puesto(self, id_entrevista, respuesta_ia):
        # Patrones de expresiones regulares para cada sección
        patrones = {
            "validar_puesto_match": r"Validar Puesto Match: ([^\n]+)",
            "razon_validacion": r"Razón validación: ([^\n]+)"
        }
        # Extraer la información usando expresiones regulares
        datos = {key: re.search(pattern, respuesta_ia).group(1) for key, pattern in patrones.items() if
                 re.search(pattern, respuesta_ia)}
        validar_puesto_match = datos.get('validar_puesto_match', '')
        razon_validacion = datos.get('razon_validacion', '')
        # Genera boolianos de la respuesta
        if validar_puesto_match.lower() == "True".lower():
            match_valido = True
        else:
            match_valido = False
        validacion_match = Match(
            id_entrevista=id_entrevista,
            match_valido=match_valido,
            razon_validacion=razon_validacion
        )
        return validacion_match

    async def extraer_informacion_hoja_de_vida(self, formulario, id_hoja_de_vida_rag):

        hoja_de_vida = await self.hoja_de_vida_rag_repository.obtener_por_id(id_hoja_de_vida_rag)
        conversation_chain = self.generar_modelo_contexto.ejecutar(hoja_de_vida.hoja_de_vida_vect)
        predefined_questions = [
            "Analiza la siguiente hoja de vida e identifica si es adecuada para el "
            "siguiente puesto de trabajo al que se intenta aplicar: "
            f"Perfil Empresa: {formulario.perfil}"
            f"Senority: {formulario.seniority}"
            "Indica con 'True' en caso que sea adecuado y False en caso contrario. "
            "Entrega una muy breve razon de porque es o no adecuada (10 palabras). "
            "Limita tu respuesta a estas dos parametros. "
            "Ejemplo: "
            "Validar Puesto Match: True"
            "Razón validación: Motivo"
        ]
        response = conversation_chain({'question': predefined_questions[0]})

        respuesta_ia = response['chat_history'][-1].content if response['chat_history'] else ""
        # Comprobar si se extrajo algún texto
        if not respuesta_ia:
            raise HTTPException(status_code=400, detail="No se pudo generar analisis cv")
        return respuesta_ia
