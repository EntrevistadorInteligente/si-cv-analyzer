import uuid
from app.domain.exceptions import PriceIsLessThanOrEqualToZero, StockIsLessThanOrEqualToZero


class HojaDeVida:

    def __init__(self, username: str, hoja_de_vida_vect: list[str]):
        self.__validate_price(username)
        self.__validate_stock(hoja_de_vida_vect)

        self.username = username
        self.hoja_de_vida_vect = hoja_de_vida_vect

    @staticmethod
    def __validate_price(username: str):
        if not username:
            raise PriceIsLessThanOrEqualToZero

    @staticmethod
    def __validate_stock(hoja_de_vida_vect: list[str]):
        if hoja_de_vida_vect.__sizeof__() <= 0:
            raise StockIsLessThanOrEqualToZero


class HojaDeVidaFactory:

    @staticmethod
    def create(username: str, hoja_de_vida_vect: list[str]) -> HojaDeVida:
        return HojaDeVida(username, hoja_de_vida_vect)
