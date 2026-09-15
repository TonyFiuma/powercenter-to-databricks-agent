from src.agent.nodes.create_migration_plan import (
    build_runtime_context,
)
from src.agent.nodes.parse_mapping import (
    parse_mapping_node,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)

MAPPING_NAME = (
    "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
)


def test_runtime_context_contains_resolved_variables():
    """
    Runtime variables already resolved by the
    deterministic layer must be exposed to the
    AI planner as deterministic facts.
    """

    state = {
        "xml_path": XML_PATH,
        "mapping_name": MAPPING_NAME,
    }

    parsed_state = parse_mapping_node(
        state
    )

    context = build_runtime_context(
        mapping=parsed_state["mapping"],
        session=parsed_state["session"],
        workflow=parsed_state["workflow"],
    )

    print("\n")
    print(context)

    assert "$$m_DT_RIFERIMENTO" in context
    assert "resolution_type: external" in context
    assert "resolved_powercenter_value: $$DT_RIFERIMENTO" in context
    assert "databricks_variable_type: parameter" in context
    assert "databricks_value: DT_RIFERIMENTO" in context

    assert "$$m_DT_LOAD" in context
    assert "resolution_type: computed" in context
    assert "resolved_powercenter_value: SYSDATE" in context
    assert "databricks_variable_type: expression" in context
    assert "databricks_value: current_timestamp()" in context