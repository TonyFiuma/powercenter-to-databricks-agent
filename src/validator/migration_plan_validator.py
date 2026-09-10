def validate_setvariable_plan(
    migration_plan: str,
) -> list[str]:
    """
    Detect speculative Databricks implementations
    for unresolved PowerCenter SETVARIABLE logic.
    """

    violations = []

    plan_lower = migration_plan.lower()

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
                "SETVARIABLE semantics: "
                f"{pattern}"
            )

    return violations


def validate_target_plan(
    migration_plan: str,
) -> list[str]:
    """
    Detect speculative target implementation details
    when the target configuration is unresolved.
    """

    violations = []

    plan_lower = migration_plan.lower()

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
                "target implementation detail: "
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
    """

    violations = []

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