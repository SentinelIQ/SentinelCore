from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from api.core.responses import success_response, error_response


@extend_schema(
    tags=['System Monitoring & Operations'],
    summary="Test Sentry integration",
    description="Endpoint to test if Sentry error reporting is working correctly. Admin only.",
    responses={
        200: OpenApiResponse(description="Success message with transaction ID"),
        500: OpenApiResponse(description="Deliberate error to test Sentry"),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def test_sentry(request):
    """
    Test endpoint to verify Sentry integration.
    
    If debug=true is provided, raises an exception to test error reporting.
    Otherwise, sends a test message to Sentry.
    
    Admin permissions required.
    """
    try:
        # Import Sentry functions
        from sentineliq.sentry import capture_message, set_context
        
        # Add additional test context
        set_context("test_data", {
            "source": "api_endpoint",
            "user_id": str(request.user.id) if request.user.is_authenticated else None,
            "transaction_id": getattr(request, 'transaction_id', 'none'),
        })
        
        # Check if we should trigger a test error
        if request.query_params.get('debug', '').lower() == 'true':
            # Trigger a test exception for Sentry
            capture_message("Test error about to be triggered", level="info")
            
            # Simulate division by zero
            result = 1 / 0
            
            # Code never reaches here
            return success_response("This will never be returned")
        
        # Send a test message to Sentry
        capture_message(
            "Sentry test message from API endpoint", 
            level="info",
            tags={"test_type": "api_endpoint"}
        )
        
        # Also execute the Celery task for testing
        from sentineliq.celery import test_sentry_task
        if request.query_params.get('celery', '').lower() == 'true':
            task = test_sentry_task.delay()
            task_info = {"task_id": task.id}
        else:
            task_info = None
        
        return success_response(
            "Sentry test successful. A test message has been sent to Sentry.",
            {"transaction_id": getattr(request, 'transaction_id', None), "task": task_info}
        )
    
    except ImportError:
        return error_response(
            "Sentry is not properly configured.", 
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        # This exception will be automatically captured by Sentry
        return error_response(
            f"Test error triggered: {str(e)}",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 