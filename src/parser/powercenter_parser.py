"""
Parser for XML files exported from Informatica PowerCenter.

This module reads a PowerCenter XML file and extracts
the main repository, folder, source, target, session and mapping information.
"""

import xml.etree.ElementTree as ET

from parser.mapping_parser import (
    parse_mappings,
    parse_mapplets,
)


def parse_flat_file_config(element) -> dict | None:
    """
    Extract Flat File configuration from an XML element.

    Flat File configuration can be defined both:

    - inside a TARGET definition;
    - inside a SESSION target instance.

    Args:
        element: XML element that may contain a FLATFILE child.

    Returns:
        dict | None:
            Flat File configuration when present,
            otherwise None.
    """

    flat_file = element.find("FLATFILE")

    if flat_file is None:
        return None

    return {
        "codepage": flat_file.get("CODEPAGE"),
        "delimited": flat_file.get("DELIMITED"),
        "delimiter": flat_file.get("DELIMITERS"),
        "quote_character": flat_file.get("QUOTE_CHARACTER"),
        "null_character": flat_file.get("NULL_CHARACTER"),
        "row_delimiter": flat_file.get("ROWDELIMITER"),
        "skip_rows": flat_file.get("SKIPROWS"),
        "strip_trailing_blanks": flat_file.get(
            "STRIPTRAILINGBLANKS"
        ),
    }


def merge_flat_file_config(
    definition_config: dict | None,
    session_config: dict | None,
) -> dict:
    """
    Resolve the effective Flat File configuration.

    Session-level configuration takes precedence over
    Target Definition configuration.

    Args:
        definition_config:
            Configuration defined in the TARGET.

        session_config:
            Configuration defined in the SESSION.

    Returns:
        dict:
            Effective Flat File configuration.
    """

    effective_config = {}

    if definition_config:
        effective_config.update(definition_config)

    if session_config:
        for key, value in session_config.items():
            if value is not None:
                effective_config[key] = value

    return effective_config


def parse_targets(folder) -> list:
    """
    Extract targets from a PowerCenter folder.
    """

    targets = []

    for target in folder.findall("TARGET"):
        target_data = {
            "name": target.get("NAME"),
            "database_type": target.get("DATABASETYPE"),
            "version_number": target.get("VERSIONNUMBER"),
            "flat_file": parse_flat_file_config(target),
            "fields": [],
        }

        for field in target.findall("TARGETFIELD"):
            field_data = {
                "name": field.get("NAME"),
                "datatype": field.get("DATATYPE"),
                "precision": field.get("PRECISION"),
                "scale": field.get("SCALE"),
                "nullable": field.get("NULLABLE"),
            }

            target_data["fields"].append(field_data)

        targets.append(target_data)

    return targets


def parse_sources(folder) -> list:
    """
    Extract sources from a PowerCenter folder.
    """

    sources = []

    for source in folder.findall("SOURCE"):
        source_data = {
            "name": source.get("NAME"),
            "database_type": source.get("DATABASETYPE"),
            "database_name": source.get("DBDNAME"),
            "owner_name": source.get("OWNERNAME"),
            "version_number": source.get("VERSIONNUMBER"),
            "fields": [],
        }

        for field in source.findall("SOURCEFIELD"):
            field_data = {
                "name": field.get("NAME"),
                "datatype": field.get("DATATYPE"),
                "precision": field.get("PRECISION"),
                "scale": field.get("SCALE"),
                "nullable": field.get("NULLABLE"),
            }

            source_data["fields"].append(field_data)

        sources.append(source_data)

    return sources


