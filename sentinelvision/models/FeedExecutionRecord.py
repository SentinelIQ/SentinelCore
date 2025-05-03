from django.db import models
from django.utils import timezone
from api.core.models import CoreModel
from sentinelvision.models import FeedModule
from django.contrib.auth import get_user_model

User = get_user_model()

class ExecutionSourceEnum(models.TextChoices):
    MANUAL = 'manual', 'Manual Execution'
    SCHEDULED = 'scheduled', 'Scheduled Execution'

class ExecutionStatusEnum(models.TextChoices):
    PENDING = 'pending', 'Pending'
    RUNNING = 'running', 'Running'
    SUCCESS = 'success', 'Success'
    FAILED = 'failed', 'Failed'

class FeedExecutionRecord(CoreModel):
    """
    Record of feed module execution.
    Tracks executions, status, and metrics for Feed modules.
    """
    # Relationships
    feed = models.ForeignKey(
        FeedModule,
        on_delete=models.CASCADE,
        related_name='execution_records',
        verbose_name='Feed Module'
    )
    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feed_executions',
        verbose_name='Executed By',
        help_text='User who triggered the execution (null if automated)'
    )
    
    # Execution Metadata
    source = models.CharField(
        'Execution Source',
        max_length=20,
        choices=ExecutionSourceEnum.choices,
        default=ExecutionSourceEnum.MANUAL
    )
    status = models.CharField(
        'Execution Status',
        max_length=20,
        choices=ExecutionStatusEnum.choices,
        default=ExecutionStatusEnum.PENDING
    )
    started_at = models.DateTimeField(
        'Started At',
        default=timezone.now
    )
    ended_at = models.DateTimeField(
        'Ended At',
        null=True,
        blank=True
    )
    
    # Execution Details
    log = models.TextField(
        'Execution Log',
        blank=True,
        help_text='Detailed log of the execution process'
    )
    iocs_processed = models.PositiveIntegerField(
        'IOCs Processed',
        default=0,
        help_text='Number of IOCs processed during execution'
    )
    error_message = models.TextField(
        'Error Message',
        blank=True,
        help_text='Error message if execution failed'
    )
    
    class Meta:
        verbose_name = 'Feed Execution Record'
        verbose_name_plural = 'Feed Execution Records'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['feed', '-started_at']),
            models.Index(fields=['status']),
            models.Index(fields=['source']),
        ]
    
    def __str__(self):
        return f"{self.feed.name} - {self.get_status_display()} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"
    
    def mark_running(self):
        """Mark the execution as running."""
        self.status = ExecutionStatusEnum.RUNNING
        self.save(update_fields=['status'])
    
    def mark_success(self, iocs_processed=0, log=''):
        """
        Mark the execution as successful.
        
        Args:
            iocs_processed (int): Number of IOCs processed
            log (str): Execution log
        """
        self.status = ExecutionStatusEnum.SUCCESS
        self.ended_at = timezone.now()
        self.iocs_processed = iocs_processed
        self.log = log
        self.save(update_fields=['status', 'ended_at', 'iocs_processed', 'log'])
    
    def mark_failed(self, error_message='', log=''):
        """
        Mark the execution as failed.
        
        Args:
            error_message (str): Error message
            log (str): Execution log
        """
        self.status = ExecutionStatusEnum.FAILED
        self.ended_at = timezone.now()
        self.error_message = error_message
        self.log = log
        self.save(update_fields=['status', 'ended_at', 'error_message', 'log'])
    
    @property
    def duration_seconds(self):
        """Get execution duration in seconds."""
        if not self.ended_at:
            return None
        return (self.ended_at - self.started_at).total_seconds()
    
    @property
    def is_complete(self):
        """Check if execution is complete (success or failed)."""
        return self.status in [ExecutionStatusEnum.SUCCESS, ExecutionStatusEnum.FAILED] 