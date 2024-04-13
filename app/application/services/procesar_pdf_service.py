from app.application.services.extraer_pdf import ExtraerPdf
from app.application.services.generar_modelo_contexto import GenerarModeloContextoPdf
from app.infrastructure.schemas.hoja_de_vida_dto import HojaDeVidaDto
from fastapi import HTTPException
import re

predefined_questions = [
    "Analiza el siguiente CV y extrae la información relevante en un formato estructurado con las siguientes "
    "categorías:nombre, perfil profesional, seniority, tecnologías principales, experiencias laborales "
    "(incluyendo título del puesto, nombre de la empresa y fechas de inicio y fin), habilidades técnicas, "
    "certificaciones (con entidad emisora), proyectos (con descripción breve), nivel de inglés y otras habilidades. "
    "Suprime cualquier comentario subjetivo o valoración personal y enfócate en los datos objetivos. "
    "Si el CV tiene un formato visual complejo, contiene muchas gráficas o no es una hoja de vida , "
    "indica 'ALERTA ROJA'. las Experiencias laborales separarlas por comas no numericamente"
    "Maqueta respuesta NO CAMBIAR USA ESTOS MISMOS CAMPOS:"
    "Nombre: Jamilton Quintero "
    "Perfil: Full stack developer con experiencia en Java, Spring Boot, Docker, entre otros."
    "Seniority: Senior "
    "Tecnologías principales: Java, Spring Boot, Docker, Kubernetes, Azure, .NET, Angular."
    "Experiencias laborales: Apiux Tecnología - Senior back-end developer / abril de 2023 - Presente."
    "Ceiba Software - ARCHITECT DEVELOPER/ mayo de 2022 - abril de 2023."
    "Habilidades técnicas: Desarrollo con Java Spring Boot, Angular, manejo de Docker y Kubernetes, CI/CD con Jenkins."
    "Certificaciones: Curso de Java SE, Diplomado en Java, Curso de Kotlin para Android, Desarrollo con Android, "
    "Curso de Bases Técnicas de Android. "
    "Proyectos: Sistema de recomendación de productos con IA, canal de YouTube sobre desarrollo en Java."
    "Nivel de inglés: B2 intermedio-avanzado"
    "Otras habilidades: Liderazgo de equipos, enseñanza técnica."
]


class ProcesarPdfService:

    def __init__(self, extraer_pdf_service: ExtraerPdf,
                 generar_modelo_contexto: GenerarModeloContextoPdf,
                 kafka_producer_service) -> HojaDeVidaDto:
        self.extraer_pdf_service = extraer_pdf_service
        self.generar_modelo_contexto = generar_modelo_contexto
        self.kafka_producer_service = kafka_producer_service

    async def execute(self, username: str, contents: bytes) -> HojaDeVidaDto:
        text_chunks, id_hoja_de_vida = await self.extraer_pdf_service.ejecutar(username, contents)
        conversation_chain = self.generar_modelo_contexto.ejecutar(text_chunks)

        response = conversation_chain({'question': predefined_questions[0]})
        respuesta_ia = response['chat_history'][-1].content if response['chat_history'] else ""

        # Comprobar si se extrajo algún texto
        if not respuesta_ia:
            raise HTTPException(status_code=400, detail="No se pudo generar analisis cv")

        # Patrones de expresiones regulares para cada sección
        patrones = {
            "nombre": r"Nombre: ([^\n]+)",
            "perfil": r"Perfil: ([^\n]+)",
            "seniority": r"Seniority: ([^\n]+)",
            "tecnologias_principales": r"Tecnologías principales: ([^\n]+)",
            "experiencias_laborales": r"Experiencias laborales: ([^\n]+)",
            "habilidades_tecnicas": r"Habilidades técnicas: ([^\n]+)",
            "certificaciones": r"Certificaciones: ([^\n]+)",
            "proyectos": r"Proyectos: ([^\n]+)",
            "nivel_ingles": r"Nivel de inglés: ([^\n]+)",
            "otras_habilidades": r"Otras habilidades: ([^\n]+)",
        }

        # Extraer la información usando expresiones regulares
        datos = {key: re.search(pattern, respuesta_ia).group(1) for key, pattern in patrones.items() if
                 re.search(pattern, respuesta_ia)}

        datos['id_hoja_de_vida_rag'] = id_hoja_de_vida
        # Procesamiento especial para secciones que contienen listas o varios elementos
        datos['tecnologias_principales'] = datos.get('tecnologias_principales', '').split(', ')
        datos['habilidades_tecnicas'] = datos.get('habilidades_tecnicas', '').split(', ')

        # Ejemplo simple basado en el formato proporcionado
        # Nota: Esto puede requerir una lógica más compleja si el formato varía
        datos['experiencias_laborales'] = datos.get('experiencias_laborales', '').split(', ')

        datos['proyectos'] = datos.get('proyectos', '').split(', ')
        datos['certificaciones'] = datos.get('certificaciones', '').split(', ')
        # Asegurarse de que todas las habilidades se conviertan en una lista
        otras_habilidades = datos.get('otras_habilidades', '')
        if otras_habilidades:
            datos['otras_habilidades'] = [hab.strip() for hab in otras_habilidades.split(',')]

        datos['username'] = username
        # Construir el DTO
        try:
            hoja_de_vida_dto = HojaDeVidaDto(**datos)
        except HTTPException as e:
            print("Error al validar la información extraída:", e)
            # Manejar el error o crear una respuesta por defecto si es necesario
            hoja_de_vida_dto = HojaDeVidaDto()

        await self.kafka_producer_service.send_message(hoja_de_vida_dto.dict(), 'hojaDeVidaListenerTopic')



