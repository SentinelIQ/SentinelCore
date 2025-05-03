import uuid
import json
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth import get_user_model
from django.utils import timezone
from companies.models import Company
from model_utils import FieldTracker
# Remove direct imports that cause circular dependencies
# from alerts.models import Alert
# from observables.models import Observable
from api.v1.incidents.enums import (
    IncidentSeverityEnum, IncidentStatusEnum, IncidentTLPEnum, IncidentPAPEnum,
    TimelineEventTypeEnum, IncidentTaskStatusEnum
)
from api.core.utils.enum_utils import enum_to_choices
from api.core.models import CoreModel

User = get_user_model()


# Custom JSON encoder to handle UUIDs
class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            # Return a string representation of the UUID
            return str(obj)
        return super().default(obj)


class Incident(CoreModel):
    """
    Security incident model for the Sentineliq system.
    Incidents can be created manually or escalated from alerts.
    """
    title = models.CharField('Title', max_length=200)
    description = models.TextField('Description')
    summary = models.CharField(
        'Summary', 
        max_length=255,
        blank=True,
        help_text='Brief summary of the incident'
    )
    severity = models.CharField(
        'Severity',
        max_length=20,
        choices=enum_to_choices(IncidentSeverityEnum),
        default=IncidentSeverityEnum.MEDIUM.value
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=enum_to_choices(IncidentStatusEnum),
        default=IncidentStatusEnum.OPEN.value
    )
    
    # Standard fields for security classification and tagging
    tags = ArrayField(
        models.CharField(max_length=50),
        verbose_name='Tags',
        blank=True,
        default=list
    )
    tlp = models.IntegerField(
        'TLP (Traffic Light Protocol)',
        choices=enum_to_choices(IncidentTLPEnum),
        default=IncidentTLPEnum.AMBER.value
    )
    pap = models.IntegerField(
        'PAP (Permissible Actions Protocol)',
        choices=enum_to_choices(IncidentPAPEnum),
        default=IncidentPAPEnum.AMBER.value
    )
    
    # Field tracker
    tracker = FieldTracker(fields=['status', 'assignee', 'severity', 'tlp', 'pap'])
    
    # MITRE ATT&CK Fields
    primary_technique = models.ForeignKey(
        'mitre.MitreTechnique',
        on_delete=models.SET_NULL,
        related_name='primary_technique_incidents',
        verbose_name='Primary MITRE Technique',
        null=True,
        blank=True,
        help_text='Primary MITRE ATT&CK technique associated with this incident',
        limit_choices_to={'is_subtechnique': False}
    )
    sub_technique = models.ForeignKey(
        'mitre.MitreTechnique',
        on_delete=models.SET_NULL,
        related_name='sub_technique_incidents',
        verbose_name='MITRE Sub-technique',
        null=True,
        blank=True,
        help_text='MITRE ATT&CK sub-technique associated with this incident',
        limit_choices_to={'is_subtechnique': True}
    )
    
    # Dates
    start_date = models.DateTimeField(
        'Start Date',
        default=timezone.now
    )
    end_date = models.DateTimeField(
        'End Date',
        null=True,
        blank=True
    )
    
    # New fields for enhanced incident management
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='assigned_incidents',
        verbose_name='Assignee',
        null=True,
        blank=True,
        help_text='User assigned to investigate this incident'
    )
    impact_score = models.PositiveSmallIntegerField(
        'Impact Score',
        default=0,
        help_text='Computed impact score of the incident (0-100)'
    )
    timeline = models.JSONField(
        'Timeline',
        default=list,
        blank=True,
        help_text='Chronological order of events and actions'
    )
    custom_fields = models.JSONField(
        'Custom Fields',
        default=dict,
        blank=True,
        help_text='User-defined metadata for the incident'
    )
    linked_entities = ArrayField(
        models.CharField(max_length=255),
        verbose_name='Linked Entities',
        blank=True,
        default=list,
        help_text='Links to external systems (URLs, ticket IDs, etc.)'
    )
    
    # Direct M2M relationship to Observables - using string reference
    observables = models.ManyToManyField(
        'observables.Observable',
        through='IncidentObservable',
        related_name='incidents',
        verbose_name='Observables',
        blank=True
    )
    
    # SentinelVision responders configuration
    sentinelvision_responders = models.JSONField(
        'SentinelVision Responders',
        default=list,
        blank=True,
        help_text='List of SentinelVision responders to run on this incident'
    )
    
    # Relationships and tenant isolation
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='incidents',
        verbose_name='Company'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_incidents',
        verbose_name='Created by'
    )
    related_alerts = models.ManyToManyField(
        'alerts.Alert',  # Use string reference
        related_name='incidents',
        verbose_name='Related Alerts',
        blank=True
    )
    
    class Meta:
        verbose_name = 'Incident'
        verbose_name_plural = 'Incidents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'severity']),
            models.Index(fields=['created_at']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['assignee']),
            models.Index(fields=['impact_score']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_severity_display()}) - {self.company.name}"
    
    @property
    def alert_count(self):
        """
        Returns the count of related alerts.
        """
        return self.related_alerts.count()
    
    @property
    def observable_count(self):
        """
        Returns the count of related observables.
        """
        return self.observables.count()
    
    @property
    def task_count(self):
        """
        Returns the count of related tasks.
        """
        return self.tasks.count()
    
    def close(self):
        """
        Closes the incident and sets the end date to now.
        """
        self.status = IncidentStatusEnum.CLOSED.value
        self.end_date = timezone.now()
        self.save(update_fields=['status', 'end_date'])
        return True
    
    def add_timeline_entry(self, title, content=None, event_type='note', created_by=None):
        """
        Adds a new entry to the incident timeline.
        
        Args:
            title (str): Title of the timeline entry
            content (str, optional): Content or message
            event_type (str, optional): Type of event
            created_by (User, optional): User who created the entry
            
        Returns:
            dict: The newly created timeline entry
        """
        # Create a new timeline entry
        entry = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content or "",
            "type": event_type,
            "timestamp": timezone.now().isoformat(),
        }
        
        # Add user info if provided
        if created_by:
            entry["created_by"] = str(created_by.id)
            entry["created_by_name"] = created_by.get_full_name() or created_by.username
        
        # Add to timeline
        if not self.timeline:
            self.timeline = []
            
        self.timeline.append(entry)
        self.save(update_fields=['timeline'])
        
        return entry
    
    def calculate_impact_score(self):
        """
        Calculates an impact score based on severity, number of observables, and tasks.
        
        Returns:
            int: The calculated impact score (0-100)
        """
        # Base score from severity
        severity_scores = {
            IncidentSeverityEnum.LOW.value: 10,
            IncidentSeverityEnum.MEDIUM.value: 30,
            IncidentSeverityEnum.HIGH.value: 60,
            IncidentSeverityEnum.CRITICAL.value: 85
        }
        
        base_score = severity_scores.get(self.severity, 30)
        
        # Modifiers
        alert_count = min(self.alert_count, 10)  # Cap at 10
        observable_count = min(self.observable_count, 20)  # Cap at 20
        task_count = min(self.task_count, 10)  # Cap at 10
        
        # Calculate score components
        alert_modifier = alert_count * 0.5  # Up to +5
        observable_modifier = observable_count * 0.25  # Up to +5
        task_modifier = task_count * 0.5  # Up to +5
        
        # Final score (capped at 100)
        score = min(base_score + alert_modifier + observable_modifier + task_modifier, 100)
        
        # Save and return
        self.impact_score = int(score)
        self.save(update_fields=['impact_score'])
        
        return self.impact_score
    
    def run_sentinelvision_responder(self, responder_id=None):
        """
        Executes SentinelVision responders for threat intelligence enrichment
        
        Args:
            responder_id (str, optional): Specific responder to run
            
        Returns:
            dict: Execution results
        """
        try:
            from api.core.utils.sentinelvision import SentinelVisionClient
            
            # Prepare incident data
            incident_data = {
                "incident_id": str(self.id),
                "title": self.title,
                "description": self.description,
                "severity": self.severity,
                "company_id": str(self.company.id),
                "observables": [
                    {
                        "id": str(obs.id),
                        "type": obs.type,
                        "value": obs.value
                    } for obs in self.observables.all()
                ]
            }
            
            # Initialize client and run
            client = SentinelVisionClient()
            
            if responder_id:
                result = client.execute_responder(responder_id, incident_data)
            else:
                result = client.run_all_responders(incident_data)
                
            return {"status": "success", "result": result}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def export_to_report(self, format_type='pdf'):
        """
        Exports the incident to a report format.
        
        Args:
            format_type (str): The format to export to ('pdf', 'html', 'json')
            
        Returns:
            dict: Report data or file reference
        """
        try:
            from api.core.utils.reporting import ReportGenerator
            
            # Create a report generator and export
            generator = ReportGenerator(format_type=format_type)
            result = generator.generate_incident_report(self)
            
            # Log the export
            self.add_timeline_entry(
                title="Report exported",
                content=f"Incident exported to {format_type} format",
                event_type="report_export"
            )
            
            return {
                "status": "success",
                "format": format_type,
                "result": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


class TimelineEvent(CoreModel):
    """
    Individual timeline event for an incident.
    Each event belongs to a specific incident and is created by a user.
    """
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='timeline_events',
        verbose_name='Incident'
    )
    
    # Event metadata
    type = models.CharField(
        'Event Type',
        max_length=50,
        choices=enum_to_choices(TimelineEventTypeEnum),
        default=TimelineEventTypeEnum.OTHER.value
    )
    title = models.CharField('Title', max_length=200)
    message = models.TextField('Message', blank=True, null=True)
    metadata = models.JSONField('Metadata', default=dict, blank=True)
    
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timeline_events',
        verbose_name='User'
    )
    
    # For tenant isolation
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='timeline_events',
        verbose_name='Company'
    )
    
    # Timestamps
    timestamp = models.DateTimeField('Timestamp', default=timezone.now)
    
    class Meta:
        verbose_name = 'Timeline Event'
        verbose_name_plural = 'Timeline Events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['incident']),
            models.Index(fields=['company']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_type_display()}) - {self.incident.title}"
    
    def save(self, *args, **kwargs):
        # Ensure the company is always the same as the incident's
        if self.incident and not self.company_id:
            self.company = self.incident.company
        super().save(*args, **kwargs)


