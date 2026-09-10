from dotenv import load_dotenv

# Load environment variables BEFORE importing the graph.
load_dotenv()

from src.agent.graph import build_graph


def main():
    """
    Run the PowerCenter -> Databricks migration agent.
    """

    app = build_graph()

    result = app.invoke(
        {
            "xml_path": "data/input/wf_m_DHUBTOMIS_MBDT_CSV.XML"
        }
    )

    print("\nSTATE KEYS:")
    print(result.keys())

    print("\nVALIDATION PASSED VALUE:")
    print(
        result.get(
            "validation_passed",
            "KEY NOT FOUND",
        )
    )

    print("\nMigration plan:")
    print(result["migration_plan"])

    print("\nGenerated PySpark:")
    print(result["pyspark_code"])

    print("\nValidation results:")

    for validation in result[
        "validation_results"
    ]:
        print(
            f"- {validation['mapping_name']}: "
            f"{'PASSED' if validation['passed'] else 'FAILED'}"
        )

        for violation in validation[
            "violations"
        ]:
            print(
                f"    - {violation}"
            )

    print(
        "\nOverall validation:",
        "PASSED"
        if result["validation_passed"]
        else "FAILED",
    )


if __name__ == "__main__":
    main()