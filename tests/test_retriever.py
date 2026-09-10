from rag.embeddings import create_embeddings
from rag.vectorstore import load_vectorstore
from rag.retriever import retrieve_documents


def main():
    embeddings = create_embeddings()
    vectorstore = load_vectorstore(embeddings)

    query = "Filter transformation in PowerCenter"

    documents = retrieve_documents(
        vectorstore=vectorstore,
        query=query,
        k=3
    )

    for i, document in enumerate(documents):
        print(f"\n--- RESULT {i} ---")
        print(f"Page: {document.metadata.get('page_number')}")
        print(document.page_content[:700])


if __name__ == "__main__":
    main()