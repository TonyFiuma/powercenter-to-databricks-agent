import traceback

from src.agent.state import AgentState

from src.agent.context.mapping_context import (
    build_single_mapping_input,
)

from src.agent.context.generator_context import (
    build_generator_context,
)

from src.agent.prompts.pyspark_repair_prompt import (
    build_pyspark_repair_prompt,
)

from src.llm.provider import (
    get_generator_llm,
)

from src.storage.generated_code_store import (
    is_usable_generated_code,
    save_generated_codes,
)


HUMAN_REVIEW_BEGIN_MARKER = (
    "BEGIN HUMAN_REVIEW_SUGGESTION"
)

HUMAN_REVIEW_END_MARKER = (
    "END HUMAN_REVIEW_SUGGESTION"
)


def enforce_human_review_comment_safety(
    code: str,
) -> str:
    """
    Ensure that every line inside a generated
    HUMAN_REVIEW_SUGGESTION block is a Python comment.

    Expected structure:

    # BEGIN HUMAN_REVIEW_SUGGESTION
    # ...
    # suggested_code = ...
    # END HUMAN_REVIEW_SUGGESTION

    If the LLM accidentally produces executable code inside
    the block, this function comments it out deterministically
    before the repaired code is persisted.

    This function does not invent, remove, or approve any
    migration logic. It only prevents human-review material
    from becoming executable Python.
    """

    lines = code.splitlines()

    safe_lines = []

    inside_human_review = False

    for line in lines:
        stripped = line.strip()

        # ----------------------------------------------------
        # BEGIN marker
        # ----------------------------------------------------

        if (
            HUMAN_REVIEW_BEGIN_MARKER
            in stripped.upper()
        ):
            inside_human_review = True

            if stripped.startswith("#"):
                safe_lines.append(
                    line
                )
            else:
                indentation = (
                    line[
                        :len(line)
                        - len(
                            line.lstrip()
                        )
                    ]
                )

                safe_lines.append(
                    f"{indentation}# {stripped}"
                )

            continue

        # ----------------------------------------------------
        # END marker
        # ----------------------------------------------------

        if (
            HUMAN_REVIEW_END_MARKER
            in stripped.upper()
        ):
            if stripped.startswith("#"):
                safe_lines.append(
                    line
                )
            else:
                indentation = (
                    line[
                        :len(line)
                        - len(
                            line.lstrip()
                        )
                    ]
                )

                safe_lines.append(
                    f"{indentation}# {stripped}"
                )

            inside_human_review = False

            continue

        # ----------------------------------------------------
        # Human-review block
        # ----------------------------------------------------

        if inside_human_review:
            # Preserve empty lines.
            if not stripped:
                safe_lines.append(
                    line
                )
                continue

            # Already safe.
            if stripped.startswith("#"):
                safe_lines.append(
                    line
                )
                continue

            # Anything else would be executable Python.
            # Comment it out deterministically.
            indentation = (
                line[
                    :len(line)
                    - len(
                        line.lstrip()
                    )
                ]
            )

            safe_lines.append(
                f"{indentation}# {stripped}"
            )

            continue

        # ----------------------------------------------------
        # Normal executable migration code
        # ----------------------------------------------------

        safe_lines.append(
            line
        )

    return "\n".join(
        safe_lines
    )


