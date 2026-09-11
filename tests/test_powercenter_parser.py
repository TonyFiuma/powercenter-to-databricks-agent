from parser.powercenter_parser import parse_powercenter_xml
from agent.context.mapping_context import (
    build_mapping_context,
    build_single_mapping_input,
)


xml_path = (
    "data/input/"
    "wf_m_DHUBTOMIS_MBDT_CSV.XML"
)

result = parse_powercenter_xml(xml_path)

mapping = result["mappings"][0]

single_mapping = build_single_mapping_input(
    full_mapping=result,
    pc_mapping=mapping,
)

context = build_mapping_context(
    single_mapping
)

print(context)