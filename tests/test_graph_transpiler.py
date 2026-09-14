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


parsed = parse_powercenter_xml(
    XML_PATH
)


mapplets = parsed.get(
    "mapplets",
    []
)


mapplet = next(
    (
        item
        for item in mapplets
        if item.get("name")
        == MAPPLET_NAME
    ),
    None,
)


assert mapplet is not None, (
    "Expected mapplet not found: "
    f"{MAPPLET_NAME}"
)


sql = transpile_data_flow_to_sql(
    mapping=mapplet,
    target_node="OUTPUT",
)


print(
    "\nGENERATED SQL:\n"
)


print(
    sql
)


# ============================================================
# JOINER REGRESSION
# ============================================================


assert (
    "INNER JOIN"
    in sql
)


assert (
    "LEFT OUTER JOIN"
    in sql
)


# ============================================================
# AGGREGATOR REGRESSION
# ============================================================


assert (
    "GROUP BY"
    in sql
)


assert (
    "COUNT("
    in sql
)


# ============================================================
# EXPRESSION REGRESSION
#
# This is particularly important now because
# Expression must be handled by the new registry.
# ============================================================


assert (
    "CASE WHEN"
    in sql
)


assert (
    "IS NULL"
    in sql
    or "IS NOT NULL"
    in sql
)


# ============================================================
# OUTPUT REGRESSION
# ============================================================


assert (
    "AS ABI"
    in sql
)


assert (
    "AS VALORE"
    in sql
)


assert (
    "AS CONTROLLO"
    in sql
)


assert (
    "AS DELTA"
    in sql
)


assert (
    "AS PERC"
    in sql
)


assert (
    "AS ESITO"
    in sql
)


assert (
    "AS GRUPPO"
    in sql
)


print(
    "\nGRAPH TRANSPILER TEST PASSED"
)