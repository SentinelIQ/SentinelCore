import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth import get_user_model
from companies.models import Company
from django.utils import timezone
from django.db.models import Count
from observables.models import Observable
from model_utils import FieldTracker
import logging
from api.v1.alerts.enums import AlertSeverityEnum, AlertStatusEnum, AlertTLPEnum, AlertPAPEnum
from api.core.utils.enum_utils import enum_to_choices
from api.core.models import CoreModel

User = get_user_model()
logger = logging.getLogger('api')


class Alert(CoreModel):
    """
    Security alert model for the Sentineliq system.
    Each alert belongs to a specific company and has a severity level.
    """
    title = models.CharField('Title', max_length=200)
    description = models.TextField('Description')
    severity = models.CharField(
        'Severity',
        max_length=20,
        choices=enum_to_choices(AlertSeverityEnum),
        default=AlertSeverityEnum.MEDIUM.value
    )
    source = models.CharField('Source', max_length=100)
    source_ref = models.CharField('Source Reference', max_length=100, blank=True)
    status = models.CharField(
        'Status',
        max_length=20,
        choices=enum_to_choices(AlertStatusEnum),
        default=AlertStatusEnum.NEW.value
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
        choices=enum_to_choices(AlertTLPEnum),
        default=AlertTLPEnum.AMBER.value
    )
    pap = models.IntegerField(
        'PAP (Permissible Actions Protocol)',
        choices=enum_to_choices(AlertPAPEnum),
        default=AlertPAPEnum.AMBER.value
    )
    
    # Field tracker
    tracker = FieldTracker(fields=['status'])
    
    date = models.DateTimeField(
        'Alert Date',
        default=timezone.now
    )
    
    # MITRE ATT&CK Fields
    primary_technique = models.ForeignKey(
        'mitre.MitreTechnique',
        on_delete=models.SET_NULL,
        related_name='primary_technique_alerts',
        verbose_name='Primary MITRE Technique',
        null=True,
        blank=True,
        help_text='Primary MITRE ATT&CK technique associated with this alert',
        limit_choices_to={'is_subtechnique': False}
    )
    sub_technique = models.ForeignKey(
        'mitre.MitreTechnique',
        on_delete=models.SET_NULL,
        related_name='sub_technique_alerts',
        verbose_name='MITRE Sub-technique',
        null=True,
        blank=True,
        help_text='MITRE ATT&CK sub-technique associated with this alert',
        limit_choices_to={'is_subtechnique': True}
    )
    
    # New fields for enhanced alert functionality
    external_source = models.CharField(
        'External Source',
        max_length=100,
        blank=True,
        help_text='External system that generated the alert (e.g., MISP, SIEM, Firewall)'
    )
    observable_data = models.JSONField(
        'Observable Data',
        default=dict,
        blank=True,
        help_text='List of observables (IPs, domains, hashes) related to this alert'
    )
    artifact_count = models.PositiveIntegerField(
        'Artifact Count',
        default=0,
        help_text='Number of attached observables/artifacts'
    )
    ioc_tags = ArrayField(
        models.CharField(max_length=50),
        verbose_name='IOC Tags',
        blank=True,
        default=list,
        help_text='Specific tags for Indicators of Compromise (IOCs)'
    )
    raw_payload = models.JSONField(
        'Raw Payload',
        default=dict,
        blank=True,
        help_text='Original alert data as received from the source system'
    )
    
    # Direct M2M relationship with Observable (replacing the through model)
    observables = models.ManyToManyField(
        Observable,
        related_name='alerts',
        verbose_name='Observables',
        blank=True
    )
    
    # Relationships and tenant isolation
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name='Company'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_alerts',
        verbose_name='Created by'
    )
    
    class Meta:
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'severity']),
            models.Index(fields=['created_at']),
            models.Index(fields=['date']),
            models.Index(fields=['source_ref']),
            models.Index(fields=['external_source']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['source_ref', 'external_source', 'company'],
                name='unique_alert_per_source_ref_and_company'
            )
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_severity_display()}) - {self.company.name}"
    
    def can_escalate(self):
        """
        Checks if the alert can be escalated to an incident.
        """
        return self.status != AlertStatusEnum.ESCALATED.value
    
    @property
    def is_escalated(self):
        """
        Returns whether the alert has been escalated to an incident.
        """
        return self.status == AlertStatusEnum.ESCALATED.value
    
    def update_artifact_count(self):
        """
        Updates the artifact_count based on observable count and observable_data.
        """
        # Count direct observables
        observable_count = self.observables.count()
        
        # Count observables in observable_data
        json_observable_count = 0
        if self.observable_data and isinstance(self.observable_data, dict):
            json_observable_count = sum(len(items) if isinstance(items, list) else 1 
                                     for items in self.observable_data.values())
        elif self.observable_data and isinstance(self.observable_data, list):
            json_observable_count = len(self.observable_data)
        
        self.artifact_count = observable_count + json_observable_count
        
    def save(self, *args, **kwargs):
        """
        Override save method to update artifact_count before saving.
        """
        self.update_artifact_count()
        super().save(*args, **kwargs)
    
    def add_observable(self, observable, is_ioc=False):
        """
        Add an observable to this alert and mark if it's an IOC.
        
        Args:
            observable (Observable): Observable instance to add
            is_ioc (bool): Whether this observable is an Indicator of Compromise
        """
        if is_ioc and observable.id not in self.observables.values_list('id', flat=True):
            # If it's an IOC, add its tags to ioc_tags
            if observable.tags:
                self.ioc_tags = list(set(self.ioc_tags + observable.tags))
                
        # Add the observable to the M2M relationship
        self.observables.add(observable)
        
        # Update the artifact count
        self.update_artifact_count()
        self.save(update_fields=['artifact_count', 'ioc_tags'])
        
        return True
    
    def remove_observable(self, observable):
        """
        Remove an observable from this alert.
        
        Args:
            observable (Observable): Observable instance to remove
        """
        if observable.id in self.observables.values_list('id', flat=True):
            self.observables.remove(observable)
            
            # Update the artifact count
            self.update_artifact_count()
            self.save(update_fields=['artifact_count'])
            
            return True
        return False
    
    @classmethod
    def deduplicate(cls, alert_data, company):
        """
        Check if an alert with the same source_ref and external_source already exists.
        
        Args:
            alert_data (dict): The alert data containing source_ref and external_source
            company (Company): The company to check for duplicates
            
        Returns:
            Alert or None: The existing alert if found, otherwise None
        """
        if not alert_data.get('source_ref') or not alert_data.get('external_source'):
            return None
            
        try:
            return cls.objects.get(
                source_ref=alert_data['source_ref'],
                external_source=alert_data['external_source'],
                company=company
            )
        except cls.DoesNotExist:
            return None

    def prepare_for_sentinelvision(self):
        """
        Prepares alert data for SentinelVision analysis.
        
        Returns:
            dict: Formatted alert data for the vision pipeline
        """
        observable_types_by_pattern = {
            "ip": ["ip", "ip-src", "ip-dst"],
            "url": ["url", "uri"],
            "domain": ["domain", "hostname"],
            "hash": ["md5", "sha1", "sha256"],
            "file": ["filename"],
            "email": ["email", "email-src", "email-dst"]
        }
        
        # Get direct observables
        direct_observables = {}
        for observable in self.observables.all():
            obs_type = observable.type
            
            # Map observable type to broader category
            for category, patterns in observable_types_by_pattern.items():
                if obs_type in patterns:
                    obs_type = category
                    break
            
            if obs_type not in direct_observables:
                direct_observables[obs_type] = []
                
            direct_observables[obs_type].append(observable.value)
        
        # Combine with observable_data if it exists
        all_observables = direct_observables.copy()
        if self.observable_data and isinstance(self.observable_data, dict):
            for obs_type, values in self.observable_data.items():
                # Map type if needed
                mapped_type = obs_type
                for category, patterns in observable_types_by_pattern.items():
                    if obs_type in patterns:
                        mapped_type = category
                        break
                
                if mapped_type not in all_observables:
                    all_observables[mapped_type] = []
                
                # Add values, handling both lists and single values
                if isinstance(values, list):
                    all_observables[mapped_type].extend(values)
                else:
                    all_observables[mapped_type].append(values)
        
        return {
            "alert_id": str(self.id),
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "source": self.source,
            "company_id": str(self.company.id),
            "observables": all_observables,
            "tags": self.tags
        }
    
    def trigger_sentinelvision_pipeline(self, pipeline_name=None):
        """
        Triggers SentinelVision analysis with this alert's data.
        
        Args:
            pipeline_name (str, optional): Specific pipeline to run. If None, runs the default.
            
        Returns:
            dict: Pipeline execution result or error information
        """
        try:
            from api.core.utils.sentinelvision import SentinelVisionClient
            
            # Prepare data
            data = self.prepare_for_sentinelvision()
            
            # Initialize client
            client = SentinelVisionClient()
            
            # Execute pipeline
            if pipeline_name:
                result = client.execute_pipeline(pipeline_name, data)
            else:
                result = client.process_alert(data)
                
            logger.info(f"SentinelVision triggered for alert {self.id} - Result: {result}")
            return {"status": "success", "result": result}
            
        except Exception as e:
            logger.error(f"Error triggering SentinelVision for alert {self.id}: {str(e)}")
            return {"status": "error", "message": str(e)} 