import xml.etree.ElementTree as ET

from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)
from src.parser.workflow_parser import (
    parse_workflows,
)
from src.transpiler.databricks_runtime_variable import (
    build_databricks_runtime_variables,
)
from src.transpiler.databricks_sql_runtime import (
    apply_runtime_variables_to_sql,
)
from src.transpiler.graph_transpiler import (
    transpile_data_flow_to_sql,
)
from src.transpiler.mapping_validation import (
    validate_powercenter_mapping,
)
from src.transpiler.migration_validation import (
    combine_validation_results,
)
from src.transpiler.sql_validation import (
    validate_databricks_sql,
)


def test_databricks_sql_runtime_end_to_end():
    xml_path = (
        "data/input/"
        "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
    )

    parsed = parse_powercenter_xml(
        xml_path
    )

    mapping = next(
        mapping
        for mapping in parsed["mappings"]
        if mapping["name"]
        == "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
    )

    root = ET.parse(
        xml_path
    ).getroot()

    folder = root.find(
        ".//FOLDER"
    )

    workflows = parse_workflows(
        folder
    )

    workflow = next(
        workflow
        for workflow in workflows
        if workflow["name"]
        == "wf_CONTROLLI_ANDAMENTALE_INTERNO"
    )

    session = next(
        session
        for session in workflow["sessions"]
        if session["mapping_name"]
        == mapping["name"]
    )

    # 1. Validate PowerCenter semantics
    mapping_validation = (
        validate_powercenter_mapping(
            mapping
        )
    )

    # 2. Deterministic mapping transpilation
    powercenter_sql = transpile_data_flow_to_sql(
        mapping=mapping,
        mapplets=parsed["mapplets"],
        target_node="SVDDMTBP_MASTER_CONTROLLI",
    )

    # 3. Resolve PowerCenter runtime variables
    runtime_variables = (
        build_databricks_runtime_variables(
            mapping=mapping,
            session=session,
            workflow=workflow,
        )
    )

    # 4. Render Databricks runtime SQL
    databricks_sql = (
        apply_runtime_variables_to_sql(
            sql=powercenter_sql,
            runtime_variables=runtime_variables,
        )
    )

    # 5. Validate generated SQL
    sql_validation = (
        validate_databricks_sql(
            databricks_sql
        )
    )

    # 6. Build final migration gate
    migration_validation = (
        combine_validation_results(
            mapping_validation=mapping_validation,
            sql_validation=sql_validation,
        )
    )

    print(
        "\n--- DATABRICKS SQL ---\n"
    )
    print(databricks_sql)

    print(
        "\n--- MAPPING VALIDATION ---\n"
    )
    print(mapping_validation)

    print(
        "\n--- SQL VALIDATION ---\n"
    )
    print(sql_validation)

    print(
        "\n--- MIGRATION VALIDATION ---\n"
    )
    print(migration_validation)

    assert (
        mapping_validation.status
        == "VALID"
    )

    assert (
        sql_validation.status
        == "VALID"
    )

    assert (
        migration_validation.status
        == "VALID"
    )

    assert (
        migration_validation.mapping_validation
        == mapping_validation
    )

    assert (
        migration_validation.sql_validation
        == sql_validation
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

    assert (
        "CASE WHEN"
        in sql_validation.supported_features
    )

    assert (
        "INNER JOIN"
        in sql_validation.supported_features
    )

    assert (
        "LEFT OUTER JOIN"
        in sql_validation.supported_features
    )