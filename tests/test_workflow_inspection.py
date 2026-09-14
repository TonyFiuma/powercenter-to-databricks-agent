import xml.etree.ElementTree as ET


XML_PATH = (
    "data/input/"
    "wf_CONTROLLI_ANDAMENTALE_INTERNO.XML"
)


tree = ET.parse(
    XML_PATH
)

root = tree.getroot()


repository = root.find(
    "REPOSITORY"
)

if repository is None:
    raise ValueError(
        "REPOSITORY not found."
    )


folder = repository.find(
    "FOLDER"
)

if folder is None:
    raise ValueError(
        "FOLDER not found."
    )


print(
    "\nWORKFLOWS FOUND:\n"
)


for workflow in folder.findall(
    "WORKFLOW"
):
    workflow_name = workflow.get(
        "NAME"
    )

    print(
        "=" * 80
    )

    print(
        "WORKFLOW:",
        workflow_name,
    )

    print(
        "DESCRIPTION:",
        workflow.get(
            "DESCRIPTION"
        ),
    )

    print(
        "VERSION:",
        workflow.get(
            "VERSION"
        ),
    )


    # ========================================================
    # TASK INSTANCES
    # ========================================================

    print(
        "\nTASK INSTANCES:\n"
    )

    for task_instance in workflow.findall(
        "TASKINSTANCE"
    ):
        print(
            "NAME:",
            task_instance.get(
                "NAME"
            ),
        )

        print(
            "TASKNAME:",
            task_instance.get(
                "TASKNAME"
            ),
        )

        print(
            "TASKTYPE:",
            task_instance.get(
                "TASKTYPE"
            ),
        )

        print(
            "ISENABLED:",
            task_instance.get(
                "ISENABLED"
            ),
        )

        print(
            "-" * 40
        )


    # ========================================================
    # WORKFLOW LINKS
    # ========================================================

    print(
        "\nWORKFLOW LINKS:\n"
    )

    for link in workflow.findall(
        "WORKFLOWLINK"
    ):
        print(
            link.get(
                "FROMTASK"
            ),
            "->",
            link.get(
                "TOTASK"
            ),
        )

        print(
            "CONDITION:",
            link.get(
                "CONDITION"
            ),
        )

        print(
            "-" * 40
        )


    # ========================================================
    # SESSIONS
    # ========================================================

    print(
        "\nSESSIONS:\n"
    )

    for session in workflow.findall(
        "SESSION"
    ):
        print(
            "NAME:",
            session.get(
                "NAME"
            ),
        )

        print(
            "MAPPINGNAME:",
            session.get(
                "MAPPINGNAME"
            ),
        )

        print(
            "ISVALID:",
            session.get(
                "ISVALID"
            ),
        )

        print(
            "SORTORDER:",
            session.get(
                "SORTORDER"
            ),
        )

        print(
            "-" * 40
        )


    # ========================================================
    # OTHER TASK TYPES
    # ========================================================

    print(
        "\nOTHER WORKFLOW CHILD ELEMENTS:\n"
    )

    known_tags = {
        "TASKINSTANCE",
        "WORKFLOWLINK",
        "SESSION",
    }

    for child in workflow:
        if child.tag not in known_tags:
            print(
                child.tag,
                child.attrib,
            )

    print(
        "=" * 80
    )