from langchain_chroma import Chroma

from src.rag.embeddings import create_embeddings


VECTORSTORE_PATH = "data/vectorstore/databricks"


def load_databricks_vectorstore() -> Chroma:
    embeddings = create_embeddings()

    return Chroma(
        persist_directory=VECTORSTORE_PATH,
        embedding_function=embeddings,
    )


def retrieve_databricks_documents(
    vectorstore: Chroma,
    query: str,
    k: int = 5,
):
    return vectorstore.similarity_search(
        query=query,
        k=k,
    )