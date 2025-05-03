"""
Standard enums for the observables module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.
"""
from enum import Enum


class ObservableCategoryEnum(str, Enum):
    """MISP-compatible categories for observables"""
    ANTIVIRUS = "antivirus"
    ARTIFACTS = "artifacts"
    ATTRIBUTION = "attribution"
    EXTERNAL_ANALYSIS = "external_analysis"
    FINANCIAL_FRAUD = "financial_fraud"
    INTERNAL_REFERENCE = "internal_reference"
    NETWORK_ACTIVITY = "network_activity"
    OTHER = "other"
    PAYLOAD_DELIVERY = "payload_delivery"
    PAYLOAD_INSTALLATION = "payload_installation"
    PAYLOAD_TYPE = "payload_type"
    PERSISTENCE = "persistence"
    PERSON = "person"
    SOCIAL_NETWORK = "social_network"
    SUPPORT_TOOL = "support_tool"
    TARGETING = "targeting"


class ObservableTypeEnum(str, Enum):
    """Observable type enum"""
    # Network observables
    AS = "as"
    DOMAIN = "domain"
    EMAIL = "email"
    EMAIL_ATTACHMENT = "email-attachment"
    EMAIL_BODY = "email-body"
    EMAIL_HEADER = "email-header"
    EMAIL_SUBJECT = "email-subject"
    HOSTNAME = "hostname"
    IP = "ip"
    IP_PORT = "ip-port"
    MAC_ADDRESS = "mac-address"
    URI = "uri"
    URL = "url"
    USER_AGENT = "user-agent"
    
    # File observables
    AUTHENTIHASH = "authentihash"
    FILENAME = "filename"
    FILEPATH = "filepath"
    HASH_MD5 = "hash-md5"
    HASH_SHA1 = "hash-sha1"
    HASH_SHA256 = "hash-sha256"
    HASH_SHA512 = "hash-sha512"
    IMPHASH = "imphash"
    MALWARE_SAMPLE = "malware-sample"
    MIME_TYPE = "mime-type"
    PEHASH = "pehash"
    SSDEEP = "ssdeep"
    
    # System observables
    MUTEX = "mutex"
    NAMED_PIPE = "named-pipe"
    PROCESS = "process"
    PROCESS_STATE = "process-state"
    REGISTRY = "regkey"
    REGISTRY_VALUE = "regkey|value"
    WINDOWS_SERVICE = "windows-service-name"
    WINDOWS_SCHEDULED_TASK = "windows-scheduled-task"
    
    # Financial observables
    BANK_ACCOUNT = "bank-account-nr"
    BIC = "bic"
    BITCOIN = "btc"
    CC_NUMBER = "cc-number"
    IBAN = "iban"
    
    # Person observables
    FIRST_NAME = "first-name"
    LAST_NAME = "last-name"
    FULL_NAME = "full-name"
    PASSPORT_NUMBER = "passport-number"
    PHONE_NUMBER = "phone-number"
    
    # Analysis observables
    SIGMA = "sigma"
    SNORT = "snort"
    STIX2 = "stix2-pattern"
    YARA = "yara"
    
    # Threat intelligence
    CAMPAIGN_NAME = "campaign-name"
    JA3_FINGERPRINT = "ja3-fingerprint-md5"
    THREAT_ACTOR = "threat-actor"
    VULNERABILITY = "vulnerability"
    WEAKNESS = "weakness"
    
    # Other
    COMMENT = "comment"
    OTHER = "other"


class ObservableTLPEnum(int, Enum):
    """Traffic Light Protocol classification enum"""
    WHITE = 0
    GREEN = 1
    AMBER = 2
    RED = 3


class ObservableRelationTypeEnum(str, Enum):
    """Observable relationship type enum"""
    CONNECTED = "connected"
    CONTAINS = "contains"
    DROPS = "drops"
    DOWNLOADS = "downloads"
    RESOLVES_TO = "resolves_to"
    COMMUNICATES_WITH = "communicates_with"
    EXTRACTED_FROM = "extracted_from"
    CREATED_BY = "created_by"
    PART_OF = "part_of"
    VARIANT_OF = "variant_of" 