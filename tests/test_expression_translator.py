from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)

from src.transpiler.expression_translator import (
    translate_powercenter_expression,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)


# ============================================================
# PARSE XML
# ============================================================


parsed = parse_powercenter_xml(
    XML_PATH
)


# ============================================================
# SELECT MAPPLET
# ============================================================


mapplet = next(
    current_mapplet
    for current_mapplet
    in parsed.get(
        "mapplets",
        [],
    )
    if current_mapplet.get(
        "name"
    )
    == "mpl_MASTER_CONTROLLI_ABI_GRUPPO"
)


# ============================================================
# SELECT EXP_CAMPI_CALCOLATI
# ============================================================


expression_transformation = next(
    transformation
    for transformation
    in mapplet.get(
        "transformations",
        [],
    )
    if transformation.get(
        "name"
    )
    == "EXP_CAMPI_CALCOLATI"
)


# ============================================================
# PRINT ORIGINAL + TRANSLATED EXPRESSIONS
# ============================================================


print(
    "\nEXP_CAMPI_CALCOLATI TRANSLATION TEST:\n"
)


for field in expression_transformation.get(
    "fields",
    [],
):
    field_name = field.get(
        "name"
    )

    expression = field.get(
        "expression"
    )

    if not expression:
        continue

    print(
        "=" * 80
    )

    print(
        "FIELD:",
        field_name,
    )

    print(
        "\nPOWERCENTER:\n"
    )

    print(
        expression
    )

    translated_expression = (
        translate_powercenter_expression(
            expression
        )
    )

    print(
        "\nSQL:\n"
    )

    print(
        translated_expression
    )

    print()


# ============================================================
# DIRECT BASIC TESTS
# ============================================================


print(
    "\nDIRECT TRANSLATION TESTS:\n"
)


test_expressions = [
    (
        "ISNULL(VALORE_in)"
    ),
    (
        "NOT ISNULL(VALORE_in)"
    ),
    (
        "IIF("
        "NOT ISNULL(VALORE_in), "
        "VALORE_in, "
        "0"
        ")"
    ),
    (
        "IIF("
        "VALORE > 10, "
        "'OK', "
        "'KO'"
        ")"
    ),
    (
        "IIF("
        "A = 1, "
        "IIF(B = 2, 10, 20), "
        "30"
        ")"
    ),
    (
        "CONCAT("
        "'COUNT_ABI_', "
        "GRUPPO_ANAG"
        ")"
    ),
]


for expression in test_expressions:
    print(
        "=" * 80
    )

    print(
        "INPUT:"
    )

    print(
        expression
    )

    print(
        "\nOUTPUT:"
    )

    print(
        translate_powercenter_expression(
            expression
        )
    )

    print()