def build_pyspark_repair_prompt(
    mapping_context: str,
    migration_plan: str,
    current_code: str,
    violations: list[str],
) -> str:
    """
    Build the prompt used to repair generated PySpark code
    that failed deterministic validation.
    """

    violations_text = "\n".join(
        f"- {violation}"
        for violation in violations
    )

    return f"""
You are repairing PySpark code generated from an
Informatica PowerCenter mapping.

The existing generated code failed deterministic
validation.

Your task is to correct ONLY the reported violations
while preserving all valid migration logic.

==================================================
AUTHORITATIVE RULES
==================================================

1. The parsed PowerCenter mapping is the source of truth.

2. The migration plan is advisory only.
   If the migration plan suggests something that is not
   supported by the parsed mapping, do not implement it.

3. Never invent:
   - JDBC URLs
   - usernames
   - passwords
   - JDBC drivers
   - file paths
   - file formats
   - delimiters
   - header settings
   - write modes
   - filters
   - joins
   - aggregations
   - SQL overrides
   - business rules

4. If configuration is unresolved, preserve it as a TODO
   or placeholder.

5. A TODO must not be accompanied by executable code that
   still assumes the unresolved value.

6. If a Flat File target does not contain enough
   configuration to determine its implementation:
   - do not assume CSV
   - do not assume a path
   - do not assume append/overwrite
   - leave the write operation commented or unresolved

7. If PowerCenter SETVARIABLE semantics cannot be
   reproduced safely:
   - preserve the original expression in a comment
   - mark the migration as unresolved
   - do not use collect(), first(), head(), take(),
     broadcast(), Spark configuration, widgets, or
     speculative timestamp logic

8. Source JDBC configuration may use explicit placeholders,
   for example:

   .option("url", "TODO_URL")
   .option("user", "TODO_USER")
   .option("password", "TODO_PASSWORD")
   .option("driver", "TODO_DRIVER")

   Do not invent concrete values.

9. Fix all reported validator violations.

10. Do not remove valid transformations merely to make
    validation pass.

11. Return ONLY Python/PySpark code.

12. Do not return Markdown code fences.

==================================================
POWERcenter MAPPING
==================================================

{mapping_context}

==================================================
MIGRATION PLAN
==================================================

{migration_plan}

==================================================
CURRENT GENERATED CODE
==================================================

{current_code}

==================================================
VALIDATOR VIOLATIONS
==================================================

{violations_text}

==================================================
TASK
==================================================

Return the corrected PySpark implementation.

Perform a final self-check before answering:

- Did I invent any configuration?
- Did I assume CSV for an unresolved Flat File target?
- Did I assume a write mode?
- Did I implement unresolved SETVARIABLE semantics?
- Did I preserve valid existing transformations?
- Did I fix every validator violation?

Return only the corrected Python code.
""".strip()