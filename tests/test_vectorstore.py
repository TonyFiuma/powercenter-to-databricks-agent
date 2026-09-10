from rag.loader import (
    load_powercenter_docs,
    group_documents_by_page,
    filter_content_pages,
)
from rag.splitter import split_documents
from rag.embeddings import create_embeddings
from rag.vectorstore import create_vectorstore


def main():
    pdf_path = "data/docs/powercenter/PC_105_TransformationGuide_en.pdf"

    documents = load_powercenter_docs(pdf_path)
    grouped_documents = group_documents_by_page(documents)
    content_documents = filter_content_pages(grouped_documents)
    chunks = split_documents(content_documents)

    print(f"Chunks created: {len(chunks)}")

    embeddings = create_embeddings()

    vectorstore = create_vectorstore(
        chunks=chunks,
        embeddings=embeddings
    )

    print("Vector store created successfully.")

    query = "How does a Filter transformation work?"

    results = vectorstore.similarity_search(
        query,
        k=3
    )

    print("\nSearch results:\n")

    for i, document in enumerate(results):
        print(f"--- RESULT {i} ---")
        print(f"Page: {document.metadata.get('page_number')}")
        print(document.page_content[:700])
        print()


if __name__ == "__main__":
    main()