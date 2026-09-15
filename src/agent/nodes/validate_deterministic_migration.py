from typing import Any

from src.agent.state import AgentState
from src.transpiler.mapping_validation import (
    MappingValidationResult,
)
from src.transpiler.migration_validation import (
    MigrationValidationResult,
)
from src.transpiler.sql_validation import (
    SqlValidationResult,
)


def collect_validation_issues(
    mapping_validation: MappingValidationResult,
    sql_validation: SqlValidationResult,
) -> list[Any]:
    """
    Collect mapping-level and SQL-level validation
    issues into a single list for the agent state.
    """

    return [
        *mapping_validation.issues,
        *sql_validation.issues,
    ]


def validate_deterministic_migration(
    state: AgentState,
) -> dict[str, Any]:
    """
    Convert deterministic migration validation
    results into the decision state used by the
    LangGraph agent.

    Expected migration statuses:

        VALID
        REQUIRES_REVIEW
        UNSUPPORTED
    """

    migration_validation = state.get(
        "migration_validation"
    )

    if migration_validation is None:
        raise ValueError(
            "migration_validation is required "
            "before deterministic migration "
            "validation."
        )

    if not isinstance(
        migration_validation,
        MigrationValidationResult,
    ):
        raise TypeError(
            "migration_validation must be a "
            "MigrationValidationResult."
        )

    mapping_validation = (
        migration_validation.mapping_validation
    )

    sql_validation = (
        migration_validation.sql_validation
    )

    validation_issues = (
        collect_validation_issues(
            mapping_validation=mapping_validation,
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
        "validation_status": (
            migration_validation.status
        ),
        "validation_issues": (
            validation_issues
        ),
    }