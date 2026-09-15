from src.transpiler.mapping_validation import (
    MappingValidationIssue,
    MappingValidationResult,
)
from src.transpiler.migration_validation import (
    combine_validation_results,
)
from src.transpiler.sql_validation import (
    SqlValidationIssue,
    SqlValidationResult,
)


def test_all_valid():
    mapping_result = MappingValidationResult(
        status="VALID",
        issues=[],
    )

    sql_result = SqlValidationResult(
        status="VALID",
        supported_features=[
            "CASE WHEN",
            "COUNT",
        ],
        issues=[],
    )

    result = combine_validation_results(
        mapping_validation=mapping_result,
        sql_validation=sql_result,
    )

    print(result)

    assert result.status == "VALID"


def test_mapping_requires_review():
    mapping_result = MappingValidationResult(
        status="REQUIRES_REVIEW",
        issues=[
            MappingValidationIssue(
                transformation_name="SQ_CUSTOMERS",
                category="unsupported_feature",
                feature="Pre SQL",
                message="Pre SQL requires review.",
                severity="error",
            )
        ],
    )

    sql_result = SqlValidationResult(
        status="VALID",
        supported_features=[],
        issues=[],
    )

    result = combine_validation_results(
        mapping_validation=mapping_result,
        sql_validation=sql_result,
    )

    print(result)

    assert (
        result.status
        == "REQUIRES_REVIEW"
    )


def test_sql_requires_review():
    mapping_result = MappingValidationResult(
        status="VALID",
        issues=[],
    )

    sql_result = SqlValidationResult(
        status="REQUIRES_REVIEW",
        supported_features=[],
        issues=[
            SqlValidationIssue(
                category="runtime_variable",
                message=(
                    "Unresolved PowerCenter "
                    "runtime variable."
                ),
                severity="error",
            )
        ],
    )

    result = combine_validation_results(
        mapping_validation=mapping_result,
        sql_validation=sql_result,
    )

    print(result)

    assert (
        result.status
        == "REQUIRES_REVIEW"
    )


def test_unsupported_has_highest_priority():
    mapping_result = MappingValidationResult(
        status="UNSUPPORTED",
        issues=[],
    )

    sql_result = SqlValidationResult(
        status="REQUIRES_REVIEW",
        supported_features=[],
        issues=[],
    )

    result = combine_validation_results(
        mapping_validation=mapping_result,
        sql_validation=sql_result,
    )

    print(result)

    assert (
        result.status
        == "UNSUPPORTED"
    )