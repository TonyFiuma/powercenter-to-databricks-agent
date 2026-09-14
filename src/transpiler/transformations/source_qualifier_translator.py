from typing import Any

from src.transpiler.transformations.base import (
    TransformationTranslator,
)


def find_source_definition(
    mapping: dict[str, Any],
    source_name: str,
) -> dict[str, Any]:
    """
    Find a PowerCenter source definition by name.
    """

    for source in mapping.get(
        "sources",
        [],
    ):
        if source.get("name") == source_name:
            return source

    raise ValueError(
        f"Source definition '{source_name}' not found."
    )


def build_source_table_name(
    source: dict[str, Any],
) -> str:
    """
    Build the physical source table name.

    Example:

        owner = DWHEVO
        name = RSK_DM_ANDINT_CONTICORRENTI_SYN

    becomes:

        DWHEVO.RSK_DM_ANDINT_CONTICORRENTI_SYN
    """

    source_name = source.get("name")
    owner_name = source.get("owner_name")

    if not source_name:
        raise ValueError(
            "Source definition without name."
        )

    if owner_name:
        return (
            f"{owner_name}.{source_name}"
        )

    return source_name


def build_source_qualifier_sql(
    source: dict[str, Any],
    transformation: dict[str, Any],
) -> str:
    """
    Translate a PowerCenter Source Qualifier
    into SQL.

    Currently supported:

    - regular source selection;
    - output ports;
    - Select Distinct;
    - Source Filter.

    Unsupported Source Qualifier features raise
    NotImplementedError rather than being silently
    ignored.
    """

    table_attributes = (
        transformation.get(
            "table_attributes",
            {},
        )
    )

    sql_query = (
        table_attributes.get(
            "Sql Query"
        )
        or ""
    ).strip()

    user_defined_join = (
        table_attributes.get(
            "User Defined Join"
        )
        or ""
    ).strip()

    pre_sql = (
        table_attributes.get(
            "Pre SQL"
        )
        or ""
    ).strip()

    post_sql = (
        table_attributes.get(
            "Post SQL"
        )
        or ""
    ).strip()

    if sql_query:
        raise NotImplementedError(
            "Source Qualifier custom SQL query "
            "is not supported yet."
        )

    if user_defined_join:
        raise NotImplementedError(
            "Source Qualifier User Defined Join "
            "is not supported yet."
        )

    if pre_sql:
        raise NotImplementedError(
            "Source Qualifier Pre SQL "
            "is not supported yet."
        )

    if post_sql:
        raise NotImplementedError(
            "Source Qualifier Post SQL "
            "is not supported yet."
        )

    output_fields = []

    for field in transformation.get(
        "fields",
        [],
    ):
        field_name = field.get(
            "name"
        )

        port_type = (
            field.get(
                "port_type"
            )
            or ""
        ).upper()

        if not field_name:
            continue

        if "OUTPUT" not in port_type:
            continue

        output_fields.append(
            field_name
        )

    if not output_fields:
        raise ValueError(
            "Source Qualifier "
            f"'{transformation.get('name')}' "
            "does not contain output fields."
        )

    select_distinct = (
        table_attributes.get(
            "Select Distinct"
        )
        or "NO"
    ).upper() == "YES"

    source_filter = (
        table_attributes.get(
            "Source Filter"
        )
        or ""
    ).strip()

    source_table = (
        build_source_table_name(
            source
        )
    )

    distinct_keyword = (
        " DISTINCT"
        if select_distinct
        else ""
    )

    select_clause = ",\n    ".join(
        output_fields
    )

    sql = (
        f"SELECT{distinct_keyword}\n"
        f"    {select_clause}\n"
        f"FROM {source_table}"
    )

    if source_filter:
        sql += (
            "\nWHERE "
            f"{source_filter}"
        )

    return sql


class SourceQualifierTransformationTranslator(
    TransformationTranslator
):
    """
    SQL translator for PowerCenter
    Source Qualifier transformations.
    """

    @property
    def transformation_type(
        self,
    ) -> str:
        return "Source Qualifier"

    def translate(
        self,
        *,
        mapping: dict[str, Any],
        transformation: dict[str, Any],
        node_name: str,
        predecessors: list[str],
        sql_by_node: dict[str, str],
    ) -> str:
        """
        Translate one Source Qualifier node.

        The predecessor must be a PowerCenter
        SOURCE instance.
        """

        if len(predecessors) != 1:
            raise NotImplementedError(
                "Source Qualifier "
                f"'{node_name}' requires exactly "
                "one source predecessor."
            )

        source_name = predecessors[0]

        source = find_source_definition(
            mapping=mapping,
            source_name=source_name,
        )

        return build_source_qualifier_sql(
            source=source,
            transformation=transformation,
        )