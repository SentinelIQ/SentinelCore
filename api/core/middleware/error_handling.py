"""
Middleware for handling errors and exceptions in requests.

This middleware provides centralized error handling for the application,
with proper logging and formatting of error responses.
"""

import logging
import traceback
from django.http import JsonResponse
from rest_framework import status
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('api')


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware que captura exceções não tratadas e retorna respostas JSON padronizadas.
    
    Garante que todas as exceções não tratadas sejam:
    1. Registradas no log com contexto completo
    2. Retornadas como respostas JSON com código de status apropriado
    3. Formatadas de acordo com o padrão da API
    """
    
    def process_exception(self, request, exception):
        """
        Process unhandled exceptions and return a standardized JSON response.
        
        Args:
            request: The HTTP request
            exception: The unhandled exception
            
        Returns:
            JsonResponse with error details
        """
        # Log the error with full traceback
        logger.error(
            f"Unhandled exception in request {request.method} {request.path}: {str(exception)}",
            exc_info=True
        )
        
        # Create error response
        error_data = {
            "success": False,
            "message": "An error occurred while processing your request",
            "error": str(exception),
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
        
        # Add traceback in debug mode
        if hasattr(request, 'debug') and request.debug:
            error_data["traceback"] = traceback.format_exc()
        
        # Return formatted error response
        return JsonResponse(
            error_data, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 