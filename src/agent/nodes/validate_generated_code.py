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

HUMAN_REVIEW_PLAN_MARKER = (
    "[HUMAN_REVIEW_SUGGESTION]"
)

HUMAN_REVIEW_BEGIN_MARKER = (
    "BEGIN HUMAN_REVIEW_SUGGESTION"
)

HUMAN_REVIEW_END_MARKER = (
    "END HUMAN_REVIEW_SUGGESTION"
)

HUMAN_REVIEW_REQUIRED_MARKER = (
    "HUMAN REVIEW REQUIRED"
)

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

def validate_human_review_safety(
    code: str,
    migration_plan: str,
) -> list[str]:
    """
    Validate that HUMAN_REVIEW_SUGGESTION material
    remains completely non-executable.

    Human-review suggestions are allowed only when the
    validated migration plan contains an explicit
    [HUMAN_REVIEW_SUGGESTION].

    Generated Human Review material must be enclosed by:

    # BEGIN HUMAN_REVIEW_SUGGESTION
    ...
    # END HUMAN_REVIEW_SUGGESTION

    Every non-empty line inside the block must remain
    a Python comment.
    """

    violations = []

    plan_lower = migration_plan.lower()

    plan_has_human_review = (
        HUMAN_REVIEW_PLAN_MARKER.lower()
        in plan_lower
    )

    lines = code.splitlines()

    begin_indexes = []
    end_indexes = []

    # ========================================================
    # Locate BEGIN / END markers
    # ========================================================

    for index, line in enumerate(
        lines
    ):
        stripped = line.strip()
        stripped_lower = stripped.lower()

        if (
            HUMAN_REVIEW_BEGIN_MARKER.lower()
            in stripped_lower
        ):
            begin_indexes.append(
                index
            )

            if not stripped.startswith("#"):
                violations.append(
                    "BEGIN HUMAN_REVIEW_SUGGESTION "
                    "marker must be a Python comment "
                    f"at line {index + 1}."
                )

        if (
            HUMAN_REVIEW_END_MARKER.lower()
            in stripped_lower
        ):
            end_indexes.append(
                index
            )

            if not stripped.startswith("#"):
                violations.append(
                    "END HUMAN_REVIEW_SUGGESTION "
                    "marker must be a Python comment "
                    f"at line {index + 1}."
                )

    code_has_human_review = bool(
        begin_indexes
        or end_indexes
    )

    # ========================================================
    # Generated code must not invent a Human Review suggestion
    # ========================================================

    if (
        code_has_human_review
        and not plan_has_human_review
    ):
        violations.append(
            "Generated code contains a "
            "HUMAN_REVIEW_SUGGESTION that does not "
            "exist in the validated migration plan."
        )

    # ========================================================
    # A validated suggestion must not disappear
    # ========================================================

    if (
        plan_has_human_review
        and not code_has_human_review
    ):
        violations.append(
            "Validated migration plan contains a "
            "HUMAN_REVIEW_SUGGESTION, but generated "
            "code does not preserve it inside an explicit "
            "BEGIN/END human-review block."
        )

        return violations

    if not code_has_human_review:
        return violations

    # ========================================================
    # BEGIN / END markers must be balanced
    # ========================================================

    if (
        len(begin_indexes)
        != len(end_indexes)
    ):
        violations.append(
            "HUMAN_REVIEW_SUGGESTION markers are "
            "unbalanced: every BEGIN marker must have "
            "exactly one END marker."
        )

        return violations

    # ========================================================
    # Validate every Human Review block
    # ========================================================

    previous_end_index = -1

    for block_number, (
        begin_index,
        end_index,
    ) in enumerate(
        zip(
            begin_indexes,
            end_indexes,
        ),
        start=1,
    ):
        # ----------------------------------------------------
        # Prevent overlapping / malformed blocks
        # ----------------------------------------------------

        if begin_index <= previous_end_index:
            violations.append(
                "HUMAN_REVIEW_SUGGESTION "
                f"{block_number} overlaps a previous "
                "Human Review block."
            )

        if end_index <= begin_index:
            violations.append(
                "HUMAN_REVIEW_SUGGESTION "
                f"{block_number} has END before BEGIN."
            )

            continue

        previous_end_index = end_index

        block_lines = lines[
            begin_index:end_index + 1
        ]

        # ----------------------------------------------------
        # Every line must be non-executable
        # ----------------------------------------------------

        for relative_index, line in enumerate(
            block_lines
        ):
            line_number = (
                begin_index
                + relative_index
                + 1
            )

            stripped = line.strip()

            if not stripped:
                continue

            if not stripped.startswith("#"):
                violations.append(
                    "Executable code detected inside "
                    "HUMAN_REVIEW_SUGGESTION "
                    f"{block_number} at line "
                    f"{line_number}: {stripped}"
                )

        block_text = "\n".join(
            block_lines
        ).lower()

        # ----------------------------------------------------
        # Required Human Review metadata
        # ----------------------------------------------------

        if (
            HUMAN_REVIEW_REQUIRED_MARKER.lower()
            not in block_text
        ):
            violations.append(
                "HUMAN_REVIEW_SUGGESTION "
                f"{block_number} is missing "
                "'HUMAN REVIEW REQUIRED'."
            )

        if (
            "status: human_review_suggestion"
            not in block_text
        ):
            violations.append(
                "HUMAN_REVIEW_SUGGESTION "
                f"{block_number} is missing "
                "'Status: HUMAN_REVIEW_SUGGESTION'."
            )

        if "confidence:" not in block_text:
            violations.append(
                "HUMAN_REVIEW_SUGGESTION "
                f"{block_number} is missing "
                "a confidence level."
            )

        if not (
            "confidence: low"
            in block_text
            or "confidence: medium"
            in block_text
        ):
            violations.append(
                "HUMAN_REVIEW_SUGGESTION "
                f"{block_number} must use "
                "Confidence: LOW or "
                "Confidence: MEDIUM."
            )

        if (
            "not an approved"
            not in block_text
            and
            "not approved"
            not in block_text
        ):
            violations.append(
                "HUMAN_REVIEW_SUGGESTION "
                f"{block_number} does not clearly "
                "state that the suggestion is not "
                "an approved migration implementation."
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

def validate_mapping_code(
    code: str,
    single_mapping: dict[str, Any],
    migration_plan: str = "",
) -> list[str]:
    """
    Run all deterministic validation rules for one generated mapping.

    The validator combines:

    - Python syntax validation
    - negative anti-hallucination checks
    - positive preservation checks
    - HUMAN_REVIEW_SUGGESTION safety validation

    HUMAN REVIEW material may exist in generated code only
    when it originated from the validated migration plan and
    remains entirely non-executable.
    """

    violations = []

    violations.extend(
        validate_python_syntax(
            code=code,
        )
    )

    violations.extend(
        validate_structural_completeness(
            code=code,
        )
    )

    violations.extend(
        validate_human_review_safety(
            code=code,
            migration_plan=migration_plan,
        )
    )

    violations.extend(
        validate_setvariable_usage(
            code=code,
            single_mapping=single_mapping,
        )
    )

    violations.extend(
        validate_setvariable_preservation(
            code=code,
            single_mapping=single_mapping,
        )
    )

    violations.extend(
        validate_flat_file_target(
            code=code,
            single_mapping=single_mapping,
        )
    )

    violations.extend(
        validate_unresolved_source_configuration(
            code=code,
            single_mapping=single_mapping,
        )
    )

    return violations


def validate_generated_code_node(
    state: AgentState,
) -> dict:
    """
    Validate the generated PySpark for the PowerCenter
    mapping selected in the current agent execution.

    The result shape is intentionally compatible with
    the repair node: each mapping result contains
    mapping_name, passed, and violations.
    """

    print(
        "\nValidating generated PySpark..."
    )

    mapping = state["mapping"]

    powercenter_project = state[
        "powercenter_project"
    ]

    generated_codes = state.get(
        "generated_codes",
        {},
    )

    migration_plans = state.get(
        "migration_plans",
        {},
    )

    # The graph processes one selected mapping.
    pc_mappings = [
        mapping
    ]

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

        migration_plan = migration_plans.get(
            mapping_name,
            "",
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
                    full_mapping=powercenter_project,
                    pc_mapping=pc_mapping,
                )
            )

            violations = (
                validate_mapping_code(
                    code=code,
                    single_mapping=single_mapping,
                    migration_plan=migration_plan,
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

    # Calculate the overall result after all mappings
    # have been validated.
    validation_passed = (
        len(validation_results) > 0
        and all(
            result["passed"]
            for result in validation_results
        )
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

