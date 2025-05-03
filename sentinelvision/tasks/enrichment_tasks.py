import logging
import traceback
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from sentinelvision.models import ExecutionRecord
from sentinelvision.analyzers.virustotal import VirusTotalAnalyzer
from sentinelvision.services.executor import ModuleExecutor
from sentinelvision.logging import get_structured_logger
from observables.models import Observable
from observables.services.elastic import BaseElasticIndexer, ElasticLookupService
import time

from sentinelvision.models import (
    EnrichedIOC, FeedModule, IOCFeedMatch, 
    EnrichmentStatusEnum, IOCTypeEnum
)
from companies.models import Company
from elasticsearch_dsl import Search, Q as ESQ
from django.conf import settings

User = get_user_model()
logger = get_structured_logger('sentinelvision.enrichment')


@shared_task(
    bind=True,
    rate_limit="20/m",
    acks_late=True,
    max_retries=3,
    retry_backoff=True,
    default_retry_delay=60,
    queue="observables",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3}
)
def enrich_observable(self, observable_id, analyzer_id=None, company_id=None, user_id=None):
    """
    Enrich a specific observable with tenant context.
    
    Args:
        observable_id (str): UUID of the observable to enrich
        analyzer_id (str): Optional UUID of the analyzer to use (if None, all compatible analyzers)
        company_id (str): UUID of the company for tenant isolation
        user_id (str): UUID of the user triggering the enrichment
    """
    try:
        # Verify observable exists and belongs to company
        observable = Observable.objects.get(id=observable_id)
        
        # Ensure tenant isolation
        if company_id and str(observable.company.id) != company_id:
            logger.error(
                f"Tenant mismatch: Observable belongs to {observable.company.id}, "
                f"but enrichment requested for company {company_id}",
                extra={
                    'observable_id': observable_id,
                    'tenant_id': company_id
                }
            )
            return {'status': 'error', 'message': 'Tenant isolation violation'}
        
        # Set company_id for logging
        company_id = str(observable.company.id)
        
        # Find a system/automation user or the specified user
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                # Fallback to system user
                user = User.objects.filter(
                    company=observable.company,
                    is_active=True,
                    is_system=True
                ).first()
                if not user:
                    # Final fallback to any admin user
                    user = User.objects.filter(
                        company=observable.company,
                        is_active=True,
                        is_staff=True
                    ).first()
        else:
            # Use system user
            user = User.objects.filter(
                company=observable.company,
                is_active=True,
                is_system=True
            ).first()
            if not user:
                # Fallback to any admin user
                user = User.objects.filter(
                    company=observable.company,
                    is_active=True,
                    is_staff=True
                ).first()
        
        if not user:
            logger.error(
                f"No suitable user found for company {company_id} to perform enrichment",
                extra={
                    'observable_id': observable_id,
                    'tenant_id': company_id
                }
            )
            return {'status': 'error', 'message': 'No suitable user found for enrichment'}
        
        logger.info(
            f"Starting enrichment for observable {observable.type}: {observable.value}",
            extra={
                'observable_id': str(observable.id),
                'observable_type': observable.type,
                'observable_value': observable.value,
                'tenant_id': company_id,
                'user_id': str(user.id)
            }
        )
        
        # Find appropriate analyzers
        if analyzer_id:
            analyzers = VirusTotalAnalyzer.objects.filter(
                id=analyzer_id,
                company=observable.company,
                is_active=True
            )
        else:
            # Find all compatible analyzers
            analyzers = VirusTotalAnalyzer.objects.filter(
                company=observable.company,
                is_active=True,
                supported_observable_types__contains=[observable.type]
            )
        
        if not analyzers.exists():
            logger.warning(
                f"No compatible analyzers found for observable {observable.id}",
                extra={
                    'observable_id': str(observable.id),
                    'observable_type': observable.type,
                    'tenant_id': company_id
                }
            )
            return {
                'status': 'warning',
                'message': 'No compatible analyzers found'
            }
        
        results = []
        
        # Execute each analyzer
        for analyzer in analyzers:
            try:
                logger.info(
                    f"Executing analyzer {analyzer.name} on observable {observable.id}",
                    extra={
                        'observable_id': str(observable.id),
                        'observable_type': observable.type,
                        'analyzer_id': str(analyzer.id),
                        'analyzer_name': analyzer.name,
                        'tenant_id': company_id
                    }
                )
                
                # Execute analyzer using ModuleExecutor
                execution_record, result = ModuleExecutor.execute_analyzer(
                    analyzer=analyzer,
                    observable=observable,
                    user=user,
                    incident=observable.incident,
                    alert=observable.alert
                )
                
                if execution_record:
                    logger.info(
                        f"Analyzer execution completed with status: {execution_record.status}",
                        extra={
                            'execution_id': str(execution_record.id),
                            'status': execution_record.status,
                            'observable_id': str(observable.id),
                            'tenant_id': company_id
                        }
                    )
                    
                    # Index updated observable in Elasticsearch
                    if execution_record.status == ExecutionRecord.Status.SUCCESS:
                        try:
                            indexer = BaseElasticIndexer(company_id=observable.company.id)
                            index_result = indexer.index_observable(observable)
                            logger.info(
                                f"Indexed enriched observable in Elasticsearch: {index_result.get('status')}",
                                extra={
                                    'observable_id': str(observable.id),
                                    'elastic_result': index_result.get('status'),
                                    'tenant_id': company_id
                                }
                            )
                        except Exception as e:
                            logger.error(
                                f"Error indexing enriched observable: {str(e)}",
                                extra={
                                    'observable_id': str(observable.id),
                                    'tenant_id': company_id,
                                    'error': str(e)
                                },
                                exc_info=True
                            )
                    
                    results.append({
                        'analyzer': analyzer.name,
                        'execution_id': str(execution_record.id),
                        'status': execution_record.status,
                        'result': result
                    })
                else:
                    logger.warning(
                        f"Analyzer {analyzer.name} not compatible with observable {observable.type}",
                        extra={
                            'analyzer_name': analyzer.name,
                            'observable_type': observable.type,
                            'observable_id': str(observable.id),
                            'tenant_id': company_id
                        }
                    )
                    results.append({
                        'analyzer': analyzer.name,
                        'status': 'error',
                        'error': 'Analyzer not compatible with observable type'
                    })
            
            except Exception as e:
                logger.error(
                    f"Error executing analyzer {analyzer.name}: {str(e)}",
                    extra={
                        'analyzer_name': analyzer.name,
                        'observable_id': str(observable.id),
                        'tenant_id': company_id,
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    },
                    exc_info=True
                )
                results.append({
                    'analyzer': analyzer.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'status': 'success',
            'observable_id': str(observable.id),
            'observable_type': observable.type,
            'results': results
        }
    
    except Observable.DoesNotExist:
        logger.error(
            f"Observable {observable_id} not found",
            extra={'observable_id': observable_id}
        )
        return {'status': 'error', 'message': f"Observable {observable_id} not found"}
    
    except Exception as e:
        logger.error(
            f"Error enriching observable {observable_id}: {str(e)}",
            extra={
                'observable_id': observable_id,
                'error': str(e),
                'traceback': traceback.format_exc()
            },
            exc_info=True
        )
        
        # Retry with backoff
        self.retry(exc=e)
        
        return {
            'status': 'error',
            'error': str(e),
            'is_retrying': True
        }


@shared_task(
    bind=True,
    rate_limit="5/m",
    acks_late=True,
    max_retries=5,
    retry_backoff=True,
    retry_backoff_max=3600,  # Max 1 hour between retries
    default_retry_delay=300,  # 5 minutes initial delay
    queue="observables",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5}
)
def reenrich_observables(self, days=1, company_id=None, limit=100):
    """
    Background task to reenrich older observables.
    
    Args:
        days (int): Age threshold in days
        company_id (str): Optional company ID for limiting scope
        limit (int): Maximum number of observables to process per run
        
    Returns:
        dict: Status information about the enrichment process
    
    Raises:
        Exception: Any unexpected error during processing
    """
    try:
        threshold_date = timezone.now() - timedelta(days=days)
        
        query = Q(
            updated_at__lt=threshold_date,
            is_ioc=True  # Focus on confirmed IOCs first
        )
        
        # Apply company filter if provided
        if company_id:
            query &= Q(company_id=company_id)
        
        # Get observables that haven't been updated recently
        observables = Observable.objects.filter(query).order_by('updated_at')[:limit]
        
        count = observables.count()
        logger.info(
            f"Found {count} observables to reenrich",
            extra={
                'count': count,
                'days': days,
                'company_id': company_id,
                'task_id': self.request.id
            }
        )
        
        if count == 0:
            return {
                'status': 'success',
                'message': 'No observables found to reenrich',
                'scheduled_count': 0,
                'total_found': 0,
                'task_id': self.request.id
            }
        
        enrich_count = 0
        error_count = 0
        
        # Process each observable
        for observable in observables:
            try:
                company_id = str(observable.company.id)
                
                logger.info(
                    f"Scheduling reenrichment for observable {observable.id}",
                    extra={
                        'observable_id': str(observable.id),
                        'observable_type': observable.type,
                        'observable_value': observable.value,
                        'tenant_id': company_id,
                        'last_updated': observable.updated_at.isoformat(),
                        'task_id': self.request.id
                    }
                )
                
                # Schedule enrichment task with appropriate priority based on IOC status and age
                priority = 5  # Default priority (lower number = higher priority)
                
                # Increase priority for critical observables
                if observable.is_ioc and observable.severity == 'critical':
                    priority = 3
                elif observable.is_ioc and observable.severity == 'high':
                    priority = 4
                
                # Schedule enrichment task
                enrich_observable.apply_async(
                    args=[str(observable.id)],
                    kwargs={'company_id': company_id},
                    expires=86400,  # Expire task after 24 hours if not executed
                    retry=True,
                    priority=priority,
                    retry_policy={
                        'max_retries': 3,
                        'interval_start': 60,
                        'interval_step': 120,
                        'interval_max': 600
                    }
                )
                
                # Mark as processing to prevent duplicate scheduling
                observable.status = 'processing'
                observable.save(update_fields=['status', 'updated_at'])
                
                enrich_count += 1
                
                # Add a small delay between tasks to prevent overloading the task queue
                if enrich_count % 10 == 0:
                    time.sleep(0.5)
                    
            except Exception as e:
                error_count += 1
                logger.error(
                    f"Error scheduling enrichment for observable {observable.id}: {str(e)}",
                    extra={
                        'observable_id': str(observable.id),
                        'error': str(e),
                        'task_id': self.request.id
                    },
                    exc_info=True
                )
        
        return {
            'status': 'success',
            'scheduled_count': enrich_count,
            'error_count': error_count,
            'total_found': count,
            'task_id': self.request.id
        }
    except Exception as e:
        logger.error(
            f"Critical error in reenrich_observables: {str(e)}",
            extra={
                'error': str(e),
                'traceback': traceback.format_exc(),
                'parameters': {
                    'days': days,
                    'company_id': company_id,
                    'limit': limit
                },
                'task_id': self.request.id
            },
            exc_info=True
        )
        
        # Determine if we should retry based on the error type
        retryable_errors = [
            "database", "connection", "timeout", "deadlock", 
            "lock", "operational error", "server", "network"
        ]
        
        should_retry = any(err_type in str(e).lower() for err_type in retryable_errors)
        
        if should_retry:
            logger.info(f"Retrying task due to retryable error: {str(e)}")
            # Use exponential backoff for transient errors
            self.retry(exc=e)
        
        # Reraise for non-retryable errors
        raise 


