import re


def split_function_arguments(
    arguments: str,
) -> list[str]:
    """
    Split the arguments of a PowerCenter function.

    Commas inside nested functions are ignored.

    Example:

        A,
        IIF(B = 1, 10, 20),
        C

    becomes:

        [
            "A",
            "IIF(B = 1, 10, 20)",
            "C",
        ]
    """

    result = []
    current = []

    parentheses_depth = 0
    inside_string = False

    index = 0

    while index < len(arguments):
        character = arguments[index]

        if character == "'":
            current.append(character)

            # Handle escaped SQL quote:
            # 'John''s'
            if (
                inside_string
                and index + 1 < len(arguments)
                and arguments[index + 1] == "'"
            ):
                current.append("'")
                index += 2
                continue

            inside_string = not inside_string
            index += 1
            continue

        if not inside_string:
            if character == "(":
                parentheses_depth += 1

            elif character == ")":
                parentheses_depth -= 1

            elif (
                character == ","
                and parentheses_depth == 0
            ):
                result.append(
                    "".join(current).strip()
                )

                current = []

                index += 1
                continue

        current.append(character)
        index += 1

    if current:
        result.append(
            "".join(current).strip()
        )

    return result


def find_matching_parenthesis(
    expression: str,
    opening_position: int,
) -> int:
    """
    Find the closing parenthesis corresponding
    to an opening parenthesis.
    """

    depth = 0
    inside_string = False

    index = opening_position

    while index < len(expression):
        character = expression[index]

        if character == "'":
            if (
                inside_string
                and index + 1 < len(expression)
                and expression[index + 1] == "'"
            ):
                index += 2
                continue

            inside_string = not inside_string

        elif not inside_string:
            if character == "(":
                depth += 1

            elif character == ")":
                depth -= 1

                if depth == 0:
                    return index

        index += 1

    raise ValueError(
        "Unbalanced parentheses in "
        f"PowerCenter expression: {expression}"
    )


def translate_isnull(
    argument: str,
) -> str:
    """
    Translate:

        ISNULL(column)

    into:

        column IS NULL
    """

    translated_argument = (
        translate_powercenter_expression(
            argument
        )
    )

    return (
        f"{translated_argument} IS NULL"
    )


def translate_concat(
    arguments: str,
) -> str:
    """
    Translate PowerCenter CONCAT.

    CONCAT is also supported by Spark SQL,
    therefore only its arguments need to
    be recursively translated.
    """

    parsed_arguments = (
        split_function_arguments(
            arguments
        )
    )

    if len(parsed_arguments) != 2:
        raise NotImplementedError(
            "CONCAT currently requires "
            "exactly two arguments."
        )

    translated_arguments = [
        translate_powercenter_expression(
            argument
        )
        for argument in parsed_arguments
    ]

    return (
        "CONCAT("
        + ", ".join(
            translated_arguments
        )
        + ")"
    )


def translate_iif(
    arguments: str,
) -> str:
    """
    Translate:

        IIF(condition, true_value, false_value)

    into:

        CASE
            WHEN condition
            THEN true_value
            ELSE false_value
        END

    Nested IIF expressions are supported
    recursively.
    """

    parsed_arguments = (
        split_function_arguments(
            arguments
        )
    )

    if len(parsed_arguments) != 3:
        raise NotImplementedError(
            "IIF requires exactly "
            "three arguments."
        )

    condition = (
        translate_powercenter_expression(
            parsed_arguments[0]
        )
    )

    true_value = (
        translate_powercenter_expression(
            parsed_arguments[1]
        )
    )

    false_value = (
        translate_powercenter_expression(
            parsed_arguments[2]
        )
    )

    return (
        "CASE "
        f"WHEN {condition} "
        f"THEN {true_value} "
        f"ELSE {false_value} "
        "END"
    )


def translate_function_calls(
    expression: str,
) -> str:
    """
    Translate supported PowerCenter functions
    recursively.

    Currently supported:

        IIF
        ISNULL
        CONCAT
    """

    supported_functions = {
        "IIF",
        "ISNULL",
        "CONCAT",
    }

    index = 0

    while index < len(expression):
        match = re.search(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(",
            expression[index:],
        )

        if match is None:
            break

        function_name = (
            match.group(1).upper()
        )

        function_start = (
            index
            + match.start()
        )

        opening_parenthesis = (
            index
            + match.end()
            - 1
        )

        if (
            function_name
            not in supported_functions
        ):
            index = (
                opening_parenthesis + 1
            )
            continue

        closing_parenthesis = (
            find_matching_parenthesis(
                expression,
                opening_parenthesis,
            )
        )

        arguments = expression[
            opening_parenthesis + 1:
            closing_parenthesis
        ]

        if function_name == "IIF":
            translated_function = (
                translate_iif(
                    arguments
                )
            )

        elif function_name == "ISNULL":
            translated_function = (
                translate_isnull(
                    arguments
                )
            )

        elif function_name == "CONCAT":
            translated_function = (
                translate_concat(
                    arguments
                )
            )

        else:
            raise NotImplementedError(
                "Unsupported PowerCenter "
                f"function: {function_name}"
            )

        expression = (
            expression[
                :function_start
            ]
            + translated_function
            + expression[
                closing_parenthesis + 1:
            ]
        )

        index = (
            function_start
            + len(
                translated_function
            )
        )

    return expression


def translate_not_isnull(
    expression: str,
) -> str:
    """
    Normalize:

        NOT column IS NULL

    into:

        column IS NOT NULL

    This pattern appears after ISNULL
    has been translated.
    """

    pattern = re.compile(
        r"\bNOT\s+"
        r"([A-Za-z_][A-Za-z0-9_.]*)"
        r"\s+IS\s+NULL\b",
        flags=re.IGNORECASE,
    )

    return pattern.sub(
        r"\1 IS NOT NULL",
        expression,
    )


def translate_logical_operators(
    expression: str,
) -> str:
    """
    Normalize common PowerCenter logical
    operators for SQL.

    PowerCenter uses operators such as:

        AND
        OR
        NOT

    which are already SQL compatible.

    The function exists as a dedicated extension
    point for future operator conversions.
    """

    return expression


def translate_powercenter_expression(
    expression: str,
) -> str:
    """
    Translate a PowerCenter expression
    into Spark SQL compatible syntax.

    Current support:

        IIF(...)
            -> CASE WHEN ... THEN ... ELSE ... END

        ISNULL(x)
            -> x IS NULL

        NOT ISNULL(x)
            -> x IS NOT NULL

        CONCAT(a, b)
            -> CONCAT(a, b)

        nested IIF
            -> nested CASE expressions

        arithmetic operators
            -> preserved

        AND / OR
            -> preserved

    This function is deterministic and does
    not use an LLM.
    """

    if expression is None:
        raise ValueError(
            "PowerCenter expression cannot be None."
        )

    translated = expression.strip()

    translated = (
        translate_function_calls(
            translated
        )
    )

    translated = (
        translate_not_isnull(
            translated
        )
    )

    translated = (
        translate_logical_operators(
            translated
        )
    )

    return translated