import time

from groq import RateLimitError

from src.agent.context.mapping_context import (
    build_mapping_context,
    build_single_mapping_input,
)
from src.agent.prompts.migration_plan_repair_prompt import (
    build_migration_plan_repair_prompt,
)
from src.agent.state import AgentState
from src.llm.provider import get_planner_llm
from src.storage.migration_plan_store import (
    save_migration_plans,
)


MAX_LLM_RETRIES = 3
RETRY_WAIT_SECONDS = 4


def invoke_repair_llm_with_retry(
    llm,
    prompt: str,
):
    """
    Invoke the planner LLM with retry handling
    for Groq rate-limit errors.
    """

    for attempt in range(
        1,
        MAX_LLM_RETRIES + 1,
    ):
        try:
            print(
                f"Repair LLM attempt "
                f"{attempt}/{MAX_LLM_RETRIES}..."
            )

            return llm.invoke(
                prompt
            )

        except RateLimitError:
            print(
                "\nGroq rate limit reached "
                "during migration-plan repair."
            )

            if attempt >= MAX_LLM_RETRIES:
                print(
                    "Maximum migration-plan repair "
                    "retries reached."
                )
                raise

            print(
                f"Retrying in "
                f"{RETRY_WAIT_SECONDS} seconds..."
            )

            time.sleep(
                RETRY_WAIT_SECONDS
            )


def repair_migration_plan_node(
    state: AgentState,
) -> dict:
    """
    Repair migration plans that failed deterministic
    validation.

    The current AgentState contains:

    - mapping:
        the single PowerCenter mapping selected
        for the current graph execution;

    - powercenter_project:
        the complete parsed PowerCenter project;

    - migration_plans:
        migration plans indexed by mapping name;

    - migration_plan_validation_results:
        deterministic validation results.

    Only failed plans are sent to the repair LLM.

    Repaired plans are persisted immediately in the
    migration-plan cache.
    """

    print(
        "\nRepairing failed migration plans..."
    )

    mapping = state["mapping"]

    powercenter_project = state[
        "powercenter_project"
    ]

    xml_path = state["xml_path"]

    migration_plans = dict(
        state.get(
            "migration_plans",
            {},
        )
    )

    validation_results = state.get(
        "migration_plan_validation_results",
        [],
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
        "Failed migration plans to repair: "
        f"{len(failed_results)}"
    )

    # A failed validation with no failed result is an
    # inconsistent graph state. There is nothing that
    # the repair node can safely repair.
    if not failed_results:
        raise RuntimeError(
            "Migration plan validation failed, but no "
            "failed migration plans were provided to "
            "the repair node. The graph cannot "
            "continue safely."
        )

    # The graph processes exactly one selected mapping.
    # Keep a list here for compatibility with the
    # existing repair logic and combined-plan handling.
    pc_mappings = [
        mapping
    ]

    mapping_by_name = {
        pc_mapping.get(
            "name",
            "UNKNOWN_MAPPING",
        ): pc_mapping
        for pc_mapping in pc_mappings
    }

    # Lazy initialization:
    # instantiate the LLM only when there is actually
    # something to repair.
    llm = get_planner_llm()

    for index, result in enumerate(
        failed_results,
        start=1,
    ):
        mapping_name = result.get(
            "mapping_name",
            "UNKNOWN_MAPPING",
        )

        violations = result.get(
            "violations",
            [],
        )

        print("")
        print(
            f"[{index}/{len(failed_results)}] "
            f"Repairing migration plan: "
            f"{mapping_name}"
        )

        print(
            "Violations received: "
            f"{len(violations)}"
        )

        for violation in violations:
            print(
                f"  - {violation}"
            )

        pc_mapping = mapping_by_name.get(
            mapping_name
        )

        if pc_mapping is None:
            raise ValueError(
                "Parsed mapping not found for "
                "migration-plan repair: "
                f"{mapping_name}"
            )

        current_plan = migration_plans.get(
            mapping_name
        )

        if (
            not isinstance(
                current_plan,
                str,
            )
            or not current_plan.strip()
        ):
            raise ValueError(
                "Migration plan not found for "
                f"repair: {mapping_name}"
            )

        # Rebuild the structure expected by
        # build_mapping_context().
        #
        # The full project provides repository/folder
        # and global metadata, while pc_mapping is the
        # single mapping being repaired.
        single_mapping = (
            build_single_mapping_input(
                full_mapping=powercenter_project,
                pc_mapping=pc_mapping,
            )
        )

        mapping_context = (
            build_mapping_context(
                single_mapping
            )
        )

        prompt = (
            build_migration_plan_repair_prompt(
                mapping_context=(
                    mapping_context
                ),
                current_plan=(
                    current_plan
                ),
                violations=violations,
            )
        )

        print(
            "Migration plan repair prompt "
            f"characters: {len(prompt)}"
        )

        print(
            "Sending migration-plan repair "
            "request to LLM..."
        )

        response = (
            invoke_repair_llm_with_retry(
                llm=llm,
                prompt=prompt,
            )
        )

        repaired_plan = (
            response.content.strip()
        )

        print(
            "Migration-plan repair "
            "response received."
        )

        print(
            "Repaired migration plan "
            f"characters: {len(repaired_plan)}"
        )

        if not repaired_plan:
            print(
                "Repair returned an empty plan."
            )

            print(
                "Keeping previous migration plan."
            )

            continue

        migration_plans[
            mapping_name
        ] = repaired_plan

        # Persist immediately so a later failure does
        # not lose an already repaired migration plan.
        save_migration_plans(
            source_xml=xml_path,
            migration_plans=migration_plans,
        )

        print(
            "Repaired migration plan "
            "saved to cache."
        )

    # Rebuild the combined plan in mapping order.
    # The current graph executes one mapping, but this
    # keeps the return contract compatible with the
    # rest of the agent.
    ordered_plans = []

    for pc_mapping in pc_mappings:
        mapping_name = pc_mapping.get(
            "name",
            "UNKNOWN_MAPPING",
        )

        plan = migration_plans.get(
            mapping_name
        )

        if (
            not isinstance(
                plan,
                str,
            )
            or not plan.strip()
        ):
            raise ValueError(
                "Migration plan missing after "
                f"repair: {mapping_name}"
            )

        ordered_plans.append(
            plan
        )

    combined_plan = "\n\n".join(
        ordered_plans
    )

    repair_attempts = (
        state.get(
            "migration_plan_repair_attempts",
            0,
        )
        + 1
    )

    print("")

    print(
        "Migration-plan repair round "
        "completed."
    )

    print(
        "Migration-plan repair attempts: "
        f"{repair_attempts}"
    )

    return {
        "migration_plans": migration_plans,
        "migration_plan": combined_plan,
        "migration_plan_repair_attempts": (
            repair_attempts
        ),
    }