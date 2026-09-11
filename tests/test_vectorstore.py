from rag.loader import (
    load_powercenter_docs,
    group_documents_by_page,
    filter_content_pages,
)
from rag.splitter import split_documents
from rag.embeddings import create_embeddings
from rag.vectorstore import create_vectorstore
from pathlib import Path
import shutil


def main():
    pdf_path = (
        "data/docs/powercenter/"
        "PC_105_TransformationGuide_en.pdf"
    )

    # 1. Load PDF
    documents = load_powercenter_docs(
        pdf_path
    )

    print(
        f"Raw documents loaded: "
        f"{len(documents)}"
    )

    # 2. Group by page
    grouped_documents = (
        group_documents_by_page(
            documents
        )
    )

    print(
        f"Grouped documents: "
        f"{len(grouped_documents)}"
    )

    # 3. Remove non-content pages
    content_documents = (
        filter_content_pages(
            grouped_documents
        )
    )

    print(
        f"Content documents: "
        f"{len(content_documents)}"
    )

    # 4. Split into chunks
    chunks = split_documents(
        content_documents
    )

    print(
        f"Chunks created: "
        f"{len(chunks)}"
    )

    # Stop here if ingestion failed
    if not chunks:
        raise ValueError(
            "No chunks were created. "
            "Vector store creation aborted."
        )

    # 5. Embeddings
    embeddings = create_embeddings()

    vectorstore_path = Path(
    "data/vectorstore/powercenter"
    )

    if vectorstore_path.exists():
        shutil.rmtree(
        vectorstore_path
        )

    print(
        "Previous PowerCenter vector store removed."
    )
    # 6. Create vector store
    vectorstore = create_vectorstore(
        chunks=chunks,
        embeddings=embeddings,
        version="10.5.7",
    )

    print(
        "Vector store created successfully."
    )

    # 7. Test search
    query = (
        "How does a Filter "
        "transformation work?"
    )

    results = vectorstore.similarity_search(
        query,
        k=3,
    )

    print("\nSearch results:\n")

    for i, document in enumerate(results):
        print(f"--- RESULT {i} ---")

        print(
            "Page: "
            f"{document.metadata.get('page_number')}"
        )

        print(
            "Product: "
            f"{document.metadata.get('product')}"
        )

        print(
            "Version: "
            f"{document.metadata.get('version')}"
        )

        print(
            "Source: "
            f"{document.metadata.get('source')}"
        )

        print(
            "Document type: "
            f"{document.metadata.get('document_type')}"
        )

        print(
            document.page_content[:700]
        )

        print()


if __name__ == "__main__":
    main()