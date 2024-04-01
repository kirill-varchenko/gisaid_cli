import logging

from gisaid_cli.enums import FrameshiftsConfirmation
from gisaid_cli.models import Metadata, Submission

logger = logging.getLogger("gisaid_cli")


def generate_submissions(
    metadata: list[Metadata],
    sequences: dict[str, str],
    frameshifts_confirmation: FrameshiftsConfirmation,
) -> list[Submission]:
    """Generate submissions from metadata and sequences."""
    submissions: list[Submission] = []
    covv_virus_names: set[str] = set()
    for item in metadata:
        if item.covv_virus_name not in sequences:
            logger.warning("Sequence not found: %s", item.covv_virus_name)
            continue
        covv_virus_names.add(item.covv_virus_name)
        data = item.model_dump() | {
            "covv_sequence": sequences[item.covv_virus_name],
            "subm_confirmed": frameshifts_confirmation,
        }
        submissions.append(Submission.model_validate(data))

    not_in_meta = set(sequences.keys()) - covv_virus_names
    if not_in_meta:
        logger.info("Sequences not found in metadata: %s", ", ".join(not_in_meta))

    return submissions
