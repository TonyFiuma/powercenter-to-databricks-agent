from typing import Any

from src.transpiler.mapplet_binding import (
    build_mapplet_input_sql_bindings,
)

from src.transpiler.mapplet_resolver import (
    resolve_mapplet_contract,
)

from src.transpiler.transformations.base import (
    TransformationTranslator,
)


def build_mapplet_output_sql(
    *,
    internal_sql: str,
    mapplet_contract: dict[str, Any],
) -> str:
    """
    Project the internal mapplet output fields
    to the public mapplet output ports.

    Example:

        internal OUTPUT.ABI
            ->
        public ABI1
    """

    output_bindings = []

    for binding in mapplet_contract.get(
        "internal_bindings",
        [],
    ):
        port_type = (
            binding.get(
                "port_type"
            )
            or ""
        ).upper()

        if port_type != "OUTPUT":
            continue

        output_bindings.append(
            binding
        )

    if not output_bindings:
        raise ValueError(
            "Mapplet contract does not contain "
            "output bindings."
        )

    projections = []

    for binding in output_bindings:
        internal_field = binding.get(
            "internal_field"
        )

        public_port = binding.get(
            "public_port"
        )

        if not (
            internal_field
            and public_port
        ):
            raise ValueError(
                "Incomplete mapplet output "
                "binding."
            )

        projections.append(
            "    "
            f"src.{internal_field} "
            f"AS {public_port}"
        )

    projection_sql = ",\n".join(
        projections
    )

    indented_internal_sql = "\n".join(
        "    " + line
        for line
        in internal_sql.splitlines()
    )

    return (
        "SELECT\n"
        f"{projection_sql}\n"
        "FROM (\n"
        f"{indented_internal_sql}\n"
        ") src"
    )


def find_internal_output_node(
    mapplet_contract: dict[str, Any],
) -> str:
    """
    Find the internal Output Transformation
    exposed by the mapplet public interface.

    MVP limitation:
    exactly one internal output transformation
    is currently supported.
    """

    output_nodes = set()

    for binding in mapplet_contract.get(
        "internal_bindings",
        [],
    ):
        port_type = (
            binding.get(
                "port_type"
            )
            or ""
        ).upper()

        if port_type != "OUTPUT":
            continue

        internal_instance = binding.get(
            "internal_instance"
        )

        if internal_instance:
            output_nodes.add(
                internal_instance
            )

    if not output_nodes:
        raise ValueError(
            "No internal mapplet output "
            "transformation found."
        )

    if len(output_nodes) != 1:
        raise NotImplementedError(
            "Mapplets with multiple internal "
            "output transformations are not "
            "supported yet."
        )

    return next(
        iter(output_nodes)
    )


class MappletTransformationTranslator(
    TransformationTranslator
):
    """
    Translator for PowerCenter MAPPLET instances.

    The translator:

    1. resolves the mapplet contract;
    2. binds parent SQL to internal input
       transformations;
    3. transpiles the internal mapplet DAG;
    4. maps internal output fields back to
       public mapplet ports.
    """

    def __init__(
        self,
        mapplets: list[dict[str, Any]],
    ) -> None:
        self._mapplets = mapplets

    @property
    def transformation_type(
        self,
    ) -> str:
        return "MAPPLET"

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
        Translate one mapplet instance.
        """

        if not self._mapplets:
            raise ValueError(
                "No mapplet definitions "
                "available."
            )

        contract = resolve_mapplet_contract(
            mapping,
            self._mapplets,
            node_name,
        )

        validation_status = (
            contract.get(
                "validation_status"
            )
        )

        if validation_status != "VALID":
            raise ValueError(
                "Mapplet contract for "
                f"'{node_name}' "
                "is not valid."
            )

        mapplet = contract.get(
            "mapplet"
        )

        if not mapplet:
            raise ValueError(
                "Resolved mapplet contract "
                "does not contain the mapplet "
                "definition."
            )

        input_sql_bindings = (
            build_mapplet_input_sql_bindings(
                mapplet_contract=contract,
                sql_by_node=sql_by_node,
            )
        )

        internal_output_node = (
            find_internal_output_node(
                contract
            )
        )

        # Local import avoids a module-level
        # circular dependency:
        #
        # graph_transpiler
        #   -> default_registry
        #   -> mapplet_translator
        #   -> graph_transpiler
        from src.transpiler.graph_transpiler import (
            transpile_data_flow_to_sql,
        )

        internal_sql = (
            transpile_data_flow_to_sql(
                mapping=mapplet,
                target_node=(
                    internal_output_node
                ),
                mapplets=self._mapplets,
                initial_sql_by_node=(
                    input_sql_bindings
                ),
            )
        )

        return build_mapplet_output_sql(
            internal_sql=internal_sql,
            mapplet_contract=contract,
        )