from rag.loader import (
    load_powercenter_docs,
    group_documents_by_page,
    filter_content_pages,
)
from rag.splitter import split_documents


def main():
    pdf_path = "data/docs/powercenter/PC_105_TransformationGuide_en.pdf"

    documents = load_powercenter_docs(pdf_path)
    print(f"Raw elements loaded: {len(documents)}")

    grouped_documents = group_documents_by_page(documents)
    print(f"Pages created: {len(grouped_documents)}")

    content_documents = filter_content_pages(grouped_documents)
    print(f"Content pages after filtering: {len(content_documents)}")

    chunks = split_documents(content_documents)
    print(f"Chunks created: {len(chunks)}")

    print("\nFirst 10 chunks:\n")

    for i, chunk in enumerate(chunks[:10]):
        print(f"--- CHUNK {i} ---")
        print(f"Page: {chunk.metadata.get('page_number')}")
        print(f"Length: {len(chunk.page_content)}")
        print(chunk.page_content[:500])
        print()


if __name__ == "__main__":
    main()