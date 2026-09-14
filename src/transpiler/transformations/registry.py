from typing import Iterable

from src.transpiler.transformations.base import (
    TransformationTranslator,
)


class TransformationTranslatorRegistry:
    """
    Registry of PowerCenter transformation
    translators.

    The orchestrator depends on this registry
    instead of depending directly on concrete
    translator implementations.
    """

    def __init__(
        self,
        translators: Iterable[
            TransformationTranslator
        ] | None = None,
    ) -> None:
        self._translators: dict[
            str,
            TransformationTranslator,
        ] = {}

        if translators:
            for translator in translators:
                self.register(
                    translator
                )


    def register(
        self,
        translator: TransformationTranslator,
    ) -> None:
        """
        Register one transformation translator.
        """

        transformation_type = (
            translator.transformation_type
        )

        if not transformation_type:
            raise ValueError(
                "Translator transformation_type "
                "cannot be empty."
            )

        if (
            transformation_type
            in self._translators
        ):
            raise ValueError(
                "Translator already registered "
                "for transformation type: "
                f"{transformation_type}"
            )

        self._translators[
            transformation_type
        ] = translator


    def get(
        self,
        transformation_type: str,
    ) -> TransformationTranslator | None:
        """
        Return the translator registered for
        the requested PowerCenter type.
        """

        return self._translators.get(
            transformation_type
        )


    def require(
        self,
        transformation_type: str,
    ) -> TransformationTranslator:
        """
        Return a translator or fail explicitly
        when the transformation is unsupported.
        """

        translator = self.get(
            transformation_type
        )

        if translator is None:
            raise NotImplementedError(
                "Unsupported PowerCenter "
                "transformation type: "
                f"{transformation_type}"
            )

        return translator


    def supports(
        self,
        transformation_type: str,
    ) -> bool:
        """
        Check whether a translator exists for
        the requested transformation type.
        """

        return (
            transformation_type
            in self._translators
        )


    def supported_types(
        self,
    ) -> set[str]:
        """
        Return all currently registered
        transformation types.
        """

        return set(
            self._translators.keys()
        )