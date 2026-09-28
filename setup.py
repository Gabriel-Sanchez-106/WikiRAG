import os
from pathlib import Path
import shutil

from langchain_community.document_loaders import MWDumpLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from dotenv import load_dotenv
from aux_funcs import analizar_documentos, guardar_documentos, cargar_documentos_filtrados, filtrar_documentos

load_dotenv()

RUTA_XML = Path(os.getenv("RUTA_XML", ".data/warframe.xml"))
RUTA_FILTRADA = Path(os.getenv("RUTA_FILTRADA", ".data/warframe_filtrada.jsonl"))
RUTA_DB = Path(os.getenv("RUTA_DB", ".data/warframe_db"))

MODELO_HF = os.getenv("MODELO_HF", "all-MiniLM-L6-v2")

print("="*50)
print("===== HERRAMIENTA DE GENERACIÓN VECTORIAL_DB =====")
print("="*50)


try:

    if RUTA_FILTRADA.exists():
        print(f"\nArchivo filtrado encontrado:" 
              f"\n{RUTA_FILTRADA}")
        
        documentos = cargar_documentos_filtrados(
                        RUTA_FILTRADA)
            
        print( f"\nDocumentos cargados: "
            f"{len(documentos):,}")

    else:
        print("No existe dataset filtrado.\n")

        print("Cargando y parseando XML original...")

        loader = MWDumpLoader(
            file_path=RUTA_XML,
            encoding="utf8",
            skip_redirects=True,
            stop_on_error=False
        )

        documentos = loader.load()

        print(
            f"\nDocumentos originales: "
            f"{len(documentos):,}"
        )

        analizar_documentos(
            documentos
        )

        documentos = filtrar_documentos(
            documentos
        )

        guardar_documentos(
            documentos,
            RUTA_FILTRADA
        )
            

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    chunks = text_splitter.split_documents(documentos)

    print(f"*Chunks generados: {len(chunks):,}")

    if len(chunks) > 100_000:
        raise ValueError(
            f"Demasiados chunks ({len(chunks):,}). "
            "Revisar el filtrado antes de vectorizar."
        )

    print("\nEjemplo de chunk:")
    print(chunks[0].page_content[:500])
    print("\nMetadata:")
    print(chunks[0].metadata)


    if RUTA_DB.exists():
        print("Eliminando base vectorial anterior...")
        shutil.rmtree(RUTA_DB)


    print("\nVectorizando los chunks obtenidos...")

    embeddings = HuggingFaceEmbeddings(
        model_name= MODELO_HF
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(RUTA_DB)
    )

    print("\n----- Vectorización finalizada exitosamente -----")
    print("-" * 50)


except FileNotFoundError as e:
    print(f"ERROR: No se encontró el archivo de la Wiki: {e}")

except UnicodeDecodeError as e:
    print(f"ERROR: Problema de codificación del XML: {e}")

except PermissionError as e:
    print(f"ERROR: No hay permisos para acceder a un archivo/directorio: {e}")

except OSError as e:
    print(f"ERROR del sistema de archivos: {e}")

except ValueError as e:
    print(f"ERROR de datos/parámetros: {e}")

except ImportError as e:
    print(f"ERROR: Falta una dependencia: {e}")

except Exception as e:
    print(f"ERROR inesperado: {type(e).__name__}: {e}")
    raise
    

print("="*50)
print("===== PROCESO FINALIZADO =====")
print("="*50)