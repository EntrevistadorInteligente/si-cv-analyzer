from abc import ABC, abstractmethod
from app.domain.entities.hoja_de_vida import HojaDeVida


class HojaDeVidaRepository(ABC):

    @abstractmethod
    async def add(self,  hoja_de_vida: HojaDeVida) -> str:
        raise NotImplemented

    @abstractmethod
    async def obtener_por_id(self, id_hoja_de_vida: str) -> HojaDeVida:
        raise NotImplemented
