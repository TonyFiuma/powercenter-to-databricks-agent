from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from src.agent.state import AgentState

from src.agent.nodes.parse_mapping import (
    parse_mapping_node,
)
from src.agent.nodes.retrieve_docs import (
    retrieve_docs_node,
)
from src.agent.nodes.create_migration_plan import (
    create_migration_plan_node,
)
from src.agent.nodes.validate_migration_plan import (
    validate_migration_plan_node,
)
from src.agent.nodes.repair_migration_plan import (
    repair_migration_plan_node,
)
from src.agent.nodes.generate_pyspark import (
    generate_pyspark_node,
)
from src.agent.nodes.validate_generated_code import (
    validate_generated_code_node,
)
from src.agent.nodes.repair_generated_code import (
    repair_generated_code_node,
)
from src.agent.nodes.build_migration_report import (
    build_migration_report_node,
)

from src.agent.nodes.resolve_version import (
    resolve_powercenter_version_node,
)

# ============================================================
# Configuration
# ============================================================

MAX_MIGRATION_PLAN_REPAIR_ATTEMPTS = 2
MAX_CODE_REPAIR_ATTEMPTS = 2


# ============================================================
# Migration-plan routing
# ============================================================

def route_after_migration_plan_validation(
    state: AgentState,
) -> str:
    """
    Decide whether migration plans can proceed to PySpark
    generation or require another repair round.
    """

    validation_passed = state.get(
        "migration_plan_validation_passed",
        False,
    )

    if validation_passed:
        print(
            "\nMigration plan validation passed."
        )
        print(
            "Proceeding to PySpark generation."
        )
        return "generate"

    repair_attempts = state.get(
        "migration_plan_repair_attempts",
        0,
    )

    print(
        "\nMigration plan validation failed."
    )

    print(
        "Migration-plan repair attempts "
        f"completed: {repair_attempts}"
    )

    if (
        repair_attempts
        >= MAX_MIGRATION_PLAN_REPAIR_ATTEMPTS
    ):
        raise RuntimeError(
            "Migration plan validation still failed "
            "after the maximum number of repair "
            "attempts. PySpark generation has been "
            "stopped to avoid generating code from "
            "an invalid migration plan."
        )

    print(
        "Starting migration-plan repair round "
        f"{repair_attempts + 1} of "
        f"{MAX_MIGRATION_PLAN_REPAIR_ATTEMPTS}."
    )

    return "repair"


# ============================================================
# Generated-code routing
# ============================================================

def route_after_code_validation(
    state: AgentState,
) -> str:
    """
    Decide what to do after generated PySpark validation.
    """

    validation_passed = state.get(
        "validation_passed",
        False,
    )

    if validation_passed:
        print(
            "\nGenerated PySpark validation passed."
        )
        print(
            "No repair required."
        )
        return "export"

    repair_attempts = state.get(
        "repair_attempts",
        0,
    )

    print(
        "\nGenerated PySpark validation failed."
    )

    print(
        "Repair attempts completed: "
        f"{repair_attempts}"
    )

    if (
        repair_attempts
        >= MAX_CODE_REPAIR_ATTEMPTS
    ):
        print(
            "Maximum repair attempts reached."
        )
        print(
            "Stopping workflow with unresolved "
            "validation violations."
        )
        return "export"

    print(
        "Starting PySpark repair round "
        f"{repair_attempts + 1} of "
        f"{MAX_CODE_REPAIR_ATTEMPTS}."
    )

    return "repair"


def build_graph():
    """
    Build the deterministic PowerCenter -> Databricks
    migration workflow.

    Flow:

    parser
    -> PowerCenter version resolution
    -> retrieval
    -> migration planner
    -> migration-plan validator
        -> repair loop when needed
    -> PySpark generator
    -> PySpark validator
        -> repair loop when needed
    -> migration artifact export
    -> END
    """

    graph = StateGraph(
        AgentState
    )

    # --------------------------------------------------------
    # Nodes
    # --------------------------------------------------------

    graph.add_node(
        "parse_mapping",
        parse_mapping_node,
    )

    graph.add_node(
        "resolve_powercenter_version",
        resolve_powercenter_version_node,
    )

    graph.add_node(
        "retrieve_docs",
        retrieve_docs_node,
    )

    graph.add_node(
        "create_migration_plan",
        create_migration_plan_node,
    )

    graph.add_node(
        "validate_migration_plan",
        validate_migration_plan_node,
    )

    graph.add_node(
        "repair_migration_plan",
        repair_migration_plan_node,
    )

    graph.add_node(
        "generate_pyspark",
        generate_pyspark_node,
    )

    graph.add_node(
        "validate_generated_code",
        validate_generated_code_node,
    )

    graph.add_node(
        "repair_generated_code",
        repair_generated_code_node,
    )

    graph.add_node(
        "build_migration_report",
        build_migration_report_node,
    )

    # --------------------------------------------------------
    # Main flow
    # --------------------------------------------------------

    graph.add_edge(
        START,
        "parse_mapping",
    )

    graph.add_edge(
        "parse_mapping",
        "resolve_powercenter_version",
    )

    graph.add_edge(
        "resolve_powercenter_version",
        "retrieve_docs",
    )

    graph.add_edge(
        "retrieve_docs",
        "create_migration_plan",
    )

    graph.add_edge(
        "create_migration_plan",
        "validate_migration_plan",
    )

    # --------------------------------------------------------
    # Migration-plan repair loop
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "validate_migration_plan",
        route_after_migration_plan_validation,
        {
            "repair": (
                "repair_migration_plan"
            ),
            "generate": (
                "generate_pyspark"
            ),
        },
    )

    graph.add_edge(
        "repair_migration_plan",
        "validate_migration_plan",
    )

    # --------------------------------------------------------
    # PySpark generation + repair loop
    # --------------------------------------------------------

    graph.add_edge(
        "generate_pyspark",
        "validate_generated_code",
    )

    graph.add_conditional_edges(
        "validate_generated_code",
        route_after_code_validation,
        {
            "repair": (
                "repair_generated_code"
            ),
            "export": (
                "build_migration_report"
            ),
        },
    )

    graph.add_edge(
        "repair_generated_code",
        "validate_generated_code",
    )

    graph.add_edge(
        "build_migration_report",
        END,
    )

    return graph.compile()


migration_graph = build_graph()
