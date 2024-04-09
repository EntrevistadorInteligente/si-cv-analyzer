from abc import ABC, abstractmethod
from app.domain.entities.hoja_de_vida import HojaDeVida
from app.infrastructure.schemas.hoja_de_vida_dto import HojaDeVidaDto


class HojaDeVidaRepository(ABC):

    @abstractmethod
    def add(self,  hoja_de_vida: HojaDeVida) -> str:
        raise NotImplemented

    @abstractmethod
    def obtener_por_id(self, id_hoja_de_vida: str) -> HojaDeVida:
        raise NotImplemented