from src.rag.databricks_loader import (
    load_databricks_docs,
)

from src.rag.databricks_splitter import (
    split_databricks_docs,
)


def main():
    documents = load_databricks_docs()

    chunks = split_databricks_docs(
        documents
    )

    print(
        f"\nDocuments: {len(documents)}"
    )

    print(
        f"Chunks: {len(chunks)}"
    )

    for index, chunk in enumerate(
        chunks[:5],
        start=1,
    ):
        print(
            f"\n{'=' * 80}"
        )

        print(
            f"CHUNK {index}"
        )

        print(
            f"{'=' * 80}"
        )

        print(
            "Metadata:",
            chunk.metadata,
        )

        print(
            "\nContent:"
        )

        print(
            chunk.page_content
        )


if __name__ == "__main__":
    main()