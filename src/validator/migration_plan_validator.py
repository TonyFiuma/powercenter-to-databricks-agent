import re


HUMAN_REVIEW_MARKER = "[HUMAN_REVIEW_SUGGESTION]"


def extract_human_review_suggestions(
    migration_plan: str,
) -> list[str]:
    """
    Extract HUMAN_REVIEW_SUGGESTION blocks from a migration plan.

    A human-review block starts with:

    [HUMAN_REVIEW_SUGGESTION]

    and ends before the next major section separator or
    at the end of the migration plan.
    """

    pattern = re.compile(
        r"\[HUMAN_REVIEW_SUGGESTION\]"
        r".*?"
        r"(?=\n={10,}\n|\Z)",
        flags=re.IGNORECASE | re.DOTALL,
    )

    return [
        match.group(0)
        for match in pattern.finditer(
            migration_plan
        )
    ]


def remove_human_review_suggestions(
    migration_plan: str,
) -> str:
    """
    Remove HUMAN_REVIEW_SUGGESTION blocks from the plan.

    This allows deterministic anti-hallucination rules to
    validate only the approved migration plan and not the
    explicitly separated human-review suggestions.
    """

    pattern = re.compile(
        r"\[HUMAN_REVIEW_SUGGESTION\]"
        r".*?"
        r"(?=\n={10,}\n|\Z)",
        flags=re.IGNORECASE | re.DOTALL,
    )

    return pattern.sub(
        "",
        migration_plan,
    )


def validate_human_review_suggestions(
    migration_plan: str,
) -> list[str]:
    """
    Validate HUMAN_REVIEW_SUGGESTION blocks.

    Suggestions may contain possible implementation approaches,
    but they must remain clearly separated from approved
    migration logic and must explicitly require human review.
    """

    violations = []

    plan_lower = migration_plan.lower()

    suggestions = (
        extract_human_review_suggestions(
            migration_plan
        )
    )

    # --------------------------------------------------------
    # Detect malformed Human Review sections
    # --------------------------------------------------------

    if (
        "human review suggestion:"
        in plan_lower
        and HUMAN_REVIEW_MARKER.lower()
        not in plan_lower
    ):
        violations.append(
            "Human review suggestion is present but "
            "the required [HUMAN_REVIEW_SUGGESTION] "
            "marker is missing."
        )

    if not suggestions:
        return violations

    # --------------------------------------------------------
    # The approved migration must remain unresolved
    # --------------------------------------------------------

    approved_plan = (
        remove_human_review_suggestions(
            migration_plan
        )
    )

    approved_plan_lower = (
        approved_plan.lower()
    )

    unresolved_markers = [
        "not identified in parsed mapping",
        "unresolved",
        "cannot be determined",
        "must be identified before",
    ]

    approved_plan_is_unresolved = any(
        marker in approved_plan_lower
        for marker in unresolved_markers
    )

    if not approved_plan_is_unresolved:
        violations.append(
            "HUMAN_REVIEW_SUGGESTION exists but "
            "the approved migration plan does not "
            "keep the underlying implementation "
            "UNRESOLVED."
        )

    # --------------------------------------------------------
    # Validate every suggestion
    # --------------------------------------------------------

    for index, suggestion in enumerate(
        suggestions,
        start=1,
    ):
        suggestion_lower = (
            suggestion.lower()
        )

        if (
            "possible approach:"
            not in suggestion_lower
        ):
            violations.append(
                "HUMAN_REVIEW_SUGGESTION "
                f"{index} is missing "
                "'Possible approach:'."
            )

        if (
            "why human review is required:"
            not in suggestion_lower
        ):
            violations.append(
                "HUMAN_REVIEW_SUGGESTION "
                f"{index} is missing "
                "'Why human review is required:'."
            )

        if (
            "confidence:"
            not in suggestion_lower
        ):
            violations.append(
                "HUMAN_REVIEW_SUGGESTION "
                f"{index} is missing "
                "'Confidence:'."
            )
        else:
            confidence_match = re.search(
                r"confidence:\s*"
                r"(low|medium)\b",
                suggestion,
                flags=re.IGNORECASE,
            )

            if confidence_match is None:
                violations.append(
                    "HUMAN_REVIEW_SUGGESTION "
                    f"{index} must use confidence "
                    "LOW or MEDIUM."
                )

        # The suggestion must explicitly remain
        # human-review material.
        human_review_markers = [
            "human review",
            "not approved",
            "requires human",
            "human validation",
            "must be reviewed",
        ]

        explicitly_requires_review = any(
            marker in suggestion_lower
            for marker in human_review_markers
        )

        if not explicitly_requires_review:
            violations.append(
                "HUMAN_REVIEW_SUGGESTION "
                f"{index} does not clearly state "
                "that human review is required."
            )

    return violations


