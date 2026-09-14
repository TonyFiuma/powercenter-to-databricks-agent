import xml.etree.ElementTree as ET

from src.parser.workflow_parser import (
    parse_workflows,
)


def test_session_variable_bindings():
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

    pre_session_component = next(
        component
        for component in session["components"]
        if component["type"]
        == "Pre-session variable assignment"
    )

    bindings = {
        value_pair["name"]: value_pair["value"]
        for value_pair
        in pre_session_component["value_pairs"]
    }

    print(bindings)

    assert bindings["$$m_ABI"] == "$$ABI"

    assert (
        bindings["$$m_DT_LOAD"]
        == "$$wf_DT_LOAD"
    )

    assert (
        bindings["$$m_DT_RIFERIMENTO"]
        == "$$DT_RIFERIMENTO"
    )