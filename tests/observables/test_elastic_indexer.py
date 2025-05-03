import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from observables.services.elastic import BaseElasticIndexer
from observables.models import Observable
from companies.models import Company
from django.contrib.auth import get_user_model

User = get_user_model()


class MockElasticsearch:
    """Mock Elasticsearch client for testing"""
    
    def __init__(self, *args, **kwargs):
        self.indices = MagicMock()
        self.indices.exists.return_value = False
        self.indices.create.return_value = {"acknowledged": True}
        
        # Mock for index method
        self.index_response = {"_id": "test_id", "result": "created"}
        
        # Mock for get method
        self.get_response = {"_id": "test_id", "_source": {}, "found": False}
    
    def index(self, *args, **kwargs):
        return self.index_response
    
    def get(self, *args, **kwargs):
        return self.get_response
    
    def search(self, *args, **kwargs):
        return {"hits": {"hits": []}}


@patch('elasticsearch.Elasticsearch', MockElasticsearch)
class ElasticIndexerTest(TestCase):
    """Test suite for the Elasticsearch indexer"""

    def setUp(self):
        # Create test company
        self.company = Company.objects.create(
            name="Test Company"
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword",
            company=self.company
        )
        
        # Create test observable
        self.observable = Observable.objects.create(
            type=Observable.Type.IP,
            value="192.168.1.1",
            description="Test IP",
            company=self.company,
            created_by=self.user,
            is_ioc=True
        )
        
        # Mock Elasticsearch in the indexer class
        self.es_mock = MockElasticsearch()
        with patch('elasticsearch.Elasticsearch', return_value=self.es_mock):
            # Initialize indexer with company ID
            self.indexer = BaseElasticIndexer(company_id=self.company.id)
            self.indexer.es_client = self.es_mock

    def test_index_name_format(self):
        """Test that index name is formatted correctly"""
        self.assertEqual(
            self.indexer.index_name,
            f"observables_v1_{self.company.id}"
        )
    
    @patch('elasticsearch.Elasticsearch')
    def test_ensure_index_exists(self, mock_es):
        """Test ensure_index_exists method"""
        # Set up the mock
        mock_es_instance = mock_es.return_value
        mock_es_instance.indices.exists.return_value = False
        mock_es_instance.indices.create.return_value = {"acknowledged": True}
        
        # Set mock client
        self.indexer.es_client = mock_es_instance
        
        # Index doesn't exist yet, should create it
        result = self.indexer.ensure_index_exists()
        
        # Verify result is True
        self.assertTrue(result)
        
        # Verify indices.create was called
        mock_es_instance.indices.exists.assert_called_once()
        mock_es_instance.indices.create.assert_called_once()
    
    def test_generate_doc_id(self):
        """Test document ID generation"""
        doc_id = self.indexer._generate_doc_id(
            "ip",
            "192.168.1.1",
            self.company.id
        )
        
        # Check that we got a hex string (SHA256 hash)
        self.assertTrue(len(doc_id) == 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in doc_id))
    
    @patch('elasticsearch.Elasticsearch')
    def test_index_observable(self, mock_es):
        """Test indexing an observable"""
        # Set up the mock
        mock_es_instance = mock_es.return_value
        mock_es_instance.indices.exists.return_value = True  # Index exists
        mock_es_instance.index.return_value = {"_id": "test_id", "result": "created"}
        
        # Set mock client
        self.indexer.es_client = mock_es_instance
        
        # Run the indexing
        result = self.indexer.index_observable(self.observable)
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], "created")
        
        # Verify index method was called
        mock_es_instance.index.assert_called_once()
    
    def test_tenant_isolation(self):
        """Test tenant isolation in indexing"""
        # Create a different company
        company2 = Company.objects.create(
            name="Another Company"
        )
        
        # Initialize indexer with different company ID
        indexer2 = BaseElasticIndexer(company_id=company2.id)
        
        # Try to index observable that belongs to a different company
        result = indexer2.index_observable(self.observable)
        
        # Should get an error due to tenant mismatch
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Tenant isolation violation")
    
    def test_index_name_without_company(self):
        """Test that index_name raises error when no company_id is provided"""
        indexer = BaseElasticIndexer()  # No company_id
        
        # Should raise ValueError
        with self.assertRaises(ValueError):
            indexer.index_name 