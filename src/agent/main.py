from dotenv import load_dotenv

# Load environment variables BEFORE importing the graph.
load_dotenv()

from src.agent.graph import build_graph


def main():
    """
    Run the hybrid PowerCenter -> Databricks
    migration agent.

    The deterministic transpiler is the primary
    migration path.

    RAG/LLM is used only when deterministic
    validation requires review.
    """

    app = build_graph()

    result = app.invoke(
        {
            "xml_path": (
                "data/input/"
                "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
            ),
            "mapping_name": (
                "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
            ),
            "powercenter_version": "10.5.7",
        }
    )

    print(
        "\n========================================"
    )
    print(
        "MIGRATION RESULT"
    )
    print(
        "========================================"
    )

    print(
        "\nPowerCenter version:"
    )
    print(
        result.get(
            "powercenter_version"
        )
    )

    print(
        "\nPowerCenter version source:"
    )
    print(
        result.get(
            "powercenter_version_source"
        )
    )

    print(
        "\nMapping:"
    )
    print(
        result["mapping"]["name"]
    )

    print(
        "\nWorkflow:"
    )
    print(
        result["workflow"]["name"]
    )

    print(
        "\nSession:"
    )
    print(
        result["session"]["name"]
    )

    print(
        "\nDeterministic validation status:"
    )

    validation_status = result.get(
        "validation_status"
    )

    print(
        validation_status
    )

    print(
        "\nValidation issues:"
    )

    validation_issues = result.get(
        "validation_issues",
        [],
    )

    if validation_issues:
        for issue in validation_issues:
            print(
                f"- {issue}"
            )
    else:
        print(
            "None"
        )

    # --------------------------------------------
    # Deterministic migration succeeded
    # --------------------------------------------

    if validation_status == "VALID":
        print(
            "\nMigration completed through "
            "the deterministic transpiler."
        )

        print(
            "RAG/LLM fallback was not used."
        )

        print(
            "\nGenerated Databricks SQL:"
        )

        print(
            result["databricks_sql"]
        )

        return

    # --------------------------------------------
    # Unsupported deterministic migration
    # --------------------------------------------

    if validation_status == "UNSUPPORTED":
        print(
            "\nAutomatic migration stopped "
            "because unsupported semantics "
            "were detected."
        )

        return

    # --------------------------------------------
    # AI / RAG fallback
    # --------------------------------------------

    if validation_status == "REQUIRES_REVIEW":
        print(
            "\nMigration required AI/RAG "
            "fallback."
        )

        migration_plan = result.get(
            "migration_plan"
        )

        pyspark_code = result.get(
            "pyspark_code"
        )

        if migration_plan:
            print(
                "\nMigration plan:"
            )
            print(
                migration_plan
            )

        if pyspark_code:
            print(
                "\nGenerated PySpark:"
            )
            print(
                pyspark_code
            )

        print(
            "\nGenerated-code validation:"
        )

        print(
            "PASSED"
            if result.get(
                "validation_passed",
                False,
            )
            else "FAILED"
        )

        return

    raise RuntimeError(
        "Unexpected migration validation "
        f"status: {validation_status}"
    )


if __name__ == "__main__":
    main()