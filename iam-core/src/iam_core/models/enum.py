from enum import StrEnum


class DataPolicyTypeEnum(StrEnum):
    ALLOW = "ALLOW"
    DISALLOW = "DISALLOW"


class PolicyTargetEnum(StrEnum):
    REGISTER_RECORD = "REGISTER_RECORD"
    GEO = "GEO"
    ATTRIBUTE = "ATTRIBUTE"


class ApplicationType(StrEnum):
    STAFF = "staff"
    AGENT = "agent"
    BENEFICIARY = "beneficiary"


class SyncStatus(StrEnum):
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"
