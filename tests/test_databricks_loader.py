from src.rag.databricks_loader import load_databricks_docs


def main():
    documents = load_databricks_docs()

    print(f"\nDocuments loaded: {len(documents)}")

    for index, document in enumerate(
        documents[:3],
        start=1,
    ):
        print(f"\n{'=' * 80}")
        print(f"DOCUMENT {index}")
        print(f"{'=' * 80}")

        print("\nMETADATA:")
        print(document.metadata)

        print("\nCONTENT PREVIEW:")
        print(document.page_content[:1500])


if __name__ == "__main__":
    main()