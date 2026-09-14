from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)

from src.transpiler.graph_transpiler import (
    transpile_data_flow_to_sql,
)

from src.transpiler.mapplet_binding import (
    build_mapplet_input_sql_bindings,
)

from src.transpiler.mapplet_resolver import (
    resolve_mapplet_contract,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)

MAPPING_NAME = (
    "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
)

MAPPLET_NAME = (
    "mpl_MASTER_CONTROLLI_ABI_GRUPPO"
)


def main() -> None:
    parsed = parse_powercenter_xml(
        XML_PATH
    )

    mapping = next(
        item
        for item in parsed["mappings"]
        if item["name"] == MAPPING_NAME
    )

    contract = resolve_mapplet_contract(
        mapping,
        parsed["mapplets"],
        MAPPLET_NAME,
    )

    sql_first_source = (
        transpile_data_flow_to_sql(
            mapping=mapping,
            mapplets=parsed["mapplets"],
            target_node=(
                "SQ_RSK_DM_ANDINT_"
                "CONTICORRENTI_SYN"
            ),
        )
    )

    sql_second_source = (
        transpile_data_flow_to_sql(
            mapping=mapping,
            mapplets=parsed["mapplets"],
            target_node=(
                "SQ_RSK_WK_ANAGRAFICA_"
                "BANCHE_SOCIETA"
            ),
        )
    )

    sql_by_node = {
        (
            "SQ_RSK_DM_ANDINT_"
            "CONTICORRENTI_SYN"
        ): sql_first_source,
        (
            "SQ_RSK_WK_ANAGRAFICA_"
            "BANCHE_SOCIETA"
        ): sql_second_source,
    }

    bindings = (
        build_mapplet_input_sql_bindings(
            mapplet_contract=contract,
            sql_by_node=sql_by_node,
        )
    )

    assert "TARGET" in bindings

    assert (
        "ANAGRAFICA_BANCHE"
        in bindings
    )

    target_sql = bindings[
        "TARGET"
    ]

    anagrafica_sql = bindings[
        "ANAGRAFICA_BANCHE"
    ]

    assert (
        "src.COD_ABI AS ABI"
        in target_sql
    )

    assert (
        "src.ABI_BANCA AS ABI_ANAG"
        in anagrafica_sql
    )

    assert (
        "src.COD_GRUPPO AS GRUPPO_ANAG"
        in anagrafica_sql
    )

    assert (
        "DWHEVO."
        "RSK_DM_ANDINT_CONTICORRENTI_SYN"
        in target_sql
    )

    assert (
        "DWHEVO."
        "RSK_WK_ANAGRAFICA_BANCHE_SOCIETA"
        in anagrafica_sql
    )

    print(
        "\nTARGET BINDING:\n"
    )

    print(target_sql)

    print(
        "\nANAGRAFICA_BANCHE BINDING:\n"
    )

    print(anagrafica_sql)

    print(
        "\nMAPLET INPUT BINDING "
        "TEST PASSED"
    )


if __name__ == "__main__":
    main()