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


llm = get_planner_llm()

MAX_LLM_RETRIES = 3
RETRY_WAIT_SECONDS = 4


def invoke_planner_with_retry(
    prompt: str,
):
    """
    Invoke the planner LLM with retry handling for
    temporary Groq token-per-minute rate limits.

    Only Groq RateLimitError exceptions are retried.
    All other failures are propagated immediately.
    """

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
    Build a bounded documentation context for the planner.

    Each retrieved document includes both its content and the
    most useful metadata so the planner can reference the
    documentation during HUMAN_REVIEW suggestions.

    To avoid exceeding the planner model token budget, the
    documentation context is limited deterministically by:

    - number of documents per source;
    - maximum number of characters per document.

    The parsed PowerCenter mapping is not truncated here.
    Only retrieved documentation is bounded.
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
        """
        Format one retrieved document while preserving
        useful metadata and limiting its text size.
        """

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
        for document in selected_powercenter_docs
    )

    databricks_context = "\n\n".join(
        format_document(
            document
        )
        for document in selected_databricks_docs
    )

    return (
        "=== POWERCENTER DOCUMENTATION ===\n\n"
        f"{powercenter_context}\n\n"
        "=== DATABRICKS DOCUMENTATION ===\n\n"
        f"{databricks_context}"
    )


