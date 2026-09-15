from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """
    Shared state of the PowerCenter -> Databricks
    migration agent.

    The state contains both deterministic
    transpilation results and AI/RAG fallback
    information.
    """

    # Input
    xml_path: str
    mapping_name: str

    # PowerCenter metadata
    powercenter_version: str | None
    powercenter_version_source: str | None

    # Complete parsed PowerCenter document
    powercenter_project: dict[str, Any]

    # Selected PowerCenter execution context
    mapping: dict[str, Any]
    mapplets: list[dict[str, Any]]
    workflow: dict[str, Any]
    session: dict[str, Any]

    # Transformation analysis
    detected_transformations: list[str]
    unsupported_transformations: list[str]

    # Deterministic transpilation
    powercenter_sql: str
    databricks_sql: str

    # Validation
    mapping_validation: Any
    sql_validation: Any
    migration_validation: Any
    validation_status: str
    validation_issues: list[Any]

    # RAG fallback
    retrieval_query: str
    filters: dict[str, Any]
    retrieved_docs: list[Any]

    # AI migration fallback
    migration_plan: str
    pyspark_code: str

    # Migration-plan validation / repair
    migration_plan_validation_passed: bool
    migration_plan_repair_attempts: int

    # Generated-code validation / repair
    validation_results: list[Any]
    validation_passed: bool
    repair_attempts: int

    # Final output
    migration_report: str