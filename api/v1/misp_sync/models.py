from django.db import models
from django.contrib.postgres.fields import ArrayField
from companies.models import Company
from django.contrib.auth import get_user_model
from django.utils import timezone
from model_utils import FieldTracker
from api.core.models import CoreModel
import uuid
import logging

User = get_user_model()
logger = logging.getLogger('api')


class MISPServer(CoreModel):
    """
    MISP server configuration to connect to different MISP instances.
    Each MISP server belongs to a specific company for tenant isolation.
    """
    name = models.CharField('Name', max_length=100)
    url = models.URLField('URL', max_length=255)
    api_key = models.CharField('API Key', max_length=255)
    description = models.TextField('Description', blank=True)
    verify_ssl = models.BooleanField('Verify SSL', default=True)
    is_active = models.BooleanField('Is Active', default=True)
    last_sync = models.DateTimeField('Last Sync', null=True, blank=True)
    sync_interval_hours = models.PositiveIntegerField('Sync Interval (hours)', default=24)
    
    # Relationships and tenant isolation
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='misp_servers',
        verbose_name='Company'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_misp_servers',
        verbose_name='Created by'
    )
    
    # Field tracker for auditing
    tracker = FieldTracker()
    
    class Meta:
        verbose_name = 'MISP Server'
        verbose_name_plural = 'MISP Servers'
        ordering = ['name']
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_sync']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'company'],
                name='unique_misp_server_name_per_company'
            )
        ]
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"


class MISPEvent(CoreModel):
    """
    MISP event model that stores synchronized events from a MISP server.
    Each event belongs to a specific company and is linked to a MISP server.
    """
    uuid = models.UUIDField('UUID', default=uuid.uuid4, editable=False)
    misp_id = models.PositiveIntegerField('MISP ID')
    misp_uuid = models.UUIDField('MISP UUID', unique=True)
    info = models.CharField('Info/Title', max_length=255)
    date = models.DateField('Event Date')
    threat_level_id = models.PositiveSmallIntegerField('Threat Level ID', default=2)
    analysis = models.PositiveSmallIntegerField('Analysis', default=0)
    distribution = models.PositiveSmallIntegerField('Distribution', default=0)
    published = models.BooleanField('Published', default=False)
    tags = ArrayField(
        models.CharField(max_length=100),
        verbose_name='Tags',
        blank=True,
        default=list
    )
    org_name = models.CharField('Organization Name', max_length=255)
    orgc_name = models.CharField('Creator Organization Name', max_length=255)
    timestamp = models.DateTimeField('Timestamp')
    raw_data = models.JSONField('Raw Data', default=dict)
    
    # Links to related alert and incident
    alert = models.ForeignKey(
        'alerts.Alert',
        on_delete=models.SET_NULL,
        related_name='misp_events',
        verbose_name='Related Alert',
        null=True,
        blank=True
    )
    
    incident = models.ForeignKey(
        'incidents.Incident',
        on_delete=models.SET_NULL,
        related_name='misp_events',
        verbose_name='Related Incident',
        null=True,
        blank=True
    )
    
    # Relationships and tenant isolation
    misp_server = models.ForeignKey(
        MISPServer,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='MISP Server'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='misp_events',
        verbose_name='Company'
    )
    
    # Field tracker for auditing
    tracker = FieldTracker()
    
    class Meta:
        verbose_name = 'MISP Event'
        verbose_name_plural = 'MISP Events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['misp_server']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['misp_id']),
            models.Index(fields=['misp_uuid']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['misp_id', 'misp_server'],
                name='unique_event_per_misp_server'
            )
        ]
    
    def __str__(self):
        return f"{self.info} ({self.misp_id}) - {self.company.name}"
    
    def convert_to_alert(self):
        """
        Converts the MISP event to a SentinelIQ Alert.
        """
        from api.v1.misp_sync.tasks import convert_misp_event_to_alert
        
        # Check if already converted
        if self.alert:
            logger.info(f"MISP event {self.info} (ID: {self.id}) already converted to Alert (ID: {self.alert.id})")
            return {
                "status": "already_converted",
                "event_id": self.id,
                "alert_id": self.alert.id
            }
        
        # Start async task
        result = convert_misp_event_to_alert(self.id)
        return result
    
    def convert_to_incident(self):
        """
        Converts the MISP event to a SentinelIQ Incident.
        """
        from api.v1.misp_sync.tasks import convert_misp_event_to_incident
        
        # Check if already converted
        if self.incident:
            logger.info(f"MISP event {self.info} (ID: {self.id}) already converted to Incident (ID: {self.incident.id})")
            return {
                "status": "already_converted",
                "event_id": self.id,
                "incident_id": self.incident.id
            }
        
        # Start async task
        result = convert_misp_event_to_incident(self.id)
        return result


