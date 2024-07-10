import logging

from app.application.services.extraer_pdf import ExtraerPdf
from app.application.services.generar_modelo_contexto import GenerarModeloContextoPdf
from app.infrastructure.schemas.hoja_de_vida_dto import HojaDeVidaDto
from fastapi import HTTPException
import re

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

predefined_questions = [
    "Analiza el siguiente CV y extrae la información relevante en un formato estructurado. "
    "Utiliza EXACTAMENTE las siguientes categorías y formato, sin añadir ni omitir ninguna:\n\n"
    "Nombre: [nombre completo]\n"
    "Perfil: [perfil profesional indicado en el CV]\n"
    "Seniority: [nivel de seniority indicado en el CV o inferido]\n"
    "Tecnologías principales: [tecnologías principales separadas por punto y coma (;)]\n"
    "Experiencias laborales: [experiencias laborales separadas por punto y coma (;)]\n"
    "Habilidades técnicas: [habilidades técnicas separadas por punto y coma (;)]\n"
    "Certificaciones: [certificaciones con entidad emisora separadas por punto y coma (;)]\n"
    "Proyectos: [proyectos personales con descripción breve separados por punto y coma (;)]\n"
    "Nivel de inglés: [nivel de inglés indicado en el CV]\n"
    "Otras habilidades: [otras habilidades indicadas en el CV separadas por punto y coma (;)]\n\n"
    "Instrucciones adicionales:\n"
    "- Si alguna categoría no tiene información, deja el campo vacío pero incluye la categoría.\n"
    "- Usa punto y coma (;) como separador en lugar de comas para listas.\n"
    "- Para las experiencias laborales, usa el formato: 'Puesto en Empresa, Fecha inicio - Fecha fin'\n"
    "- Si el documento no es un CV, responde solo con: 'ALERTA ROJA: El documento no es un CV.'\n"
    "- No incluyas comentarios adicionales o explicaciones fuera de las categorías especificadas."
]


def preprocesar_respuesta(respuesta):
    # Normalizar saltos de línea
    respuesta = re.sub(r'\n+', '\n', respuesta)

    # Asegurar que cada categoría esté en su propia línea
    categorias = ["Nombre:", "Perfil:", "Seniority:", "Tecnologías principales:",
                  "Experiencias laborales:", "Habilidades técnicas:", "Certificaciones:",
                  "Proyectos:", "Nivel de inglés:", "Otras habilidades:"]
    for categoria in categorias:
        respuesta = re.sub(f"({categoria})", r"\n\1", respuesta)

    # Eliminar espacios en blanco al inicio y final de cada línea
    respuesta = '\n'.join(line.strip() for line in respuesta.split('\n'))

    return respuesta


def extraer_informacion(respuesta_ia):
    respuesta_ia = preprocesar_respuesta(respuesta_ia)

    patrones = {
        "nombre": r"Nombre:(.+?)(?:\n|$)",
        "perfil": r"Perfil:(.+?)(?:\n|$)",
        "seniority": r"Seniority:(.+?)(?:\n|$)",
        "tecnologias_principales": r"Tecnologías principales:(.+?)(?:\n|$)",
        "experiencias_laborales": r"Experiencias laborales:(.*?)(?:\n(?=[A-Z])|$)",
        "habilidades_tecnicas": r"Habilidades técnicas:(.+?)(?:\n|$)",
        "certificaciones": r"Certificaciones:(.+?)(?:\n|$)",
        "proyectos": r"Proyectos:(.+?)(?:\n|$)",
        "nivel_ingles": r"Nivel de inglés:(.+?)(?:\n|$)",
        "otras_habilidades": r"Otras habilidades:(.+?)(?:\n|$)",
    }

    datos = {}
    for key, patron in patrones.items():
        match = re.search(patron, respuesta_ia, re.DOTALL | re.IGNORECASE)
        if match:
            datos[key] = match.group(1).strip()
        else:
            datos[key] = [] if key in ['tecnologias_principales', 'experiencias_laborales', 'habilidades_tecnicas',
                                       'certificaciones', 'proyectos', 'otras_habilidades'] else ""

    # Procesar listas
    for key in ['tecnologias_principales', 'habilidades_tecnicas', 'certificaciones', 'proyectos', 'otras_habilidades']:
        if datos[key] and isinstance(datos[key], str):
            datos[key] = [item.strip() for item in re.split(r'[;,]', datos[key]) if item.strip()]
        elif not isinstance(datos[key], list):
            datos[key] = []

    # Procesar experiencias laborales
    if datos['experiencias_laborales'] and isinstance(datos['experiencias_laborales'], str):
        experiencias = re.findall(r'[-•]\s*(.+?)(?=\n[-•]|\Z)', datos['experiencias_laborales'], re.DOTALL)
        datos['experiencias_laborales'] = [exp.strip() for exp in experiencias if exp.strip()]
    elif not isinstance(datos['experiencias_laborales'], list):
        datos['experiencias_laborales'] = []

    return datos


