def build_single_mapping_input(
    full_mapping: dict,
    pc_mapping: dict,
) -> dict:
    """
    Create a reduced PowerCenter structure containing
    only one mapping.

    Prefer mapping-specific enriched source and target metadata
    when available, because they include runtime/session information
    such as target Flat File overrides.

    Fall back to global Source/Target Definitions when mapping-level
    metadata is not available.
    """

    return {
        "repository": full_mapping.get("repository"),
        "folder": full_mapping.get("folder"),

        "sources": (
            pc_mapping.get("sources")
            or full_mapping.get("sources", [])
        ),

        "targets": (
            pc_mapping.get("targets")
            or full_mapping.get("targets", [])
        ),

        "mappings": [pc_mapping],
    }


def build_instance_lookup(
    pc_mapping: dict,
) -> dict:
    """
    Build a lookup that maps PowerCenter instance names
    to their instance metadata.
    """

    return {
        instance["name"]: instance
        for instance in pc_mapping.get(
            "instances",
            [],
        )
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

    instance = instance_lookup.get(
        node_name
    )

    if not instance:
        return node_name

    return (
        instance.get(
            "transformation_name"
        )
        or node_name
    )


def collect_mapping_endpoints(
    data_flow: list,
    instance_lookup: dict,
) -> tuple[dict, dict]:
    """
    Collect source and target instances used by a mapping.

    Returns:
        tuple[dict, dict]:
            Source and target dictionaries in the form:

            {
                definition_name: instance_name
            }
    """

    sources = {}
    targets = {}

    for connection in data_flow:
        for node in (
            connection.get(
                "from",
                {},
            ),
            connection.get(
                "to",
                {},
            ),
        ):
            node_type = node.get("type")
            instance_name = node.get("name")

            if not instance_name:
                continue

            definition_name = (
                resolve_definition_name(
                    node,
                    instance_lookup,
                )
            )

            if not definition_name:
                continue

            if node_type == "SOURCE":
                sources[
                    definition_name
                ] = instance_name

            elif node_type == "TARGET":
                targets[
                    definition_name
                ] = instance_name

    return sources, targets


def append_flat_file_config(
    lines: list,
    title: str,
    config: dict | None,
) -> None:
    """
    Append Flat File configuration to the mapping context.

    Only properties explicitly parsed from the PowerCenter
    XML are included.
    """

    if not config:
        return

    lines.append(
        f"  {title}:"
    )

    properties = (
        (
            "codepage",
            "codepage",
        ),
        (
            "delimited",
            "delimited",
        ),
        (
            "delimiter",
            "delimiter",
        ),
        (
            "quote_character",
            "quote_character",
        ),
        (
            "null_character",
            "null_character",
        ),
        (
            "row_delimiter",
            "row_delimiter",
        ),
        (
            "skip_rows",
            "skip_rows",
        ),
        (
            "strip_trailing_blanks",
            "strip_trailing_blanks",
        ),
    )

    for key, label in properties:
        value = config.get(key)

        if value is not None:
            lines.append(
                f"    {label}: {value}"
            )


def append_transformation_fields(
    lines: list,
    fields: list,
) -> None:
    """
    Append transformation fields in a compact form.

    Pass-through INPUT/OUTPUT fields are grouped into a
    single line to reduce prompt size.

    Fields with non-trivial expressions are preserved
    individually with their full expression because they
    are migration-relevant.

    Other ports, such as INPUT-only or OUTPUT-only fields,
    are also retained.
    """

    passthrough_fields = []
    other_ports = []
    non_trivial_fields = []

    for field in fields:
        field_name = field.get(
            "name"
        )

        datatype = field.get(
            "datatype"
        )

        port_type = field.get(
            "port_type"
        )

        expression = field.get(
            "expression"
        )

        if not field_name:
            continue

        is_non_trivial_expression = (
            expression
            and expression.strip()
            != field_name.strip()
        )

        if is_non_trivial_expression:
            non_trivial_fields.append(
                {
                    "name": field_name,
                    "datatype": datatype,
                    "port_type": port_type,
                    "expression": expression,
                }
            )

            continue

        if port_type == "INPUT/OUTPUT":
            passthrough_fields.append(
                field_name
            )

        elif port_type:
            other_ports.append(
                {
                    "name": field_name,
                    "datatype": datatype,
                    "port_type": port_type,
                }
            )

    if passthrough_fields:
        lines.append(
            "  pass_through_fields: "
            + ", ".join(
                passthrough_fields
            )
        )

    if other_ports:
        lines.append(
            "  other_ports:"
        )

        for field in other_ports:
            field_line = (
                f"    - {field['name']}"
            )

            if field["datatype"]:
                field_line += (
                    " | datatype: "
                    f"{field['datatype']}"
                )

            if field["port_type"]:
                field_line += (
                    " | port_type: "
                    f"{field['port_type']}"
                )

            lines.append(
                field_line
            )

    for field in non_trivial_fields:
        field_line = (
            f"  - {field['name']}"
        )

        if field["datatype"]:
            field_line += (
                " | datatype: "
                f"{field['datatype']}"
            )

        if field["port_type"]:
            field_line += (
                " | port_type: "
                f"{field['port_type']}"
            )

        lines.append(
            field_line
        )

        lines.append(
            "    expression: "
            f"{field['expression']}"
        )


def build_mapping_context(
    mapping: dict,
) -> str:
    """
    Build a compact migration-relevant context from the parsed
    PowerCenter structure.

    The context explicitly distinguishes:

    - instance name;
    - underlying Source/Target Definition;
    - source database metadata;
    - transformation behavior;
    - target definition configuration;
    - session-level target overrides;
    - effective target runtime configuration;
    - mapping data flow.

    Pass-through transformation fields are grouped to reduce
    prompt size while preserving migration-relevant expressions.
    """

    lines = []

    repository = mapping.get(
        "repository"
    )

    folder = mapping.get(
        "folder"
    )

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
        for source in mapping.get(
            "sources",
            [],
        )
        if source.get("name")
    }

    targets_by_name = {
        target.get("name"): target
        for target in mapping.get(
            "targets",
            [],
        )
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
        lines.append(
            "=" * 60
        )

        lines.append(
            f"Mapping: {mapping_name}"
        )

        lines.append(
            "=" * 60
        )

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
            lines.append(
                "SOURCES:"
            )

            for definition_name in sorted(
                source_endpoints
            ):
                instance_name = (
                    source_endpoints[
                        definition_name
                    ]
                )

                source = (
                    sources_by_name.get(
                        definition_name
                    )
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

                    owner_name = (
                        source.get(
                            "owner_name"
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

                    if owner_name:
                        lines.append(
                            "  owner_name: "
                            f"{owner_name}"
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
                name = (
                    transformation.get(
                        "name"
                    )
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

                fields = (
                    transformation.get(
                        "fields",
                        [],
                    )
                )

                append_transformation_fields(
                    lines=lines,
                    fields=fields,
                )

        if target_endpoints:
            lines.append("")
            lines.append(
                "TARGETS:"
            )

            for definition_name in sorted(
                target_endpoints
            ):
                instance_name = (
                    target_endpoints[
                        definition_name
                    ]
                )

                target = (
                    targets_by_name.get(
                        definition_name
                    )
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

                    append_flat_file_config(
                        lines=lines,
                        title=(
                            "target_definition_flat_file"
                        ),
                        config=target.get(
                            "flat_file"
                        ),
                    )

                    append_flat_file_config(
                        lines=lines,
                        title=(
                            "session_flat_file_override"
                        ),
                        config=target.get(
                            "session_flat_file"
                        ),
                    )

                    append_flat_file_config(
                        lines=lines,
                        title=(
                            "effective_flat_file"
                        ),
                        config=target.get(
                            "effective_flat_file"
                        ),
                    )

        if data_flow:
            lines.append("")
            lines.append(
                "DATA FLOW:"
            )

            for connection in data_flow:
                from_node = (
                    connection.get(
                        "from",
                        {},
                    )
                )

                to_node = (
                    connection.get(
                        "to",
                        {},
                    )
                )

                from_name = (
                    from_node.get(
                        "name"
                    )
                )

                from_type = (
                    from_node.get(
                        "type"
                    )
                )

                to_name = (
                    to_node.get(
                        "name"
                    )
                )

                to_type = (
                    to_node.get(
                        "type"
                    )
                )

                if (
                    from_name
                    and to_name
                ):
                    lines.append(
                        f"- {from_name}"
                        f" [{from_type}]"
                        " -> "
                        f"{to_name}"
                        f" [{to_type}]"
                    )

    return "\n".join(
        lines
    )