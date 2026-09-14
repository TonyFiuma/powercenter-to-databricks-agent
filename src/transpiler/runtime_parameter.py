import re
from dataclasses import dataclass
from typing import Any


POWERCENTER_PARAMETER_PATTERN = re.compile(
    r"\$\$[A-Za-z_][A-Za-z0-9_]*"
)


@dataclass(frozen=True)
class RuntimeParameter:
    """
    Runtime parameter referenced by PowerCenter logic.

    Example:

        $$m_DT_RIFERIMENTO

    becomes:

        RuntimeParameter(
            name="m_DT_RIFERIMENTO",
            raw_name="$$m_DT_RIFERIMENTO",
        )
    """

    name: str
    raw_name: str


def extract_runtime_parameters(
    expression: str | None,
) -> list[RuntimeParameter]:
    """
    Extract PowerCenter runtime parameters from
    an expression.

    Parameters are identified by the PowerCenter
    $$ prefix.
    """

    if not expression:
        return []

    raw_parameters = (
        POWERCENTER_PARAMETER_PATTERN.findall(
            expression
        )
    )

    parameters: list[RuntimeParameter] = []
    seen: set[str] = set()

    for raw_name in raw_parameters:
        if raw_name in seen:
            continue

        seen.add(raw_name)

        parameters.append(
            RuntimeParameter(
                name=raw_name[2:],
                raw_name=raw_name,
            )
        )

    return parameters


def extract_mapping_runtime_parameters(
    mapping: dict[str, Any],
) -> list[RuntimeParameter]:
    """
    Scan a parsed PowerCenter mapping and collect
    all runtime parameters referenced inside
    transformation field expressions.

    Duplicate parameters are returned only once.
    """

    parameters: list[RuntimeParameter] = []
    seen: set[str] = set()

    for transformation in mapping.get(
        "transformations",
        [],
    ):
        for field in transformation.get(
            "fields",
            [],
        ):
            expression = field.get("expression")

            for parameter in extract_runtime_parameters(
                expression
            ):
                if parameter.raw_name in seen:
                    continue

                seen.add(parameter.raw_name)
                parameters.append(parameter)

    return parameters