import uuid
from django.db import models
from django.contrib.auth import get_user_model
from observables.models import Observable
from companies.models import Company
from incidents.models import Incident
from alerts.models import Alert
from django.utils import timezone
from sentinelvision.logging import get_structured_logger
from api.v1.sentinelvision.enums import ExecutionStatusEnum
from api.core.utils.enum_utils import enum_to_choices
from api.core.models import CoreModel

User = get_user_model()
logger = get_structured_logger('sentinelvision.execution')


class ExecutionRecord(CoreModel):
    """
    Record of module executions for auditing and debugging.
    """
    # Execution Identification
    module_name = models.CharField('Module Name', max_length=100)
    module_type = models.CharField('Module Type', max_length=50, default='generic')
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='execution_records'
    )
    
    # Execution Details
    status = models.CharField(
        'Status',
        max_length=20,
        choices=enum_to_choices(ExecutionStatusEnum),
        default=ExecutionStatusEnum.PENDING.value
    )
    started_at = models.DateTimeField('Started At', null=True, blank=True)
    completed_at = models.DateTimeField('Completed At', null=True, blank=True)
    duration_seconds = models.FloatField('Duration (seconds)', null=True, blank=True)
    
    # Execution Results
    result_count = models.PositiveIntegerField('Result Count', default=0)
    error_message = models.TextField('Error Message', blank=True)
    execution_log = models.TextField('Execution Log', blank=True)
    
    # Context
    input_data = models.JSONField('Input Data', default=dict, blank=True)
    output_data = models.JSONField('Output Data', default=dict, blank=True)
    
    # Execution context
    execution_arguments = models.JSONField(
        'Execution Arguments',
        default=dict,
        blank=True
    )
    
    # Relationships
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='execution_records',
        verbose_name='Related Incident',
        null=True,
        blank=True
    )
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='execution_records',
        verbose_name='Related Alert',
        null=True,
        blank=True
    )
    executed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='executed_modules',
        verbose_name='Executed by'
    )
    
    class Meta:
        verbose_name = 'Execution Record'
        verbose_name_plural = 'Execution Records'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['company', 'module_type']),
            models.Index(fields=['status']),
            models.Index(fields=['started_at']),
        ]
    
    def __str__(self):
        return f"{self.module_name} ({self.status})"
    
    def start_execution(self, input_data=None):
        """Start execution record."""
        self.status = ExecutionStatusEnum.RUNNING.value
        self.started_at = timezone.now()
        self.input_data = input_data or {}
        self.save(update_fields=['status', 'started_at', 'input_data'])
        
        logger.info(
            f"Started execution of {self.module_name}",
            extra={
                'module_name': self.module_name,
                'module_type': self.module_type,
                'company_id': str(self.company.id)
            }
        )
    
    def complete_execution(self, status, output_data=None, error_message=None):
        """Complete execution record."""
        self.status = status
        self.completed_at = timezone.now()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.output_data = output_data or {}
        self.error_message = error_message or ''
        
        if status == ExecutionStatusEnum.SUCCESS.value:
            self.result_count = len(output_data.get('results', []))
        
        self.save(update_fields=[
            'status', 'completed_at', 'duration_seconds',
            'output_data', 'error_message', 'result_count'
        ])
        
        log_level = 'info' if status == ExecutionStatusEnum.SUCCESS.value else 'error'
        getattr(logger, log_level)(
            f"Completed execution of {self.module_name}: {status}",
            extra={
                'module_name': self.module_name,
                'module_type': self.module_type,
                'company_id': str(self.company.id),
                'status': status,
                'duration_seconds': self.duration_seconds,
                'result_count': self.result_count
            }
        )
    
    def add_log(self, message):
        """Add log message to execution record."""
        if not self.execution_log:
            self.execution_log = message
        else:
            self.execution_log += f"\n{message}"
        self.save(update_fields=['execution_log'])
    
    def get_metrics(self):
        """
        Get execution metrics.
        
        Returns:
            dict: Execution metrics
        """
        return {
            'status': self.status,
            'duration_seconds': self.duration_seconds,
            'result_count': self.result_count,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }

    def save(self, *args, **kwargs):
        """
        Override save method to ensure data validity.
        """
        # Run validation
        self.full_clean()
        
        super().save(*args, **kwargs) 