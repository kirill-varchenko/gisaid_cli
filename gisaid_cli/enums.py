from enum import StrEnum


class Database(StrEnum):
    EpiCoV = "EpiCoV"
    EpiFlu = "EpiFlu"
    EpiRSV = "EpiRSV"


class FrameshiftsConfirmation(StrEnum):
    CATCH_ALL = "none"
    CATCH_NOVEL = "com"
    CATCH_NONE = "all"
