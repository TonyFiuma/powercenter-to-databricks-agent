from typing import Any

from src.transpiler.connector_utils import (
    build_connection_projection,
    find_connection,
)

from src.transpiler.transformations.base import (
    TransformationTranslator,
)


class OutputTransformationTranslator(
    TransformationTranslator
):
    """
    SQL translator for PowerCenter
    Output Transformation nodes.
    """

    @property
    def transformation_type(
        self,
    ) -> str:
        return "Output Transformation"


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
        Translate one Output Transformation.

        Output Transformations do not contain
        executable logic. Their semantics are
        represented by connector field mappings.
        """

        if len(predecessors) != 1:
            raise NotImplementedError(
                "Output Transformation "
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

        return build_connection_projection(
            input_sql=input_sql,
            connection=connection,
        )