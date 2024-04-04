from motor.motor_asyncio import AsyncIOMotorClient

from app.domain.entities.hoja_de_vida import HojaDeVida, HojaDeVidaFactory
from app.domain.repositories.hoja_de_vida_rag import HojaDeVidaRepository
from app.infrastructure.schemas.hoja_de_vida_entity import HojaDeVidaEntityRag

# MongoDB connection URL
MONGO_URL = "mongodb://root:secret@localhost:27017/"
client = AsyncIOMotorClient(MONGO_URL)
database = client["analizador_hoja_vida_rag"]
collection = database["hoja_vida"]


class HojaDeVidaMongoRepository(HojaDeVidaRepository):

    async def add(self, hoja_de_vida: HojaDeVida) -> str:
        proceso_entrevista = HojaDeVidaEntityRag(
            id_entrevista=hoja_de_vida.id_entrevista,
            hoja_de_vida_vect=hoja_de_vida.hoja_de_vida_vect
        )
        result = await collection.insert_one(proceso_entrevista.dict())
        return str(result.inserted_id)
