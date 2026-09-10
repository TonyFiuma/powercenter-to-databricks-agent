from parser.data_flow import build_data_flow

def parse_transform_fields(transformation) -> list:
    """
    Extract fields from a PowerCenter transformation.

    Args:
        transformation: XML element representing a PowerCenter transformation.

    Returns:
        list: List of fields found in the transformation,
        including field metadata and expressions.
    """

    fields = []

    for field in transformation.findall("TRANSFORMFIELD"):
        field_data = {
            "name": field.get("NAME"),
            "datatype": field.get("DATATYPE"),
            "precision": field.get("PRECISION"),
            "scale": field.get("SCALE"),
            "port_type": field.get("PORTTYPE"),
            "expression": field.get("EXPRESSION")
        }

        fields.append(field_data)

    return fields


def parse_transformations(mapping) -> list:
    """
    Extract transformations from a PowerCenter mapping.
    """

    transformations = []

    for transformation in mapping.findall("TRANSFORMATION"):
        transformation_data = {
            "name": transformation.get("NAME"),
            "type": transformation.get("TYPE"),
            "fields": parse_transform_fields(transformation)
        }

        transformations.append(transformation_data)

    return transformations


def parse_connectors(mapping) -> list:
    """
    Extract connectors from a PowerCenter mapping.
    """

    connectors = []

    for connector in mapping.findall("CONNECTOR"):
        connector_data = {
            "from_instance": connector.get("FROMINSTANCE"),
            "from_field": connector.get("FROMFIELD"),
            "to_instance": connector.get("TOINSTANCE"),
            "to_field": connector.get("TOFIELD")
        }

        connectors.append(connector_data)

    return connectors


def parse_instances(mapping) -> list:
    """
    Extract instances from a PowerCenter mapping.
    """

    instances = []

    for instance in mapping.findall("INSTANCE"):
        instance_data = {
            "name": instance.get("NAME"),
            "transformation_name": instance.get("TRANSFORMATION_NAME"),
            "transformation_type": instance.get("TRANSFORMATION_TYPE"),
            "type": instance.get("TYPE")
        }

        instances.append(instance_data)

    return instances


def parse_mappings(folder) -> list:
    """
    Extract mappings from a PowerCenter folder.
    """

    mappings = []

    for mapping in folder.findall("MAPPING"):
        mapping_data = {
            "name": mapping.get("NAME"),
            "description": mapping.get("DESCRIPTION"),
            "transformations": parse_transformations(mapping),
            "instances": parse_instances(mapping),
            "connectors": parse_connectors(mapping)
        }

        mapping_data["data_flow"] = build_data_flow(mapping_data)

        mappings.append(mapping_data)

    return mappings