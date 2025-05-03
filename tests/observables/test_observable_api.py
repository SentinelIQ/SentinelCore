import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from observables.models import Observable
from alerts.models import Alert
from incidents.models import Incident
from companies.models import Company
from django.contrib.auth import get_user_model

User = get_user_model()


class ObservableAPITestCase(APITestCase):
    """Test case for Observable API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create a company
        self.company = Company.objects.create(
            name="Test Company",
        )
        
        # Create superuser (adminsentinel)
        self.admin = User.objects.create_superuser(
            username="admin_observable",
            email="admin_observable@sentineliq.com",
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
            created_by=self.company_admin
        )
        
        # Create test incident
        self.incident = Incident.objects.create(
            title="Test Incident",
            description="Test incident description",
            severity=Incident.Severity.MEDIUM,
            status=Incident.Status.OPEN,
            company=self.company,
            created_by=self.company_admin
        )
        
        # Create test observable
        self.observable = Observable.objects.create(
            type=Observable.Type.IP,
            value="192.168.1.1",
            description="Suspicious IP",
            company=self.company,
            created_by=self.company_admin,
            alert=self.alert,
            tags=["suspicious", "internal"]
        )
        
        # URLs - using direct paths instead of reverse lookup
        self.observable_list_url = '/api/v1/observables/'
        self.observable_detail_url = f'/api/v1/observables/{self.observable.id}/'
        self.observable_ioc_url = f'/api/v1/observables/{self.observable.id}/mark-as-ioc/'
    
    def test_list_observables(self):
        """Test that users can list observables based on their permissions."""
        # Test company admin can list observables
        self.client.force_authenticate(user=self.company_admin)
        response = self.client.get(self.observable_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        
        # Test company analyst can list observables
        self.client.force_authenticate(user=self.company_analyst)
        response = self.client.get(self.observable_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        
        # Test superuser can list all observables
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.observable_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
    
    def test_create_observable(self):
        """Test that only authorized users can create observables."""
        self.client.force_authenticate(user=self.company_admin)
        data = {
            'type': Observable.Type.DOMAIN,
            'value': 'example.com',
            'description': 'Suspicious domain',
            'tags': ['phishing', 'malicious'],
            'incident': str(self.incident.id)
        }
        response = self.client.post(self.observable_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Observable.objects.count(), 2)
        
        # Test deduplication
        response = self.client.post(self.observable_list_url, data, format='json')
        # It should return the existing observable in our new response format
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Observable.objects.count(), 2)
        
        # Create a read-only user to test permission restrictions
        read_only_user = User.objects.create_user(
            username="readonly_observable",
            email="readonly_observable@testcompany.com",
            password="password123",
            role="read_only",
            company=self.company,
        )
        
        # Test read-only user cannot create observables
        self.client.force_authenticate(user=read_only_user)
        data = {
            'type': Observable.Type.EMAIL,
            'value': 'phishing@example.com',
            'description': 'Phishing email',
            'tags': ['phishing'],
            'incident': str(self.incident.id)
        }
        response = self.client.post(self.observable_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_mark_as_ioc(self):
        """Test marking an observable as an IOC."""
        self.client.force_authenticate(user=self.company_admin)
        
        data = {
            'is_ioc': True,
            'reason': 'Confirmed malicious'
        }
        
        response = self.client.post(self.observable_ioc_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify observable was marked as IOC
        self.observable.refresh_from_db()
        self.assertTrue(self.observable.is_ioc)
    
    def test_filter_observables(self):
        """Test filtering observables by various criteria."""
        # Create observables with different types
        Observable.objects.create(
            type=Observable.Type.URL,
            value="https://example.com/malicious",
            company=self.company,
            created_by=self.company_admin,
            incident=self.incident,
            is_ioc=True,
            tags=["malicious"]
        )
        
        self.client.force_authenticate(user=self.company_admin)
        
        # Test filtering by type
        response = self.client.get(f"{self.observable_list_url}?type=ip")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['type'], 'ip')
        
        # Test filtering by is_ioc
        response = self.client.get(f"{self.observable_list_url}?is_ioc=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertTrue(response.data['data']['results'][0]['is_ioc']) 