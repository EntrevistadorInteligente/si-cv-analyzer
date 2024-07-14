import base64
import pypdfium2 as pdfium
import io
from fastapi import HTTPException
from langchain.text_splitter import CharacterTextSplitter

from app.domain.entities.hoja_de_vida import HojaDeVidaFactory
from app.domain.repositories.hoja_de_vida_rag import HojaDeVidaRepository


class ExtraerPdf:

    def __init__(self, hoja_de_vida_rag_repository: HojaDeVidaRepository):
        self.hoja_de_vida_rag_repository = hoja_de_vida_rag_repository

    async def ejecutar(self, username: str, contents: bytes) -> tuple[list[str], str]:

        decoded_bytes = base64.b64decode(contents)

        # Utilizar pypdfium2 para leer el archivo PDF
        pdf_document = pdfium.PdfDocument(io.BytesIO(decoded_bytes))

        # Extraer texto del PDF
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            textpage = page.get_textpage()
            width, height = page.get_size()
            text += textpage.get_text_bounded(left=0, bottom=0, right=width, top=height)

        # Comprobar si se extrajo algún texto
        if not text:
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF")

        # Dividir el texto en chunks
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=800,
            chunk_overlap=50,
            length_function=len
        )

        text_chunks = text_splitter.split_text(text)

        id_hoja_de_vida = await (self.hoja_de_vida_rag_repository.
                                 add(HojaDeVidaFactory.create(username, text_chunks)))

        return text_chunks, id_hoja_de_vida