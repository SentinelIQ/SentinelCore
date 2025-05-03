import requests
import csv
import io
from io import StringIO
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
from sentinelvision.logging import get_structured_logger

logger = get_structured_logger('sentinelvision.feeds.ssl_blacklist')

@register_feed
class SSLBlacklistFeed(FeedModule):
    """
    Feed module for SSL Certificate Blacklist.
    Collects SSL certificate fingerprints associated with malware and botnet C&C.
    """
    # Module identification
    feed_id = 'ssl_blacklist'
    module_type = 'feed'
    
    # Add feedmodule_ptr with a default value to fix migration
    feedmodule_ptr = models.OneToOneField(
        FeedModule,
        on_delete=models.CASCADE,
        parent_link=True,
        primary_key=True,
        auto_created=True,
        default=1  # Default value for migration
    )
    
    # Configuration - removed feed_url and interval_hours as they're in parent class
    es_index_name = models.CharField(
        'Elasticsearch Index',
        max_length=100,
        default='sentineliq-ssl-blacklist',
        help_text='Elasticsearch index where data will be stored'
    )
    
    class Meta:
        verbose_name = 'SSL Certificate Blacklist'
        verbose_name_plural = 'SSL Certificate Blacklists'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_type = 'feed'
        self.feed_type = 'ssl_blacklist'
        
        # Set default configuration if not provided
        if not self.feed_url:
            self.feed_url = 'https://sslbl.abuse.ch/blacklist/sslblacklist.csv'
        if not self.interval_hours:
            self.interval_hours = 12
    
    def save(self, *args, **kwargs):
        # Ensure module_type is always 'feed'
        self.module_type = 'feed'
        super().save(*args, **kwargs)

    # Helper method to get headers for requests
    def get_feed_headers(self):
        """Get default headers for feed requests."""
        return {
            'User-Agent': 'SentinelIQ/1.0',
            'Accept': 'text/csv,text/plain,application/json'
        }
    
    def execute(self):
        """
        Execute the feed module by updating from the source.
        
        Returns:
            dict: Execution results with status and counts
        """
        return self.update_feed()

    def update_feed(self):
        """
        Fetch data from the SSL Blacklist feed URL and store it in Elasticsearch.
        """
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
            logger.info(f"Fetching SSL blacklist data from {self.feed_url}")
            response = requests.get(
                self.feed_url,
                headers=self.get_feed_headers(),
                timeout=60
            )
            response.raise_for_status()
            
            # Parse the CSV data
            csv_data = io.StringIO(response.text)
            
            # Skip comment lines (starting with #)
            csv_lines = []
            for line in csv_data:
                if not line.startswith('#'):
                    csv_lines.append(line)
            
            # If we didn't get any valid lines, return early
            if not csv_lines:
                logger.warning(f"No valid data found in SSL blacklist feed")
                return {
                    'status': 'warning',
                    'error': "No valid data found in feed",
                    'processed_count': 0
                }
                
            csv_data = io.StringIO('\n'.join(csv_lines))
            
            reader = csv.DictReader(csv_data, delimiter=',', 
                                    fieldnames=['Listingdate', 'SHA1', 'Listingreason'])
            
            # Process each entry and ingest to Elasticsearch
            processed_count = 0
            bulk_data = []
            
            for row in reader:
                if 'SHA1' not in row or not row['SHA1']:
                    continue
                
                # Extract and clean data
                sha1_hash = row.get('SHA1', '').strip()
                listing_date = row.get('Listingdate', '')
                listing_reason = row.get('Listingreason', 'Unknown')
                
                if not sha1_hash:
                    continue
                
                # Prepare document for Elasticsearch
                es_doc = {
                    'value': sha1_hash,
                    'type': 'hash-sha1',  # Updated to match new Observable.Type
                    'category': ObservableCategoryEnum.NETWORK_ACTIVITY.value,
                    'source': 'abuse.ch',
                    'feed_type': 'ssl_blacklist',
                    'description': f"SSL Certificate Blacklist - {listing_reason}",
                    'first_seen': listing_date,
                    'last_updated': datetime.now().isoformat(),
                    'listing_reason': listing_reason,
                    'tags': ['abuse.ch', 'ssl_blacklist', listing_reason.lower().replace(' ', '_')],
                    'tenant_id': str(self.company.id),
                    'tenant_name': self.company.name,
                    'is_potential_ioc': True,
                    'is_confirmed_ioc': False,  # Only confirmed when used in a case
                    'confidence': 70  # Moderate confidence score for feed data
                }
                
                # Add to bulk indexing request
                doc_id = f"{sha1_hash}-{self.company.id}"
                bulk_data.append({"index": {"_index": self.es_index_name, "_id": doc_id}})
                bulk_data.append(es_doc)
                
                processed_count += 1
                
                # Execute bulk request in batches of 500
                if len(bulk_data) >= 1000:
                    if bulk_data:
                        es_client.bulk(operations=bulk_data, refresh=True)
                        bulk_data = []
                        logger.info(f"Indexed batch of SSL blacklist records to Elasticsearch")
            
            # Index any remaining documents
            if bulk_data:
                es_client.bulk(operations=bulk_data, refresh=True)
                logger.info(f"Indexed final batch of SSL blacklist records to Elasticsearch")
            
            # Update status with success
            self.update_status(success=True)
            
            return {
                'status': 'success',
                'processed_count': processed_count,
                'timestamp': timezone.now().isoformat(),
                'message': f"Successfully ingested {processed_count} SSL blacklist records to Elasticsearch"
            }
            
        except Exception as e:
            error_message = f"Error updating SSL Blacklist feed: {str(e)}"
            logger.error(error_message, exc_info=True)
            self.update_status(success=False, error=error_message)
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
                        "first_seen": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis||strict_date_optional_time"},
                        "last_updated": {"type": "date"},
                        "listing_reason": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
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
            logger.info(f"Created Elasticsearch index {self.es_index_name} for SSL blacklist data")
        else:
            logger.info(f"Elasticsearch index {self.es_index_name} already exists")
    
    @classmethod
    def check_ioc_status(cls, value, company_id):
        """
        Check if a value exists as a potential IOC in Elasticsearch.
        This method should be called when creating a case to determine if the
        observable is a known IOC from the SSL Blacklist feed.
        
        Args:
            value (str): The observable value to check (SHA1 hash)
            company_id: The company ID to check for
            
        Returns:
            dict: Information about the IOC if found, None otherwise
        """
        try:
            # Get an instance of the feed for this company to get the index name
            feed_instance = cls.objects.filter(company_id=company_id).first()
            if not feed_instance:
                logger.warning(f"No SSL Blacklist feed configured for company {company_id}")
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
                        
                        logger.info(f"Marked SSL Blacklist IOC as confirmed: {value}")
                        
                        # Also create/update Observable record in database
                        try:
                            observable, created = Observable.objects.get_or_create(
                                type='hash-sha1',  # Using the new naming format
                                value=value,
                                company_id=company_id,
                                defaults={
                                    'description': source.get('description', ''),
                                    'category': ObservableCategoryEnum.NETWORK_ACTIVITY.value,
                                    'tags': source.get('tags', []),
                                    'is_ioc': True,
                                    'source': 'abuse.ch (SSL Blacklist)',
                                    'confidence': source.get('confidence', 70),
                                    'first_seen': datetime.fromisoformat(source.get('first_seen')).date() if source.get('first_seen') else timezone.now()
                                }
                            )
                            
                            if not created and not observable.is_ioc:
                                observable.is_ioc = True
                                observable.save(update_fields=['is_ioc'])
                                
                        except Exception as e:
                            logger.error(f"Error creating/updating Observable from SSL Blacklist: {str(e)}", exc_info=True)
                    
                    return {
                        'value': source.get('value'),
                        'type': source.get('type'),
                        'category': source.get('category'),
                        'feed_type': source.get('feed_type'),
                        'description': source.get('description'),
                        'first_seen': source.get('first_seen'),
                        'listing_reason': source.get('listing_reason'),
                        'tags': source.get('tags', []),
                        'confidence': source.get('confidence', 70),
                        'is_ioc': True
                    }
                
            except Exception as e:
                # Document not found or other ES error
                logger.debug(f"SSL Blacklist IOC not found: {value} - {str(e)}")
                
            return None
            
        except Exception as e:
            logger.error(f"Error checking SSL Blacklist IOC status: {str(e)}", exc_info=True)
            return None 