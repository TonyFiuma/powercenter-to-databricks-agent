"""
Utilities for reconstructing PowerCenter mapping data flows.
"""

def build_data_flow(mapping: dict) -> list:
    """
    Build a simplified data flow from PowerCenter connectors.

    Args:
        mapping (dict): Parsed PowerCenter mapping.

    Returns:
        list: Unique connections between mapping instances,
        enriched with instance type information.
    """

    data_flow = []

    instances_by_name = {
        instance["name"]: instance
        for instance in mapping["instances"]
    }

    for connector in mapping["connectors"]:
        from_instance_name = connector["from_instance"]
        to_instance_name = connector["to_instance"]

        from_instance = instances_by_name.get(from_instance_name)
        to_instance = instances_by_name.get(to_instance_name)

        connection = {
            "from": {
                "name": from_instance_name,
                "type": from_instance.get("type") if from_instance else None,
                "transformation_type": (
                    from_instance.get("transformation_type")
                    if from_instance
                    else None
                )
            },
            "to": {
                "name": to_instance_name,
                "type": to_instance.get("type") if to_instance else None,
                "transformation_type": (
                    to_instance.get("transformation_type")
                    if to_instance
                    else None
                )
            }
        }

        if connection not in data_flow:
            data_flow.append(connection)

    return data_flow