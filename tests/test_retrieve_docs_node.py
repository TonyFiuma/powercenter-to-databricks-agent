from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)

from src.agent.nodes.retrieve_docs import (
    retrieve_docs_node,
)


def main():
    xml_path = (
        "data/input/wf_m_DHUBTOMIS_MBDT_CSV.XML"
    )

    mapping = parse_powercenter_xml(
        xml_path
    )

    state = {
        "xml_path": xml_path,
        "mapping": mapping,
    }

    result = retrieve_docs_node(
        state
    )

    print("\n" + "=" * 80)
    print("RETRIEVAL QUERIES")
    print("=" * 80)

    print(
        result["retrieval_query"]
    )

    print("\n" + "=" * 80)
    print("RETRIEVED DOCUMENTS")
    print("=" * 80)

    documents = result[
        "retrieved_docs"
    ]

    print(
        f"\nTotal documents retrieved: "
        f"{len(documents)}"
    )

    for index, document in enumerate(
        documents,
        start=1,
    ):
        print(
            f"\n--- DOCUMENT {index} ---"
        )

        print(
            "Source:",
            document.metadata.get(
                "source"
            ),
        )

        print(
            "Title:",
            document.metadata.get(
                "title"
            ),
        )

        print(
            "Category:",
            document.metadata.get(
                "category"
            ),
        )

        print(
            "URL:",
            document.metadata.get(
                "url"
            ),
        )

        print(
            "\nContent preview:"
        )

        print(
            document.page_content[:500]
        )


if __name__ == "__main__":
    main()