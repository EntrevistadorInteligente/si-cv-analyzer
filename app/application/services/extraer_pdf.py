import base64

from PyPDF2 import PdfReader
import io
from fastapi import HTTPException
from langchain.text_splitter import CharacterTextSplitter


class ExtraerPdf:
    def ejecutar(self, contents: bytes) -> list[str]:
        decoded_bytes = base64.b64decode(contents)

        pdf_reader = PdfReader(io.BytesIO(decoded_bytes))

        # Extraer texto del PDF
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""

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
        return text_chunks
