import xml.etree.ElementTree as ET

from src.parser.workflow_parser import (
    parse_workflows,
)

from src.transpiler.workflow_to_databricks import (
    transpile_workflow_to_job_model,
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


workflow = parse_workflows(
    folder
)[0]


job_model = (
    transpile_workflow_to_job_model(
        workflow
    )
)


print(
    "\nDATABRICKS-ORIENTED JOB MODEL:\n"
)


print(
    "JOB:",
    job_model.get(
        "job_name"
    ),
)


print(
    "\nEXTERNAL PARAMETERS:\n"
)


for parameter in job_model.get(
    "parameters",
    [],
):
    print(
        parameter
    )


print(
    "\nINTERNAL WORKFLOW VARIABLES:\n"
)


for variable in job_model.get(
    "workflow_variables",
    [],
):
    print(
        variable
    )


print(
    "\nTASKS:\n"
)


for task in job_model.get(
    "tasks",
    [],
):
    print(
        task
    )


assert (
    job_model[
        "job_name"
    ]
    == "wf_CONTROLLI_ANDAMENTALE_INTERNO"
)


assert len(
    job_model[
        "tasks"
    ]
) == 9


# ============================================================
# ASSIGNMENT
# ============================================================


assignment_task = next(
    task
    for task
    in job_model[
        "tasks"
    ]
    if task[
        "source_task_name"
    ]
    == "Assignment"
)


assert (
    assignment_task[
        "migration_status"
    ]
    == "SUPPORTED"
)


assert (
    assignment_task[
        "assignments"
    ][0][
        "variable"
    ]
    == "$$wf_DT_LOAD"
)


assert (
    assignment_task[
        "assignments"
    ][0][
        "value"
    ][
        "type"
    ]
    == "current_timestamp"
)


# ============================================================
# SESSION -> MAPPING
# ============================================================


conti_task = next(
    task
    for task
    in job_model[
        "tasks"
    ]
    if task[
        "source_task_name"
    ]
    == (
        "s_m_CONTROLLI_ANDINT_"
        "CONTICORRENTI_ID_01"
    )
)


assert (
    conti_task[
        "mapping_name"
    ]
    == (
        "m_CONTROLLI_ANDINT_"
        "CONTICORRENTI_ID_01"
    )
)


assert (
    conti_task[
        "depends_on"
    ]
    == [
        "Assignment"
    ]
)


# ============================================================
# EXTERNAL PARAMETERS
# ============================================================


parameter_names = {
    parameter[
        "name"
    ]
    for parameter
    in job_model[
        "parameters"
    ]
}


assert "$$ABI" in parameter_names


assert (
    "$$DT_RIFERIMENTO"
    in parameter_names
)


assert (
    "$$wf_DT_LOAD"
    not in parameter_names
)


# ============================================================
# INTERNAL WORKFLOW VARIABLES
# ============================================================


workflow_variable_names = {
    variable[
        "name"
    ]
    for variable
    in job_model[
        "workflow_variables"
    ]
}


assert (
    "$$wf_DT_LOAD"
    in workflow_variable_names
)


assert (
    "$$ABI"
    not in workflow_variable_names
)


assert (
    "$$DT_RIFERIMENTO"
    not in workflow_variable_names
)


print(
    "\nWORKFLOW TO DATABRICKS TEST PASSED"
)