from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.domain.entities.hoja_de_vida import HojaDeVida, HojaDeVidaFactory
from app.domain.repositories.hoja_de_vida_rag import HojaDeVidaRepository
from app.infrastructure.schemas.hoja_de_vida_entity import HojaDeVidaEntityRag
from app.infrastructure.schemas.hoja_de_vida_dto import HojaDeVidaDto

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

    async def obtener_por_id(self, id_hoja_de_vida: str) -> HojaDeVida:
        data = await collection.find_one({'_id': ObjectId(id_hoja_de_vida)})
        if data:
            return data

        else:
            raise Exception(f'HojaDeVida with id {id_hoja_de_vida} not found')