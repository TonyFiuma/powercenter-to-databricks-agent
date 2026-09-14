from typing import Any

from src.transpiler.connector_utils import (
    build_connection_projection,
    find_connection,
)

from src.transpiler.expression_translator import (
    translate_powercenter_expression,
)

from src.transpiler.sql_utils import (
    indent_sql,
)

from src.transpiler.transformations.base import (
    TransformationTranslator,
)


def build_aggregator_sql(
    input_sql: str,
    transformation: dict[str, Any],
) -> str:
    """
    Translate a PowerCenter Aggregator
    transformation into SQL.
    """

    group_by_fields = []
    select_expressions = []

    for field in transformation.get(
        "fields",
        [],
    ):
        field_name = field.get(
            "name"
        )

        expression = field.get(
            "expression"
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


class AggregatorTransformationTranslator(
    TransformationTranslator
):
    """
    SQL translator for PowerCenter
    Aggregator transformations.
    """

    @property
    def transformation_type(
        self,
    ) -> str:
        return "Aggregator"


    def translate(
        self,
        *,
        mapping: dict[str, Any],
        transformation: dict[str, Any],
        node_name: str,
        predecessors: list[str],
        sql_by_node: dict[str, str],
    ) -> str:
        """
        Translate one Aggregator node.
        """

        if len(predecessors) != 1:
            raise NotImplementedError(
                "Aggregator transformation "
                f"'{node_name}' requires exactly "
                "one predecessor."
            )

        input_node = predecessors[0]

        input_sql = sql_by_node.get(
            input_node
        )

        if input_sql is None:
            raise ValueError(
                "SQL not generated for "
                f"predecessor '{input_node}'."
            )

        connection = find_connection(
            mapping=mapping,
            from_node=input_node,
            to_node=node_name,
        )

        if connection is None:
            raise ValueError(
                "Connection not found between "
                f"'{input_node}' and "
                f"'{node_name}'."
            )

        projected_input_sql = (
            build_connection_projection(
                input_sql=input_sql,
                connection=connection,
            )
        )

        return build_aggregator_sql(
            input_sql=projected_input_sql,
            transformation=transformation,
        )