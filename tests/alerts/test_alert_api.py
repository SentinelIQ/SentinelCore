import json
import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from alerts.models import Alert
from companies.models import Company
from django.contrib.auth import get_user_model

User = get_user_model()


class AlertAPITestCase(APITestCase):
    """Test case for Alert API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create a company
        self.company = Company.objects.create(
            name="Test Company",
        )
        
        # Create superuser (adminsentinel)
        self.admin = User.objects.create_superuser(
            username="admin_alert_api",
            email="admin_alert_api@sentineliq.com",
            password="adminpassword",
            role="adminsentinel",
        )
        
        # Create company admin
        self.company_admin = User.objects.create_user(
            username="companyadmin",
            email="admin@testcompany.com",
            password="adminpassword",
            role="admin_company",
            company=self.company,
        )
        
        # Create company analyst
        self.company_analyst = User.objects.create_user(
            username="companyanalyst",
            email="analyst@testcompany.com",
            password="analystpassword",
            role="analyst_company",
            company=self.company,
        )
        
        # Create test alert
        self.alert = Alert.objects.create(
            title="Test Alert",
            description="Test alert description",
            severity=Alert.Severity.MEDIUM,
            source="Test Source",
            source_ref="TEST-123",
            company=self.company,
            created_by=self.company_admin,
            external_source="SIEM",
            observable_data={"ip": ["192.168.1.1", "10.0.0.1"]},
            raw_payload={"original": "data"}
        )
        
        # URLs using direct paths instead of reverse
        self.alert_list_url = '/api/v1/alerts/'
        self.alert_detail_url = f'/api/v1/alerts/{self.alert.id}/'
        self.alert_ingest_url = '/api/v1/alerts/ingest/'
        self.alert_escalate_url = f'/api/v1/alerts/{self.alert.id}/escalate/'
    
    def test_list_alerts(self):
        """Test that users can list alerts based on their permissions."""
        # Test company admin can list alerts
        self.client.force_authenticate(user=self.company_admin)
        response = self.client.get(self.alert_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        
        # Test company analyst can list alerts
        self.client.force_authenticate(user=self.company_analyst)
        response = self.client.get(self.alert_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        
        # Test superuser can list all alerts
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.alert_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
    
    def test_create_alert(self):
        """Test that only authorized users can create alerts."""
        self.client.force_authenticate(user=self.company_admin)
        data = {
            'title': 'New Alert',
            'description': 'New alert description',
            'severity': Alert.Severity.HIGH,
            'source': 'Test Source',
            'source_ref': 'TEST-NEW-123',
            'external_source': 'Firewall',
            'observable_data': {'domain': ['example.com']},
            'raw_payload': {'new': 'data'}
        }
        response = self.client.post(self.alert_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Alert.objects.count(), 2)
        
        # Create a read-only user to test permission restrictions
        read_only_user = User.objects.create_user(
            username="readonly_user",
            email="readonly@testcompany.com",
            password="password123",
            role="read_only",
            company=self.company,
        )
        
        # Test read-only user cannot create alerts
        self.client.force_authenticate(user=read_only_user)
        data['source_ref'] = 'TEST-NEW-124'
        response = self.client.post(self.alert_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_ingest_alert(self):
        """Test the alert ingestion endpoint."""
        self.client.force_authenticate(user=self.company_admin)
        
        # Generate a unique source_ref to avoid test conflicts
        unique_source_ref = f"MISP-{uuid.uuid4()}"
        
        data = {
            'title': 'Ingested Alert',
            'description': 'Alert from external system',
            'severity': Alert.Severity.CRITICAL,
            'source': 'MISP',
            'source_ref': unique_source_ref,
            'external_source': 'MISP',
            'observable_data': {'hash': ['aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d']},
            'raw_payload': {'event_id': '1234', 'attributes': []},
            # Company_id is not needed when logged in as a user with a company
        }
        
        # Print the request data for debugging
        print(f"Ingest test data: {data}")
        
        # First ingest - should create a new alert
        response = self.client.post(self.alert_ingest_url, data, format='json')
        
        # Print the response for debugging
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Ingest error: {response.data}")
            
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Alert.objects.count(), 2)
        
        # Second ingest - should detect duplicate
        response = self.client.post(self.alert_ingest_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Alert.objects.count(), 2)
        self.assertTrue(response.data['data']['duplicate'])
    
    def test_escalate_alert(self):
        """Test escalating an alert to an incident."""
        self.client.force_authenticate(user=self.company_admin)
        response = self.client.post(self.alert_escalate_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify alert status is updated
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, Alert.Status.ESCALATED)
        
        # Verify incident was created
        incident_id = response.data['data']['incident_id']
        self.assertTrue(self.alert.incidents.filter(id=incident_id).exists()) 