def validar_datos(datos):
    errores = []

    # Verificar campos obligatorios
    campos_obligatorios = ['nombre', 'perfil', 'seniority']
    for campo in campos_obligatorios:
        if not datos.get(campo):
            errores.append(f"Campo obligatorio '{campo}' está vacío")

    # Verificar que las listas no estén vacías
    campos_lista = ['tecnologias_principales', 'experiencias_laborales', 'habilidades_tecnicas']
    for campo in campos_lista:
        if not datos.get(campo):
            errores.append(f"La lista '{campo}' está vacía")

    # Verificar formato de experiencias laborales
    for exp in datos.get('experiencias_laborales', []):
        if not re.search(r'.+ en .+,', exp):
            errores.append(f"Formato incorrecto en experiencia laboral: {exp}")

    return errores


def extraer_con_fallback(respuesta_ia):
    datos = extraer_informacion(respuesta_ia)
    errores = validar_datos(datos)

    if errores:
        datos = extraer_informacion_agresiva(respuesta_ia)
        errores = validar_datos(datos)

        if errores:
            datos = extraer_mejor_esfuerzo(respuesta_ia)

    # Asegurarse de que los campos de lista sean siempre listas
    campos_lista = ['tecnologias_principales', 'experiencias_laborales', 'habilidades_tecnicas', 'certificaciones', 'proyectos', 'otras_habilidades']
    for campo in campos_lista:
        if not isinstance(datos.get(campo), list):
            datos[campo] = []

    return datos


def extraer_informacion_agresiva(respuesta_ia):
    datos = {}
    secciones = re.split(r'\n(?=[A-Z])', respuesta_ia)
    for seccion in secciones:
        if ':' in seccion:
            key, value = seccion.split(':', 1)
            key = key.lower().replace(' ', '_')
            if key in ['tecnologias_principales', 'experiencias_laborales', 'habilidades_tecnicas', 'certificaciones',
                       'proyectos', 'otras_habilidades']:
                datos[key] = [item.strip() for item in re.split(r'[;,]', value) if item.strip()]
            else:
                datos[key] = value.strip()
    return datos

def extraer_mejor_esfuerzo(respuesta_ia):
    datos = {}
    lineas = respuesta_ia.split('\n')
    for linea in lineas:
        if ':' in linea:
            key, value = linea.split(':', 1)
            key = key.lower().replace(' ', '_')
            if key in ['tecnologias_principales', 'experiencias_laborales', 'habilidades_tecnicas', 'certificaciones',
                       'proyectos', 'otras_habilidades']:
                datos[key] = [item.strip() for item in re.split(r'[;,]', value) if item.strip()]
            else:
                datos[key] = value.strip()
    return datos


class ProcesarPdfService:
    def __init__(self, extraer_pdf_service: ExtraerPdf, generar_modelo_contexto: GenerarModeloContextoPdf,
                 kafka_producer_service):
        self.extraer_pdf_service = extraer_pdf_service
        self.generar_modelo_contexto = generar_modelo_contexto
        self.kafka_producer_service = kafka_producer_service

    async def execute(self, username: str, contents: bytes) -> HojaDeVidaDto:
        logger.info(f"Inicio proceso de análisis de hoja de vida para el usuario {username}")
        text_chunks, id_hoja_de_vida = await self.extraer_pdf_service.ejecutar(username, contents)
        conversation_chain = await self.generar_modelo_contexto.ejecutar(text_chunks)

        response = conversation_chain({'question': predefined_questions[0]})
        respuesta_ia = response['chat_history'][-1].content if response['chat_history'] else ""

        if not respuesta_ia:
            raise HTTPException(status_code=400, detail="No se pudo generar análisis CV")

        if respuesta_ia.startswith("ALERTA ROJA"):
            raise HTTPException(status_code=400, detail="El documento no es un CV válido")

        datos = extraer_con_fallback(respuesta_ia)
        datos['id_hoja_de_vida_rag'] = id_hoja_de_vida
        datos['username'] = username

        errores_validacion = validar_datos(datos)
        if errores_validacion:
            logger.warning(f"Errores de validación: {errores_validacion}")

        try:
            hoja_de_vida_dto = HojaDeVidaDto(**datos)
        except Exception as e:
            logger.error(f"Error al validar la información extraída: {e}")
            raise HTTPException(status_code=400, detail="Error al validar la información extraída")

        return hoja_de_vida_dto

