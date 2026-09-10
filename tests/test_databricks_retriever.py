from src.rag.databricks_retriever import (
    load_databricks_vectorstore,
    retrieve_databricks_documents,
)


def main():
    vectorstore = load_databricks_vectorstore()

    queries = [
        "How to read a database table using PySpark JDBC?",
        "How to transform columns using PySpark DataFrame?",
        "How to write a DataFrame to a file?",
    ]

    for query in queries:
        print("\n" + "=" * 80)
        print(f"QUERY: {query}")
        print("=" * 80)

        documents = retrieve_databricks_documents(
            vectorstore=vectorstore,
            query=query,
            k=3,
        )

        for index, document in enumerate(
            documents,
            start=1,
        ):
            print(f"\n--- RESULT {index} ---")

            print(
                "Source:",
                document.metadata.get("title"),
            )

            print(
                "URL:",
                document.metadata.get("url"),
            )

            print("\nContent:")
            print(
                document.page_content[:1000]
            )


if __name__ == "__main__":
    main()