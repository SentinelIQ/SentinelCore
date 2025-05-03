import os
import json
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from mitre.models import MitreTactic, MitreTechnique, MitreMitigation, MitreRelationship
from mitre.services import MitreImporter


class MockResponse:
    """Mock HTTP response for testing"""
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        
    def json(self):
        return self.json_data
        
    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception(f"HTTP Error: {self.status_code}")


class TestMitreImport(TestCase):
    """Tests for MITRE ATT&CK data import functionality"""
    
    fixtures = ['auth_app/fixtures/users.json', 'companies/fixtures/companies.json']
    
    def setUp(self):
        """Set up test environment"""
        # Create test STIX data
        self.stix_data = {
            "objects": [
                # Tactic
                {
                    "type": "x-mitre-tactic",
                    "id": "x-mitre-tactic--2558fd61-8c75-4730-94c4-11926db2a263",
                    "created": "2020-10-02T16:30:56.845Z",
                    "modified": "2022-04-28T15:16:12.813Z",
                    "name": "Initial Access",
                    "description": "The adversary is trying to get into your network.",
                    "external_references": [
                        {
                            "source_name": "mitre-attack",
                            "external_id": "TA0001",
                            "url": "https://attack.mitre.org/tactics/TA0001"
                        }
                    ]
                },
                # Technique
                {
                    "type": "attack-pattern",
                    "id": "attack-pattern--970a3432-3237-47ad-bcca-7d8cbb217736",
                    "created": "2020-10-02T16:30:56.845Z",
                    "modified": "2023-04-12T00:40:49.102Z",
                    "name": "Spearphishing Attachment",
                    "description": "Adversaries may send spearphishing emails with a malicious attachment.",
                    "kill_chain_phases": [
                        {
                            "kill_chain_name": "mitre-attack",
                            "phase_name": "Initial Access"
                        }
                    ],
                    "external_references": [
                        {
                            "source_name": "mitre-attack",
                            "external_id": "T1566.001",
                            "url": "https://attack.mitre.org/techniques/T1566/001"
                        }
                    ],
                    "x_mitre_platforms": [
                        "Windows", 
                        "macOS", 
                        "Linux"
                    ],
                    "x_mitre_detection": "Network intrusion detection systems and email gateways can be used to detect spearphishing."
                },
                # Mitigation
                {
                    "type": "course-of-action",
                    "id": "course-of-action--5d156fd9-cbce-4e36-a011-76a11117c45b",
                    "created": "2020-10-02T16:30:56.845Z",
                    "modified": "2022-04-28T15:16:12.813Z",
                    "name": "User Training",
                    "description": "Train users to be suspicious of unexpected emails.",
                    "external_references": [
                        {
                            "source_name": "mitre-attack",
                            "external_id": "M1017",
                            "url": "https://attack.mitre.org/mitigations/M1017"
                        }
                    ]
                },
                # Relationship
                {
                    "type": "relationship",
                    "id": "relationship--9a777ca7-6116-401d-b578-d3cb45f4fa22",
                    "created": "2020-10-02T16:30:56.845Z",
                    "modified": "2022-04-28T15:16:12.813Z",
                    "relationship_type": "mitigates",
                    "source_ref": "course-of-action--5d156fd9-cbce-4e36-a011-76a11117c45b",
                    "target_ref": "attack-pattern--970a3432-3237-47ad-bcca-7d8cbb217736",
                    "description": "User training can help mitigate spearphishing."
                }
            ]
        }

    @patch('requests.get')
    def test_mitre_importer(self, mock_get):
        """Test that MitreImporter correctly imports data"""
        # Mock the HTTP response
        mock_get.return_value = MockResponse(self.stix_data)
        
        # Create the importer and run the import
        importer = MitreImporter()
        stats = importer.run_full_sync(force=True)
        
        # Check that the expected objects were created
        self.assertEqual(MitreTactic.objects.count(), 1)
        self.assertEqual(MitreTechnique.objects.count(), 1)
        self.assertEqual(MitreMitigation.objects.count(), 1)
        self.assertEqual(MitreRelationship.objects.count(), 1)
        
        # Check specific objects
        tactic = MitreTactic.objects.get(external_id="TA0001")
        self.assertEqual(tactic.name, "Initial Access")
        
        technique = MitreTechnique.objects.get(external_id="T1566.001")
        self.assertEqual(technique.name, "Spearphishing Attachment")
        self.assertEqual(technique.platforms, ["Windows", "macOS", "Linux"])
        self.assertTrue("Network intrusion detection systems" in technique.detection)
        
        # Check that the technique is linked to the tactic
        self.assertEqual(technique.tactics.count(), 1)
        self.assertEqual(technique.tactics.first().external_id, "TA0001")

    @patch('mitre.services.MitreImporter.run_full_sync')
    def test_import_mitre_command(self, mock_run_full_sync):
        """Test that the management command works correctly"""
        # Set up mock return value
        mock_run_full_sync.return_value = {
            "tactics": 1,
            "techniques": 1,
            "subtechniques": 0,
            "mitigations": 1,
            "relationships": 1
        }
        
        # Call the command
        out = StringIO()
        call_command('import_mitre', source='json', stdout=out)
        
        # Check the output
        output = out.getvalue()
        self.assertIn("Successfully imported MITRE ATT&CK data", output)
        self.assertIn("Tactics: 1", output)
        
        # Verify the mock was called with expected parameters
        mock_run_full_sync.assert_called_once()
        args, kwargs = mock_run_full_sync.call_args
        self.assertEqual(kwargs['source_type'], 'json')
        self.assertFalse(kwargs['force'])

    @patch('mitre.services.MitreImporter.run_full_sync')
    def test_mitre_sync_task(self, mock_run_full_sync):
        """Test that the Celery task works correctly"""
        from mitre.tasks import sync_mitre_data
        
        # Set up mock return value
        mock_run_full_sync.return_value = {
            "tactics": 1,
            "techniques": 1,
            "subtechniques": 0,
            "mitigations": 1,
            "relationships": 1
        }
        
        # Run the task
        result = sync_mitre_data()
        
        # Verify the mock was called with expected parameters
        mock_run_full_sync.assert_called_once()
        args, kwargs = mock_run_full_sync.call_args
        self.assertEqual(kwargs['source_type'], 'json')
        self.assertFalse(kwargs['force'])
        
        # Check the result
        self.assertEqual(result['tactics'], 1)
        self.assertEqual(result['techniques'], 1) 