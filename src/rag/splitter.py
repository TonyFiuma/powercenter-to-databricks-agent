from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documents: list) -> list:
    """
    Split LangChain documents into smaller chunks.
    """

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=[
            "\n[TABLE]\n",
            "\n[/TABLE]\n",
            "\n\n",
            "\n",
            " ",
            ""
        ]
    )

    return text_splitter.split_documents(documents)