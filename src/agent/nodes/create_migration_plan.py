import time

from groq import RateLimitError

from src.agent.state import AgentState

from src.agent.context.mapping_context import (
    build_mapping_context,
    build_single_mapping_input,
)

from src.llm.provider import (
    get_planner_llm,
)

from src.storage.migration_plan_store import (
    load_migration_plans,
    save_migration_plans,
)

from src.transpiler.databricks_runtime_variable import (
    build_databricks_runtime_variables,
)

from src.transpiler.runtime_variable_resolver import (
    resolve_mapping_runtime_variables,
)


MAX_LLM_RETRIES = 3
RETRY_WAIT_SECONDS = 4

# Increment this value whenever the information supplied
# to the planner changes in a migration-relevant way.
PLANNER_CONTEXT_VERSION = "v5"


def invoke_planner_with_retry(
    prompt: str,
):
    """
    Invoke the planner LLM with retry handling for
    temporary Groq token-per-minute rate limits.

    The planner is initialized lazily so deterministic
    migrations do not initialize an LLM unnecessarily.
    """

    llm = get_planner_llm()

    print(
        "Planner prompt characters: "
        f"{len(prompt)}"
    )

    for attempt in range(
        1,
        MAX_LLM_RETRIES + 1,
    ):
        try:
            print(
                f"LLM attempt "
                f"{attempt}/{MAX_LLM_RETRIES}..."
            )

            return llm.invoke(
                prompt
            )

        except RateLimitError:
            print(
                "\nGroq rate limit reached."
            )

            if attempt >= MAX_LLM_RETRIES:
                print(
                    "Maximum planner retries reached."
                )
                raise

            print(
                f"Retrying in "
                f"{RETRY_WAIT_SECONDS} seconds..."
            )

            time.sleep(
                RETRY_WAIT_SECONDS
            )

    raise RuntimeError(
        "Planner LLM call failed unexpectedly."
    )


def build_documentation_context(
    retrieved_docs: list,
) -> str:
    """
    Build a bounded documentation context for the
    planner.

    Documentation is reference material only.
    Parsed and deterministically resolved PowerCenter
    facts remain the source of truth.
    """

    MAX_DOCUMENTS_PER_SOURCE = 3
    MAX_DOCUMENT_CHARS = 2500

    powercenter_docs = []
    databricks_docs = []

    for document in retrieved_docs:
        source = document.metadata.get(
            "source",
            "",
        )

        if source == "databricks":
            databricks_docs.append(
                document
            )
        else:
            powercenter_docs.append(
                document
            )

    def format_document(
        document,
    ) -> str:
        metadata = document.metadata

        product = metadata.get(
            "product",
            "unknown",
        )

        version = metadata.get(
            "version",
            "unknown",
        )

        document_type = metadata.get(
            "document_type",
            "unknown",
        )

        page_number = metadata.get(
            "page_number",
            "unknown",
        )

        source = metadata.get(
            "source",
            "unknown",
        )

        content = (
            document.page_content
            or ""
        )

        content = content[
            :MAX_DOCUMENT_CHARS
        ]

        return (
            "DOCUMENT METADATA\n"
            f"- product: {product}\n"
            f"- version: {version}\n"
            f"- document_type: {document_type}\n"
            f"- page_number: {page_number}\n"
            f"- source: {source}\n\n"
            "DOCUMENT CONTENT\n"
            f"{content}"
        )

    selected_powercenter_docs = (
        powercenter_docs[
            :MAX_DOCUMENTS_PER_SOURCE
        ]
    )

    selected_databricks_docs = (
        databricks_docs[
            :MAX_DOCUMENTS_PER_SOURCE
        ]
    )

    powercenter_context = "\n\n".join(
        format_document(
            document
        )
        for document
        in selected_powercenter_docs
    )

    databricks_context = "\n\n".join(
        format_document(
            document
        )
        for document
        in selected_databricks_docs
    )

    return (
        "=== POWERCENTER DOCUMENTATION ===\n\n"
        f"{powercenter_context}\n\n"
        "=== DATABRICKS DOCUMENTATION ===\n\n"
        f"{databricks_context}"
    )


