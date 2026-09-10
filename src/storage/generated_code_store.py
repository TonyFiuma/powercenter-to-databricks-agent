import hashlib
import json
from pathlib import Path


DEFAULT_CACHE_PATH = Path(
    "data/output/generated_codes.json"
)


def calculate_file_hash(
    file_path: str,
) -> str:
    """
    Calculate the SHA256 hash of a file.
    """

    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb",
    ) as file:
        while chunk := file.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


def is_usable_generated_code(
    code: object,
) -> bool:
    """
    Check whether an LLM response can be considered
    usable generated code.

    This prevents empty or clearly anomalous responses
    from being stored or reused from cache.
    """

    if not isinstance(
        code,
        str,
    ):
        return False

    cleaned_code = code.strip()

    if not cleaned_code:
        return False

    normalized_code = (
        cleaned_code
        .lower()
        .replace(" ", "")
    )

    invalid_responses = {
        "usersafety:safe",
        "safe",
    }

    if normalized_code in invalid_responses:
        return False

    return True


def load_generated_codes(
    source_xml: str,
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> dict[str, str]:
    """
    Load previously generated PySpark code.

    The cache is valid only if the source XML
    has not changed.

    Invalid cached responses are ignored so they
    can be regenerated.
    """

    if not cache_path.exists():
        print(
            "Generated code cache not found."
        )
        return {}

    try:
        with open(
            cache_path,
            "r",
            encoding="utf-8",
        ) as file:
            cache_data = json.load(
                file
            )

    except (
        json.JSONDecodeError,
        OSError,
    ) as exc:
        print(
            "Generated code cache could "
            f"not be loaded: {exc}"
        )
        return {}

    current_hash = calculate_file_hash(
        source_xml
    )

    cached_hash = cache_data.get(
        "source_hash"
    )

    if cached_hash != current_hash:
        print(
            "Generated code cache is stale. "
            "The source XML has changed."
        )
        return {}

    cached_codes = cache_data.get(
        "generated_codes",
        {},
    )

    if not isinstance(
        cached_codes,
        dict,
    ):
        print(
            "Generated code cache has "
            "an invalid structure."
        )
        return {}

    # ==================================================
    # Remove unusable cached responses
    # ==================================================

    generated_codes = {}

    for mapping_name, code in (
        cached_codes.items()
    ):
        if is_usable_generated_code(
            code
        ):
            generated_codes[
                mapping_name
            ] = code

        else:
            print(
                "Ignoring invalid cached "
                f"PySpark for mapping: "
                f"{mapping_name}"
            )

    print(
        "Generated code cache loaded: "
        f"{len(generated_codes)} usable mappings."
    )

    return generated_codes


def save_generated_codes(
    source_xml: str,
    generated_codes: dict[str, str],
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> None:
    """
    Persist generated PySpark code to disk.

    Only usable responses are saved.
    """

    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ==================================================
    # Defensive filtering
    # ==================================================

    valid_generated_codes = {}

    for mapping_name, code in (
        generated_codes.items()
    ):
        if is_usable_generated_code(
            code
        ):
            valid_generated_codes[
                mapping_name
            ] = code

    source_hash = calculate_file_hash(
        source_xml
    )

    cache_data = {
        "source_xml": source_xml,
        "source_hash": source_hash,
        "generated_codes": (
            valid_generated_codes
        ),
    }

    with open(
        cache_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            cache_data,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        "Generated code cache saved: "
        f"{len(valid_generated_codes)} mappings."
    )