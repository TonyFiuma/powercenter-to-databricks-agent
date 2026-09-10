from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)

from src.agent.nodes.retrieve_docs import (
    retrieve_docs_node,
)

from src.agent.nodes.create_migration_plan import (
    build_documentation_context,
)


def main():
    xml_path = (
        "data/input/wf_m_DHUBTOMIS_MBDT_CSV.XML"
    )

    # 1. Parse the real PowerCenter XML
    mapping = parse_powercenter_xml(
        xml_path
    )

    state = {
        "xml_path": xml_path,
        "mapping": mapping,
    }

    # 2. Retrieve PowerCenter + Databricks docs
    retrieval_result = retrieve_docs_node(
        state
    )

    retrieved_docs = retrieval_result[
        "retrieved_docs"
    ]

    # 3. Build the real documentation context
    documentation_context = (
        build_documentation_context(
            retrieved_docs
        )
    )

    print("\n" + "=" * 80)
    print("RETRIEVAL SUMMARY")
    print("=" * 80)

    print(
        retrieval_result[
            "retrieval_query"
        ]
    )

    print(
        f"\nTotal documents retrieved: "
        f"{len(retrieved_docs)}"
    )

    # Count the two sources
    powercenter_docs = [
        doc
        for doc in retrieved_docs
        if doc.metadata.get("source")
        != "databricks"
    ]

    databricks_docs = [
        doc
        for doc in retrieved_docs
        if doc.metadata.get("source")
        == "databricks"
    ]

    print(
        f"PowerCenter documents: "
        f"{len(powercenter_docs)}"
    )

    print(
        f"Databricks documents: "
        f"{len(databricks_docs)}"
    )

    print("\n" + "=" * 80)
    print("DOCUMENTATION CONTEXT")
    print("=" * 80)

    print(
        documentation_context
    )

    print("\n" + "=" * 80)
    print("CHECKS")
    print("=" * 80)

    assert (
        len(powercenter_docs) > 0
    )

    assert (
        len(databricks_docs) > 0
    )

    assert (
        "=== POWERCENTER DOCUMENTATION ==="
        in documentation_context
    )

    assert (
        "=== DATABRICKS DOCUMENTATION ==="
        in documentation_context
    )

    print(
        "PowerCenter retrieval: OK"
    )

    print(
        "Databricks retrieval: OK"
    )

    print(
        "Documentation separation: OK"
    )

    print(
        "\nTEST PASSED"
    )


if __name__ == "__main__":
    main()