from src.transpiler.mapping_validation import (
    validate_powercenter_mapping,
)


def test_mapping_with_unsupported_pre_sql():
    mapping = {
        "transformations": [
            {
                "name": "SQ_CUSTOMERS",
                "type": "Source Qualifier",
                "table_attributes": {
                    "Source Filter": "",
                    "Select Distinct": "NO",
                    "Pre SQL": (
                        "DELETE FROM TEMP_CUSTOMERS"
                    ),
                    "Post SQL": "",
                    "Sql Query": "",
                    "User Defined Join": "",
                },
            }
        ]
    }

    result = validate_powercenter_mapping(
        mapping
    )

    print(
        "\n--- MAPPING VALIDATION ---\n"
    )
    print(result)

    assert (
        result.status
        == "REQUIRES_REVIEW"
    )

    assert len(result.issues) == 1

    issue = result.issues[0]

    assert (
        issue.transformation_name
        == "SQ_CUSTOMERS"
    )

    assert (
        issue.category
        == "unsupported_feature"
    )

    assert issue.feature == "Pre SQL"

    assert issue.severity == "error"

    assert (
        "not currently migrated"
        in issue.message
    )


def test_empty_unsupported_attributes_are_ignored():
    mapping = {
        "transformations": [
            {
                "name": "SQ_CUSTOMERS",
                "type": "Source Qualifier",
                "table_attributes": {
                    "Pre SQL": "",
                    "Post SQL": "",
                    "Sql Query": "",
                    "User Defined Join": "",
                },
            }
        ]
    }

    result = validate_powercenter_mapping(
        mapping
    )

    print(result)

    assert result.status == "VALID"
    assert result.issues == []

def test_target_instance_with_pre_sql_requires_review():
    mapping = {
        "transformations": [],
        "instances": [
            {
                "name": "SVDDMTBP_MASTER_CONTROLLI",
                "transformation_name": (
                    "SVDDMTBP_MASTER_CONTROLLI"
                ),
                "transformation_type": (
                    "Target Definition"
                ),
                "type": "TARGET",
                "table_attributes": {
                    "Pre SQL": (
                        "DELETE FROM "
                        "SVDDMTBP_MASTER_CONTROLLI "
                        "WHERE id_quadratura = 'ID_01'"
                    ),
                    "Post SQL": "",
                },
            }
        ],
    }

    result = validate_powercenter_mapping(
        mapping
    )

    assert (
        result.status
        == "REQUIRES_REVIEW"
    )

    assert len(result.issues) == 1

    issue = result.issues[0]

    assert (
        issue.transformation_name
        == "SVDDMTBP_MASTER_CONTROLLI"
    )

    assert (
        issue.category
        == "unsupported_feature"
    )

    assert issue.feature == "Pre SQL"
    assert issue.severity == "error"

    assert (
        "Target instance"
        in issue.message
    )