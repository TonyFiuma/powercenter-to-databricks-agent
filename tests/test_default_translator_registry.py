from src.transpiler.transformations.default_registry import (
    build_default_translator_registry,
)


def main() -> None:
    registry = (
        build_default_translator_registry()
    )

    expected_types = {
        "Input Transformation",
        "Source Qualifier",
        "Expression",
        "Aggregator",
        "Joiner",
        "Output Transformation",
    }

    supported_types = (
        registry.supported_types()
    )

    assert (
        supported_types
        == expected_types
    )

    for transformation_type in expected_types:
        assert registry.supports(
            transformation_type
        )

        translator = registry.require(
            transformation_type
        )

        assert (
            translator.transformation_type
            == transformation_type
        )

    print(
        "DEFAULT TRANSLATOR "
        "REGISTRY TEST PASSED"
    )


if __name__ == "__main__":
    main()