from typing import Any


def parse_task_instances(
    workflow,
) -> list[dict[str, Any]]:
    """
    Parse PowerCenter TASKINSTANCE elements.

    A task instance represents a node
    in the workflow execution graph.
    """

    task_instances = []

    for task_instance in workflow.findall(
        "TASKINSTANCE"
    ):
        task_instances.append(
            {
                "name": task_instance.get(
                    "NAME"
                ),
                "task_name": task_instance.get(
                    "TASKNAME"
                ),
                "task_type": task_instance.get(
                    "TASKTYPE"
                ),
                "is_enabled": task_instance.get(
                    "ISENABLED"
                ),
                "fail_parent_if_instance_fails": (
                    task_instance.get(
                        "FAIL_PARENT_IF_INSTANCE_FAILS"
                    )
                ),
                "fail_parent_if_instance_did_not_run": (
                    task_instance.get(
                        "FAIL_PARENT_IF_INSTANCE_DID_NOT_RUN"
                    )
                ),
                "treat_input_link_as_and": (
                    task_instance.get(
                        "TREAT_INPUTLINK_AS_AND"
                    )
                ),
            }
        )

    return task_instances


def parse_task_definitions(
    workflow,
) -> list[dict[str, Any]]:
    """
    Parse PowerCenter TASK definitions.

    TASK elements contain the executable
    semantics of workflow tasks such as
    Assignment tasks.
    """

    tasks = []

    for task in workflow.findall(
        "TASK"
    ):
        task_data = {
            "name": task.get(
                "NAME"
            ),
            "type": task.get(
                "TYPE"
            ),
            "description": task.get(
                "DESCRIPTION"
            ),
            "reusable": task.get(
                "REUSABLE"
            ),
            "version_number": task.get(
                "VERSIONNUMBER"
            ),
            "attributes": {},
            "value_pairs": [],
        }

        for attribute in task.findall(
            "ATTRIBUTE"
        ):
            attribute_name = (
                attribute.get(
                    "NAME"
                )
            )

            if attribute_name:
                task_data[
                    "attributes"
                ][
                    attribute_name
                ] = attribute.get(
                    "VALUE"
                )

        for value_pair in task.findall(
            "VALUEPAIR"
        ):
            task_data[
                "value_pairs"
            ].append(
                {
                    "name": value_pair.get(
                        "NAME"
                    ),
                    "value": value_pair.get(
                        "VALUE"
                    ),
                    "execution_order": (
                        value_pair.get(
                            "EXECORDER"
                        )
                    ),
                    "reverse_assignment": (
                        value_pair.get(
                            "REVERSEASSIGNMENT"
                        )
                    ),
                }
            )

        tasks.append(
            task_data
        )

    return tasks


def parse_workflow_links(
    workflow,
) -> list[dict[str, Any]]:
    """
    Parse PowerCenter WORKFLOWLINK elements.

    Workflow links represent dependencies
    between workflow task instances.
    """

    links = []

    for link in workflow.findall(
        "WORKFLOWLINK"
    ):
        links.append(
            {
                "from_task": link.get(
                    "FROMTASK"
                ),
                "to_task": link.get(
                    "TOTASK"
                ),
                "condition": link.get(
                    "CONDITION"
                ),
            }
        )

    return links


def parse_session_components(
    session,
) -> list[dict[str, Any]]:
    """
    Parse SESSIONCOMPONENT elements.

    Session components may contain PowerCenter
    variable assignments such as:

        $$m_DT_LOAD = $$wf_DT_LOAD

        $$m_DT_RIFERIMENTO = $$DT_RIFERIMENTO
    """

    components = []

    for component in session.findall(
        "SESSIONCOMPONENT"
    ):
        component_data = {
            "reference_object_name": (
                component.get(
                    "REFOBJECTNAME"
                )
            ),
            "type": component.get(
                "TYPE"
            ),
            "reusable": component.get(
                "REUSABLE"
            ),
            "value_pairs": [],
        }

        for value_pair in component.findall(
            "VALUEPAIR"
        ):
            component_data[
                "value_pairs"
            ].append(
                {
                    "name": value_pair.get(
                        "NAME"
                    ),
                    "value": value_pair.get(
                        "VALUE"
                    ),
                    "execution_order": (
                        value_pair.get(
                            "EXECORDER"
                        )
                    ),
                    "reverse_assignment": (
                        value_pair.get(
                            "REVERSEASSIGNMENT"
                        )
                    ),
                }
            )

        components.append(
            component_data
        )

    return components


def parse_sessions(
    workflow,
) -> list[dict[str, Any]]:
    """
    Parse PowerCenter SESSION elements.

    Sessions connect workflow tasks
    to PowerCenter mappings and may also
    contain runtime variable bindings.
    """

    sessions = []

    for session in workflow.findall(
        "SESSION"
    ):
        sessions.append(
            {
                "name": session.get(
                    "NAME"
                ),
                "mapping_name": session.get(
                    "MAPPINGNAME"
                ),
                "is_valid": session.get(
                    "ISVALID"
                ),
                "sort_order": session.get(
                    "SORTORDER"
                ),
                "components": (
                    parse_session_components(
                        session
                    )
                ),
            }
        )

    return sessions


def parse_workflow_variables(
    workflow,
) -> list[dict[str, Any]]:
    """
    Parse PowerCenter WORKFLOWVARIABLE elements.

    Both system-generated and user-defined
    variables are preserved.
    """

    variables = []

    for variable in workflow.findall(
        "WORKFLOWVARIABLE"
    ):
        variables.append(
            {
                "name": variable.get(
                    "NAME"
                ),
                "datatype": variable.get(
                    "DATATYPE"
                ),
                "default_value": variable.get(
                    "DEFAULTVALUE"
                ),
                "description": variable.get(
                    "DESCRIPTION"
                ),
                "is_null": variable.get(
                    "ISNULL"
                ),
                "is_persistent": variable.get(
                    "ISPERSISTENT"
                ),
                "user_defined": variable.get(
                    "USERDEFINED"
                ),
            }
        )

    return variables


def parse_workflow_attributes(
    workflow,
) -> dict[str, Any]:
    """
    Parse workflow-level ATTRIBUTE elements.
    """

    attributes = {}

    for attribute in workflow.findall(
        "ATTRIBUTE"
    ):
        name = attribute.get(
            "NAME"
        )

        value = attribute.get(
            "VALUE"
        )

        if name:
            attributes[
                name
            ] = value

    return attributes


def parse_workflow(
    workflow,
) -> dict[str, Any]:
    """
    Parse a single PowerCenter WORKFLOW.
    """

    return {
        "name": workflow.get(
            "NAME"
        ),
        "description": workflow.get(
            "DESCRIPTION"
        ),
        "version": workflow.get(
            "VERSION"
        ),
        "tasks": parse_task_instances(
            workflow
        ),
        "task_definitions": (
            parse_task_definitions(
                workflow
            )
        ),
        "links": parse_workflow_links(
            workflow
        ),
        "sessions": parse_sessions(
            workflow
        ),
        "variables": (
            parse_workflow_variables(
                workflow
            )
        ),
        "attributes": (
            parse_workflow_attributes(
                workflow
            )
        ),
    }


def parse_workflows(
    folder,
) -> list[dict[str, Any]]:
    """
    Parse all PowerCenter workflows
    contained in a folder.
    """

    workflows = []

    for workflow in folder.findall(
        "WORKFLOW"
    ):
        workflows.append(
            parse_workflow(
                workflow
            )
        )

    return workflows