from langchain_chroma import Chroma


PERSIST_DIRECTORY = "data/vectorstore/powercenter"


def clean_metadata(chunks: list) -> list:
    """
    Remove complex metadata values that Chroma cannot store.
    """

    allowed_types = (
        str,
        int,
        float,
        bool,
    )

    for chunk in chunks:
        chunk.metadata = {
            key: value
            for key, value in chunk.metadata.items()
            if isinstance(
                value,
                allowed_types,
            )
        }

    return chunks


def add_document_metadata(
    chunks: list,
    version: str,
) -> list:
    """
    Add PowerCenter metadata used
    for version-aware retrieval.
    """

    for chunk in chunks:
        chunk.metadata[
            "product"
        ] = "powercenter"

        chunk.metadata[
            "version"
        ] = version

        chunk.metadata[
            "source"
        ] = "official"

        chunk.metadata[
            "document_type"
        ] = "transformation_guide"

    return chunks


def create_vectorstore(
    chunks: list,
    embeddings,
    version: str,
    persist_directory: str = PERSIST_DIRECTORY,
):
    """
    Create and persist a PowerCenter vector store.

    Args:
        chunks:
            Documentation chunks to index.

        embeddings:
            Embedding model used by Chroma.

        version:
            PowerCenter product version
            associated with the documentation.

        persist_directory:
            Directory where Chroma persists
            the vector store.
    """

    if not chunks:
        raise ValueError(
            "Cannot create PowerCenter "
            "vector store: no chunks "
            "were provided."
        )

    chunks_with_metadata = (
        add_document_metadata(
            chunks=chunks,
            version=version,
        )
    )

    clean_chunks = clean_metadata(
        chunks_with_metadata
    )

    vectorstore = Chroma.from_documents(
        documents=clean_chunks,
        embedding=embeddings,
        persist_directory=persist_directory,
    )

    return vectorstore


def load_vectorstore(
    embeddings,
    persist_directory: str = PERSIST_DIRECTORY,
):
    """
    Load an existing PowerCenter
    vector store.
    """

    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )

    return vectorstore