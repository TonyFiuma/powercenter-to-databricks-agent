from langchain_chroma import Chroma


PERSIST_DIRECTORY = "data/vectorstore/powercenter"


def clean_metadata(chunks: list) -> list:
    """
    Remove complex metadata values that Chroma cannot store.
    """

    allowed_types = (str, int, float, bool)

    for chunk in chunks:
        chunk.metadata = {
            key: value
            for key, value in chunk.metadata.items()
            if isinstance(value, allowed_types)
        }

    return chunks


def create_vectorstore(chunks: list, embeddings):
    """
    Create and persist the PowerCenter vector store.
    This should be executed only during ingestion.
    """

    clean_chunks = clean_metadata(chunks)

    vectorstore = Chroma.from_documents(
        documents=clean_chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )

    return vectorstore


def load_vectorstore(embeddings):
    """
    Load an existing PowerCenter vector store.
    """

    vectorstore = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embeddings
    )

    return vectorstore