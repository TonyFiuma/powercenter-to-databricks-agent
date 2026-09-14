import xml.etree.ElementTree as ET


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)


def print_element(
    element,
    level: int = 0,
) -> None:
    """
    Recursively print an XML element,
    its attributes and its children.
    """

    indentation = (
        "    " * level
    )

    print(
        f"{indentation}{element.tag}"
    )

    if element.attrib:
        for (
            attribute_name,
            attribute_value,
        ) in element.attrib.items():
            print(
                f"{indentation}    "
                f"{attribute_name} = "
                f"{attribute_value}"
            )

    if (
        element.text
        and element.text.strip()
    ):
        print(
            f"{indentation}    "
            f"TEXT = "
            f"{element.text.strip()}"
        )

    for child in element:
        print_element(
            child,
            level + 1,
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


workflow = folder.find(
    "WORKFLOW"
)

if workflow is None:
    raise ValueError(
        "WORKFLOW not found."
    )


print(
    "\nASSIGNMENT TASK INSPECTION:\n"
)


assignment_task = None


for task in workflow.findall(
    "TASK"
):
    if (
        task.get("NAME")
        == "Assignment"
    ):
        assignment_task = task
        break


if assignment_task is None:
    raise ValueError(
        "Assignment TASK not found."
    )


print_element(
    assignment_task
)


print(
    "\nRELATED TASK INSTANCE:\n"
)


for task_instance in workflow.findall(
    "TASKINSTANCE"
):
    if (
        task_instance.get("NAME")
        == "Assignment"
    ):
        print_element(
            task_instance
        )


print(
    "\nUSER DEFINED WORKFLOW VARIABLES:\n"
)


for variable in workflow.findall(
    "WORKFLOWVARIABLE"
):
    if (
        variable.get(
            "USERDEFINED"
        )
        == "YES"
    ):
        print_element(
            variable
        )

        print(
            "-" * 60
        )