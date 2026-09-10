def build_single_mapping_input(
    full_mapping: dict,
    pc_mapping: dict,
) -> dict:
    """
    Create a reduced PowerCenter structure containing
    only one mapping while preserving the global source
    and target definitions required by the context resolver.

    This helper is shared by planner and generator nodes.
    """

    return {
        "repository": full_mapping.get("repository"),
        "folder": full_mapping.get("folder"),
        "sources": full_mapping.get("sources", []),
        "targets": full_mapping.get("targets", []),
        "mappings": [pc_mapping],
    }


def build_instance_lookup(pc_mapping: dict) -> dict:
    """
    Build a lookup that maps PowerCenter instance names
    to their instance metadata.
    """

    return {
        instance["name"]: instance
        for instance in pc_mapping.get("instances", [])
        if instance.get("name")
    }


def resolve_definition_name(
    node: dict,
    instance_lookup: dict,
) -> str | None:
    """
    Resolve a data-flow instance name to the underlying
    PowerCenter definition name.
    """

    node_name = node.get("name")

    if not node_name:
        return None

    instance = instance_lookup.get(node_name)

    if not instance:
        return node_name

    return (
        instance.get("transformation_name")
        or node_name
    )


def collect_mapping_endpoints(
    data_flow: list,
    instance_lookup: dict,
) -> tuple[dict, dict]:
    """
    Collect source and target instances used by a mapping.

    Returns dictionaries in the following form:

    {
        definition_name: instance_name
    }
    """

    sources = {}
    targets = {}

    for connection in data_flow:
        for node in (
            connection.get("from", {}),
            connection.get("to", {}),
        ):
            node_type = node.get("type")
            instance_name = node.get("name")

            if not instance_name:
                continue

            definition_name = resolve_definition_name(
                node,
                instance_lookup,
            )

            if not definition_name:
                continue

            if node_type == "SOURCE":
                sources[definition_name] = instance_name

            elif node_type == "TARGET":
                targets[definition_name] = instance_name

    return sources, targets


def build_mapping_context(mapping: dict) -> str:
    """
    Build a compact migration-relevant context from the parsed
    PowerCenter structure.

    The context explicitly distinguishes:

    - instance name: object used inside the PowerCenter mapping
    - definition name: underlying Source/Target Definition
    """

    lines = []

    repository = mapping.get("repository")
    folder = mapping.get("folder")

    if repository:
        lines.append(
            f"Repository: {repository}"
        )

    if folder:
        lines.append(
            f"Folder: {folder}"
        )

    sources_by_name = {
        source.get("name"): source
        for source in mapping.get("sources", [])
        if source.get("name")
    }

    targets_by_name = {
        target.get("name"): target
        for target in mapping.get("targets", [])
        if target.get("name")
    }

    for pc_mapping in mapping.get(
        "mappings",
        [],
    ):
        mapping_name = pc_mapping.get(
            "name"
        )

        lines.append("")
        lines.append("=" * 60)
        lines.append(
            f"Mapping: {mapping_name}"
        )
        lines.append("=" * 60)

        data_flow = pc_mapping.get(
            "data_flow",
            [],
        )

        instance_lookup = (
            build_instance_lookup(
                pc_mapping
            )
        )

        (
            source_endpoints,
            target_endpoints,
        ) = collect_mapping_endpoints(
            data_flow,
            instance_lookup,
        )

        if source_endpoints:
            lines.append("")
            lines.append("SOURCES:")

            for definition_name in sorted(
                source_endpoints
            ):
                instance_name = (
                    source_endpoints[
                        definition_name
                    ]
                )

                source = sources_by_name.get(
                    definition_name
                )

                lines.append(
                    f"- instance: "
                    f"{instance_name}"
                )

                lines.append(
                    f"  definition: "
                    f"{definition_name}"
                )

                if source:
                    database_type = (
                        source.get(
                            "database_type"
                        )
                    )

                    database_name = (
                        source.get(
                            "database_name"
                        )
                    )

                    if database_type:
                        lines.append(
                            "  database_type: "
                            f"{database_type}"
                        )

                    if database_name:
                        lines.append(
                            "  database_name: "
                            f"{database_name}"
                        )

        transformations = (
            pc_mapping.get(
                "transformations",
                [],
            )
        )

        if transformations:
            lines.append("")
            lines.append(
                "TRANSFORMATIONS:"
            )

            for transformation in transformations:
                name = transformation.get(
                    "name"
                )

                transformation_type = (
                    transformation.get(
                        "type"
                    )
                )

                lines.append("")

                lines.append(
                    f"- {name}"
                    f" | type: "
                    f"{transformation_type}"
                )

                fields = transformation.get(
                    "fields",
                    [],
                )

                for field in fields:
                    expression = field.get(
                        "expression"
                    )

                    port_type = field.get(
                        "port_type"
                    )

                    if (
                        not expression
                        and not port_type
                    ):
                        continue

                    field_name = field.get(
                        "name"
                    )

                    datatype = field.get(
                        "datatype"
                    )

                    field_line = (
                        f"  - {field_name}"
                    )

                    if datatype:
                        field_line += (
                            " | datatype: "
                            f"{datatype}"
                        )

                    if port_type:
                        field_line += (
                            " | port_type: "
                            f"{port_type}"
                        )

                    lines.append(
                        field_line
                    )

                    if (
                        expression
                        and field_name
                        and expression.strip()
                        != field_name.strip()
                    ):
                        lines.append(
                            "    expression: "
                            f"{expression}"
                        )

        if target_endpoints:
            lines.append("")
            lines.append("TARGETS:")

            for definition_name in sorted(
                target_endpoints
            ):
                instance_name = (
                    target_endpoints[
                        definition_name
                    ]
                )

                target = targets_by_name.get(
                    definition_name
                )

                lines.append(
                    f"- instance: "
                    f"{instance_name}"
                )

                lines.append(
                    f"  definition: "
                    f"{definition_name}"
                )

                if target:
                    database_type = (
                        target.get(
                            "database_type"
                        )
                    )

                    if database_type:
                        lines.append(
                            "  database_type: "
                            f"{database_type}"
                        )

        if data_flow:
            lines.append("")
            lines.append("DATA FLOW:")

            for connection in data_flow:
                from_node = connection.get(
                    "from",
                    {},
                )

                to_node = connection.get(
                    "to",
                    {},
                )

                from_name = from_node.get(
                    "name"
                )

                from_type = from_node.get(
                    "type"
                )

                to_name = to_node.get(
                    "name"
                )

                to_type = to_node.get(
                    "type"
                )

                if from_name and to_name:
                    lines.append(
                        f"- {from_name}"
                        f" [{from_type}]"
                        " -> "
                        f"{to_name}"
                        f" [{to_type}]"
                    )

    return "\n".join(lines)