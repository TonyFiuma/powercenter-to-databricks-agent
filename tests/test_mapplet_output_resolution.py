from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)


MAPPLET_NAME = (
    "mpl_MASTER_CONTROLLI_ABI_GRUPPO"
)


parsed = parse_powercenter_xml(
    XML_PATH
)


mapplet = next(
    current_mapplet
    for current_mapplet
    in parsed.get(
        "mapplets",
        [],
    )
    if current_mapplet.get(
        "name"
    )
    == MAPPLET_NAME
)


print(
    "\nMAPPLET OUTPUT RESOLUTION INSPECTION\n"
)


print(
    "MAPPLET:",
    mapplet.get(
        "name"
    ),
)


print(
    "\nTRANSFORMATIONS:\n"
)


for transformation in mapplet.get(
    "transformations",
    [],
):
    print(
        transformation.get(
            "name"
        ),
        "|",
        transformation.get(
            "type"
        ),
    )

    for field in transformation.get(
        "fields",
        [],
    ):
        print(
            "   ",
            field.get(
                "name"
            ),
            "| port:",
            field.get(
                "port_type"
            ),
            "| expression:",
            field.get(
                "expression"
            ),
        )


print(
    "\nINSTANCES:\n"
)


for instance in mapplet.get(
    "instances",
    [],
):
    print(
        instance.get(
            "name"
        ),
        "| type:",
        instance.get(
            "type"
        ),
        "| transformation:",
        instance.get(
            "transformation_name"
        ),
        "| transformation_type:",
        instance.get(
            "transformation_type"
        ),
    )


print(
    "\nCONNECTORS INTO OUTPUT:\n"
)


for connector in mapplet.get(
    "connectors",
    [],
):
    if (
        connector.get(
            "to_instance"
        )
        == "OUTPUT"
    ):
        print(
            connector.get(
                "from_instance"
            ),
            ".",
            connector.get(
                "from_field"
            ),
            " -> OUTPUT.",
            connector.get(
                "to_field"
            ),
            sep="",
        )


print(
    "\nALL CONNECTORS CONTAINING ABI:\n"
)


for connector in mapplet.get(
    "connectors",
    [],
):
    values = [
        connector.get(
            "from_instance"
        ),
        connector.get(
            "from_field"
        ),
        connector.get(
            "to_instance"
        ),
        connector.get(
            "to_field"
        ),
    ]

    if any(
        value
        and "ABI" in value.upper()
        for value in values
    ):
        print(
            connector.get(
                "from_instance"
            ),
            ".",
            connector.get(
                "from_field"
            ),
            " -> ",
            connector.get(
                "to_instance"
            ),
            ".",
            connector.get(
                "to_field"
            ),
            sep="",
        )


print(
    "\nOUTPUT TRANSFORMATION FIELDS:\n"
)


output_transformation = next(
    transformation
    for transformation
    in mapplet.get(
        "transformations",
        [],
    )
    if transformation.get(
        "type"
    )
    == "Output Transformation"
)


for field in output_transformation.get(
    "fields",
    [],
):
    print(
        {
            "name": field.get(
                "name"
            ),
            "datatype": field.get(
                "datatype"
            ),
            "port_type": field.get(
                "port_type"
            ),
            "expression": field.get(
                "expression"
            ),
            "expression_type": field.get(
                "expression_type"
            ),
        }
    )


print(
    "\nMAPPLET OUTPUT RESOLUTION INSPECTION COMPLETED"
)