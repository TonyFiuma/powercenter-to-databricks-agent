from typing import Any


def resolve_powercenter_version_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    """
    Resolve the PowerCenter version used by the migration agent.

    Priority:
    1. Version detected from parsed XML metadata.
    2. Fallback version provided in the agent state.

    Raises:
        ValueError: If no PowerCenter version can be resolved.
    """

    mapping = state.get("mapping", {})
    metadata = mapping.get("metadata", {})

    detected_version = metadata.get(
        "powercenter_version"
    )

    if detected_version:
        return {
            "powercenter_version": detected_version,
            "powercenter_version_source": "xml",
        }

    fallback_version = state.get(
        "powercenter_version"
    )

    if fallback_version:
        return {
            "powercenter_version": fallback_version,
            "powercenter_version_source": "fallback",
        }

    raise ValueError(
        "Unable to determine PowerCenter version. "
        "No version was detected from the XML "
        "and no fallback was provided."
    )