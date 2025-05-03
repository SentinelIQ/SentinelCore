from django.db import models
from django.contrib.postgres.fields import ArrayField
from api.core.models import CoreModel
from alerts.models import Alert
from incidents.models import Incident
from observables.models import Observable


class MitreTactic(CoreModel):
    """
    Represents a MITRE ATT&CK Tactic (e.g., Initial Access, Execution, etc.)
    """
    external_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    class Meta:
        ordering = ['name']
        verbose_name = 'MITRE Tactic'
        verbose_name_plural = 'MITRE Tactics'
    
    def __str__(self):
        return f"{self.external_id}: {self.name}"


class MitreTechnique(CoreModel):
    """
    Represents a MITRE ATT&CK Technique or Sub-technique
    """
    external_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    tactics = models.ManyToManyField(MitreTactic, related_name='techniques')
    platforms = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    detection = models.TextField(blank=True, null=True)
    is_subtechnique = models.BooleanField(default=False)
    parent_technique = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='subtechniques'
    )
    
    # Integration with other entities
    alerts = models.ManyToManyField(
        Alert, 
        through='AlertMitreMapping',
        related_name='mitre_techniques',
        blank=True
    )
    incidents = models.ManyToManyField(
        Incident, 
        through='IncidentMitreMapping',
        related_name='mitre_techniques',
        blank=True
    )
    observables = models.ManyToManyField(
        Observable, 
        through='ObservableMitreMapping',
        related_name='mitre_techniques',
        blank=True
    )
    
    class Meta:
        ordering = ['external_id']
        verbose_name = 'MITRE Technique'
        verbose_name_plural = 'MITRE Techniques'
    
    def __str__(self):
        return f"{self.external_id}: {self.name}"


class MitreMitigation(CoreModel):
    """
    Represents a MITRE ATT&CK Mitigation
    """
    external_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    techniques = models.ManyToManyField(
        MitreTechnique, 
        through='MitreMitigationMapping',
        related_name='mitigations',
        blank=True
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'MITRE Mitigation'
        verbose_name_plural = 'MITRE Mitigations'
    
    def __str__(self):
        return f"{self.external_id}: {self.name}"


class MitreRelationship(CoreModel):
    """
    Represents relationships between MITRE ATT&CK entities
    """
    source_id = models.CharField(max_length=255)
    target_id = models.CharField(max_length=255)
    relationship_type = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('source_id', 'target_id', 'relationship_type')
        verbose_name = 'MITRE Relationship'
        verbose_name_plural = 'MITRE Relationships'
    
    def __str__(self):
        return f"{self.source_id} {self.relationship_type} {self.target_id}"


class MitreMitigationMapping(CoreModel):
    """
    Mapping between MITRE techniques and mitigations
    """
    technique = models.ForeignKey(MitreTechnique, on_delete=models.CASCADE)
    mitigation = models.ForeignKey(MitreMitigation, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('technique', 'mitigation')
        verbose_name = 'MITRE Mitigation Mapping'
        verbose_name_plural = 'MITRE Mitigation Mappings'


class AlertMitreMapping(CoreModel):
    """
    Mapping between Alerts and MITRE techniques
    """
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE)
    technique = models.ForeignKey(MitreTechnique, on_delete=models.CASCADE)
    confidence = models.IntegerField(default=50)  # 0-100 confidence score
    auto_detected = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('alert', 'technique')
        verbose_name = 'Alert MITRE Mapping'
        verbose_name_plural = 'Alert MITRE Mappings'


class IncidentMitreMapping(CoreModel):
    """
    Mapping between Incidents and MITRE techniques
    """
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    technique = models.ForeignKey(MitreTechnique, on_delete=models.CASCADE)
    confidence = models.IntegerField(default=100)  # 0-100 confidence score
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('incident', 'technique')
        verbose_name = 'Incident MITRE Mapping'
        verbose_name_plural = 'Incident MITRE Mappings'


class ObservableMitreMapping(CoreModel):
    """
    Mapping between Observables and MITRE techniques
    """
    observable = models.ForeignKey(Observable, on_delete=models.CASCADE)
    technique = models.ForeignKey(MitreTechnique, on_delete=models.CASCADE)
    confidence = models.IntegerField(default=70)  # 0-100 confidence score
    auto_detected = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('observable', 'technique')
        verbose_name = 'Observable MITRE Mapping'
        verbose_name_plural = 'Observable MITRE Mappings'
