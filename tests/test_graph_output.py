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


parsed = parse_powercenter_xml(
    XML_PATH
)


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


print(
    "\nOUTPUT GRAPH DRIVEN SQL TEST:\n"
)


sql = (
    transpile_linear_path_to_sql(
        mapping=mapplet,
        target_node="OUTPUT",
    )
)


print(
    sql
)