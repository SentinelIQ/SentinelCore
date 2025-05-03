import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from companies.models import Company
from incidents.models import Incident
from api.v1.observables.enums import ObservableCategoryEnum, ObservableTypeEnum, ObservableTLPEnum, ObservableRelationTypeEnum
from api.core.utils.enum_utils import enum_to_choices
from api.core.models import CoreModel

User = get_user_model()


class Observable(CoreModel):
    """
    Observable model (also known as artifacts or IOCs) for the Sentineliq system.
    MISP-compatible implementation for storing indicators of compromise.
    Can be associated with alerts, incidents, or both.
    """
    # Primary fields
    type = models.CharField(
        'Type',
        max_length=50,
        choices=enum_to_choices(ObservableTypeEnum)
    )
    value = models.TextField('Value')
    description = models.TextField('Description', blank=True)
    
    # MISP compatibility fields
    category = models.CharField(
        'Category',
        max_length=50,
        choices=enum_to_choices(ObservableCategoryEnum),
        default=ObservableCategoryEnum.OTHER.value
    )
    first_seen = models.DateTimeField('First seen', null=True, blank=True)
    last_seen = models.DateTimeField('Last seen', null=True, blank=True)
    
    # Classification fields
    tags = ArrayField(
        models.CharField(max_length=50),
        verbose_name='Tags',
        blank=True,
        default=list
    )
    tlp = models.IntegerField(
        'TLP (Traffic Light Protocol)',
        choices=enum_to_choices(ObservableTLPEnum),
        default=ObservableTLPEnum.AMBER.value
    )
    source = models.CharField(
        'Source',
        max_length=100,
        blank=True,
        help_text='Source of this observable (feed, product, analyst, etc.)'
    )
    confidence = models.IntegerField(
        'Confidence Score',
        default=50,
        help_text='Confidence score (0-100)'
    )
    
    # Relationships
    alert = models.ForeignKey(
        'alerts.Alert',  # Use string reference instead of direct import
        on_delete=models.CASCADE,
        related_name='direct_observables',
        verbose_name='Related Alert',
        null=True,
        blank=True
    )
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='direct_observables',
        verbose_name='Related Incident',
        null=True,
        blank=True
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='observables',
        verbose_name='Company'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_observables',
        verbose_name='Created by'
    )
    
    # Related observables 
    related_observables = models.ManyToManyField(
        'self',
        through='ObservableRelationship',
        symmetrical=False,
        related_name='related_to',
        blank=True,
        verbose_name='Related Observables'
    )
    
    # Enrichment data
    enrichment_data = models.JSONField(
        'Enrichment Data',
        default=dict,
        blank=True,
        help_text='Additional data from enrichment services'
    )
    
    # IOC status
    is_ioc = models.BooleanField(
        'Is IOC',
        default=False,
        help_text='Whether this observable is confirmed as an Indicator of Compromise'
    )
    is_false_positive = models.BooleanField(
        'Is False Positive',
        default=False,
        help_text='Whether this observable is a known false positive'
    )
    
    class Meta:
        verbose_name = 'Observable'
        verbose_name_plural = 'Observables'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'type']),
            models.Index(fields=['company', 'category']),
            models.Index(fields=['alert']),
            models.Index(fields=['incident']),
            models.Index(fields=['is_ioc']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['type', 'value', 'company'],
                name='unique_observable_per_company'
            )
        ]
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.value}"
    
    def clean(self):
        """
        Validate model constraints that involve multiple fields.
        """
        super().clean()
        
        # Validate that alert and incident are related when both are provided
        if self.alert and self.incident:
            # Check if alert is related to the incident
            if not self.incident.related_alerts.filter(id=self.alert.id).exists():
                raise ValidationError({
                    'alert': 'The alert must be related to the incident when both are specified.'
                })
        
        # Validate company consistency
        if self.alert and self.company != self.alert.company:
            raise ValidationError({
                'company': 'The observable company must match the alert company.'
            })
            
        if self.incident and self.company != self.incident.company:
            raise ValidationError({
                'company': 'The observable company must match the incident company.'
            })
            
        # If both alert and incident are None, ensure created_by has permission on company
        if not self.alert and not self.incident:
            if hasattr(self.created_by, 'company') and self.created_by.company != self.company and not self.created_by.is_superuser:
                raise ValidationError({
                    'created_by': 'User can only create observables for their own company.'
                })
                
        # Validate confidence score range
        if not 0 <= self.confidence <= 100:
            raise ValidationError({
                'confidence': 'Confidence score must be between 0 and 100.'
            })
    
    def save(self, *args, **kwargs):
        """
        Override save method to ensure consistency in relationships.
        """
        # If alert is provided but company is not, use alert's company
        if self.alert and not self.company_id:
            self.company = self.alert.company
            
        # If incident is provided but company is not, use incident's company
        elif self.incident and not self.company_id:
            self.company = self.incident.company
            
        # Run validation
        self.full_clean()
        
        super().save(*args, **kwargs)
    
    @classmethod
    def deduplicate(cls, observable_data, company):
        """
        Check if an observable with the same type and value already exists.
        
        Args:
            observable_data (dict): Dictionary containing 'type' and 'value'
            company (Company): Company to check against
            
        Returns:
            tuple: (observable, created) - whether the observable exists or was created
        """
        # Extract type and value from the data
        obs_type = observable_data.get('type')
        obs_value = observable_data.get('value')
        
        if not obs_type or not obs_value:
            return None, False
            
        try:
            return cls.objects.get(
                type=obs_type,
                value=obs_value,
                company=company
            ), False
        except cls.DoesNotExist:
            return None, True


class ObservableRelationship(CoreModel):
    """
    Model for tracking relationships between Observables.
    """
    source = models.ForeignKey(
        Observable,
        on_delete=models.CASCADE,
        related_name='relationship_source',
        verbose_name='Source Observable'
    )
    target = models.ForeignKey(
        Observable,
        on_delete=models.CASCADE,
        related_name='relationship_target',
        verbose_name='Target Observable'
    )
    relationship_type = models.CharField(
        'Relationship Type',
        max_length=50,
        choices=enum_to_choices(ObservableRelationTypeEnum),
        default=ObservableRelationTypeEnum.CONNECTED.value
    )
    description = models.TextField('Description', blank=True)
    
    # For tenant isolation
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='observable_relationships',
        verbose_name='Company'
    )
    
    # Extra data
    tags = ArrayField(
        models.CharField(max_length=50),
        verbose_name='Tags',
        blank=True,
        default=list
    )
    metadata = models.JSONField(
        'Metadata',
        default=dict,
        blank=True
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_relationships',
        verbose_name='Created by'
    )
    
    class Meta:
        verbose_name = 'Observable Relationship'
        verbose_name_plural = 'Observable Relationships'
        unique_together = ['source', 'target', 'relationship_type']
    
    def __str__(self):
        return f"{self.source} {self.get_relationship_type_display()} {self.target}"
    
    def clean(self):
        """
        Validate model constraints.
        """
        super().clean()
        
        # Validate companies match
        if self.source.company != self.target.company:
            raise ValidationError(
                "Related observables must belong to the same company."
            )
            
        # Set company same as source observable
        self.company = self.source.company
    
    def save(self, *args, **kwargs):
        """
        Override to ensure company matches source observable.
        """
        # Ensure company matches source observable
        self.company = self.source.company
        
        # Run validation
        self.full_clean()
        
        super().save(*args, **kwargs) 