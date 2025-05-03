import json
import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from incidents.models import Incident
from alerts.models import Alert
from companies.models import Company
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()


class IncidentAPITestCase(APITestCase):
    """Test case for Incident API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create a company
        self.company = Company.objects.create(
            name="Test Company",
        )
        
        # Create superuser (adminsentinel)
        self.admin = User.objects.create_superuser(
            username="admin_incident",
            email="admin_incident@sentineliq.com",
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
        
        # Create test incident
        self.incident = Incident.objects.create(
            title="Test Incident",
            description="Test incident description",
            summary="Brief summary of test incident",
            severity=Incident.Severity.MEDIUM,
            status=Incident.Status.OPEN,
            company=self.company,
            created_by=self.company_admin,
            timeline=[{
                "id": str(uuid.uuid4()),
                "title": "Incident created",
                "content": "Incident was created manually",
                "type": "creation",
                "timestamp": "2023-01-01T12:00:00Z",
                "created_by": str(self.company_admin.id)
            }]
        )
        
        # Create a test alert
        self.alert = Alert.objects.create(
            title="Test Alert",
            description="Test alert description",
            severity=Alert.Severity.HIGH,
            source="Test Source",
            source_ref="TEST-123",
            company=self.company,
            created_by=self.company_admin
        )
        
        # Add alert to incident
        self.incident.related_alerts.add(self.alert)
        
        # URLs - using direct paths instead of reverse lookup
        self.incident_list_url = '/api/v1/incidents/'
        self.incident_detail_url = f'/api/v1/incidents/{self.incident.id}/'
        self.incident_timeline_url = f'/api/v1/incidents/{self.incident.id}/add-timeline-entry/'
        self.incident_assign_url = f'/api/v1/incidents/{self.incident.id}/assign/'
    
    def test_list_incidents(self):
        """Test that users can list incidents based on their permissions."""
        # Test company admin can list incidents
        self.client.force_authenticate(user=self.company_admin)
        response = self.client.get(self.incident_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        
        # Test company analyst can list incidents
        self.client.force_authenticate(user=self.company_analyst)
        response = self.client.get(self.incident_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        
        # Test superuser can list all incidents
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.incident_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
    
    def test_create_incident(self):
        """Test that only authorized users can create incidents."""
        self.client.force_authenticate(user=self.company_admin)
        data = {
            'title': 'New Incident',
            'description': 'New incident description',
            'summary': 'Brief summary',
            'severity': Incident.Severity.HIGH,
            'tags': ['malware', 'ransomware'],
            'tlp': Incident.TLP.GREEN,
            'pap': Incident.PAP.GREEN
        }
        response = self.client.post(self.incident_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Incident.objects.count(), 2)
        
        # Create a read-only user to test permission restrictions
        read_only_user = User.objects.create_user(
            username="readonly_incident",
            email="readonly_incident@testcompany.com",
            password="password123",
            role="read_only",
            company=self.company,
        )
        
        # Test read-only user cannot create incidents
        self.client.force_authenticate(user=read_only_user)
        data['title'] = 'Another Incident'
        response = self.client.post(self.incident_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_add_timeline_entry(self):
        """Test adding a timeline entry to an incident."""
        self.client.force_authenticate(user=self.company_admin)
        
        data = {
            'title': 'Investigation update',
            'content': 'Found suspicious network traffic',
            'event_type': 'note'
        }
        
        response = self.client.post(self.incident_timeline_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify timeline entry was added
        self.incident.refresh_from_db()
        self.assertEqual(len(self.incident.timeline), 2)
        self.assertEqual(self.incident.timeline[1]['title'], 'Investigation update')
    
    def test_assign_incident(self):
        """Test assigning an incident to a user."""
        self.client.force_authenticate(user=self.company_admin)
        
        # Create a new user to assign the incident to
        test_assignee = User.objects.create_user(
            username="test_assignee_for_incident",
            email="test_assignee@testcompany.com", 
            password="password123",
            role="analyst_company",
            company=self.company,
        )
        
        # Show user ID for debugging
        print(f"Created test_assignee with ID: {test_assignee.id}")
        print(f"Type of ID: {type(test_assignee.id)}")
        print(f"String representation: {str(test_assignee.id)}")
        
        # Make sure this user exists and we can retrieve it
        test_lookup = User.objects.filter(id=test_assignee.id).exists()
        print(f"Can find user by direct ID lookup: {test_lookup}")
        
        test_lookup_str = User.objects.filter(id=str(test_assignee.id)).exists()
        print(f"Can find user by string ID lookup: {test_lookup_str}")
        
        # Prepare assignment data with user ID as string
        data = {
            'assignee': str(test_assignee.id)
        }
        
        print(f"Assigning incident to user ID: {test_assignee.id}")
        
        # Make the request
        response = self.client.post(self.incident_assign_url, data, format='json')
        if response.status_code != status.HTTP_200_OK:
            print(f"Assignment error: {response.data}")
            print(f"Response status code: {response.status_code}")
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify incident was assigned
        self.incident.refresh_from_db()
        
        # Check if assignee is set correctly
        self.assertIsNotNone(self.incident.assignee)
        self.assertEqual(self.incident.assignee.id, test_assignee.id)
        
        # Verify timeline entry was added
        self.assertTrue(any(entry['title'] == 'Incident assigned' for entry in self.incident.timeline))
    
    def test_filter_incidents(self):
        """Test filtering incidents by various criteria."""
        # Create another incident with different status
        Incident.objects.create(
            title="Another Incident",
            description="Description of another incident",
            severity=Incident.Severity.HIGH,
            status=Incident.Status.IN_PROGRESS,
            company=self.company,
            created_by=self.company_admin
        )
        
        self.client.force_authenticate(user=self.company_admin)
        
        # Test filtering by status
        response = self.client.get(f"{self.incident_list_url}?status=open")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['status'], 'open')
        
        # Test filtering by severity
        response = self.client.get(f"{self.incident_list_url}?severity=high")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['severity'], 'high') 