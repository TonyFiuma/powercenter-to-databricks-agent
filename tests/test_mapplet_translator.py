from src.parser.data_flow import (
    find_predecessors,
)

from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)

from src.transpiler.graph_transpiler import (
    transpile_data_flow_to_sql,
)

from src.transpiler.transformations.mapplet_translator import (
    MappletTransformationTranslator,
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

    mapplet_instance = next(
        instance
        for instance in mapping["instances"]
        if instance["name"] == MAPPLET_NAME
    )

    first_sq_name = (
        "SQ_RSK_DM_ANDINT_"
        "CONTICORRENTI_SYN"
    )

    second_sq_name = (
        "SQ_RSK_WK_ANAGRAFICA_"
        "BANCHE_SOCIETA"
    )

    first_sq_sql = (
        transpile_data_flow_to_sql(
            mapping=mapping,
            mapplets=parsed["mapplets"],
            target_node=first_sq_name,
        )
    )

    second_sq_sql = (
        transpile_data_flow_to_sql(
            mapping=mapping,
            mapplets=parsed["mapplets"],
            target_node=second_sq_name,
        )
    )

    sql_by_node = {
        first_sq_name: first_sq_sql,
        second_sq_name: second_sq_sql,
    }

    translator = (
        MappletTransformationTranslator(
            parsed["mapplets"]
        )
    )

    sql = translator.translate(
        mapping=mapping,
        transformation=mapplet_instance,
        node_name=MAPPLET_NAME,
        predecessors=find_predecessors(
            mapping,
            MAPPLET_NAME,
        ),
        sql_by_node=sql_by_node,
    )

    assert (
        "DWHEVO."
        "RSK_DM_ANDINT_CONTICORRENTI_SYN"
        in sql
    )

    assert (
        "DWHEVO."
        "RSK_WK_ANAGRAFICA_BANCHE_SOCIETA"
        in sql
    )

    assert (
        "src.ABI AS ABI1"
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

    assert "INNER JOIN" in sql

    assert (
        "LEFT OUTER JOIN"
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
        "\nGENERATED MAPPLET SQL:\n"
    )

    print(sql)

    print(
        "\nMAPPLET TRANSLATOR "
        "TEST PASSED"
    )


if __name__ == "__main__":
    main()