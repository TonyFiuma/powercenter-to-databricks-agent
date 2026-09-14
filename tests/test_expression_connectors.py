from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)


# ============================================================
# PARSE XML
# ============================================================


parsed = parse_powercenter_xml(
    XML_PATH
)


# ============================================================
# SELECT MAPPLET
# ============================================================


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


# ============================================================
# JNRTRANS -> EXP_CAMPI_CALCOLATI CONNECTORS
# ============================================================


print(
    "\nJNRTRANS -> EXP_CAMPI_CALCOLATI:\n"
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
        from_name != "JNRTRANS"
        or to_name != "EXP_CAMPI_CALCOLATI"
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


# ============================================================
# EXP_CAMPI_CALCOLATI FIELDS
# ============================================================


print(
    "\nEXP_CAMPI_CALCOLATI FIELDS:\n"
)


expression_transformation = next(
    transformation
    for transformation
    in mapplet.get(
        "transformations",
        [],
    )
    if transformation.get(
        "name"
    )
    == "EXP_CAMPI_CALCOLATI"
)


for field in expression_transformation.get(
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