class MISPAttribute(CoreModel):
    """
    MISP attribute model that stores attributes of MISP events.
    Each attribute belongs to a specific MISP event.
    """
    uuid = models.UUIDField('UUID', default=uuid.uuid4, editable=False)
    misp_id = models.PositiveIntegerField('MISP ID')
    misp_uuid = models.UUIDField('MISP UUID', unique=True)
    type = models.CharField('Type', max_length=100)
    category = models.CharField('Category', max_length=100)
    value = models.TextField('Value')
    to_ids = models.BooleanField('To IDS', default=False)
    distribution = models.PositiveSmallIntegerField('Distribution', default=0)
    timestamp = models.DateTimeField('Timestamp')
    comment = models.TextField('Comment', blank=True)
    tags = ArrayField(
        models.CharField(max_length=100),
        verbose_name='Tags',
        blank=True,
        default=list
    )
    raw_data = models.JSONField('Raw Data', default=dict)
    
    # Relationships
    event = models.ForeignKey(
        MISPEvent,
        on_delete=models.CASCADE,
        related_name='attributes',
        verbose_name='MISP Event'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='misp_attributes',
        verbose_name='Company',
        default=None,
        null=True
    )
    
    # Field tracker for auditing
    tracker = FieldTracker()
    
    class Meta:
        verbose_name = 'MISP Attribute'
        verbose_name_plural = 'MISP Attributes'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['type']),
            models.Index(fields=['category']),
            models.Index(fields=['to_ids']),
            models.Index(fields=['misp_id']),
            models.Index(fields=['misp_uuid']),
        ]
    
    def __str__(self):
        return f"{self.type}:{self.value} - {self.event.info}"
    
    def convert_to_observable(self):
        """
        Converts the MISP attribute to a SentinelIQ Observable.
        """
        from api.v1.observables.models import Observable, ObservableType
        
        # Map MISP attribute types to Observable types
        type_mapping = {
            'ip-src': ObservableType.IP,
            'ip-dst': ObservableType.IP,
            'domain': ObservableType.DOMAIN,
            'hostname': ObservableType.HOSTNAME,
            'url': ObservableType.URL,
            'md5': ObservableType.HASH_MD5,
            'sha1': ObservableType.HASH_SHA1,
            'sha256': ObservableType.HASH_SHA256,
            'filename': ObservableType.FILENAME,
            'email': ObservableType.EMAIL,
            'email-src': ObservableType.EMAIL,
            'email-dst': ObservableType.EMAIL,
        }
        
        obs_type = type_mapping.get(self.type)
        
        if not obs_type:
            logger.warning(f"Cannot convert MISP attribute {self.id} of type {self.type} to Observable: type mapping not found")
            return None
        
        # Create observable from attribute
        try:
            observable = Observable.objects.create(
                value=self.value,
                type=obs_type,
                tlp="AMBER",
                is_ioc=self.to_ids,
                source="MISP",
                source_reference=str(self.uuid),
                company=self.company or self.event.company,
                first_seen=self.timestamp,
                last_seen=self.timestamp,
                description=self.comment if self.comment else f"From MISP event: {self.event.info}"
            )
            
            logger.info(f"Converted MISP attribute {self.id} to Observable {observable.id}")
            return observable
            
        except Exception as e:
            logger.exception(f"Error converting MISP attribute {self.id} to Observable: {str(e)}")
            return None


class MISPObject(CoreModel):
    """
    MISP object model that stores objects of MISP events.
    Each object belongs to a specific MISP event.
    """
    uuid = models.UUIDField('UUID', default=uuid.uuid4, editable=False)
    misp_id = models.PositiveIntegerField('MISP ID')
    misp_uuid = models.UUIDField('MISP UUID', unique=True)
    name = models.CharField('Name', max_length=255)
    meta_category = models.CharField('Meta Category', max_length=255)
    description = models.TextField('Description', blank=True)
    template_uuid = models.CharField('Template UUID', max_length=36)
    template_version = models.CharField('Template Version', max_length=10)
    distribution = models.PositiveSmallIntegerField('Distribution', default=0)
    timestamp = models.DateTimeField('Timestamp')
    comment = models.TextField('Comment', blank=True)
    deleted = models.BooleanField('Deleted', default=False)
    raw_data = models.JSONField('Raw Data', default=dict)
    
    # Relationships
    event = models.ForeignKey(
        MISPEvent,
        on_delete=models.CASCADE,
        related_name='objects',
        verbose_name='MISP Event'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='misp_objects',
        verbose_name='Company',
        default=None,
        null=True
    )
    
    # Field tracker for auditing
    tracker = FieldTracker()
    
    class Meta:
        verbose_name = 'MISP Object'
        verbose_name_plural = 'MISP Objects'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['name']),
            models.Index(fields=['meta_category']),
            models.Index(fields=['deleted']),
            models.Index(fields=['misp_id']),
            models.Index(fields=['misp_uuid']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.misp_id}) - {self.event.info}"
