from src.rag.databricks_loader import (
    load_databricks_docs,
)

from src.rag.databricks_splitter import (
    split_databricks_docs,
)

from src.rag.databricks_vectorstore import (
    create_databricks_vectorstore,
)


def main():
    documents = load_databricks_docs()

    chunks = split_databricks_docs(
        documents
    )

    vectorstore = (
        create_databricks_vectorstore(
            chunks
        )
    )

    print(
        "\nVectorstore ready."
    )


if __name__ == "__main__":
    main()