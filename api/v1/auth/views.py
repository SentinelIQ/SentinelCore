from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auditlog.models import LogEntry
from api.v1.audit_logs.enums import EntityTypeEnum
from api.core.responses import success_response
from drf_spectacular.utils import extend_schema, OpenApiResponse
import datetime


class TestAuditLogView(APIView):
    """
    A test view that creates an audit log entry.
    This is solely for testing purposes and should be removed in production.
    """
    
    @extend_schema(
        summary="Test Audit Log Creation",
        description="Creates a test audit log entry for the current user",
        tags=["Authentication & Access Control"],
        responses={
            200: OpenApiResponse(description="Audit log created successfully"),
        }
    )
    def post(self, request, *args, **kwargs):
        # Create a test audit log entry
        current_time = datetime.datetime.now()
        
        # Create log entry using django-auditlog directly
        LogEntry.objects.log_create(
            instance=request.user,
            action=LogEntry.Action.CREATE,
            changes={},
            actor=request.user,
            additional_data={
                "entity_type": EntityTypeEnum.USER.value,
                "test": True, 
                "timestamp": str(current_time),
                "request_method": request.method,
                "request_path": request.path,
                "response_status": 200
            }
        )
        
        return success_response(
            message="Test audit log created successfully",
            data={"user_id": str(request.user.id)}
        ) 