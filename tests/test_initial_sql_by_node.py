from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)

from src.transpiler.graph_transpiler import (
    transpile_data_flow_to_sql,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)

MAPPLET_NAME = (
    "mpl_MASTER_CONTROLLI_ABI_GRUPPO"
)


def main() -> None:
    parsed = parse_powercenter_xml(
        XML_PATH
    )

    mapplet = next(
        item
        for item in parsed["mapplets"]
        if item["name"] == MAPPLET_NAME
    )

    target_sql = (
        "SELECT\n"
        "    COD_ABI AS ABI\n"
        "FROM TEST_TARGET_SOURCE"
    )

    anagrafica_sql = (
        "SELECT\n"
        "    ABI_BANCA AS ABI_ANAG,\n"
        "    COD_GRUPPO AS GRUPPO_ANAG\n"
        "FROM TEST_ANAGRAFICA_SOURCE"
    )

    sql = transpile_data_flow_to_sql(
        mapping=mapplet,
        target_node="OUTPUT",
        initial_sql_by_node={
            "TARGET": target_sql,
            "ANAGRAFICA_BANCHE": (
                anagrafica_sql
            ),
        },
    )

    assert (
        "TEST_TARGET_SOURCE"
        in sql
    )

    assert (
        "TEST_ANAGRAFICA_SOURCE"
        in sql
    )

    assert (
        "FROM TARGET"
        not in sql
    )

    assert (
        "FROM ANAGRAFICA_BANCHE"
        not in sql
    )

    print(
        "\nGENERATED SQL WITH "
        "PRE-BOUND INPUTS:\n"
    )

    print(sql)

    print(
        "\nINITIAL SQL BY NODE "
        "TEST PASSED"
    )


if __name__ == "__main__":
    main()