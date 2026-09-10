def extract_transformation_types(
    mapping: dict,
) -> list[str]:
    transformation_types = set()

    for pc_mapping in mapping.get(
        "mappings",
        [],
    ):
        for transformation in pc_mapping.get(
            "transformations",
            [],
        ):
            transformation_type = (
                transformation.get("type")
            )

            if transformation_type:
                transformation_types.add(
                    transformation_type
                )

    return sorted(
        transformation_types
    )


def build_powercenter_retrieval_query(
    transformation_type: str,
) -> str:
    return (
        "Informatica PowerCenter "
        f"{transformation_type} "
        "Transformation documentation"
    )


def build_databricks_retrieval_query(
    transformation_type: str,
) -> str:
    transformation_type_lower = (
        transformation_type.lower()
    )

    query_map = {
        "expression": (
            "PySpark DataFrame column expressions "
            "withColumn expr select transformations"
        ),

        "source qualifier": (
            "PySpark DataFrame JDBC database read "
            "query filter data source"
        ),

        "filter": (
            "PySpark DataFrame filter where rows "
            "conditional expressions"
        ),

        "aggregator": (
            "PySpark DataFrame groupBy agg "
            "aggregation functions"
        ),

        "joiner": (
            "PySpark DataFrame join "
            "join conditions join types"
        ),

        "lookup": (
            "PySpark DataFrame lookup join "
            "reference table broadcast join"
        ),

        "router": (
            "PySpark DataFrame conditional filtering "
            "multiple output branches"
        ),

        "sorter": (
            "PySpark DataFrame sort orderBy "
            "ascending descending"
        ),

        "rank": (
            "PySpark DataFrame window functions "
            "rank dense_rank row_number"
        ),
    }

    return query_map.get(
        transformation_type_lower,
        (
            "PySpark DataFrame transformation "
            f"{transformation_type}"
        ),
    )