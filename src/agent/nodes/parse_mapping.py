import xml.etree.ElementTree as ET
from typing import Any

from src.agent.state import AgentState
from src.parser.powercenter_parser import (
    parse_powercenter_xml,
)
from src.parser.workflow_parser import (
    parse_workflows,
)


def find_mapping(
    powercenter_project: dict[str, Any],
    mapping_name: str,
) -> dict[str, Any]:
    """
    Find a PowerCenter mapping by name.
    """

    for mapping in powercenter_project.get(
        "mappings",
        [],
    ):
        if mapping.get("name") == mapping_name:
            return mapping

    raise ValueError(
        f"PowerCenter mapping not found: "
        f"{mapping_name}"
    )


def find_execution_context(
    workflows: list[dict[str, Any]],
    mapping_name: str,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
]:
    """
    Find the workflow and session executing
    the requested PowerCenter mapping.

    MVP constraint:
    exactly one session must reference the
    requested mapping.
    """

    matches = []

    for workflow in workflows:
        for session in workflow.get(
            "sessions",
            [],
        ):
            if (
                session.get("mapping_name")
                == mapping_name
            ):
                matches.append(
                    (
                        workflow,
                        session,
                    )
                )

    if not matches:
        raise ValueError(
            "No PowerCenter session found "
            "for mapping: "
            f"{mapping_name}"
        )

    if len(matches) > 1:
        raise ValueError(
            "Multiple PowerCenter sessions "
            "reference mapping "
            f"'{mapping_name}'. "
            "Explicit session selection is "
            "required."
        )

    return matches[0]


def parse_mapping_node(
    state: AgentState,
) -> dict[str, Any]:
    """
    Parse the PowerCenter XML and resolve the
    execution context for the requested mapping.

    The node resolves:

        mapping
        mapplets
        workflow
        session

    from the PowerCenter XML document.
    """

    xml_path = state["xml_path"]
    mapping_name = state.get(
        "mapping_name"
    )

    if not mapping_name:
        raise ValueError(
            "mapping_name is required."
        )

    print(
        f"Parsing PowerCenter XML: "
        f"{xml_path}"
    )

    powercenter_project = (
        parse_powercenter_xml(
            xml_path
        )
    )

    mapping = find_mapping(
        powercenter_project=(
            powercenter_project
        ),
        mapping_name=mapping_name,
    )

    root = ET.parse(
        xml_path
    ).getroot()

    folder = root.find(
        ".//FOLDER"
    )

    if folder is None:
        raise ValueError(
            "PowerCenter FOLDER element "
            "not found."
        )

    workflows = parse_workflows(
        folder
    )

    workflow, session = (
        find_execution_context(
            workflows=workflows,
            mapping_name=mapping_name,
        )
    )

    mapplets = powercenter_project.get(
        "mapplets",
        [],
    )

    print(
        "PowerCenter execution context "
        "resolved successfully."
    )

    print(
        f"Mapping: {mapping['name']}"
    )

    print(
        f"Workflow: {workflow['name']}"
    )

    print(
        f"Session: {session['name']}"
    )

    return {
        "powercenter_project": (
            powercenter_project
        ),
        "mapping": mapping,
        "mapplets": mapplets,
        "workflow": workflow,
        "session": session,
    }