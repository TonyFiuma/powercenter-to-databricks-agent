from src.transpiler.databricks_runtime_variable import (
    translate_runtime_variable,
)
from src.transpiler.resolved_runtime_variable import (
    ResolvedRuntimeVariable,
)


def test_translate_computed_runtime_variable():
    variable = ResolvedRuntimeVariable(
        source_name="$$m_DT_LOAD",
        resolved_value="SYSDATE",
        resolution_type="computed",
    )

    result = translate_runtime_variable(
        variable
    )

    print("Computed:", result)

    assert result.source_name == "$$m_DT_LOAD"
    assert result.value == "current_timestamp()"
    assert result.variable_type == "expression"


def test_translate_external_runtime_variable():
    variable = ResolvedRuntimeVariable(
        source_name="$$m_DT_RIFERIMENTO",
        resolved_value="$$DT_RIFERIMENTO",
        resolution_type="external",
    )

    result = translate_runtime_variable(
        variable
    )

    print("External:", result)

    assert (
        result.source_name
        == "$$m_DT_RIFERIMENTO"
    )
    assert result.value == "DT_RIFERIMENTO"
    assert result.variable_type == "parameter"


def test_translate_unresolved_runtime_variable():
    variable = ResolvedRuntimeVariable(
        source_name="$$m_UNKNOWN",
        resolved_value=None,
        resolution_type="unresolved",
    )

    result = translate_runtime_variable(
        variable
    )

    print("Unresolved:", result)

    assert result.source_name == "$$m_UNKNOWN"
    assert result.value is None
    assert result.variable_type == "unresolved"