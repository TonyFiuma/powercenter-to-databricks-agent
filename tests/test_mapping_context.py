from src.agent.context.mapping_context import (
    build_mapping_context,
    build_single_mapping_input,
)
from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)

MAPPING_NAME = (
    "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
)


def get_test_mapping(
    project: dict,
) -> dict:
    """
    Return the real PowerCenter mapping used by the
    mapping-context regression tests.
    """

    return next(
        mapping
        for mapping in project["mappings"]
        if mapping["name"] == MAPPING_NAME
    )


def test_single_mapping_input_contains_only_selected_mapping():
    """
    The AI context builder must receive only the selected
    PowerCenter mapping, not every mapping contained in
    the exported XML.
    """

    project = parse_powercenter_xml(
        XML_PATH
    )

    mapping = get_test_mapping(
        project
    )

    single_mapping = (
        build_single_mapping_input(
            full_mapping=project,
            pc_mapping=mapping,
        )
    )

    assert len(
        single_mapping["mappings"]
    ) == 1

    assert (
        single_mapping[
            "mappings"
        ][0]["name"]
        == MAPPING_NAME
    )


def test_target_pre_sql_is_in_mapping_context():
    """
    Target instance TABLEATTRIBUTE metadata must reach
    the context provided to the AI layer.

    The selected real mapping contains Target Pre SQL
    that performs a DELETE before loading the target.
    """

    project = parse_powercenter_xml(
        XML_PATH
    )

    mapping = get_test_mapping(
        project
    )

    single_mapping = (
        build_single_mapping_input(
            full_mapping=project,
            pc_mapping=mapping,
        )
    )

    context = build_mapping_context(
        single_mapping
    )

    assert (
        "instance_table_attributes:"
        in context
    )

    assert (
        "Pre SQL:"
        in context
    )

    assert (
        "delete from "
        "SVDDMTBP_MASTER_CONTROLLI"
        in context
    )

    assert (
        "$$m_DT_RIFERIMENTO"
        in context
    )


def test_target_post_sql_is_not_printed_when_empty():
    """
    Empty Target Post SQL must not pollute the AI
    migration context.
    """

    project = parse_powercenter_xml(
        XML_PATH
    )

    mapping = get_test_mapping(
        project
    )

    single_mapping = (
        build_single_mapping_input(
            full_mapping=project,
            pc_mapping=mapping,
        )
    )

    context = build_mapping_context(
        single_mapping
    )

    assert (
        "Post SQL:"
        not in context
    )