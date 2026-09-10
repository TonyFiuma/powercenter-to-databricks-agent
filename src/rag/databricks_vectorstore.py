from langchain_chroma import Chroma

from src.rag.embeddings import create_embeddings


VECTORSTORE_PATH = "data/vectorstore/databricks"


def create_databricks_vectorstore(
    chunks,
) -> Chroma:
    embeddings = create_embeddings()

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTORSTORE_PATH,
    )

    print(
        f"Databricks vectorstore created at: "
        f"{VECTORSTORE_PATH}"
    )

    return vectorstore