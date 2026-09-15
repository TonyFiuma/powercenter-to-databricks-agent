from src.agent.nodes.parse_mapping import (
    parse_mapping_node,
)


def test_parse_mapping_node_real():
    state = {
        "xml_path": (
            "data/input/"
            "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
        ),
        "mapping_name": (
            "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
        ),
    }

    result = parse_mapping_node(
        state
    )

    print(
        "\n--- EXECUTION CONTEXT ---\n"
    )

    print(
        "Mapping:",
        result["mapping"]["name"],
    )

    print(
        "Workflow:",
        result["workflow"]["name"],
    )

    print(
        "Session:",
        result["session"]["name"],
    )

    print(
        "Session mapping:",
        result["session"]["mapping_name"],
    )

    print(
        "Mapplets:",
        [
            mapplet["name"]
            for mapplet
            in result["mapplets"]
        ],
    )

    assert (
        result["mapping"]["name"]
        == "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
    )

    assert (
        result["workflow"]["name"]
        == "wf_CONTROLLI_ANDAMENTALE_INTERNO"
    )

    assert (
        result["session"]["mapping_name"]
        == result["mapping"]["name"]
    )

    assert (
        result["powercenter_project"]
        is not None
    )

    assert len(
        result["powercenter_project"]["mappings"]
    ) == 7

    assert len(
        result["mapplets"]
    ) == 1