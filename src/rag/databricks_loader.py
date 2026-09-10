import requests

from bs4 import BeautifulSoup
from langchain_core.documents import Document

from src.rag.databricks_sources import (
    DATABRICKS_SOURCES,
)


def load_databricks_docs() -> list[Document]:
    documents = []

    for source in DATABRICKS_SOURCES:
        print(
            f"Loading Databricks documentation: "
            f"{source['title']}"
        )

        response = requests.get(
            source["url"],
            timeout=30,
        )

        response.raise_for_status()

        # Detect the correct encoding of the web page
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        for tag in soup.find_all(
            [
            "nav",
            "header",
            "footer",
            "script",
            "style",
            "aside",
            ]
        ):
            tag.decompose()

        text = soup.get_text(
            separator="\n",
            strip=True,
        )

        document = Document(
            page_content=text,
            metadata={
                "source": "databricks",
                "source_name": source["name"],
                "title": source["title"],
                "category": source["category"],
                "url": source["url"],
            },
        )

        documents.append(document)

    print(
        f"\nDatabricks documents loaded: "
        f"{len(documents)}"
    )

    return documents