class IncidentObservable(CoreModel):
    """
    Through model for the M2M relationship between Incident and Observable.
    Enables tracking additional metadata about the relationship.
    """
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='incident_observables',
        verbose_name='Incident'
    )
    observable = models.ForeignKey(
        'observables.Observable',
        on_delete=models.CASCADE,
        related_name='incident_observables',
        verbose_name='Observable'
    )
    
    # Relationship metadata
    is_ioc = models.BooleanField(
        'Is an IOC',
        default=False,
        help_text='Indicates if this observable is an Indicator of Compromise for this incident'
    )
    description = models.TextField('Description', blank=True)
    
    # For tenant isolation (always same as incident)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='incident_observable_links',
        verbose_name='Company'
    )
    
    class Meta:
        verbose_name = 'Incident Observable'
        verbose_name_plural = 'Incident Observables'
        unique_together = ['incident', 'observable']
        indexes = [
            models.Index(fields=['incident']),
            models.Index(fields=['observable']),
            models.Index(fields=['company']),
        ]
    
    def __str__(self):
        return f"{self.incident.title} - {self.observable.value}"
    
    def save(self, *args, **kwargs):
        # Ensure the company is always the same as the incident's
        if self.incident and not self.company_id:
            self.company = self.incident.company
        super().save(*args, **kwargs)


