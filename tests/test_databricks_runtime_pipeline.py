import xml.etree.ElementTree as ET

from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)
from src.parser.workflow_parser import (
    parse_workflows,
)
from src.transpiler.databricks_runtime_variable import (
    build_databricks_runtime_variables,
)


def test_databricks_runtime_pipeline():
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

    runtime_variables = (
        build_databricks_runtime_variables(
            mapping=mapping,
            session=session,
            workflow=workflow,
        )
    )

    print("Databricks runtime variables:")

    for variable in runtime_variables:
        print(variable)

    runtime_by_source = {
        variable.source_name: variable
        for variable in runtime_variables
    }

    dt_riferimento = runtime_by_source[
        "$$m_DT_RIFERIMENTO"
    ]

    dt_load = runtime_by_source[
        "$$m_DT_LOAD"
    ]

    assert (
        dt_riferimento.value
        == "DT_RIFERIMENTO"
    )
    assert (
        dt_riferimento.variable_type
        == "parameter"
    )

    assert (
        dt_load.value
        == "current_timestamp()"
    )
    assert (
        dt_load.variable_type
        == "expression"
    )