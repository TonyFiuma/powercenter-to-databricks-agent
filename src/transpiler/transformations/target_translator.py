from src.transpiler.transformations.output_translator import (
    OutputTransformationTranslator,
)


class TargetTransformationTranslator(
    OutputTransformationTranslator
):
    """
    Translator for PowerCenter TARGET nodes.

    At SQL-IR level a target behaves as a final
    projection of the upstream transformation.

    Physical write semantics such as INSERT,
    MERGE or Delta writes are intentionally kept
    outside this translator.
    """

    @property
    def transformation_type(self) -> str:
        return "TARGET"