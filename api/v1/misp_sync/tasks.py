import logging
from django.utils import timezone
from django.db import transaction
from api.core.tasks import audit_task
from api.v1.misp_sync.models import MISPServer, MISPEvent, MISPAttribute, MISPObject
from api.v1.misp_sync.enums import MISPSyncStatusEnum, MISPThreatLevelEnum
from api.v1.audit_logs.enums import EntityTypeEnum, ActionTypeEnum
import json
from datetime import timedelta, datetime
from pymisp import PyMISP, MISPEvent as PyMISPEvent
from alerts.models import Alert
from api.v1.alerts.enums import AlertSeverityEnum, AlertStatusEnum
from incidents.models import Incident
from api.v1.incidents.enums import IncidentSeverityEnum, IncidentStatusEnum
from observables.models import Observable
from api.v1.observables.enums import ObservableTypeEnum
import uuid

logger = logging.getLogger('api')


@audit_task(entity_type=EntityTypeEnum.MISP_EVENT, action=ActionTypeEnum.SYNC)
def sync_misp_server(server_id, days_back=7, max_events=1000):
    """
    Synchronize events from a MISP server.
    
    Args:
        server_id: ID of the MISPServer to sync
        days_back: Number of days to go back for synchronization
        max_events: Maximum number of events to retrieve
        
    Returns:
        dict: Synchronization result
    """
    try:
        # Get the MISP server
        server = MISPServer.objects.get(id=server_id)
        
        # Update last_sync timestamp
        server.last_sync = timezone.now()
        server.save(update_fields=['last_sync'])
        
        # Log sync start
        logger.info(f"Starting MISP sync for server {server.name} (ID: {server.id})")
        
        # Calculate the date range for synchronization
        from_date = (timezone.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Initialize PyMISP
        misp = PyMISP(server.url, server.api_key, server.verify_ssl)
        
        # Fetch events from the MISP server
        logger.info(f"Fetching events from {server.url} since {from_date}")
        events = misp.search(controller='events', date_from=from_date, limit=max_events, published=True)
        
        # Track statistics
        imported_events = 0
        imported_objects = 0
        imported_attributes = 0
        
        # Process each event
        if 'response' in events and events['response']:
            for event_data in events['response']:
                if 'Event' in event_data:
                    event_data = event_data['Event']
                    
                    # Check if event already exists
                    event_uuid = event_data.get('uuid')
                    existing_event = MISPEvent.objects.filter(uuid=event_uuid).first()
                    
                    if existing_event:
                        logger.info(f"Updating existing event {event_data.get('id')} - {event_data.get('info')}")
                        event = existing_event
                        # Update event data
                        event.info = event_data.get('info')
                        event.threat_level_id = event_data.get('threat_level_id', 2)
                        event.analysis = event_data.get('analysis', 0)
                        event.date = event_data.get('date')
                        event.published = event_data.get('published', False)
                        event.timestamp = datetime.fromtimestamp(int(event_data.get('timestamp')))
                        event.distribution = event_data.get('distribution', 0)
                        event.org_name = event_data.get('Org', {}).get('name', '')
                        event.orgc_name = event_data.get('Orgc', {}).get('name', '')
                        event.raw_data = event_data
                        event.save()
                    else:
                        logger.info(f"Creating new event {event_data.get('id')} - {event_data.get('info')}")
                        # Create new event
                        event = MISPEvent.objects.create(
                            misp_id=event_data.get('id'),
                            misp_uuid=event_uuid,
                            info=event_data.get('info'),
                            threat_level_id=event_data.get('threat_level_id', 2),
                            analysis=event_data.get('analysis', 0),
                            date=event_data.get('date'),
                            published=event_data.get('published', False),
                            timestamp=datetime.fromtimestamp(int(event_data.get('timestamp'))),
                            distribution=event_data.get('distribution', 0),
                            org_name=event_data.get('Org', {}).get('name', ''),
                            orgc_name=event_data.get('Orgc', {}).get('name', ''),
                            raw_data=event_data,
                            misp_server=server,
                            company=server.company
                        )
                        
                    imported_events += 1
                    
                    # Process attributes
                    if 'Attribute' in event_data:
                        for attr_data in event_data['Attribute']:
                            attr_uuid = attr_data.get('uuid')
                            existing_attr = MISPAttribute.objects.filter(uuid=attr_uuid).first()
                            
                            if existing_attr:
                                # Update existing attribute
                                existing_attr.type = attr_data.get('type')
                                existing_attr.category = attr_data.get('category')
                                existing_attr.value = attr_data.get('value')
                                existing_attr.to_ids = attr_data.get('to_ids', False)
                                existing_attr.distribution = attr_data.get('distribution', 0)
                                existing_attr.timestamp = datetime.fromtimestamp(int(attr_data.get('timestamp')))
                                existing_attr.comment = attr_data.get('comment', '')
                                existing_attr.raw_data = attr_data
                                existing_attr.save()
                            else:
                                # Create new attribute
                                MISPAttribute.objects.create(
                                    misp_id=attr_data.get('id'),
                                    misp_uuid=attr_uuid,
                                    type=attr_data.get('type'),
                                    category=attr_data.get('category'),
                                    value=attr_data.get('value'),
                                    to_ids=attr_data.get('to_ids', False),
                                    distribution=attr_data.get('distribution', 0),
                                    timestamp=datetime.fromtimestamp(int(attr_data.get('timestamp'))),
                                    comment=attr_data.get('comment', ''),
                                    raw_data=attr_data,
                                    event=event,
                                    company=server.company
                                )
                                imported_attributes += 1
                    
                    # Process objects
                    if 'Object' in event_data:
                        for obj_data in event_data['Object']:
                            obj_uuid = obj_data.get('uuid')
                            existing_obj = MISPObject.objects.filter(uuid=obj_uuid).first()
                            
                            if existing_obj:
                                # Update existing object
                                existing_obj.name = obj_data.get('name')
                                existing_obj.meta_category = obj_data.get('meta-category')
                                existing_obj.description = obj_data.get('description', '')
                                existing_obj.template_uuid = obj_data.get('template_uuid')
                                existing_obj.template_version = obj_data.get('template_version')
                                existing_obj.timestamp = datetime.fromtimestamp(int(obj_data.get('timestamp')))
                                existing_obj.distribution = obj_data.get('distribution', 0)
                                existing_obj.comment = obj_data.get('comment', '')
                                existing_obj.deleted = obj_data.get('deleted', False)
                                existing_obj.raw_data = obj_data
                                existing_obj.save()
                            else:
                                # Create new object
                                MISPObject.objects.create(
                                    misp_id=obj_data.get('id'),
                                    misp_uuid=obj_uuid,
                                    name=obj_data.get('name'),
                                    meta_category=obj_data.get('meta-category'),
                                    description=obj_data.get('description', ''),
                                    template_uuid=obj_data.get('template_uuid'),
                                    template_version=obj_data.get('template_version'),
                                    timestamp=datetime.fromtimestamp(int(obj_data.get('timestamp'))),
                                    distribution=obj_data.get('distribution', 0),
                                    comment=obj_data.get('comment', ''),
                                    deleted=obj_data.get('deleted', False),
                                    raw_data=obj_data,
                                    event=event,
                                    company=server.company
                                )
                                imported_objects += 1
        
        # Return result
        result = {
            "status": MISPSyncStatusEnum.COMPLETED.value,
            "server_id": server.id,
            "server_name": server.name,
            "sync_date": server.last_sync.isoformat(),
            "stats": {
                "events_imported": imported_events,
                "attributes_imported": imported_attributes,
                "objects_imported": imported_objects,
                "days_back": days_back,
                "max_events": max_events
            }
        }
        
        logger.info(f"MISP sync completed for server {server.name}: {imported_events} events, {imported_attributes} attributes, {imported_objects} objects")
        return result
        
    except MISPServer.DoesNotExist:
        logger.error(f"MISP server with ID {server_id} not found")
        return {
            "status": MISPSyncStatusEnum.FAILED.value,
            "error": f"MISP server with ID {server_id} not found"
        }
    except Exception as e:
        logger.exception(f"Error during MISP sync for server {server_id}: {str(e)}")
        return {
            "status": MISPSyncStatusEnum.FAILED.value,
            "error": str(e)
        }


@audit_task(entity_type=EntityTypeEnum.MISP_EVENT, action=ActionTypeEnum.TRANSFORM)
def convert_misp_event_to_alert(event_id):
    """
    Convert a MISP event to a SentinelIQ alert.
    
    Args:
        event_id: ID of the MISPEvent to convert
        
    Returns:
        dict: Conversion result
    """
    try:
        # Get the MISP event
        event = MISPEvent.objects.get(id=event_id)
        
        # Check if already converted to alert
        existing_alert = Alert.objects.filter(source="MISP", source_ref=str(event.uuid), company=event.company).first()
        if existing_alert:
            logger.info(f"MISP event {event.info} already converted to alert ID {existing_alert.id}")
            return {
                "status": "already_converted",
                "alert_id": existing_alert.id,
                "event_id": event.id
            }
            
        # Log conversion start
        logger.info(f"Converting MISP event {event.info} to alert")
        
        with transaction.atomic():
            # Map MISP threat level to alert severity
            severity_mapping = {
                MISPThreatLevelEnum.HIGH: AlertSeverityEnum.CRITICAL,
                MISPThreatLevelEnum.MEDIUM: AlertSeverityEnum.HIGH,
                MISPThreatLevelEnum.LOW: AlertSeverityEnum.MEDIUM,
                MISPThreatLevelEnum.UNDEFINED: AlertSeverityEnum.LOW,
            }
            
            severity = severity_mapping.get(
                event.threat_level_id, 
                AlertSeverityEnum.MEDIUM
            )
            
            # Create the alert
            alert = Alert.objects.create(
                title=event.info,
                description=f"Alert created from MISP event: {event.info}\nOrganization: {event.org_name}",
                severity=severity,
                status=AlertStatusEnum.NEW,
                source="MISP",
                source_ref=str(event.uuid),
                external_source="MISP",
                date=event.timestamp,
                company=event.company,
                created_by=event.created_by or event.company.users.filter(is_superuser=True).first(),  # Default to company admin
                tags=event.tags or [],
                raw_payload=event.raw_data
            )
            
            # Process attributes as observables
            for attr in event.attributes.all():
                # Map MISP attribute types to Observable types
                type_mapping = {
                    'ip-src': ObservableTypeEnum.IP,
                    'ip-dst': ObservableTypeEnum.IP,
                    'domain': ObservableTypeEnum.DOMAIN,
                    'hostname': ObservableTypeEnum.HOSTNAME,
                    'url': ObservableTypeEnum.URL,
                    'md5': ObservableTypeEnum.HASH_MD5,
                    'sha1': ObservableTypeEnum.HASH_SHA1,
                    'sha256': ObservableTypeEnum.HASH_SHA256,
                    'filename': ObservableTypeEnum.FILENAME,
                    'email': ObservableTypeEnum.EMAIL,
                    'email-src': ObservableTypeEnum.EMAIL,
                    'email-dst': ObservableTypeEnum.EMAIL,
                }
                
                # Skip attributes that don't map to observable types
                if attr.type not in type_mapping:
                    continue
                    
                # Create or get Observable
                observable, created = Observable.objects.get_or_create(
                    type=type_mapping[attr.type].value,
                    value=attr.value,
                    company=event.company,
                    defaults={
                        'description': attr.comment or f"From MISP event: {event.info}",
                        'is_ioc': attr.to_ids,
                        'source': "MISP",
                        'tags': attr.tags or [],
                        'created_by': event.created_by or event.company.users.filter(is_superuser=True).first()
                    }
                )
                
                # Link observable to alert
                alert.observables.add(observable)
                
            # Update artifact count
            alert.update_artifact_count()
            alert.save()
            
            # Log success
            logger.info(f"Successfully converted MISP event {event.info} to alert ID {alert.id}")
            
            return {
                "status": "completed",
                "alert_id": alert.id,
                "event_id": event.id,
                "observable_count": alert.artifact_count
            }
    
    except MISPEvent.DoesNotExist:
        logger.error(f"MISP event with ID {event_id} not found")
        return {
            "status": "failed",
            "error": f"MISP event with ID {event_id} not found"
        }
    except Exception as e:
        logger.error(f"Error converting MISP event to alert: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@audit_task(entity_type=EntityTypeEnum.INCIDENT, action=ActionTypeEnum.TRANSFORM)
def convert_misp_event_to_incident(event_id):
    """
    Convert a MISP event directly to a SentinelIQ Incident.
    
    Args:
        event_id: ID of the MISPEvent to convert
        
    Returns:
        dict: Conversion result
    """
    try:
        # Get the MISP event
        event = MISPEvent.objects.get(id=event_id)
        
        # Log conversion start
        logger.info(f"Converting MISP event {event.info} (ID: {event.id}) to Incident")
        
        # Map MISP threat level to incident severity
        severity_mapping = {
            MISPThreatLevelEnum.HIGH: IncidentSeverityEnum.CRITICAL,
            MISPThreatLevelEnum.MEDIUM: IncidentSeverityEnum.HIGH,
            MISPThreatLevelEnum.LOW: IncidentSeverityEnum.MEDIUM,
            MISPThreatLevelEnum.UNDEFINED: IncidentSeverityEnum.LOW,
        }
        
        severity = severity_mapping.get(
            event.threat_level_id, 
            IncidentSeverityEnum.MEDIUM
        )
        
        # Create Incident
        incident = Incident.objects.create(
            title=f"MISP: {event.info}",
            description=f"Incident created from MISP event: {event.info}\nOrganization: {event.org_name}",
            severity=severity,
            status=IncidentStatusEnum.NEW,
            source="MISP",
            source_reference=str(event.uuid),
            company=event.company,
            raw_data=event.raw_data
        )
        
        # Link back to the MISP event
        event.incident = incident
        event.save()
        
        # Convert attributes to observables
        attributes = MISPAttribute.objects.filter(event=event)
        
        for attr in attributes:
            # Map MISP attribute types to Observable types
            type_mapping = {
                'ip-src': ObservableTypeEnum.IP,
                'ip-dst': ObservableTypeEnum.IP,
                'domain': ObservableTypeEnum.DOMAIN,
                'hostname': ObservableTypeEnum.HOSTNAME,
                'url': ObservableTypeEnum.URL,
                'md5': ObservableTypeEnum.HASH_MD5,
                'sha1': ObservableTypeEnum.HASH_SHA1,
                'sha256': ObservableTypeEnum.HASH_SHA256,
                'filename': ObservableTypeEnum.FILENAME,
                'email': ObservableTypeEnum.EMAIL,
                'email-src': ObservableTypeEnum.EMAIL,
                'email-dst': ObservableTypeEnum.EMAIL,
            }
            
            obs_type = type_mapping.get(attr.type)
            
            if obs_type:
                Observable.objects.create(
                    value=attr.value,
                    type=obs_type,
                    tlp="AMBER",
                    is_ioc=attr.to_ids,
                    incident=incident,
                    source="MISP",
                    source_reference=str(attr.uuid),
                    company=event.company,
                    first_seen=attr.timestamp,
                    last_seen=attr.timestamp,
                    description=attr.comment if attr.comment else f"From MISP event: {event.info}"
                )
        
        # Return result
        result = {
            "status": "completed",
            "event_id": event.id,
            "event_info": event.info,
            "incident_id": incident.id,
        }
        
        logger.info(f"MISP event {event.info} converted to Incident successfully (Incident ID: {incident.id})")
        return result
        
    except MISPEvent.DoesNotExist:
        logger.error(f"MISP event with ID {event_id} not found")
        return {
            "status": "failed",
            "error": f"MISP event with ID {event_id} not found"
        }
    except Exception as e:
        logger.exception(f"Error during MISP event conversion for event {event_id}: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@audit_task(entity_type=EntityTypeEnum.MISP_EVENT, action=ActionTypeEnum.SYNC)
def schedule_misp_sync_for_active_servers():
    """
    Schedule synchronization for all active MISP servers based on their sync interval.
    
    This task is intended to be run periodically to check for servers that need synchronization.
    """
    now = timezone.now()
    
    # Get all active servers
    active_servers = MISPServer.objects.filter(is_active=True)
    
    sync_scheduled = 0
    for server in active_servers:
        # Check if server needs sync based on last_sync and sync_interval_hours
        if server.last_sync is None or (now - server.last_sync) > timedelta(hours=server.sync_interval_hours):
            # Schedule sync task
            sync_misp_server.delay(server.id)
            sync_scheduled += 1
            
            logger.info(f"Scheduled MISP sync for server {server.name} (ID: {server.id})")
    
    logger.info(f"Scheduled MISP sync for {sync_scheduled} servers")
    
    return {
        "status": "completed",
        "servers_scheduled": sync_scheduled,
        "total_active_servers": active_servers.count()
    } 