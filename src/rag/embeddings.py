from langchain_huggingface import (
    HuggingFaceEmbeddings,
)


def create_embeddings():
    """
    Create the embedding model used by the local
    Chroma vector stores.

    The project uses:
    sentence-transformers/all-MiniLM-L6-v2

    Embedding dimension:
    384

    local_files_only=True prevents Hugging Face from
    performing network calls when the model is already
    available in the local cache.
    """

    embeddings = HuggingFaceEmbeddings(
        model_name=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        ),
        model_kwargs={
            "local_files_only": True,
        },
    )

    return embeddings