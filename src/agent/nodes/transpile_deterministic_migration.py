from typing import Any

from src.agent.state import AgentState
from src.transpiler.databricks_runtime_variable import (
    build_databricks_runtime_variables,
)
from src.transpiler.databricks_sql_runtime import (
    apply_runtime_variables_to_sql,
)
from src.transpiler.graph_transpiler import (
    transpile_data_flow_to_sql,
)


def resolve_target_node(
    mapping: dict[str, Any],
) -> str:
    """
    Resolve the target node of the selected
    PowerCenter mapping.

    MVP constraint:
    exactly one target must exist.
    """

    targets = mapping.get(
        "targets",
        []
    )

    if not targets:
        raise ValueError(
            "No target found in PowerCenter "
            f"mapping '{mapping.get('name')}'."
        )

    if len(targets) > 1:
        raise ValueError(
            "Multiple targets found in "
            "PowerCenter mapping "
            f"'{mapping.get('name')}'. "
            "Explicit target selection is "
            "required."
        )

    target = targets[0]

    if isinstance(target, str):
        return target

    if isinstance(target, dict):
        target_name = (
            target.get("name")
            or target.get("instance_name")
            or target.get("target_name")
        )

        if target_name:
            return target_name

    raise ValueError(
        "Unable to resolve target node from "
        f"mapping '{mapping.get('name')}'."
    )


def transpile_deterministic_migration_node(
    state: AgentState,
) -> dict[str, Any]:
    """
    Execute deterministic PowerCenter mapping
    transpilation and runtime-variable rendering.

    Input state:

        mapping
        mapplets
        workflow
        session

    Output state:

        powercenter_sql
        databricks_sql
    """

    mapping = state.get("mapping")
    mapplets = state.get(
        "mapplets",
        [],
    )
    workflow = state.get("workflow")
    session = state.get("session")

    if mapping is None:
        raise ValueError(
            "mapping is required before "
            "deterministic transpilation."
        )

    if workflow is None:
        raise ValueError(
            "workflow is required before "
            "deterministic transpilation."
        )

    if session is None:
        raise ValueError(
            "session is required before "
            "deterministic transpilation."
        )

    target_node = resolve_target_node(
        mapping
    )

    print(
        "\nRunning deterministic "
        "PowerCenter transpilation."
    )

    print(
        f"Mapping: {mapping.get('name')}"
    )

    print(
        f"Target: {target_node}"
    )

    powercenter_sql = (
        transpile_data_flow_to_sql(
            mapping=mapping,
            mapplets=mapplets,
            target_node=target_node,
        )
    )

    runtime_variables = (
        build_databricks_runtime_variables(
            mapping=mapping,
            session=session,
            workflow=workflow,
        )
    )

    databricks_sql = (
        apply_runtime_variables_to_sql(
            sql=powercenter_sql,
            runtime_variables=runtime_variables,
        )
    )

    print(
        "Deterministic transpilation "
        "completed successfully."
    )

    return {
        "powercenter_sql": powercenter_sql,
        "databricks_sql": databricks_sql,
    }