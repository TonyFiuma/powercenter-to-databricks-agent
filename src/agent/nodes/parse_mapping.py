from src.agent.state import AgentState
from src.parser.powercenter_parser import parse_powercenter_xml


def parse_mapping_node(state: AgentState) -> dict:
    """
    Parse a PowerCenter XML file and store the structured
    mapping representation in the LangGraph state.
    """

    xml_path = state["xml_path"]

    print(f"Parsing PowerCenter XML: {xml_path}")

    mapping = parse_powercenter_xml(xml_path)

    print("PowerCenter XML parsed successfully.")

    return {
        "mapping": mapping
    }