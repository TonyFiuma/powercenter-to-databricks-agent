from dataclasses import dataclass, field
from typing import Any


UNSUPPORTED_SOURCE_QUALIFIER_ATTRIBUTES = (
    "Sql Query",
    "User Defined Join",
    "Pre SQL",
    "Post SQL",
)

UNSUPPORTED_TARGET_INSTANCE_ATTRIBUTES = (
    "Pre SQL",
    "Post SQL",
)


@dataclass(frozen=True)
class MappingValidationIssue:
    """
    Semantic migration issue detected directly
    from the PowerCenter mapping metadata.
    """

    transformation_name: str
    category: str
    feature: str
    message: str
    severity: str


@dataclass(frozen=True)
class MappingValidationResult:
    """
    Result of PowerCenter mapping semantic
    validation.

    status examples:

        VALID
        REQUIRES_REVIEW
        UNSUPPORTED
    """

    status: str

    issues: list[MappingValidationIssue] = field(
        default_factory=list
    )


def validate_source_qualifier(
    transformation: dict[str, Any],
) -> list[MappingValidationIssue]:
    """
    Detect Source Qualifier attributes whose
    semantics are not currently migrated by the
    deterministic transpiler.

    Empty PowerCenter attributes are ignored.
    """

    issues: list[MappingValidationIssue] = []

    table_attributes = transformation.get(
        "table_attributes",
        {},
    )

    for feature in (
        UNSUPPORTED_SOURCE_QUALIFIER_ATTRIBUTES
    ):
        value = table_attributes.get(feature)

        if value is None:
            continue

        if not str(value).strip():
            continue

        issues.append(
            MappingValidationIssue(
                transformation_name=(
                    transformation.get("name")
                    or "<unknown>"
                ),
                category="unsupported_feature",
                feature=feature,
                message=(
                    "Source Qualifier feature "
                    f"'{feature}' is populated "
                    "but is not currently migrated "
                    "by the deterministic transpiler."
                ),
                severity="error",
            )
        )

    return issues


def validate_target_instance(
    instance: dict[str, Any],
) -> list[MappingValidationIssue]:
    """
    Detect Target instance attributes whose
    semantics are not currently migrated by the
    deterministic transpiler.

    Target Pre SQL and Post SQL may contain
    executable PowerCenter logic that must not
    be silently discarded.

    Empty attributes are ignored.
    """

    issues: list[MappingValidationIssue] = []

    table_attributes = instance.get(
        "table_attributes",
        {},
    )

    for feature in (
        UNSUPPORTED_TARGET_INSTANCE_ATTRIBUTES
    ):
        value = table_attributes.get(feature)

        if value is None:
            continue

        if not str(value).strip():
            continue

        issues.append(
            MappingValidationIssue(
                transformation_name=(
                    instance.get("name")
                    or "<unknown>"
                ),
                category="unsupported_feature",
                feature=feature,
                message=(
                    "Target instance feature "
                    f"'{feature}' is populated "
                    "but is not currently migrated "
                    "by the deterministic transpiler."
                ),
                severity="error",
            )
        )

    return issues


def validate_powercenter_mapping(
    mapping: dict[str, Any],
) -> MappingValidationResult:
    """
    Validate PowerCenter mapping semantics that
    may be lost before SQL generation.
    """

    issues: list[MappingValidationIssue] = []

    for transformation in mapping.get(
        "transformations",
        [],
    ):
        if (
            transformation.get("type")
            == "Source Qualifier"
        ):
            issues.extend(
                validate_source_qualifier(
                    transformation
                )
            )

    for instance in mapping.get(
        "instances",
        [],
    ):
        if instance.get("type") == "TARGET":
            issues.extend(
                validate_target_instance(
                    instance
                )
            )

    if issues:
        status = "REQUIRES_REVIEW"
    else:
        status = "VALID"

    return MappingValidationResult(
        status=status,
        issues=issues,
    )