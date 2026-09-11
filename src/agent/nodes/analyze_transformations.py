from src.agent.main import AgentState
from src.transformations.registry import is_supported_transformation


def analyze_transformations(state: AgentState) -> dict:
    """
    Analyze PowerCenter transformations extracted by the parser.

    Identifies supported and unsupported transformation types.
    """

    mapping = state["mapping"]

    transformations = mapping.get("transformations", [])

    detected = []
    unsupported = []

    for transformation in transformations:

        transformation_type = transformation.get("type")

        if not transformation_type:
            continue

        if transformation_type not in detected:
            detected.append(transformation_type)

        if not is_supported_transformation(transformation_type):
            if transformation_type not in unsupported:
                unsupported.append(transformation_type)

    return {
        "detected_transformations": detected,
        "unsupported_transformations": unsupported,
    }