from typing import Any


def find_mapplet_definition(
    mapplets: list[dict[str, Any]],
    mapplet_name: str,
) -> dict[str, Any]:
    """
    Find a parsed mapplet definition by name.
    """

    for mapplet in mapplets:
        if (
            mapplet.get("name")
            == mapplet_name
        ):
            return mapplet

    raise ValueError(
        f"Mapplet definition not found: "
        f"{mapplet_name}"
    )


def find_mapplet_instance(
    mapping: dict[str, Any],
    mapplet_instance_name: str,
) -> dict[str, Any]:
    """
    Find a mapplet instance inside
    a PowerCenter mapping.
    """

    for instance in mapping.get(
        "instances",
        [],
    ):
        if (
            instance.get("name")
            == mapplet_instance_name
        ):
            if (
                instance.get("type")
                != "MAPPLET"
            ):
                raise ValueError(
                    f"Instance "
                    f"{mapplet_instance_name} "
                    f"is not a MAPPLET."
                )

            return instance

    raise ValueError(
        f"Mapplet instance not found: "
        f"{mapplet_instance_name}"
    )


def find_mapplet_interface_transformation(
    mapplet: dict[str, Any],
) -> dict[str, Any]:
    """
    Find the transformation that defines
    the public interface of the mapplet.
    """

    mapplet_name = mapplet.get(
        "name"
    )

    for transformation in mapplet.get(
        "transformations",
        [],
    ):
        if (
            transformation.get("type")
            == "Mapplet"
        ):
            return transformation

    raise ValueError(
        "Mapplet interface transformation "
        f"not found for: {mapplet_name}"
    )


