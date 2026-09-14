def indent_sql(
    sql: str,
    spaces: int = 4,
) -> str:
    """
    Indent a SQL block by the requested
    number of spaces.
    """

    prefix = " " * spaces

    return "\n".join(
        f"{prefix}{line}"
        for line in sql.splitlines()
    )