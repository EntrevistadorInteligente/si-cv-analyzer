from typing import List, Optional
from pydantic import BaseModel
from enum import Enum


class HojaDeVidaDto(BaseModel):
    nombre: Optional[str] = None
    perfil: Optional[str] = None
    seniority: Optional[str] = None
    tecnologias_principales: List[str] = []
    experiencias_laborales: List[str] = []
    habilidades_tecnicas: List[str] = []
    certificaciones: List[str] = []
    proyectos: List[str] = []
    nivel_ingles: Optional[str] = None
    otras_habilidades: List[str] = []
    alertas: Optional[str] = None


class PreparacionEntrevistaDto(BaseModel):
    id_entrevista: Optional[str] = None
    evento_entrevista_id: Optional[str] = None
    hoja_de_vida: Optional[bytes] = None


class EstadoProcesoEnum(str, Enum):
    AC = "AC"
    CVA = "CVA"
    FN = "FN"


class ProcesoEntrevistaDto(BaseModel):
    uuid: Optional[str] = None
    estado: EstadoProcesoEnum
    fuente: Optional[str] = None
    error: Optional[str] = None


class MensajeAnalizadorDto(BaseModel):
    proceso_entrevista: ProcesoEntrevistaDto
    id_entrevista: Optional[str] = None,
    hoja_de_vida: HojaDeVidaDto


