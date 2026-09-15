import xml.etree.ElementTree as ET

from src.parser.workflow_parser import (
    parse_workflows,
)
from src.transpiler.runtime_variable_resolver import (
    resolve_runtime_variable,
)


def test_resolved_runtime_variables():
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

    unknown = resolve_runtime_variable(
        raw_name="$$m_UNKNOWN",
        session=session,
        workflow=workflow,
    )

    print("DT_LOAD:", dt_load)
    print("DT_RIFERIMENTO:", dt_riferimento)
    print("UNKNOWN:", unknown)

    assert dt_load.source_name == "$$m_DT_LOAD"
    assert dt_load.resolved_value == "SYSDATE"
    assert dt_load.resolution_type == "computed"

    assert (
        dt_riferimento.source_name
        == "$$m_DT_RIFERIMENTO"
    )
    assert (
        dt_riferimento.resolved_value
        == "$$DT_RIFERIMENTO"
    )
    assert (
        dt_riferimento.resolution_type
        == "external"
    )

    assert unknown.source_name == "$$m_UNKNOWN"
    assert unknown.resolved_value is None
    assert unknown.resolution_type == "unresolved"