from src.agent.nodes.validate_deterministic_migration import (
    validate_deterministic_migration,
)
from src.transpiler.mapping_validation import (
    MappingValidationIssue,
    MappingValidationResult,
)
from src.transpiler.migration_validation import (
    MigrationValidationResult,
)
from src.transpiler.sql_validation import (
    SqlValidationIssue,
    SqlValidationResult,
)


def test_valid_deterministic_migration():
    mapping_validation = MappingValidationResult(
        status="VALID",
        issues=[],
    )

    sql_validation = SqlValidationResult(
        status="VALID",
        supported_features=[
            "CASE WHEN",
            "COUNT",
        ],
        issues=[],
    )

    migration_validation = MigrationValidationResult(
        status="VALID",
        mapping_validation=mapping_validation,
        sql_validation=sql_validation,
    )

    state = {
        "migration_validation": migration_validation,
    }

    result = validate_deterministic_migration(
        state
    )

    print(result)

    assert result["validation_status"] == "VALID"
    assert result["validation_issues"] == []

    assert (
        result["mapping_validation"]
        == mapping_validation
    )

    assert (
        result["sql_validation"]
        == sql_validation
    )


def test_requires_review_collects_all_issues():
    mapping_issue = MappingValidationIssue(
        transformation_name="SQ_CUSTOMERS",
        category="unsupported_feature",
        feature="Pre SQL",
        message="Pre SQL requires review.",
        severity="error",
    )

    sql_issue = SqlValidationIssue(
        category="runtime_variable",
        message=(
            "Unresolved PowerCenter runtime variable."
        ),
        severity="error",
    )

    mapping_validation = MappingValidationResult(
        status="REQUIRES_REVIEW",
        issues=[mapping_issue],
    )

    sql_validation = SqlValidationResult(
        status="REQUIRES_REVIEW",
        supported_features=[],
        issues=[sql_issue],
    )

    migration_validation = MigrationValidationResult(
        status="REQUIRES_REVIEW",
        mapping_validation=mapping_validation,
        sql_validation=sql_validation,
    )

    state = {
        "migration_validation": migration_validation,
    }

    result = validate_deterministic_migration(
        state
    )

    print(result)

    assert (
        result["validation_status"]
        == "REQUIRES_REVIEW"
    )

    assert result["validation_issues"] == [
        mapping_issue,
        sql_issue,
    ]


def test_missing_migration_validation_fails():
    state = {}

    try:
        validate_deterministic_migration(
            state
        )
    except ValueError as exc:
        assert (
            "migration_validation is required"
            in str(exc)
        )
    else:
        raise AssertionError(
            "Expected ValueError"
        )