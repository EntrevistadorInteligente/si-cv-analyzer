from typing import Optional
from pydantic import BaseModel


class HojaDeVidaEntityRag(BaseModel):
    id_entrevista: Optional[str] = None
    hoja_de_vida_vect: Optional[list[str]] = None

