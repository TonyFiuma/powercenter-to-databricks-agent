from parser.powercenter_parser import parse_powercenter_xml


def test_mapping_structure():
    file_path = "data/input/wf_m_DHUBTOMIS_MBDT_CSV.XML"

    result = parse_powercenter_xml(file_path)

    mappings = result["mappings"]

    assert len(mappings) > 0

    mapping = mappings[0]

    assert "transformations" in mapping
    assert "instances" in mapping
    assert "connectors" in mapping

def test_data_flow_exists():
    file_path = "data/input/wf_m_DHUBTOMIS_MBDT_CSV.XML"

    result = parse_powercenter_xml(file_path)

    mappings = result["mappings"]

    assert len(mappings) > 0

    mapping = mappings[0]

    assert "data_flow" in mapping
    assert len(mapping["data_flow"]) > 0

def test_data_flow_contains_instance_types():
    file_path = "data/input/wf_m_DHUBTOMIS_MBDT_CSV.XML"

    result = parse_powercenter_xml(file_path)

    mapping = result["mappings"][0]
    data_flow = mapping["data_flow"]

    assert len(data_flow) > 0

    connection = data_flow[0]

    assert "name" in connection["from"]
    assert "type" in connection["from"]

    assert "name" in connection["to"]
    assert "type" in connection["to"]