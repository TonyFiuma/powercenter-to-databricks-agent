from src.transpiler.transformations.expression_translator import (
    ExpressionTransformationTranslator,
)


mapping = {
    "data_flow": [
        {
            "from": {
                "name": "SOURCE",
            },
            "to": {
                "name": "EXP_TEST",
            },
            "fields": [
                {
                    "from_field": "VALUE_IN",
                    "to_field": "VALUE_IN",
                }
            ],
        }
    ]
}


transformation = {
    "name": "EXP_TEST",
    "type": "Expression",
    "fields": [
        {
            "name": "VALUE_IN",
            "port_type": "INPUT",
            "expression": None,
        },
        {
            "name": "VALUE_OUT",
            "port_type": "OUTPUT",
            "expression": (
                "IIF("
                "NOT ISNULL(VALUE_IN),"
                "VALUE_IN,"
                "0"
                ")"
            ),
        },
    ],
}


sql_by_node = {
    "SOURCE": (
        "SELECT VALUE_IN\n"
        "FROM TEST_SOURCE"
    )
}


translator = (
    ExpressionTransformationTranslator()
)


assert (
    translator.transformation_type
    == "Expression"
)


sql = translator.translate(
    mapping=mapping,
    transformation=transformation,
    node_name="EXP_TEST",
    predecessors=[
        "SOURCE",
    ],
    sql_by_node=sql_by_node,
)


print(
    "\nGENERATED SQL:\n"
)


print(
    sql
)


assert (
    "CASE WHEN VALUE_IN IS NOT NULL"
    in sql
)


assert (
    "THEN VALUE_IN ELSE 0 END"
    in sql
)


assert (
    "AS VALUE_OUT"
    in sql
)


assert (
    "src.VALUE_IN AS VALUE_IN"
    in sql
)


print(
    "\nEXPRESSION TRANSFORMATION "
    "TRANSLATOR TEST PASSED"
)