from typing import Any

from src.transpiler.transformations.base import (
    TransformationTranslator,
)


class FakeExpressionTranslator(
    TransformationTranslator
):
    """
    Minimal implementation used only to verify
    the common translator contract.
    """

    @property
    def transformation_type(
        self,
    ) -> str:
        return "Expression"


    def translate(
        self,
        *,
        mapping: dict[str, Any],
        transformation: dict[str, Any],
        node_name: str,
        predecessors: list[str],
        sql_by_node: dict[str, str],
    ) -> str:
        return (
            "SELECT * "
            "FROM fake_expression"
        )


translator = FakeExpressionTranslator()


assert (
    translator.transformation_type
    == "Expression"
)


sql = translator.translate(
    mapping={},
    transformation={},
    node_name="EXP_TEST",
    predecessors=[],
    sql_by_node={},
)


assert (
    sql
    == "SELECT * FROM fake_expression"
)


print(
    "\nTRANSFORMATION TRANSLATOR BASE TEST PASSED"
)