from tools.powercenter_parser_tool import parse_powercenter_mapping


def main():

    result = parse_powercenter_mapping.invoke(
        {
            "xml_path": "data/input/wf_m_DHUBTOMIS_MBDT_CSV.XML"
        }
    )

    print(result)


if __name__ == "__main__":
    main()