from typing import Any

from src.transpiler.transformations.base import (
    TransformationTranslator,
)

from src.transpiler.transformations.registry import (
    TransformationTranslatorRegistry,
)


class FakeExpressionTranslator(
    TransformationTranslator
):
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


translator = (
    FakeExpressionTranslator()
)


registry = (
    TransformationTranslatorRegistry(
        translators=[
            translator,
        ]
    )
)


assert (
    registry.supports(
        "Expression"
    )
)


assert not (
    registry.supports(
        "Joiner"
    )
)


assert (
    registry.get(
        "Expression"
    )
    is translator
)


assert (
    registry.require(
        "Expression"
    )
    is translator
)


assert (
    registry.supported_types()
    == {
        "Expression",
    }
)


try:
    registry.require(
        "Joiner"
    )

    raise AssertionError(
        "Expected NotImplementedError."
    )

except NotImplementedError:
    pass


print(
    "\nTRANSFORMATION TRANSLATOR "
    "REGISTRY TEST PASSED"
)