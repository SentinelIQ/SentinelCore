import requests
import csv
import io
import json
import uuid
from datetime import datetime
from django.db import models
from django.utils import timezone
from django.conf import settings
from elasticsearch import Elasticsearch
from sentinelvision.models import FeedModule
from observables.models import Observable
from api.v1.observables.enums import ObservableCategoryEnum
from sentinelvision.feeds import register_feed


@register_feed
class BlocklistDeFeed(FeedModule):
    """
    Feed module for ingesting IP addresses from blocklist.de.
    Contains IP addresses that have been reported for various malicious activities.
    Data is stored in Elasticsearch for later reference when creating cases.
    """
    # Module identification
    feed_id = 'blocklist_de'
    module_type = 'feed'
    
    # Configuration - removed feed_url and interval_hours as they're in parent class  
    es_index_name = models.CharField(
        'Elasticsearch Index',
        max_length=100,
        default='sentineliq-blocklist-de',
        help_text='Elasticsearch index where data will be stored'
    )
    
    class Meta:
        verbose_name = 'Blocklist.de Feed'
        verbose_name_plural = 'Blocklist.de Feeds'
    
    def save(self, *args, **kwargs):
        # Ensure module_type is always 'feed'
        self.module_type = 'feed'
        super().save(*args, **kwargs)
    
    def update_feed(self):
        """
        Fetch data from the blocklist.de feed URL and store it in Elasticsearch.
        """
        import logging
        logger = logging.getLogger('sentinelvision.feeds')
        
        try:
            # Initialize Elasticsearch client
            es_hosts = settings.ELASTICSEARCH_HOSTS
            es_username = settings.ELASTICSEARCH_USERNAME
            es_password = settings.ELASTICSEARCH_PASSWORD
            es_verify_certs = settings.ELASTICSEARCH_VERIFY_CERTS
            
            es_client = Elasticsearch(
                es_hosts,
                basic_auth=(es_username, es_password),
                verify_certs=es_verify_certs
            )
            
            # Ensure index exists with proper mapping
            self._ensure_index_exists(es_client)
            
            # Fetch data from feed
            logger.info(f"Fetching blocklist.de data from {self.feed_url}")
            response = requests.get(self.feed_url, timeout=60)
            response.raise_for_status()
            
            # Parse the data
            data = response.text.split('\n')
            processed_count = 0
            bulk_data = []
            
            for line in data:
                # Skip empty lines
                if not line.strip():
                    continue
                
                ip_address = line.strip()
                
                if not ip_address:
                    continue
                
                # Prepare document for Elasticsearch
                es_doc = {
                    'value': ip_address,
                    'type': 'ipv4',
                    'category': ObservableCategoryEnum.NETWORK_ACTIVITY.value,
                    'source': 'blocklist.de',
                    'feed_type': 'blocklist_de',
                    'description': "Blocklist.de - Reported malicious IP",
                    'first_seen': timezone.now().isoformat(),
                    'last_updated': timezone.now().isoformat(),
                    'threat_type': 'Reported Malicious IP',
                    'tags': ['blocklist.de', 'reported_malicious'],
                    'tenant_id': str(self.company.id),
                    'tenant_name': self.company.name,
                    'is_potential_ioc': True,
                    'is_confirmed_ioc': False,  # Only confirmed when used in a case
                    'confidence': 75  # Moderate confidence score for blocklist.de data
                }
                
                # Add to bulk indexing request
                doc_id = f"{ip_address}-{self.company.id}"
                bulk_data.append({"index": {"_index": self.es_index_name, "_id": doc_id}})
                bulk_data.append(es_doc)
                
                processed_count += 1
                
                # Execute bulk request in batches of 500
                if len(bulk_data) >= 1000:
                    if bulk_data:
                        es_client.bulk(operations=bulk_data, refresh=True)
                        bulk_data = []
                        logger.info(f"Indexed batch of blocklist.de records to Elasticsearch")
            
            # Index any remaining documents
            if bulk_data:
                es_client.bulk(operations=bulk_data, refresh=True)
                logger.info(f"Indexed final batch of blocklist.de records to Elasticsearch")
            
            # Update status with success
            self.update_status(success=True)
            
            return {
                'status': 'success',
                'processed_count': processed_count,
                'timestamp': timezone.now().isoformat(),
                'message': f"Successfully ingested {processed_count} blocklist.de records to Elasticsearch"
            }
            
        except Exception as e:
            error_message = f"Error updating blocklist.de feed: {str(e)}"
            logger.error(error_message, exc_info=True)
            return {
                'status': 'error',
                'error': error_message,
                'timestamp': timezone.now().isoformat()
            }
    
    def _ensure_index_exists(self, es_client):
        """
        Ensure the Elasticsearch index exists with the proper mapping.
        
        Args:
            es_client: Elasticsearch client instance
        """
        import logging
        logger = logging.getLogger('sentinelvision.feeds')
        
        # Check if index exists
        if not es_client.indices.exists(index=self.es_index_name):
            # Define index mapping
            mapping = {
                "mappings": {
                    "properties": {
                        "value": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "source": {"type": "keyword"},
                        "feed_type": {"type": "keyword"},
                        "description": {"type": "text"},
                        "first_seen": {"type": "date"},
                        "last_updated": {"type": "date"},
                        "threat_type": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "tags": {"type": "keyword"},
                        "tenant_id": {"type": "keyword"},
                        "tenant_name": {"type": "keyword"},
                        "is_potential_ioc": {"type": "boolean"},
                        "is_confirmed_ioc": {"type": "boolean"},
                        "confidence": {"type": "integer"}
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1
                }
            }
            
            # Create the index
            es_client.indices.create(index=self.es_index_name, body=mapping)
            logger.info(f"Created Elasticsearch index {self.es_index_name} for blocklist.de data")
        else:
            logger.info(f"Elasticsearch index {self.es_index_name} already exists")
    
    @classmethod
    def check_ioc_status(cls, value, company_id):
        """
        Check if a value exists as a potential IOC in Elasticsearch.
        This method should be called when creating a case to determine if the
        observable is a known IOC from the blocklist.de feed.
        
        Args:
            value (str): The observable value to check (IP address)
            company_id: The company ID to check for
            
        Returns:
            dict: Information about the IOC if found, None otherwise
        """
        import logging
        logger = logging.getLogger('sentinelvision.feeds')
        
        try:
            # Get an instance of the feed for this company to get the index name
            feed_instance = cls.objects.filter(company_id=company_id).first()
            if not feed_instance:
                logger.warning(f"No blocklist.de feed configured for company {company_id}")
                return None
                
            # Initialize Elasticsearch client
            es_hosts = settings.ELASTICSEARCH_HOSTS
            es_username = settings.ELASTICSEARCH_USERNAME
            es_password = settings.ELASTICSEARCH_PASSWORD
            es_verify_certs = settings.ELASTICSEARCH_VERIFY_CERTS
            
            es_client = Elasticsearch(
                es_hosts,
                basic_auth=(es_username, es_password),
                verify_certs=es_verify_certs
            )
            
            # Search for the value in Elasticsearch
            doc_id = f"{value}-{company_id}"
            
            try:
                doc = es_client.get(index=feed_instance.es_index_name, id=doc_id)
                if doc and doc.get('found'):
                    source = doc.get('_source', {})
                    
                    # If found in a case context, mark as confirmed IOC
                    if not source.get('is_confirmed_ioc'):
                        # Update the document to mark as confirmed IOC
                        source['is_confirmed_ioc'] = True
                        source['last_updated'] = datetime.now().isoformat()
                        
                        es_client.index(
                            index=feed_instance.es_index_name,
                            id=doc_id,
                            document=source
                        )
                        
                        logger.info(f"Marked blocklist.de IOC as confirmed: {value}")
                        
                        # Also create/update Observable record in database
                        try:
                            observable, created = Observable.objects.get_or_create(
                                type='ipv4',
                                value=value,
                                company_id=company_id,
                                defaults={
                                    'description': source.get('description', ''),
                                    'category': ObservableCategoryEnum.NETWORK_ACTIVITY.value,
                                    'tags': source.get('tags', []),
                                    'is_ioc': True,
                                    'source': 'Blocklist.de',
                                    'confidence': source.get('confidence', 75),
                                    'first_seen': datetime.fromisoformat(source.get('first_seen')).date() if source.get('first_seen') else timezone.now()
                                }
                            )
                            
                            if not created and not observable.is_ioc:
                                observable.is_ioc = True
                                observable.save(update_fields=['is_ioc'])
                                
                        except Exception as e:
                            logger.error(f"Error creating/updating Observable from blocklist.de: {str(e)}", exc_info=True)
                    
                    return {
                        'value': source.get('value'),
                        'type': source.get('type'),
                        'category': source.get('category'),
                        'feed_type': source.get('feed_type'),
                        'description': source.get('description'),
                        'first_seen': source.get('first_seen'),
                        'threat_type': source.get('threat_type'),
                        'tags': source.get('tags', []),
                        'confidence': source.get('confidence', 75),
                        'is_ioc': True
                    }
                
            except Exception as e:
                # Document not found or other ES error
                logger.debug(f"Blocklist.de IOC not found: {value} - {str(e)}")
                
            return None
            
        except Exception as e:
            logger.error(f"Error checking blocklist.de IOC status: {str(e)}", exc_info=True)
            return None 