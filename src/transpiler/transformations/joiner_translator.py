from typing import Any

from src.transpiler.joiner_utils import (
    build_joiner_sql,
    get_joiner_input_connections,
)

from src.transpiler.transformations.base import (
    TransformationTranslator,
)


class JoinerTransformationTranslator(
    TransformationTranslator
):
    """
    SQL translator for PowerCenter
    Joiner transformations.
    """

    @property
    def transformation_type(
        self,
    ) -> str:
        return "Joiner"


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
        Translate one PowerCenter Joiner node.
        """

        if len(predecessors) != 2:
            raise NotImplementedError(
                "Joiner transformation "
                f"'{node_name}' requires exactly "
                "two predecessors."
            )

        (
            master_connection,
            detail_connection,
        ) = get_joiner_input_connections(
            mapping=mapping,
            transformation=transformation,
        )

        master_node = (
            master_connection.get(
                "from",
                {},
            ).get(
                "name"
            )
        )

        detail_node = (
            detail_connection.get(
                "from",
                {},
            ).get(
                "name"
            )
        )

        if not master_node:
            raise ValueError(
                "Unable to determine MASTER "
                f"predecessor for '{node_name}'."
            )

        if not detail_node:
            raise ValueError(
                "Unable to determine DETAIL "
                f"predecessor for '{node_name}'."
            )

        master_sql = sql_by_node.get(
            master_node
        )

        detail_sql = sql_by_node.get(
            detail_node
        )

        if master_sql is None:
            raise ValueError(
                "SQL not generated for "
                f"MASTER input '{master_node}'."
            )

        if detail_sql is None:
            raise ValueError(
                "SQL not generated for "
                f"DETAIL input '{detail_node}'."
            )

        return build_joiner_sql(
            master_sql=master_sql,
            detail_sql=detail_sql,
            master_connection=master_connection,
            detail_connection=detail_connection,
            transformation=transformation,
        )