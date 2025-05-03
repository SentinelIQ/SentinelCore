import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from companies.models import Company
from incidents.models import Incident
from model_utils import FieldTracker
from api.v1.tasks.enums import TaskStatusEnum, TaskPriorityEnum
from api.core.utils.enum_utils import enum_to_choices
from api.core.models import CoreModel

User = get_user_model()


class Task(CoreModel):
    """
    Task model for incident investigation workflow in the Sentineliq system.
    Each task belongs to a specific incident and can be assigned to a user.
    """
    title = models.CharField('Title', max_length=200)
    description = models.TextField('Description', blank=True)
    status = models.CharField(
        'Status',
        max_length=20,
        choices=enum_to_choices(TaskStatusEnum),
        default=TaskStatusEnum.OPEN.value
    )
    priority = models.CharField(
        'Priority',
        max_length=20,
        choices=enum_to_choices(TaskPriorityEnum),
        default=TaskPriorityEnum.MEDIUM.value
    )
    
    # Field tracker
    tracker = FieldTracker(fields=['status', 'assigned_to'])
    
    # Dates
    due_date = models.DateTimeField(
        'Due Date',
        null=True,
        blank=True
    )
    completion_date = models.DateTimeField(
        'Completion Date',
        null=True, 
        blank=True
    )
    
    # Relationships
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='standalone_tasks',
        verbose_name='Related Incident'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Company'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_standalone_tasks',
        verbose_name='Created by'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='assigned_standalone_tasks',
        verbose_name='Assigned to',
        null=True,
        blank=True
    )
    
    # Additional fields
    order = models.PositiveIntegerField(
        'Order',
        default=0,
        help_text='Display order in the task list'
    )
    notes = models.TextField(
        'Notes',
        blank=True,
        help_text='Additional notes or progress updates'
    )
    
    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['order', 'due_date', '-priority']
        indexes = [
            models.Index(fields=['incident']),
            models.Index(fields=['company']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['due_date']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def clean(self):
        """
        Validate model constraints that involve multiple fields.
        """
        super().clean()
        
        # Validate that assigned_to belongs to the same company
        if self.assigned_to and self.company and hasattr(self.assigned_to, 'company'):
            if self.assigned_to.company != self.company and not self.assigned_to.is_superuser:
                raise ValidationError({
                    'assigned_to': 'The assigned user must belong to the same company as the task.'
                })
    
    def mark_completed(self, user=None):
        """
        Marks the task as completed and adds a timeline entry to the parent incident.
        
        Args:
            user (User, optional): User who completed the task
        """
        self.status = TaskStatusEnum.COMPLETED.value
        self.completion_date = timezone.now()
        self.save(update_fields=['status', 'completion_date'])
        
        # Add entry to incident timeline
        if self.incident:
            self.incident.add_timeline_entry(
                title=f"Task completed: {self.title}",
                content=f"Task marked as completed by {user.username if user else 'system'}",
                event_type='task_update',
                created_by=user
            )
    
    def save(self, *args, **kwargs):
        """
        Override save method to ensure the company field matches the incident's company.
        Also validates the assigned_to user.
        """
        # Ensure company matches incident's company
        if self.incident and not self.company_id:
            self.company = self.incident.company
        
        # Validate assigned_to user belongs to the same company
        if self.assigned_to and hasattr(self.assigned_to, 'company') and self.company and not self.assigned_to.is_superuser:
            if self.assigned_to.company != self.company:
                raise ValidationError("The assigned user must belong to the same company as the task.")
            
        # Set default order if none provided
        if self.order == 0:
            max_order = Task.objects.filter(incident=self.incident).aggregate(
                models.Max('order')
            )['order__max'] or 0
            self.order = max_order + 1
            
        super().save(*args, **kwargs) 