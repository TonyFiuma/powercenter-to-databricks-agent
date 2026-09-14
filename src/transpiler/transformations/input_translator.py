from typing import Any

from src.transpiler.transformations.base import (
    TransformationTranslator,
)


class InputTransformationTranslator(
    TransformationTranslator
):
    """
    SQL translator for PowerCenter
    Input Transformation nodes.
    """

    @property
    def transformation_type(
        self,
    ) -> str:
        return "Input Transformation"


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
        Translate one Input Transformation
        into a basic SQL source query.
        """

        transformation_name = (
            transformation.get(
                "name"
            )
        )

        if not transformation_name:
            raise ValueError(
                "Input Transformation without name."
            )

        return (
            "SELECT *\n"
            f"FROM {transformation_name}"
        )