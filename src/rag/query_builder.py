IGNORED_RETRIEVAL_TRANSFORMATION_TYPES = {
    "Input Transformation",
    "Output Transformation",
    "Mapplet",
}


def extract_transformation_types(
    mapping: dict,
    mapplets: list[dict] | None = None,
) -> list[str]:
    """
    Extract migration-relevant transformation types
    from the selected PowerCenter mapping and its
    referenced mapplets.

    The current agent-state contract is:

        state["mapping"]
            -> selected mapping

        state["mapplets"]
            -> parsed PowerCenter mapplets

    Structural mapplet transformations such as
    Input Transformation and Output Transformation
    are excluded from documentation retrieval.
    """

    transformation_types = set()

    def add_transformations(
        transformations: list[dict],
    ) -> None:
        for transformation in transformations:
            transformation_type = (
                transformation.get(
                    "type"
                )
            )

            if not transformation_type:
                continue

            if (
                transformation_type
                in IGNORED_RETRIEVAL_TRANSFORMATION_TYPES
            ):
                continue

            transformation_types.add(
                transformation_type
            )

    # Selected mapping transformations.
    add_transformations(
        mapping.get(
            "transformations",
            [],
        )
    )

    # Determine which mapplets are actually referenced
    # by the selected mapping.
    referenced_mapplet_names = {
        instance.get(
            "transformation_name"
        )
        for instance in mapping.get(
            "instances",
            [],
        )
        if instance.get("type") == "MAPPLET"
        and instance.get(
            "transformation_name"
        )
    }

    # Include transformations only from mapplets used
    # by this mapping.
    for mapplet in mapplets or []:
        mapplet_name = mapplet.get(
            "name"
        )

        if (
            mapplet_name
            not in referenced_mapplet_names
        ):
            continue

        add_transformations(
            mapplet.get(
                "transformations",
                [],
            )
        )

    return sorted(
        transformation_types
    )


def build_powercenter_retrieval_query(
    transformation_type: str,
) -> str:
    """
    Build a PowerCenter documentation retrieval
    query for one transformation type.
    """

    return (
        "Informatica PowerCenter "
        f"{transformation_type} "
        "Transformation documentation"
    )


def build_databricks_retrieval_query(
    transformation_type: str,
) -> str:
    """
    Build a Databricks/PySpark documentation query
    corresponding to a PowerCenter transformation
    type.
    """

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