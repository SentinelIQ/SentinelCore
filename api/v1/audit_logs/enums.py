"""
Standard enums for the audit_logs module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.

Usage examples:

In models:
```python
from api.v1.audit_logs.enums import EntityTypeEnum, ActionTypeEnum
from api.core.utils.enum_utils import enum_to_choices

entity_type = models.CharField(
    max_length=50,
    choices=enum_to_choices(EntityTypeEnum),
    default=EntityTypeEnum.OTHER.value
)
```

In serializers:
```python
from api.v1.audit_logs.enums import EntityTypeEnum
from api.core.utils.enum_utils import enum_to_choices

entity_type = serializers.ChoiceField(
    choices=enum_to_choices(EntityTypeEnum),
    default=EntityTypeEnum.OTHER.value
)
```

In views/viewsets:
```python
from api.v1.audit_logs.enums import EntityTypeEnum
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='entity_type',
            description='Filter by entity type',
            enum=EntityTypeEnum,
            required=False
        )
    ]
)
def list(self, request):
    # View implementation
    pass
```
"""
from enum import Enum


class EntityTypeEnum(str, Enum):
    """Common entity types for audit logs"""
    # Alert module
    ALERT = "alert"
    ALERT_RULE = "alert_rule"
    ALERT_COMMENT = "alert_comment"
    
    # Incident module
    INCIDENT = "incident"
    INCIDENT_TIMELINE = "incident_timeline"
    INCIDENT_COMMENT = "incident_comment"
    
    # Task module
    TASK = "task"
    TASK_GROUP = "task_group"
    TASK_TEMPLATE = "task_template"
    
    # Observable module
    OBSERVABLE = "observable"
    OBSERVABLE_TYPE = "observable_type"
    IOC = "ioc"
    TAG = "tag"
    
    # Company/tenant module
    COMPANY = "company"
    DEPARTMENT = "department"
    TEAM = "team"
    
    # User module
    USER = "user"
    USER_GROUP = "user_group"
    ROLE = "role"
    PERMISSION = "permission"
    
    # System module
    SYSTEM = "system"
    SETTING = "setting"
    CONFIG = "config"
    
    # Feed/integrations module
    FEED = "feed"
    ENRICHMENT = "enrichment"
    RESPONDER = "responder"
    ANALYZER = "analyzer"
    CONNECTOR = "connector"
    
    # Notification module
    NOTIFICATION = "notification"
    NOTIFICATION_RULE = "notification_rule"
    NOTIFICATION_CHANNEL = "notification_channel"
    NOTIFICATION_TEMPLATE = "notification_template"
    
    # Reporting module
    REPORT = "report"
    REPORT_TEMPLATE = "report_template"
    DASHBOARD = "dashboard"
    DASHBOARD_WIDGET = "dashboard_widget"
    
    # Wiki module
    WIKI_ARTICLE = "wiki_article"
    WIKI_CATEGORY = "wiki_category"
    
    # MITRE module
    MITRE_TECHNIQUE = "mitre_technique"
    MITRE_TACTIC = "mitre_tactic"
    MITRE_MITIGATION = "mitre_mitigation"
    MITRE_MAPPING = "mitre_mapping"
    
    # MISP module
    MISP_EVENT = "misp_event"
    MISP_ATTRIBUTE = "misp_attribute"
    
    # Authentication module
    SESSION = "session"
    TOKEN = "token"
    API_KEY = "api_key"
    
    # SentinelVision module
    SENTINELVISION_RULE = "sentinelvision_rule"
    SENTINELVISION_RESULT = "sentinelvision_result"
    
    # Integration module
    INTEGRATION = "integration"
    PLAYBOOK = "playbook"
    PLAYBOOK_RUN = "playbook_run"
    
    # Audit module
    AUDIT_LOG = "audit_log"
    
    # Other
    OTHER = "other"


