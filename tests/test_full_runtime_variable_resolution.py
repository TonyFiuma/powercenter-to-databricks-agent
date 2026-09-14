import xml.etree.ElementTree as ET

from src.parser.workflow_parser import (
    parse_workflows,
)
from src.transpiler.runtime_variable_resolver import (
    build_workflow_variable_assignments,
    resolve_runtime_variable,
)


def test_full_runtime_variable_resolution():
    root = ET.parse(
        "data/input/wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
    ).getroot()

    folder = root.find(".//FOLDER")

    workflows = parse_workflows(
        folder
    )

    workflow = next(
        workflow
        for workflow in workflows
        if workflow["name"]
        == "wf_CONTROLLI_ANDAMENTALE_INTERNO"
    )

    session = next(
        session
        for session in workflow["sessions"]
        if session["name"]
        == "s_m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
    )

    assignments = build_workflow_variable_assignments(
        workflow
    )

    print(
        "Workflow assignments:",
        assignments,
    )

    dt_load = resolve_runtime_variable(
        raw_name="$$m_DT_LOAD",
        session=session,
        workflow=workflow,
    )

    dt_riferimento = resolve_runtime_variable(
        raw_name="$$m_DT_RIFERIMENTO",
        session=session,
        workflow=workflow,
    )

    abi = resolve_runtime_variable(
        raw_name="$$m_ABI",
        session=session,
        workflow=workflow,
    )

    print(
        "$$m_DT_LOAD ->",
        dt_load,
    )

    print(
        "$$m_DT_RIFERIMENTO ->",
        dt_riferimento,
    )

    print(
        "$$m_ABI ->",
        abi,
    )

    assert dt_load == "SYSDATE"

    assert (
        dt_riferimento
        == "$$DT_RIFERIMENTO"
    )

    assert abi == "$$ABI"