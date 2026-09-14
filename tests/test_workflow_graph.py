import xml.etree.ElementTree as ET

from src.parser.workflow_graph import (
    build_workflow_adjacency,
    build_workflow_execution_plan,
    find_workflow_end_tasks,
    find_workflow_start_tasks,
    topological_sort_workflow,
)

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


print(
    "\nWORKFLOW ADJACENCY:\n"
)


adjacency = (
    build_workflow_adjacency(
        workflow
    )
)


for (
    task_name,
    next_tasks,
) in adjacency.items():
    print(
        task_name
    )

    for next_task in next_tasks:
        print(
            "    ->",
            next_task,
        )


print(
    "\nSTART TASKS:"
)

start_tasks = (
    find_workflow_start_tasks(
        workflow
    )
)

print(
    start_tasks
)


print(
    "\nEND TASKS:"
)

end_tasks = (
    find_workflow_end_tasks(
        workflow
    )
)

print(
    end_tasks
)


print(
    "\nTOPOLOGICAL ORDER:\n"
)

ordered_tasks = (
    topological_sort_workflow(
        workflow
    )
)


for task_name in ordered_tasks:
    print(
        task_name
    )


print(
    "\nWORKFLOW EXECUTION PLAN:\n"
)


execution_plan = (
    build_workflow_execution_plan(
        workflow
    )
)


for step in execution_plan:
    print(
        step.get(
            "task_name"
        ),
        "| type:",
        step.get(
            "task_type"
        ),
        "| predecessors:",
        step.get(
            "predecessors"
        ),
        "| mapping:",
        step.get(
            "mapping_name"
        ),
    )


# ============================================================
# ASSERTS
# ============================================================


assert start_tasks == [
    "Start"
]


assert end_tasks == [
    "s_m_CONTROLLI_ANDINT_FONDIESICAV_ID_01"
]


assert ordered_tasks == [
    "Start",
    "Assignment",
    "s_m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01",
    "s_m_CONTROLLI_ANDINT_MOVASSEGNI_ID_01",
    "s_m_CONTROLLI_ANDINT_RATEALI_ID_01",
    "s_m_CONTROLLI_ANDINT_ANTICIPIEFACTORING_ID_01",
    "s_m_CONTROLLI_ANDINT_CREDITIDIFIRMA_ID_01",
    "s_m_CONTROLLI_ANDINT_DEPOSITOTITOLI_ID_01",
    "s_m_CONTROLLI_ANDINT_FONDIESICAV_ID_01",
]


conti_step = next(
    step
    for step
    in execution_plan
    if step.get(
        "task_name"
    )
    == (
        "s_m_CONTROLLI_ANDINT_"
        "CONTICORRENTI_ID_01"
    )
)


assert (
    conti_step[
        "mapping_name"
    ]
    == (
        "m_CONTROLLI_ANDINT_"
        "CONTICORRENTI_ID_01"
    )
)


assert (
    conti_step[
        "predecessors"
    ]
    == [
        "Assignment"
    ]
)


print(
    "\nWORKFLOW GRAPH TEST PASSED"
)