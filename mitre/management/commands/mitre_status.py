import logging
from django.core.management.base import BaseCommand
from django.db.models import Count
from mitre.models import (
    MitreTactic, 
    MitreTechnique, 
    MitreMitigation, 
    MitreRelationship,
    AlertMitreMapping,
    IncidentMitreMapping,
    ObservableMitreMapping
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Shows the status of MITRE ATT&CK data in the database'

    def handle(self, *args, **options):
        """
        Display statistics about MITRE ATT&CK data in the database
        """
        tactics_count = MitreTactic.objects.count()
        techniques_count = MitreTechnique.objects.filter(is_subtechnique=False).count()
        subtechniques_count = MitreTechnique.objects.filter(is_subtechnique=True).count()
        mitigations_count = MitreMitigation.objects.count()
        relationships_count = MitreRelationship.objects.count()
        
        # Count mappings
        alert_mappings = AlertMitreMapping.objects.count()
        incident_mappings = IncidentMitreMapping.objects.count()
        observable_mappings = ObservableMitreMapping.objects.count()
        
        self.stdout.write(self.style.SUCCESS("===== MITRE ATT&CK Import Status ====="))
        self.stdout.write(f"Tactics: {tactics_count}")
        self.stdout.write(f"Techniques: {techniques_count}")
        self.stdout.write(f"Subtechniques: {subtechniques_count}")
        self.stdout.write(f"Mitigations: {mitigations_count}")
        self.stdout.write(f"Relationships: {relationships_count}")
        
        self.stdout.write("\n----- Mappings -----")
        self.stdout.write(f"Alert Mappings: {alert_mappings}")
        self.stdout.write(f"Incident Mappings: {incident_mappings}")
        self.stdout.write(f"Observable Mappings: {observable_mappings}")
        
        if not tactics_count or not techniques_count:
            self.stdout.write(self.style.ERROR("\nWARNING: MITRE ATT&CK data appears to be missing or incomplete"))
            self.stdout.write(self.style.WARNING("Run 'python manage.py import_mitre' to import data"))
        else:
            self.stdout.write(self.style.SUCCESS("\nMITRE ATT&CK data appears to be complete"))
            
        # Get tactics with technique counts
        self.stdout.write("\nTop tactics by number of techniques:")
        tactics_with_counts = MitreTactic.objects.annotate(
            technique_count=Count('techniques')
        ).order_by('-technique_count')[:5]
        
        for tactic in tactics_with_counts:
            self.stdout.write(f"  - {tactic.name} ({tactic.external_id}): {tactic.technique_count} techniques") 