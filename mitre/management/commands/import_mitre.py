import json
import logging
import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from mitre.services import MitreImporter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import MITRE ATT&CK data from enterprise STIX/TAXII or JSON sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default='json',
            help='Source type: json or taxii (default: json)'
        )
        parser.add_argument(
            '--url',
            type=str,
            help='URL to fetch MITRE data from (optional, uses default if not provided)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reimport of all data even if already exists'
        )
        parser.add_argument(
            '--no-relationships',
            action='store_true',
            help='Skip importing relationships'
        )

    def handle(self, *args, **options):
        source_type = options.get('source')
        url = options.get('url')
        force = options.get('force', False)
        skip_relationships = options.get('no_relationships', False)
        
        self.stdout.write(self.style.NOTICE(f"Starting MITRE ATT&CK import using {source_type} source..."))
        
        try:
            importer = MitreImporter()
            
            result = importer.run_full_sync(
                source_type=source_type,
                url=url,
                force=force,
                skip_relationships=skip_relationships
            )
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully imported MITRE ATT&CK data:\n"
                f"- Tactics: {result['tactics']}\n"
                f"- Techniques: {result['techniques']}\n"
                f"- Sub-techniques: {result['subtechniques']}\n"
                f"- Mitigations: {result['mitigations']}\n"
                f"- Relationships: {result['relationships']}"
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importing MITRE ATT&CK data: {str(e)}"))
            logger.exception("Error in import_mitre command")
            raise 