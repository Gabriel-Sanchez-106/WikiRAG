import json
from collections import Counter
from langchain_core.documents import Document

NAMESPACES_PERMITIDOS = {
    "MAIN",
    "Conclave",
    "Operation",
    "Map",
    "GHOULS",
    "WARFRAME",
    "Gradivus",
    "Warframe 1999",
    "Nightwave/Template",
}


def obtener_namespace(source):

    if ":" in source:
        return source.split(":", 1)[0]

    return "MAIN"

def analizar_documentos(documentos):

    namespaces = Counter()

    for doc in documentos:

        source = doc.metadata.get(
            "source",
            ""
        )

        namespace = obtener_namespace(source)

        namespaces[namespace] += 1

    print("\nNamespaces:")

    for namespace, cantidad in namespaces.most_common():

        print(
            f"{namespace:25} {cantidad:,}"
        )

def filtrar_documentos(documentos):

    documentos_filtrados = []

    eliminados_namespace = 0
    eliminados_vacios = 0
    eliminados_cortos = 0

    for doc in documentos:

        source = doc.metadata.get(
            "source",
            ""
        )

        texto = doc.page_content.strip()

        namespace = obtener_namespace(source)


        if namespace not in NAMESPACES_PERMITIDOS:

            eliminados_namespace += 1
            continue


        if not texto:

            eliminados_vacios += 1
            continue


        if len(texto) < 100:

            eliminados_cortos += 1
            continue

        documentos_filtrados.append(doc)

    print("\n===== FILTRADO =====")

    print(
        f"Conservados:          "
        f"{len(documentos_filtrados):,}"
    )

    print(
        f"Eliminados namespace:  "
        f"{eliminados_namespace:,}"
    )

    print(
        f"Eliminados vacíos:     "
        f"{eliminados_vacios:,}"
    )

    print(
        f"Eliminados cortos:     "
        f"{eliminados_cortos:,}"
    )

    return documentos_filtrados

def guardar_documentos(documentos, ruta):

    print(
        f"\nGuardando documentos filtrados en:"
        f"\n{ruta}"
    )

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as f:

        for doc in documentos:

            registro = {
                "page_content": doc.page_content,
                "metadata": doc.metadata
            }

            f.write(
                json.dumps(
                    registro,
                    ensure_ascii=False
                )
                + "\n"
            )

    print("Guardado correctamente.")

def cargar_documentos_filtrados(ruta):

    documentos = []

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as f:

        for linea in f:

            registro = json.loads(linea)

            documentos.append(
                Document(
                    page_content=registro["page_content"],
                    metadata=registro["metadata"]
                )
            )

    return documentos
