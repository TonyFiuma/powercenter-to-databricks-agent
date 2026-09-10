def build_migration_plan_repair_prompt(
    mapping_context: str,
    current_plan: str,
    violations: list[str],
) -> str:
    """
    Build a focused repair prompt for one migration plan.

    The repair LLM must correct validator violations without
    introducing new assumptions or changing valid mapping facts.
    """

    violations_text = "\n".join(
        f"- {violation}"
        for violation in violations
    )

    return f"""
You are repairing ONE Informatica PowerCenter to Databricks
migration plan.

Your goal is NOT to redesign the plan.
Your goal is to fix the validator violations while preserving
all valid facts and migration requirements.

==================================================
SOURCE OF TRUTH
==================================================

The parsed PowerCenter mapping is the authoritative source.

Do not add information that is not explicitly present in the
parsed mapping.

==================================================
STRICT REPAIR RULES
==================================================

1. Fix every validator violation listed below.

2. Preserve valid FACT statements from the current plan.

3. Preserve valid MIGRATION REQUIREMENT statements.

4. Do NOT invent:
   - file formats
   - CSV
   - JSON
   - Parquet
   - DBFS
   - ADLS
   - S3
   - storage paths
   - delimiters
   - headers
   - write modes
   - compression
   - partitioning
   - JDBC URLs
   - credentials
   - drivers
   - filters
   - joins
   - aggregations
   - SQL overrides
   - variable lifecycle
   - downstream usage
   - session behavior

5. A PowerCenter target identified only as "Flat File" does NOT
   prove that the Databricks output format is CSV.

   If the exact file format or location is not present in the
   parsed mapping, mark it as UNRESOLVED.

   Do not write examples such as:
   - df.write.format("csv")
   - DBFS
   - ADLS
   - S3

6. If SETVARIABLE appears in the parsed mapping:
   - preserve the exact original expression
   - preserve the migration requirement
   - do not invent a Databricks implementation
   - mark implementation as unresolved unless its lifecycle and
     downstream consumption are explicitly present

7. When information required for implementation is unavailable,
   use exactly:

   Not identified in parsed mapping.

8. Do not provide speculative implementation alternatives for
   unresolved items.

9. Return the COMPLETE repaired migration plan, not only the
   changed section.

10. Return only the migration plan.
    Do not add explanations before or after it.

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

Before returning the repaired plan, verify:

- Did I remove every unsupported CSV assumption?
- Did I remove every unsupported storage-location assumption?
- Did I preserve mapping facts?
- Did I preserve required PowerCenter expressions?
- Did I avoid inventing implementation details?
- Did I mark unresolved information as unresolved?

If any validator violation is still present, repair it before
returning the final plan.
""".strip()
