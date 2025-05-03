import json
import uuid
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from auth_app.models import User
from mitre.models import (
    MitreTactic,
    MitreTechnique,
    MitreMitigation,
    AlertMitreMapping,
)
from alerts.models import Alert


class MitreAPITest(APITestCase):
    """Tests for MITRE ATT&CK API endpoints"""
    
    fixtures = ['auth_app/fixtures/users.json', 'companies/fixtures/companies.json']
    
    def setUp(self):
        """Set up test environment"""
        # Get admin user
        self.admin_user = User.objects.get(username='adminsentinel')
        self.client.force_authenticate(user=self.admin_user)
        
        # Create test data
        self.tactic = MitreTactic.objects.create(
            external_id='TA0001',
            name='Initial Access',
            description='The adversary is trying to get into your network.'
        )
        
        self.technique = MitreTechnique.objects.create(
            external_id='T1566.001',
            name='Spearphishing Attachment',
            description='Adversaries may send spearphishing emails with a malicious attachment.',
            platforms=['Windows', 'macOS', 'Linux'],
            detection='Network intrusion detection systems can be used to detect spearphishing.',
            is_subtechnique=True
        )
        self.technique.tactics.add(self.tactic)
        
        self.mitigation = MitreMitigation.objects.create(
            external_id='M1017',
            name='User Training',
            description='Train users to be suspicious of unexpected emails.'
        )
        self.mitigation.techniques.add(self.technique)
        
        # Create an alert
        self.alert = Alert.objects.create(
            title='Test Phishing Alert',
            description='Test alert for phishing attack',
            source='Test Source',
            severity='high',
            status='new',
            company_id=1,  # Use hardcoded company ID instead of adminuser.company
            created_by=self.admin_user  # Add the created_by field
        )
        
        # Create alert-technique mapping
        self.alert_mapping = AlertMitreMapping.objects.create(
            alert=self.alert,
            technique=self.technique,
            confidence=75,
            auto_detected=True
        )
    
    def test_list_tactics(self):
        """Test listing tactics"""
        url = reverse('mitre-tactics-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['external_id'], 'TA0001')
    
    def test_retrieve_tactic(self):
        """Test retrieving a specific tactic"""
        url = reverse('mitre-tactics-detail', args=[self.tactic.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['external_id'], 'TA0001')
        self.assertEqual(response.data['data']['name'], 'Initial Access')
        self.assertEqual(response.data['data']['technique_count'], 1)
    
    def test_list_techniques(self):
        """Test listing techniques"""
        url = reverse('mitre-techniques-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['external_id'], 'T1566.001')
    
    def test_filter_techniques_by_tactic(self):
        """Test filtering techniques by tactic"""
        url = reverse('mitre-techniques-list')
        response = self.client.get(url, {'tactics': self.tactic.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['external_id'], 'T1566.001')
    
    def test_retrieve_technique(self):
        """Test retrieving a specific technique"""
        url = reverse('mitre-techniques-detail', args=[self.technique.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['external_id'], 'T1566.001')
        self.assertEqual(response.data['data']['name'], 'Spearphishing Attachment')
        self.assertEqual(len(response.data['data']['tactics']), 1)
        self.assertEqual(response.data['data']['tactics'][0]['external_id'], 'TA0001')
    
    def test_list_mitigations(self):
        """Test listing mitigations"""
        url = reverse('mitre-mitigations-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['external_id'], 'M1017')
    
    def test_alert_mitre_mappings(self):
        """Test alert-MITRE mappings"""
        url = reverse('mitre-alert-mappings-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['technique_detail']['external_id'], 'T1566.001')
        self.assertEqual(response.data['data']['results'][0]['confidence'], 75)
    
    def test_create_alert_mitre_mapping(self):
        """Test creating a new alert-MITRE mapping"""
        url = reverse('mitre-alert-mappings-list')
        data = {
            'alert': str(self.alert.id),
            'technique': str(self.technique.id),
            'confidence': 90,
            'auto_detected': False
        }
        
        # First delete the existing mapping to avoid conflict
        self.alert_mapping.delete()
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['confidence'], 90)
        self.assertEqual(response.data['data']['auto_detected'], False)
    
    def test_bulk_delete_alert_mappings(self):
        """Test bulk deleting alert-MITRE mappings"""
        url = reverse('mitre-alert-mappings-bulk-delete')
        # Send the alert_id as a query parameter
        url = f"{url}?alert_id={str(self.alert.id)}"
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['deleted_count'], 1)
        
        # Verify the mapping was deleted
        self.assertEqual(AlertMitreMapping.objects.count(), 0) 