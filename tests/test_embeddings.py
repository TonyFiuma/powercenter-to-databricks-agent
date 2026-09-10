from rag.embeddings import create_embeddings


def main():
    embeddings = create_embeddings()

    text = "The Filter transformation filters rows based on a condition."

    vector = embeddings.embed_query(text)

    print(f"Vector dimensions: {len(vector)}")
    print(f"First 10 values: {vector[:10]}")


if __name__ == "__main__":
    main()