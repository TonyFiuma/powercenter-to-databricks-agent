import xml.etree.ElementTree as ET

from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)
from src.parser.workflow_parser import (
    parse_workflows,
)
from src.transpiler.runtime_variable_resolver import (
    resolve_mapping_runtime_variables,
)


def test_mapping_runtime_variable_resolution():
    xml_path = (
        "data/input/"
        "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
    )

    parsed = parse_powercenter_xml(
        xml_path
    )

    mapping = next(
        mapping
        for mapping in parsed["mappings"]
        if mapping["name"]
        == "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
    )

    root = ET.parse(
        xml_path
    ).getroot()

    folder = root.find(
        ".//FOLDER"
    )

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
        if session["mapping_name"]
        == mapping["name"]
    )

    resolved_variables = (
        resolve_mapping_runtime_variables(
            mapping=mapping,
            session=session,
            workflow=workflow,
        )
    )

    print(
        "Resolved variables:"
    )

    for variable in resolved_variables:
        print(variable)

    resolved_by_name = {
        variable.source_name: variable
        for variable in resolved_variables
    }

    dt_load = resolved_by_name[
        "$$m_DT_LOAD"
    ]

    dt_riferimento = resolved_by_name[
        "$$m_DT_RIFERIMENTO"
    ]

    assert (
        dt_load.resolved_value
        == "SYSDATE"
    )
    assert (
        dt_load.resolution_type
        == "computed"
    )

    assert (
        dt_riferimento.resolved_value
        == "$$DT_RIFERIMENTO"
    )
    assert (
        dt_riferimento.resolution_type
        == "external"
    )