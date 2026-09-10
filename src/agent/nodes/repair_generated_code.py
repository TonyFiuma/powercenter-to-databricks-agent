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


llm = get_generator_llm()


def repair_generated_code_node(
    state: AgentState,
) -> dict:
    """
    Repair generated PySpark code that failed
    deterministic validation.

    Only failed mappings are sent back to the LLM.
    """

    print(
        "\nRepairing failed PySpark mappings..."
    )

    xml_path = state.get(
        "xml_path"
    )

    full_mapping = state.get(
        "mapping"
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

    if not full_mapping:
        raise ValueError(
            "Parsed mapping not found in agent state."
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

    mappings = full_mapping.get(
        "mappings",
        [],
    )

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
                full_mapping=full_mapping,
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

        repaired_code = (
            repaired_code.strip()
        )

        print(
            "Repair response received."
        )

        print(
            "Repaired PySpark characters: "
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