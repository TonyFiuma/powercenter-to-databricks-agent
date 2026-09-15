from src.transpiler.sql_validation import (
    detect_supported_features,
)


def test_detect_supported_features():
    sql = """
SELECT
    CASE WHEN VALUE IS NULL
        THEN 0
        ELSE VALUE
    END AS VALUE,

    CONCAT('COUNT_', GRUPPO) AS LABEL,

    COUNT(ABI) AS COUNT_ABI

FROM source_table a

INNER JOIN second_table b
    ON a.ID = b.ID

LEFT OUTER JOIN third_table c
    ON a.ID = c.ID

GROUP BY
    GRUPPO
"""

    features = detect_supported_features(
        sql
    )

    print("Detected features:")
    print(features)

    assert "CASE WHEN" in features
    assert "CONCAT" in features
    assert "COUNT" in features
    assert "GROUP BY" in features
    assert "INNER JOIN" in features
    assert "LEFT OUTER JOIN" in features