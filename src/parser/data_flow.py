"""
Utilities for reconstructing PowerCenter mapping data flows.
"""

from collections import defaultdict
from typing import Any


def build_instance_index(
    mapping: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """
    Build an index of PowerCenter instances by instance name.

    Args:
        mapping:
            Parsed PowerCenter mapping or mapplet.

    Returns:
        dict:
            Dictionary keyed by instance name.
    """

    return {
        instance["name"]: instance
        for instance in mapping.get(
            "instances",
            [],
        )
        if instance.get("name")
    }


def build_data_flow(
    mapping: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Build the instance-level data flow from PowerCenter connectors.

    Multiple field-level connectors between the same pair of
    instances are grouped inside one connection.

    Example:

        EXPTRANS1 -> AGGTRANS1

        fields:
            ABI -> ABI
            GRUPPO_ANAG -> GRUPPO_ANAG

    Args:
        mapping:
            Parsed PowerCenter mapping or mapplet.

    Returns:
        list:
            Connections between PowerCenter instances,
            including transformation metadata and
            field-level mappings.
    """

    instances_by_name = build_instance_index(
        mapping
    )

    grouped_connections = {}

    for connector in mapping.get(
        "connectors",
        [],
    ):
        from_instance_name = connector.get(
            "from_instance"
        )

        to_instance_name = connector.get(
            "to_instance"
        )

        if (
            not from_instance_name
            or not to_instance_name
        ):
            continue

        connection_key = (
            from_instance_name,
            to_instance_name,
        )

        if connection_key not in grouped_connections:
            from_instance = instances_by_name.get(
                from_instance_name
            )

            to_instance = instances_by_name.get(
                to_instance_name
            )

            grouped_connections[
                connection_key
            ] = {
                "from": {
                    "name": from_instance_name,

                    "type": (
                        from_instance.get("type")
                        if from_instance
                        else None
                    ),

                    "transformation_name": (
                        from_instance.get(
                            "transformation_name"
                        )
                        if from_instance
                        else None
                    ),

                    "transformation_type": (
                        from_instance.get(
                            "transformation_type"
                        )
                        if from_instance
                        else None
                    ),
                },

                "to": {
                    "name": to_instance_name,

                    "type": (
                        to_instance.get("type")
                        if to_instance
                        else None
                    ),

                    "transformation_name": (
                        to_instance.get(
                            "transformation_name"
                        )
                        if to_instance
                        else None
                    ),

                    "transformation_type": (
                        to_instance.get(
                            "transformation_type"
                        )
                        if to_instance
                        else None
                    ),
                },

                "fields": [],
            }

        field_connection = {
            "from_field": connector.get(
                "from_field"
            ),
            "to_field": connector.get(
                "to_field"
            ),
        }

        if (
            field_connection
            not in grouped_connections[
                connection_key
            ]["fields"]
        ):
            grouped_connections[
                connection_key
            ]["fields"].append(
                field_connection
            )

    return list(
        grouped_connections.values()
    )


def build_adjacency_list(
    mapping: dict[str, Any],
) -> dict[str, list[str]]:
    """
    Build an adjacency list representing the PowerCenter graph.

    Example:

        {
            "EXPTRANS1": [
                "AGGTRANS1",
                "JNRTRANS1",
            ],
            "AGGTRANS1": [
                "JNRTRANS",
            ],
        }

    This representation is useful for detecting branches
    and traversing the mapping in execution order.
    """

    adjacency = defaultdict(list)

    for connection in build_data_flow(
        mapping
    ):
        from_name = connection[
            "from"
        ]["name"]

        to_name = connection[
            "to"
        ]["name"]

        if to_name not in adjacency[
            from_name
        ]:
            adjacency[
                from_name
            ].append(
                to_name
            )

        # Ensure destination nodes also exist
        # in the adjacency dictionary.
        adjacency.setdefault(
            to_name,
            [],
        )

    return dict(adjacency)


def find_source_instances(
    mapping: dict[str, Any],
) -> list[str]:
    """
    Find graph nodes that have outgoing connections
    but no incoming connections.

    These are entry points of the mapping or mapplet.
    """

    data_flow = build_data_flow(
        mapping
    )

    from_instances = {
        connection["from"]["name"]
        for connection in data_flow
    }

    to_instances = {
        connection["to"]["name"]
        for connection in data_flow
    }

    return sorted(
        from_instances - to_instances
    )


def find_target_instances(
    mapping: dict[str, Any],
) -> list[str]:
    """
    Find graph nodes that have incoming connections
    but no outgoing connections.

    These are exit points of the mapping or mapplet.
    """

    data_flow = build_data_flow(
        mapping
    )

    from_instances = {
        connection["from"]["name"]
        for connection in data_flow
    }

    to_instances = {
        connection["to"]["name"]
        for connection in data_flow
    }

    return sorted(
        to_instances - from_instances
    )

def topological_sort(
    mapping: dict[str, Any],
) -> list[str]:
    """
    Return PowerCenter instances in dependency order.

    Nodes are ordered so that every upstream dependency
    appears before the transformations that consume it.

    Raises:
        ValueError:
            If the graph contains a cycle.
    """

    adjacency = build_adjacency_list(
        mapping
    )

    indegree = {
        node: 0
        for node in adjacency
    }

    for from_node, to_nodes in adjacency.items():
        indegree.setdefault(
            from_node,
            0,
        )

        for to_node in to_nodes:
            indegree.setdefault(
                to_node,
                0,
            )

            indegree[to_node] += 1

    queue = sorted(
        node
        for node, degree in indegree.items()
        if degree == 0
    )

    ordered_nodes = []

    while queue:
        current_node = queue.pop(0)

        ordered_nodes.append(
            current_node
        )

        for next_node in adjacency.get(
            current_node,
            [],
        ):
            indegree[next_node] -= 1

            if indegree[next_node] == 0:
                queue.append(
                    next_node
                )

                queue.sort()

    if len(ordered_nodes) != len(indegree):
        raise ValueError(
            "Cycle detected in PowerCenter data flow."
        )

    return ordered_nodes

def build_transformation_index(
    mapping: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """
    Build an index of transformation definitions by name.

    This allows graph nodes to be resolved quickly
    to their PowerCenter transformation metadata.
    """

    return {
        transformation["name"]: transformation
        for transformation in mapping.get(
            "transformations",
            [],
        )
        if transformation.get("name")
    }

def find_predecessors(
    mapping: dict[str, Any],
    node_name: str,
) -> list[str]:
    """
    Return the upstream instances connected
    directly to the requested node.
    """

    predecessors = []

    for connection in build_data_flow(
        mapping
    ):
        if (
            connection["to"]["name"]
            == node_name
        ):
            from_name = (
                connection["from"]["name"]
            )

            if from_name not in predecessors:
                predecessors.append(
                    from_name
                )

    return predecessors