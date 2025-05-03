import json
import logging
import requests
from django.db import transaction
from django.conf import settings
from mitre.models import (
    MitreTactic, 
    MitreTechnique, 
    MitreMitigation, 
    MitreRelationship
)

logger = logging.getLogger(__name__)


class MitreImporter:
    """
    Service to import MITRE ATT&CK data from STIX/TAXII or JSON sources
    """
    DEFAULT_JSON_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
    
    def __init__(self):
        self.stats = {
            "tactics": 0,
            "techniques": 0,
            "subtechniques": 0,
            "mitigations": 0,
            "relationships": 0
        }
    
    def run_full_sync(self, source_type="json", url=None, force=False, skip_relationships=False):
        """
        Run a full sync of MITRE ATT&CK data
        
        Args:
            source_type: 'json' or 'taxii'
            url: URL to fetch data from (optional)
            force: Force reimport of all data
            skip_relationships: Skip importing relationships
            
        Returns:
            Dict with statistics on imported items
        """
        logger.info(f"Running MITRE ATT&CK full sync using {source_type} source")
        
        # Reset stats
        self.stats = {
            "tactics": 0,
            "techniques": 0,
            "subtechniques": 0,
            "mitigations": 0,
            "relationships": 0
        }
        
        # Fetch data based on source type
        if source_type == "json":
            data = self._fetch_json_data(url)
        elif source_type == "taxii":
            data = self._fetch_taxii_data(url)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        # Process data within a transaction
        with transaction.atomic():
            # If force is True, delete all existing data
            if force:
                logger.warning("Deleting all existing MITRE ATT&CK data")
                MitreRelationship.objects.all().delete()
                MitreMitigation.objects.all().delete()
                MitreTechnique.objects.all().delete()
                MitreTactic.objects.all().delete()
            
            # Process objects by type
            self._process_tactics(data)
            self._process_techniques(data)
            self._process_mitigations(data)
            
            # Process relationships if not skipped
            if not skip_relationships:
                self._process_relationships(data)
        
        logger.info(f"MITRE ATT&CK sync completed: {self.stats}")
        return self.stats
    
    def _fetch_json_data(self, url=None):
        """Fetch MITRE ATT&CK data from JSON source"""
        target_url = url or self.DEFAULT_JSON_URL
        logger.info(f"Fetching MITRE ATT&CK data from {target_url}")
        
        try:
            response = requests.get(target_url, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception(f"Error fetching MITRE ATT&CK data: {str(e)}")
            raise
    
    def _fetch_taxii_data(self, url=None):
        """Fetch MITRE ATT&CK data from TAXII source (stub)"""
        # This is a placeholder. TAXII implementation requires additional libraries
        # such as taxii2-client and would be more complex
        logger.warning("TAXII data fetching not fully implemented")
        raise NotImplementedError("TAXII data fetching not implemented")
    
    def _process_tactics(self, data):
        """Process and import tactics from STIX data"""
        logger.info("Processing MITRE ATT&CK tactics")
        
        for obj in data.get("objects", []):
            if obj.get("type") == "x-mitre-tactic" and obj.get("name"):
                external_id = obj.get("external_references", [{}])[0].get("external_id", "")
                
                if not external_id:
                    continue
                
                tactic, created = MitreTactic.objects.update_or_create(
                    external_id=external_id,
                    defaults={
                        "name": obj.get("name", ""),
                        "description": obj.get("description", "")
                    }
                )
                
                if created:
                    self.stats["tactics"] += 1
    
    def _process_techniques(self, data):
        """Process and import techniques from STIX data"""
        logger.info("Processing MITRE ATT&CK techniques")
        
        # First, create all techniques
        for obj in data.get("objects", []):
            if obj.get("type") == "attack-pattern" and obj.get("name"):
                external_references = obj.get("external_references", [])
                if not external_references:
                    continue
                
                external_id = external_references[0].get("external_id", "")
                if not external_id:
                    continue
                
                # Determine if this is a sub-technique
                is_subtechnique = "." in external_id
                parent_external_id = None
                
                if is_subtechnique:
                    parent_external_id = external_id.split(".")[0]
                
                # Get platforms
                platforms = obj.get("x_mitre_platforms", [])
                
                # Create or update technique
                technique, created = MitreTechnique.objects.update_or_create(
                    external_id=external_id,
                    defaults={
                        "name": obj.get("name", ""),
                        "description": obj.get("description", ""),
                        "platforms": platforms,
                        "detection": obj.get("x_mitre_detection", ""),
                        "is_subtechnique": is_subtechnique
                    }
                )
                
                # Link to tactics based on kill_chain_phases
                kill_chain_phases = obj.get("kill_chain_phases", [])
                for phase in kill_chain_phases:
                    phase_name = phase.get("phase_name", "")
                    if phase_name:
                        tactics = MitreTactic.objects.filter(name__iexact=phase_name)
                        for tactic in tactics:
                            technique.tactics.add(tactic)
                
                if created:
                    if is_subtechnique:
                        self.stats["subtechniques"] += 1
                    else:
                        self.stats["techniques"] += 1
        
        # Now link sub-techniques to parent techniques
        for obj in data.get("objects", []):
            if obj.get("type") == "attack-pattern" and "." in obj.get("external_references", [{}])[0].get("external_id", ""):
                external_id = obj.get("external_references", [{}])[0].get("external_id", "")
                parent_external_id = external_id.split(".")[0]
                
                try:
                    technique = MitreTechnique.objects.get(external_id=external_id)
                    parent = MitreTechnique.objects.get(external_id=parent_external_id)
                    technique.parent_technique = parent
                    technique.save()
                except MitreTechnique.DoesNotExist:
                    logger.warning(f"Could not link sub-technique {external_id} to parent {parent_external_id}")
    
    def _process_mitigations(self, data):
        """Process and import mitigations from STIX data"""
        logger.info("Processing MITRE ATT&CK mitigations")
        
        for obj in data.get("objects", []):
            if obj.get("type") == "course-of-action" and obj.get("name"):
                external_references = obj.get("external_references", [])
                if not external_references:
                    continue
                
                external_id = external_references[0].get("external_id", "")
                if not external_id:
                    continue
                
                mitigation, created = MitreMitigation.objects.update_or_create(
                    external_id=external_id,
                    defaults={
                        "name": obj.get("name", ""),
                        "description": obj.get("description", "")
                    }
                )
                
                if created:
                    self.stats["mitigations"] += 1
    
    def _process_relationships(self, data):
        """Process and import relationships between MITRE objects"""
        logger.info("Processing MITRE ATT&CK relationships")
        
        for obj in data.get("objects", []):
            if obj.get("type") == "relationship":
                source_ref = obj.get("source_ref", "")
                target_ref = obj.get("target_ref", "")
                relationship_type = obj.get("relationship_type", "")
                
                if not (source_ref and target_ref and relationship_type):
                    continue
                
                # Process mitigation relationships
                if relationship_type == "mitigates" and source_ref.startswith("course-of-action"):
                    self._link_mitigation_to_technique(source_ref, target_ref, data)
                
                # Create generic relationship record
                relationship, created = MitreRelationship.objects.update_or_create(
                    source_id=source_ref,
                    target_id=target_ref,
                    relationship_type=relationship_type,
                    defaults={
                        "description": obj.get("description", "")
                    }
                )
                
                if created:
                    self.stats["relationships"] += 1
    
    def _link_mitigation_to_technique(self, mitigation_ref, technique_ref, data):
        """Link a mitigation to a technique based on STIX references"""
        try:
            # Find the external IDs
            mitigation_obj = next((obj for obj in data.get("objects", []) 
                                  if obj.get("id") == mitigation_ref), None)
            technique_obj = next((obj for obj in data.get("objects", []) 
                                  if obj.get("id") == technique_ref), None)
            
            if not (mitigation_obj and technique_obj):
                return
            
            mitigation_external_id = mitigation_obj.get("external_references", [{}])[0].get("external_id", "")
            technique_external_id = technique_obj.get("external_references", [{}])[0].get("external_id", "")
            
            if not (mitigation_external_id and technique_external_id):
                return
            
            # Get or create the MitreMitigationMapping
            mitigation = MitreMitigation.objects.filter(external_id=mitigation_external_id).first()
            technique = MitreTechnique.objects.filter(external_id=technique_external_id).first()
            
            if mitigation and technique:
                mitigation.techniques.add(technique)
        except Exception as e:
            logger.warning(f"Error linking mitigation to technique: {str(e)}")
            # No need to raise, just log the warning 