class ActionTypeEnum(str, Enum):
    """Common action types for audit logs"""
    # Basic CRUD operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    
    # Authentication actions
    LOGIN = "login"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_VERIFY = "token_verify"
    PASSWORD_RESET = "password_reset"
    PASSWORD_CHANGE = "password_change"
    
    # Alert actions
    ESCALATE = "escalate"
    INGEST = "ingest"
    BULK_INGEST = "bulk_ingest"
    RESOLVE = "resolve"
    CLOSE = "close"
    REOPEN = "reopen"
    FLAG = "flag"
    UNFLAG = "unflag"
    MERGE = "merge"
    SPLIT = "split"
    FORWARD = "forward"
    
    # Incident actions
    ASSIGN = "assign"
    UNASSIGN = "unassign"
    COMMENT = "comment"
    ADD_TIMELINE = "add_timeline"
    REMOVE_TIMELINE = "remove_timeline"
    LINK_ENTITY = "link_entity"
    UNLINK_ENTITY = "unlink_entity"
    CHANGE_SEVERITY = "change_severity"
    CHANGE_STATUS = "change_status"
    
    # Task actions
    COMPLETE = "complete"
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    REASSIGN = "reassign"
    POSTPONE = "postpone"
    
    # Observable actions
    ENRICH = "enrich"
    MARK_AS_IOC = "mark_as_ioc"
    UNMARK_AS_IOC = "unmark_as_ioc"
    TAG = "tag"
    UNTAG = "untag"
    BLACKLIST = "blacklist"
    WHITELIST = "whitelist"
    CORRELATE = "correlate"
    
    # Feed actions
    IMPORT = "import"
    EXPORT = "export"
    SYNC = "sync"
    REFRESH = "refresh"
    VALIDATE = "validate"
    
    # System actions
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    MAINTENANCE = "maintenance"
    BACKUP = "backup"
    RESTORE = "restore"
    PURGE = "purge"
    CONFIGURE = "configure"
    
    # User management
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    PROMOTE = "promote"
    DEMOTE = "demote"
    GRANT_PERMISSION = "grant_permission"
    REVOKE_PERMISSION = "revoke_permission"
    ADD_TO_GROUP = "add_to_group"
    REMOVE_FROM_GROUP = "remove_from_group"
    
    # Wiki actions
    PUBLISH = "publish"
    UNPUBLISH = "unpublish"
    APPROVE = "approve"
    REJECT = "reject"
    
    # Reporting actions
    GENERATE = "generate"
    SCHEDULE = "schedule"
    RENDER = "render"
    SHARE = "share"
    
    # Notification actions
    SEND = "send"
    TRIGGER = "trigger"
    ACKNOWLEDGE = "acknowledge"
    DISMISS = "dismiss"
    
    # Bulk operations
    BULK_CREATE = "bulk_create"
    BULK_UPDATE = "bulk_update"
    BULK_DELETE = "bulk_delete"
    
    # Celery task actions
    TASK_QUEUED = "task_queued"
    TASK_START = "task_start"
    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    TASK_REVOKED = "task_revoked"
    
    # Playbook actions
    PLAYBOOK_START = "playbook_start"
    PLAYBOOK_COMPLETE = "playbook_complete"
    PLAYBOOK_FAIL = "playbook_fail"
    PLAYBOOK_STEP = "playbook_step"
    
    # Integration actions
    INTEGRATE = "integrate"
    TEST_CONNECTION = "test_connection"
    
    # Other
    SEARCH = "search"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    QUERY = "query"
    TRANSFORM = "transform"
    ANALYZE = "analyze"
    DETECT = "detect"
    OTHER = "other"


# drf-spectacular integration
try:
    from drf_spectacular.extensions import OpenApiSerializerFieldExtension
    from drf_spectacular.plumbing import build_basic_type
    
    class EnumFieldExtension(OpenApiSerializerFieldExtension):
        target_class = 'EnumField'  # Placeholder for custom extension
        
        def map_serializer_field(self, auto_schema, direction):
            enum_values = [e.value for e in self.field.enum_class]
            return build_basic_type(enum_values)
except ImportError:
    pass 