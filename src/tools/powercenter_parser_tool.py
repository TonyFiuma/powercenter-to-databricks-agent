import json

from langchain_core.tools import tool

from parser.powercenter_parser import parse_powercenter_xml


@tool
def parse_powercenter_mapping(xml_path: str) -> str:
    """
    Parse a PowerCenter XML export and return its structured content.

    Use this tool when you need to inspect repositories, folders,
    mappings, transformations, sources, targets, fields, or other
    information contained in a PowerCenter XML file.
    """

    parsed_data = parse_powercenter_xml(xml_path)

    return json.dumps(
        parsed_data,
        indent=2
    )