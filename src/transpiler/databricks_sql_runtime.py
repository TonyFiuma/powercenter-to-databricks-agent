from src.transpiler.databricks_runtime_variable import (
    DatabricksRuntimeVariable,
)


def render_runtime_variable(
    variable: DatabricksRuntimeVariable,
) -> str | None:
    """
    Render a Databricks runtime variable into
    its SQL representation.

    Current rules:

        expression
            -> executable SQL expression

        parameter
            -> named SQL parameter placeholder

        unresolved
            -> None
    """

    if variable.variable_type == "expression":
        return variable.value

    if variable.variable_type == "parameter":
        if not variable.value:
            return None

        return f":{variable.value}"

    return None


def apply_runtime_variables_to_sql(
    sql: str,
    runtime_variables: list[
        DatabricksRuntimeVariable
    ],
) -> str:
    """
    Replace PowerCenter runtime-variable
    references in SQL with their Databricks
    runtime representations.

    Both quoted and unquoted PowerCenter
    runtime-variable references are supported.

    Examples:

        $$m_DT_RIFERIMENTO
            -> :DT_RIFERIMENTO

        '$$m_DT_RIFERIMENTO'
            -> :DT_RIFERIMENTO

        $$m_DT_LOAD
            -> current_timestamp()

    Unresolved variables are intentionally
    preserved.
    """

    rendered_sql = sql

    for variable in runtime_variables:
        replacement = render_runtime_variable(
            variable
        )

        if replacement is None:
            continue

        quoted_source = (
            f"'{variable.source_name}'"
        )

        rendered_sql = rendered_sql.replace(
            quoted_source,
            replacement,
        )

        rendered_sql = rendered_sql.replace(
            variable.source_name,
            replacement,
        )

    return rendered_sql