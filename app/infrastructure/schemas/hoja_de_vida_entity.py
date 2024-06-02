from typing import Optional
from pydantic import BaseModel


class HojaDeVidaEntityRag(BaseModel):
    username: Optional[str] = None
    hoja_de_vida_vect: Optional[list[str]] = None

