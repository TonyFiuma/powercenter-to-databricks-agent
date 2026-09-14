from parser.data_flow import build_data_flow


def parse_transform_fields(
    transformation,
) -> list:
    """
    Extract fields from a PowerCenter transformation.

    In addition to the standard field metadata,
    mapplet interface metadata is preserved when
    present.

    Args:
        transformation:
            XML element representing a PowerCenter
            transformation.

    Returns:
        list:
            Transformation fields and their metadata.
    """

    fields = []

    for field in transformation.findall(
        "TRANSFORMFIELD"
    ):
        field_data = {
            "name": field.get(
                "NAME"
            ),

            "datatype": field.get(
                "DATATYPE"
            ),

            "precision": field.get(
                "PRECISION"
            ),

            "scale": field.get(
                "SCALE"
            ),

            "port_type": field.get(
                "PORTTYPE"
            ),

            "expression": field.get(
                "EXPRESSION"
            ),

            "expression_type": field.get(
                "EXPRESSIONTYPE"
            ),

            # Mapplet public-interface metadata.
            #
            # Example:
            #
            # NAME="ABI1"
            # REF_FIELD="ABI"
            # REF_INSTANCETYPE="Output Transformation"
            # MAPPLETGROUP="OUTPUT"
            #
            # means:
            #
            # public port ABI1
            #     ->
            # OUTPUT.ABI
            "ref_field": field.get(
                "REF_FIELD"
            ),

            "ref_instance_type": field.get(
                "REF_INSTANCETYPE"
            ),

            "mapplet_group": field.get(
                "MAPPLETGROUP"
            ),
        }

        fields.append(
            field_data
        )

    return fields


def parse_table_attributes(
    transformation,
) -> dict:
    """
    Extract TABLEATTRIBUTE values from a
    PowerCenter transformation.

    Example:

        <TABLEATTRIBUTE
            NAME="Filter Condition"
            VALUE="TOTAL > 100"
        />

    becomes:

        {
            "Filter Condition": "TOTAL > 100"
        }
    """

    attributes = {}

    for attribute in transformation.findall(
        "TABLEATTRIBUTE"
    ):
        name = attribute.get(
            "NAME"
        )

        value = attribute.get(
            "VALUE"
        )

        if name:
            attributes[
                name
            ] = value

    return attributes


def parse_transformations(
    mapping,
) -> list:
    """
    Extract transformations from a PowerCenter
    mapping or mapplet.
    """

    transformations = []

    for transformation in mapping.findall(
        "TRANSFORMATION"
    ):
        table_attributes = (
            parse_table_attributes(
                transformation
            )
        )

        transformation_data = {
            "name": transformation.get(
                "NAME"
            ),

            "type": transformation.get(
                "TYPE"
            ),

            "fields": parse_transform_fields(
                transformation
            ),

            "table_attributes": (
                table_attributes
            ),
        }

        if (
            transformation.get(
                "TYPE"
            )
            == "Filter"
        ):
            transformation_data[
                "filter_condition"
            ] = table_attributes.get(
                "Filter Condition"
            )

        transformations.append(
            transformation_data
        )

    return transformations


def parse_connectors(
    mapping,
) -> list:
    """
    Extract connectors from a PowerCenter
    mapping or mapplet.
    """

    connectors = []

    for connector in mapping.findall(
        "CONNECTOR"
    ):
        connector_data = {
            "from_instance": connector.get(
                "FROMINSTANCE"
            ),

            "from_field": connector.get(
                "FROMFIELD"
            ),

            "to_instance": connector.get(
                "TOINSTANCE"
            ),

            "to_field": connector.get(
                "TOFIELD"
            ),
        }

        connectors.append(
            connector_data
        )

    return connectors


def parse_instances(
    mapping,
) -> list:
    """
    Extract instances from a PowerCenter
    mapping or mapplet.
    """

    instances = []

    for instance in mapping.findall(
        "INSTANCE"
    ):
        instance_data = {
            "name": instance.get(
                "NAME"
            ),

            "transformation_name": (
                instance.get(
                    "TRANSFORMATION_NAME"
                )
            ),

            "transformation_type": (
                instance.get(
                    "TRANSFORMATION_TYPE"
                )
            ),

            "type": instance.get(
                "TYPE"
            ),
        }

        instances.append(
            instance_data
        )

    return instances


def parse_mappings(
    folder,
) -> list:
    """
    Extract mappings from a PowerCenter folder.
    """

    mappings = []

    for mapping in folder.findall(
        "MAPPING"
    ):
        mapping_data = {
            "name": mapping.get(
                "NAME"
            ),

            "description": mapping.get(
                "DESCRIPTION"
            ),

            "transformations": (
                parse_transformations(
                    mapping
                )
            ),

            "instances": (
                parse_instances(
                    mapping
                )
            ),

            "connectors": (
                parse_connectors(
                    mapping
                )
            ),
        }

        mapping_data[
            "data_flow"
        ] = build_data_flow(
            mapping_data
        )

        mappings.append(
            mapping_data
        )

    return mappings


def parse_mapplets(
    folder,
) -> list:
    """
    Parse reusable PowerCenter mapplets.

    Each mapplet is represented similarly
    to a mapping:

    - name
    - description
    - transformations
    - instances
    - connectors
    - data_flow

    Mapplet public-interface metadata such as
    REF_FIELD, REF_INSTANCETYPE and MAPPLETGROUP
    is preserved inside transformation fields.
    """

    mapplets = []

    for mapplet in folder.findall(
        "MAPPLET"
    ):
        mapplet_data = {
            "name": mapplet.get(
                "NAME"
            ),

            "description": mapplet.get(
                "DESCRIPTION"
            ),

            "transformations": (
                parse_transformations(
                    mapplet
                )
            ),

            "instances": (
                parse_instances(
                    mapplet
                )
            ),

            "connectors": (
                parse_connectors(
                    mapplet
                )
            ),
        }

        mapplet_data[
            "data_flow"
        ] = build_data_flow(
            mapplet_data
        )

        mapplets.append(
            mapplet_data
        )

    return mapplets