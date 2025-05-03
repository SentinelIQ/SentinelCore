import csv
import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from companies.models import Company
from observables.models import Observable, ObservableCategory


class Command(BaseCommand):
    help = 'Import observables from various formats (CSV, MISP JSON, STIX)'

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            help='Path to the file containing observables to import'
        )
        parser.add_argument(
            '--company',
            required=True,
            help='Company ID to associate the observables with'
        )
        parser.add_argument(
            '--format',
            choices=['csv', 'misp', 'stix'],
            default='csv',
            help='Format of the import file (default: csv)'
        )
        parser.add_argument(
            '--category',
            help='Default category for imported observables (if not specified in file)'
        )
        parser.add_argument(
            '--source',
            default='import',
            help='Source of the observables (default: import)'
        )
        parser.add_argument(
            '--user',
            required=True,
            help='User ID to set as created_by'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate but do not import the data'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        format_type = options['format']
        company_id = options['company']
        source = options['source']
        user_id = options['user']
        dry_run = options['dry_run']
        default_category = options.get('category', ObservableCategory.OTHER)
        
        # Validate file exists
        if not os.path.exists(file_path):
            raise CommandError(f"File does not exist: {file_path}")
        
        # Validate company exists
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            raise CommandError(f"Company with ID {company_id} does not exist")
        
        # Validate user exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise CommandError(f"User with ID {user_id} does not exist")
        
        # Import based on format
        if format_type == 'csv':
            self.import_from_csv(file_path, company, user, source, default_category, dry_run)
        elif format_type == 'misp':
            self.import_from_misp(file_path, company, user, source, dry_run)
        elif format_type == 'stix':
            self.import_from_stix(file_path, company, user, source, dry_run)
    
    def import_from_csv(self, file_path, company, user, source, default_category, dry_run):
        """Import observables from a CSV file"""
        self.stdout.write(self.style.SUCCESS(f"Importing observables from CSV: {file_path}"))
        
        # CSV should have columns: value,type,description,tags,tlp,category,is_ioc
        # Optional columns: first_seen,last_seen,confidence,source
        
        processed = 0
        created = 0
        updated = 0
        errors = 0
        
        try:
            with open(file_path, 'r') as csv_file:
                reader = csv.DictReader(csv_file)
                
                # Validate required columns
                required_fields = ['value', 'type']
                for field in required_fields:
                    if field not in reader.fieldnames:
                        raise CommandError(f"CSV file missing required column: {field}")
                
                # Start transaction for all imports
                with transaction.atomic():
                    for row in reader:
                        processed += 1
                        
                        # Skip empty rows
                        if not row.get('value'):
                            continue
                            
                        try:
                            # Prepare data
                            value = row.get('value', '').strip()
                            obs_type = row.get('type', '').strip()
                            
                            # Skip if value or type is missing
                            if not value or not obs_type:
                                self.stdout.write(self.style.WARNING(
                                    f"Row {processed}: Skipping - missing value or type"
                                ))
                                errors += 1
                                continue
                            
                            # Prepare tags
                            tags = []
                            if 'tags' in row and row['tags']:
                                # Handle comma-separated or JSON array format
                                if row['tags'].startswith('['):
                                    try:
                                        tags = json.loads(row['tags'])
                                    except json.JSONDecodeError:
                                        tags = [t.strip() for t in row['tags'].split(',')]
                                else:
                                    tags = [t.strip() for t in row['tags'].split(',')]
                            
                            # Add source to tags
                            if source and source not in tags:
                                tags.append(source)
                            
                            # Get or set TLP
                            tlp = row.get('tlp', '2')  # Default to AMBER (2)
                            try:
                                tlp = int(tlp)
                                if tlp not in range(4):  # Check if in valid range (0-3)
                                    tlp = 2  # Default to AMBER if invalid
                            except ValueError:
                                # Try to map TLP strings to values
                                tlp_map = {'white': 0, 'green': 1, 'amber': 2, 'red': 3}
                                tlp = tlp_map.get(tlp.lower(), 2)
                                
                            # Parse category
                            category = row.get('category', default_category)
                            if not hasattr(ObservableCategory, category.upper()):
                                # If not a valid category enum value, use default
                                category = default_category
                            
                            # Check for dates
                            first_seen = None
                            if 'first_seen' in row and row['first_seen']:
                                try:
                                    first_seen = datetime.fromisoformat(row['first_seen'])
                                except ValueError:
                                    # Try different formats
                                    try:
                                        first_seen = datetime.strptime(row['first_seen'], '%Y-%m-%d')
                                    except ValueError:
                                        pass
                            
                            last_seen = None
                            if 'last_seen' in row and row['last_seen']:
                                try:
                                    last_seen = datetime.fromisoformat(row['last_seen'])
                                except ValueError:
                                    # Try different formats
                                    try:
                                        last_seen = datetime.strptime(row['last_seen'], '%Y-%m-%d')
                                    except ValueError:
                                        pass
                            
                            # Get confidence
                            confidence = 50  # Default medium confidence
                            if 'confidence' in row and row['confidence']:
                                try:
                                    confidence = int(row['confidence'])
                                    if confidence < 0 or confidence > 100:
                                        confidence = 50
                                except ValueError:
                                    pass
                            
                            # Create observable data dict
                            observable_data = {
                                'value': value,
                                'type': obs_type,
                                'description': row.get('description', ''),
                                'tags': tags,
                                'tlp': tlp,
                                'category': category,
                                'is_ioc': row.get('is_ioc', '').lower() in ('true', 'yes', '1'),
                                'source': row.get('source', source),
                                'confidence': confidence,
                                'first_seen': first_seen,
                                'last_seen': last_seen
                            }
                            
                            if dry_run:
                                self.stdout.write(f"DRY RUN: Would import {obs_type}: {value}")
                                created += 1
                                continue
                            
                            # Try to get existing observable
                            observable, new = Observable.objects.get_or_create(
                                type=obs_type,
                                value=value,
                                company=company,
                                defaults={
                                    'description': observable_data['description'],
                                    'tags': observable_data['tags'],
                                    'tlp': observable_data['tlp'],
                                    'category': observable_data['category'],
                                    'is_ioc': observable_data['is_ioc'],
                                    'source': observable_data['source'],
                                    'confidence': observable_data['confidence'],
                                    'first_seen': observable_data['first_seen'],
                                    'last_seen': observable_data['last_seen'],
                                    'created_by': user
                                }
                            )
                            
                            if new:
                                created += 1
                                self.stdout.write(f"Created observable {obs_type}: {value}")
                            else:
                                # Update existing
                                updated += 1
                                # Extend tags rather than replace
                                for tag in observable_data['tags']:
                                    if tag not in observable.tags:
                                        observable.tags.append(tag)
                                
                                # Update other fields if provided
                                if observable_data['description']:
                                    observable.description = observable_data['description']
                                
                                # Take the earliest first_seen date
                                if observable_data['first_seen'] and (
                                    not observable.first_seen or 
                                    observable_data['first_seen'] < observable.first_seen
                                ):
                                    observable.first_seen = observable_data['first_seen']
                                
                                # Take the latest last_seen date
                                if observable_data['last_seen'] and (
                                    not observable.last_seen or
                                    observable_data['last_seen'] > observable.last_seen
                                ):
                                    observable.last_seen = observable_data['last_seen']
                                
                                # Max confidence
                                if observable_data['confidence'] > observable.confidence:
                                    observable.confidence = observable_data['confidence']
                                
                                # Mark as IOC if flagged
                                if observable_data['is_ioc']:
                                    observable.is_ioc = True
                                
                                observable.save()
                                self.stdout.write(f"Updated observable {obs_type}: {value}")
                                
                        except Exception as e:
                            errors += 1
                            self.stdout.write(self.style.ERROR(
                                f"Row {processed}: Error - {str(e)}"
                            ))
                            
                    if dry_run:
                        # Rollback the transaction in dry run mode
                        transaction.set_rollback(True)
                        self.stdout.write(self.style.SUCCESS(
                            f"DRY RUN: Would import {processed} observables"
                        ))
                    else:
                        self.stdout.write(self.style.SUCCESS(
                            f"Imported {created} new and updated {updated} existing observables "
                            f"with {errors} errors"
                        ))
                        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Import failed: {str(e)}"))
            raise CommandError(f"Failed to import from CSV: {str(e)}")
    
    def import_from_misp(self, file_path, company, user, source, dry_run):
        """Import observables from a MISP JSON export"""
        self.stdout.write(self.style.SUCCESS(f"Importing observables from MISP JSON: {file_path}"))
        
        processed = 0
        created = 0
        updated = 0
        errors = 0
        
        try:
            with open(file_path, 'r') as json_file:
                misp_data = json.load(json_file)
                
                # MISP exports can contain an event or multiple events
                events = misp_data.get('response', [])
                
                # If it's a single event response
                if isinstance(events, dict) and 'Event' in events:
                    events = [events]
                
                # Start transaction for all imports
                with transaction.atomic():
                    for event in events:
                        event_data = event.get('Event', {})
                        event_id = event_data.get('id', 'unknown')
                        event_info = event_data.get('info', 'MISP Event')
                        event_tags = []
                        
                        # Extract event tags
                        for tag_data in event_data.get('Tag', []):
                            tag_name = tag_data.get('name', '')
                            if tag_name and tag_name not in event_tags:
                                event_tags.append(tag_name.replace('misp-galaxy:', ''))
                        
                        # Add event source
                        event_source = f"MISP:{event_id}"
                        
                        # Process attributes
                        for attribute in event_data.get('Attribute', []):
                            processed += 1
                            
                            try:
                                # Extract attribute data
                                attr_type = attribute.get('type', '')
                                attr_value = attribute.get('value', '')
                                attr_category = attribute.get('category', '')
                                
                                # Skip if missing required fields
                                if not attr_type or not attr_value:
                                    errors += 1
                                    continue
                                    
                                # Map MISP attribute type to our Observable type
                                obs_type = self._map_misp_type(attr_type)
                                if not obs_type:
                                    # Skip unsupported types
                                    self.stdout.write(self.style.WARNING(
                                        f"Skipping unsupported MISP type: {attr_type}"
                                    ))
                                    errors += 1
                                    continue
                                
                                # Map MISP category to our category
                                obs_category = self._map_misp_category(attr_category)
                                
                                # Get attribute tags
                                attr_tags = event_tags.copy()  # Start with event tags
                                for tag_data in attribute.get('Tag', []):
                                    tag_name = tag_data.get('name', '')
                                    if tag_name and tag_name not in attr_tags:
                                        attr_tags.append(tag_name.replace('misp-galaxy:', ''))
                                
                                # Add source to tags
                                if source and source not in attr_tags:
                                    attr_tags.append(source)
                                if event_source not in attr_tags:
                                    attr_tags.append(event_source)
                                
                                # Add event info to description
                                description = attribute.get('comment', '')
                                if event_info and not description:
                                    description = f"From MISP event: {event_info}"
                                elif event_info:
                                    description = f"{description} (Event: {event_info})"
                                
                                # Get dates
                                first_seen = None
                                if attribute.get('first_seen'):
                                    try:
                                        first_seen = datetime.fromisoformat(attribute['first_seen'])
                                    except (ValueError, TypeError):
                                        pass
                                
                                if not first_seen and attribute.get('timestamp'):
                                    try:
                                        first_seen = datetime.fromtimestamp(int(attribute['timestamp']))
                                    except (ValueError, TypeError):
                                        pass
                                
                                # Calculate TLP
                                tlp = 2  # Default AMBER
                                for tag in attr_tags:
                                    if tag.startswith('tlp:'):
                                        tlp_value = tag.split(':')[1].lower()
                                        tlp_map = {'white': 0, 'green': 1, 'amber': 2, 'red': 3}
                                        if tlp_value in tlp_map:
                                            tlp = tlp_map[tlp_value]
                                            break
                                
                                # Prepare observable data
                                observable_data = {
                                    'value': attr_value,
                                    'type': obs_type,
                                    'description': description,
                                    'tags': attr_tags,
                                    'tlp': tlp,
                                    'category': obs_category,
                                    'is_ioc': attribute.get('to_ids', False),
                                    'source': event_source,
                                    'confidence': 70,  # Default medium-high for MISP data
                                    'first_seen': first_seen,
                                    'last_seen': None
                                }
                                
                                if dry_run:
                                    self.stdout.write(f"DRY RUN: Would import {obs_type}: {attr_value}")
                                    created += 1
                                    continue
                                
                                # Try to get existing observable
                                observable, new = Observable.objects.get_or_create(
                                    type=obs_type,
                                    value=attr_value,
                                    company=company,
                                    defaults={
                                        'description': observable_data['description'],
                                        'tags': observable_data['tags'],
                                        'tlp': observable_data['tlp'],
                                        'category': observable_data['category'],
                                        'is_ioc': observable_data['is_ioc'],
                                        'source': observable_data['source'],
                                        'confidence': observable_data['confidence'],
                                        'first_seen': observable_data['first_seen'],
                                        'last_seen': observable_data['last_seen'],
                                        'created_by': user
                                    }
                                )
                                
                                if new:
                                    created += 1
                                    self.stdout.write(f"Created observable {obs_type}: {attr_value}")
                                else:
                                    # Update existing
                                    updated += 1
                                    # Extend tags rather than replace
                                    for tag in observable_data['tags']:
                                        if tag not in observable.tags:
                                            observable.tags.append(tag)
                                    
                                    # Update other fields if provided
                                    if observable_data['description']:
                                        observable.description = observable_data['description']
                                    
                                    # Take the earliest first_seen date
                                    if observable_data['first_seen'] and (
                                        not observable.first_seen or 
                                        observable_data['first_seen'] < observable.first_seen
                                    ):
                                        observable.first_seen = observable_data['first_seen']
                                    
                                    # Max confidence
                                    if observable_data['confidence'] > observable.confidence:
                                        observable.confidence = observable_data['confidence']
                                    
                                    # Mark as IOC if flagged
                                    if observable_data['is_ioc']:
                                        observable.is_ioc = True
                                    
                                    observable.save()
                                    self.stdout.write(f"Updated observable {obs_type}: {attr_value}")
                            
                            except Exception as e:
                                errors += 1
                                self.stdout.write(self.style.ERROR(
                                    f"Error processing MISP attribute: {str(e)}"
                                ))
                
                if dry_run:
                    # Rollback the transaction in dry run mode
                    transaction.set_rollback(True)
                    self.stdout.write(self.style.SUCCESS(
                        f"DRY RUN: Would import {processed} observables from MISP"
                    ))
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f"Imported {created} new and updated {updated} existing observables "
                        f"from MISP with {errors} errors"
                    ))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"MISP import failed: {str(e)}"))
            raise CommandError(f"Failed to import from MISP: {str(e)}")
    
    def import_from_stix(self, file_path, company, user, source, dry_run):
        """Import observables from a STIX JSON file"""
        self.stdout.write(self.style.SUCCESS(f"Importing observables from STIX: {file_path}"))
        self.stdout.write(self.style.WARNING("STIX import is currently limited to basic indicators"))
        
        processed = 0
        created = 0
        updated = 0
        errors = 0
        
        try:
            with open(file_path, 'r') as json_file:
                stix_data = json.load(json_file)
                
                # STIX 2.x format - look for objects
                objects = stix_data.get('objects', [])
                
                # Start transaction for all imports
                with transaction.atomic():
                    for obj in objects:
                        # We mainly care about indicators in STIX
                        if obj.get('type') != 'indicator':
                            continue
                            
                        processed += 1
                        
                        try:
                            # Get pattern from indicator
                            pattern = obj.get('pattern', '')
                            if not pattern:
                                errors += 1
                                continue
                                
                            # Extract observable value from pattern
                            # Example: [url:value = 'http://example.com']
                            obs_type, obs_value = self._parse_stix_pattern(pattern)
                            
                            if not obs_type or not obs_value:
                                self.stdout.write(self.style.WARNING(
                                    f"Skipping unparseable STIX pattern: {pattern}"
                                ))
                                errors += 1
                                continue
                            
                            # Extract other indicator data
                            name = obj.get('name', '')
                            description = obj.get('description', '')
                            
                            if name and not description:
                                description = name
                            elif name:
                                description = f"{name}: {description}"
                                
                            # Get created date
                            first_seen = None
                            if obj.get('created'):
                                try:
                                    first_seen = datetime.fromisoformat(obj['created'].replace('Z', '+00:00'))
                                except (ValueError, TypeError):
                                    pass
                            
                            # Get modified date
                            last_seen = None
                            if obj.get('modified'):
                                try:
                                    last_seen = datetime.fromisoformat(obj['modified'].replace('Z', '+00:00'))
                                except (ValueError, TypeError):
                                    pass
                            
                            # Get labels as tags
                            tags = obj.get('labels', [])
                            
                            # Add source to tags
                            if source and source not in tags:
                                tags.append(source)
                            tags.append('stix2')
                            
                            # Set default category based on pattern type
                            category = ObservableCategory.NETWORK_ACTIVITY
                            if obs_type.startswith('hash'):
                                category = ObservableCategory.ARTIFACTS
                            elif obs_type in ('process', 'windows-registry-key'):
                                category = ObservableCategory.PAYLOAD_INSTALLATION
                            
                            # Prepare observable data
                            observable_data = {
                                'value': obs_value,
                                'type': obs_type,
                                'description': description,
                                'tags': tags,
                                'tlp': 2,  # Default AMBER
                                'category': category,
                                'is_ioc': True,  # STIX indicators are always IOCs
                                'source': f"STIX:{obj.get('id', 'unknown')}",
                                'confidence': 70,  # Default medium-high for STIX data
                                'first_seen': first_seen,
                                'last_seen': last_seen
                            }
                            
                            if dry_run:
                                self.stdout.write(f"DRY RUN: Would import {obs_type}: {obs_value}")
                                created += 1
                                continue
                            
                            # Try to get existing observable
                            observable, new = Observable.objects.get_or_create(
                                type=obs_type,
                                value=obs_value,
                                company=company,
                                defaults={
                                    'description': observable_data['description'],
                                    'tags': observable_data['tags'],
                                    'tlp': observable_data['tlp'],
                                    'category': observable_data['category'],
                                    'is_ioc': observable_data['is_ioc'],
                                    'source': observable_data['source'],
                                    'confidence': observable_data['confidence'],
                                    'first_seen': observable_data['first_seen'],
                                    'last_seen': observable_data['last_seen'],
                                    'created_by': user
                                }
                            )
                            
                            if new:
                                created += 1
                                self.stdout.write(f"Created observable {obs_type}: {obs_value}")
                            else:
                                # Update existing
                                updated += 1
                                # Extend tags rather than replace
                                for tag in observable_data['tags']:
                                    if tag not in observable.tags:
                                        observable.tags.append(tag)
                                
                                # Update other fields if provided
                                if observable_data['description'] and not observable.description:
                                    observable.description = observable_data['description']
                                
                                # Take the earliest first_seen date
                                if observable_data['first_seen'] and (
                                    not observable.first_seen or 
                                    observable_data['first_seen'] < observable.first_seen
                                ):
                                    observable.first_seen = observable_data['first_seen']
                                
                                # Take the latest last_seen date
                                if observable_data['last_seen'] and (
                                    not observable.last_seen or
                                    observable_data['last_seen'] > observable.last_seen
                                ):
                                    observable.last_seen = observable_data['last_seen']
                                
                                # Max confidence
                                if observable_data['confidence'] > observable.confidence:
                                    observable.confidence = observable_data['confidence']
                                
                                # Mark as IOC if flagged
                                if observable_data['is_ioc']:
                                    observable.is_ioc = True
                                
                                observable.save()
                                self.stdout.write(f"Updated observable {obs_type}: {obs_value}")
                                
                        except Exception as e:
                            errors += 1
                            self.stdout.write(self.style.ERROR(
                                f"Error processing STIX indicator: {str(e)}"
                            ))
                
                if dry_run:
                    # Rollback the transaction in dry run mode
                    transaction.set_rollback(True)
                    self.stdout.write(self.style.SUCCESS(
                        f"DRY RUN: Would import {processed} observables from STIX"
                    ))
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f"Imported {created} new and updated {updated} existing observables "
                        f"from STIX with {errors} errors"
                    ))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"STIX import failed: {str(e)}"))
            raise CommandError(f"Failed to import from STIX: {str(e)}")
    
    def _map_misp_type(self, misp_type):
        """Map MISP attribute types to our Observable types"""
        type_map = {
            'ip-src': 'ip',
            'ip-dst': 'ip',
            'hostname': 'hostname',
            'domain': 'domain',
            'email': 'email',
            'url': 'url',
            'uri': 'uri',
            'md5': 'hash-md5',
            'sha1': 'hash-sha1',
            'sha256': 'hash-sha256',
            'filename': 'filename',
            'attachment': 'filename',
            'email-subject': 'email-subject',
            'mutex': 'mutex',
            'regkey': 'regkey',
            'vulnerability': 'vulnerability',
            'threat-actor': 'threat-actor',
            'btc': 'btc',
            'ssdeep': 'ssdeep',
            'email-src': 'email',
            'email-dst': 'email',
            'email-attachment': 'email-attachment',
            'mac-address': 'mac-address',
            'authentihash': 'authentihash',
            'ja3-fingerprint-md5': 'ja3-fingerprint-md5'
        }
        
        return type_map.get(misp_type, None)
    
    def _map_misp_category(self, misp_category):
        """Map MISP categories to our ObservableCategory"""
        category_map = {
            'Artifacts dropped': ObservableCategory.ARTIFACTS,
            'Payload delivery': ObservableCategory.PAYLOAD_DELIVERY,
            'Network activity': ObservableCategory.NETWORK_ACTIVITY,
            'Payload installation': ObservableCategory.PAYLOAD_INSTALLATION,
            'Persistence mechanism': ObservableCategory.PERSISTENCE,
            'Payload type': ObservableCategory.PAYLOAD_TYPE,
            'Attribution': ObservableCategory.ATTRIBUTION,
            'External analysis': ObservableCategory.EXTERNAL_ANALYSIS,
            'Financial fraud': ObservableCategory.FINANCIAL_FRAUD,
            'Support Tool': ObservableCategory.SUPPORT_TOOL,
            'Social network': ObservableCategory.SOCIAL_NETWORK,
            'Person': ObservableCategory.PERSON,
            'Targeting data': ObservableCategory.TARGETING,
            'Antivirus detection': ObservableCategory.ANTIVIRUS,
            'Internal reference': ObservableCategory.INTERNAL_REFERENCE,
            'Other': ObservableCategory.OTHER
        }
        
        return category_map.get(misp_category, ObservableCategory.OTHER)
    
    def _parse_stix_pattern(self, pattern):
        """
        Parse a STIX pattern and extract observable type and value
        Example pattern: [url:value = 'http://example.com']
        """
        import re
        
        # Simple regex to extract type and value from basic STIX patterns
        match = re.search(r'\[([\w-]+):value\s*=\s*[\'"]([^\'"]+)[\'"]', pattern)
        if match:
            stix_type = match.group(1)
            value = match.group(2)
            
            # Map STIX object types to our Observable types
            type_map = {
                'ipv4-addr': 'ip',
                'ipv6-addr': 'ip',
                'domain-name': 'domain',
                'url': 'url',
                'email-addr': 'email',
                'file': 'filename',  # Default, will need refinement
                'md5': 'hash-md5',
                'sha-1': 'hash-sha1',
                'sha-256': 'hash-sha256',
                'registry-key': 'regkey',
                'mutex': 'mutex',
                'process': 'process',
                'mac-addr': 'mac-address',
                'autonomous-system': 'as',
                'user-agent': 'user-agent'
            }
            
            # Check for hash type refinements
            if stix_type == 'file' and 'MD5' in pattern:
                return 'hash-md5', value
            elif stix_type == 'file' and 'SHA-1' in pattern:
                return 'hash-sha1', value
            elif stix_type == 'file' and 'SHA-256' in pattern:
                return 'hash-sha256', value
            
            return type_map.get(stix_type, None), value
        
        return None, None 