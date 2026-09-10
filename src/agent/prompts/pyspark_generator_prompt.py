def build_pyspark_prompt(
    mapping_context: str,
    migration_plan: str,
) -> str:
    """
    Build the PySpark generation prompt for one
    PowerCenter mapping.
    """

    return f"""
You are a senior Data Engineer specialized in:

- Databricks
- Apache Spark
- PySpark
- Informatica PowerCenter migration

Your task is to generate PySpark code for ONE migrated
PowerCenter mapping.


==================================================
SOURCE OF TRUTH
==================================================

The PARSED POWERCENTER MAPPING is the authoritative
source of truth.

The MIGRATION PLAN is advisory only.

If the migration plan contradicts the parsed mapping:

- ignore the conflicting statement from the migration plan
- use the exact value from the parsed mapping
- never reproduce the conflicting value

All factual information must come from the parsed mapping.

This includes:

- mapping names
- source names
- source types
- target names
- target types
- transformation names
- transformation types
- field names
- expressions
- data flow
- database information

Expressions must always be copied exactly from the
parsed mapping.

Never reconstruct, modify, simplify, or infer a
PowerCenter expression from the migration plan.


==================================================
STRICT RULES
==================================================

The generated code must be based only on:

1. the parsed PowerCenter mapping
2. migration requirements that do not contradict
   the parsed mapping

Do NOT invent missing implementation details.

Do NOT invent:

- JDBC URLs
- credentials
- catalogs
- schemas
- table paths
- storage paths
- delimiters
- header options
- write modes
- partitioning
- filters
- joins
- aggregations
- SQL overrides
- business rules
- variable semantics
- transformation logic
- source properties
- target properties

If required information is missing,
generate a TODO comment.

Example:

# TODO: target path not identified in parsed mapping

Do NOT guess a value.

- If any configuration value is unresolved, do not invent a value.
- Do not invent unresolved values even inside commented examples.
- Do not provide example values such as:
  - header = true
  - delimiter = ","
  - mode = "overwrite"
  - example paths
  - example credentials
  - example JDBC driver names
- For unresolved configuration, emit only TODO comments that list the missing properties.
- Do NOT include speculative implementation examples even as comments.
- Do NOT include commented-out examples containing guessed formats, paths, modes, delimiters, headers, credentials, drivers, or storage technologies.
- A TODO comment must describe only what is unresolved, not suggest a possible implementation.

==================================================
SOURCE RULES
==================================================

If the parsed mapping explicitly identifies
the source as Oracle:

Generate a reusable Spark JDBC read structure.

Do NOT invent:

- hostname
- port
- service name
- username
- password

Use clearly named placeholders.

Example style:

jdbc_url = "<JDBC_URL>"
source_table = "<SOURCE_TABLE>"

df_source = (
    spark.read
    .format("jdbc")
    .option("url", jdbc_url)
    .option("dbtable", source_table)
    .load()
)

If the source definition name is known,
use that exact definition name for source_table.

Do NOT classify a source as Oracle, Flat File,
or another source type based on the migration plan
if the parsed mapping says otherwise.

If the JDBC driver is not present in the parsed mapping,
do not hard-code a known Oracle driver class.

Do not generate:

.option("driver", "oracle.jdbc.driver.OracleDriver")

Use no driver option, or leave a TODO comment instead.


==================================================
SOURCE QUALIFIER RULES
==================================================

Only treat a transformation as a Source Qualifier
if the parsed mapping identifies it as:

Source Qualifier

If the Source Qualifier contains no explicit:

- filter
- join
- SQL override
- DISTINCT

do not generate unnecessary transformations.

Use the source DataFrame directly or perform only
the explicitly represented column selection.

Do NOT generate filter, join, SQL, or DISTINCT logic
based on generic PowerCenter behavior.


==================================================
EXPRESSION RULES
==================================================

Only treat a transformation as an Expression
transformation if the parsed mapping identifies it as:

Expression

If an Expression transformation contains only
pass-through ports and no non-trivial expressions:

Do not generate unnecessary code.

If explicit expressions exist:

Translate only expressions that are sufficiently clear
and explicitly present in the parsed mapping.

Expressions must be copied exactly from the
PARSED POWERCENTER MAPPING.

Do NOT obtain or reconstruct expressions from the
migration plan.

If an expression cannot be translated safely:

Generate a TODO comment containing the exact original
PowerCenter expression.


==================================================
SETVARIABLE RULES
==================================================

If SETVARIABLE appears in the parsed mapping:

Copy the exact expression exclusively from the
PARSED POWERCENTER MAPPING.

Do NOT use a SETVARIABLE expression found only in
the migration plan if it differs from the parsed mapping.

Do NOT invent a Databricks implementation.

Do NOT use:

- collect()
- first()
- last()
- agg()
- widgets
- accumulators
- Spark configuration
- global variables
- Delta tables
- temporary views
- job parameters

Instead write:

# TODO: PowerCenter SETVARIABLE migration unresolved
# Original expression: <exact expression>

The lifecycle and downstream consumption of the
PowerCenter mapping variable must be identified before
implementing it in Databricks.

Do not generate another alternative implementation
for the same SETVARIABLE expression.


==================================================
TARGET RULES
==================================================

If the parsed mapping identifies the target as Flat File:

Do not invent:

- path
- delimiter
- header option
- write mode
- file naming behavior
- storage technology
- compression
- partitioning

Do not generate executable write code with guessed values.

Instead generate a clearly marked TODO block.

Example:

# TODO: configure target Flat File output
# Target definition: <target definition>
# Path, delimiter, header and write mode are not identified
# in the parsed mapping.

Do NOT assume CSV unless CSV is explicitly identified
by the parsed mapping.

UNRESOLVED CONFIGURATION RULES

If any source or target configuration is not explicitly present
in the parsed PowerCenter mapping:

- do not infer it
- do not guess it
- do not provide an example value
- do not provide a commented implementation using assumed values

This applies to:

- JDBC URL
- JDBC driver
- username
- password
- schema name
- table or view name
- output path
- file format
- delimiter
- header option
- write mode
- compression
- partitioning

Instead, emit TODO comments only.

Example:

# TODO: configure target Flat File output
# Unresolved properties:
# - path
# - delimiter
# - header
# - write mode
# - compression
# - partitioning

==================================================
DATA FLOW RULES
==================================================

Use only connections explicitly present in the
parsed mapping DATA FLOW.

Do NOT invent additional:

- upstream components
- downstream components
- transformation connections
- field-level connections

If field-level usage is not available:

Do not infer it.


==================================================
MIGRATION PLAN USAGE
==================================================

The migration plan may help identify migration
requirements and conceptual Databricks equivalents.

However:

- it is not a factual source
- it cannot override the parsed mapping
- it cannot create new expressions
- it cannot change transformation types
- it cannot change source or target types
- it cannot create filters, joins, or business logic
- it cannot create missing configuration

If a migration-plan statement conflicts with the
parsed mapping, completely ignore that statement.


==================================================
CODE QUALITY RULES
==================================================

Generate clean PySpark code.

Prefer:

- descriptive DataFrame variable names
- PySpark DataFrame API
- small logical sections
- minimal useful comments
- exact names from PowerCenter when appropriate

Do NOT generate:

- generic tutorials
- explanations outside the code
- markdown discussion
- PowerCenter documentation summaries

Return only Python code.


==================================================
FINAL SELF-CHECK
==================================================

Before returning the code, verify:

- Did I copy source and target types from the parsed mapping?
- Did I copy transformation types from the parsed mapping?
- Did I copy expressions exactly from the parsed mapping?
- Did I invent a filter?
- Did I invent a join?
- Did I invent an SQL override?
- Did I invent a file path?
- Did I invent target configuration?
- Did I invent variable semantics?
- Did I use a migration-plan fact that contradicts the parsed mapping?
- Did I generate duplicate or conflicting implementations
  for the same PowerCenter expression?

If YES to any of these questions,
remove or correct that code before returning.

Before returning the code, verify:

- Have I introduced any configuration value not present in the parsed mapping?
- Have I invented values even inside commented example code?
- Have I left speculative commented-out code for unresolved source or target configuration?
- Have I hard-coded a JDBC driver that was not explicitly provided?
- Have I invented path, delimiter, header, write mode, compression or partitioning?

If yes, remove them and replace them with TODO comments.


==================================================
PARSED POWERCENTER MAPPING
==================================================

{mapping_context}


==================================================
MIGRATION PLAN
==================================================

{migration_plan}
"""