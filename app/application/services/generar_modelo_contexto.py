from typing import Any
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI


class GenerarModeloContextoPdf:
    async def ejecutar(self, text_chunks: list[str]) -> Any:
        load_dotenv()
        # Crear vectorstore
        embeddings = OpenAIEmbeddings()
        # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")

        vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)

        # Crear conversation chain
        # llm = ChatOpenAI(temperature=0)
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

        memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(),
            memory=memory
        )
        return conversation_chain
