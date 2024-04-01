import csv
import logging
from pathlib import Path

from gisaid_cli.models import Metadata

logger = logging.getLogger("gisaid_cli")


def load_metadata(file: Path) -> list[Metadata]:
    """Load Metadata items from a csv file."""
    items: list[Metadata] = []
    with open(file, "r", newline="") as fi:
        reader = csv.DictReader(fi)
        for row in reader:
            items.append(Metadata.model_validate(row))
    return items


def load_sequences(file: Path) -> dict[str, str]:
    """Load sequences from fasta file and return dictionaries header:sequence."""
    sequences: dict[str, str] = {}
    with open(file, "r") as fi:
        header = None
        body_lines = []

        for line in fi:
            if line.startswith(">"):
                if header is not None:
                    if body_lines:
                        sequences[header] = "".join(body_lines)
                    else:
                        logger.warning("Empty sequence: %s", header)
                body_lines = []
                header = line.removeprefix(">").rstrip()
            elif line:
                body_lines.append(line.rstrip())

        if header is not None:
            if body_lines:
                sequences[header] = "".join(body_lines)
            else:
                logger.warning("Empty sequence: %s", header)

    return sequences
