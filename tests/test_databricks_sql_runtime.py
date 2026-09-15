from src.transpiler.databricks_runtime_variable import (
    DatabricksRuntimeVariable,
)
from src.transpiler.databricks_sql_runtime import (
    apply_runtime_variables_to_sql,
    render_runtime_variable,
)


def test_render_expression_runtime_variable():
    variable = DatabricksRuntimeVariable(
        source_name="$$m_DT_LOAD",
        value="current_timestamp()",
        variable_type="expression",
    )

    result = render_runtime_variable(
        variable
    )

    assert result == "current_timestamp()"


def test_render_parameter_runtime_variable():
    variable = DatabricksRuntimeVariable(
        source_name="$$m_DT_RIFERIMENTO",
        value="DT_RIFERIMENTO",
        variable_type="parameter",
    )

    result = render_runtime_variable(
        variable
    )

    assert result == ":DT_RIFERIMENTO"


def test_apply_runtime_variables_to_sql():
    sql = """
SELECT
    $$m_DT_LOAD AS DATA_INSERIMENTO
FROM source_table
WHERE DATA_RIFERIMENTO =
    TO_DATE($$m_DT_RIFERIMENTO, 'YYYYMMDD')
"""

    runtime_variables = [
        DatabricksRuntimeVariable(
            source_name="$$m_DT_LOAD",
            value="current_timestamp()",
            variable_type="expression",
        ),
        DatabricksRuntimeVariable(
            source_name="$$m_DT_RIFERIMENTO",
            value="DT_RIFERIMENTO",
            variable_type="parameter",
        ),
    ]

    result = apply_runtime_variables_to_sql(
        sql=sql,
        runtime_variables=runtime_variables,
    )

    print(result)

    assert (
        "current_timestamp() AS DATA_INSERIMENTO"
        in result
    )

    assert (
        "TO_DATE(:DT_RIFERIMENTO, 'YYYYMMDD')"
        in result
    )


def test_parameter_inside_powercenter_string_literal():
    sql = """
SELECT *
FROM source_table
WHERE DATA_RIFERIMENTO =
    TO_DATE('$$m_DT_RIFERIMENTO', 'YYYYMMDD')
"""

    runtime_variables = [
        DatabricksRuntimeVariable(
            source_name="$$m_DT_RIFERIMENTO",
            value="DT_RIFERIMENTO",
            variable_type="parameter",
        )
    ]

    result = apply_runtime_variables_to_sql(
        sql=sql,
        runtime_variables=runtime_variables,
    )

    print(result)

    assert (
        "TO_DATE(:DT_RIFERIMENTO, 'YYYYMMDD')"
        in result
    )

    assert (
        "':DT_RIFERIMENTO'"
        not in result
    )