def build_runtime_context(
    mapping: dict,
    session: dict,
    workflow: dict,
) -> str:
    """
    Build deterministic runtime-variable facts for
    the planner.

    PowerCenter resolution and Databricks translation
    are performed by the deterministic transpiler
    components.

    The LLM must consume these results as facts rather
    than rediscovering variable semantics.
    """

    resolved_variables = (
        resolve_mapping_runtime_variables(
            mapping=mapping,
            session=session,
            workflow=workflow,
        )
    )

    databricks_variables = (
        build_databricks_runtime_variables(
            mapping=mapping,
            session=session,
            workflow=workflow,
        )
    )

    resolved_by_name = {
        variable.source_name: variable
        for variable in resolved_variables
    }

    databricks_by_name = {
        variable.source_name: variable
        for variable in databricks_variables
    }

    variable_names = sorted(
        set(resolved_by_name)
        | set(databricks_by_name)
    )

    if not variable_names:
        return (
            "No runtime variables identified "
            "deterministically."
        )

    lines = []

    for variable_name in variable_names:
        resolved = resolved_by_name.get(
            variable_name
        )

        databricks = databricks_by_name.get(
            variable_name
        )

        lines.append(
            f"- source_name: {variable_name}"
        )

        if resolved:
            lines.append(
                "  resolution_type: "
                f"{resolved.resolution_type}"
            )

            lines.append(
                "  resolved_powercenter_value: "
                f"{resolved.resolved_value}"
            )

        if databricks:
            lines.append(
                "  databricks_variable_type: "
                f"{databricks.variable_type}"
            )

            lines.append(
                "  databricks_value: "
                f"{databricks.value}"
            )

        lines.append("")

    return "\n".join(
        lines
    ).strip()