def repair_generated_code_node(
    state: AgentState,
) -> dict:
    """
    Repair generated PySpark code that failed
    deterministic validation.

    Only failed mappings are sent back to the LLM.

    HUMAN_REVIEW_SUGGESTION content is additionally
    protected deterministically before persistence:
    any line inside a HUMAN REVIEW block is forced
    to remain a Python comment.
    """

    print(
        "\nRepairing failed PySpark mappings..."
    )

    xml_path = state.get(
        "xml_path"
    )

    mapping = state.get(
        "mapping"
    )

    powercenter_project = state.get(
        "powercenter_project"
    )

    generated_codes = dict(
        state.get(
            "generated_codes",
            {},
        )
    )

    migration_plans = state.get(
        "migration_plans",
        {},
    )

    validation_results = state.get(
        "validation_results",
        [],
    )

    repair_attempts = state.get(
        "repair_attempts",
        0,
    )

    if not xml_path:
        raise ValueError(
            "XML path not found in agent state."
        )

    if not mapping:
        raise ValueError(
            "Selected PowerCenter mapping not found "
            "in agent state."
        )

    if not powercenter_project:
        raise ValueError(
            "Complete PowerCenter project not found "
            "in agent state."
        )

    failed_results = [
        result
        for result in validation_results
        if not result.get(
            "passed",
            False,
        )
    ]

    print(
        "Failed mappings to repair: "
        f"{len(failed_results)}"
    )

    if not failed_results:
        return {
            "generated_codes": (
                generated_codes
            ),
            "repair_attempts": (
                repair_attempts
            ),
        }

    mappings = [
        mapping
    ]

    mappings_by_name = {
        mapping.get("name"): mapping
        for mapping in mappings
        if mapping.get("name")
    }

    # ========================================================
    # Repair each failed mapping
    # ========================================================

    for index, validation in enumerate(
        failed_results,
        start=1,
    ):
        mapping_name = validation.get(
            "mapping_name"
        )

        violations = validation.get(
            "violations",
            [],
        )

        print(
            f"\n[{index}/{len(failed_results)}] "
            f"Repairing: {mapping_name}"
        )

        if not mapping_name:
            print(
                "Skipping validation result "
                "without mapping name."
            )
            continue

        pc_mapping = mappings_by_name.get(
            mapping_name
        )

        if not pc_mapping:
            print(
                "PowerCenter mapping not found: "
                f"{mapping_name}"
            )
            continue

        current_code = generated_codes.get(
            mapping_name
        )

        if not current_code:
            print(
                "Generated PySpark code not found: "
                f"{mapping_name}"
            )
            continue

        migration_plan = migration_plans.get(
            mapping_name
        )

        if not migration_plan:
            print(
                "Migration plan not found: "
                f"{mapping_name}"
            )
            continue

        print(
            "Violations received: "
            f"{len(violations)}"
        )

        for violation in violations:
            print(
                f"  - {violation}"
            )

        # ----------------------------------------------------
        # Build isolated mapping
        # ----------------------------------------------------

        single_mapping = (
            build_single_mapping_input(
                full_mapping=powercenter_project,
                pc_mapping=pc_mapping,
            )
        )

        mapping_context = (
            build_generator_context(
                single_mapping
            )
        )

        # ----------------------------------------------------
        # Build repair prompt
        # ----------------------------------------------------

        prompt = build_pyspark_repair_prompt(
            mapping_context=(
                mapping_context
            ),
            migration_plan=(
                migration_plan
            ),
            current_code=(
                current_code
            ),
            violations=(
                violations
            ),
        )

        print(
            "Repair prompt characters: "
            f"{len(prompt)}"
        )

        print(
            "Sending repair request to LLM..."
        )

        # ----------------------------------------------------
        # LLM repair
        # ----------------------------------------------------

        try:
            llm = get_generator_llm()

            response = llm.invoke(
                prompt
            )

        except Exception as exc:
            print(
                "\nREPAIR LLM CALL FAILED "
                f"for mapping: {mapping_name}"
            )

            print(
                "Error type: "
                f"{type(exc).__name__}"
            )

            print(
                f"Error: {exc}"
            )

            traceback.print_exc()

            # Keep original code instead of
            # destroying the previous generation.
            continue

            repaired_code = response.content

        if not isinstance(
            repaired_code,
            str,
        ):
            repaired_code = str(
                repaired_code
            )

        repaired_code = repaired_code.strip()

        print(
            "PySpark repair response received."
        )

        print(
            "Raw repaired PySpark characters: "
            f"{len(repaired_code)}"
        )
        # ----------------------------------------------------
        # HUMAN REVIEW deterministic safety enforcement
        # ----------------------------------------------------

        repaired_code = (
            enforce_human_review_comment_safety(
                repaired_code
            )
        )

        repaired_code = (
            repaired_code.strip()
        )

        print(
            "Repaired PySpark characters "
            "after safety enforcement: "
            f"{len(repaired_code)}"
        )

        # ----------------------------------------------------
        # Reject obviously unusable responses
        # ----------------------------------------------------

        if not is_usable_generated_code(
            repaired_code
        ):
            print(
                "Repair returned unusable code."
            )

            print(
                "Keeping previous generated code."
            )

            continue

        # ----------------------------------------------------
        # Replace failed code
        # ----------------------------------------------------

        generated_codes[
            mapping_name
        ] = repaired_code

        # ----------------------------------------------------
        # Persist immediately
        # ----------------------------------------------------

        save_generated_codes(
            source_xml=xml_path,
            generated_codes=generated_codes,
        )

        print(
            "Repaired PySpark saved to cache."
        )

    # ========================================================
    # Rebuild combined output
    # ========================================================

    combined_sections = []

    for pc_mapping in mappings:
        mapping_name = pc_mapping.get(
            "name"
        )

        if not mapping_name:
            continue

        code = generated_codes.get(
            mapping_name
        )

        if not code:
            continue

        combined_sections.append(
            (
                "# ======================================\n"
                f"# Mapping: {mapping_name}\n"
                "# ======================================\n\n"
                f"{code}"
            )
        )

    combined_code = "\n\n\n".join(
        combined_sections
    )

    new_repair_attempts = (
        repair_attempts + 1
    )

    print(
        "\nRepair round completed."
    )

    print(
        "Repair attempts: "
        f"{new_repair_attempts}"
    )

    return {
        "generated_codes": (
            generated_codes
        ),
        "pyspark_code": (
            combined_code
        ),
        "repair_attempts": (
            new_repair_attempts
        ),
    }