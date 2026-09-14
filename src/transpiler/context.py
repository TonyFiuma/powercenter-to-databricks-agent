from dataclasses import dataclass, field
from typing import Any


@dataclass
class TranspilationContext:
    """
    Shared context used during PowerCenter
    SQL transpilation.

    It contains information that is broader
    than a single transformation node.

    Examples:

    - current mapping;
    - available mapplet definitions;
    - future runtime parameters or metadata.
    """

    mapping: dict[str, Any]

    mapplets: list[
        dict[str, Any]
    ] = field(
        default_factory=list
    )