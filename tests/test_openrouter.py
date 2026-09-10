from src.llm.provider import (
    get_generator_llm,
)


def main():
    llm = get_generator_llm()

    response = llm.invoke(
        """
            Generate only PySpark code that reads a table named
            CUSTOMERS and filters rows where ACTIVE = 1.
        """
    )

    print("CONTENT:")
    print(response.content)

    print("\nMETADATA:")
    print(response.response_metadata)


if __name__ == "__main__":
    main()