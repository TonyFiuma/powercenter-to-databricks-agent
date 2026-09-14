from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)
from src.transpiler.runtime_parameter import (
    extract_mapping_runtime_parameters,
)


def test_extract_mapping_runtime_parameters():
    parsed = parse_powercenter_xml(
        "data/input/wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
    )

    mapping = next(
        mapping
        for mapping in parsed["mappings"]
        if mapping["name"]
        == "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
    )

    parameters = extract_mapping_runtime_parameters(
        mapping
    )

    print(parameters)

    parameter_names = {
        parameter.name
        for parameter in parameters
    }

    assert "m_DT_RIFERIMENTO" in parameter_names
    assert "m_DT_LOAD" in parameter_names