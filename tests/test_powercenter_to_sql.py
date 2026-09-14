from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)

from src.parser.data_flow import (
    build_adjacency_list,
    build_transformation_index,
    find_predecessors,
    find_source_instances,
    find_target_instances,
    topological_sort,
)

from src.transpiler.powercenter_to_sql import (
    build_aggregator_sql,
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
# MAPPINGS
# ============================================================


print("\nMAPPINGS FOUND:\n")

for mapping in parsed.get(
    "mappings",
    [],
):
    print(
        mapping.get("name")
    )

    print("Transformations:")

    for transformation in mapping.get(
        "transformations",
        [],
    ):
        print(
            "  -",
            transformation.get("name"),
            "|",
            transformation.get("type"),
        )

    print(
        "Connectors:",
        len(
            mapping.get(
                "connectors",
                [],
            )
        ),
    )

    print(
        "-" * 80
    )


# ============================================================
# MAPPLETS
# ============================================================


print("\nMAPPLETS FOUND:\n")

for mapplet_item in parsed.get(
    "mapplets",
    [],
):
    print(
        mapplet_item.get("name")
    )

    print("Transformations:")

    for transformation in mapplet_item.get(
        "transformations",
        [],
    ):
        print(
            "  -",
            transformation.get("name"),
            "|",
            transformation.get("type"),
        )

    print(
        "Connectors:",
        len(
            mapplet_item.get(
                "connectors",
                [],
            )
        ),
    )

    print(
        "-" * 80
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
# DATA FLOW
# ============================================================


print("\nMAPPLET DATA FLOW:\n")

print(
    "Mapplet:",
    mapplet.get("name"),
)

print()

adjacency = build_adjacency_list(
    mapplet
)

for source_node, target_nodes in (
    adjacency.items()
):
    for target_node in target_nodes:
        print(
            source_node
        )

        print(
            "    ->",
            target_node,
        )

print()

print(
    "Source instances:",
    find_source_instances(
        mapplet
    ),
)

print(
    "Target instances:",
    find_target_instances(
        mapplet
    ),
)

print(
    "-" * 80
)


# ============================================================
# TOPOLOGICAL ORDER
# ============================================================


ordered_nodes = topological_sort(
    mapplet
)

print(
    "\nTopological order:",
    ordered_nodes,
)


# ============================================================
# ORDERED TRANSFORMATIONS
# ============================================================


print(
    "\nOrdered transformations:\n"
)

transformation_index = (
    build_transformation_index(
        mapplet
    )
)

for node_name in ordered_nodes:
    transformation = (
        transformation_index.get(
            node_name
        )
    )

    if transformation is None:
        continue

    print(
        node_name,
        "|",
        transformation.get(
            "type"
        ),
    )


# ============================================================
# AGGREGATOR METADATA
# ============================================================


print(
    "\nAGGREGATOR DETAILS:\n"
)

for transformation in mapplet.get(
    "transformations",
    [],
):
    if (
        transformation.get("type")
        != "Aggregator"
    ):
        continue

    print(
        transformation.get(
            "name"
        )
    )

    for field in transformation.get(
        "fields",
        [],
    ):
        print(
            "  ",
            field.get("name"),
            "| expression:",
            field.get("expression"),
            "| type:",
            field.get(
                "expression_type"
            ),
        )

    print()


# ============================================================
# AGGREGATOR ISOLATED TEST
# ============================================================


print(
    "\nAGGREGATOR SQL TEST:\n"
)

aggtrans1 = next(
    transformation
    for transformation
    in mapplet.get(
        "transformations",
        [],
    )
    if transformation.get(
        "name"
    )
    == "AGGTRANS1"
)

manual_input_sql = """
SELECT
    ABI_BANCA,
    ABI,
    GRUPPO_ANAG
FROM EXPTRANS1
""".strip()

aggregator_sql = (
    build_aggregator_sql(
        input_sql=manual_input_sql,
        transformation=aggtrans1,
    )
)

print(
    aggregator_sql
)


# ============================================================
# PREDECESSORS
# ============================================================


print(
    "\nPREDECESSOR TEST:\n"
)

for node_name in ordered_nodes:
    predecessors = (
        find_predecessors(
            mapplet,
            node_name,
        )
    )

    print(
        node_name,
        "<-",
        predecessors,
    )


# ============================================================
# GRAPH-DRIVEN AGGTRANS1
#
# ANAGRAFICA_BANCHE
#        ↓
#    EXPTRANS1
#        ↓
#    AGGTRANS1
# ============================================================


print(
    "\nGRAPH DRIVEN AGGTRANS1 SQL TEST:\n"
)

sql = (
    transpile_linear_path_to_sql(
        mapping=mapplet,
        target_node="AGGTRANS1",
    )
)

print(
    sql
)


# ============================================================
# JOINER METADATA
# ============================================================


print(
    "\nJOINER DETAILS:\n"
)

for transformation in mapplet.get(
    "transformations",
    [],
):
    if (
        transformation.get("type")
        != "Joiner"
    ):
        continue

    print(
        "Joiner:",
        transformation.get(
            "name"
        ),
    )

    print(
        "Join condition:",
        transformation.get(
            "table_attributes",
            {},
        ).get(
            "Join Condition"
        ),
    )

    print(
        "Join type:",
        transformation.get(
            "table_attributes",
            {},
        ).get(
            "Join Type"
        ),
    )

    print(
        "Fields:"
    )

    for field in transformation.get(
        "fields",
        [],
    ):
        print(
            "  ",
            field.get("name"),
            "| port:",
            field.get(
                "port_type"
            ),
        )

    print()


# ============================================================
# GRAPH-DRIVEN JNRTRANS1
#
# EXPTRANS1 ---- MASTER ----┐
#                           ├── JNRTRANS1
# TARGET -------- DETAIL ---┘
#
# PowerCenter:
#     Normal Join
#
# Expected SQL:
#     INNER JOIN
# ============================================================


print(
    "\nJNRTRANS1 GRAPH DRIVEN SQL TEST:\n"
)

sql = (
    transpile_linear_path_to_sql(
        mapping=mapplet,
        target_node="JNRTRANS1",
    )
)

print(
    sql
)


# ============================================================
# GRAPH-DRIVEN AGGTRANS2
#
# JNRTRANS1
#     ↓
# AGGTRANS2
# ============================================================


print(
    "\nAGGTRANS2 GRAPH DRIVEN SQL TEST:\n"
)

sql = (
    transpile_linear_path_to_sql(
        mapping=mapplet,
        target_node="AGGTRANS2",
    )
)

print(
    sql
)


# ============================================================
# GRAPH-DRIVEN JNRTRANS
#
#                     ┌── AGGTRANS1
#                     │
# ANAGRAFICA_BANCHE ──┤
#                     │
#                     └── JNRTRANS1 ← TARGET
#                              ↓
#                          AGGTRANS2
#
# AGGTRANS1 ----┐
#               ├── JNRTRANS
# AGGTRANS2 ----┘
#
# PowerCenter:
#     Detail Outer Join
#
# Join condition:
#     GRUPPO_ANAG = GRUPPO_ANAG1
#
# This test verifies that the transpiler can merge
# two already-transpiled branches of the DAG.
# ============================================================


print(
    "\nJNRTRANS GRAPH DRIVEN SQL TEST:\n"
)

sql = (
    transpile_linear_path_to_sql(
        mapping=mapplet,
        target_node="JNRTRANS",
    )
)

print(
    sql
)