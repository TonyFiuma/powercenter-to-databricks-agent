from tools.powercenter_docs_tool import search_powercenter_documentation


def main():
    result = search_powercenter_documentation.invoke(
        {
            "query": "How does a Filter transformation work?"
        }
    )

    print(result)


if __name__ == "__main__":
    main()