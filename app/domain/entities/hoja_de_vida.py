import uuid
from app.domain.exceptions import PriceIsLessThanOrEqualToZero, StockIsLessThanOrEqualToZero


class HojaDeVida:

    def __init__(self, id_entrevista: str, hoja_de_vida_vect: list[str]):
        self.__validate_price(id_entrevista)
        self.__validate_stock(hoja_de_vida_vect)

        self.id_entrevista = id_entrevista
        self.hoja_de_vida_vect = hoja_de_vida_vect

    @staticmethod
    def __validate_price(id_entrevista: str):
        if not id_entrevista:
            raise PriceIsLessThanOrEqualToZero

    @staticmethod
    def __validate_stock(hoja_de_vida_vect: list[str]):
        if hoja_de_vida_vect.__sizeof__() <= 0:
            raise StockIsLessThanOrEqualToZero


class HojaDeVidaFactory:

    @staticmethod
    def create(id_entrevista: str, hoja_de_vida_vect: list[str]) -> HojaDeVida:
        return HojaDeVida(id_entrevista, hoja_de_vida_vect)
