from src.transformations.models import TransformationSpec


TRANSFORMATION_REGISTRY: dict[str, TransformationSpec] = {

    "Expression": TransformationSpec(
        powercenter_type="Expression",
        supported=True,
        pyspark_operations=[
            "withColumn",
            "select",
        ],
        retrieval_tags=[
            "expression",
            "expression transformation",
        ],
    ),

    "Filter": TransformationSpec(
        powercenter_type="Filter",
        supported=True,
        pyspark_operations=[
            "filter",
            "where",
        ],
        retrieval_tags=[
            "filter",
            "filter transformation",
        ],
    ),

    "Aggregator": TransformationSpec(
        powercenter_type="Aggregator",
        supported=True,
        pyspark_operations=[
            "groupBy",
            "agg",
        ],
        retrieval_tags=[
            "aggregator",
            "aggregation",
        ],
        requires_partitioning=True,
    ),

    "Lookup": TransformationSpec(
        powercenter_type="Lookup",
        supported=True,
        pyspark_operations=[
            "join",
        ],
        retrieval_tags=[
            "lookup",
            "lookup transformation",
        ],
    ),
}

def get_transformation_spec(
    transformation_type: str,
) -> TransformationSpec | None:
    """
    Return the specification for a PowerCenter transformation.
    """

    return TRANSFORMATION_REGISTRY.get(transformation_type)

def is_supported_transformation(
    transformation_type: str,
) -> bool:
    """
    Check whether a PowerCenter transformation is supported.
    """

    spec = get_transformation_spec(transformation_type)

    return spec is not None and spec.supported