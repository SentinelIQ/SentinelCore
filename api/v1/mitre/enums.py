"""
Standard enums for the MITRE module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.
"""
from enum import Enum


class MitreRelationshipTypeEnum(str, Enum):
    """MITRE relationship type enum"""
    USES = "uses"
    MITIGATES = "mitigates"
    SUBTECHNIQUE_OF = "subtechnique-of"
    TECHNIQUE_OF = "technique-of"
    REVOKED_BY = "revoked-by"
    DETECTS = "detects" 