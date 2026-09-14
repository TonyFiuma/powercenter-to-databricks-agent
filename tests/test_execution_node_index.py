from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)

from src.transpiler.execution_node_index import (
    build_execution_node_index,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)

MAPPING_NAME = (
    "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
)


def main() -> None:
    parsed = parse_powercenter_xml(
        XML_PATH
    )

    mapping = next(
        mapping
        for mapping in parsed["mappings"]
        if mapping["name"] == MAPPING_NAME
    )

    node_index = (
        build_execution_node_index(
            mapping
        )
    )

    expected_nodes = {
        "RSK_DM_ANDINT_CONTICORRENTI_SYN",
        "RSK_WK_ANAGRAFICA_BANCHE_SOCIETA",
        "SQ_RSK_DM_ANDINT_CONTICORRENTI_SYN",
        "SQ_RSK_WK_ANAGRAFICA_BANCHE_SOCIETA",
        "mpl_MASTER_CONTROLLI_ABI_GRUPPO",
        "EXPTRANS1",
        "SVDDMTBP_MASTER_CONTROLLI",
    }

    for node_name in expected_nodes:
        assert node_name in node_index

    assert (
        node_index[
            "SQ_RSK_DM_ANDINT_CONTICORRENTI_SYN"
        ]["type"]
        == "Source Qualifier"
    )

    assert (
        node_index[
            "mpl_MASTER_CONTROLLI_ABI_GRUPPO"
        ]["type"]
        == "MAPPLET"
    )

    assert (
        node_index[
            "SVDDMTBP_MASTER_CONTROLLI"
        ]["type"]
        == "TARGET"
    )

    assert (
        node_index[
            "RSK_DM_ANDINT_CONTICORRENTI_SYN"
        ]["type"]
        == "SOURCE"
    )

    print(
        "EXECUTION NODE INDEX TEST PASSED"
    )


if __name__ == "__main__":
    main()