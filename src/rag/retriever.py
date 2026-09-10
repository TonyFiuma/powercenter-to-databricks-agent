from langchain_chroma import Chroma

from src.rag.embeddings import create_embeddings


VECTORSTORE_PATH = "data/vectorstore/powercenter"


def load_vectorstore() -> Chroma:
    """
    Load the persisted PowerCenter Chroma vector store.
    """

    embeddings = create_embeddings()

    vectorstore = Chroma(
        persist_directory=VECTORSTORE_PATH,
        embedding_function=embeddings,
    )

    return vectorstore


def retrieve_documents(vectorstore, query: str, k: int = 3):
    """
    Retrieve and rerank PowerCenter documentation chunks.
    """

    candidates = vectorstore.similarity_search(
        query=query,
        k=30,
    )

    query_lower = query.lower()

    known_transformations = [
        "filter",
        "expression",
        "aggregator",
        "router",
        "joiner",
        "sorter",
        "lookup",
        "rank",
        "source qualifier",
    ]

    transformation_name = None

    for name in known_transformations:
        if name in query_lower:
            transformation_name = name
            break

    def rerank_score(document):
        """
        Rank documentation chunks based on how closely they match
        the requested PowerCenter transformation.
        """

        text = document.page_content.lower()

        score = 0

        if transformation_name:
            exact_phrase = f"{transformation_name} transformation"

            if exact_phrase in text:
                score += 20

            score += text.count(exact_phrase) * 5
            score += text.count(transformation_name) * 2

            if f"{exact_phrase} overview" in text:
                score += 15

            if f"configuring {exact_phrase}" in text:
                score += 15

            if f"creating {exact_phrase}" in text:
                score += 10

        if "powercenter" in text:
            score += 1

        if (
            transformation_name == "source qualifier"
            and "xml source qualifier" in text
        ):
            score -= 30

        if (
            transformation_name == "expression"
            and "java expression" in text
        ):
            score -= 20

        return score

    reranked = sorted(
        candidates,
        key=rerank_score,
        reverse=True,
    )

    return reranked[:k]