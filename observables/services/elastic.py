import json
import logging
import hashlib
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('api')


class BaseElasticIndexer:
    """
    Base class for Elasticsearch indexing operations with tenant isolation.
    Handles index versioning, document lifecycle, and tenant security.
    """
    INDEX_VERSION = "v1"
    DEFAULT_TTL_DAYS = 90
    
    def __init__(self, company_id=None):
        """
        Initialize the indexer with company-specific context.
        
        Args:
            company_id: UUID of the company for tenant isolation
        """
        self.es_client = Elasticsearch(
            hosts=settings.ELASTICSEARCH_HOSTS,
            basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD),
            verify_certs=settings.ELASTICSEARCH_VERIFY_CERTS
        )
        self.company_id = company_id
        
    @property
    def index_name(self):
        """
        Get the versioned, tenant-specific index name.
        
        Returns:
            str: Index name in format observables_v1_<company_id>
        """
        if not self.company_id:
            raise ValueError("Company ID is required for tenant isolation")
        
        return f"observables_{self.INDEX_VERSION}_{self.company_id}"
    
    def ensure_index_exists(self):
        """
        Check if the index exists and create it if it doesn't.
        
        Returns:
            bool: True if index exists/created, False on error
        """
        try:
            if not self.es_client.indices.exists(index=self.index_name):
                # Create index with company isolation and TTL
                self.es_client.indices.create(
                    index=self.index_name,
                    body={
                        "settings": {
                            "number_of_shards": 1,
                            "number_of_replicas": 1,
                            "index.lifecycle.name": "observable_retention_policy",
                            "index.lifecycle.rollover_alias": "observables"
                        },
                        "mappings": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "value": {"type": "text", "fields": {"raw": {"type": "keyword"}}},
                                "company_id": {"type": "keyword"},
                                "first_seen": {"type": "date"},
                                "last_seen": {"type": "date"},
                                "tags": {"type": "keyword"},
                                "sources": {"type": "keyword"},
                                "is_ioc": {"type": "boolean"},
                                "enrichment": {"type": "object", "dynamic": True},
                                "sightings_count": {"type": "integer"},
                                "related_ids": {"type": "keyword"}
                            }
                        }
                    }
                )
                logger.info(f"Created Elasticsearch index {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating Elasticsearch index: {str(e)}")
            return False
    
    def index_observable(self, observable, additional_data=None):
        """
        Index an observable in Elasticsearch with deduplication via upsert.
        
        Args:
            observable: Observable model instance
            additional_data: Any additional data to include in the document
            
        Returns:
            dict: Indexing result with status and details
        """
        if observable.company.id != self.company_id:
            logger.error(f"Tenant mismatch: Observable belongs to {observable.company.id}, " 
                         f"indexer initialized with {self.company_id}")
            return {"status": "error", "message": "Tenant isolation violation"}
        
        try:
            # Ensure index exists
            if not self.ensure_index_exists():
                return {"status": "error", "message": "Index creation failed"}
            
            # Create document with all necessary fields
            doc = {
                "type": observable.type,
                "value": observable.value,
                "company_id": str(self.company_id),
                "last_seen": datetime.now().isoformat(),
                "tags": observable.tags,
                "is_ioc": observable.is_ioc,
                "enrichment": observable.enrichment_data,
                "related_ids": [],
                "sources": ["postgresql"],
                "pg_id": str(observable.id)
            }
            
            # Add/update additional data if provided
            if additional_data:
                doc.update(additional_data)
            
            # Generate hash-based _id for deduplication
            doc_id = self._generate_doc_id(observable.type, observable.value, self.company_id)
            
            # Check if document already exists
            try:
                existing = self.es_client.get(index=self.index_name, id=doc_id)
                if existing["found"]:
                    # Update existing document with merge logic
                    # Set first_seen from existing doc if available
                    doc["first_seen"] = existing["_source"].get("first_seen", datetime.now().isoformat())
                    # Increment sightings counter
                    doc["sightings_count"] = existing["_source"].get("sightings_count", 0) + 1
                    # Merge tags without duplicates
                    existing_tags = set(existing["_source"].get("tags", []))
                    new_tags = set(doc["tags"])
                    doc["tags"] = list(existing_tags | new_tags)
                    # Merge sources without duplicates
                    existing_sources = set(existing["_source"].get("sources", []))
                    new_sources = set(doc["sources"])
                    doc["sources"] = list(existing_sources | new_sources)
            except Exception:
                # Document doesn't exist, set first_seen
                doc["first_seen"] = datetime.now().isoformat()
                doc["sightings_count"] = 1
            
            # Index with upsert to handle race conditions
            response = self.es_client.index(
                index=self.index_name,
                id=doc_id,
                document=doc,
                refresh=True
            )
            
            logger.info(
                f"Indexed observable in Elasticsearch: type={observable.type}, "
                f"value={observable.value}, company={self.company_id}"
            )
            
            return {
                "status": "success", 
                "doc_id": doc_id,
                "_id": response["_id"],
                "result": response["result"]
            }
        
        except Exception as e:
            logger.error(
                f"Error indexing observable in Elasticsearch: {str(e)}",
                extra={
                    "observable_type": observable.type,
                    "observable_value": observable.value,
                    "company_id": str(self.company_id),
                    "error": str(e)
                }
            )
            return {"status": "error", "message": str(e)}
    
    def _generate_doc_id(self, type_val, value, company_id):
        """
        Generate a deterministic document ID as SHA256 hash of key fields.
        
        Args:
            type_val: Observable type
            value: Observable value
            company_id: Company UUID
            
        Returns:
            str: SHA256 hash for document ID
        """
        # Create composite key and hash it
        key = f"{type_val}:{value}:{company_id}"
        return hashlib.sha256(key.encode()).hexdigest()


