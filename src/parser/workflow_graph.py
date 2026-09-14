from collections import defaultdict
from typing import Any


def build_workflow_adjacency(
    workflow: dict[str, Any],
) -> dict[str, list[str]]:
    """
    Build an adjacency list from
    PowerCenter workflow links.
    """

    adjacency = defaultdict(list)

    for task in workflow.get(
        "tasks",
        [],
    ):
        task_name = task.get(
            "name"
        )

        if task_name:
            adjacency.setdefault(
                task_name,
                [],
            )

    for link in workflow.get(
        "links",
        [],
    ):
        from_task = link.get(
            "from_task"
        )

        to_task = link.get(
            "to_task"
        )

        if (
            not from_task
            or not to_task
        ):
            continue

        if to_task not in adjacency[
            from_task
        ]:
            adjacency[
                from_task
            ].append(
                to_task
            )

        adjacency.setdefault(
            to_task,
            [],
        )

    return dict(
        adjacency
    )


def find_workflow_predecessors(
    workflow: dict[str, Any],
    task_name: str,
) -> list[str]:
    """
    Find all direct predecessors
    of a workflow task.
    """

    predecessors = []

    for link in workflow.get(
        "links",
        [],
    ):
        if (
            link.get(
                "to_task"
            )
            == task_name
        ):
            from_task = (
                link.get(
                    "from_task"
                )
            )

            if (
                from_task
                and from_task
                not in predecessors
            ):
                predecessors.append(
                    from_task
                )

    return predecessors


def find_workflow_start_tasks(
    workflow: dict[str, Any],
) -> list[str]:
    """
    Find workflow nodes that have
    no incoming dependencies.
    """

    task_names = {
        task.get(
            "name"
        )
        for task in workflow.get(
            "tasks",
            [],
        )
        if task.get(
            "name"
        )
    }

    target_tasks = {
        link.get(
            "to_task"
        )
        for link in workflow.get(
            "links",
            [],
        )
        if link.get(
            "to_task"
        )
    }

    return sorted(
        task_names
        - target_tasks
    )


def find_workflow_end_tasks(
    workflow: dict[str, Any],
) -> list[str]:
    """
    Find workflow nodes that have
    no outgoing dependencies.
    """

    task_names = {
        task.get(
            "name"
        )
        for task in workflow.get(
            "tasks",
            [],
        )
        if task.get(
            "name"
        )
    }

    source_tasks = {
        link.get(
            "from_task"
        )
        for link in workflow.get(
            "links",
            [],
        )
        if link.get(
            "from_task"
        )
    }

    return sorted(
        task_names
        - source_tasks
    )


def topological_sort_workflow(
    workflow: dict[str, Any],
) -> list[str]:
    """
    Return workflow tasks in
    dependency execution order.
    """

    adjacency = (
        build_workflow_adjacency(
            workflow
        )
    )

    indegree = {
        task_name: 0
        for task_name
        in adjacency
    }

    for (
        from_task,
        to_tasks,
    ) in adjacency.items():
        indegree.setdefault(
            from_task,
            0,
        )

        for to_task in to_tasks:
            indegree.setdefault(
                to_task,
                0,
            )

            indegree[
                to_task
            ] += 1

    queue = sorted(
        task_name
        for (
            task_name,
            degree,
        ) in indegree.items()
        if degree == 0
    )

    ordered_tasks = []

    while queue:
        current_task = (
            queue.pop(0)
        )

        ordered_tasks.append(
            current_task
        )

        for next_task in adjacency.get(
            current_task,
            [],
        ):
            indegree[
                next_task
            ] -= 1

            if (
                indegree[
                    next_task
                ]
                == 0
            ):
                queue.append(
                    next_task
                )

                queue.sort()

    if (
        len(
            ordered_tasks
        )
        != len(
            indegree
        )
    ):
        raise ValueError(
            "Cycle detected in "
            "PowerCenter workflow."
        )

    return ordered_tasks


def build_session_mapping_index(
    workflow: dict[str, Any],
) -> dict[str, str]:
    """
    Build:
        session_name -> mapping_name
    """

    return {
        session["name"]: session[
            "mapping_name"
        ]
        for session
        in workflow.get(
            "sessions",
            [],
        )
        if (
            session.get(
                "name"
            )
            and session.get(
                "mapping_name"
            )
        )
    }


def build_workflow_execution_plan(
    workflow: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Build a normalized workflow
    execution plan.

    Each entry contains:
    - task name
    - task type
    - predecessors
    - mapping name, if Session
    """

    ordered_tasks = (
        topological_sort_workflow(
            workflow
        )
    )

    task_index = {
        task["name"]: task
        for task
        in workflow.get(
            "tasks",
            [],
        )
        if task.get(
            "name"
        )
    }

    session_mapping_index = (
        build_session_mapping_index(
            workflow
        )
    )

    execution_plan = []

    for task_name in ordered_tasks:
        task = task_index.get(
            task_name,
            {},
        )

        task_type = (
            task.get(
                "task_type"
            )
        )

        execution_plan.append(
            {
                "task_name": task_name,
                "task_type": task_type,
                "is_enabled": task.get(
                    "is_enabled"
                ),
                "predecessors": (
                    find_workflow_predecessors(
                        workflow,
                        task_name,
                    )
                ),
                "mapping_name": (
                    session_mapping_index.get(
                        task_name
                    )
                ),
            }
        )

    return execution_plan