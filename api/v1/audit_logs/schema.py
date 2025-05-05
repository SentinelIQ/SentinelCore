"""
OpenAPI schema documentation for the audit logs API.

This module enhances the OpenAPI schema documentation for the audit logs API endpoints,
providing detailed information about available endpoints, parameters, and response formats.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.openapi import OpenApiResponse, OpenApiExample
from rest_framework import viewsets

from .views import AuditLogViewSet
from .serializers import LogEntrySerializer, LogEntryListSerializer, AuditLogExportSerializer


# Define examples for better documentation
AUDIT_LOG_EXAMPLE = {
    "id": 12345,
    "timestamp": "2023-08-15T14:22:31.456789Z",
    "actor": {
        "id": "5fa85f64-5717-4562-b3fc-2c963f66def9",
        "username": "john.smith"
    },
    "action": "create",
    "action_display": "Created",
    "entity_type": "incident",
    "entity_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "entity_repr": "Security Breach Investigation #2023-08-001",
    "changes": {
        "title": {
            "old": None,
            "new": "Security Breach Investigation #2023-08-001"
        },
        "status": {
            "old": None,
            "new": "open"
        },
        "severity": {
            "old": None,
            "new": "high"
        }
    },
    "remote_addr": "192.168.1.100",
    "additional_data": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "company_id": "7fa85f64-5717-4562-b3fc-2c963f66bcd7",
        "company_name": "Acme Corporation"
    }
}

AUDIT_LOG_FILTERED_EXAMPLE = {
    "count": 2,
    "next": "https://api.sentineliq.com/api/v1/audit-logs/?page=2",
    "previous": None,
    "results": [
        {
            "id": 12345,
            "timestamp": "2023-08-15T14:22:31.456789Z",
            "actor": {
                "id": "5fa85f64-5717-4562-b3fc-2c963f66def9",
                "username": "john.smith"
            },
            "action": "create",
            "action_display": "Created",
            "entity_type": "incident",
            "entity_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "entity_repr": "Security Breach Investigation #2023-08-001",
            "changes": {
                "title": {
                    "old": None,
                    "new": "Security Breach Investigation #2023-08-001"
                },
                "status": {
                    "old": None,
                    "new": "open"
                }
            },
            "remote_addr": "192.168.1.100"
        },
        {
            "id": 12346,
            "timestamp": "2023-08-15T14:24:15.123456Z",
            "actor": {
                "id": "5fa85f64-5717-4562-b3fc-2c963f66def9", 
                "username": "john.smith"
            },
            "action": "update",
            "action_display": "Updated",
            "entity_type": "incident",
            "entity_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "entity_repr": "Security Breach Investigation #2023-08-001",
            "changes": {
                "status": {
                    "old": "open",
                    "new": "in_progress"
                }
            },
            "remote_addr": "192.168.1.100"
        }
    ]
}

# Create enhanced schema documentation
@extend_schema_view(
    list=extend_schema(
        summary="List audit logs",
        description=(
            "Returns a paginated list of audit logs with filtering capabilities. "
            "This endpoint is crucial for security monitoring, compliance, and forensic analysis. "
            "The logs track all changes to system data with full attribution, timestamps, and the "
            "specific changes made. Administrators can use these logs to investigate incidents, "
            "track user activity, and generate compliance reports. The logs are structured to provide "
            "complete context for each action including who performed it, when, from where, and what "
            "exactly was changed."
        ),
        responses={
            200: OpenApiResponse(
                response=LogEntryListSerializer,
                description="List of audit logs with pagination",
                examples=[
                    OpenApiExample(
                        name="filtered_logs",
                        summary="Filtered audit logs",
                        description="Example of filtered audit logs list",
                        value=AUDIT_LOG_FILTERED_EXAMPLE
                    )
                ]
            )
        }
    ),
    retrieve=extend_schema(
        summary="Retrieve a specific audit log entry",
        description=(
            "Retrieves detailed information about a specific audit log entry. "
            "This endpoint provides comprehensive details about a single system action, "
            "including the user who performed it, timestamps, affected data, and specific "
            "changes made. Security analysts use this information during investigations to "
            "understand exactly what changes were made to system data. The detailed change "
            "history includes both old and new values for each field modified, providing "
            "complete context for the action."
        ),
        responses={
            200: OpenApiResponse(
                response=LogEntrySerializer,
                description="Detailed audit log entry",
                examples=[
                    OpenApiExample(
                        name="log_entry",
                        summary="Audit log entry",
                        description="Example of a detailed audit log entry",
                        value=AUDIT_LOG_EXAMPLE
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Audit log entry not found"
            )
        }
    ),
    export=extend_schema(
        summary="Export audit logs",
        description=(
            "Exports audit logs in various formats for reporting and compliance purposes. "
            "This endpoint supports CSV, Excel, and JSON export formats, enabling integration "
            "with external reporting tools and documentation processes. Security teams use "
            "these exports for compliance reporting, evidence gathering, and offline analysis. "
            "The export can be filtered using the same parameters as the list endpoint, allowing "
            "for targeted exports of specific types of actions, date ranges, or entities. "
            "Exported data maintains all the essential audit information while formatting "
            "it for easy consumption in the requested format."
        ),
        request=AuditLogExportSerializer,
        responses={
            200: OpenApiResponse(
                description="Exported audit logs file",
                examples=[
                    OpenApiExample(
                        name="export_success",
                        summary="Export success response",
                        description="Example response indicating successful export",
                        value={
                            "status": "success",
                            "message": "Audit logs exported successfully",
                            "data": {
                                "file_url": "/media/exports/audit_logs_2023-08-15_143522.csv",
                                "format": "csv",
                                "record_count": 245
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid export parameters",
                examples=[
                    OpenApiExample(
                        name="invalid_format",
                        summary="Invalid format error",
                        description="Example of response when an invalid format is requested",
                        value={
                            "status": "error",
                            "message": "Invalid export format. Supported formats: csv, xlsx, json",
                            "errors": {
                                "format": ["This is not a valid export format."]
                            }
                        }
                    )
                ]
            )
        }
    )
)
class DocumentedAuditLogViewSet(AuditLogViewSet):
    """
    Enhanced documentation for AuditLogViewSet.
    
    This class only exists for documentation purposes and adds extended schema
    information to the AuditLogViewSet for the OpenAPI specification.
    """
    pass 