class ElasticLookupService:
    """
    Service for querying and searching observables from Elasticsearch
    with tenant isolation enforced.
    """
    
    def __init__(self, company_id=None):
        """
        Initialize the lookup service with company-specific context.
        
        Args:
            company_id: UUID of the company for tenant isolation
        """
        self.es_client = Elasticsearch(
            hosts=settings.ELASTICSEARCH_HOSTS,
            basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD),
            verify_certs=settings.ELASTICSEARCH_VERIFY_CERTS
        )
        self.company_id = company_id
        self.indexer = BaseElasticIndexer(company_id)
    
    def find_by_value(self, value, limit=100):
        """
        Find observables by exact or partial value.
        
        Args:
            value: Value to search for
            limit: Maximum number of results to return
            
        Returns:
            list: Matching observables
        """
        if not self.company_id:
            logger.error("Company ID is required for tenant isolation")
            return []
        
        try:
            # Search with tenant isolation enforced
            results = self.es_client.search(
                index=self.indexer.index_name,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"value": value}},
                                {"term": {"company_id": str(self.company_id)}}
                            ]
                        }
                    },
                    "size": limit
                }
            )
            
            hits = results.get("hits", {}).get("hits", [])
            return [hit["_source"] for hit in hits]
        
        except Exception as e:
            logger.error(
                f"Error searching Elasticsearch: {str(e)}",
                extra={
                    "value": value,
                    "company_id": str(self.company_id),
                    "error": str(e)
                }
            )
            return []
    
    def find_by_type_and_value(self, type_val, value):
        """
        Find an observable by exact type and value with tenant isolation.
        
        Args:
            type_val: Observable type
            value: Observable value
            
        Returns:
            dict: The observable document or None
        """
        if not self.company_id:
            logger.error("Company ID is required for tenant isolation")
            return None
        
        try:
            # Generate the document ID
            doc_id = self.indexer._generate_doc_id(type_val, value, self.company_id)
            
            # Try to get the document directly by ID (most efficient)
            try:
                result = self.es_client.get(
                    index=self.indexer.index_name,
                    id=doc_id
                )
                if result["found"]:
                    return result["_source"]
            except Exception:
                # Document not found by ID, try search as fallback
                pass
            
            # Search with exact match
            results = self.es_client.search(
                index=self.indexer.index_name,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"type": type_val}},
                                {"term": {"value.raw": value}},
                                {"term": {"company_id": str(self.company_id)}}
                            ]
                        }
                    },
                    "size": 1
                }
            )
            
            hits = results.get("hits", {}).get("hits", [])
            return hits[0]["_source"] if hits else None
        
        except Exception as e:
            logger.error(
                f"Error searching Elasticsearch: {str(e)}",
                extra={
                    "type": type_val,
                    "value": value,
                    "company_id": str(self.company_id),
                    "error": str(e)
                }
            )
            return None
    
    def search_observables(self, query_string, limit=50, days=90, filters=None):
        """
        Advanced search for observables with tenant isolation and filtering.
        
        Args:
            query_string: Search query string
            limit: Maximum number of results (default: 50)
            days: How many days back to search (default: 90)
            filters: Dictionary of additional filters to apply
            
        Returns:
            dict: Search results and metadata
        """
        if not self.company_id:
            logger.error("Company ID is required for tenant isolation")
            return {"total": 0, "results": []}
        
        # Calculate date threshold for time-based filtering
        time_threshold = None
        if days:
            time_threshold = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Build bool query
        must_clauses = [{"term": {"company_id": str(self.company_id)}}]
        
        # Add time threshold filter if specified
        if time_threshold:
            must_clauses.append({
                "range": {
                    "last_seen": {"gte": time_threshold}
                }
            })
        
        # Add value search (multi-match for better results)
        must_clauses.append({
            "multi_match": {
                "query": query_string,
                "fields": ["value^3", "value.raw^5", "tags^2", "sources"],
                "type": "best_fields",
                "operator": "and"
            }
        })
        
        # Add filters if provided
        if filters:
            for key, value in filters.items():
                if key == 'type':
                    must_clauses.append({"term": {"type": value}})
                elif key == 'is_ioc':
                    must_clauses.append({"term": {"is_ioc": value}})
                elif key == 'tags' and isinstance(value, list):
                    must_clauses.append({"terms": {"tags": value}})
        
        try:
            # Execute search with filters
            results = self.es_client.search(
                index=self.indexer.index_name,
                body={
                    "query": {
                        "bool": {
                            "must": must_clauses
                        }
                    },
                    "size": limit,
                    "sort": [
                        {"last_seen": {"order": "desc"}},
                        {"sightings_count": {"order": "desc"}}
                    ],
                    "highlight": {
                        "fields": {
                            "value": {},
                            "tags": {}
                        }
                    }
                }
            )
            
            # Process results and add highlights
            hits = results.get("hits", {}).get("hits", [])
            processed_results = []
            
            for hit in hits:
                result = hit["_source"]
                # Add highlight if available
                if "highlight" in hit:
                    result["highlights"] = hit["highlight"]
                # Add score
                result["score"] = hit["_score"]
                processed_results.append(result)
            
            return {
                "total": results.get("hits", {}).get("total", {}).get("value", 0),
                "results": processed_results
            }
            
        except Exception as e:
            logger.error(
                f"Error searching Elasticsearch: {str(e)}",
                extra={
                    "query": query_string,
                    "company_id": str(self.company_id),
                    "error": str(e)
                },
                exc_info=True
            )
            return {"total": 0, "results": []} 