from langchain_core.tools import tool

from rag.embeddings import create_embeddings
from rag.vectorstore import load_vectorstore
from rag.retriever import retrieve_documents


embeddings = create_embeddings()
vectorstore = load_vectorstore(embeddings)


@tool
def search_powercenter_documentation(query: str) -> str:
    """
    Search the PowerCenter documentation for information
    relevant to the given query.
    """

    documents = retrieve_documents(
        vectorstore=vectorstore,
        query=query,
        k=3
    )

    results = []

    for document in documents:
        page = document.metadata.get("page_number")
        content = document.page_content

        results.append(
            f"Page {page}\n{content}"
        )

    return "\n\n---\n\n".join(results)