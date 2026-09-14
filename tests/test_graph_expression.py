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


# ============================================================
# PARSE XML
# ============================================================


parsed = parse_powercenter_xml(
    XML_PATH
)


# ============================================================
# SELECT MAPPLET
# ============================================================


mapplet = next(
    current_mapplet
    for current_mapplet
    in parsed.get(
        "mapplets",
        [],
    )
    if current_mapplet.get(
        "name"
    )
    == "mpl_MASTER_CONTROLLI_ABI_GRUPPO"
)


# ============================================================
# GRAPH-DRIVEN EXP_CAMPI_CALCOLATI
#
# AGGTRANS1 --------------------┐
#                              │
# EXPTRANS1 -> JNRTRANS1        ├── JNRTRANS
#                  ↑            │       ↓
#                TARGET         │  connector projection
#                  ↓            │       ↓
#              AGGTRANS2 -------┘  EXP_CAMPI_CALCOLATI
#
#
# Important connector mappings:
#
# JNRTRANS.ABI_ANAG
#     -> ABI_ANAG
#
# JNRTRANS.ABI
#     -> ABI
#
# JNRTRANS.COUNT_ABI
#     -> VALORE_in
#
# JNRTRANS.COUNT_ABI_ANAG
#     -> CONTROLLO
#
# JNRTRANS.GRUPPO_ANAG
#     -> GRUPPO
#
#
# Expression translation:
#
# IIF(...)
#     -> CASE WHEN
#
# ISNULL(...)
#     -> IS NULL
#
# NOT ISNULL(...)
#     -> IS NOT NULL
#
# ============================================================


print(
    "\nEXP_CAMPI_CALCOLATI "
    "GRAPH DRIVEN SQL TEST:\n"
)


sql = (
    transpile_linear_path_to_sql(
        mapping=mapplet,
        target_node=(
            "EXP_CAMPI_CALCOLATI"
        ),
    )
)


print(
    sql
)