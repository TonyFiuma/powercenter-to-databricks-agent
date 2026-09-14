from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)

from src.transpiler.transformations.source_qualifier_translator import (
    SourceQualifierTransformationTranslator,
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
        if mapping.get("name")
        == MAPPING_NAME
    )

    transformations = {
        transformation.get("name"):
        transformation
        for transformation
        in mapping.get(
            "transformations",
            [],
        )
    }

    translator = (
        SourceQualifierTransformationTranslator()
    )

    first_sq = transformations[
        "SQ_RSK_DM_ANDINT_CONTICORRENTI_SYN"
    ]

    first_sql = translator.translate(
        mapping=mapping,
        transformation=first_sq,
        node_name=first_sq["name"],
        predecessors=[
            "RSK_DM_ANDINT_CONTICORRENTI_SYN"
        ],
        sql_by_node={},
    )

    print(
        "\nFIRST SOURCE QUALIFIER:\n"
    )
    print(first_sql)

    assert (
        "SELECT DISTINCT"
        in first_sql
    )

    assert (
        "FROM "
        "DWHEVO."
        "RSK_DM_ANDINT_CONTICORRENTI_SYN"
        in first_sql
    )

    assert (
        "DATA_RIFERIMENTO = "
        "TO_DATE('$$m_DT_RIFERIMENTO','YYYYMMDD')"
        in first_sql
    )

    second_sq = transformations[
        "SQ_RSK_WK_ANAGRAFICA_BANCHE_SOCIETA"
    ]

    second_sql = translator.translate(
        mapping=mapping,
        transformation=second_sq,
        node_name=second_sq["name"],
        predecessors=[
            "RSK_WK_ANAGRAFICA_BANCHE_SOCIETA"
        ],
        sql_by_node={},
    )

    print(
        "\nSECOND SOURCE QUALIFIER:\n"
    )
    print(second_sql)

    assert (
        "SELECT DISTINCT"
        in second_sql
    )

    assert (
        "FROM "
        "DWHEVO."
        "RSK_WK_ANAGRAFICA_BANCHE_SOCIETA"
        in second_sql
    )

    assert (
        "DATA_FINE_VALIDITA > "
        "TO_DATE('$$m_DT_RIFERIMENTO','YYYYMMDD')"
        in second_sql
    )

    assert (
        "COD_GRUPPO IN ('1', '2', '3')"
        in second_sql
    )

    print(
        "\nSOURCE QUALIFIER "
        "TRANSLATOR TEST PASSED"
    )


if __name__ == "__main__":
    main()