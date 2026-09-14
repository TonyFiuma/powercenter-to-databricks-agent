from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
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
    == "mpl_MASTER_CONTROLLI_ABI_GRUPPO"
)


print(
    "\nEXP_CAMPI_CALCOLATI -> OUTPUT:\n"
)


for connection in mapplet.get(
    "data_flow",
    [],
):
    from_name = (
        connection.get(
            "from",
            {},
        ).get(
            "name"
        )
    )

    to_name = (
        connection.get(
            "to",
            {},
        ).get(
            "name"
        )
    )

    if (
        from_name
        != "EXP_CAMPI_CALCOLATI"
        or to_name
        != "OUTPUT"
    ):
        continue

    for field_connection in connection.get(
        "fields",
        [],
    ):
        print(
            field_connection.get(
                "from_field"
            ),
            "->",
            field_connection.get(
                "to_field"
            ),
        )


print(
    "\nOUTPUT FIELDS:\n"
)


output_transformation = next(
    transformation
    for transformation
    in mapplet.get(
        "transformations",
        [],
    )
    if transformation.get(
        "name"
    )
    == "OUTPUT"
)


for field in output_transformation.get(
    "fields",
    [],
):
    print(
        field.get("name"),
        "| port:",
        field.get("port_type"),
        "| expression:",
        field.get("expression"),
    )