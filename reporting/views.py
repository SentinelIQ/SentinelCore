from django.shortcuts import render
import logging
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
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
    
    @extend_schema(
        tags=['Reporting'],
        summary="Generate incident report in Markdown format",
        description=(
            "Generates a comprehensive Markdown report for a security incident. This endpoint is essential "
            "for security teams that need to document and share incident details for post-incident analysis, "
            "compliance, or knowledge sharing. The Markdown format allows for easy editing, conversion to "
            "other formats, and inclusion in documentation systems. The report includes all incident details, "
            "timeline events, related alerts, observables (IOCs), tasks, and analyst notes. This report can "
            "be used for incident documentation, team handovers, management updates, and regulatory reporting."
        ),
        parameters=[
            OpenApiParameter(
                name="incident_id",
                description="UUID of the incident to generate a report for",
                required=True,
                type=str,
                location=OpenApiParameter.PATH
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Markdown report generated successfully"
            ),
            404: OpenApiResponse(
                description="Incident not found",
                examples=[
                    OpenApiExample(
                        name="incident_not_found",
                        summary="Incident not found error",
                        description="Example of response when the specified incident doesn't exist",
                        value={
                            "status": "error",
                            "message": "Incident not found",
                            "data": None
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        name="permission_denied",
                        summary="Permission denied error",
                        description="Example of response when user lacks permission to view the incident",
                        value={
                            "status": "error",
                            "message": "You do not have permission to view this incident",
                            "data": None
                        }
                    )
                ]
            ),
            500: OpenApiResponse(
                description="Report generation error",
                examples=[
                    OpenApiExample(
                        name="generation_error",
                        summary="Report generation error",
                        description="Example of response when there's an error generating the report",
                        value={
                            "status": "error",
                            "message": "Error generating report: Failed to render template",
                            "data": None
                        }
                    )
                ]
            )
        }
    )
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
    
    @extend_schema(
        tags=['Reporting'],
        summary="Generate incident report in PDF format",
        description=(
            "Generates a professionally formatted PDF report for a security incident. PDF reports "
            "are essential for formal documentation, management presentations, and regulatory compliance. "
            "This endpoint creates a comprehensive document with the incident details, timeline, "
            "related observables (IOCs), affected systems, and remediation actions. PDF reports include "
            "proper formatting, company branding, tables, charts, and data visualizations where appropriate. "
            "These reports are commonly used for executive briefings, customer communications, legal "
            "documentation, and regulatory submissions following a security incident."
        ),
        parameters=[
            OpenApiParameter(
                name="incident_id",
                description="UUID of the incident to generate a report for",
                required=True,
                type=str,
                location=OpenApiParameter.PATH
            ),
            OpenApiParameter(
                name="template",
                description="Report template to use (default, executive, detailed, technical, compliance)",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name="include_iocs",
                description="Whether to include observables/IOCs in the report",
                required=False,
                type=bool,
                location=OpenApiParameter.QUERY
            )
        ],
        responses={
            200: OpenApiResponse(
                description="PDF report generated successfully"
            ),
            404: OpenApiResponse(
                description="Incident not found",
                examples=[
                    OpenApiExample(
                        name="incident_not_found",
                        summary="Incident not found error",
                        description="Example of response when the specified incident doesn't exist",
                        value={
                            "status": "error",
                            "message": "Incident not found",
                            "data": None
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        name="permission_denied",
                        summary="Permission denied error",
                        description="Example of response when user lacks permission to view the incident",
                        value={
                            "status": "error",
                            "message": "You do not have permission to view this incident",
                            "data": None
                        }
                    )
                ]
            ),
            500: OpenApiResponse(
                description="Report generation error",
                examples=[
                    OpenApiExample(
                        name="generation_error",
                        summary="Report generation error",
                        description="Example of response when there's an error generating the PDF",
                        value={
                            "status": "error",
                            "message": "Error generating report: PDF rendering failed",
                            "data": None
                        }
                    )
                ]
            )
        }
    )
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
