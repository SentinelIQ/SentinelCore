from django.test import TestCase
from companies.models import Company
from django.utils import timezone
from datetime import timedelta


class CompanyModelTestCase(TestCase):
    """
    Test case for the Company model.
    """
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
    
    def test_company_creation(self):
        """Test that a company is created with the correct name."""
        self.assertEqual(self.company.name, "Test Company")
        self.assertIsNotNone(self.company.created_at)
        self.assertIsNotNone(self.company.updated_at)
    
    def test_company_str_method(self):
        """Test the string representation of a company."""
        self.assertEqual(str(self.company), "Test Company")
    
    def test_company_ordering(self):
        """Test that companies are ordered by name."""
        # Create more companies
        Company.objects.create(name="Acme Inc")
        Company.objects.create(name="Zenith Corp")
        
        # Get all companies ordered by name
        companies = Company.objects.all()
        
        # Check that they are ordered by name
        self.assertEqual(companies[0].name, "Acme Inc")
        self.assertEqual(companies[1].name, "Test Company")
        self.assertEqual(companies[2].name, "Zenith Corp")
    
    def test_company_update(self):
        """Test that updating a company updates the updated_at field."""
        # Get the initial updated_at time
        initial_updated_at = self.company.updated_at
        
        # Wait a moment to ensure the timestamp changes
        timezone.now()
        
        # Update the company
        self.company.name = "Updated Company"
        self.company.save()
        
        # Check that the updated_at time has changed
        self.assertGreater(self.company.updated_at, initial_updated_at) 