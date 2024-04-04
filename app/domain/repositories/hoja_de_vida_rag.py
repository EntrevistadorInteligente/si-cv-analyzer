from abc import ABC, abstractmethod

from app.domain.entities.hoja_de_vida import HojaDeVida


class HojaDeVidaRepository(ABC):

    @abstractmethod
    def add(self,  hoja_de_vida: HojaDeVida) -> str:
        raise NotImplemented

