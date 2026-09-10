"""
Parser for XML files exported from Informatica PowerCenter.

This module reads a PowerCenter XML file and extracts
the main repository, folder, source, target and mapping information.
"""

import xml.etree.ElementTree as ET

from parser.mapping_parser import parse_mappings


def parse_targets(folder) -> list:
    """
    Extract targets from a PowerCenter folder.
    """

    targets = []

    for target in folder.findall("TARGET"):
        target_data = {
            "name": target.get("NAME"),
            "database_type": target.get("DATABASETYPE"),
            "fields": []
        }

        for field in target.findall("TARGETFIELD"):
            field_data = {
                "name": field.get("NAME"),
                "datatype": field.get("DATATYPE"),
                "precision": field.get("PRECISION"),
                "scale": field.get("SCALE"),
                "nullable": field.get("NULLABLE")
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
            "fields": []
        }

        for field in source.findall("SOURCEFIELD"):
            field_data = {
                "name": field.get("NAME"),
                "datatype": field.get("DATATYPE"),
                "precision": field.get("PRECISION"),
                "scale": field.get("SCALE"),
                "nullable": field.get("NULLABLE")
            }

            source_data["fields"].append(field_data)

        sources.append(source_data)

    return sources


def parse_powercenter_xml(file_path: str) -> dict:
    """
    Parse an XML file exported from Informatica PowerCenter.

    Args:
        file_path (str): Path to the PowerCenter XML file.

    Returns:
        dict: Parsed PowerCenter structure.
    """

    tree = ET.parse(file_path)
    root = tree.getroot()

    repository = root.find("REPOSITORY")
    folder = repository.find("FOLDER")

    result = {
        "repository": repository.get("NAME"),
        "folder": folder.get("NAME"),
        "sources": parse_sources(folder),
        "targets": parse_targets(folder),
        "mappings": parse_mappings(folder)
    }

    return result