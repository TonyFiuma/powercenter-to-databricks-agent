import ast
import re
from typing import Any

from src.agent.context.mapping_context import (
    build_single_mapping_input,
)
from src.agent.state import AgentState


SETVARIABLE_FORBIDDEN_PATTERNS = [
    "current_timestamp(",
    "date_format(",
    ".collect(",
    ".first(",
    ".agg(",
    "spark.conf.set",
    "dbutils.widgets",
    ".head(",
    ".take(",
    "broadcast(",
    "sparkcontext.broadcast",
]


FLAT_FILE_FORBIDDEN_PATTERNS = [
    '.write.format("csv")',
    ".write.format('csv')",
    '.write.csv(',
    ".write.csv('",
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


ASSUMED_WRITE_MODE_PATTERNS = [
    '.mode("append")',
    ".mode('append')",
    '.mode("overwrite")',
    ".mode('overwrite')",
    '.mode("error")',
    ".mode('error')",
    '.mode("errorifexists")',
    ".mode('errorifexists')",
    '.mode("ignore")',
    ".mode('ignore')",
]


SOURCE_OPTION_KEYS = [
    "url",
    "user",
    "password",
    "driver",
]


PLACEHOLDER_MARKERS = [
    "todo",
    "<",
    ">",
    "unresolved",
    "placeholder",
    "your_",
    "replace_me",
]


UNRESOLVED_MARKERS = [
    "todo",
    "unresolved",
    "not implemented",
    "cannot determine",
    "cannot be determined",
    "requires clarification",
    "requires resolution",
]


def remove_comments(
    code: str,
) -> str:
    """
    Remove markdown fences and full-line Python comments.

    Negative validation intentionally ignores commented examples,
    because comments may document unresolved migration details without
    making them executable.
    """

    executable_lines = []

    for line in code.splitlines():
        stripped = line.strip()

        if stripped.startswith("```"):
            continue

        if stripped.startswith("#"):
            continue

        executable_lines.append(line)

    return "\n".join(executable_lines)


def normalize_expression(
    value: str,
) -> str:
    """
    Normalize an expression for deterministic comparison.

    Whitespace and casing differences are ignored while preserving the
    expression content itself.
    """

    return "".join(
        value.upper().split()
    )


def extract_setvariable_expressions(
    single_mapping: dict[str, Any],
) -> list[str]:
    """
    Extract all original PowerCenter SETVARIABLE expressions from one
    parsed mapping.
    """

    expressions = []

    mappings = single_mapping.get(
        "mappings",
        [],
    )

    for mapping in mappings:
        transformations = mapping.get(
            "transformations",
            [],
        )

        for transformation in transformations:
            fields = transformation.get(
                "fields",
                [],
            )

            for field in fields:
                expression = field.get(
                    "expression"
                )

                if not expression:
                    continue

                if (
                    "SETVARIABLE("
                    in expression.upper()
                ):
                    expressions.append(
                        expression.strip()
                    )

    return expressions


def contains_setvariable(
    single_mapping: dict[str, Any],
) -> bool:
    return bool(
        extract_setvariable_expressions(
            single_mapping
        )
    )


def has_flat_file_target(
    single_mapping: dict[str, Any],
) -> bool:
    """
    Return True when at least one parsed target is identified as a
    PowerCenter Flat File target.
    """

    targets = single_mapping.get(
        "targets",
        [],
    )

    for target in targets:
        target_type = (
            target.get("database_type")
            or target.get("type")
            or ""
        )

        if "flat file" in str(
            target_type
        ).lower():
            return True

    return False


def _collect_values_for_key(
    value: Any,
    key_name: str,
) -> list[str]:
    """
    Recursively collect explicit values for one configuration key from
    parsed source metadata.
    """

    collected = []

    if isinstance(value, dict):
        for key, nested_value in value.items():
            if (
                key.lower() == key_name.lower()
                and nested_value is not None
            ):
                collected.append(
                    str(nested_value)
                )

            collected.extend(
                _collect_values_for_key(
                    nested_value,
                    key_name,
                )
            )

    elif isinstance(value, list):
        for item in value:
            collected.extend(
                _collect_values_for_key(
                    item,
                    key_name,
                )
            )

    return collected


def _is_placeholder_value(
    value: str,
) -> bool:
    value_lower = value.lower()

    return any(
        marker in value_lower
        for marker in PLACEHOLDER_MARKERS
    )


def _is_explicit_source_value(
    value: str,
    single_mapping: dict[str, Any],
    key_name: str,
) -> bool:
    """
    Check whether a concrete JDBC option value is explicitly present in
    parsed source metadata.

    database_type is intentionally not treated as a JDBC driver value.
    """

    sources = single_mapping.get(
        "sources",
        [],
    )

    explicit_values = []

    for source in sources:
        explicit_values.extend(
            _collect_values_for_key(
                source,
                key_name,
            )
        )

    normalized_candidate = (
        value.strip().lower()
    )

    return any(
        str(explicit_value).strip().lower()
        == normalized_candidate
        for explicit_value in explicit_values
    )


def validate_setvariable_usage(
    code: str,
    single_mapping: dict[str, Any],
) -> list[str]:
    """
    Negative validation for unresolved PowerCenter SETVARIABLE logic.

    When SETVARIABLE exists in the parsed mapping, the generator must not
    invent row extraction, timestamp, widget, Spark configuration, or
    broadcast semantics that are not supported by the mapping.
    """

    violations = []

    if not contains_setvariable(
        single_mapping
    ):
        return violations

    executable_code = remove_comments(
        code
    ).lower()

    for pattern in SETVARIABLE_FORBIDDEN_PATTERNS:
        if pattern.lower() in executable_code:
            violations.append(
                "Generated code appears to implement "
                "PowerCenter SETVARIABLE semantics using "
                "a forbidden pattern: "
                f"{pattern}"
            )

    return violations


def validate_setvariable_preservation(
    code: str,
    single_mapping: dict[str, Any],
) -> list[str]:
    """
    Positive validation for unresolved PowerCenter SETVARIABLE logic.

    The generator is not allowed to make a SETVARIABLE disappear merely
    to satisfy negative validation. Every original expression must remain
    traceable in the generated code, normally as a TODO/comment when the
    exact Databricks implementation is unresolved.
    """

    violations = []

    expressions = (
        extract_setvariable_expressions(
            single_mapping
        )
    )

    if not expressions:
        return violations

    normalized_code = normalize_expression(
        code
    )

    for expression in expressions:
        normalized_expression = (
            normalize_expression(
                expression
            )
        )

        if (
            normalized_expression
            not in normalized_code
        ):
            violations.append(
                "Generated code removed or failed "
                "to preserve the original PowerCenter "
                "SETVARIABLE expression: "
                f"{expression}"
            )

    code_lower = code.lower()

    has_unresolved_marker = any(
        marker in code_lower
        for marker in UNRESOLVED_MARKERS
    )

    if not has_unresolved_marker:
        violations.append(
            "Generated code contains PowerCenter "
            "SETVARIABLE logic but does not explicitly "
            "mark its Databricks implementation as "
            "unresolved or TODO."
        )

    return violations


def validate_flat_file_target(
    code: str,
    single_mapping: dict[str, Any],
) -> list[str]:
    """
    Reject executable assumptions about unresolved Flat File target
    configuration.

    Full-line comments are ignored intentionally.
    """

    violations = []

    if not has_flat_file_target(
        single_mapping
    ):
        return violations

    executable_code = remove_comments(
        code
    ).lower()

    for pattern in ASSUMED_WRITE_MODE_PATTERNS:
        if pattern.lower() in executable_code:
            violations.append(
                "Generated code contains an assumed "
                "target configuration: "
                f"{pattern}"
            )

    for pattern in FLAT_FILE_FORBIDDEN_PATTERNS:
        if pattern.lower() in executable_code:
            violations.append(
                "Generated code implements an unresolved "
                "flat-file target property using a "
                "forbidden pattern: "
                f"{pattern}"
            )

    return violations


def validate_unresolved_source_configuration(
    code: str,
    single_mapping: dict[str, Any],
) -> list[str]:
    """
    Reject invented concrete JDBC connection configuration.

    Explicit TODO/placeholders are allowed. dbtable is intentionally not
    validated here because the source definition/table name can be known
    from the parsed PowerCenter mapping.
    """

    violations = []

    executable_code = remove_comments(
        code
    )

    option_pattern = re.compile(
        r"\.option\(\s*"
        r"[\"'](url|user|password|driver)[\"']"
        r"\s*,\s*"
        r"[\"']([^\"']*)[\"']"
        r"\s*\)",
        flags=re.IGNORECASE,
    )

    for match in option_pattern.finditer(
        executable_code
    ):
        key_name = match.group(1)
        value = match.group(2)
        full_option = match.group(0)

        if _is_placeholder_value(
            value
        ):
            continue

        if _is_explicit_source_value(
            value=value,
            single_mapping=single_mapping,
            key_name=key_name,
        ):
            continue

        violations.append(
            "Generated code contains an assumed "
            "source/JDBC configuration: "
            f"{full_option}"
        )

    return violations



def validate_python_syntax(
    code: str,
) -> list[str]:
    """
    Validate that the generated output is syntactically valid Python.

    Markdown fences are removed before parsing because some LLMs may
    return fenced code even when instructed not to.
    """

    violations = []

    cleaned_lines = []

    for line in code.splitlines():
        if line.strip().startswith("```"):
            continue

        cleaned_lines.append(line)

    cleaned_code = "\n".join(
        cleaned_lines
    )

    try:
        ast.parse(
            cleaned_code
        )
    except SyntaxError as exc:
        location = ""

        if exc.lineno is not None:
            location = (
                f" at line {exc.lineno}"
            )

            if exc.offset is not None:
                location += (
                    f", column {exc.offset}"
                )

        violations.append(
            "Generated code is not valid Python syntax"
            f"{location}: {exc.msg}"
        )

    return violations

def validate_mapping_code(
    code: str,
    single_mapping: dict,
) -> list[str]:

    violations = []

    violations.extend(
        validate_python_syntax(code)
    )

    violations.extend(
        validate_structural_completeness(code)
    )

    violations.extend(
        validate_setvariable_usage(
            code,
            single_mapping,
        )
    )

    violations.extend(
        validate_setvariable_preservation(
            code,
            single_mapping,
        )
    )

    violations.extend(
        validate_flat_file_target(
            code,
            single_mapping,
        )
    )

    violations.extend(
        validate_unresolved_source_configuration(
            code,
            single_mapping,
        )
    )

    return violations


def validate_generated_code_node(
    state: AgentState,
) -> dict:
    """
    Validate the generated PySpark for every parsed PowerCenter mapping.

    The result shape is intentionally compatible with the repair node:
    each mapping result contains mapping_name, passed, and violations.
    """

    print(
        "\nValidating generated PySpark..."
    )

    mapping = state["mapping"]

    generated_codes = state.get(
        "generated_codes",
        {},
    )

    pc_mappings = mapping.get(
        "mappings",
        [],
    )

    print(
        f"Mappings to validate: "
        f"{len(pc_mappings)}"
    )

    validation_results = []

    for index, pc_mapping in enumerate(
        pc_mappings,
        start=1,
    ):
        mapping_name = pc_mapping.get(
            "name",
            "UNKNOWN_MAPPING",
        )

        print("")
        print(
            f"[{index}/{len(pc_mappings)}] "
            f"Validating: {mapping_name}"
        )

        code = generated_codes.get(
            mapping_name
        )

        if (
            not isinstance(code, str)
            or not code.strip()
        ):
            violations = [
                "Generated PySpark code not found "
                "for this mapping."
            ]

        else:
            single_mapping = (
                build_single_mapping_input(
                    full_mapping=mapping,
                    pc_mapping=pc_mapping,
                )
            )

            violations = (
                validate_mapping_code(
                    code=code,
                    single_mapping=single_mapping,
                )
            )

        passed = not violations

        validation_results.append(
            {
                "mapping_name": mapping_name,
                "passed": passed,
                "violations": violations,
            }
        )

        if passed:
            print(
                "Validation passed."
            )
        else:
            print(
                "Validation failed."
            )

            for violation in violations:
                print(
                    f"  - {violation}"
                )

    validation_passed = all(
        result["passed"]
        for result in validation_results
    )

    print("")
    print(
        "Overall validation: "
        + (
            "PASSED"
            if validation_passed
            else "FAILED"
        )
    )

    return {
        "validation_results": (
            validation_results
        ),
        "validation_passed": (
            validation_passed
        ),
    }

def validate_structural_completeness(
    code: str,
) -> list[str]:
    """
    Detect generated code that is syntactically valid
    but appears structurally incomplete or truncated.

    Example:
        # For now, selecting only the common columns that
    """

    violations = []

    cleaned_lines = []

    for line in code.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("```"):
            continue

        cleaned_lines.append(stripped)

    if not cleaned_lines:
        violations.append(
            "Generated code is empty."
        )
        return violations

    last_line = cleaned_lines[-1]

    # Only inspect trailing comments.
    # Executable Python statements are already checked
    # by ast.parse().
    if not last_line.startswith("#"):
        return violations

    comment = (
        last_line
        .lstrip("#")
        .strip()
        .lower()
    )

    incomplete_endings = (
        " that",
        " because",
        " with",
        " using",
        " to",
        " and",
        " or",
        " for",
        " from",
    )

    if comment.endswith(incomplete_endings):
        violations.append(
            "Generated code appears truncated or structurally "
            f"incomplete. Last comment: {last_line}"
        )

    return violations