import xml.etree.ElementTree as ET


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)


MAPPLET_NAME = (
    "mpl_MASTER_CONTROLLI_ABI_GRUPPO"
)


tree = ET.parse(
    XML_PATH
)

root = tree.getroot()


repository = root.find(
    "REPOSITORY"
)

if repository is None:
    raise ValueError(
        "REPOSITORY not found."
    )


folder = repository.find(
    "FOLDER"
)

if folder is None:
    raise ValueError(
        "FOLDER not found."
    )


mapplet = next(
    current_mapplet
    for current_mapplet
    in folder.findall(
        "MAPPLET"
    )
    if current_mapplet.get(
        "NAME"
    )
    == MAPPLET_NAME
)


print(
    "\nMAPPLET INTERFACE RAW XML INSPECTION\n"
)


# ============================================================
# MAPLET INTERFACE TRANSFORMATION
# ============================================================


interface = next(
    transformation
    for transformation
    in mapplet.findall(
        "TRANSFORMATION"
    )
    if transformation.get(
        "TYPE"
    )
    == "Mapplet"
)


print(
    "PUBLIC INTERFACE TRANSFORMATION:\n"
)


print(
    "NAME:",
    interface.get(
        "NAME"
    ),
)


for field in interface.findall(
    "TRANSFORMFIELD"
):
    print(
        "\nFIELD:"
    )

    for (
        attribute_name,
        attribute_value,
    ) in field.attrib.items():
        print(
            "   ",
            attribute_name,
            "=",
            attribute_value,
        )


# ============================================================
# INTERNAL OUTPUT TRANSFORMATION
# ============================================================


output_transformation = next(
    transformation
    for transformation
    in mapplet.findall(
        "TRANSFORMATION"
    )
    if transformation.get(
        "TYPE"
    )
    == "Output Transformation"
)


print(
    "\n\nINTERNAL OUTPUT TRANSFORMATION:\n"
)


print(
    "NAME:",
    output_transformation.get(
        "NAME"
    ),
)


for field in output_transformation.findall(
    "TRANSFORMFIELD"
):
    print(
        "\nFIELD:"
    )

    for (
        attribute_name,
        attribute_value,
    ) in field.attrib.items():
        print(
            "   ",
            attribute_name,
            "=",
            attribute_value,
        )


# ============================================================
# INSTANCE METADATA
# ============================================================


print(
    "\n\nMAPPLET INSTANCES:\n"
)


for instance in mapplet.findall(
    "INSTANCE"
):
    print(
        "\nINSTANCE:",
        instance.get(
            "NAME"
        ),
    )

    for (
        attribute_name,
        attribute_value,
    ) in instance.attrib.items():
        print(
            "   ",
            attribute_name,
            "=",
            attribute_value,
        )


# ============================================================
# RAW CONNECTORS AROUND OUTPUT
# ============================================================


print(
    "\n\nRAW CONNECTORS INTO OUTPUT:\n"
)


for connector in mapplet.findall(
    "CONNECTOR"
):
    if (
        connector.get(
            "TOINSTANCE"
        )
        == "OUTPUT"
    ):
        for (
            attribute_name,
            attribute_value,
        ) in connector.attrib.items():
            print(
                "   ",
                attribute_name,
                "=",
                attribute_value,
            )

        print(
            "-" * 60
        )


print(
    "\nMAPPLET INTERFACE RAW XML INSPECTION COMPLETED"
)