def build_prompt(
    mapping_context: str,
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

The parsed PowerCenter mapping is the source of truth.


==================================================
EVIDENCE RULES
==================================================

For every statement in the migration plan, distinguish between:

1. FACT
   Information explicitly present in the parsed mapping.

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

If the parsed mapping does not contain enough information,
write exactly:

Not identified in parsed mapping.


==================================================
POWERCENTER INSTANCE RULE
==================================================

Source and target INSTANCE names may differ from their
underlying DEFINITION names.

Example:

instance:
    MY_SOURCE1

definition:
    MY_SOURCE

This is normal PowerCenter behavior.

Do NOT report a mismatch if the parsed mapping explicitly
links the instance to the definition.


==================================================
SOURCE QUALIFIER RULES
==================================================

For a Source Qualifier:

- report a filter only if explicitly present
- report a join only if explicitly present
- report a SQL override only if explicitly present
- report DISTINCT only if explicitly present

If none of those are present, state:

No filter, join, SQL override, or DISTINCT logic identified
in parsed mapping.

Do NOT infer that the Source Qualifier performs additional logic.


==================================================
EXPRESSION TRANSFORMATION RULES
==================================================

For an Expression transformation:

- report only expressions explicitly present
- INPUT/OUTPUT ports alone are not business logic
- do not invent calculations
- do not invent column derivations
- do not infer downstream usage from port names

If all ports are pass-through and no non-trivial expression
is present, state:

No non-trivial expression logic identified in parsed mapping.


==================================================
SETVARIABLE RULES
==================================================

If a PowerCenter expression contains SETVARIABLE:

Example:

SETVARIABLE($$variable_name, expression)

You MUST:

1. Report the exact PowerCenter expression.

2. Identify the migration requirement:

   The value assigned to the PowerCenter mapping variable
   must be preserved in the Databricks implementation.

3. Mark the final Databricks implementation as unresolved
   unless the parsed mapping explicitly provides enough
   information to determine the variable lifecycle and usage.

4. If the available documentation provides enough evidence for
   a reasonable migration approach, you MAY add a separate
   HUMAN_REVIEW_SUGGESTION.

The HUMAN_REVIEW_SUGGESTION must never be presented as the final
implementation.

Do NOT invent mapping-specific semantics such as:

- how many rows produce the variable value
- which row wins when multiple rows are processed
- how the variable is consumed downstream
- whether the value must persist between runs
- whether it is session-scoped or workflow-scoped
- whether collect(), first(), last(), agg(), broadcast,
  temporary views, widgets, job parameters, Python variables,
  Spark configuration, Delta tables, or external storage are
  semantically equivalent

unless those facts are supported by the parsed mapping or the
provided documentation.

For unresolved SETVARIABLE migration semantics, keep:

Databricks implementation:
Not identified in parsed mapping.

Unresolved information:
The lifecycle and downstream consumption of the PowerCenter
mapping variable must be identified before choosing the
Databricks implementation.

If a reasonable documented approach exists, append a separate
HUMAN_REVIEW_SUGGESTION section using the required format below.


==================================================
TARGET RULES
==================================================

If the parsed mapping identifies the target as Flat File,
you may state that a file-based Databricks output is required.

However, DO NOT invent:

- path
- DBFS location
- cloud storage location
- delimiter
- header=true
- header=false
- overwrite
- append
- partitioning
- compression
- file naming behavior

Do NOT show example code containing guessed values.

Bad example:

df.write.mode("overwrite").option("header", "true").csv(...)

Do not produce this.

Instead state unresolved properties explicitly.

Do NOT suggest example storage technologies or locations
when the target location is unresolved.

Do NOT mention examples such as:

- DBFS
- ADLS
- S3
- cloud storage

unless explicitly present in the parsed mapping.


==================================================
DATA FLOW RULES
==================================================

Represent only connections explicitly present in DATA FLOW.

Do NOT infer that a transformation output port is unused
simply because port-level connector metadata is not available.

Do NOT infer additional upstream or downstream components.

If port-level usage cannot be determined, state:

Not identified in parsed mapping.


==================================================
MIGRATION RISK RULES
==================================================

Only list a migration risk when supported by evidence in
the parsed mapping.

Do NOT create speculative risks such as:

- hidden logic may exist
- workflow logic may exist
- session SQL may exist
- other mappings may modify the data
- external dependencies may exist

unless such evidence appears in the parsed mapping.

Missing configuration may be listed as UNRESOLVED,
but it must not be converted into a hypothetical problem.


==================================================
DOCUMENTATION USAGE
==================================================

The documentation context is divided into two sources:

1. POWERCENTER DOCUMENTATION
   Use it to understand the behavior and semantics of the
   original Informatica PowerCenter transformations.

2. DATABRICKS DOCUMENTATION
   Use it as reference material for identifying appropriate
   Databricks and PySpark equivalents.

The parsed PowerCenter mapping remains the source of truth.

Documentation is generic reference material only.

PowerCenter documentation explains what a transformation CAN do.
It does NOT prove that a capability is used in this mapping.

Databricks documentation explains available target mechanisms.
It does NOT justify introducing implementation logic that is not
required by the parsed mapping.

Never use either documentation source to invent mapping-specific
logic, configuration, behavior, or dependencies.

Parsed mapping evidence always takes precedence over all
documentation.

Documentation metadata may be used to identify material that a human
reviewer should inspect.

When creating a HUMAN_REVIEW_SUGGESTION, cite the available metadata
when present, for example:

- product
- version
- document_type
- page_number
- source

Do not invent a document title, page number, version, or source that
is not present in the documentation context.


==================================================
PYSPARK RULE
==================================================

Do NOT generate complete PySpark source code yet.

You may identify a conceptual Databricks/PySpark equivalent
only when it follows directly from the mapping.

Do not include guessed configuration values or implementation
details.


==================================================
PARSED POWERCENTER MAPPING
==================================================

{mapping_context}


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
Not identified in parsed mapping.


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
- Include this section only when a documented, reasonable migration
  approach exists but human validation is still required.
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

Represent only the connections explicitly present in
the parsed mapping.


==================================================
MIGRATION RISKS / UNRESOLVED
==================================================

List only:

- unresolved information explicitly visible from the mapping
- migration requirements that cannot yet be implemented safely
- HUMAN_REVIEW_SUGGESTION items that remain pending human approval

Do not include speculative risks.

A HUMAN_REVIEW_SUGGESTION must never be reported as a completed
migration decision.


==================================================
HUMAN REVIEW SUGGESTIONS
==================================================

When an implementation cannot be determined safely, keep the
implementation classified as UNRESOLVED.

However, when the available PowerCenter or Databricks documentation
provides enough information to identify a reasonable migration
approach, you MAY add a separate HUMAN_REVIEW_SUGGESTION.

The suggestion must use this structure:

Human review suggestion:
[HUMAN_REVIEW_SUGGESTION]

Possible approach:
<describe the possible Databricks approach>

Why human review is required:
<explain what information is still missing>

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

Rules for suggested code:

- Suggested code is NOT approved migration code.
- Suggested code is for human review only.
- Suggested code must not contain invented configuration values.
- Suggested code must not invent mapping-specific behavior.
- Suggested code must not be treated as executable migration output.
- The final PySpark generator will be responsible for rendering
  HUMAN_REVIEW_SUGGESTION code as comments only.
- The underlying migration action must remain UNRESOLVED.
- If there is not enough evidence even for a reasonable suggestion,
  do not create a HUMAN_REVIEW_SUGGESTION.


==================================================
NO SPECULATIVE VALIDATION
==================================================

Do not ask the user to confirm hypothetical missing logic.

Do NOT write statements such as:

- confirm that no hidden logic exists
- verify that no hidden calculations are required
- potential hidden logic
- check whether additional business rules exist

If no such logic is present in the parsed mapping,
simply state what was identified.

Absence of evidence is UNRESOLVED only when that missing
information is required for the migration.


==================================================
FINAL SELF-CHECK
==================================================

Before producing the answer, verify:

- Did I invent a filter?
- Did I invent a join?
- Did I invent an SQL override?
- Did I invent a file path?
- Did I invent header or write mode?
- Did I invent variable semantics?
- Did I invent collect/first/last/agg logic?
- Did I infer downstream usage not shown in DATA FLOW?
- Did I treat documentation capabilities as actual mapping logic?
- Did I present a HUMAN_REVIEW_SUGGESTION as a confirmed solution?
- Did I create suggested code without keeping the implementation
  UNRESOLVED?
- Did I invent documentation metadata or references?

If the answer to any question is YES,
remove or correct that statement before returning the migration plan.
"""


def create_migration_plan_node(
    state: AgentState,
) -> dict:
    """
    Create a migration plan for every PowerCenter mapping.

    Each mapping is analyzed independently to keep prompts
    smaller and avoid truncated LLM responses.

    Cached plans are reused when available.
    Newly generated plans are saved immediately so
    interrupted executions can resume without repeating
    already completed LLM calls.
    """

    print("\nCreating migration plans...")

    mapping = state["mapping"]
    xml_path = state["xml_path"]

    retrieved_docs = state.get(
        "retrieved_docs",
        [],
    )

    documentation_context = (
        build_documentation_context(
            retrieved_docs
        )
    )

    pc_mappings = mapping.get(
        "mappings",
        [],
    )

    print(
        f"Mappings to analyze: "
        f"{len(pc_mappings)}"
    )

    # Load plans already generated for this XML.
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
        # CACHE HIT
        # ---------------------------------------------

        cached_plan = migration_plans.get(
            mapping_name
        )

        if (
            cached_plan
            and cached_plan.strip()
        ):
            print(
                "Migration plan found in cache."
            )

            print(
                f"Cached plan characters: "
                f"{len(cached_plan)}"
            )

            continue

        # ---------------------------------------------
        # BUILD CONTEXT
        # ---------------------------------------------

        single_mapping = (
            build_single_mapping_input(
                full_mapping=mapping,
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
        # BUILD PROMPT
        # ---------------------------------------------

        prompt = build_prompt(
            mapping_context=mapping_context,
            documentation_context=(
                documentation_context
            ),
        )

        # ---------------------------------------------
        # CALL LLM
        # ---------------------------------------------

        try:
            print(
                "Sending mapping to LLM..."
            )

            response = invoke_planner_with_retry(
                prompt=prompt,
            )

            print(
                "LLM response received."
            )

            migration_plan = (
                response.content
            )

            if not migration_plan.strip():
                raise ValueError(
                    "LLM returned an empty "
                    "migration plan for mapping: "
                    f"{mapping_name}"
                )

            migration_plans[
                mapping_name
            ] = migration_plan

            # Save immediately after every successful
            # mapping so progress is never lost.
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
    # VALIDATE THAT ALL MAPPINGS HAVE A PLAN
    # ---------------------------------------------

    missing_mappings = []

    for pc_mapping in pc_mappings:
        mapping_name = pc_mapping.get(
            "name",
            "UNKNOWN_MAPPING",
        )

        plan = migration_plans.get(
            mapping_name
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
    # BUILD COMBINED PLAN IN ORIGINAL MAPPING ORDER
    # ---------------------------------------------

    ordered_plans = []

    for pc_mapping in pc_mappings:
        mapping_name = pc_mapping.get(
            "name",
            "UNKNOWN_MAPPING",
        )

        ordered_plans.append(
            migration_plans[
                mapping_name
            ]
        )

    combined_plan = "\n\n".join(
        ordered_plans
    )

    # ---------------------------------------------
    # DEBUG OUTPUT
    # ---------------------------------------------

    print(
        "\nMigration plans available:"
    )

    for pc_mapping in pc_mappings:
        mapping_name = pc_mapping.get(
            "name",
            "UNKNOWN_MAPPING",
        )

        plan = migration_plans[
            mapping_name
        ]

        print(
            f"- {mapping_name}: "
            f"{len(plan)} characters"
        )

    return {
        "migration_plan": combined_plan,
        "migration_plans": migration_plans,
    }