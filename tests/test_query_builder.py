from src.rag.query_builder import (
    build_powercenter_retrieval_query,
    build_databricks_retrieval_query,
)


def main():
    transformations = [
        "Expression",
        "Source Qualifier",
        "Filter",
        "Aggregator",
        "Joiner",
        "Lookup",
    ]

    for transformation in transformations:
        print("\n" + "=" * 80)

        print(
            f"TRANSFORMATION: "
            f"{transformation}"
        )

        print(
            "\nPowerCenter query:"
        )

        print(
            build_powercenter_retrieval_query(
                transformation
            )
        )

        print(
            "\nDatabricks query:"
        )

        print(
            build_databricks_retrieval_query(
                transformation
            )
        )


if __name__ == "__main__":
    main()