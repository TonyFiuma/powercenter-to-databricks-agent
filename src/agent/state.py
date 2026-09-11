from typing import TypedDict, Any


class AgentState(TypedDict, total=False):
    """
    Shared state of the PowerCenter -> Databricks migration graph.
    """

    # Input
    xml_path: str

    # PowerCenter metadata
    powercenter_version: str
    powercenter_version_source: str

    # Parser output
    mapping: dict[str, Any]

    # Transformation analysis
    detected_transformations: list[str]
    unsupported_transformations: list[str]

    # RAG
    retrieval_query: str
    retrieval_filters: dict[str, Any]
    retrieved_docs: list[Any]

    # Migration plans
    migration_plan: str
    migration_plans: dict[str, str]

    # Migration-plan validation
    migration_plan_validation_results: list[dict[str, Any]]
    migration_plan_validation_passed: bool
    migration_plan_repair_attempts: int

    # Generated PySpark
    pyspark_code: str
    generated_codes: dict[str, str]

    # Generated-code validation
    validation_results: list[dict[str, Any]]
    validation_passed: bool
    validation_status: str
    validation_issues: list[dict[str, Any]]
    repair_attempts: int