class IncidentTask(CoreModel):
    """
    Task associated with an incident.
    Represents an action that needs to be taken as part of the investigation.
    """
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Incident'
    )
    
    # Task details
    title = models.CharField('Title', max_length=200)
    description = models.TextField('Description', blank=True)
    status = models.CharField(
        'Status',
        max_length=20,
        choices=enum_to_choices(IncidentTaskStatusEnum),
        default=IncidentTaskStatusEnum.PENDING.value
    )
    priority = models.PositiveSmallIntegerField(
        'Priority',
        default=1,
        help_text='Task priority (1-5, with 5 being highest)'
    )
    due_date = models.DateTimeField('Due Date', null=True, blank=True)
    
    # Relationships
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name='Assignee'
    )
    
    # For tenant isolation (always same as incident)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='incident_tasks',
        verbose_name='Company'
    )
    
    # Task metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_tasks',
        verbose_name='Created by'
    )
    completed_at = models.DateTimeField('Completed at', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Incident Task'
        verbose_name_plural = 'Incident Tasks'
        ordering = ['priority', 'due_date', 'created_at']
        indexes = [
            models.Index(fields=['incident']),
            models.Index(fields=['assignee']),
            models.Index(fields=['company']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()}) - {self.incident.title}"
    
    def save(self, *args, **kwargs):
        # Ensure the company is always the same as the incident's
        if self.incident and not self.company_id:
            self.company = self.incident.company
            
        # Set completed_at when status changes to complete
        if self.pk:
            old_instance = IncidentTask.objects.get(pk=self.pk)
            if (old_instance.status != IncidentTaskStatusEnum.COMPLETED.value and 
                self.status == IncidentTaskStatusEnum.COMPLETED.value):
                self.completed_at = timezone.now()
                
            # If moving back from completed, reset completed_at
            elif (old_instance.status == IncidentTaskStatusEnum.COMPLETED.value and
                  self.status != IncidentTaskStatusEnum.COMPLETED.value):
                self.completed_at = None
        
        # For new task being created as completed
        elif self.status == IncidentTaskStatusEnum.COMPLETED.value and not self.completed_at:
            self.completed_at = timezone.now()
            
        super().save(*args, **kwargs)
    
    def complete(self):
        """
        Marks the task as completed.
        
        Returns:
            bool: True if the task was completed
        """
        if self.status != IncidentTaskStatusEnum.COMPLETED.value:
            self.status = IncidentTaskStatusEnum.COMPLETED.value
            self.completed_at = timezone.now()
            self.save(update_fields=['status', 'completed_at'])
            
            # Add to incident timeline
            self.incident.add_timeline_entry(
                title=f"Task completed: {self.title}",
                content=f"Task marked as complete by {self.assignee.get_full_name() if self.assignee else 'system'}",
                event_type="task_completed",
                created_by=self.assignee
            )
            
            return True
            
        return False 