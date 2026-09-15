from typing import Any

from src.agent.state import AgentState
from src.transpiler.mapping_validation import (
    validate_powercenter_mapping,
)
from src.transpiler.migration_validation import (
    combine_validation_results,
)
from src.transpiler.sql_validation import (
    validate_databricks_sql,
)


def run_deterministic_migration_node(
    state: AgentState,
) -> dict[str, Any]:
    """
    Execute the deterministic validation stage of
    the PowerCenter -> Databricks migration.

    This node currently combines mapping semantic
    validation with validation of an already
    generated Databricks SQL statement.

    The complete deterministic transpilation
    pipeline will populate databricks_sql before
    this node is used in the final graph.
    """

    mapping = state.get("mapping")

    if mapping is None:
        raise ValueError(
            "mapping is required before running "
            "deterministic migration."
        )

    databricks_sql = state.get(
        "databricks_sql"
    )

    if not databricks_sql:
        raise ValueError(
            "databricks_sql is required before "
            "running deterministic migration."
        )

    mapping_validation = (
        validate_powercenter_mapping(
            mapping
        )
    )

    sql_validation = (
        validate_databricks_sql(
            databricks_sql
        )
    )

    migration_validation = (
        combine_validation_results(
            mapping_validation=(
                mapping_validation
            ),
            sql_validation=sql_validation,
        )
    )

    return {
        "mapping_validation": (
            mapping_validation
        ),
        "sql_validation": sql_validation,
        "migration_validation": (
            migration_validation
        ),
    }