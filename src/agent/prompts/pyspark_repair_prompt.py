"""
Prompt builder for repairing generated PySpark migration code.

This module defines the prompt used by the PowerCenter-to-Databricks
migration agent when generated PySpark code fails deterministic
validation.

The repair prompt instructs the LLM to:

- use the parsed PowerCenter mapping as the authoritative source;
- preserve valid migration logic already present in the generated code;
- fix only the violations reported by the deterministic validator;
- avoid inventing unresolved source, target, or transformation details;
- preserve unresolved PowerCenter semantics as TODO comments;
- preserve HUMAN_REVIEW_SUGGESTION content without promoting it to
  approved executable migration logic;
- ensure that suggested Human Review code remains fully commented and
  enclosed between explicit BEGIN/END markers.

The repaired output is subsequently processed by deterministic safety
enforcement and validated again before it can be accepted by the
migration workflow.
"""


def build_pyspark_repair_prompt(
    mapping_context: str,
    migration_plan: str,
    current_code: str,
    violations: list[str],
) -> str:
    """
    Build the prompt used to repair generated PySpark code
    that failed deterministic validation.

    The prompt provides the LLM with the authoritative parsed
    PowerCenter mapping, the migration plan, the current generated
    code, and the exact validator violations that must be corrected.

    HUMAN_REVIEW_SUGGESTION content is treated as non-approved
    migration guidance and must remain completely non-executable.
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
   supported by the parsed mapping, do not implement it
   as executable migration logic.

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
   - variable lifecycle
   - downstream variable usage
   - mapping-specific behavior

4. If configuration is unresolved, preserve it as a TODO
   or explicit placeholder when placeholders are allowed.

5. A TODO must not be accompanied by executable code that
   still assumes the unresolved value.

6. If a Flat File target does not contain enough
   configuration to determine its implementation:

   - do not assume CSV
   - do not assume a path
   - do not assume a delimiter
   - do not assume a header setting
   - do not assume append or overwrite
   - do not assume compression
   - do not assume partitioning
   - leave the write operation commented or unresolved

7. If PowerCenter SETVARIABLE semantics cannot be
   reproduced safely:

   - preserve the exact original expression in a comment
   - mark the migration as unresolved
   - preserve the corresponding TODO
   - do not create an approved implementation using
     collect(), first(), head(), take(), broadcast(),
     Spark configuration, widgets, Python global variables,
     temporary views, Delta tables, job parameters, or
     speculative timestamp logic

8. Source JDBC configuration may use explicit unresolved
   placeholders when required by the existing migration
   structure, for example:

   .option("url", "TODO_URL")
   .option("user", "TODO_USER")
   .option("password", "TODO_PASSWORD")
   .option("driver", "TODO_DRIVER")

   Do not replace placeholders with invented concrete values.

9. Fix all reported validator violations.

10. Do not remove valid transformations merely to make
    validation pass.

11. Do not change correct mapping logic that is unrelated
    to the reported violations.

12. Return ONLY Python/PySpark code.

13. Do not return Markdown code fences.


==================================================
HUMAN REVIEW SUGGESTION RULES
==================================================

The MIGRATION PLAN may contain explicitly marked sections:

[HUMAN_REVIEW_SUGGESTION]

These sections represent possible migration approaches that have
NOT been approved.

A HUMAN_REVIEW_SUGGESTION is NOT executable migration logic.

If the migration plan contains a HUMAN_REVIEW_SUGGESTION:

1. Preserve the fact that the real implementation is UNRESOLVED.

2. Preserve or restore the TODO associated with the unresolved
   migration item.

3. Preserve the human-review suggestion when it can be repaired
   safely.

4. Do NOT delete a valid HUMAN_REVIEW_SUGGESTION merely to make
   validation pass.

5. Do NOT promote the suggestion to normal executable migration
   code.

6. The generated HUMAN_REVIEW_SUGGESTION must be enclosed between
   these exact markers:

   # BEGIN HUMAN_REVIEW_SUGGESTION

   and

   # END HUMAN_REVIEW_SUGGESTION

7. Both BEGIN and END markers are mandatory.

8. Every non-empty line between BEGIN HUMAN_REVIEW_SUGGESTION
   and END HUMAN_REVIEW_SUGGESTION must be a Python comment
   beginning with "#".

9. Any suggested PySpark or Python code must be completely
   commented out.

10. There must be ZERO executable Python statements inside
    the HUMAN_REVIEW_SUGGESTION block.

11. There must be ZERO executable statements outside the block
    that were derived exclusively from a HUMAN_REVIEW_SUGGESTION.

12. Do not remove:

    - HUMAN REVIEW REQUIRED
    - Status: HUMAN_REVIEW_SUGGESTION
    - Confidence
    - why human review is required
    - documentation references when present
    - the warning that the suggestion is not approved

13. Confidence must remain LOW or MEDIUM.

14. Never upgrade a LOW or MEDIUM confidence suggestion to a
    confirmed implementation.

15. Do not introduce a new implementation alternative that was
    not already present in the validated migration plan.

16. Do not invent configuration or mapping-specific facts inside
    a HUMAN_REVIEW_SUGGESTION.

17. If the current generated code accidentally contains executable
    suggestion code, COMMENT IT OUT instead of promoting it or
    silently treating it as approved logic.

18. If HUMAN REVIEW markers are missing or malformed, restore the
    explicit BEGIN and END markers.

19. If suggested code appears outside the HUMAN REVIEW block,
    move it inside the block and comment it out completely,
    but only when that suggested approach already exists in the
    validated migration plan.

20. If a suggestion cannot be preserved safely without inventing
    information, preserve the unresolved TODO and omit unsupported
    suggested details.


==================================================
HUMAN REVIEW REQUIRED STRUCTURE
==================================================

When repairing a HUMAN_REVIEW_SUGGESTION, use this structure:

# TODO: <describe the unresolved migration item>
#
# BEGIN HUMAN_REVIEW_SUGGESTION
# ============================================================
# HUMAN REVIEW REQUIRED
# ============================================================
# Status: HUMAN_REVIEW_SUGGESTION
# Confidence: LOW
#
# PowerCenter:
# <exact original PowerCenter expression or logic if relevant>
#
# Possible approach:
# <suggestion already present in the migration plan>
#
# Why human review is required:
# <reason already present in the migration plan>
#
# Documentation to review:
# <documentation metadata from the migration plan if present>
#
# Suggested PySpark / Python:
#
# suggested_code = ...
#
# IMPORTANT:
# This suggestion is NOT an approved migration implementation.
# Review the PowerCenter semantics and relevant documentation
# before enabling or adapting this code.
# ============================================================
# END HUMAN_REVIEW_SUGGESTION


CRITICAL HUMAN REVIEW SAFETY RULE:

Every non-empty line from:

# BEGIN HUMAN_REVIEW_SUGGESTION

through:

# END HUMAN_REVIEW_SUGGESTION

must begin with "#".

For example, this is INVALID:

# BEGIN HUMAN_REVIEW_SUGGESTION
possible_value = df.first()
# END HUMAN_REVIEW_SUGGESTION

because:

possible_value = df.first()

is executable Python.

The repaired version must be:

# BEGIN HUMAN_REVIEW_SUGGESTION
# possible_value = df.first()
# END HUMAN_REVIEW_SUGGESTION

Never place suggested implementation code after:

# END HUMAN_REVIEW_SUGGESTION

Never transform HUMAN_REVIEW_SUGGESTION content into normal
executable migration code.


==================================================
REPAIR BEHAVIOR
==================================================

Use the VALIDATOR VIOLATIONS below as the specific repair target.

If a violation reports executable code inside a
HUMAN_REVIEW_SUGGESTION:

- preserve the suggestion when supported by the migration plan
- comment out the executable line
- keep it inside the BEGIN/END block
- preserve the unresolved TODO
- do not delete valid Human Review information

If a violation reports missing HUMAN REVIEW markers:

- restore the exact BEGIN marker
- restore the exact END marker
- ensure all content between them is commented

If a violation reports a HUMAN_REVIEW_SUGGESTION that does not
exist in the validated migration plan:

- remove that invented suggestion
- do not preserve its proposed implementation
- preserve any legitimate unresolved TODO

If a violation reports that a validated HUMAN_REVIEW_SUGGESTION
was lost:

- reconstruct it only from information already present in the
  validated migration plan
- do not add new alternatives
- make the reconstructed block completely non-executable

For all other validator violations:

- make the smallest safe correction
- preserve unrelated valid migration logic
- preserve exact PowerCenter expressions
- preserve unresolved TODO items


==================================================
POWERCENTER MAPPING
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

Correct all reported validator violations while changing
as little valid migration logic as possible.


==================================================
FINAL SELF-CHECK
==================================================

Before returning the repaired code, verify:

- Did I invent any configuration?

- Did I assume CSV for an unresolved Flat File target?

- Did I assume a file path, delimiter, header, write mode,
  compression, or partitioning?

- Did I implement unresolved SETVARIABLE semantics as approved
  executable logic?

- Did I preserve the exact original PowerCenter SETVARIABLE
  expression when required?

- Did I preserve valid existing transformations?

- Did I fix every reported validator violation?

- Did I accidentally remove a valid HUMAN_REVIEW_SUGGESTION?

- Did I convert a HUMAN_REVIEW_SUGGESTION into executable code?

- If the validated migration plan contains a
  HUMAN_REVIEW_SUGGESTION, is the underlying migration item
  still unresolved?

- Is the unresolved item still represented by a TODO?

- Does every HUMAN_REVIEW_SUGGESTION contain:

  # BEGIN HUMAN_REVIEW_SUGGESTION

  and

  # END HUMAN_REVIEW_SUGGESTION

- Does every non-empty line between those markers begin with "#"?

- Is there any executable suggested code between the BEGIN and
  END markers?

- Is there any suggested implementation code after the END marker?

- Did I preserve HUMAN REVIEW REQUIRED?

- Did I preserve Confidence: LOW or Confidence: MEDIUM?

- Did I clearly preserve the fact that the suggestion is NOT
  an approved migration implementation?

- Did I introduce an implementation alternative that was not
  present in the validated migration plan?

If any HUMAN_REVIEW_SUGGESTION contains executable code,
the repaired output is invalid.

Comment out that code before returning.

If HUMAN REVIEW markers are missing, restore them.

If unsupported suggested logic was invented, remove that
unsupported suggestion and preserve the unresolved TODO.

Return only the corrected Python/PySpark code.
""".strip()