def build_prompt(
    mapping_context: str,
    runtime_context: str,
    documentation_context: str,
) -> str:
    """
    Build the migration-planning prompt for one
    PowerCenter mapping.
    """

    return f"""
You are a senior Data Engineer specialized in:

- Informatica PowerCenter
- Databricks
- Apache Spark
- PySpark
- ETL modernization

Your task is to analyze ONE Informatica PowerCenter mapping
and create a migration plan for Databricks.

Your priority is factual accuracy.

The parsed PowerCenter mapping and deterministic runtime facts
are the source of truth.


==================================================
EVIDENCE RULES
==================================================

For every statement in the migration plan, distinguish between:

1. FACT
   Information explicitly present in the parsed mapping or
   deterministic runtime facts.

2. MIGRATION REQUIREMENT
   A requirement that follows directly from a FACT and must
   be preserved during migration.

3. UNRESOLVED
   Information required for the migration that cannot be
   determined with sufficient certainty.

4. HUMAN_REVIEW_SUGGESTION
   A possible migration approach that may help a human engineer
   resolve an UNRESOLVED item.

A HUMAN_REVIEW_SUGGESTION is NOT an approved implementation.

It must:

- remain clearly separated from FACT and MIGRATION REQUIREMENT
- never be presented as certain
- explain why human review is required
- reference only relevant documentation actually present in the
  documentation context
- include a confidence level: LOW or MEDIUM
- never silently convert an UNRESOLVED item into an implementation
  decision

The underlying item must remain UNRESOLVED until reviewed by a human.


==================================================
DETERMINISTIC FACT RULE
==================================================

The DETERMINISTIC RUNTIME FACTS section is produced by
deterministic code before the LLM is invoked.

You MUST treat those values as FACT.

Do NOT mark a runtime variable as UNRESOLVED when its
resolution_type is "computed" or "external".

When a deterministic Databricks value is provided, use that
value as the migration requirement.

Examples:

- resolution_type: external
  databricks_variable_type: parameter
  databricks_value: DT_RIFERIMENTO

  This means the PowerCenter variable is resolved as an
  external runtime parameter named DT_RIFERIMENTO.

- resolution_type: computed
  databricks_variable_type: expression
  databricks_value: current_timestamp()

  This means the deterministic Databricks equivalent is
  current_timestamp().

Only variables explicitly classified as "unresolved" may be
reported as unresolved runtime variables.


==================================================
STRICT ANTI-HALLUCINATION RULES
==================================================

Do NOT invent:

- filters
- joins
- aggregations
- lookups
- sorts
- SQL overrides
- variables
- expressions
- source properties
- target properties
- file paths
- delimiters
- header settings
- write modes
- partitioning
- table names
- schemas
- catalogs
- JDBC URLs
- credentials
- notebook parameters
- widgets
- accumulators
- collect operations
- first/last row logic
- ordering assumptions
- workflow behavior
- session behavior
- pre-session SQL
- post-session SQL
- downstream usage
- upstream usage

Do NOT propose an implementation merely because it would be
a common Databricks solution.

If the available evidence does not contain enough information,
write exactly:

Not identified in available migration evidence.


==================================================
POWERCENTER INSTANCE RULE
==================================================

Source and target INSTANCE names may differ from their
underlying DEFINITION names.

Do NOT report a mismatch when the parsed mapping explicitly
links the instance to its definition.


==================================================
SOURCE QUALIFIER RULES
==================================================

For a Source Qualifier:

- report a filter only if explicitly present
- report a join only if explicitly present
- report a SQL override only if explicitly present
- report DISTINCT only if explicitly present

Do NOT infer additional Source Qualifier behavior.


==================================================
EXPRESSION TRANSFORMATION RULES
==================================================

For an Expression transformation:

- report only expressions explicitly present
- INPUT/OUTPUT ports alone are not business logic
- do not invent calculations
- do not invent column derivations
- do not infer downstream usage from port names


==================================================
RUNTIME VARIABLE RULES
==================================================

Runtime-variable semantics may be supplied in the
DETERMINISTIC RUNTIME FACTS section.

Those facts take precedence over any uncertainty inferred
from the mapping text alone.

Do NOT claim that a variable lifecycle or runtime origin is
unknown when the deterministic section explicitly resolves it.

Do NOT replace deterministic parameter or expression values
with speculative widgets, job parameters, Python variables,
Spark configuration, Delta tables, or external storage.


==================================================
TARGET INSTANCE SQL RULES
==================================================

Target INSTANCE metadata may contain TABLEATTRIBUTE values
such as:

- Pre SQL
- Post SQL

When populated, these values are FACTS from the PowerCenter
mapping.

You MUST:

1. report the exact behavior represented by the populated
   Target instance SQL;

2. identify that its semantics must be preserved during
   migration;

3. never state that Pre SQL or Post SQL is absent when a
   populated instance_table_attributes value is present;

4. keep the Databricks implementation UNRESOLVED if the
   available evidence does not determine safely where or how
   the SQL should execute.

Do not silently discard Target Pre SQL or Post SQL.


==================================================
TARGET RULES
==================================================

If the parsed mapping identifies the target as Flat File,
you may state that a file-based Databricks output is required.

Do NOT invent:

- path
- DBFS location
- cloud storage location
- delimiter
- header
- write mode
- partitioning
- compression
- file naming behavior

For database targets, do not invent catalog, schema,
connection, or write semantics that are not present in the
available evidence.


==================================================
DATA FLOW RULES
==================================================

Represent only connections explicitly present in DATA FLOW.

Do NOT infer additional upstream or downstream components.

If port-level usage cannot be determined, state:

Not identified in available migration evidence.


==================================================
MIGRATION RISK RULES
==================================================

Only list a migration risk when supported by available
migration evidence.

Do not create speculative risks.

Missing configuration may be listed as UNRESOLVED only when
that information is required for the migration.


==================================================
DOCUMENTATION USAGE
==================================================

Documentation is generic reference material.

PowerCenter documentation explains what a transformation CAN
do. It does not prove that a capability is used in this mapping.

Databricks documentation describes available target mechanisms.
It does not justify introducing implementation logic that is
not required by the mapping.

Parsed mapping evidence and deterministic facts always take
precedence over documentation.


==================================================
PYSPARK RULE
==================================================

Do NOT generate complete PySpark source code yet.

You may identify a conceptual Databricks/PySpark equivalent
only when it follows directly from the available migration
evidence.


==================================================
PARSED POWERCENTER MAPPING
==================================================

{mapping_context}


==================================================
DETERMINISTIC RUNTIME FACTS
==================================================

{runtime_context}


==================================================
RELEVANT MIGRATION DOCUMENTATION
==================================================

{documentation_context}


==================================================
REQUIRED OUTPUT FORMAT
==================================================

==================================================
MAPPING
==================================================

Mapping name:

Purpose:

If purpose is not explicitly identifiable:
Not identified in available migration evidence.


==================================================
SOURCE PLAN
==================================================

For each source:

Source instance:
Source definition:
Source type:
Database / system:

Facts:
- ...

Migration requirement:
- ...

Databricks equivalent:

Migration action:

Unresolved information:
- ...


==================================================
TRANSFORMATION PLAN
==================================================

For each transformation:

Transformation:
PowerCenter type:

Facts:
- ...

Relevant PowerCenter logic:
- ...

Migration requirement:
- ...

Databricks / PySpark equivalent:

Migration action:

Unresolved information:
- ...

Human review suggestion:
- Include this section only when a documented, reasonable
  migration approach exists but human validation is still
  required.
- Otherwise omit it.


==================================================
TARGET PLAN
==================================================

For each target:

Target instance:
Target definition:
Target type:

Facts:
- ...

Migration requirement:
- ...

Databricks equivalent:

Migration action:

Unresolved information:
- ...


==================================================
DATA FLOW
==================================================

Represent only connections explicitly present in
the parsed mapping.


==================================================
MIGRATION RISKS / UNRESOLVED
==================================================

List only:

- unresolved information explicitly supported by evidence
- migration requirements that cannot yet be implemented safely
- HUMAN_REVIEW_SUGGESTION items pending human approval

Do not include speculative risks.


==================================================
HUMAN REVIEW SUGGESTIONS
==================================================

When an implementation cannot be determined safely, keep the
implementation classified as UNRESOLVED.

When documentation provides enough information for a reasonable
possible approach, you MAY add:

Human review suggestion:
[HUMAN_REVIEW_SUGGESTION]

Possible approach:
<possible Databricks approach>

Why human review is required:
<missing information>

Documentation to review:
- Product: <metadata value if available>
- Version: <metadata value if available>
- Document type: <metadata value if available>
- Page: <metadata value if available>
- Source: <metadata value if available>

Confidence:
LOW or MEDIUM

Suggested PySpark / Python:
<optional conceptual code>

Suggested code is NOT approved executable migration code.


==================================================
FINAL SELF-CHECK
==================================================

Before producing the answer verify:

- Did I contradict a deterministic runtime fact?
- Did I mark a resolved runtime variable as unresolved?
- Did I ignore populated Target Pre SQL or Post SQL?
- Did I invent a filter?
- Did I invent a join?
- Did I invent an SQL override?
- Did I invent a file path?
- Did I invent write mode?
- Did I invent variable semantics?
- Did I infer behavior not present in the evidence?
- Did I present a HUMAN_REVIEW_SUGGESTION as confirmed?

If YES, correct the migration plan before returning it.
"""


