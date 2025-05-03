from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from auth_app.models import User
from companies.models import Company
from alerts.models import Alert
from incidents.models import Incident
from api.v1.alerts.enums import AlertSeverityEnum, AlertStatusEnum, AlertTLPEnum, AlertPAPEnum
from api.v1.auth.enums import UserRoleEnum
import uuid


class AlertEscalationTests(TestCase):
    """
    Tests for alert escalation to incidents
    """
    def setUp(self):
        self.client = APIClient()
        
        # Create company for testing
        self.company = Company.objects.create(name='Test Company')
        
        # Create a superuser for testing
        self.superuser = User.objects.create_superuser(
            username='admin_test',
            email='admin@example.com',
            password='securepass123'
        )
        
        # Create a company admin user
        self.admin_user = User.objects.create_user(
            username='company_admin',
            email='admin@company.com',
            password='securepass123',
            role=UserRoleEnum.ADMIN_COMPANY.value,
            company=self.company
        )
        
        # Create an alert for testing
        self.alert = Alert.objects.create(
            title='Test Alert for Escalation',
            description='This is a test alert that will be escalated',
            severity=AlertSeverityEnum.HIGH.value,
            source='test_system',
            source_ref='ESC-001',
            status=AlertStatusEnum.NEW.value,
            company=self.company,
            created_by=self.admin_user,
            tags=['test', 'escalation'],
            tlp=AlertTLPEnum.AMBER.value,
            pap=AlertPAPEnum.GREEN.value
        )
        
        # URL for escalation
        self.escalate_url = f'/api/v1/alerts/{self.alert.id}/escalate/'
    
    def test_escalate_alert_as_admin(self):
        """
        Verify that a company admin can escalate an alert to an incident
        """
        # Login as company admin
        self.client.force_authenticate(user=self.admin_user)
        
        # Make the request
        response = self.client.post(self.escalate_url, format='json')
        
        # Verify that the alert was escalated
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify that an incident was created
        self.assertEqual(Incident.objects.count(), 1)
        
        # Verify that the alert was updated
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, AlertStatusEnum.ESCALATED.value)
        
        # Verify the created incident
        incident = Incident.objects.first()
        self.assertEqual(incident.severity, self.alert.severity)
        self.assertEqual(incident.company, self.company)
        self.assertEqual(incident.related_alerts.count(), 1)
        self.assertEqual(incident.related_alerts.first(), self.alert)
        
        # Verify default classification fields
        self.assertEqual(incident.tags, self.alert.tags)
        self.assertEqual(incident.tlp, self.alert.tlp)
        self.assertEqual(incident.pap, self.alert.pap)
    
    def test_escalate_already_escalated_alert(self):
        """
        Verify that it's not possible to escalate an alert that has already been escalated
        """
        # Set the alert as already escalated
        self.alert.status = AlertStatusEnum.ESCALATED.value
        self.alert.save()
        
        # Login as company admin
        self.client.force_authenticate(user=self.admin_user)
        
        # Make the request
        response = self.client.post(self.escalate_url, format='json')
        
        # Verify that the escalation was rejected
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify that no incident was created
        self.assertEqual(Incident.objects.count(), 0)
    
    def test_escalate_nonexistent_alert(self):
        """
        Verify that it's not possible to escalate an alert that doesn't exist
        """
        # Login as company admin
        self.client.force_authenticate(user=self.admin_user)
        
        # URL for nonexistent alert
        nonexistent_url = f'/api/v1/alerts/{uuid.uuid4()}/escalate/'
        
        # Make the request
        response = self.client.post(nonexistent_url, format='json')
        
        # Verify that the escalation was rejected
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify that no incident was created
        self.assertEqual(Incident.objects.count(), 0) 