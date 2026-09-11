def build_migration_plan_repair_prompt(
    mapping_context: str,
    current_plan: str,
    violations: list[str],
) -> str:
    """
    Build a compact repair prompt for one migration plan.

    The repair LLM must fix validator violations while
    preserving valid facts, requirements, unresolved items,
    and safe HUMAN_REVIEW_SUGGESTION sections.
    """

    violations_text = "\n".join(
        f"- {violation}"
        for violation in violations
    )

    return f"""
You are repairing ONE Informatica PowerCenter to Databricks
migration plan.

Fix ONLY the validator violations listed below.

Do not redesign the migration plan.

The parsed PowerCenter mapping is the authoritative source
for mapping-specific facts and behavior.

Preserve valid:

- FACT statements
- MIGRATION REQUIREMENT statements
- UNRESOLVED items
- HUMAN_REVIEW_SUGGESTION sections


==================================================
CORE REPAIR RULES
==================================================

1. Fix every validator violation.

2. Do not invent mapping-specific behavior or configuration.

3. Do not convert unsupported assumptions into FACT,
   MIGRATION REQUIREMENT, Databricks equivalent, or
   Migration action.

4. When required implementation information is missing,
   keep the item UNRESOLVED.

5. Use exactly:

Not identified in parsed mapping.

when the implementation cannot be determined safely.

6. Preserve exact PowerCenter expressions when present.

7. Return the COMPLETE repaired migration plan.


==================================================
DO NOT INVENT
==================================================

Do not invent or confirm unsupported:

- CSV, JSON, Parquet, or other file formats
- DBFS, ADLS, S3, or storage paths
- delimiters or headers
- write modes
- compression or partitioning
- JDBC URLs or credentials
- filters
- joins
- aggregations
- SQL overrides
- variable lifecycle
- variable scope
- downstream usage
- persistence behavior
- workflow or session behavior


==================================================
FLAT FILE RULE
==================================================

A PowerCenter target identified only as "Flat File" does NOT
prove that the Databricks output format is CSV.

If format, path, delimiter, header, write mode, or storage
technology are not explicitly present in the parsed mapping:

- keep them UNRESOLVED
- do not put them in approved migration logic

Examples such as:

df.write.format("csv")
DBFS
ADLS
S3

must not appear as confirmed migration implementation unless
explicitly supported by the parsed mapping.


==================================================
SETVARIABLE RULE
==================================================

If SETVARIABLE appears:

- preserve the exact original expression
- preserve the migration requirement
- keep the Databricks implementation UNRESOLVED unless
  variable lifecycle, scope, downstream usage, and required
  persistence are explicitly known

Do NOT present Python variables, job parameters, widgets,
Spark configuration, temporary views, Delta tables,
collect(), first(), last(), aggregation, broadcast, or similar
mechanisms as the confirmed equivalent of SETVARIABLE unless
the mapping proves those semantics.

Such approaches may exist only inside a valid
HUMAN_REVIEW_SUGGESTION.


==================================================
HUMAN REVIEW RULE
==================================================

A HUMAN_REVIEW_SUGGESTION is NOT an approved implementation.

If one exists, it must use this structure:

Human review suggestion:
[HUMAN_REVIEW_SUGGESTION]

Possible approach:
<possible approach>

Why human review is required:
<missing evidence or semantic uncertainty>

Documentation to review:
<only references already present in the current plan>

Confidence:
LOW

or:

Confidence:
MEDIUM

Suggested PySpark / Python:
<optional conceptual code>

Rules:

- the marker [HUMAN_REVIEW_SUGGESTION] is mandatory
- Confidence must be exactly LOW or MEDIUM
- the underlying migration item must remain UNRESOLVED
- suggested code is not approved migration code
- do not move suggestion content into Migration action
- do not move suggestion content into Databricks equivalent
- do not invent new documentation references
- do not invent new migration alternatives

If an existing suggestion cannot be repaired safely,
remove the suggestion and keep the item UNRESOLVED.


==================================================
PARSED MAPPING
==================================================

{mapping_context}


==================================================
CURRENT MIGRATION PLAN
==================================================

{current_plan}


==================================================
VALIDATOR VIOLATIONS
==================================================

{violations_text}


==================================================
FINAL CHECK
==================================================

Before returning:

- every validator violation must be fixed
- unsupported CSV/storage assumptions must be removed
- SETVARIABLE implementation must remain unresolved unless proven
- every Human Review suggestion must contain the exact marker
- Confidence must be exactly LOW or MEDIUM
- suggested code must remain non-approved
- no valid mapping facts may be lost

Return ONLY the complete repaired migration plan.
Do not add explanations or markdown fences.
""".strip()