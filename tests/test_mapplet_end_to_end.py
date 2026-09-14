from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)

from src.transpiler.powercenter_to_sql import (
    transpile_linear_path_to_sql,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)


MAPPLET_NAME = (
    "mpl_MASTER_CONTROLLI_ABI_GRUPPO"
)


def get_test_mapplet() -> dict:
    parsed = parse_powercenter_xml(
        XML_PATH
    )

    return next(
        mapplet
        for mapplet
        in parsed.get(
            "mapplets",
            [],
        )
        if mapplet.get(
            "name"
        )
        == MAPPLET_NAME
    )


def test_mapplet_end_to_end_sql():
    mapplet = get_test_mapplet()

    sql = transpile_linear_path_to_sql(
        mapping=mapplet,
        target_node="OUTPUT",
    )

    # ========================================================
    # JOINER SEMANTICS
    # ========================================================

    assert (
        "INNER JOIN"
        in sql
    )

    assert (
        "LEFT OUTER JOIN"
        in sql
    )

    # ========================================================
    # AGGREGATORS
    # ========================================================

    assert (
        "COUNT (ABI_BANCA) AS COUNT_ABI"
        in sql
    )

    assert (
        "COUNT(ABI) AS COUNT_ABI"
        in sql
    )

    assert (
        "GROUP BY"
        in sql
    )

    # ========================================================
    # CONNECTOR RENAMING
    # ========================================================

    assert (
        "src.COUNT_ABI AS VALORE_in"
        in sql
    )

    assert (
        "src.COUNT_ABI_ANAG AS CONTROLLO"
        in sql
    )

    assert (
        "src.GRUPPO_ANAG AS GRUPPO"
        in sql
    )

    # ========================================================
    # EXPRESSION TRANSLATION
    # ========================================================

    assert (
        "VALORE_in IS NOT NULL"
        in sql
    )

    assert (
        "CASE WHEN"
        in sql
    )

    assert (
        "VALORE_in IS NULL"
        in sql
    )

    assert (
        "'OK'"
        in sql
    )

    assert (
        "'KO'"
        in sql
    )

    # ========================================================
    # OUTPUT TRANSFORMATION
    # ========================================================

    assert (
        "src.ABI_ANAG AS ABI"
        in sql
    )

    assert (
        "src.VALORE AS VALORE"
        in sql
    )

    assert (
        "src.CONTROLLO AS CONTROLLO"
        in sql
    )

    assert (
        "src.DELTA AS DELTA"
        in sql
    )

    assert (
        "src.PERC AS PERC"
        in sql
    )

    assert (
        "src.ESITO AS ESITO"
        in sql
    )

    assert (
        "src.GRUPPO AS GRUPPO"
        in sql
    )