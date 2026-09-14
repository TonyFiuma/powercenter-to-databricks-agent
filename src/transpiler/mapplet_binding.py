from typing import Any


def build_mapplet_input_sql_bindings(
    *,
    mapplet_contract: dict[str, Any],
    sql_by_node: dict[str, str],
) -> dict[str, str]:
    """
    Build SQL bindings for the internal Input
    Transformations of a mapplet.

    The function combines:

    1. parent mapping -> public mapplet ports;
    2. public mapplet ports -> internal inputs;
    3. SQL already generated for parent nodes.

    Example result:

        {
            "TARGET": "...",
            "ANAGRAFICA_BANCHE": "...",
        }

    The returned dictionary can be passed to
    transpile_data_flow_to_sql through
    initial_sql_by_node.
    """

    input_bindings = (
        mapplet_contract.get(
            "input_bindings",
            [],
        )
    )

    internal_bindings = (
        mapplet_contract.get(
            "internal_bindings",
            [],
        )
    )

    if not input_bindings:
        raise ValueError(
            "Mapplet contract does not contain "
            "input bindings."
        )

    if not internal_bindings:
        raise ValueError(
            "Mapplet contract does not contain "
            "internal bindings."
        )

    internal_by_public_port: dict[
        str,
        dict[str, Any],
    ] = {}

    for binding in internal_bindings:
        port_type = (
            binding.get(
                "port_type"
            )
            or ""
        ).upper()

        if port_type != "INPUT":
            continue

        public_port = binding.get(
            "public_port"
        )

        if not public_port:
            continue

        internal_by_public_port[
            public_port
        ] = binding

    fields_by_internal_node: dict[
        str,
        list[tuple[str, str]],
    ] = {}

    source_by_internal_node: dict[
        str,
        str,
    ] = {}

    for binding in input_bindings:
        source_instance = binding.get(
            "source_instance"
        )

        source_field = binding.get(
            "source_field"
        )

        mapplet_port = binding.get(
            "mapplet_port"
        )

        if not (
            source_instance
            and source_field
            and mapplet_port
        ):
            raise ValueError(
                "Incomplete parent-to-mapplet "
                "input binding."
            )

        if source_instance not in sql_by_node:
            raise ValueError(
                "SQL not generated for mapplet "
                f"predecessor "
                f"'{source_instance}'."
            )

        internal_binding = (
            internal_by_public_port.get(
                mapplet_port
            )
        )

        if internal_binding is None:
            raise ValueError(
                "Internal mapplet binding not "
                f"found for public input "
                f"'{mapplet_port}'."
            )

        internal_node = (
            internal_binding.get(
                "internal_instance"
            )
        )

        internal_field = (
            internal_binding.get(
                "internal_field"
            )
        )

        if not (
            internal_node
            and internal_field
        ):
            raise ValueError(
                "Incomplete internal mapplet "
                f"binding for public input "
                f"'{mapplet_port}'."
            )

        predecessor_sql = (
            sql_by_node[
                source_instance
            ]
        )

        existing_source = (
            source_by_internal_node.get(
                internal_node
            )
        )

        if (
            existing_source is not None
            and existing_source
            != source_instance
        ):
            raise NotImplementedError(
                "Multiple parent SQL nodes "
                "feeding the same internal "
                "mapplet input are not "
                "supported yet."
            )

        source_by_internal_node[
            internal_node
        ] = source_instance

        fields_by_internal_node.setdefault(
            internal_node,
            [],
        ).append(
            (
                source_field,
                internal_field,
            )
        )

    result: dict[str, str] = {}

    for (
        internal_node,
        field_mappings,
    ) in fields_by_internal_node.items():
        source_instance = (
            source_by_internal_node[
                internal_node
            ]
        )

        source_sql = (
            sql_by_node[
                source_instance
            ]
        )

        projections = []

        for (
            source_field,
            internal_field,
        ) in field_mappings:
            projections.append(
                "    "
                f"src.{source_field} "
                f"AS {internal_field}"
            )

        projection_sql = ",\n".join(
            projections
        )

        indented_source_sql = "\n".join(
            "    " + line
            for line
            in source_sql.splitlines()
        )

        result[
            internal_node
        ] = (
            "SELECT\n"
            f"{projection_sql}\n"
            "FROM (\n"
            f"{indented_source_sql}\n"
            ") src"
        )

    return result