def create_migration_plan_node(
    state: AgentState,
) -> dict:
    """
    Create a migration plan for the selected
    PowerCenter mapping.

    The planner receives:

    - parsed mapping facts;
    - Target instance TABLEATTRIBUTE metadata;
    - deterministic runtime-variable facts;
    - retrieved PowerCenter/Databricks documentation.

    Cached plans are versioned so changes to planner
    evidence do not silently reuse stale plans.
    """

    print(
        "\nCreating migration plans..."
    )

    mapping = state["mapping"]
    xml_path = state["xml_path"]
    powercenter_project = (
        state["powercenter_project"]
    )

    session = state["session"]
    workflow = state["workflow"]

    retrieved_docs = state.get(
        "retrieved_docs",
        [],
    )

    documentation_context = (
        build_documentation_context(
            retrieved_docs
        )
    )

    pc_mappings = [
        mapping
    ]

    print(
        f"Mappings to analyze: "
        f"{len(pc_mappings)}"
    )

    migration_plans = load_migration_plans(
        source_xml=xml_path,
    )

    for index, pc_mapping in enumerate(
        pc_mappings,
        start=1,
    ):
        mapping_name = pc_mapping.get(
            "name",
            "UNKNOWN_MAPPING",
        )

        print("")
        print(
            f"[{index}/{len(pc_mappings)}] "
            f"Creating plan for: "
            f"{mapping_name}"
        )

        # ---------------------------------------------
        # VERSIONED CACHE KEY
        # ---------------------------------------------

        cache_key = (
            f"{mapping_name}"
            f"::{PLANNER_CONTEXT_VERSION}"
        )

        cached_plan = migration_plans.get(
            cache_key
        )

        if (
            cached_plan
            and cached_plan.strip()
        ):
            print(
                "Migration plan found in cache."
            )

            print(
                f"Planner context version: "
                f"{PLANNER_CONTEXT_VERSION}"
            )

            print(
                f"Cached plan characters: "
                f"{len(cached_plan)}"
            )

            continue

        # ---------------------------------------------
        # MAPPING CONTEXT
        # ---------------------------------------------

        single_mapping = (
            build_single_mapping_input(
                full_mapping=powercenter_project,
                pc_mapping=pc_mapping,
            )
        )

        mapping_context = (
            build_mapping_context(
                single_mapping
            )
        )

        print(
            "Mapping context characters: "
            f"{len(mapping_context)}"
        )

        # ---------------------------------------------
        # DETERMINISTIC RUNTIME CONTEXT
        # ---------------------------------------------

        runtime_context = (
            build_runtime_context(
                mapping=pc_mapping,
                session=session,
                workflow=workflow,
            )
        )

        print(
            "Runtime context characters: "
            f"{len(runtime_context)}"
        )

        print(
            "Planner context version: "
            f"{PLANNER_CONTEXT_VERSION}"
        )

        # ---------------------------------------------
        # PROMPT
        # ---------------------------------------------

        prompt = build_prompt(
            mapping_context=mapping_context,
            runtime_context=runtime_context,
            documentation_context=(
                documentation_context
            ),
        )

        # ---------------------------------------------
        # LLM
        # ---------------------------------------------

        try:
            print(
                "Sending mapping to LLM..."
            )

            response = (
                invoke_planner_with_retry(
                    prompt=prompt,
                )
            )

            print(
                "LLM response received."
            )

            migration_plan = (
                response.content
            )

            if not isinstance(
                migration_plan,
                str,
            ):
                migration_plan = str(
                    migration_plan
                )

            migration_plan = (
                migration_plan.strip()
            )

            if not migration_plan:
                raise ValueError(
                    "LLM returned an empty "
                    "migration plan for mapping: "
                    f"{mapping_name}"
                )

            migration_plans[
                cache_key
            ] = migration_plan

            save_migration_plans(
                source_xml=xml_path,
                migration_plans=migration_plans,
            )

        except Exception as exc:
            print(
                f"\nLLM CALL FAILED "
                f"for mapping: {mapping_name}"
            )

            print(
                f"Error type: "
                f"{type(exc).__name__}"
            )

            print(
                f"Error: {exc}"
            )

            raise

    # ---------------------------------------------
    # VALIDATE CACHE / GENERATED PLANS
    # ---------------------------------------------

    missing_mappings = []

    for pc_mapping in pc_mappings:
        mapping_name = pc_mapping.get(
            "name",
            "UNKNOWN_MAPPING",
        )

        cache_key = (
            f"{mapping_name}"
            f"::{PLANNER_CONTEXT_VERSION}"
        )

        plan = migration_plans.get(
            cache_key
        )

        if (
            not plan
            or not plan.strip()
        ):
            missing_mappings.append(
                mapping_name
            )

    if missing_mappings:
        raise ValueError(
            "Migration plans missing for mappings: "
            f"{missing_mappings}"
        )

    # ---------------------------------------------
    # BUILD COMBINED PLAN
    # ---------------------------------------------

    ordered_plans = []

    output_migration_plans = {}

    for pc_mapping in pc_mappings:
        mapping_name = pc_mapping.get(
            "name",
            "UNKNOWN_MAPPING",
        )

        cache_key = (
            f"{mapping_name}"
            f"::{PLANNER_CONTEXT_VERSION}"
        )

        plan = migration_plans[
            cache_key
        ]

        ordered_plans.append(
            plan
        )

        # Agent state keeps the normal mapping name as
        # its public key. Cache implementation details
        # do not leak into downstream nodes.
        output_migration_plans[
            mapping_name
        ] = plan

    combined_plan = "\n\n".join(
        ordered_plans
    )

    # ---------------------------------------------
    # DEBUG
    # ---------------------------------------------

    print(
        "\nMigration plans available:"
    )

    for mapping_name, plan in (
        output_migration_plans.items()
    ):
        print(
            f"- {mapping_name}: "
            f"{len(plan)} characters"
        )

    return {
        "migration_plan": combined_plan,
        "migration_plans": (
            output_migration_plans
        ),
    }