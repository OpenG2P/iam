from enum import StrEnum


class DataPolicyTypeEnum(StrEnum):
    ALLOW = "ALLOW"
    DISALLOW = "DISALLOW"


class PolicyTargetEnum(StrEnum):
    REGISTER_RECORD = "REGISTER_RECORD"
    GEO = "GEO"
    ATTRIBUTE = "ATTRIBUTE"
