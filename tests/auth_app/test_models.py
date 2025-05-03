from django.test import TestCase
from django.contrib.auth import get_user_model
from companies.models import Company

User = get_user_model()


class UserModelTestCase(TestCase):
    """
    Test case for the User model.
    """
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        
        # Create a superuser
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="password123"
        )
        
        # Create a company admin
        self.admin_company = User.objects.create_user(
            username="company_admin",
            email="admin@company.com",
            password="password123",
            role=User.Role.ADMIN_COMPANY,
            company=self.company
        )
        
        # Create a company analyst
        self.analyst_company = User.objects.create_user(
            username="company_analyst",
            email="analyst@company.com",
            password="password123",
            role=User.Role.ANALYST_COMPANY,
            company=self.company
        )
    
    def test_user_roles(self):
        """Test that user roles are set correctly."""
        self.assertEqual(self.superuser.role, User.Role.SUPERUSER)
        self.assertEqual(self.admin_company.role, User.Role.ADMIN_COMPANY)
        self.assertEqual(self.analyst_company.role, User.Role.ANALYST_COMPANY)
    
    def test_user_company_relationships(self):
        """Test that user-company relationships are correct."""
        self.assertIsNone(self.superuser.company)
        self.assertEqual(self.admin_company.company, self.company)
        self.assertEqual(self.analyst_company.company, self.company)
    
    def test_role_properties(self):
        """Test that role properties work correctly."""
        self.assertFalse(self.superuser.is_admin_company)
        self.assertFalse(self.superuser.is_analyst_company)
        
        self.assertTrue(self.admin_company.is_admin_company)
        self.assertFalse(self.admin_company.is_analyst_company)
        
        self.assertFalse(self.analyst_company.is_admin_company)
        self.assertTrue(self.analyst_company.is_analyst_company)
    
    def test_superuser_save_method(self):
        """Test that superuser save method sets role to SUPERUSER and company to None."""
        # Create a regular user
        user = User.objects.create_user(
            username="regular_user",
            email="user@test.com",
            password="password123",
            role=User.Role.ANALYST_COMPANY,
            company=self.company
        )
        
        # Make the user a superuser
        user.is_superuser = True
        user.save()
        
        # Refresh from the database
        user.refresh_from_db()
        
        # Check that the role is SUPERUSER and company is None
        self.assertEqual(user.role, User.Role.SUPERUSER)
        self.assertIsNone(user.company) 