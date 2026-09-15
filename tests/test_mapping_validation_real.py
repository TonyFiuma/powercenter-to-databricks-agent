from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)
from src.transpiler.mapping_validation import (
    validate_powercenter_mapping,
)


def test_real_mapping_semantic_validation():
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

    result = validate_powercenter_mapping(
        mapping
    )

    print(
        "\n--- MAPPING VALIDATION ---\n"
    )
    print(result)

    assert result.status == "VALID"
    assert result.issues == []