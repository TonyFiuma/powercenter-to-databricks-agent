from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedRuntimeVariable:
    """
    Structured representation of a resolved
    PowerCenter runtime variable.

    resolution_type examples:

        external
        computed
        unresolved
    """

    source_name: str
    resolved_value: str | None
    resolution_type: str