def parse_session_target_overrides(folder) -> dict:
    """
    Extract target runtime configuration from PowerCenter sessions.

    A PowerCenter session may override properties defined
    in the Target Definition.

    These values are important because they represent
    the runtime configuration used by the session.

    Returns:
        dict:
            Overrides grouped by mapping name
            and target instance name.

    Example:

        {
            "mapping_name": {
                "target_name": {
                    "flat_file": {
                        "delimiter": ";"
                    }
                }
            }
        }
    """

    session_overrides = {}

    for session in folder.findall(".//SESSION"):
        mapping_name = session.get("MAPPINGNAME")

        if not mapping_name:
            continue

        for instance in session.findall(
            "SESSTRANSFORMATIONINST"
        ):
            transformation_type = instance.get(
                "TRANSFORMATIONTYPE"
            )

            if transformation_type != "Target Definition":
                continue

            instance_name = instance.get(
                "SINSTANCENAME"
            )

            if not instance_name:
                continue

            flat_file_config = parse_flat_file_config(
                instance
            )

            if flat_file_config is None:
                continue

            if mapping_name not in session_overrides:
                session_overrides[mapping_name] = {}

            session_overrides[mapping_name][
                instance_name
            ] = {
                "flat_file": flat_file_config
            }

    return session_overrides


def enrich_mappings_with_io_metadata(
    mappings: list,
    sources: list,
    targets: list,
    session_overrides: dict,
) -> list:
    """
    Enrich mappings with source and target metadata.

    The INSTANCE elements parsed by mapping_parser.py
    are used to associate each mapping with its
    corresponding Source Definitions and Target Definitions.

    Target metadata also includes:

    - Target Definition Flat File configuration;
    - Session-level Flat File override;
    - Effective runtime Flat File configuration.
    """

    source_by_name = {
        source["name"]: source
        for source in sources
    }

    target_by_name = {
        target["name"]: target
        for target in targets
    }

    for mapping in mappings:
        mapping_name = mapping.get("name")

        mapping["sources"] = []
        mapping["targets"] = []

        for instance in mapping.get(
            "instances",
            [],
        ):
            instance_type = instance.get("type")

            transformation_name = instance.get(
                "transformation_name"
            )

            if not transformation_name:
                continue

            if instance_type == "SOURCE":
                source_definition = source_by_name.get(
                    transformation_name
                )

                if source_definition:
                    mapping["sources"].append(
                        dict(source_definition)
                    )

            elif instance_type == "TARGET":
                target_definition = target_by_name.get(
                    transformation_name
                )

                if target_definition is None:
                    continue

                target_data = dict(
                    target_definition
                )

                definition_flat_file = (
                    target_data.get("flat_file")
                )

                session_flat_file = (
                    session_overrides
                    .get(mapping_name, {})
                    .get(transformation_name, {})
                    .get("flat_file")
                )

                target_data[
                    "session_flat_file"
                ] = session_flat_file

                target_data[
                    "effective_flat_file"
                ] = merge_flat_file_config(
                    definition_config=(
                        definition_flat_file
                    ),
                    session_config=(
                        session_flat_file
                    ),
                )

                mapping["targets"].append(
                    target_data
                )

    return mappings

def parse_powercenter_xml(
    file_path: str,
) -> dict:
    """
    Parse an XML file exported from Informatica PowerCenter.

    Args:
        file_path:
            Path to the PowerCenter XML file.

    Returns:
        dict:
            Parsed PowerCenter structure.
    """

    tree = ET.parse(file_path)

    root = tree.getroot()

    repository = root.find(
        "REPOSITORY"
    )

    if repository is None:
        raise ValueError(
            "REPOSITORY element not found "
            "in PowerCenter XML."
        )

    folder = repository.find(
        "FOLDER"
    )

    if folder is None:
        raise ValueError(
            "FOLDER element not found "
            "in PowerCenter XML."
        )

    sources = parse_sources(
        folder
    )

    targets = parse_targets(
        folder
    )

    mappings = parse_mappings(
        folder
    )

    mapplets = parse_mapplets(
        folder
    )

    session_overrides = (
        parse_session_target_overrides(
            folder
        )
    )

    mappings = (
        enrich_mappings_with_io_metadata(
            mappings=mappings,
            sources=sources,
            targets=targets,
            session_overrides=(
                session_overrides
            ),
        )
    )

    result = {
        "repository": repository.get(
            "NAME"
        ),

        "folder": folder.get(
            "NAME"
        ),

        "metadata": {
            "repository_version": (
                repository.get(
                    "VERSION"
                )
            ),

            "powercenter_version": None,
        },

        "sources": sources,

        "targets": targets,

        "session_target_overrides": (
            session_overrides
        ),

        "mappings": mappings,

        "mapplets": mapplets,
    }

    return result