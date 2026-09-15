from typing import Any

from src.transpiler.resolved_runtime_variable import (
    ResolvedRuntimeVariable,
)
from src.transpiler.runtime_parameter import (
    extract_mapping_runtime_parameters,
)


def build_session_variable_bindings(
    session: dict[str, Any],
) -> dict[str, str]:
    """
    Build mapping-variable bindings from the
    PowerCenter pre-session variable assignment
    component.

    Example:

        $$m_DT_RIFERIMENTO -> $$DT_RIFERIMENTO
        $$m_DT_LOAD        -> $$wf_DT_LOAD
    """

    bindings: dict[str, str] = {}

    for component in session.get(
        "components",
        [],
    ):
        if (
            component.get("type")
            != "Pre-session variable assignment"
        ):
            continue

        for value_pair in component.get(
            "value_pairs",
            [],
        ):
            name = value_pair.get("name")
            value = value_pair.get("value")

            if not name or not value:
                continue

            bindings[name] = value

    return bindings


def build_workflow_variable_assignments(
    workflow: dict[str, Any],
) -> dict[str, str]:
    """
    Build workflow-variable assignments from
    Assignment task definitions.

    Example:

        $$wf_DT_LOAD -> SYSDATE
    """

    assignments: dict[str, str] = {}

    for task in workflow.get(
        "task_definitions",
        [],
    ):
        if task.get("type") != "Assignment":
            continue

        for value_pair in task.get(
            "value_pairs",
            [],
        ):
            name = value_pair.get("name")
            value = value_pair.get("value")

            if not name or not value:
                continue

            assignments[name] = value

    return assignments


def resolve_mapping_runtime_variable(
    raw_name: str,
    session: dict[str, Any],
) -> str | None:
    """
    Resolve a PowerCenter mapping runtime
    variable through the session bindings.
    """

    bindings = build_session_variable_bindings(
        session
    )

    return bindings.get(
        raw_name
    )


def resolve_runtime_variable(
    raw_name: str,
    session: dict[str, Any],
    workflow: dict[str, Any],
) -> ResolvedRuntimeVariable:
    """
    Resolve a PowerCenter mapping runtime variable
    and classify its runtime origin.

    Resolution types:

        computed
        external
        unresolved
    """

    session_value = resolve_mapping_runtime_variable(
        raw_name=raw_name,
        session=session,
    )

    if session_value is None:
        return ResolvedRuntimeVariable(
            source_name=raw_name,
            resolved_value=None,
            resolution_type="unresolved",
        )

    workflow_assignments = (
        build_workflow_variable_assignments(
            workflow
        )
    )

    computed_value = workflow_assignments.get(
        session_value
    )

    if computed_value is not None:
        return ResolvedRuntimeVariable(
            source_name=raw_name,
            resolved_value=computed_value,
            resolution_type="computed",
        )

    return ResolvedRuntimeVariable(
        source_name=raw_name,
        resolved_value=session_value,
        resolution_type="external",
    )


def resolve_mapping_runtime_variables(
    mapping: dict[str, Any],
    session: dict[str, Any],
    workflow: dict[str, Any],
) -> list[ResolvedRuntimeVariable]:
    """
    Discover all runtime variables referenced by
    a mapping and resolve their runtime origin.

    The mapping expressions are scanned
    automatically, then every discovered variable
    is resolved through the session and workflow.
    """

    runtime_parameters = (
        extract_mapping_runtime_parameters(
            mapping
        )
    )

    resolved_variables = []

    for parameter in runtime_parameters:
        resolved_variables.append(
            resolve_runtime_variable(
                raw_name=parameter.raw_name,
                session=session,
                workflow=workflow,
            )
        )

    return resolved_variables