import xml.etree.ElementTree as ET

from src.parser.workflow_parser import (
    parse_workflows,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
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


workflows = parse_workflows(
    folder
)


print(
    "\nPARSED WORKFLOWS:\n"
)


for workflow in workflows:
    print(
        "WORKFLOW:",
        workflow.get(
            "name"
        ),
    )

    print(
        "\nTASKS:"
    )

    for task in workflow.get(
        "tasks",
        [],
    ):
        print(
            task.get("name"),
            "|",
            task.get("task_type"),
            "| enabled:",
            task.get("is_enabled"),
        )

    print(
        "\nLINKS:"
    )

    for link in workflow.get(
        "links",
        [],
    ):
        print(
            link.get("from_task"),
            "->",
            link.get("to_task"),
            "| condition:",
            link.get("condition"),
        )

    print(
        "\nSESSIONS:"
    )

    for session in workflow.get(
        "sessions",
        [],
    ):
        print(
            session.get("name"),
            "->",
            session.get(
                "mapping_name"
            ),
        )

    print(
        "\nUSER DEFINED VARIABLES:"
    )

    for variable in workflow.get(
        "variables",
        [],
    ):
        if (
            variable.get(
                "user_defined"
            )
            == "YES"
        ):
            print(
                variable.get("name"),
                "|",
                variable.get(
                    "datatype"
                ),
                "| default:",
                variable.get(
                    "default_value"
                ),
            )


# ============================================================
# BASIC REGRESSION ASSERTS
# ============================================================


assert len(workflows) == 1


workflow = workflows[0]


assert (
    workflow["name"]
    == "wf_CONTROLLI_ANDAMENTALE_INTERNO"
)


assert len(
    workflow["tasks"]
) == 9


assert len(
    workflow["sessions"]
) == 7


assert len(
    workflow["links"]
) == 8


session_mapping_names = {
    session["mapping_name"]
    for session
    in workflow["sessions"]
}


assert (
    "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
    in session_mapping_names
)


user_variables = {
    variable["name"]
    for variable
    in workflow["variables"]
    if variable["user_defined"]
    == "YES"
}


assert "$$ABI" in user_variables

assert (
    "$$DT_RIFERIMENTO"
    in user_variables
)

assert (
    "$$wf_DT_LOAD"
    in user_variables
)


print(
    "\nWORKFLOW PARSER TEST PASSED"
)