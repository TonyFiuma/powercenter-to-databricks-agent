from src.parser.data_flow import (
    find_source_instances,
    find_target_instances,
    topological_sort,
)

from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)

from src.parser.workflow_parser import (
    parse_workflows,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)


parsed = parse_powercenter_xml(
    XML_PATH
)


mapping_index = {
    mapping["name"]: mapping
    for mapping in parsed.get(
        "mappings",
        [],
    )
    if mapping.get(
        "name"
    )
}


workflow = parse_workflows(
    __import__(
        "xml.etree.ElementTree",
        fromlist=["ElementTree"],
    )
    .parse(
        XML_PATH
    )
    .getroot()
    .find("REPOSITORY")
    .find("FOLDER")
)[0]


print(
    "\nWORKFLOW SESSION -> MAPPING -> TARGET:\n"
)


for session in workflow.get(
    "sessions",
    [],
):
    session_name = session.get(
        "name"
    )

    mapping_name = session.get(
        "mapping_name"
    )

    print(
        "=" * 80
    )

    print(
        "SESSION:",
        session_name,
    )

    print(
        "MAPPING:",
        mapping_name,
    )


    mapping = mapping_index.get(
        mapping_name
    )


    if mapping is None:
        print(
            "ERROR: mapping not found"
        )

        continue


    source_instances = (
        find_source_instances(
            mapping
        )
    )

    target_instances = (
        find_target_instances(
            mapping
        )
    )

    ordered_nodes = (
        topological_sort(
            mapping
        )
    )


    print(
        "SOURCE INSTANCES:",
        source_instances,
    )

    print(
        "TARGET INSTANCES:",
        target_instances,
    )

    print(
        "TOPOLOGICAL ORDER:"
    )

    for node_name in ordered_nodes:
        print(
            "   ",
            node_name,
        )


    print(
        "TRANSFORMATIONS:"
    )

    for transformation in mapping.get(
        "transformations",
        [],
    ):
        print(
            "   ",
            transformation.get(
                "name"
            ),
            "|",
            transformation.get(
                "type"
            ),
        )


    print(
        "INSTANCES:"
    )

    for instance in mapping.get(
        "instances",
        [],
    ):
        print(
            "   ",
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
    "\nWORKFLOW MAPPING TARGET INSPECTION COMPLETED"
)