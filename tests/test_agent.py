from agent.powercenter_agent import create_powercenter_agent


def main():
    agent = create_powercenter_agent()

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                                "Analyze the PowerCenter XML file "
                                "data/input/wf_m_DHUBTOMIS_MBDT_CSV.XML. "
                                "First use parse_powercenter_mapping to identify the Expression transformations. "
                                "Then you MUST use search_powercenter_documentation to retrieve official "
                                "PowerCenter documentation about Expression transformations. "
                                "Finally explain the Expression transformations found in the XML "
                                "using the retrieved documentation. "
                                "Do not answer before using BOTH tools."
                                )
                }
            ]
        }
    )

    print("\nMESSAGES:\n")

    for i, message in enumerate(result["messages"]):
        print(f"\n--- MESSAGE {i} ---")
        print(f"Type: {type(message).__name__}")
        print(f"Content: {message.content}")

        if hasattr(message, "tool_calls"):
            print(f"Tool calls: {message.tool_calls}")


if __name__ == "__main__":
    main()