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

def test_target_instance_preserves_table_attributes():
    file_path = "data/input/wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"

    result = parse_powercenter_xml(file_path)

    mapping = next(
        mapping
        for mapping in result["mappings"]
        if mapping["name"] == "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
    )

    target_instance = next(
        instance
        for instance in mapping["instances"]
        if instance["type"] == "TARGET"
    )

    table_attributes = target_instance["table_attributes"]

    assert "Pre SQL" in table_attributes
    assert "Post SQL" in table_attributes

    assert "delete from SVDDMTBP_MASTER_CONTROLLI" in table_attributes["Pre SQL"]
    assert "$$m_DT_RIFERIMENTO" in table_attributes["Pre SQL"]

    assert table_attributes["Post SQL"] == ""