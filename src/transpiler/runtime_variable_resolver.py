from typing import Any


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

    Example:

        $$m_DT_RIFERIMENTO
            ->
        $$DT_RIFERIMENTO
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
) -> str | None:
    """
    Resolve a mapping runtime variable through
    both session bindings and workflow variable
    assignments.

    Examples:

        $$m_DT_LOAD
            ->
        $$wf_DT_LOAD
            ->
        SYSDATE

        $$m_DT_RIFERIMENTO
            ->
        $$DT_RIFERIMENTO

    If the workflow variable is not internally
    assigned, the workflow variable name is
    returned unchanged.
    """

    resolved = resolve_mapping_runtime_variable(
        raw_name=raw_name,
        session=session,
    )

    if resolved is None:
        return None

    workflow_assignments = (
        build_workflow_variable_assignments(
            workflow
        )
    )

    return workflow_assignments.get(
        resolved,
        resolved,
    )