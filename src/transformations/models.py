from dataclasses import dataclass, field


@dataclass(frozen=True)
class TransformationSpec:
    """
    Describes how a PowerCenter transformation should be handled
    by the migration agent.
    """

    powercenter_type: str

    supported: bool

    pyspark_operations: list[str] = field(default_factory=list)

    retrieval_tags: list[str] = field(default_factory=list)

    requires_partitioning: bool = False
    requires_ordering: bool = False
    requires_state: bool = False

    notes: str | None = None