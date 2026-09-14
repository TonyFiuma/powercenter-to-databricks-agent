from abc import ABC, abstractmethod
from typing import Any


class TransformationTranslator(ABC):
    """
    Base contract for PowerCenter transformation
    translators.

    Each concrete translator is responsible for
    translating exactly one PowerCenter
    transformation type into SQL.
    """

    @property
    @abstractmethod
    def transformation_type(
        self,
    ) -> str:
        """
        PowerCenter transformation type handled
        by this translator.

        Examples:

            Expression
            Aggregator
            Joiner
            Filter
        """

        raise NotImplementedError


    @abstractmethod
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
        Translate one PowerCenter transformation
        into SQL.

        Args:
            mapping:
                Parsed PowerCenter mapping.

            transformation:
                Transformation metadata.

            node_name:
                Current node name in the DAG.

            predecessors:
                Upstream nodes.

            sql_by_node:
                SQL already generated for upstream
                nodes.

        Returns:
            SQL generated for the current node.
        """

        raise NotImplementedError