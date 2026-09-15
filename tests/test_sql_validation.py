from src.transpiler.sql_validation import (
    validate_databricks_sql,
)


def test_valid_sql_without_powercenter_variables():
    sql = """
SELECT *
FROM source_table
WHERE DATA_RIFERIMENTO =
    TO_DATE(:DT_RIFERIMENTO, 'YYYYMMDD')
"""

    result = validate_databricks_sql(
        sql
    )

    print(result)

    assert result.status == "VALID"
    assert result.issues == []


def test_unresolved_powercenter_variable():
    sql = """
SELECT
    $$m_UNKNOWN AS VALUE
FROM source_table
"""

    result = validate_databricks_sql(
        sql
    )

    print(result)

    assert (
        result.status
        == "REQUIRES_REVIEW"
    )

    assert len(result.issues) == 1

    issue = result.issues[0]

    assert (
        issue.category
        == "runtime_variable"
    )

    assert issue.severity == "error"

    assert (
        "$$m_UNKNOWN"
        in issue.message
    )


def test_duplicate_unresolved_variable():
    sql = """
SELECT
    $$m_UNKNOWN AS VALUE
FROM source_table
WHERE COLUMN_A = $$m_UNKNOWN
"""

    result = validate_databricks_sql(
        sql
    )

    print(result)

    assert (
        result.status
        == "REQUIRES_REVIEW"
    )

    assert len(result.issues) == 1