from collections import defaultdict

from langchain_core.documents import Document
from langchain_unstructured import UnstructuredLoader


def load_powercenter_docs(pdf_path: str) -> list:
    loader = UnstructuredLoader(
    file_path=pdf_path,
    strategy="fast"
    )
    
    return loader.load()


def group_documents_by_page(documents: list) -> list:
    """
    Group Unstructured elements belonging to the same PDF page.
    Preserve tables as distinct blocks.
    """

    pages = defaultdict(list)
    metadata_by_page = {}

    for document in documents:
        page_number = document.metadata.get("page_number")

        if page_number is None:
            continue

        category = document.metadata.get("category")

        if category == "Table":
            content = f"\n[TABLE]\n{document.page_content}\n[/TABLE]\n"
        else:
            content = document.page_content

        pages[page_number].append(content)

        if page_number not in metadata_by_page:
            metadata_by_page[page_number] = document.metadata.copy()

    grouped_documents = []

    for page_number in sorted(pages):
        page_content = "\n\n".join(pages[page_number])

        grouped_documents.append(
            Document(
                page_content=page_content,
                metadata=metadata_by_page[page_number]
            )
        )

    return grouped_documents

def filter_content_pages(documents: list, start_page: int = 24) -> list:
    """
    Remove front matter, table of contents, and preface pages.
    Keep only technical content starting from Chapter 1.
    """

    return [
        document
        for document in documents
        if document.metadata.get("page_number", 0) >= start_page
    ]