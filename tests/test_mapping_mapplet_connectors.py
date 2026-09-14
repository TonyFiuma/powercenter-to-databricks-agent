from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)


MAPPING_NAME = (
    "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
)


MAPPLET_INSTANCE_NAME = (
    "mpl_MASTER_CONTROLLI_ABI_GRUPPO"
)


parsed = parse_powercenter_xml(
    XML_PATH
)


mapping = next(
    current_mapping
    for current_mapping
    in parsed.get(
        "mappings",
        [],
    )
    if current_mapping.get(
        "name"
    )
    == MAPPING_NAME
)


print(
    "\nMAPPLET CONNECTOR INSPECTION:\n"
)


print(
    "MAPPING:",
    mapping.get(
        "name"
    ),
)


print(
    "\nCONNECTORS INTO MAPPLET:\n"
)


input_connectors = []


for connector in mapping.get(
    "connectors",
    [],
):
    if (
        connector.get(
            "to_instance"
        )
        == MAPPLET_INSTANCE_NAME
    ):
        input_connectors.append(
            connector
        )

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
    "\nCONNECTORS OUT OF MAPPLET:\n"
)


output_connectors = []


for connector in mapping.get(
    "connectors",
    [],
):
    if (
        connector.get(
            "from_instance"
        )
        == MAPPLET_INSTANCE_NAME
    ):
        output_connectors.append(
            connector
        )

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
    "\nMAPPLET DEFINITION:\n"
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
    == MAPPLET_INSTANCE_NAME
)


print(
    "NAME:",
    mapplet.get(
        "name"
    ),
)


print(
    "\nINPUT TRANSFORMATIONS:\n"
)


for transformation in mapplet.get(
    "transformations",
    [],
):
    if (
        transformation.get(
            "type"
        )
        == "Input Transformation"
    ):
        print(
            transformation.get(
                "name"
            )
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
            )


print(
    "\nOUTPUT TRANSFORMATIONS:\n"
)


for transformation in mapplet.get(
    "transformations",
    [],
):
    if (
        transformation.get(
            "type"
        )
        == "Output Transformation"
    ):
        print(
            transformation.get(
                "name"
            )
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
            )


assert input_connectors

assert output_connectors


print(
    "\nMAPPLET CONNECTOR TEST PASSED"
)