import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from tasks.models import Task
from incidents.models import Incident
from companies.models import Company
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime

User = get_user_model()


class TaskAPITestCase(APITestCase):
    """Test case for Task API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create a company
        self.company = Company.objects.create(
            name="Test Company",
        )
        
        # Create superuser (adminsentinel)
        self.admin = User.objects.create_superuser(
            username="admin_task",
            email="admin_task@sentineliq.com",
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
            severity=Incident.Severity.MEDIUM,
            status=Incident.Status.OPEN,
            company=self.company,
            created_by=self.company_admin
        )
        
        # Create test task
        self.task = Task.objects.create(
            title="Test Task",
            description="Test task description",
            status=Task.Status.OPEN,
            priority=Task.Priority.MEDIUM,
            incident=self.incident,
            company=self.company,
            created_by=self.company_admin,
            assigned_to=self.company_analyst,
            due_date=timezone.now() + datetime.timedelta(days=1)
        )
        
        # URLs - using direct paths instead of reverse lookup
        self.task_list_url = '/api/v1/tasks/'
        self.task_detail_url = f'/api/v1/tasks/{self.task.id}/'
        self.task_complete_url = f'/api/v1/tasks/{self.task.id}/complete/'
    
    def test_list_tasks(self):
        """Test that users can list tasks based on their permissions."""
        # Test company admin can list tasks
        self.client.force_authenticate(user=self.company_admin)
        response = self.client.get(self.task_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        
        # Test company analyst can list tasks
        self.client.force_authenticate(user=self.company_analyst)
        response = self.client.get(self.task_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        
        # Test superuser can list all tasks
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.task_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
    
    def test_create_task(self):
        """Test that only authorized users can create tasks."""
        self.client.force_authenticate(user=self.company_admin)
        data = {
            'title': 'New Task',
            'description': 'New task description',
            'status': Task.Status.OPEN,
            'priority': Task.Priority.HIGH,
            'incident': str(self.incident.id),
            'assigned_to': str(self.company_analyst.id),
            'due_date': (timezone.now() + datetime.timedelta(days=2)).isoformat()
        }
        response = self.client.post(self.task_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)
        
        # Create a read-only user to test permission restrictions
        read_only_user = User.objects.create_user(
            username="readonly_task",
            email="readonly_task@testcompany.com",
            password="password123",
            role="read_only",
            company=self.company,
        )
        
        # Test read-only user cannot create tasks
        self.client.force_authenticate(user=read_only_user)
        data['title'] = 'Another Task'
        response = self.client.post(self.task_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_task_status(self):
        """Test updating task status."""
        self.client.force_authenticate(user=self.company_admin)
        
        data = {
            'status': Task.Status.IN_PROGRESS
        }
        
        response = self.client.patch(self.task_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify status was updated
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.IN_PROGRESS)
    
    def test_complete_task(self):
        """Test marking a task as completed."""
        self.client.force_authenticate(user=self.company_analyst)
        
        response = self.client.post(self.task_complete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify task was marked as completed
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.COMPLETED)
        self.assertIsNotNone(self.task.completion_date)
        
        # Verify incident timeline was updated
        self.incident.refresh_from_db()
        self.assertTrue(any(
            entry['title'].startswith('Task completed') 
            for entry in self.incident.timeline
        ))
    
    def test_filter_tasks(self):
        """Test filtering tasks by various criteria."""
        # Create another task with different status and assignee
        Task.objects.create(
            title="Another Task",
            description="Description of another task",
            status=Task.Status.IN_PROGRESS,
            priority=Task.Priority.LOW,
            incident=self.incident,
            company=self.company,
            created_by=self.company_admin,
            assigned_to=self.company_admin
        )
        
        self.client.force_authenticate(user=self.company_admin)
        
        # Test filtering by status
        response = self.client.get(f"{self.task_list_url}?status=open")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['status'], 'open')
        
        # Test filtering by assignee
        response = self.client.get(f"{self.task_list_url}?assigned_to={self.company_analyst.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        
        # Get the assigned_to value and convert to string if needed
        assigned_to = response.data['data']['results'][0]['assigned_to']
        if isinstance(assigned_to, int):
            assigned_to = str(assigned_to)
        elif isinstance(assigned_to, str) and assigned_to.isdigit():
            # It's already a string, no conversion needed
            pass
        
        # Compare with the analyst's ID as a string
        self.assertEqual(assigned_to, str(self.company_analyst.id)) 