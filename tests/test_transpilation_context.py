from src.transpiler.context import (
    TranspilationContext,
)


def main() -> None:
    mapping = {
        "name": "TEST_MAPPING",
    }

    mapplets = [
        {
            "name": "TEST_MAPPLET",
        }
    ]

    context = TranspilationContext(
        mapping=mapping,
        mapplets=mapplets,
    )

    assert (
        context.mapping["name"]
        == "TEST_MAPPING"
    )

    assert (
        context.mapplets[0]["name"]
        == "TEST_MAPPLET"
    )

    print(
        "TRANSPILATION CONTEXT TEST PASSED"
    )


if __name__ == "__main__":
    main()