def build_generator_context(
    single_mapping: dict,
) -> str:
    """
    Build a compact mapping context for PySpark generation.

    The migration planner already contains the semantic
    interpretation of the mapping. The generator therefore
    receives only the structural information required to
    implement the PySpark code.

    The function intentionally avoids:
    - verbose metadata;
    - duplicated connector information;
    - parsed data_flow dumps;
    - precision/scale unless contained in expressions;
    - repeated transformation details.
    """

    mappings = single_mapping.get(
        "mappings",
        [],
    )

    if not mappings:
        return ""

    pc_mapping = mappings[0]

    lines = []

    # ==================================================
    # Mapping
    # ==================================================

    mapping_name = pc_mapping.get(
        "name",
        "UNKNOWN_MAPPING",
    )

    lines.append(
        f"MAPPING: {mapping_name}"
    )

    # ==================================================
    # Sources
    # ==================================================

    sources = single_mapping.get(
        "sources",
        [],
    )

    if sources:
        lines.append("")
        lines.append("SOURCES:")

    for source in sources:
        source_name = source.get(
            "name",
            "UNKNOWN_SOURCE",
        )

        lines.append(
            f"- {source_name}"
        )

        fields = source.get(
            "fields",
            [],
        )

        field_names = [
            field.get("name")
            for field in fields
            if field.get("name")
        ]

        if field_names:
            lines.append(
                "  fields: "
                + ", ".join(field_names)
            )

    # ==================================================
    # Transformations
    # ==================================================

    transformations = pc_mapping.get(
        "transformations",
        [],
    )

    if transformations:
        lines.append("")
        lines.append(
            "TRANSFORMATIONS:"
        )

    for transformation in transformations:
        transformation_name = (
            transformation.get(
                "name",
                "UNKNOWN_TRANSFORMATION",
            )
        )

        transformation_type = (
            transformation.get(
                "type",
                "UNKNOWN_TYPE",
            )
        )

        lines.append(
            f"- {transformation_name} "
            f"[{transformation_type}]"
        )

        fields = transformation.get(
            "fields",
            [],
        )

        for field in fields:
            field_name = field.get(
                "name"
            )

            expression = field.get(
                "expression"
            )

            port_type = field.get(
                "port_type"
            )

            # Only keep fields containing actual
            # transformation logic.
            if expression:
                field_line = (
                    f"  {field_name}"
                )

                if port_type:
                    field_line += (
                        f" [{port_type}]"
                    )

                field_line += (
                    f" = {expression}"
                )

                lines.append(
                    field_line
                )

    # ==================================================
    # Targets
    # ==================================================

    targets = single_mapping.get(
        "targets",
        [],
    )

    if targets:
        lines.append("")
        lines.append("TARGETS:")

    for target in targets:
        target_name = target.get(
            "name",
            "UNKNOWN_TARGET",
        )

        target_type = (
            target.get("database_type")
            or target.get("type")
        )

        if target_type:
            lines.append(
                f"- {target_name} "
                f"[{target_type}]"
            )
        else:
            lines.append(
                f"- {target_name}"
            )

        fields = target.get(
            "fields",
            [],
        )

        field_names = [
            field.get("name")
            for field in fields
            if field.get("name")
        ]

        if field_names:
            lines.append(
                "  fields: "
                + ", ".join(field_names)
            )

    # ==================================================
    # Data flow
    # ==================================================
    #
    # PowerCenter XML usually contains one connector
    # for every field. Sending all of them to the LLM
    # creates a very large amount of duplicated text.
    #
    # For generation we only keep unique INSTANCE-level
    # edges:
    #
    # SOURCE -> SQ -> EXP -> TARGET
    #
    # instead of:
    #
    # SOURCE.COL1 -> SQ.COL1
    # SOURCE.COL2 -> SQ.COL2
    # SOURCE.COL3 -> SQ.COL3
    # ...

    connectors = pc_mapping.get(
        "connectors",
        [],
    )

    unique_edges = set()

    for connector in connectors:
        from_instance = (
            connector.get("from_instance")
            or connector.get(
                "from_instance_name"
            )
            or connector.get(
                "frominstance"
            )
        )

        to_instance = (
            connector.get("to_instance")
            or connector.get(
                "to_instance_name"
            )
            or connector.get(
                "toinstance"
            )
        )

        if (
            from_instance
            and to_instance
        ):
            unique_edges.add(
                (
                    from_instance,
                    to_instance,
                )
            )

    if unique_edges:
        lines.append("")
        lines.append("DATA FLOW:")

        for (
            from_instance,
            to_instance,
        ) in sorted(unique_edges):
            lines.append(
                f"- {from_instance} "
                f"-> {to_instance}"
            )

    return "\n".join(lines)