def validate_setvariable_plan(
    migration_plan: str,
) -> list[str]:
    """
    Detect speculative Databricks implementations
    for unresolved PowerCenter SETVARIABLE logic.

    HUMAN_REVIEW_SUGGESTION blocks are excluded from
    this validation because speculative approaches are
    allowed there when clearly marked for human review.
    """

    violations = []

    approved_plan = (
        remove_human_review_suggestions(
            migration_plan
        )
    )

    plan_lower = approved_plan.lower()

    forbidden_patterns = [
        "collect()",
        "broadcast",
        "spark.conf.set",
        "dbutils.widgets",
        "current_timestamp",
        "temporary view",
        "python variable",
    ]

    if "setvariable" not in plan_lower:
        return violations

    unresolved_markers = [
        "not identified in parsed mapping",
        "unresolved",
        "cannot be determined",
        "must be identified before",
    ]

    is_unresolved = any(
        marker in plan_lower
        for marker in unresolved_markers
    )

    if not is_unresolved:
        return violations

    for pattern in forbidden_patterns:
        if pattern in plan_lower:
            violations.append(
                "Migration plan proposes a speculative "
                "Databricks implementation for unresolved "
                "SETVARIABLE semantics outside a "
                "HUMAN_REVIEW_SUGGESTION: "
                f"{pattern}"
            )

    return violations


def validate_target_plan(
    migration_plan: str,
) -> list[str]:
    """
    Detect speculative target implementation details
    when the target configuration is unresolved.

    HUMAN_REVIEW_SUGGESTION blocks are excluded from
    approved target validation.
    """

    violations = []

    approved_plan = (
        remove_human_review_suggestions(
            migration_plan
        )
    )

    plan_lower = approved_plan.lower()

    unresolved_markers = [
        "file path",
        "output path",
        "file system location",
        "delimiter",
        "write mode",
        "compression",
        "partitioning",
        "not specified",
        "unresolved",
    ]

    target_is_unresolved = any(
        marker in plan_lower
        for marker in unresolved_markers
    )

    if not target_is_unresolved:
        return violations

    forbidden_patterns = [
        'format("csv")',
        "format('csv')",
        'write.format("csv")',
        "write.format('csv')",
        "dbfs",
        "abfss://",
        "wasbs://",
        "s3://",
        "s3a://",
    ]

    for pattern in forbidden_patterns:
        if pattern in plan_lower:
            violations.append(
                "Migration plan assumes an unresolved "
                "target implementation detail outside a "
                "HUMAN_REVIEW_SUGGESTION: "
                f"{pattern}"
            )

    return violations


def validate_migration_plan(
    mapping_name: str,
    migration_plan: str,
) -> dict:
    """
    Validate a migration plan using deterministic
    anti-hallucination rules.

    Approved migration logic remains strictly validated.

    HUMAN_REVIEW_SUGGESTION blocks may contain possible
    approaches, but they must follow the required structure
    and remain clearly separated from approved migration
    decisions.
    """

    violations = []

    violations.extend(
        validate_human_review_suggestions(
            migration_plan=migration_plan,
        )
    )

    violations.extend(
        validate_setvariable_plan(
            migration_plan=migration_plan,
        )
    )

    violations.extend(
        validate_target_plan(
            migration_plan=migration_plan,
        )
    )

    return {
        "mapping_name": mapping_name,
        "passed": len(violations) == 0,
        "violations": violations,
    }