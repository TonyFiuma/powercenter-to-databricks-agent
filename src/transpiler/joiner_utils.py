import re
from typing import Any

from src.transpiler.connector_utils import (
    build_connection_projection,
)

from src.transpiler.sql_utils import (
    indent_sql,
)


def get_joiner_master_fields(
    transformation: dict[str, Any],
) -> set[str]:
    """
    Return all fields belonging to the MASTER
    side of a PowerCenter Joiner transformation.
    """

    return {
        field.get("name")
        for field in transformation.get(
            "fields",
            [],
        )
        if (
            field.get("name")
            and "MASTER" in (
                field.get("port_type")
                or ""
            ).upper()
        )
    }


def get_joiner_detail_fields(
    transformation: dict[str, Any],
) -> set[str]:
    """
    Return all fields belonging to the DETAIL
    side of a PowerCenter Joiner transformation.
    """

    detail_fields = set()

    for field in transformation.get(
        "fields",
        [],
    ):
        field_name = (
            field.get(
                "name"
            )
        )

        port_type = (
            field.get(
                "port_type"
            )
            or ""
        ).upper()

        if not field_name:
            continue

        if "INPUT" not in port_type:
            continue

        if "MASTER" in port_type:
            continue

        detail_fields.add(
            field_name
        )

    return detail_fields


def get_joiner_input_connections(
    mapping: dict[str, Any],
    transformation: dict[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
]:
    """
    Identify MASTER and DETAIL connections
    feeding a PowerCenter Joiner.
    """

    joiner_name = (
        transformation.get(
            "name"
        )
    )

    if not joiner_name:
        raise ValueError(
            "Joiner transformation without name."
        )

    master_fields = (
        get_joiner_master_fields(
            transformation
        )
    )

    master_connection = None
    detail_connection = None

    for connection in mapping.get(
        "data_flow",
        [],
    ):
        to_name = (
            connection.get(
                "to",
                {},
            ).get(
                "name"
            )
        )

        if to_name != joiner_name:
            continue

        target_fields = {
            field_connection.get(
                "to_field"
            )
            for field_connection
            in connection.get(
                "fields",
                [],
            )
            if field_connection.get(
                "to_field"
            )
        }

        feeds_master = bool(
            target_fields
            & master_fields
        )

        if feeds_master:
            master_connection = (
                connection
            )
        else:
            detail_connection = (
                connection
            )

    if master_connection is None:
        raise ValueError(
            "Unable to identify MASTER "
            f"input for Joiner '{joiner_name}'."
        )

    if detail_connection is None:
        raise ValueError(
            "Unable to identify DETAIL "
            f"input for Joiner '{joiner_name}'."
        )

    return (
        master_connection,
        detail_connection,
    )


def translate_join_type(
    join_type: str,
) -> str:
    """
    Translate PowerCenter Join Type semantics
    into SQL JOIN syntax.
    """

    join_type_mapping = {
        "Normal Join": (
            "INNER JOIN"
        ),
        "Master Outer Join": (
            "RIGHT OUTER JOIN"
        ),
        "Detail Outer Join": (
            "LEFT OUTER JOIN"
        ),
        "Full Outer Join": (
            "FULL OUTER JOIN"
        ),
    }

    sql_join_type = (
        join_type_mapping.get(
            join_type
        )
    )

    if sql_join_type is None:
        raise NotImplementedError(
            "Unsupported PowerCenter "
            f"Join Type: {join_type}"
        )

    return sql_join_type


def qualify_join_condition(
    join_condition: str,
    transformation: dict[str, Any],
) -> str:
    """
    Qualify Joiner condition fields with the
    MASTER alias 'm' or DETAIL alias 'd'.
    """

    master_fields = (
        get_joiner_master_fields(
            transformation
        )
    )

    detail_fields = (
        get_joiner_detail_fields(
            transformation
        )
    )

    qualified_condition = (
        join_condition
    )

    all_fields = sorted(
        master_fields
        | detail_fields,
        key=len,
        reverse=True,
    )

    for field_name in all_fields:
        if field_name in master_fields:
            alias = "m"
        else:
            alias = "d"

        pattern = re.compile(
            rf"(?<![\w.])"
            rf"{re.escape(field_name)}"
            rf"(?![\w])"
        )

        qualified_condition = (
            pattern.sub(
                f"{alias}.{field_name}",
                qualified_condition,
            )
        )

    return qualified_condition


def build_joiner_output_expressions(
    transformation: dict[str, Any],
) -> list[str]:
    """
    Build SELECT expressions for the output
    ports of a PowerCenter Joiner.
    """

    expressions = []

    master_fields = (
        get_joiner_master_fields(
            transformation
        )
    )

    detail_fields = (
        get_joiner_detail_fields(
            transformation
        )
    )

    for field in transformation.get(
        "fields",
        [],
    ):
        field_name = (
            field.get(
                "name"
            )
        )

        port_type = (
            field.get(
                "port_type"
            )
            or ""
        ).upper()

        if not field_name:
            continue

        if "OUTPUT" not in port_type:
            continue

        if field_name in master_fields:
            expressions.append(
                f"m.{field_name} "
                f"AS {field_name}"
            )

        elif field_name in detail_fields:
            expressions.append(
                f"d.{field_name} "
                f"AS {field_name}"
            )

        else:
            raise ValueError(
                "Unable to determine source "
                f"for Joiner output field "
                f"'{field_name}'."
            )

    return expressions


def build_joiner_sql(
    master_sql: str,
    detail_sql: str,
    master_connection: dict[str, Any],
    detail_connection: dict[str, Any],
    transformation: dict[str, Any],
) -> str:
    """
    Generate SQL for a PowerCenter Joiner
    transformation.
    """

    table_attributes = (
        transformation.get(
            "table_attributes",
            {},
        )
    )

    join_condition = (
        table_attributes.get(
            "Join Condition"
        )
    )

    join_type = (
        table_attributes.get(
            "Join Type"
        )
    )

    if not join_condition:
        raise ValueError(
            "Joiner transformation "
            f"'{transformation.get('name')}' "
            "does not contain a Join Condition."
        )

    if not join_type:
        raise ValueError(
            "Joiner transformation "
            f"'{transformation.get('name')}' "
            "does not contain a Join Type."
        )

    sql_join_type = (
        translate_join_type(
            join_type
        )
    )

    projected_master_sql = (
        build_connection_projection(
            input_sql=master_sql,
            connection=master_connection,
        )
    )

    projected_detail_sql = (
        build_connection_projection(
            input_sql=detail_sql,
            connection=detail_connection,
        )
    )

    qualified_condition = (
        qualify_join_condition(
            join_condition=join_condition,
            transformation=transformation,
        )
    )

    output_expressions = (
        build_joiner_output_expressions(
            transformation
        )
    )

    if not output_expressions:
        raise ValueError(
            "Joiner transformation "
            f"'{transformation.get('name')}' "
            "does not contain output ports."
        )

    select_clause = ",\n    ".join(
        output_expressions
    )

    return (
        "SELECT\n"
        f"    {select_clause}\n"
        "FROM (\n"
        f"{indent_sql(projected_master_sql)}\n"
        ") m\n"
        f"{sql_join_type} (\n"
        f"{indent_sql(projected_detail_sql)}\n"
        ") d\n"
        f"ON {qualified_condition}"
    )