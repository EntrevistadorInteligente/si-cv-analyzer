from app.domain.repositories.hoja_de_vida_rag import HojaDeVidaRepository

class ObtenerHojaDeVida:

    def __init__(self, hoja_de_vida_repository: HojaDeVidaRepository):
        self.hoja_de_vida_rag_repository = hoja_de_vida_repository

    async def ejecutar(self, id_hoja_de_vida: str):

        text_chunks_hoja_de_vida = await self.hoja_de_vida_rag_repository.obtener_por_id(id_hoja_de_vida)

        return text_chunks_hoja_de_vida
