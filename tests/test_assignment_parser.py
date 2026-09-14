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

workflow = workflows[0]


assignment = next(
    task
    for task
    in workflow.get(
        "task_definitions",
        [],
    )
    if task.get(
        "name"
    )
    == "Assignment"
)


print(
    "\nASSIGNMENT PARSED:\n"
)

print(
    assignment
)


assert (
    assignment[
        "type"
    ]
    == "Assignment"
)


assert len(
    assignment[
        "value_pairs"
    ]
) == 1


value_pair = (
    assignment[
        "value_pairs"
    ][0]
)


assert (
    value_pair[
        "name"
    ]
    == "$$wf_DT_LOAD"
)


assert (
    value_pair[
        "value"
    ]
    == "SYSDATE"
)


assert (
    value_pair[
        "execution_order"
    ]
    == "1"
)


print(
    "\nASSIGNMENT PARSER TEST PASSED"
)