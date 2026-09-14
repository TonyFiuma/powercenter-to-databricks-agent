from typing import Any

from src.parser.workflow_graph import (
    build_workflow_execution_plan,
)


def normalize_task_key(
    task_name: str,
) -> str:
    """
    Normalize a PowerCenter task name
    into a Databricks-compatible task key.
    """

    return (
        task_name
        .replace(" ", "_")
        .replace("-", "_")
    )


def build_task_definition_index(
    workflow: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """
    Build:
        task_name -> task definition
    """

    return {
        task["name"]: task
        for task
        in workflow.get(
            "task_definitions",
            [],
        )
        if task.get(
            "name"
        )
    }


def find_assigned_variables(
    workflow: dict[str, Any],
) -> set[str]:
    """
    Find workflow variables that are
    explicitly assigned by Assignment tasks.

    Example:

        $$wf_DT_LOAD = SYSDATE

    means $$wf_DT_LOAD is an internal
    workflow variable rather than an
    external workflow parameter.
    """

    assigned_variables = set()

    for task in workflow.get(
        "task_definitions",
        [],
    ):
        if task.get(
            "type"
        ) != "Assignment":
            continue

        for value_pair in task.get(
            "value_pairs",
            [],
        ):
            variable_name = (
                value_pair.get(
                    "name"
                )
            )

            if variable_name:
                assigned_variables.add(
                    variable_name
                )

    return assigned_variables


def translate_assignment_value(
    value: str | None,
) -> dict[str, Any]:
    """
    Translate a PowerCenter Assignment value
    into an intermediate representation.

    Known deterministic values are translated
    directly.

    Example:

        SYSDATE

    becomes:

        {
            "type": "current_timestamp"
        }
    """

    if value is None:
        return {
            "type": "literal",
            "value": None,
        }

    normalized_value = (
        value.strip().upper()
    )

    if normalized_value == "SYSDATE":
        return {
            "type": "current_timestamp",
        }

    return {
        "type": "expression",
        "value": value,
        "migration_status": "HUMAN_REVIEW",
    }


def build_assignment_task(
    task_name: str,
    predecessors: list[str],
    task_definition: dict[str, Any],
) -> dict[str, Any]:
    """
    Build the intermediate representation
    of a PowerCenter Assignment task.
    """

    assignments = []

    value_pairs = sorted(
        task_definition.get(
            "value_pairs",
            [],
        ),
        key=lambda value_pair: int(
            value_pair.get(
                "execution_order"
            )
            or 0
        ),
    )

    for value_pair in value_pairs:
        assignments.append(
            {
                "variable": value_pair.get(
                    "name"
                ),
                "value": (
                    translate_assignment_value(
                        value_pair.get(
                            "value"
                        )
                    )
                ),
                "execution_order": (
                    value_pair.get(
                        "execution_order"
                    )
                ),
            }
        )

    return {
        "task_key": normalize_task_key(
            task_name
        ),
        "source_task_name": task_name,
        "source_task_type": "Assignment",
        "target_task_type": "assignment",
        "depends_on": [
            normalize_task_key(
                predecessor
            )
            for predecessor
            in predecessors
        ],
        "assignments": assignments,
        "migration_status": "SUPPORTED",
    }


def build_session_task(
    task_name: str,
    predecessors: list[str],
    mapping_name: str | None,
) -> dict[str, Any]:
    """
    Build the intermediate representation
    of a PowerCenter Session task.

    The associated PowerCenter mapping will
    later be connected to the mapping
    transpiler output.
    """

    depends_on = [
        normalize_task_key(
            predecessor
        )
        for predecessor
        in predecessors
    ]

    if not mapping_name:
        return {
            "task_key": normalize_task_key(
                task_name
            ),
            "source_task_name": task_name,
            "source_task_type": "Session",
            "target_task_type": "mapping_task",
            "depends_on": depends_on,
            "mapping_name": None,
            "migration_status": "UNRESOLVED",
            "migration_issue": (
                "Session does not reference "
                "a PowerCenter mapping."
            ),
        }

    return {
        "task_key": normalize_task_key(
            task_name
        ),
        "source_task_name": task_name,
        "source_task_type": "Session",
        "target_task_type": "mapping_task",
        "depends_on": depends_on,
        "mapping_name": mapping_name,
        "migration_status": "SUPPORTED",
    }


def build_start_task(
    task_name: str,
) -> dict[str, Any]:
    """
    Preserve the PowerCenter Start node
    in the intermediate model.

    It is not necessarily an executable
    Databricks task in the final job.
    """

    return {
        "task_key": normalize_task_key(
            task_name
        ),
        "source_task_name": task_name,
        "source_task_type": "Start",
        "target_task_type": "start",
        "depends_on": [],
        "migration_status": "SUPPORTED",
    }


def build_unsupported_task(
    task_name: str,
    task_type: str | None,
    predecessors: list[str],
) -> dict[str, Any]:
    """
    Preserve unsupported workflow tasks
    instead of silently dropping them.
    """

    return {
        "task_key": normalize_task_key(
            task_name
        ),
        "source_task_name": task_name,
        "source_task_type": task_type,
        "target_task_type": None,
        "depends_on": [
            normalize_task_key(
                predecessor
            )
            for predecessor
            in predecessors
        ],
        "migration_status": "HUMAN_REVIEW",
        "migration_issue": (
            "Unsupported PowerCenter "
            f"workflow task type: {task_type}"
        ),
    }


def build_workflow_variables(
    workflow: dict[str, Any],
    assigned_variables: set[str],
) -> list[dict[str, Any]]:
    """
    Build internal workflow variables.

    Variables assigned inside the workflow
    are kept separate from external
    parameters.
    """

    internal_variables = []

    for variable in workflow.get(
        "variables",
        [],
    ):
        variable_name = (
            variable.get(
                "name"
            )
        )

        if (
            variable.get(
                "user_defined"
            )
            == "YES"
            and variable_name
            in assigned_variables
        ):
            internal_variables.append(
                {
                    "name": variable_name,
                    "datatype": variable.get(
                        "datatype"
                    ),
                    "default_value": (
                        variable.get(
                            "default_value"
                        )
                    ),
                }
            )

    return internal_variables


def build_external_parameters(
    workflow: dict[str, Any],
    assigned_variables: set[str],
) -> list[dict[str, Any]]:
    """
    Build external workflow parameters.

    User-defined variables that are not
    assigned internally are treated as
    external inputs to the workflow.
    """

    parameters = []

    for variable in workflow.get(
        "variables",
        [],
    ):
        variable_name = (
            variable.get(
                "name"
            )
        )

        if (
            variable.get(
                "user_defined"
            )
            == "YES"
            and variable_name
            and variable_name
            not in assigned_variables
        ):
            parameters.append(
                {
                    "name": variable_name,
                    "datatype": variable.get(
                        "datatype"
                    ),
                    "default_value": (
                        variable.get(
                            "default_value"
                        )
                    ),
                }
            )

    return parameters


def transpile_workflow_to_job_model(
    workflow: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert a parsed PowerCenter workflow
    into a Databricks-oriented intermediate
    job model.

    This does not generate the final
    Databricks Jobs API payload yet.
    """

    execution_plan = (
        build_workflow_execution_plan(
            workflow
        )
    )

    task_definitions = (
        build_task_definition_index(
            workflow
        )
    )

    assigned_variables = (
        find_assigned_variables(
            workflow
        )
    )

    target_tasks = []

    for step in execution_plan:
        task_name = step.get(
            "task_name"
        )

        task_type = step.get(
            "task_type"
        )

        predecessors = step.get(
            "predecessors",
            [],
        )

        if task_type == "Start":
            target_task = (
                build_start_task(
                    task_name
                )
            )

        elif task_type == "Assignment":
            task_definition = (
                task_definitions.get(
                    task_name,
                    {},
                )
            )

            target_task = (
                build_assignment_task(
                    task_name=task_name,
                    predecessors=predecessors,
                    task_definition=task_definition,
                )
            )

        elif task_type == "Session":
            target_task = (
                build_session_task(
                    task_name=task_name,
                    predecessors=predecessors,
                    mapping_name=step.get(
                        "mapping_name"
                    ),
                )
            )

        else:
            target_task = (
                build_unsupported_task(
                    task_name=task_name,
                    task_type=task_type,
                    predecessors=predecessors,
                )
            )

        target_tasks.append(
            target_task
        )

    return {
        "job_name": workflow.get(
            "name"
        ),
        "source_type": (
            "Informatica PowerCenter"
        ),
        "parameters": (
            build_external_parameters(
                workflow,
                assigned_variables,
            )
        ),
        "workflow_variables": (
            build_workflow_variables(
                workflow,
                assigned_variables,
            )
        ),
        "tasks": target_tasks,
    }