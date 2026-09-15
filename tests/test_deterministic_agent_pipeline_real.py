from src.agent.nodes.parse_mapping import (
    parse_mapping_node,
)
from src.agent.nodes.run_deterministic_migration import (
    run_deterministic_migration_node,
)
from src.agent.nodes.transpile_deterministic_migration import (
    transpile_deterministic_migration_node,
)
from src.agent.nodes.validate_deterministic_migration import (
    validate_deterministic_migration,
)


def test_deterministic_agent_pipeline_real():
    state = {
        "xml_path": (
            "data/input/"
            "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
        ),
        "mapping_name": (
            "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
        ),
    }

    # 1. Parse and resolve execution context
    state.update(
        parse_mapping_node(
            state
        )
    )

    # 2. Deterministic transpilation
    state.update(
        transpile_deterministic_migration_node(
            state
        )
    )

    # 3. Mapping + SQL validation
    state.update(
        run_deterministic_migration_node(
            state
        )
    )

    # 4. Convert validation result into
    #    agent decision state
    state.update(
        validate_deterministic_migration(
            state
        )
    )

    print(
        "\n--- AGENT DETERMINISTIC GATE ---\n"
    )

    print(
        "Mapping:",
        state["mapping"]["name"],
    )

    print(
        "Workflow:",
        state["workflow"]["name"],
    )

    print(
        "Session:",
        state["session"]["name"],
    )

    print(
        "Mapping validation:",
        state["mapping_validation"],
    )

    print(
        "SQL validation:",
        state["sql_validation"],
    )

    print(
        "Migration validation:",
        state["migration_validation"],
    )

    print(
        "Agent validation status:",
        state["validation_status"],
    )

    print(
        "Validation issues:",
        state["validation_issues"],
    )

    databricks_sql = state[
        "databricks_sql"
    ]

    assert (
        state["validation_status"]
        == "VALID"
    )

    assert (
        state["mapping_validation"].status
        == "VALID"
    )

    assert (
        state["sql_validation"].status
        == "VALID"
    )

    assert (
        state["migration_validation"].status
        == "VALID"
    )

    assert (
        state["validation_issues"]
        == []
    )

    assert (
        "$$m_DT_RIFERIMENTO"
        not in databricks_sql
    )

    assert (
        "$$m_DT_LOAD"
        not in databricks_sql
    )

    assert (
        ":DT_RIFERIMENTO"
        in databricks_sql
    )

    assert (
        "current_timestamp()"
        in databricks_sql
    )