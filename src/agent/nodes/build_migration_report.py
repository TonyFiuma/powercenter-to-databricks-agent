import json
from pathlib import Path
from typing import Any

from src.agent.state import AgentState


OUTPUT_DIR = Path("data/output")
GENERATED_DIR = OUTPUT_DIR / "generated"
REPORT_PATH = OUTPUT_DIR / "migration_report.json"


def strip_markdown_fences(
    code: str,
) -> str:
    """
    Remove Markdown code fences from generated Python
    before writing the final .py artifact.
    """

    cleaned_lines = []

    for line in code.splitlines():
        if line.strip().startswith("```"):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip() + "\n"


def extract_unresolved_items(
    migration_plan: str,
    generated_code: str,
) -> list[str]:
    """
    Extract only meaningful unresolved migration items.

    Avoids generic headings, duplicated TODO markers,
    positive pass-through information, and commented
    implementation examples.
    """

    items = []
    seen = set()

    ignored_fragments = (
        "has no explicit filter",
        "no filter, join",
        "unresolved properties:",
        "configure target flat file output",
        "implement target write",
        "uncomment and specify driver",
    )

    def add_item(value: str):
        normalized = " ".join(
            value.strip().split()
        )

        if not normalized:
            return

        lower_value = normalized.lower()

        if any(
            fragment in lower_value
            for fragment in ignored_fragments
        ):
            return

        if normalized in seen:
            return

        seen.add(normalized)
        items.append(normalized)

    # --------------------------------------------
    # Migration plan
    # --------------------------------------------

    for line in migration_plan.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        upper_line = stripped.upper()

        if "[UNRESOLVED]" not in upper_line:
            continue

        cleaned = (
            stripped
            .replace("[UNRESOLVED]", "")
            .replace("**", "")
            .strip(" -|")
            .strip()
        )

        add_item(cleaned)

    # --------------------------------------------
    # Generated PySpark
    # --------------------------------------------

    for line in generated_code.splitlines():
        stripped = line.strip()

        if not stripped.startswith("#"):
            continue

        comment = stripped.lstrip("#").strip()

        upper_comment = comment.upper()

        if (
            "TODO" not in upper_comment
            and "UNRESOLVED"
            not in upper_comment
        ):
            continue

        cleaned = (
            comment
            .replace("TODO:", "")
            .replace("TODO", "")
            .strip()
        )

        add_item(cleaned)

    return items


def _result_by_mapping(
    results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        result.get(
            "mapping_name",
            "UNKNOWN_MAPPING",
        ): result
        for result in results
    }


def _status_for_mapping(
    plan_passed: bool,
    code_passed: bool,
    unresolved_items: list[str],
) -> str:
    if not plan_passed or not code_passed:
        return "FAILED_VALIDATION"

    if unresolved_items:
        return "READY_WITH_UNRESOLVED_ITEMS"

    return "READY"


def build_migration_report_node(
    state: AgentState,
) -> dict:
    """
    Export validated migration artifacts.

    Produces:
    - one sanitized .py file per mapping
    - data/output/migration_report.json

    Validation status and deployment readiness are kept
    separate: valid code may still contain unresolved
    configuration that requires human input.
    """

    print(
        "\nBuilding migration artifacts..."
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    GENERATED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # state["mapping"] contains the single mapping
    # selected by parse_mapping_node.
    mapping = state.get(
        "mapping"
    )

    if not mapping:
        raise ValueError(
            "Selected PowerCenter mapping not found "
            "in agent state."
        )

    pc_mappings = [
        mapping
    ]

    migration_plans = state.get(
        "migration_plans",
        {},
    )
    generated_codes = state.get(
        "generated_codes",
        {},
    )

    plan_results = _result_by_mapping(
        state.get(
            "migration_plan_validation_results",
            [],
        )
    )

    code_results = _result_by_mapping(
        state.get(
            "validation_results",
            [],
        )
    )

    report_mappings = []
    exported_files = {}

    for pc_mapping in pc_mappings:
        mapping_name = pc_mapping.get(
            "name",
            "UNKNOWN_MAPPING",
        )

        migration_plan = migration_plans.get(
            mapping_name,
            "",
        )
        generated_code = generated_codes.get(
            mapping_name,
            "",
        )

        plan_result = plan_results.get(
            mapping_name,
            {},
        )
        code_result = code_results.get(
            mapping_name,
            {},
        )

        plan_passed = bool(
            plan_result.get(
                "passed",
                False,
            )
        )
        code_passed = bool(
            code_result.get(
                "passed",
                False,
            )
        )

        unresolved_items = (
            extract_unresolved_items(
                migration_plan=(
                    migration_plan
                ),
                generated_code=(
                    generated_code
                ),
            )
        )

        status = _status_for_mapping(
            plan_passed=plan_passed,
            code_passed=code_passed,
            unresolved_items=(
                unresolved_items
            ),
        )

        python_path = None

        if generated_code.strip():
            clean_code = (
                strip_markdown_fences(
                    generated_code
                )
            )

            python_path = (
                GENERATED_DIR
                / f"{mapping_name}.py"
            )

            python_path.write_text(
                clean_code,
                encoding="utf-8",
            )

            exported_files[
                mapping_name
            ] = str(
                python_path
            )

        report_mappings.append(
            {
                "mapping_name": mapping_name,
                "status": status,
                "plan_validation": (
                    "PASSED"
                    if plan_passed
                    else "FAILED"
                ),
                "code_validation": (
                    "PASSED"
                    if code_passed
                    else "FAILED"
                ),
                "plan_violations": (
                    plan_result.get(
                        "violations",
                        [],
                    )
                ),
                "code_violations": (
                    code_result.get(
                        "violations",
                        [],
                    )
                ),
                "unresolved_items": (
                    unresolved_items
                ),
                "generated_python_file": (
                    str(python_path)
                    if python_path
                    else None
                ),
            }
        )

    overall_status = "READY"

    if any(
        item["status"]
        == "FAILED_VALIDATION"
        for item in report_mappings
    ):
        overall_status = (
            "FAILED_VALIDATION"
        )
    elif any(
        item["status"]
        == "READY_WITH_UNRESOLVED_ITEMS"
        for item in report_mappings
    ):
        overall_status = (
            "READY_WITH_UNRESOLVED_ITEMS"
        )

    report = {
        "source_xml": state.get(
            "xml_path"
        ),
        "overall_status": (
            overall_status
        ),
        "migration_plan_validation_passed": (
            state.get(
                "migration_plan_validation_passed",
                False,
            )
        ),
        "code_validation_passed": (
            state.get(
                "validation_passed",
                False,
            )
        ),
        "migration_plan_repair_attempts": (
            state.get(
                "migration_plan_repair_attempts",
                0,
            )
        ),
        "code_repair_attempts": (
            state.get(
                "repair_attempts",
                0,
            )
        ),
        "mapping_count": len(
            report_mappings
        ),
        "mappings": report_mappings,
    }

    REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Migration report saved: "
        f"{REPORT_PATH}"
    )
    print(
        f"Generated Python files: "
        f"{len(exported_files)}"
    )
    print(
        f"Overall migration status: "
        f"{overall_status}"
    )

    return {
        "migration_report": report,
        "migration_report_path": (
            str(REPORT_PATH)
        ),
        "exported_files": (
            exported_files
        ),
    }