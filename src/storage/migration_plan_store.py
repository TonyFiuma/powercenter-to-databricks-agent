import hashlib
import json
from pathlib import Path


DEFAULT_CACHE_PATH = Path(
    "data/output/migration_plans.json"
)


# ============================================================
# Cache version
# ============================================================

PLANNER_CACHE_VERSION = "v4"


# ============================================================
# Hash
# ============================================================

def calculate_file_hash(
    file_path: str,
) -> str:
    """
    Calculate the SHA256 hash of the source XML.

    The XML hash is used to invalidate migration plans
    when the PowerCenter source changes.
    """

    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb",
    ) as file:
        while chunk := file.read(8192):
            sha256.update(
                chunk
            )

    return sha256.hexdigest()


# ============================================================
# Load
# ============================================================

def load_migration_plans(
    source_xml: str,
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> dict[str, str]:
    """
    Load cached migration plans.

    Cache validity depends on:

    1. Source XML hash.
    2. Planner cache version.

    Changing the planner prompt therefore invalidates
    old plans without requiring manual cache deletion.
    """

    if not cache_path.exists():
        print(
            "Migration plan cache not found."
        )

        return {}

    # --------------------------------------------------------
    # Read cache
    # --------------------------------------------------------

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
            "Migration plan cache could "
            f"not be loaded: {exc}"
        )

        return {}

    # --------------------------------------------------------
    # Validate source XML
    # --------------------------------------------------------

    current_hash = calculate_file_hash(
        source_xml
    )

    cached_hash = cache_data.get(
        "source_hash"
    )

    if cached_hash != current_hash:
        print(
            "Migration plan cache is stale. "
            "The source XML has changed."
        )

        return {}

    # --------------------------------------------------------
    # Validate planner version
    # --------------------------------------------------------

    cached_version = cache_data.get(
        "planner_cache_version"
    )

    if (
        cached_version
        != PLANNER_CACHE_VERSION
    ):
        print(
            "Migration plan cache is stale. "
            "Planner version has changed."
        )

        print(
            "Cached version: "
            f"{cached_version}"
        )

        print(
            "Current version: "
            f"{PLANNER_CACHE_VERSION}"
        )

        return {}

    # --------------------------------------------------------
    # Read plans
    # --------------------------------------------------------

    migration_plans = cache_data.get(
        "migration_plans",
        {},
    )

    if not isinstance(
        migration_plans,
        dict,
    ):
        print(
            "Migration plan cache has "
            "an invalid structure."
        )

        return {}

    valid_plans = {}

    for mapping_name, plan in (
        migration_plans.items()
    ):
        if (
            isinstance(plan, str)
            and plan.strip()
        ):
            valid_plans[
                mapping_name
            ] = plan

    print(
        "Migration plan cache loaded: "
        f"{len(valid_plans)} mappings."
    )

    return valid_plans


# ============================================================
# Save
# ============================================================

def save_migration_plans(
    source_xml: str,
    migration_plans: dict[str, str],
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> None:
    """
    Persist migration plans to disk.

    The planner version is stored together with the XML
    hash so old plans can automatically be invalidated
    when planner behavior changes.
    """

    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Remove invalid plans
    # --------------------------------------------------------

    valid_plans = {}

    for mapping_name, plan in (
        migration_plans.items()
    ):
        if (
            isinstance(plan, str)
            and plan.strip()
        ):
            valid_plans[
                mapping_name
            ] = plan

    # --------------------------------------------------------
    # Source hash
    # --------------------------------------------------------

    source_hash = calculate_file_hash(
        source_xml
    )

    # --------------------------------------------------------
    # Cache payload
    # --------------------------------------------------------

    cache_data = {
        "source_xml": (
            source_xml
        ),
        "source_hash": (
            source_hash
        ),
        "planner_cache_version": (
            PLANNER_CACHE_VERSION
        ),
        "migration_plans": (
            valid_plans
        ),
    }

    # --------------------------------------------------------
    # Write cache
    # --------------------------------------------------------

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
        "Migration plan cache saved: "
        f"{len(valid_plans)} mappings."
    )

    print(
        "Planner cache version: "
        f"{PLANNER_CACHE_VERSION}"
    )