@shared_task(
    bind=True,
    name='sentinelvision.tasks.enrichment_tasks.enrich_observable',
    acks_late=True,
    max_retries=3,
    retry_backoff=True,
    queue="sentineliq_soar_vision_enrichment"
)
def enrich_observable(self, company_id, ioc_type, ioc_value, source='api', description=''):
    """
    Enrich a single observable/IOC by checking it against all relevant feeds.
    
    Args:
        company_id (str): ID of the company/tenant
        ioc_type (str): Type of IOC (ip, domain, hash, etc.)
        ioc_value (str): Value of the IOC
        source (str): Source of the IOC (api, alert, etc.)
        description (str): Description of the IOC
        
    Returns:
        dict: Results of the enrichment
    """
    start_time = time.time()
    
    structured_log = {
        'company_id': company_id,
        'ioc_type': ioc_type,
        'ioc_value': ioc_value,
        'source': source,
        'task_id': self.request.id
    }
    
    logger.info(
        f"Starting enrichment for {ioc_type}: {ioc_value}",
        extra=structured_log
    )
    
    try:
        # Get company
        company = Company.objects.get(id=company_id)
        structured_log['company_name'] = company.name
        
        # Get or create enriched IOC
        enriched_ioc, created = EnrichedIOC.objects.get_or_create(
            company=company,
            ioc_type=ioc_type,
            value=ioc_value,
            defaults={
                'source': source,
                'description': description,
                'status': EnrichmentStatusEnum.PENDING
            }
        )
        
        structured_log['ioc_id'] = str(enriched_ioc.id)
        structured_log['is_new'] = created
        
        # Mark as being checked
        enriched_ioc.mark_checked()
        
        # Connect to Elasticsearch
        if not hasattr(settings, 'ELASTICSEARCH') or not settings.ELASTICSEARCH.get('hosts'):
            error_msg = "Elasticsearch is not configured"
            logger.error(
                error_msg,
                extra=structured_log
            )
            return {
                'status': 'error',
                'error': error_msg,
                'ioc_type': ioc_type,
                'ioc_value': ioc_value
            }
        
        # Get all feed indices from Elasticsearch
        from elasticsearch_dsl.connections import connections
        from elasticsearch.exceptions import NotFoundError
        
        # Get ES connection
        es = connections.get_connection()
        
        # Get all feed indices
        indices = []
        try:
            index_pattern = "feed_*"
            index_info = es.indices.get(index=index_pattern)
            indices = list(index_info.keys())
        except NotFoundError:
            logger.warning(
                "No feed indices found in Elasticsearch",
                extra=structured_log
            )
        
        if not indices:
            logger.info(
                f"No feed indices found, marking IOC as not found: {ioc_type}: {ioc_value}",
                extra=structured_log
            )
            enriched_ioc.mark_not_found()
            return {
                'status': 'not_found',
                'ioc_type': ioc_type,
                'ioc_value': ioc_value,
                'elapsed_time': time.time() - start_time
            }
        
        # Map Elasticsearch field based on IOC type
        es_field_map = {
            IOCTypeEnum.IP: "value.keyword",
            IOCTypeEnum.DOMAIN: "value.keyword",
            IOCTypeEnum.URL: "value.keyword",
            IOCTypeEnum.HASH_MD5: "value.keyword",
            IOCTypeEnum.HASH_SHA1: "value.keyword",
            IOCTypeEnum.HASH_SHA256: "value.keyword",
            IOCTypeEnum.EMAIL: "value.keyword",
            IOCTypeEnum.CVE: "value.keyword",
            IOCTypeEnum.FILENAME: "value.keyword",
            IOCTypeEnum.FILEPATH: "value.keyword",
            IOCTypeEnum.REGISTRY: "value.keyword",
            IOCTypeEnum.OTHER: "value.keyword"
        }
        
        field = es_field_map.get(ioc_type, "value.keyword")
        
        # Build search query
        search = Search(using=es, index=indices)
        search = search.query(ESQ("term", **{field: ioc_value}))
        search = search.source(['type', 'value', 'source', 'tags', 'confidence', 'tlp'])
        
        # Execute search
        search_results = search.execute()
        
        # Process results
        if search_results.hits.total.value > 0:
            # We found matches
            logger.info(
                f"Found {search_results.hits.total.value} matches for {ioc_type}: {ioc_value}",
                extra={**structured_log, 'match_count': search_results.hits.total.value}
            )
            
            # Track matches and collect tags
            matched_feeds = []
            all_tags = []
            max_confidence = 0.0
            
            # Get all matching feed IDs and metadata
            for hit in search_results:
                source_meta = hit.to_dict()
                feed_name = hit.meta.index.replace('feed_', '', 1)  # Extract feed name from index
                
                # Get corresponding FeedModule
                feed = FeedModule.objects.filter(
                    feed_type=feed_name
                ).first()
                
                if feed:
                    matched_feeds.append(str(feed.id))
                    
                    # Create or update match record
                    match, created = IOCFeedMatch.objects.update_or_create(
                        ioc=enriched_ioc,
                        feed=feed,
                        defaults={
                            'match_time': timezone.now(),
                            'feed_confidence': source_meta.get('confidence', 0.0),
                            'feed_tags': source_meta.get('tags', []),
                            'metadata': source_meta
                        }
                    )
                    
                    # Collect tags from all feeds
                    if 'tags' in source_meta and source_meta['tags']:
                        all_tags.extend(source_meta['tags'])
                    
                    # Track highest confidence
                    if 'confidence' in source_meta:
                        confidence = float(source_meta['confidence'])
                        if confidence > max_confidence:
                            max_confidence = confidence
            
            # Mark as enriched
            enriched_ioc.mark_enriched(
                confidence=max_confidence,
                matched_feeds=matched_feeds,
                tags=list(set(all_tags))  # Remove duplicates
            )
            
            # Update tenant's enriched index
            tenant_index = f"tenant_{company.id}_enriched_iocs"
            
            # Ensure index exists
            if not es.indices.exists(index=tenant_index):
                # Create the index
                es.indices.create(
                    index=tenant_index,
                    body={
                        "settings": {
                            "number_of_shards": 1,
                            "number_of_replicas": 1
                        },
                        "mappings": {
                            "properties": {
                                "ioc_type": {"type": "keyword"},
                                "value": {"type": "keyword"},
                                "status": {"type": "keyword"},
                                "first_seen": {"type": "date"},
                                "last_checked": {"type": "date"},
                                "last_matched": {"type": "date"},
                                "source": {"type": "keyword"},
                                "description": {"type": "text"},
                                "confidence": {"type": "float"},
                                "tlp": {"type": "keyword"},
                                "tags": {"type": "keyword"},
                                "matched_feeds": {"type": "keyword"},
                                "match_count": {"type": "integer"}
                            }
                        }
                    }
                )
            
            # Prepare document
            doc = {
                "ioc_type": enriched_ioc.ioc_type,
                "value": enriched_ioc.value,
                "status": enriched_ioc.status,
                "first_seen": enriched_ioc.first_seen.isoformat(),
                "last_checked": enriched_ioc.last_checked.isoformat(),
                "last_matched": enriched_ioc.last_matched.isoformat() if enriched_ioc.last_matched else None,
                "source": enriched_ioc.source,
                "description": enriched_ioc.description,
                "confidence": enriched_ioc.confidence,
                "tlp": enriched_ioc.tlp,
                "tags": enriched_ioc.tags,
                "matched_feeds": matched_feeds,
                "match_count": len(matched_feeds)
            }
            
            # Update Elasticsearch
            doc_id = enriched_ioc.elasticsearch_id
            es.index(
                index=tenant_index,
                id=doc_id,
                body=doc
            )
            
            # Update model with ES info
            enriched_ioc.es_index = tenant_index
            enriched_ioc.es_doc_id = doc_id
            enriched_ioc.save(update_fields=['es_index', 'es_doc_id'])
            
            return {
                'status': 'enriched',
                'ioc_id': str(enriched_ioc.id),
                'ioc_type': ioc_type,
                'ioc_value': ioc_value,
                'match_count': len(matched_feeds),
                'confidence': max_confidence,
                'tags': list(set(all_tags)),
                'elapsed_time': time.time() - start_time
            }
        else:
            # No matches found
            logger.info(
                f"No matches found for {ioc_type}: {ioc_value}",
                extra=structured_log
            )
            
            # Mark as not found
            enriched_ioc.mark_not_found()
            
            return {
                'status': 'not_found',
                'ioc_id': str(enriched_ioc.id),
                'ioc_type': ioc_type,
                'ioc_value': ioc_value,
                'elapsed_time': time.time() - start_time
            }
    
    except Exception as e:
        error_msg = f"Error enriching {ioc_type}: {ioc_value}: {str(e)}"
        logger.error(
            error_msg,
            extra={**structured_log, 'error': str(e), 'traceback': traceback.format_exc()},
            exc_info=True
        )
        
        # Retry with backoff
        self.retry(exc=e)
        
        return {
            'status': 'error',
            'error': error_msg,
            'ioc_type': ioc_type,
            'ioc_value': ioc_value
        }


