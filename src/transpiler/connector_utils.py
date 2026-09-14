from typing import Any

from src.transpiler.sql_utils import (
    indent_sql,
)


def find_connection(
    mapping: dict[str, Any],
    from_node: str,
    to_node: str,
) -> dict[str, Any] | None:
    """
    Find the data-flow connection between
    two PowerCenter nodes.
    """

    for connection in mapping.get(
        "data_flow",
        [],
    ):
        connection_from = (
            connection.get(
                "from",
                {},
            ).get(
                "name"
            )
        )

        connection_to = (
            connection.get(
                "to",
                {},
            ).get(
                "name"
            )
        )

        if (
            connection_from == from_node
            and connection_to == to_node
        ):
            return connection

    return None


def build_connection_projection(
    input_sql: str,
    connection: dict[str, Any],
) -> str:
    """
    Rename upstream fields according to
    PowerCenter connector mappings.
    """

    select_expressions = []
    used_target_fields = set()

    for field_connection in connection.get(
        "fields",
        [],
    ):
        from_field = (
            field_connection.get(
                "from_field"
            )
        )

        to_field = (
            field_connection.get(
                "to_field"
            )
        )

        if (
            not from_field
            or not to_field
        ):
            continue

        if to_field in used_target_fields:
            continue

        used_target_fields.add(
            to_field
        )

        select_expressions.append(
            f"src.{from_field} "
            f"AS {to_field}"
        )

    if not select_expressions:
        raise ValueError(
            "Connection does not contain "
            "field mappings."
        )

    select_clause = ",\n    ".join(
        select_expressions
    )

    return (
        "SELECT\n"
        f"    {select_clause}\n"
        "FROM (\n"
        f"{indent_sql(input_sql)}\n"
        ") src"
    )