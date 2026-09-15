from dataclasses import dataclass
from typing import Any

from src.transpiler.resolved_runtime_variable import (
    ResolvedRuntimeVariable,
)
from src.transpiler.runtime_variable_resolver import (
    resolve_mapping_runtime_variables,
)


@dataclass(frozen=True)
class DatabricksRuntimeVariable:
    """
    Databricks-oriented representation of a
    resolved PowerCenter runtime variable.

    variable_type examples:

        expression
        parameter
        unresolved
    """

    source_name: str
    value: str | None
    variable_type: str


def translate_runtime_variable(
    variable: ResolvedRuntimeVariable,
) -> DatabricksRuntimeVariable:
    """
    Translate a resolved PowerCenter runtime
    variable into a Databricks-oriented runtime
    representation.

    Current deterministic rules:

        computed + SYSDATE
            -> current_timestamp()

        external
            -> Databricks runtime parameter

        unresolved
            -> unresolved
    """

    if variable.resolution_type == "computed":
        if variable.resolved_value == "SYSDATE":
            return DatabricksRuntimeVariable(
                source_name=variable.source_name,
                value="current_timestamp()",
                variable_type="expression",
            )

        return DatabricksRuntimeVariable(
            source_name=variable.source_name,
            value=variable.resolved_value,
            variable_type="expression",
        )

    if variable.resolution_type == "external":
        value = variable.resolved_value

        if value and value.startswith("$$"):
            value = value[2:]

        return DatabricksRuntimeVariable(
            source_name=variable.source_name,
            value=value,
            variable_type="parameter",
        )

    return DatabricksRuntimeVariable(
        source_name=variable.source_name,
        value=None,
        variable_type="unresolved",
    )


def build_databricks_runtime_variables(
    mapping: dict[str, Any],
    session: dict[str, Any],
    workflow: dict[str, Any],
) -> list[DatabricksRuntimeVariable]:
    """
    Discover all PowerCenter runtime variables
    referenced by a mapping, resolve their origin
    through the session and workflow, and translate
    them into Databricks-oriented runtime variables.
    """

    resolved_variables = (
        resolve_mapping_runtime_variables(
            mapping=mapping,
            session=session,
            workflow=workflow,
        )
    )

    return [
        translate_runtime_variable(variable)
        for variable in resolved_variables
    ]