from dataclasses import dataclass

from src.transpiler.mapping_validation import (
    MappingValidationResult,
)
from src.transpiler.sql_validation import (
    SqlValidationResult,
)


@dataclass(frozen=True)
class MigrationValidationResult:
    """
    Overall validation result for a
    PowerCenter -> Databricks migration.

    It combines:

        - PowerCenter mapping semantic validation
        - generated Databricks SQL validation

    status examples:

        VALID
        REQUIRES_REVIEW
        UNSUPPORTED
    """

    status: str
    mapping_validation: MappingValidationResult
    sql_validation: SqlValidationResult


def combine_validation_results(
    mapping_validation: MappingValidationResult,
    sql_validation: SqlValidationResult,
) -> MigrationValidationResult:
    """
    Combine mapping-level and SQL-level
    validation results into a single migration
    validation result.

    Status priority:

        UNSUPPORTED
            highest priority

        REQUIRES_REVIEW
            if at least one validation requires
            review

        VALID
            only when both validations are valid
    """

    statuses = {
        mapping_validation.status,
        sql_validation.status,
    }

    if "UNSUPPORTED" in statuses:
        status = "UNSUPPORTED"

    elif "REQUIRES_REVIEW" in statuses:
        status = "REQUIRES_REVIEW"

    else:
        status = "VALID"

    return MigrationValidationResult(
        status=status,
        mapping_validation=mapping_validation,
        sql_validation=sql_validation,
    )