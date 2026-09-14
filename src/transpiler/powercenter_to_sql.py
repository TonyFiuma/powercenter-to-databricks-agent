import re
from typing import Any

from src.transpiler.expression_translator import (
    translate_powercenter_expression,
)

from src.transpiler.joiner_utils import (
    build_joiner_output_expressions,
    build_joiner_sql,
    get_joiner_detail_fields,
    get_joiner_input_connections,
    get_joiner_master_fields,
    qualify_join_condition,
    translate_join_type,
)


# ============================================================
# SQL UTILITIES
# ============================================================


def indent_sql(
    sql: str,
    spaces: int = 4,
) -> str:
    prefix = " " * spaces

    return "\n".join(
        f"{prefix}{line}"
        for line in sql.splitlines()
    )


def build_source_table_name(
    source: dict[str, Any],
) -> str:
    source_name = source.get("name")
    owner_name = source.get("owner_name")

    if owner_name and source_name:
        return f"{owner_name}.{source_name}"

    if source_name:
        return source_name

    raise ValueError(
        "Unable to determine source table name."
    )


# ============================================================
# TRANSFORMATION LOOKUP
# ============================================================


def find_transformation(
    mapping: dict[str, Any],
    transformation_type: str,
) -> dict[str, Any] | None:
    for transformation in mapping.get(
        "transformations",
        [],
    ):
        if (
            transformation.get("type")
            == transformation_type
        ):
            return transformation

    return None


def find_transformation_by_name(
    mapping: dict[str, Any],
    transformation_name: str,
) -> dict[str, Any] | None:
    for transformation in mapping.get(
        "transformations",
        [],
    ):
        if (
            transformation.get("name")
            == transformation_name
        ):
            return transformation

    return None


# ============================================================
# CONNECTOR UTILITIES
# ============================================================


def find_connection(
    mapping: dict[str, Any],
    from_node: str,
    to_node: str,
) -> dict[str, Any] | None:
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


# ============================================================
# SIMPLE EXPRESSION SUPPORT
# ============================================================


def is_simple_sql_expression(
    expression: str,
) -> bool:
    allowed_pattern = re.compile(
        r"^[A-Za-z0-9_\s\+\-\*/().]+$"
    )

    return bool(
        allowed_pattern.fullmatch(
            expression
        )
    )


def translate_expression_field(
    field: dict[str, Any],
) -> str | None:
    field_name = field.get("name")

    if not field_name:
        return None

    expression = field.get(
        "expression"
    )

    if not expression:
        return field_name

    expression = (
        translate_powercenter_expression(
            expression
        )
    )

    if expression == field_name:
        return field_name

    return (
        f"{expression} "
        f"AS {field_name}"
    )


def build_select_expressions(
    transformation: dict[str, Any],
) -> list[str]:
    select_expressions = []

    for field in transformation.get(
        "fields",
        [],
    ):
        port_type = (
            field.get("port_type")
            or ""
        ).upper()

        if "OUTPUT" not in port_type:
            continue

        sql_expression = (
            translate_expression_field(
                field
            )
        )

        if sql_expression:
            select_expressions.append(
                sql_expression
            )

    return select_expressions


# ============================================================
# BASE SELECT
# ============================================================


def build_base_select(
    source_table: str,
    transformation: dict[str, Any],
) -> str:
    select_expressions = (
        build_select_expressions(
            transformation
        )
    )

    if not select_expressions:
        raise ValueError(
            "No output columns found."
        )

    select_clause = ",\n    ".join(
        select_expressions
    )

    return (
        "SELECT\n"
        f"    {select_clause}\n"
        f"FROM {source_table}"
    )


# ============================================================
# INPUT TRANSFORMATION
# ============================================================


def build_input_sql(
    transformation: dict[str, Any],
) -> str:
    """
    Legacy compatibility helper.

    New DAG-based code uses
    InputTransformationTranslator.
    """

    transformation_name = (
        transformation.get("name")
    )

    if not transformation_name:
        raise ValueError(
            "Input Transformation without name."
        )

    return (
        "SELECT *\n"
        f"FROM {transformation_name}"
    )


# ============================================================
# OUTPUT TRANSFORMATION
# ============================================================


def build_output_sql(
    input_sql: str,
    connection: dict[str, Any],
) -> str:
    """
    Legacy compatibility helper.

    Output Transformations do not contain
    executable expressions. Their semantics
    are represented by connector mappings.

    New DAG-based code uses
    OutputTransformationTranslator.
    """

    return build_connection_projection(
        input_sql=input_sql,
        connection=connection,
    )


# ============================================================
# EXPRESSION
# ============================================================


