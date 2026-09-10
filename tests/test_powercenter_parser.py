from parser.powercenter_parser import parse_powercenter_xml


def test_parse_powercenter_xml():
    file_path = "data/input/wf_m_DHUBTOMIS_MBDT_CSV.XML"

    result = parse_powercenter_xml(file_path)

    assert result["repository"] == "PWCRS_MIS_SVIL"
    assert result["folder"] == "MIS_SRB_W1"

    assert len(result["sources"]) > 0
    assert len(result["targets"]) > 0
    assert len(result["mappings"]) > 0