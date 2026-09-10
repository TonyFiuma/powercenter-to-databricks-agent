from langchain_core.documents import Document

from src.agent.nodes.create_migration_plan import (
    build_documentation_context,
)


def main():
    docs = [
        Document(
            page_content=(
                "PowerCenter Expression Transformation "
                "documentation content."
            ),
            metadata={
                "source": (
                    "data/docs/powercenter/"
                    "PC_105_TransformationGuide_en.pdf"
                )
            },
        ),
        Document(
            page_content=(
                "PySpark DataFrame withColumn "
                "documentation content."
            ),
            metadata={
                "source": "databricks",
                "title": "PySpark basics",
            },
        ),
    ]

    context = build_documentation_context(
        docs
    )

    print("\n" + "=" * 80)
    print("DOCUMENTATION CONTEXT")
    print("=" * 80)

    print(context)

    print("\n" + "=" * 80)
    print("CHECKS")
    print("=" * 80)

    assert (
        "=== POWERCENTER DOCUMENTATION ==="
        in context
    )

    assert (
        "=== DATABRICKS DOCUMENTATION ==="
        in context
    )

    assert (
        "PowerCenter Expression Transformation"
        in context
    )

    assert (
        "PySpark DataFrame withColumn"
        in context
    )

    powercenter_position = context.index(
        "=== POWERCENTER DOCUMENTATION ==="
    )

    databricks_position = context.index(
        "=== DATABRICKS DOCUMENTATION ==="
    )

    assert (
        powercenter_position
        < databricks_position
    )

    print(
        "PowerCenter section: OK"
    )

    print(
        "Databricks section: OK"
    )

    print(
        "Documents correctly separated: OK"
    )

    print(
        "\nTEST PASSED"
    )


if __name__ == "__main__":
    main()