def get_mapplet_interface_fields(
    mapplet: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Return all public interface fields
    exposed by the mapplet.
    """

    interface = (
        find_mapplet_interface_transformation(
            mapplet
        )
    )

    return interface.get(
        "fields",
        [],
    )


def get_mapplet_input_ports(
    mapplet: dict[str, Any],
) -> set[str]:
    """
    Return public INPUT ports.
    """

    input_ports = set()

    for field in get_mapplet_interface_fields(
        mapplet
    ):
        port_type = (
            field.get(
                "port_type"
            )
            or ""
        )

        field_name = (
            field.get(
                "name"
            )
        )

        if (
            field_name
            and "INPUT"
            in port_type
        ):
            input_ports.add(
                field_name
            )

    return input_ports


def get_mapplet_output_ports(
    mapplet: dict[str, Any],
) -> set[str]:
    """
    Return public OUTPUT ports.
    """

    output_ports = set()

    for field in get_mapplet_interface_fields(
        mapplet
    ):
        port_type = (
            field.get(
                "port_type"
            )
            or ""
        )

        field_name = (
            field.get(
                "name"
            )
        )

        if (
            field_name
            and "OUTPUT"
            in port_type
        ):
            output_ports.add(
                field_name
            )

    return output_ports


def build_mapplet_internal_bindings(
    mapplet: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Resolve every public mapplet port
    to the corresponding internal field.

    PowerCenter stores this relationship
    using:

        MAPPLETGROUP
        REF_FIELD
        REF_INSTANCETYPE

    Example:

        public ABI1
        MAPPLETGROUP = OUTPUT
        REF_FIELD = ABI

    becomes:

        ABI1 -> OUTPUT.ABI
    """

    bindings = []

    for field in get_mapplet_interface_fields(
        mapplet
    ):
        public_port = (
            field.get(
                "name"
            )
        )

        internal_instance = (
            field.get(
                "mapplet_group"
            )
        )

        internal_field = (
            field.get(
                "ref_field"
            )
        )

        internal_instance_type = (
            field.get(
                "ref_instance_type"
            )
        )

        port_type = (
            field.get(
                "port_type"
            )
        )

        if not public_port:
            continue

        bindings.append(
            {
                "public_port": (
                    public_port
                ),
                "port_type": (
                    port_type
                ),
                "internal_instance": (
                    internal_instance
                ),
                "internal_field": (
                    internal_field
                ),
                "internal_instance_type": (
                    internal_instance_type
                ),
            }
        )

    return bindings


def build_mapplet_input_bindings(
    mapping: dict[str, Any],
    mapplet_instance_name: str,
) -> list[dict[str, Any]]:
    """
    Build parent mapping -> mapplet
    public input bindings.
    """

    bindings = []

    for connector in mapping.get(
        "connectors",
        [],
    ):
        if (
            connector.get("to_instance")
            != mapplet_instance_name
        ):
            continue

        bindings.append(
            {
                "source_instance": (
                    connector.get(
                        "from_instance"
                    )
                ),
                "source_field": (
                    connector.get(
                        "from_field"
                    )
                ),
                "mapplet_port": (
                    connector.get(
                        "to_field"
                    )
                ),
            }
        )

    return bindings


def build_mapplet_output_bindings(
    mapping: dict[str, Any],
    mapplet_instance_name: str,
) -> list[dict[str, Any]]:
    """
    Build mapplet public output ->
    parent mapping bindings.
    """

    bindings = []

    for connector in mapping.get(
        "connectors",
        [],
    ):
        if (
            connector.get("from_instance")
            != mapplet_instance_name
        ):
            continue

        bindings.append(
            {
                "mapplet_port": (
                    connector.get(
                        "from_field"
                    )
                ),
                "target_instance": (
                    connector.get(
                        "to_instance"
                    )
                ),
                "target_field": (
                    connector.get(
                        "to_field"
                    )
                ),
            }
        )

    return bindings


def build_public_to_internal_index(
    mapplet: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """
    Build an index:

        public_port
            ->
        internal binding metadata
    """

    return {
        binding[
            "public_port"
        ]: binding
        for binding
        in build_mapplet_internal_bindings(
            mapplet
        )
    }


def validate_mapplet_bindings(
    mapplet: dict[str, Any],
    input_bindings: list[dict[str, Any]],
    output_bindings: list[dict[str, Any]],
) -> list[str]:
    """
    Validate parent connectors against
    the public mapplet interface and
    internal reference metadata.
    """

    issues = []

    input_ports = (
        get_mapplet_input_ports(
            mapplet
        )
    )

    output_ports = (
        get_mapplet_output_ports(
            mapplet
        )
    )

    internal_index = (
        build_public_to_internal_index(
            mapplet
        )
    )

    for binding in input_bindings:
        mapplet_port = (
            binding.get(
                "mapplet_port"
            )
        )

        if (
            mapplet_port
            not in input_ports
        ):
            issues.append(
                (
                    "Unknown public mapplet "
                    f"input port: {mapplet_port}"
                )
            )

    for binding in output_bindings:
        mapplet_port = (
            binding.get(
                "mapplet_port"
            )
        )

        if (
            mapplet_port
            not in output_ports
        ):
            issues.append(
                (
                    "Unknown public mapplet "
                    f"output port: {mapplet_port}"
                )
            )

    for (
        public_port,
        internal_binding,
    ) in internal_index.items():
        if not internal_binding.get(
            "internal_instance"
        ):
            issues.append(
                (
                    "Missing MAPPLETGROUP for "
                    f"public port: {public_port}"
                )
            )

        if not internal_binding.get(
            "internal_field"
        ):
            issues.append(
                (
                    "Missing REF_FIELD for "
                    f"public port: {public_port}"
                )
            )

    return issues


def resolve_mapplet_contract(
    mapping: dict[str, Any],
    mapplets: list[dict[str, Any]],
    mapplet_instance_name: str,
) -> dict[str, Any]:
    """
    Resolve the complete contract between
    a parent mapping and a mapplet.

    Includes:

    - parent -> public input bindings
    - public -> internal bindings
    - public output -> parent bindings
    """

    instance = find_mapplet_instance(
        mapping,
        mapplet_instance_name,
    )

    mapplet_name = (
        instance.get(
            "transformation_name"
        )
        or mapplet_instance_name
    )

    mapplet = find_mapplet_definition(
        mapplets,
        mapplet_name,
    )

    input_bindings = (
        build_mapplet_input_bindings(
            mapping,
            mapplet_instance_name,
        )
    )

    output_bindings = (
        build_mapplet_output_bindings(
            mapping,
            mapplet_instance_name,
        )
    )

    internal_bindings = (
        build_mapplet_internal_bindings(
            mapplet
        )
    )

    validation_issues = (
        validate_mapplet_bindings(
            mapplet,
            input_bindings,
            output_bindings,
        )
    )

    return {
        "instance_name": (
            mapplet_instance_name
        ),
        "mapplet_name": (
            mapplet_name
        ),
        "input_ports": sorted(
            get_mapplet_input_ports(
                mapplet
            )
        ),
        "output_ports": sorted(
            get_mapplet_output_ports(
                mapplet
            )
        ),
        "input_bindings": (
            input_bindings
        ),
        "internal_bindings": (
            internal_bindings
        ),
        "output_bindings": (
            output_bindings
        ),
        "validation_status": (
            "VALID"
            if not validation_issues
            else "INVALID"
        ),
        "validation_issues": (
            validation_issues
        ),
        "mapplet": (
            mapplet
        ),
    }