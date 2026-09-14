from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)

from src.transpiler.mapplet_resolver import (
    resolve_mapplet_contract,
)


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)


MAPPING_NAME = (
    "m_CONTROLLI_ANDINT_CONTICORRENTI_ID_01"
)


MAPPLET_INSTANCE_NAME = (
    "mpl_MASTER_CONTROLLI_ABI_GRUPPO"
)


parsed = parse_powercenter_xml(
    XML_PATH
)


mapping = next(
    current_mapping
    for current_mapping
    in parsed.get(
        "mappings",
        [],
    )
    if current_mapping.get(
        "name"
    )
    == MAPPING_NAME
)


contract = resolve_mapplet_contract(
    mapping=mapping,
    mapplets=parsed.get(
        "mapplets",
        [],
    ),
    mapplet_instance_name=(
        MAPPLET_INSTANCE_NAME
    ),
)


print(
    "\nMAPPLET CONTRACT:\n"
)


print(
    "INSTANCE:",
    contract.get(
        "instance_name"
    ),
)


print(
    "MAPPLET:",
    contract.get(
        "mapplet_name"
    ),
)


print(
    "\nPUBLIC INPUT PORTS:"
)


for port in contract.get(
    "input_ports",
    [],
):
    print(
        "   ",
        port,
    )


print(
    "\nPARENT -> PUBLIC INPUT:"
)


for binding in contract.get(
    "input_bindings",
    [],
):
    print(
        "   ",
        binding.get(
            "source_instance"
        ),
        ".",
        binding.get(
            "source_field"
        ),
        " -> ",
        binding.get(
            "mapplet_port"
        ),
        sep="",
    )


print(
    "\nPUBLIC -> INTERNAL:"
)


for binding in contract.get(
    "internal_bindings",
    [],
):
    print(
        "   ",
        binding.get(
            "public_port"
        ),
        " -> ",
        binding.get(
            "internal_instance"
        ),
        ".",
        binding.get(
            "internal_field"
        ),
        " | ",
        binding.get(
            "internal_instance_type"
        ),
        sep="",
    )


print(
    "\nPUBLIC OUTPUT PORTS:"
)


for port in contract.get(
    "output_ports",
    [],
):
    print(
        "   ",
        port,
    )


print(
    "\nPUBLIC OUTPUT -> PARENT:"
)


for binding in contract.get(
    "output_bindings",
    [],
):
    print(
        "   ",
        binding.get(
            "mapplet_port"
        ),
        " -> ",
        binding.get(
            "target_instance"
        ),
        ".",
        binding.get(
            "target_field"
        ),
        sep="",
    )


print(
    "\nVALIDATION:",
    contract.get(
        "validation_status"
    ),
)


print(
    "ISSUES:",
    contract.get(
        "validation_issues"
    ),
)


assert (
    contract[
        "validation_status"
    ]
    == "VALID"
)


assert (
    contract[
        "validation_issues"
    ]
    == []
)


internal_bindings = {
    binding[
        "public_port"
    ]: binding
    for binding
    in contract[
        "internal_bindings"
    ]
}


assert (
    internal_bindings[
        "ABI"
    ][
        "internal_instance"
    ]
    == "TARGET"
)


assert (
    internal_bindings[
        "ABI"
    ][
        "internal_field"
    ]
    == "ABI"
)


assert (
    internal_bindings[
        "ABI_ANAG"
    ][
        "internal_instance"
    ]
    == "ANAGRAFICA_BANCHE"
)


assert (
    internal_bindings[
        "ABI_ANAG"
    ][
        "internal_field"
    ]
    == "ABI_ANAG"
)


assert (
    internal_bindings[
        "GRUPPO_ANAG"
    ][
        "internal_instance"
    ]
    == "ANAGRAFICA_BANCHE"
)


assert (
    internal_bindings[
        "GRUPPO_ANAG"
    ][
        "internal_field"
    ]
    == "GRUPPO_ANAG"
)


assert (
    internal_bindings[
        "ABI1"
    ][
        "internal_instance"
    ]
    == "OUTPUT"
)


assert (
    internal_bindings[
        "ABI1"
    ][
        "internal_field"
    ]
    == "ABI"
)


assert (
    internal_bindings[
        "VALORE"
    ][
        "internal_instance"
    ]
    == "OUTPUT"
)


assert (
    internal_bindings[
        "VALORE"
    ][
        "internal_field"
    ]
    == "VALORE"
)


print(
    "\nMAPPLET INTERNAL RESOLUTION TEST PASSED"
)