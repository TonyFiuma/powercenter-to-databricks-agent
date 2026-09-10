def remove_comments(
    generated_code: str,
) -> str:
    """
    Remove full-line Python comments before
    validating executable code.

    This avoids false positives when forbidden
    patterns appear only inside TODO comments
    or commented examples.
    """

    executable_lines = []

    for line in generated_code.splitlines():
        if line.strip().startswith("#"):
            continue

        executable_lines.append(line)

    return "\n".join(
        executable_lines
    )


def has_setvariable(
    pc_mapping: dict,
) -> bool:
    """
    Check whether a PowerCenter mapping contains
    at least one SETVARIABLE expression.
    """

    for transformation in pc_mapping.get(
        "transformations",
        [],
    ):
        for field in transformation.get(
            "fields",
            [],
        ):
            expression = field.get(
                "expression"
            )

            if (
                expression
                and "SETVARIABLE" in expression.upper()
            ):
                return True

    return False


def validate_setvariable(
    pc_mapping: dict,
    generated_code: str,
) -> list[str]:
    """
    Detect unsafe attempts to implement PowerCenter
    SETVARIABLE semantics in PySpark.

    SETVARIABLE is currently considered unresolved
    unless its lifecycle and downstream usage are known.
    """

    violations = []

    if not has_setvariable(
        pc_mapping
    ):
        return violations

    executable_code = remove_comments(
        generated_code
    )

    code_lower = executable_code.lower()

    forbidden_patterns = [
        "current_timestamp(",
        "date_format(",
        ".collect(",
        ".first(",
        ".head(",
        ".take(",
        ".agg(",
        "spark.conf.set",
        "dbutils.widgets",
        "broadcast(",
        "sparkcontext.broadcast",
    ]

    for pattern in forbidden_patterns:
        if pattern.lower() in code_lower:
            violations.append(
                "Generated code appears to implement "
                "PowerCenter SETVARIABLE semantics "
                "using a forbidden pattern: "
                f"{pattern}"
            )

    return violations


def validate_unresolved_target(
    generated_code: str,
) -> list[str]:
    """
    Detect target configuration values that should
    remain unresolved.

    Commented examples are ignored.
    """

    violations = []

    executable_code = remove_comments(
        generated_code
    )

    code_lower = executable_code.lower()

    forbidden_patterns = [
        '.option("header", "true")',
        ".option('header', 'true')",
        '.option("header", true)',
        ".option('header', true)",
        '.option("delimiter", ",")',
        ".option('delimiter', ',')",
        '.mode("overwrite")',
        ".mode('overwrite')",
        '.mode("append")',
        ".mode('append')",
    ]

    for pattern in forbidden_patterns:
        if pattern.lower() in code_lower:
            violations.append(
                "Generated code contains an assumed "
                "target configuration: "
                f"{pattern}"
            )

    return violations


def validate_unresolved_flat_file_write(
    generated_code: str,
) -> list[str]:
    """
    Detect executable flat-file write logic that
    hard-codes unresolved target properties.

    For the current MVP, flat-file format and output
    path are considered unresolved unless explicitly
    known from the parsed mapping.
    """

    violations = []

    executable_code = remove_comments(
        generated_code
    )

    code_lower = executable_code.lower()

    forbidden_patterns = [
        '.write.format("csv")',
        ".write.format('csv')",
        ".write.csv(",
        '.format("csv").save(',
        ".format('csv').save(",
        "<output_path>",
        "<target_path>",
        "dbfs:/",
        "abfss://",
        "wasbs://",
        "s3://",
        "s3a://",
    ]

    for pattern in forbidden_patterns:
        if pattern.lower() in code_lower:
            violations.append(
                "Generated code implements an "
                "unresolved flat-file target property "
                "using a forbidden pattern: "
                f"{pattern}"
            )

    return violations


def validate_jdbc_configuration(
    generated_code: str,
) -> list[str]:
    """
    Detect JDBC configuration values that should
    not be invented by the generator.

    Commented examples are ignored.
    """

    violations = []

    executable_code = remove_comments(
        generated_code
    )

    code_lower = executable_code.lower()

    forbidden_patterns = [
        "oracle.jdbc.driver.oracledriver",
        "oracle.jdbc.oracledriver",
    ]

    for pattern in forbidden_patterns:
        if pattern in code_lower:
            violations.append(
                "Generated code hard-codes an "
                "unresolved JDBC driver: "
                f"{pattern}"
            )

    return violations


def validate_mapping_code(
    pc_mapping: dict,
    generated_code: str,
) -> dict:
    """
    Validate generated PySpark against deterministic
    migration safety rules.

    Returns a dictionary containing:

    - mapping_name
    - passed
    - violations
    """

    mapping_name = pc_mapping.get(
        "name",
        "UNKNOWN_MAPPING",
    )

    violations = []

    violations.extend(
        validate_setvariable(
            pc_mapping=pc_mapping,
            generated_code=generated_code,
        )
    )

    violations.extend(
        validate_unresolved_target(
            generated_code=generated_code,
        )
    )

    violations.extend(
        validate_unresolved_flat_file_write(
            generated_code=generated_code,
        )
    )

    violations.extend(
        validate_jdbc_configuration(
            generated_code=generated_code,
        )
    )

    return {
        "mapping_name": mapping_name,
        "passed": len(violations) == 0,
        "violations": violations,
    }