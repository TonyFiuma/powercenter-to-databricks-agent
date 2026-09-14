import xml.etree.ElementTree as ET

from src.parser.workflow_parser import (
    parse_workflows,
)
from src.transpiler.runtime_variable_resolver import (
    build_session_variable_bindings,
    resolve_mapping_runtime_variable,
)


def test_runtime_variable_resolver():
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

    bindings = build_session_variable_bindings(
        session
    )

    print(bindings)

    assert (
        resolve_mapping_runtime_variable(
            "$$m_DT_RIFERIMENTO",
            session,
        )
        == "$$DT_RIFERIMENTO"
    )

    assert (
        resolve_mapping_runtime_variable(
            "$$m_DT_LOAD",
            session,
        )
        == "$$wf_DT_LOAD"
    )

    assert (
        resolve_mapping_runtime_variable(
            "$$m_ABI",
            session,
        )
        == "$$ABI"
    )