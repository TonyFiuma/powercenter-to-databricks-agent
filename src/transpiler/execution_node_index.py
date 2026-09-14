from typing import Any

from src.parser.data_flow import (
    build_transformation_index,
)


def build_execution_node_index(
    mapping: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """
    Build an index containing every node that can
    appear in a PowerCenter mapping data-flow graph.

    PowerCenter stores regular transformations in
    mapping["transformations"], while other graph
    nodes such as SOURCE, MAPPLET and TARGET are
    represented as instances.

    Regular transformations take precedence over
    instances having the same name.
    """

    node_index = dict(
        build_transformation_index(
            mapping
        )
    )

    for instance in mapping.get(
        "instances",
        [],
    ):
        instance_name = instance.get(
            "name"
        )

        if not instance_name:
            continue

        if instance_name in node_index:
            continue

        node_index[
            instance_name
        ] = instance

    return node_index