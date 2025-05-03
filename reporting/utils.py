import uuid
import os
import logging
import markdown2
from datetime import datetime
from weasyprint import HTML
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from incidents.models import Incident
from tasks.models import Task

logger = logging.getLogger('api.reporting')
User = get_user_model()


class ReportGenerator:
    """
    Utility class for generating Markdown and PDF reports from incidents.
    """
    
    @staticmethod
    def generate_markdown_report(incident):
        """
        Generate a Markdown report for an incident.
        
        Args:
            incident (Incident): The incident to generate the report for
            
        Returns:
            str: Markdown formatted report
        """
        try:
            # Fetch related data
            tasks = Task.objects.filter(incident=incident).order_by('order')
            related_alerts = incident.related_alerts.all()
            
            # Prepare metadata
            assignee_name = "Unassigned"
            if incident.assignee:
                assignee_name = f"{incident.assignee.first_name} {incident.assignee.last_name}" if incident.assignee.first_name else incident.assignee.username
            
            company_name = incident.company.name if incident.company else "N/A"
            
            # Generate timeline entries
            timeline_entries = []
            if incident.timeline and isinstance(incident.timeline, list):
                for entry in sorted(incident.timeline, key=lambda x: x.get('timestamp', ''), reverse=False):
                    # Get user display name for the timeline entry
                    created_by_id = entry.get('created_by')
                    created_by = "System"
                    
                    if created_by_id:
                        try:
                            user = User.objects.get(id=created_by_id)
                            created_by = f"{user.first_name} {user.last_name}" if user.first_name else user.username
                        except User.DoesNotExist:
                            created_by = f"User {created_by_id} (deleted)"
                    
                    entry_time = entry.get('timestamp', '')
                    try:
                        # Try to format timestamp nicely
                        entry_time = datetime.fromisoformat(entry_time).strftime('%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        # Use as is if parsing fails
                        pass
                    
                    timeline_entries.append({
                        'title': entry.get('title', 'Event'),
                        'content': entry.get('content', ''),
                        'type': entry.get('type', 'note'),
                        'created_by': created_by,
                        'timestamp': entry_time
                    })
            
            # Build markdown content
            report = f"""# Incident Report: {incident.title}

## Summary
**ID**: {incident.id}  
**Status**: {incident.get_status_display()}  
**Severity**: {incident.get_severity_display()}  
**TLP**: {incident.get_tlp_display()}  
**PAP**: {incident.get_pap_display()}  
**Company**: {company_name}  
**Created**: {incident.created_at.strftime('%Y-%m-%d %H:%M:%S')}  
**Assignee**: {assignee_name}  

## Description
{incident.description}

## Tags
{', '.join(incident.tags) if incident.tags else 'No tags'}

## Timeline
"""

            if timeline_entries:
                for entry in timeline_entries:
                    report += f"### {entry['timestamp']} - {entry['title']} ({entry['type']})\n"
                    report += f"**By**: {entry['created_by']}\n\n"
                    if entry['content']:
                        report += f"{entry['content']}\n\n"
            else:
                report += "No timeline entries recorded.\n\n"

            report += "## Related Alerts\n"
            if related_alerts.exists():
                for alert in related_alerts:
                    report += f"- **{alert.title}** ({alert.get_severity_display()}) - {alert.created_at.strftime('%Y-%m-%d')}\n"
            else:
                report += "No related alerts.\n\n"

            report += "## Tasks\n"
            if tasks.exists():
                for task in tasks:
                    status_emoji = "✅" if task.status == Task.Status.COMPLETED else "⏳"
                    assignee = "Unassigned"
                    if task.assigned_to:
                        assignee = f"{task.assigned_to.first_name} {task.assigned_to.last_name}" if task.assigned_to.first_name else task.assigned_to.username
                    
                    report += f"- {status_emoji} **{task.title}** - {task.get_priority_display()} ({assignee})\n"
                    if task.description:
                        report += f"  - {task.description}\n"
                    if task.notes:
                        report += f"  - Notes: {task.notes}\n"
            else:
                report += "No tasks created.\n\n"

            if incident.custom_fields:
                report += "## Custom Fields\n"
                for key, value in incident.custom_fields.items():
                    report += f"- **{key}**: {value}\n"

            report += f"\n## Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            return report
        
        except Exception as e:
            logger.error(f"Error generating markdown report for incident {incident.id}: {str(e)}")
            return f"# Error Generating Report\n\nAn error occurred while generating the report: {str(e)}"
    
    @staticmethod
    def generate_pdf_report(incident, request=None):
        """
        Generate a PDF report for an incident.
        
        Args:
            incident (Incident): The incident to generate the report for
            request (HttpRequest, optional): Request object for url resolution
            
        Returns:
            bytes: PDF file content
        """
        try:
            # Generate markdown report
            markdown_report = ReportGenerator.generate_markdown_report(incident)
            
            # Convert markdown to HTML
            html_content = markdown2.markdown(
                markdown_report,
                extras=["tables", "code-friendly", "fenced-code-blocks"]
            )
            
            # Prepare context for template
            context = {
                'incident': incident,
                'html_content': html_content,
                'company_name': incident.company.name,
                'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'base_url': request.build_absolute_uri('/') if request else '',
            }
            
            # Render HTML with template
            html_string = render_to_string('reporting/pdf_report.html', context)
            
            # Generate PDF
            pdf_file = HTML(string=html_string).write_pdf()
            
            return pdf_file
        
        except Exception as e:
            logger.error(f"Error generating PDF report for incident {incident.id}: {str(e)}")
            raise 