import traceback

from src.agent.state import AgentState

from src.agent.context.mapping_context import (
    build_single_mapping_input,
)

from src.agent.context.generator_context import (
    build_generator_context,
)

from src.agent.prompts.pyspark_generator_prompt import (
    build_pyspark_prompt,
)

from src.llm.provider import (
    get_generator_llm,
)

from src.storage.generated_code_store import (
    is_usable_generated_code,
    load_generated_codes,
    save_generated_codes,
)



def generate_pyspark_node(
    state: AgentState,
) -> dict:
    """
    Generate PySpark code for every PowerCenter mapping.

    Generated code is persisted after every successful
    mapping so the process can resume after failures
    or rate limits.

    Empty or anomalous LLM responses are never cached.
    """

    print(
        "\nGenerating PySpark code..."
    )

    # ==================================================
    # Read state
    # ==================================================

    xml_path = state.get(
        "xml_path"
    )

    mapping = state.get(
        "mapping"
    )

    migration_plans = state.get(
        "migration_plans",
        {},
    )

    if not xml_path:
        raise ValueError(
            "XML path not found in agent state."
        )

    if not mapping:
        raise ValueError(
            "Parsed mapping not found in agent state."
        )

    if not migration_plans:
        raise ValueError(
            "Migration plans not found in agent state."
        )

    # ==================================================
    # Get PowerCenter mappings
    # ==================================================

    mappings = mapping.get(
        "mappings",
        [],
    )

    if not mappings:
        raise ValueError(
            "No mappings found in parsed "
            "PowerCenter XML."
        )

    print(
        f"Mappings to generate: "
        f"{len(mappings)}"
    )

    # ==================================================
    # Load generated-code cache
    # ==================================================

    generated_codes = (
        load_generated_codes(
            source_xml=xml_path,
        )
    )

    # ==================================================
    # Generate mapping by mapping
    # ==================================================

    for index, pc_mapping in enumerate(
        mappings,
        start=1,
    ):
        mapping_name = pc_mapping.get(
            "name"
        )

        if not mapping_name:
            print(
                f"\n[{index}/{len(mappings)}] "
                "Skipping mapping without name."
            )
            continue

        print(
            f"\n[{index}/{len(mappings)}] "
            f"Generating PySpark for: "
            f"{mapping_name}"
        )

        # ==============================================
        # CACHE HIT
        # ==============================================

        if mapping_name in generated_codes:
            cached_code = generated_codes[
                mapping_name
            ]

            print(
                "Generated PySpark found "
                "in cache."
            )

            print(
                "Cached PySpark characters: "
                f"{len(cached_code)}"
            )

            continue

        # ==============================================
        # Migration plan
        # ==============================================

        migration_plan = (
            migration_plans.get(
                mapping_name
            )
        )

        if not migration_plan:
            raise ValueError(
                "Migration plan not found for "
                f"mapping: {mapping_name}"
            )

        print(
            "Migration plan found: "
            f"{len(migration_plan)} characters"
        )

        # ==============================================
        # Build single-mapping input
        # ==============================================

        single_mapping = (
            build_single_mapping_input(
                full_mapping=mapping,
                pc_mapping=pc_mapping,
            )
        )

        # ==============================================
        # Compact generator context
        # ==============================================

        mapping_context = (
            build_generator_context(
                single_mapping
            )
        )

        print(
            "Generator mapping context "
            "characters: "
            f"{len(mapping_context)}"
        )

        print(
            "Migration plan characters: "
            f"{len(migration_plan)}"
        )

        # ==============================================
        # Build prompt
        # ==============================================

        prompt = build_pyspark_prompt(
            mapping_context=(
                mapping_context
            ),
            migration_plan=(
                migration_plan
            ),
        )

        print(
            "Generator prompt characters: "
            f"{len(prompt)}"
        )

        print(
            "Sending mapping to LLM..."
        )

        # ==============================================
        # LLM call
        # ==============================================

        try:
            llm = get_generator_llm()

            response = llm.invoke(
                prompt
            )

        except Exception as exc:
            print(
                "\nLLM CALL FAILED for mapping: "
                f"{mapping_name}"
            )

            print(
                "Error type: "
                f"{type(exc).__name__}"
            )

            print(
                "Error: "
                f"{exc}"
            )

            print(
                "\nPreviously generated mappings "
                "have been preserved in cache."
            )

            traceback.print_exc()

            raise
        # ==============================================
        # Extract generated code
        # ==============================================

        pyspark_code = response.content

        if not isinstance(
            pyspark_code,
            str,
        ):
            pyspark_code = str(
                pyspark_code
            )

        pyspark_code = (
            pyspark_code.strip()
        )

        print(
            "PySpark response received."
        )

        print(
            "Generated PySpark characters: "
            f"{len(pyspark_code)}"
        )

        # ==============================================
        # Validate LLM response before caching
        # ==============================================

        if not is_usable_generated_code(
            pyspark_code
        ):
            print(
                "Invalid PySpark response "
                f"for mapping: {mapping_name}"
            )

            print(
                "Response will NOT be cached."
            )

            raise ValueError(
                "LLM returned unusable PySpark "
                f"code for mapping: {mapping_name}"
            )

        # ==============================================
        # Persist immediately
        # ==============================================

        generated_codes[
            mapping_name
        ] = pyspark_code

        save_generated_codes(
            source_xml=xml_path,
            generated_codes=generated_codes,
        )

        print(
            "Generated PySpark saved "
            "to cache."
        )

    # ==================================================
    # Build combined output
    # ==================================================

    combined_sections = []

    for pc_mapping in mappings:
        mapping_name = pc_mapping.get(
            "name"
        )

        if not mapping_name:
            continue

        pyspark_code = generated_codes.get(
            mapping_name
        )

        if not pyspark_code:
            continue

        combined_sections.append(
            (
                "# ======================================\n"
                f"# Mapping: {mapping_name}\n"
                "# ======================================\n\n"
                f"{pyspark_code}"
            )
        )

    combined_code = (
        "\n\n\n".join(
            combined_sections
        )
    )

    # ==================================================
    # Summary
    # ==================================================

    print(
        "\nPySpark generation completed."
    )

    print(
        "Generated mappings available: "
        f"{len(generated_codes)}"
    )

    for mapping_name, code in (
        generated_codes.items()
    ):
        print(
            f"- {mapping_name}: "
            f"{len(code)} characters"
        )

    # ==================================================
    # Update LangGraph state
    # ==================================================

    return {
        "pyspark_code": combined_code,
        "generated_codes": generated_codes,
    }