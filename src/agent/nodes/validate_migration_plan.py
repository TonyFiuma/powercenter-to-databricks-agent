from src.agent.state import AgentState
from src.validator.migration_plan_validator import (
    validate_migration_plan,
)


def validate_migration_plan_node(
    state: AgentState,
) -> dict:
    """
    Validate migration plans before PySpark generation.
    """
    print("\n>>> MIGRATION PLAN VALIDATOR NODE EXECUTED <<<")
    
    migration_plans = state.get(
        "migration_plans",
        {},
    )

    print("\nValidating migration plans...")
    print(
        f"Plans to validate: {len(migration_plans)}"
    )

    validation_results = []

    for index, (
        mapping_name,
        migration_plan,
    ) in enumerate(
        migration_plans.items(),
        start=1,
    ):
        print(
            f"\n[{index}/{len(migration_plans)}] "
            f"Validating plan: {mapping_name}"
        )

        result = validate_migration_plan(
            mapping_name=mapping_name,
            migration_plan=migration_plan,
        )

        validation_results.append(
            result
        )

        if result["passed"]:
            print("Migration plan validation passed.")
        else:
            print("Migration plan validation failed.")

            for violation in result[
                "violations"
            ]:
                print(
                    f"  - {violation}"
                )

    validation_passed = all(
        result["passed"]
        for result in validation_results
    )

    print(
        "\nMigration plan validation: "
        f"{'PASSED' if validation_passed else 'FAILED'}"
    )

    return {
        "migration_plan_validation_results":
            validation_results,
        "migration_plan_validation_passed":
            validation_passed,
    }