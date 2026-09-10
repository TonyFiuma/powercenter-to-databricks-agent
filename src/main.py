import json

from parser.powercenter_parser import parse_powercenter_xml


def main():
    file_path = "data/input/wf_m_DHUBTOMIS_MBDT_CSV.XML"

    parsed_data = parse_powercenter_xml(file_path)

    print(json.dumps(parsed_data, indent=4))


if __name__ == "__main__":
    main()