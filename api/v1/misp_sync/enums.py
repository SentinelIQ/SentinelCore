from enum import Enum, IntEnum


class MISPThreatLevelEnum(IntEnum):
    """
    MISP Event Threat Level IDs
    """
    HIGH = 1      # High risk
    MEDIUM = 2    # Medium risk
    LOW = 3       # Low risk
    UNDEFINED = 4 # Undefined risk


class MISPAnalysisEnum(IntEnum):
    """
    MISP Event Analysis Levels
    """
    INITIAL = 0   # Initial analysis
    ONGOING = 1   # Ongoing analysis
    COMPLETED = 2 # Completed analysis


class MISPDistributionEnum(IntEnum):
    """
    MISP Event/Attribute Distribution Levels
    """
    ORGANIZATION = 0      # Your organization only
    COMMUNITY = 1         # This community only
    CONNECTED = 2         # Connected communities
    ALL = 3               # All communities
    SHARING_GROUP = 4     # Sharing group
    INHERIT = 5           # Inherit from event


class MISPSyncStatusEnum(str, Enum):
    """
    MISP Sync Status for tasks and operations
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"


class MISPSyncDirectionEnum(str, Enum):
    """
    Direction of MISP Synchronization
    """
    IMPORT = "import" # From MISP to SentinelIQ
    EXPORT = "export" # From SentinelIQ to MISP 