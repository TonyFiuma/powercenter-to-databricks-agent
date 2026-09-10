from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from langchain_core.documents import Document


def split_databricks_docs(
    documents: list[Document],
) -> list[Document]:
    """
    Split Databricks documentation into chunks
    suitable for embedding and retrieval.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
        ],
    )

    chunks = splitter.split_documents(
        documents
    )

    print(
        f"Databricks chunks created: "
        f"{len(chunks)}"
    )

    return chunks