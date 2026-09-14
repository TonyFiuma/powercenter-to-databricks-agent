from typing import Any

from src.transpiler.transformations.aggregator_translator import (
    AggregatorTransformationTranslator,
)
from src.transpiler.transformations.expression_translator import (
    ExpressionTransformationTranslator,
)
from src.transpiler.transformations.input_translator import (
    InputTransformationTranslator,
)
from src.transpiler.transformations.joiner_translator import (
    JoinerTransformationTranslator,
)
from src.transpiler.transformations.mapplet_translator import (
    MappletTransformationTranslator,
)
from src.transpiler.transformations.output_translator import (
    OutputTransformationTranslator,
)
from src.transpiler.transformations.registry import (
    TransformationTranslatorRegistry,
)
from src.transpiler.transformations.source_qualifier_translator import (
    SourceQualifierTransformationTranslator,
)
from src.transpiler.transformations.target_translator import (
    TargetTransformationTranslator,
)


def build_default_translator_registry(
    mapplets: list[dict[str, Any]] | None = None,
) -> TransformationTranslatorRegistry:
    """
    Build the default registry containing all
    currently supported PowerCenter
    transformation translators.

    Mapplet definitions are injected into the
    Mapplet translator so the graph orchestrator
    does not need transformation-specific logic.
    """

    return TransformationTranslatorRegistry(
        translators=[
            InputTransformationTranslator(),
            SourceQualifierTransformationTranslator(),
            ExpressionTransformationTranslator(),
            AggregatorTransformationTranslator(),
            JoinerTransformationTranslator(),
            OutputTransformationTranslator(),
            MappletTransformationTranslator(
                mapplets or []
            ),
            TargetTransformationTranslator(),
        ]
    )