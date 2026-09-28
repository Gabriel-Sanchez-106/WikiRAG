import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
load_dotenv()

RUTA_DB = Path(os.getenv("RUTA_DB", ".data/warframe_db"))

MODELO_GPT = os.getenv("MODELO_GPT" , "gpt-4.1-nano")
MODELO_HF = os.getenv("MODELO_HF", "all-MiniLM-L6-v2")


# --------------------------------------------------
# Embeding y DB
# --------------------------------------------------

embeddings = HuggingFaceEmbeddings(
    model_name= MODELO_HF
)

vectorstore = Chroma(
    persist_directory=str(RUTA_DB),
    embedding_function=embeddings
)


# --------------------------------------------------
# Retriever básico
# --------------------------------------------------

retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 10
    }
)


# --------------------------------------------------
# LLM
# --------------------------------------------------

llm = ChatOpenAI(
    model = MODELO_GPT,
    temperature= 0.2
)


def preguntar(pregunta: str) -> str:

    documentos = retriever.invoke(
        pregunta
    )

    contexto = "\n\n".join(
        doc.page_content
        for doc in documentos
    )

    prompt = f"""
You are a Warframe expert assistant.

Answer the user's question using the provided
Warframe Wiki context.

If the answer cannot be found in the context,
say that the information was not found.

Do not invent Warframe mechanics, stats,
drop locations or requirements.

CONTEXT:

{contexto}

USER QUESTION:

{pregunta}
"""

    respuesta = llm.invoke(prompt)

    return respuesta.content
