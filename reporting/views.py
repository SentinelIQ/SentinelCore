from django.shortcuts import render
import logging
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from api.core.responses import success_response, error_response
from api.core.rbac import HasEntityPermission
from incidents.models import Incident
from .utils import ReportGenerator

logger = logging.getLogger('api.reporting')


class IncidentMarkdownReportView(APIView):
    """
    Generate and return a Markdown report for an incident.
    """
    permission_classes = [IsAuthenticated, HasEntityPermission]
    entity_type = 'incident'  # For RBAC
    
    @extend_schema(tags=['Reporting'])
    def get(self, request, incident_id):
        """
        Generate and return a Markdown report.
        """
        try:
            # Get incident
            try:
                incident = Incident.objects.get(id=incident_id)
            except Incident.DoesNotExist:
                return error_response(
                    message="Incident not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Check permissions (handled by HasEntityPermission)
            self.check_object_permissions(request, incident)
            
            # Generate markdown report
            markdown_report = ReportGenerator.generate_markdown_report(incident)
            
            # Return as plain text response
            response = HttpResponse(markdown_report, content_type='text/markdown')
            response['Content-Disposition'] = f'attachment; filename="incident_{incident.id}_report.md"'
            
            # Log the report generation
            logger.info(f"Markdown report generated for incident {incident.id} by {request.user.username}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating markdown report: {str(e)}")
            return error_response(
                message=f"Error generating report: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IncidentPdfReportView(APIView):
    """
    Generate and return a PDF report for an incident.
    """
    permission_classes = [IsAuthenticated, HasEntityPermission]
    entity_type = 'incident'  # For RBAC
    
    @extend_schema(tags=['Reporting'])
    def get(self, request, incident_id):
        """
        Generate and return a PDF report.
        """
        try:
            # Get incident
            try:
                incident = Incident.objects.get(id=incident_id)
            except Incident.DoesNotExist:
                return error_response(
                    message="Incident not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Check permissions (handled by HasEntityPermission)
            self.check_object_permissions(request, incident)
            
            # Generate PDF report
            pdf_file = ReportGenerator.generate_pdf_report(incident, request)
            
            # Return as PDF response
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="incident_{incident.id}_report.pdf"'
            
            # Log the report generation
            logger.info(f"PDF report generated for incident {incident.id} by {request.user.username}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            return error_response(
                message=f"Error generating report: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
