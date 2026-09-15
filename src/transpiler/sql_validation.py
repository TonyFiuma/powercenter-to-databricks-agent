import re
from dataclasses import dataclass, field


POWERCENTER_RUNTIME_VARIABLE_PATTERN = re.compile(
    r"\$\$[A-Za-z_][A-Za-z0-9_]*"
)


SUPPORTED_SQL_FEATURES = {
    "CASE WHEN": re.compile(
        r"\bCASE\s+WHEN\b",
        re.IGNORECASE,
    ),
    "CONCAT": re.compile(
        r"\bCONCAT\s*\(",
        re.IGNORECASE,
    ),
    "COUNT": re.compile(
        r"\bCOUNT\s*\(",
        re.IGNORECASE,
    ),
    "GROUP BY": re.compile(
        r"\bGROUP\s+BY\b",
        re.IGNORECASE,
    ),
    "INNER JOIN": re.compile(
        r"\bINNER\s+JOIN\b",
        re.IGNORECASE,
    ),
    "LEFT OUTER JOIN": re.compile(
        r"\bLEFT\s+OUTER\s+JOIN\b",
        re.IGNORECASE,
    ),
    "RIGHT OUTER JOIN": re.compile(
        r"\bRIGHT\s+OUTER\s+JOIN\b",
        re.IGNORECASE,
    ),
    "FULL OUTER JOIN": re.compile(
        r"\bFULL\s+OUTER\s+JOIN\b",
        re.IGNORECASE,
    ),
}


@dataclass(frozen=True)
class SqlValidationIssue:
    """
    Single issue detected while validating
    generated SQL for Databricks compatibility.

    severity examples:

        warning
        error

    category examples:

        runtime_variable
        sql_function
        sql_syntax
        unsupported_feature
    """

    category: str
    message: str
    severity: str


@dataclass(frozen=True)
class SqlValidationResult:
    """
    Result of Databricks SQL compatibility
    validation.

    status examples:

        VALID
        REQUIRES_REVIEW
        UNSUPPORTED
    """

    status: str

    supported_features: list[str] = field(
        default_factory=list
    )

    issues: list[SqlValidationIssue] = field(
        default_factory=list
    )


def detect_supported_features(
    sql: str,
) -> list[str]:
    """
    Detect SQL features that are already known
    to be supported by the deterministic
    PowerCenter -> Databricks transpiler.
    """

    detected_features: list[str] = []

    for feature, pattern in (
        SUPPORTED_SQL_FEATURES.items()
    ):
        if pattern.search(sql):
            detected_features.append(
                feature
            )

    return detected_features


def validate_databricks_sql(
    sql: str,
) -> SqlValidationResult:
    """
    Validate generated SQL for Databricks
    compatibility.

    Current validation rules:

        - Detect unresolved PowerCenter runtime
          variables.

        - Report SQL features already supported
          by the deterministic transpiler.
    """

    issues: list[SqlValidationIssue] = []

    unresolved_variables = set(
        POWERCENTER_RUNTIME_VARIABLE_PATTERN.findall(
            sql
        )
    )

    for variable in sorted(
        unresolved_variables
    ):
        issues.append(
            SqlValidationIssue(
                category="runtime_variable",
                message=(
                    "Unresolved PowerCenter "
                    "runtime variable: "
                    f"{variable}"
                ),
                severity="error",
            )
        )

    supported_features = (
        detect_supported_features(
            sql
        )
    )

    if issues:
        status = "REQUIRES_REVIEW"
    else:
        status = "VALID"

    return SqlValidationResult(
        status=status,
        supported_features=supported_features,
        issues=issues,
    )