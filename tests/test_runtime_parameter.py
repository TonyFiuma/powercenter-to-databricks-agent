from src.transpiler.runtime_parameter import (
    extract_runtime_parameters,
)


def test_extract_runtime_parameters():
    result_1 = extract_runtime_parameters(
        "TO_DATE($$m_DT_RIFERIMENTO,'YYYYMMDD')"
    )

    result_2 = extract_runtime_parameters(
        "$$m_DT_LOAD"
    )

    print(result_1)
    print(result_2)

    assert len(result_1) == 1
    assert result_1[0].name == "m_DT_RIFERIMENTO"
    assert (
        result_1[0].raw_name
        == "$$m_DT_RIFERIMENTO"
    )

    assert len(result_2) == 1
    assert result_2[0].name == "m_DT_LOAD"
    assert (
        result_2[0].raw_name
        == "$$m_DT_LOAD"
    )