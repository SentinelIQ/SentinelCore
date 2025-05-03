import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from observables.services.elastic import ElasticLookupService
from observables.models import Observable
from companies.models import Company
from django.contrib.auth import get_user_model

User = get_user_model()


class MockElasticsearch:
    """Mock Elasticsearch client for testing"""
    
    def __init__(self, *args, **kwargs):
        self.indices = MagicMock()
        self.indices.exists.return_value = True
        
        # Mock search results
        self.search_results = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_id": "test_id",
                        "_source": {
                            "type": "ip",
                            "value": "192.168.1.1",
                            "company_id": "test_company_id",
                            "tags": ["malicious", "c2"],
                            "is_ioc": True,
                            "first_seen": "2023-01-01T00:00:00Z",
                            "last_seen": "2023-01-02T00:00:00Z",
                            "sightings_count": 5
                        }
                    }
                ]
            }
        }
        
        # Mock get results
        self.get_response = {
            "_id": "test_id",
            "_source": {
                "type": "ip",
                "value": "192.168.1.1",
                "company_id": "test_company_id",
                "tags": ["malicious", "c2"],
                "is_ioc": True
            },
            "found": True
        }
    
    def search(self, *args, **kwargs):
        return self.search_results
    
    def get(self, *args, **kwargs):
        return self.get_response


@patch('elasticsearch.Elasticsearch', MockElasticsearch)
class ElasticLookupServiceTest(TestCase):
    """Test suite for the Elasticsearch lookup service"""

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
        
        # Mock Elasticsearch in the lookup service
        self.es_mock = MockElasticsearch()
        with patch('elasticsearch.Elasticsearch', return_value=self.es_mock):
            # Initialize lookup service with company ID
            self.lookup_service = ElasticLookupService(company_id=self.company.id)
            self.lookup_service.es_client = self.es_mock
    
    @patch('elasticsearch.Elasticsearch')
    def test_find_by_value(self, mock_es):
        """Test finding observables by value"""
        # Configure the mock
        mock_es_instance = mock_es.return_value
        mock_es_instance.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_id": "test_id",
                        "_source": {
                            "type": "ip",
                            "value": "192.168.1.1",
                            "company_id": str(self.company.id),
                            "tags": ["malicious", "c2"],
                            "is_ioc": True
                        }
                    }
                ]
            }
        }
        
        # Update mock client
        self.lookup_service.es_client = mock_es_instance
        
        # Run the search
        results = self.lookup_service.find_by_value("192.168.1.1")
        
        # Check results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "ip")
        self.assertEqual(results[0]["value"], "192.168.1.1")
        
        # Verify search was called
        mock_es_instance.search.assert_called_once()
    
    @patch('elasticsearch.Elasticsearch')
    def test_find_by_type_and_value(self, mock_es):
        """Test finding an observable by type and value"""
        # Configure the mock
        mock_es_instance = mock_es.return_value
        mock_es_instance.get.return_value = {
            "_id": "test_id",
            "_source": {
                "type": "ip",
                "value": "192.168.1.1",
                "company_id": str(self.company.id),
                "tags": ["malicious", "c2"],
                "is_ioc": True
            },
            "found": True
        }
        
        # Update mock client
        self.lookup_service.es_client = mock_es_instance
        
        # Run the search
        result = self.lookup_service.find_by_type_and_value("ip", "192.168.1.1")
        
        # Check result
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "ip")
        self.assertEqual(result["value"], "192.168.1.1")
        self.assertTrue(result["is_ioc"])
        
        # Verify get was called
        mock_es_instance.get.assert_called_once()
    
    def test_company_id_required(self):
        """Test that company_id is required for tenant isolation"""
        lookup_service = ElasticLookupService()  # No company_id
        
        # find_by_value should return empty list
        results = lookup_service.find_by_value("192.168.1.1")
        self.assertEqual(results, [])
        
        # find_by_type_and_value should return None
        result = lookup_service.find_by_type_and_value("ip", "192.168.1.1")
        self.assertIsNone(result)
    
    def test_search_params(self):
        """Test that search parameters include tenant isolation"""
        with patch.object(self.lookup_service.es_client, 'search') as mock_search:
            mock_search.return_value = {"hits": {"hits": []}}
            
            self.lookup_service.find_by_value("192.168.1.1")
            
            # Verify search was called with correct parameters
            args, kwargs = mock_search.call_args
            
            # Check body contains company_id for tenant isolation
            self.assertIn("body", kwargs)
            self.assertIn("query", kwargs["body"])
            self.assertIn("bool", kwargs["body"]["query"])
            self.assertIn("must", kwargs["body"]["query"]["bool"])
            
            # At least one must clause should have company_id
            has_company_filter = False
            for clause in kwargs["body"]["query"]["bool"]["must"]:
                if "term" in clause and "company_id" in clause["term"]:
                    has_company_filter = True
                    break
            
            self.assertTrue(has_company_filter, "Search query must include company_id filter") 