def build_expression_sql(
    input_sql: str,
    transformation: dict[str, Any],
) -> str:
    """
    Legacy compatibility implementation.

    New DAG-based code uses
    ExpressionTransformationTranslator.
    """

    select_expressions = []

    for field in transformation.get(
        "fields",
        [],
    ):
        field_name = (
            field.get(
                "name"
            )
        )

        expression = (
            field.get(
                "expression"
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

        if not expression:
            select_expressions.append(
                field_name
            )
            continue

        translated_expression = (
            translate_powercenter_expression(
                expression
            )
        )

        if (
            translated_expression
            == field_name
        ):
            select_expressions.append(
                field_name
            )
        else:
            select_expressions.append(
                f"{translated_expression} "
                f"AS {field_name}"
            )

    if not select_expressions:
        raise ValueError(
            "Expression transformation "
            f"'{transformation.get('name')}' "
            "does not contain output fields."
        )

    select_clause = ",\n    ".join(
        select_expressions
    )

    return (
        "SELECT\n"
        f"    {select_clause}\n"
        "FROM (\n"
        f"{indent_sql(input_sql)}\n"
        ") t"
    )


# ============================================================
# FILTER
# ============================================================


def apply_filter(
    sql: str,
    filter_transformation: dict[str, Any],
) -> str:
    filter_condition = (
        filter_transformation.get(
            "filter_condition"
        )
    )

    if not filter_condition:
        raise ValueError(
            "Filter transformation found "
            "but Filter Condition is missing."
        )

    translated_condition = (
        translate_powercenter_expression(
            filter_condition
        )
    )

    return (
        "SELECT *\n"
        "FROM (\n"
        f"{indent_sql(sql)}\n"
        ") t\n"
        f"WHERE {translated_condition}"
    )


# ============================================================
# AGGREGATOR
# ============================================================


def build_aggregator_sql(
    input_sql: str,
    transformation: dict[str, Any],
) -> str:
    """
    Legacy compatibility implementation.

    New DAG-based code uses
    AggregatorTransformationTranslator.
    """

    group_by_fields = []
    select_expressions = []

    for field in transformation.get(
        "fields",
        [],
    ):
        field_name = (
            field.get(
                "name"
            )
        )

        expression = (
            field.get(
                "expression"
            )
        )

        expression_type = (
            field.get(
                "expression_type"
            )
            or ""
        ).upper()

        port_type = (
            field.get(
                "port_type"
            )
            or ""
        ).upper()

        if not field_name:
            continue

        if expression_type == "GROUPBY":
            group_expression = (
                expression
                if expression
                else field_name
            )

            group_expression = (
                translate_powercenter_expression(
                    group_expression
                )
            )

            group_by_fields.append(
                group_expression
            )

            if (
                group_expression
                == field_name
            ):
                select_expressions.append(
                    field_name
                )
            else:
                select_expressions.append(
                    f"{group_expression} "
                    f"AS {field_name}"
                )

            continue

        if (
            "OUTPUT" in port_type
            and expression
        ):
            translated_expression = (
                translate_powercenter_expression(
                    expression
                )
            )

            select_expressions.append(
                f"{translated_expression} "
                f"AS {field_name}"
            )

    if not select_expressions:
        raise ValueError(
            "Aggregator transformation "
            f"'{transformation.get('name')}' "
            "does not contain SQL output fields."
        )

    if not group_by_fields:
        raise ValueError(
            "Aggregator transformation "
            f"'{transformation.get('name')}' "
            "does not contain GROUPBY fields."
        )

    select_clause = ",\n    ".join(
        select_expressions
    )

    group_by_clause = ",\n    ".join(
        group_by_fields
    )

    return (
        "SELECT\n"
        f"    {select_clause}\n"
        "FROM (\n"
        f"{indent_sql(input_sql)}\n"
        ") t\n"
        "GROUP BY\n"
        f"    {group_by_clause}"
    )


# ============================================================
# JOINER
# ============================================================
#
# Joiner logic has been moved to:
#
#     src.transpiler.joiner_utils
#
# The functions imported at the beginning of this module
# intentionally remain available here for backward
# compatibility:
#
#     get_joiner_master_fields
#     get_joiner_detail_fields
#     get_joiner_input_connections
#     translate_join_type
#     qualify_join_condition
#     build_joiner_output_expressions
#     build_joiner_sql
#
# Existing code importing them from powercenter_to_sql
# therefore continues to work.
# ============================================================


# ============================================================
# GRAPH-DRIVEN TRANSPILER
# ============================================================


def transpile_linear_path_to_sql(
    mapping: dict[str, Any],
    target_node: str,
) -> str:
    """
    Backward-compatible entry point.

    The original implementation lived in this
    legacy module and contained transformation-
    specific if/elif branches.

    DAG orchestration now belongs to:

        src.transpiler.graph_transpiler

    Existing callers can continue using this
    function without modification.
    """

    from src.transpiler.graph_transpiler import (
        transpile_data_flow_to_sql,
    )

    return transpile_data_flow_to_sql(
        mapping=mapping,
        target_node=target_node,
    )


# ============================================================
# LEGACY SIMPLE TRANSPILER
# ============================================================


def transpile_mapping_to_sql(
    mapping: dict[str, Any],
) -> str:
    """
    Legacy simple transpiler.

    Supports mappings with:

    - exactly one source;
    - Source Qualifier;
    - optional Expression;
    - optional Filter.

    This function is retained for backward
    compatibility while the DAG-driven
    transpiler becomes the main implementation.
    """

    sources = mapping.get(
        "sources",
        [],
    )

    if len(sources) != 1:
        raise NotImplementedError(
            "Only mappings with exactly one source "
            "are currently supported."
        )

    source = sources[0]

    source_table = (
        build_source_table_name(
            source
        )
    )

    source_qualifier = (
        find_transformation(
            mapping,
            "Source Qualifier",
        )
    )

    if source_qualifier is None:
        raise NotImplementedError(
            "Source Qualifier not found."
        )

    expression = (
        find_transformation(
            mapping,
            "Expression",
        )
    )

    filter_transformation = (
        find_transformation(
            mapping,
            "Filter",
        )
    )

    transformation_for_select = (
        expression
        if expression is not None
        else source_qualifier
    )

    sql = build_base_select(
        source_table=source_table,
        transformation=(
            transformation_for_select
        ),
    )

    if (
        filter_transformation
        is not None
    ):
        sql = apply_filter(
            sql=sql,
            filter_transformation=(
                filter_transformation
            ),
        )

    return sql