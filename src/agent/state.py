from typing import Any, TypedDict


class AgentState(
    TypedDict,
    total=False,
):
    # Input
    xml_path: str

    # Parsed PowerCenter structure
    mapping: dict[str, Any]

    # RAG
    retrieval_query: str
    retrieved_docs: list[Any]

    # Migration planning
    migration_plan: str
    migration_plans: dict[str, str]

    # Migration-plan validation
    migration_plan_validation_results: list[
        dict[str, Any]
    ]
    migration_plan_validation_passed: bool

    # Migration-plan repair loop
    migration_plan_repair_attempts: int

    # PySpark generation
    pyspark_code: str
    generated_codes: dict[str, str]

    # PySpark validation
    validation_results: list[
        dict[str, Any]
    ]
    validation_passed: bool

    # PySpark repair loop
    repair_attempts: int


    # Final migration artifacts
    migration_report: dict[str, Any]
    migration_report_path: str
    exported_files: dict[str, str]
