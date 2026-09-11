from pathlib import Path
import shutil

import pikepdf
from langchain_unstructured import UnstructuredLoader

from rag.loader import (
    group_documents_by_page,
    filter_content_pages,
)
from rag.splitter import split_documents
from rag.embeddings import create_embeddings
from rag.vectorstore import create_vectorstore


def create_test_pdf(
    source_pdf: str,
    output_pdf: str,
    start_page: int = 24,
    num_pages: int = 5,
):
    """
    Create a small PDF containing only a subset
    of pages from the original PowerCenter guide.

    This avoids processing the full documentation
    during local ingestion tests.
    """

    with pikepdf.open(source_pdf) as source:
        destination = pikepdf.Pdf.new()

        start_index = start_page - 1
        end_index = start_index + num_pages

        destination.pages.extend(
            source.pages[start_index:end_index]
        )

        destination.save(output_pdf)


def main():
    # --------------------------------------------------
    # Paths
    # --------------------------------------------------

    source_pdf = (
        "data/docs/powercenter/"
        "PC_105_TransformationGuide_en.pdf"
    )

    test_pdf = (
        "data/docs/powercenter/"
        "test_powercenter_5_pages.pdf"
    )

    test_vectorstore_path = (
        "data/vectorstore/test_powercenter"
    )

    # --------------------------------------------------
    # 1. Create small test PDF
    # --------------------------------------------------

    create_test_pdf(
        source_pdf=source_pdf,
        output_pdf=test_pdf,
        start_page=24,
        num_pages=5,
    )

    print(
        f"Test PDF created: {test_pdf}"
    )

    # --------------------------------------------------
    # 2. Load PDF with Unstructured
    # --------------------------------------------------

    loader = UnstructuredLoader(
        file_path=test_pdf,
        strategy="auto",
    )

    documents = loader.load()

    print(
        f"Raw documents loaded: "
        f"{len(documents)}"
    )

    if not documents:
        raise ValueError(
            "No documents were loaded."
        )

    # --------------------------------------------------
    # 3. Group elements by page
    # --------------------------------------------------

    grouped_documents = (
        group_documents_by_page(
            documents
        )
    )

    print(
        f"Grouped documents: "
        f"{len(grouped_documents)}"
    )

    # The temporary PDF starts from page 1,
    # therefore we use start_page=1 here.
    content_documents = (
        filter_content_pages(
            grouped_documents,
            start_page=1,
        )
    )

    print(
        f"Content documents: "
        f"{len(content_documents)}"
    )

    # --------------------------------------------------
    # 4. Split pages into chunks
    # --------------------------------------------------

    chunks = split_documents(
        content_documents
    )

    print(
        f"Chunks created: "
        f"{len(chunks)}"
    )

    if not chunks:
        raise ValueError(
            "No chunks were created."
        )

    # --------------------------------------------------
    # 5. Create embeddings
    # --------------------------------------------------

    embeddings = create_embeddings()

    # --------------------------------------------------
    # 6. Clean previous test vector store
    # --------------------------------------------------

    test_vectorstore = Path(
        test_vectorstore_path
    )

    if test_vectorstore.exists():
        shutil.rmtree(
            test_vectorstore
        )

        print(
            "Previous test vector store removed."
        )

    # --------------------------------------------------
    # 7. Create isolated test vector store
    # --------------------------------------------------

    vectorstore = create_vectorstore(
        chunks=chunks,
        embeddings=embeddings,
        version="10.5.7",
        persist_directory=test_vectorstore_path,
    )

    print(
        "Test vector store created successfully."
    )

    # --------------------------------------------------
    # 8. Perform version-aware retrieval
    # --------------------------------------------------

    query = (
        "How do PowerCenter "
        "transformations work?"
    )

    metadata_filter = {
        "$and": [
            {
                "product": {
                    "$eq": "powercenter"
                }
            },
            {
                "version": {
                    "$eq": "10.5.7"
                }
            },
        ]
    }

    results = vectorstore.similarity_search(
        query=query,
        k=3,
        filter=metadata_filter,
    )

    print(
        "\nFiltered search results:\n"
    )

    if not results:
        raise ValueError(
            "No documents found using "
            "PowerCenter version filter."
        )

    # --------------------------------------------------
    # 9. Validate retrieved metadata
    # --------------------------------------------------

    for i, document in enumerate(
        results
    ):
        print(
            f"--- RESULT {i} ---"
        )

        print(
            "Page:",
            document.metadata.get(
                "page_number"
            ),
        )

        print(
            "Product:",
            document.metadata.get(
                "product"
            ),
        )

        print(
            "Version:",
            document.metadata.get(
                "version"
            ),
        )

        print(
            "Source:",
            document.metadata.get(
                "source"
            ),
        )

        print(
            "Document type:",
            document.metadata.get(
                "document_type"
            ),
        )

        print(
            document.page_content[:500]
        )

        print()

        assert (
            document.metadata.get(
                "product"
            )
            == "powercenter"
        )

        assert (
            document.metadata.get(
                "version"
            )
            == "10.5.7"
        )

        assert (
            document.metadata.get(
                "source"
            )
            == "official"
        )

        assert (
            document.metadata.get(
                "document_type"
            )
            == "transformation_guide"
        )

    print(
        "Version-aware retrieval test PASSED."
    )


if __name__ == "__main__":
    main()