@shared_task(
    bind=True,
    name='sentinelvision.tasks.enrichment_tasks.enrich_ioc_batch',
    acks_late=True,
    max_retries=3,
    retry_backoff=True,
    queue="sentineliq_soar_vision_enrichment"
)
def enrich_ioc_batch(self, company_id, ioc_ids=None, limit=100):
    """
    Enrich a batch of IOCs for a company.
    This is used by the reprocessing task.
    
    Args:
        company_id: UUID of the company
        ioc_ids: Optional list of IOC IDs to enrich
        limit: Maximum number of IOCs to process
        
    Returns:
        dict: Results of batch enrichment
    """
    start_time = time.time()
    
    structured_log = {
        'company_id': company_id,
        'ioc_count': len(ioc_ids) if ioc_ids else 0,
        'task_id': self.request.id
    }
    
    logger.info(
        f"Starting batch enrichment for company {company_id}",
        extra=structured_log
    )
    
    try:
        # Get company
        company = Company.objects.get(id=company_id)
        structured_log['company_name'] = company.name
        
        # Get IOCs to process
        if ioc_ids:
            # Process specific IOCs
            iocs = EnrichedIOC.objects.filter(
                company=company,
                id__in=ioc_ids
            )
        else:
            # Get pending or outdated IOCs
            cutoff_date = timezone.now() - timezone.timedelta(days=7)
            iocs = EnrichedIOC.objects.filter(
                company=company
            ).filter(
                Q(status=EnrichmentStatusEnum.PENDING) | 
                Q(last_checked__lt=cutoff_date)
            ).order_by(
                'last_checked'
            )[:limit]
        
        if not iocs.exists():
            logger.info(
                f"No IOCs found for batch enrichment for company {company.name}",
                extra=structured_log
            )
            return {
                'status': 'empty',
                'company_id': company_id,
                'company_name': company.name,
                'elapsed_time': time.time() - start_time
            }
        
        # Track results
        results = {
            'status': 'success',
            'company_id': company_id,
            'company_name': company.name,
            'total_processed': iocs.count(),
            'enriched_count': 0,
            'not_found_count': 0,
            'error_count': 0,
            'elapsed_time': 0,
            'ioc_results': []
        }
        
        # Process each IOC
        for ioc in iocs:
            try:
                # Enrich the IOC
                enrich_result = enrich_observable(
                    company_id=company_id,
                    ioc_type=ioc.ioc_type,
                    ioc_value=ioc.value,
                    source=ioc.source,
                    description=ioc.description
                )
                
                # Track result
                if enrich_result['status'] == 'enriched':
                    results['enriched_count'] += 1
                elif enrich_result['status'] == 'not_found':
                    results['not_found_count'] += 1
                else:
                    results['error_count'] += 1
                
                results['ioc_results'].append({
                    'ioc_id': str(ioc.id),
                    'ioc_type': ioc.ioc_type,
                    'ioc_value': ioc.value,
                    'status': enrich_result['status']
                })
            
            except Exception as e:
                logger.error(
                    f"Error processing IOC {str(ioc.id)}: {str(e)}",
                    extra={
                        'company_id': company_id,
                        'company_name': company.name,
                        'ioc_id': str(ioc.id),
                        'ioc_type': ioc.ioc_type,
                        'ioc_value': ioc.value,
                        'error': str(e)
                    },
                    exc_info=True
                )
                
                results['error_count'] += 1
                results['ioc_results'].append({
                    'ioc_id': str(ioc.id),
                    'ioc_type': ioc.ioc_type,
                    'ioc_value': ioc.value,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Calculate elapsed time
        results['elapsed_time'] = time.time() - start_time
        
        logger.info(
            f"Batch enrichment completed for company {company.name}. "
            f"Processed {results['total_processed']} IOCs in {results['elapsed_time']:.2f}s. "
            f"Enriched: {results['enriched_count']}, Not found: {results['not_found_count']}, Errors: {results['error_count']}",
            extra={
                'company_id': company_id,
                'company_name': company.name,
                'total_processed': results['total_processed'],
                'enriched_count': results['enriched_count'],
                'not_found_count': results['not_found_count'],
                'error_count': results['error_count'],
                'elapsed_time': results['elapsed_time']
            }
        )
        
        return results
    
    except Exception as e:
        error_msg = f"Error in batch enrichment for company {company_id}: {str(e)}"
        logger.error(
            error_msg,
            extra={**structured_log, 'error': str(e), 'traceback': traceback.format_exc()},
            exc_info=True
        )
        
        # Retry with backoff
        self.retry(exc=e)
        
        return {
            'status': 'error',
            'company_id': company_id,
            'error': error_msg
        }


@shared_task(
    bind=True,
    name='sentinelvision.tasks.enrichment_tasks.reenrich_observables',
    acks_late=True,
    queue="sentineliq_soar_vision_enrichment"
)
def reenrich_observables(self, days=7, limit=200):
    """
    Scan for outdated or pending IOCs across all tenants and trigger enrichment.
    This is a scheduled task that runs periodically.
    
    Args:
        days: Number of days back to look for IOCs to reprocess
        limit: Maximum number of IOCs to process per tenant
        
    Returns:
        dict: Results of the reenrichment operation
    """
    from companies.models import Company
    import time
    
    start_time = time.time()
    logger.info(
        f"Starting reenrichment of observables (days={days}, limit={limit})",
        extra={'days': days, 'limit': limit}
    )
    
    # Get all active companies
    companies = Company.objects.filter(is_active=True)
    
    results = {
        'total_companies': companies.count(),
        'processed_companies': 0,
        'total_iocs_scheduled': 0,
        'errors': 0,
        'company_results': []
    }
    
    # Define the cutoff date for IOCs to reprocess
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    
    # Process each company
    for company in companies:
        company_result = {
            'company_id': str(company.id),
            'company_name': company.name,
            'iocs_scheduled': 0,
            'status': 'success'
        }
        
        try:
            logger.info(
                f"Checking for IOCs to reenrich for company: {company.name}",
                extra={
                    'company_id': str(company.id),
                    'company_name': company.name
                }
            )
            
            # Get count of IOCs that need reprocessing
            ioc_count = EnrichedIOC.objects.filter(
                company=company
            ).filter(
                Q(status=EnrichmentStatusEnum.PENDING) | 
                Q(last_checked__lt=cutoff_date)
            ).count()
            
            if ioc_count > 0:
                # Schedule batch enrichment
                task = enrich_ioc_batch.delay(
                    company_id=str(company.id),
                    limit=limit
                )
                
                company_result['iocs_scheduled'] = min(ioc_count, limit)
                company_result['task_id'] = task.id
                
                results['total_iocs_scheduled'] += company_result['iocs_scheduled']
                
                logger.info(
                    f"Scheduled {company_result['iocs_scheduled']} IOCs for reenrichment for company {company.name}",
                    extra={
                        'company_id': str(company.id),
                        'company_name': company.name,
                        'ioc_count': company_result['iocs_scheduled'],
                        'task_id': task.id
                    }
                )
            else:
                logger.info(
                    f"No IOCs found for reenrichment for company {company.name}",
                    extra={
                        'company_id': str(company.id),
                        'company_name': company.name
                    }
                )
        
        except Exception as e:
            company_result['status'] = 'error'
            company_result['error'] = str(e)
            results['errors'] += 1
            
            logger.error(
                f"Error reenriching IOCs for company {company.name}: {str(e)}",
                extra={
                    'company_id': str(company.id),
                    'company_name': company.name,
                    'error': str(e)
                },
                exc_info=True
            )
        
        results['processed_companies'] += 1
        results['company_results'].append(company_result)
    
    # Calculate execution time
    execution_time = time.time() - start_time
    results['execution_time_seconds'] = execution_time
    
    logger.info(
        f"Reenrichment scan completed in {execution_time:.2f}s. "
        f"Scheduled {results['total_iocs_scheduled']} IOCs across {results['processed_companies']} companies.",
        extra={
            'execution_time': execution_time,
            'total_iocs': results['total_iocs_scheduled'],
            'total_companies': results['processed_companies'],
            'errors': results['errors']
        }
    )
    
    return results 