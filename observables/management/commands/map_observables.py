import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from observables.models import Observable


class Command(BaseCommand):
    help = 'Map existing observables to the new MISP-compatible types'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate but do not update the observables'
        )
        parser.add_argument(
            '--export',
            action='store_true',
            help='Export current observables to a CSV file before migration'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='observable_export.csv',
            help='Path to export CSV file (default: observable_export.csv)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        export = options['export']
        output_file = options['output']
        
        if export:
            self.export_observables(output_file)
        
        # Define mapping from old types to new types
        mapping = {
            # Old Type: New Type
            'ip': 'ip',  # IP address can remain the same
            'domain': 'domain',  # Domain can remain the same
            'url': 'url',  # URL can remain the same
            'email': 'email',  # Email can remain the same
            'hash_md5': 'hash-md5',  # Update format to use hyphen
            'hash_sha1': 'hash-sha1',  # Update format to use hyphen
            'hash_sha256': 'hash-sha256',  # Update format to use hyphen
            'filename': 'filename',  # Filename can remain the same
            'filepath': 'filepath',  # Filepath can remain the same
            'registry': 'regkey',  # Rename to match MISP format
            'user_agent': 'user-agent',  # Update format to use hyphen
            'process': 'process',  # Process can remain the same
            'other': 'other',  # Other can remain the same
        }
        
        # Get all observables
        observables = Observable.objects.all()
        total = observables.count()
        
        self.stdout.write(self.style.SUCCESS(f"Found {total} observables to process"))
        
        # If dry run, just show stats
        if dry_run:
            stats = {}
            for old_type, new_type in mapping.items():
                count = Observable.objects.filter(type=old_type).count()
                if count > 0:
                    stats[old_type] = {
                        'count': count,
                        'new_type': new_type
                    }
            
            self.stdout.write(self.style.SUCCESS("DRY RUN - Observables by type:"))
            for old_type, data in stats.items():
                self.stdout.write(f"  {old_type} -> {data['new_type']}: {data['count']} observables")
            
            # Check for any types that aren't in our mapping
            unknown_types = Observable.objects.exclude(
                type__in=mapping.keys()
            ).values('type').distinct()
            
            if unknown_types.exists():
                self.stdout.write(self.style.WARNING("Found unknown types:"))
                for t in unknown_types:
                    count = Observable.objects.filter(type=t['type']).count()
                    self.stdout.write(f"  {t['type']}: {count} observables (not mapped)")
            
            return
        
        # Perform updates in a transaction
        with transaction.atomic():
            updated_count = 0
            skipped_count = 0
            
            for old_type, new_type in mapping.items():
                if old_type == new_type:
                    # Skip if the type hasn't changed
                    count = Observable.objects.filter(type=old_type).count()
                    skipped_count += count
                    self.stdout.write(f"Skipping {count} observables with type '{old_type}' (no change needed)")
                    continue
                
                # Update observables with this type
                count = Observable.objects.filter(type=old_type).update(
                    type=new_type,
                    updated_at=timezone.now()
                )
                
                if count > 0:
                    updated_count += count
                    self.stdout.write(f"Updated {count} observables from '{old_type}' to '{new_type}'")
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully updated {updated_count} observables to new MISP-compatible types "
                f"(skipped {skipped_count} with unchanged types)"
            ))
    
    def export_observables(self, output_file):
        """Export all observables to a CSV file before migration"""
        self.stdout.write(f"Exporting observables to {output_file}...")
        
        try:
            with open(output_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'id', 'type', 'value', 'company_id', 'description', 
                    'is_ioc', 'tags', 'tlp', 'created_at'
                ])
                
                # Write data in batches to avoid memory issues
                batch_size = 1000
                count = 0
                
                for i in range(0, Observable.objects.count(), batch_size):
                    batch = Observable.objects.all()[i:i+batch_size]
                    
                    for observable in batch:
                        writer.writerow([
                            observable.id,
                            observable.type,
                            observable.value,
                            observable.company_id,
                            observable.description,
                            observable.is_ioc,
                            ','.join(observable.tags) if observable.tags else '',
                            observable.tlp,
                            observable.created_at.isoformat()
                        ])
                        
                        count += 1
                
                self.stdout.write(self.style.SUCCESS(f"Exported {count} observables to {output_file}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error exporting observables: {str(e)}"))
            raise 