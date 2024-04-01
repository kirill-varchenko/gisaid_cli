from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from gisaid_cli.enums import Database, FrameshiftsConfirmation


def empty_string_to_none(v: str | None) -> str | None:
    if not v:
        return None
    return v


NonEmptyStrOrNone = Annotated[str | None, BeforeValidator(empty_string_to_none)]


class AuthToken(BaseModel):
    database: Database
    client_id: str
    token: str
    expiry: datetime


class Metadata(BaseModel):
    submitter: str
    fn: str
    covv_virus_name: str
    covv_type: str
    covv_passage: str
    covv_collection_date: str
    covv_location: str
    covv_add_location: NonEmptyStrOrNone = None
    covv_host: str
    covv_add_host_info: NonEmptyStrOrNone = None
    covv_sampling_strategy: NonEmptyStrOrNone = None
    covv_gender: str
    covv_patient_age: str
    covv_patient_status: str
    covv_specimen: NonEmptyStrOrNone = None
    covv_outbreak: NonEmptyStrOrNone = None
    covv_last_vaccinated: NonEmptyStrOrNone = None
    covv_treatment: NonEmptyStrOrNone = None
    covv_seq_technology: str
    covv_assembly_method: NonEmptyStrOrNone = None
    covv_coverage: NonEmptyStrOrNone = None
    covv_orig_lab: str
    covv_orig_lab_addr: str
    covv_provider_sample_id: NonEmptyStrOrNone = None
    covv_subm_lab: str
    covv_subm_lab_addr: str
    covv_subm_sample_id: NonEmptyStrOrNone = None
    covv_consortium: NonEmptyStrOrNone = None
    covv_authors: str


class Submission(Metadata):
    covv_sequence: str
    subm_confirmed: FrameshiftsConfirmation = Field(
        serialization_alias="_subm_confirmed"
    )
    st: str = Field("v 3.0.4", serialization_alias="_st")
