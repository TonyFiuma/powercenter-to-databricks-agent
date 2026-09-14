from typing import Any

from src.parser.data_flow import (
    find_predecessors,
    topological_sort,
)

from src.transpiler.context import (
    TranspilationContext,
)

from src.transpiler.execution_node_index import (
    build_execution_node_index,
)

from src.transpiler.transformations.default_registry import (
    build_default_translator_registry,
)

from src.transpiler.transformations.registry import (
    TransformationTranslatorRegistry,
)


def transpile_data_flow_to_sql(
    mapping: dict[str, Any],
    target_node: str,
    translator_registry: (
        TransformationTranslatorRegistry
        | None
    ) = None,
    mapplets: (
        list[dict[str, Any]]
        | None
    ) = None,
    initial_sql_by_node: (
        dict[str, str]
        | None
    ) = None,
) -> str:
    """
    Transpile a PowerCenter data-flow graph
    into SQL up to the requested target node.

    The execution node index may contain:

    - regular transformations;
    - SOURCE instances;
    - MAPPLET instances;
    - TARGET instances.

    Parameters
    ----------
    mapping:
        Current PowerCenter mapping or mapplet.

    target_node:
        Node whose generated SQL must be
        returned.

    translator_registry:
        Optional custom translator registry.

        If omitted, the default registry is
        created automatically.

    mapplets:
        Available PowerCenter mapplet
        definitions.

    initial_sql_by_node:
        Optional SQL already bound to specific
        graph nodes.

        This is primarily used when parent SQL
        is injected into internal Mapplet Input
        Transformations.
    """

    context = TranspilationContext(
        mapping=mapping,
        mapplets=mapplets or [],
    )

    if translator_registry is None:
        translator_registry = (
            build_default_translator_registry(
                mapplets=context.mapplets,
            )
        )

    node_index = (
        build_execution_node_index(
            context.mapping
        )
    )

    ordered_nodes = (
        topological_sort(
            context.mapping
        )
    )

    sql_by_node: dict[str, str] = dict(
        initial_sql_by_node or {}
    )

    for node_name in ordered_nodes:
        # A node can already have SQL supplied
        # externally.
        #
        # This is used by Mapplets to bind
        # parent SQL to internal Input
        # Transformations.
        if node_name in sql_by_node:
            if node_name == target_node:
                return sql_by_node[
                    node_name
                ]

            continue

        node = node_index.get(
            node_name
        )

        if node is None:
            continue

        node_type = node.get(
            "type"
        )

        if not node_type:
            raise ValueError(
                "Execution node "
                f"'{node_name}' "
                "does not contain a type."
            )

        is_target_node = (
            node_name == target_node
        )

        is_supported = (
            translator_registry.supports(
                node_type
            )
        )

        if (
            is_target_node
            and not is_supported
        ):
            raise NotImplementedError(
                "Execution node type "
                f"'{node_type}' "
                "is not supported."
            )

        if not is_supported:
            continue

        predecessors = (
            find_predecessors(
                context.mapping,
                node_name,
            )
        )

        translator = (
            translator_registry.require(
                node_type
            )
        )

        sql_by_node[node_name] = (
            translator.translate(
                mapping=context.mapping,
                transformation=node,
                node_name=node_name,
                predecessors=predecessors,
                sql_by_node=sql_by_node,
            )
        )

        if is_target_node:
            return sql_by_node[
                node_name
            ]

    raise ValueError(
        "Target node "
        f"'{target_node}' "
        "was not found or was not transpiled."
    )


def transpile_linear_path_to_sql(
    mapping: dict[str, Any],
    target_node: str,
    mapplets: (
        list[dict[str, Any]]
        | None
    ) = None,
    initial_sql_by_node: (
        dict[str, str]
        | None
    ) = None,
) -> str:
    """
    Backward-compatible facade for the
    graph-driven transpiler.
    """

    return transpile_data_flow_to_sql(
        mapping=mapping,
        target_node=target_node,
        mapplets=mapplets,
        initial_sql_by_node=(
            initial_sql_by_node
        ),
    )