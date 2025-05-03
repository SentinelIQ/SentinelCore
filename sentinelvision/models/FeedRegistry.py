import uuid
from django.db import models
from django.utils import timezone
from companies.models import Company
from sentinelvision.logging import get_structured_logger
from api.v1.sentinelvision.enums import SyncStatusEnum
from api.core.utils.enum_utils import enum_to_choices
from api.core.models import CoreModel

logger = get_structured_logger('sentinelvision.feeds')

class FeedRegistry(CoreModel):
    """
    Registry for tracking feed modules and their status.
    """
    # Feed Identification
    name = models.CharField('Feed Name', max_length=100)
    feed_type = models.CharField('Feed Type', max_length=50)
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='feed_registries'
    )
    
    # Add SyncStatus class for backwards compatibility with code using FeedRegistry.SyncStatus
    class SyncStatus:
        """Legacy compatibility with SyncStatusEnum values"""
        PENDING = SyncStatusEnum.PENDING.value
        SYNCING = SyncStatusEnum.SYNCING.value
        SUCCESS = SyncStatusEnum.SUCCESS.value
        FAILURE = SyncStatusEnum.FAILURE.value
        DISABLED = SyncStatusEnum.PENDING.value  # DISABLED is not in SyncStatusEnum, use PENDING
    
    # Feed Configuration
    source_url = models.URLField('Source URL', max_length=500)
    description = models.TextField('Description', blank=True)
    sync_interval_hours = models.PositiveIntegerField('Sync Interval (hours)', default=24)
    enabled = models.BooleanField('Enabled', default=True)
    
    # Sync Status
    sync_status = models.CharField(
        'Sync Status',
        max_length=20,
        choices=enum_to_choices(SyncStatusEnum),
        default=SyncStatusEnum.PENDING.value
    )
    last_sync = models.DateTimeField('Last Sync', null=True, blank=True)
    next_sync = models.DateTimeField('Next Sync', null=True, blank=True)
    last_error = models.TextField('Last Error', blank=True)
    
    # Sync Metrics
    total_syncs = models.PositiveIntegerField('Total Syncs', default=0)
    successful_syncs = models.PositiveIntegerField('Successful Syncs', default=0)
    failed_syncs = models.PositiveIntegerField('Failed Syncs', default=0)
    last_sync_count = models.PositiveIntegerField('Last Sync Count', default=0)
    
    # Statistics
    total_iocs = models.PositiveIntegerField('Total IOCs', default=0)
    last_import_count = models.PositiveIntegerField('Last Import Count', default=0)
    total_imports = models.PositiveIntegerField('Total Imports', default=0)
    error_count = models.PositiveIntegerField('Error Count', default=0)
    
    # Configuration
    config = models.JSONField('Configuration', default=dict, blank=True)
    headers = models.JSONField('HTTP Headers', default=dict, blank=True)
    parser_options = models.JSONField('Parser Options', default=dict, blank=True)
    
    # Logging
    last_log = models.TextField('Last Log', blank=True)
    
    class Meta:
        verbose_name = 'Feed Registry'
        verbose_name_plural = 'Feed Registries'
        ordering = ['name']
        unique_together = ['company', 'feed_type']
        indexes = [
            models.Index(fields=['company', 'feed_type']),
            models.Index(fields=['sync_status']),
            models.Index(fields=['next_sync']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.feed_type})"
    
    def mark_sync_started(self):
        """Mark feed as syncing."""
        self.sync_status = SyncStatusEnum.SYNCING.value
        self.last_sync = timezone.now()
        self.save(update_fields=['sync_status', 'last_sync'])
        
        logger.info(
            f"Started syncing feed {self.name}",
            extra={
                'feed_name': self.name,
                'feed_type': self.feed_type,
                'company_id': str(self.company.id)
            }
        )
    
    def mark_sync_success(self, processed_count=0):
        """Mark feed sync as successful."""
        self.sync_status = SyncStatusEnum.SUCCESS.value
        self.last_error = ''
        self.total_syncs += 1
        self.successful_syncs += 1
        self.last_sync_count = processed_count
        self.next_sync = timezone.now() + timezone.timedelta(hours=self.sync_interval_hours)
        self.save(update_fields=[
            'sync_status', 'last_error', 'total_syncs',
            'successful_syncs', 'last_sync_count', 'next_sync'
        ])
        
        logger.info(
            f"Successfully synced feed {self.name}: {processed_count} items processed",
            extra={
                'feed_name': self.name,
                'feed_type': self.feed_type,
                'company_id': str(self.company.id),
                'processed_count': processed_count
            }
        )
    
    def mark_sync_failure(self, error):
        """Mark feed sync as failed."""
        self.sync_status = SyncStatusEnum.FAILURE.value
        self.last_error = error
        self.total_syncs += 1
        self.failed_syncs += 1
        self.next_sync = timezone.now() + timezone.timedelta(hours=1)  # Retry in 1 hour
        self.save(update_fields=[
            'sync_status', 'last_error', 'total_syncs',
            'failed_syncs', 'next_sync'
        ])
        
        logger.error(
            f"Failed to sync feed {self.name}: {error}",
            extra={
                'feed_name': self.name,
                'feed_type': self.feed_type,
                'company_id': str(self.company.id),
                'error': error
            }
        )
    
    def get_metrics(self):
        """
        Get feed registry metrics.
        
        Returns:
            dict: Feed metrics
        """
        return {
            'total_syncs': self.total_syncs,
            'successful_syncs': self.successful_syncs,
            'failed_syncs': self.failed_syncs,
            'success_rate': self.successful_syncs / self.total_syncs if self.total_syncs > 0 else 0,
            'last_sync_count': self.last_sync_count,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'next_sync': self.next_sync.isoformat() if self.next_sync else None,
            'sync_status': self.sync_status,
            'enabled': self.enabled
        }
    
    def is_due_for_sync(self):
        """
        Check if feed is due for sync.
        
        Returns:
            bool: True if feed should be synced
        """
        if not self.enabled:
            return False
        
        if not self.next_sync:
            return True
        
        return timezone.now() >= self.next_sync
    
    def save(self, *args, **kwargs):
        """
        Override save to set next_sync based on interval if not set.
        """
        if self.enabled and not self.next_sync:
            # Calculate next sync time based on interval
            if self.last_sync:
                self.next_sync = self.last_sync + timezone.timedelta(hours=self.sync_interval_hours)
            else:
                self.next_sync = timezone.now() + timezone.timedelta(hours=self.sync_interval_hours)
        
        # If disabled, clear next_sync
        if not self.enabled:
            self.next_sync = None
            self.sync_status = SyncStatusEnum.PENDING.value
            
        super().save(*args, **kwargs)
    
    def log_sync_activity(self, log_message):
        """
        Add a log message about sync activity.
        
        Args:
            log_message: Log message to store
        """
        self.last_log = log_message
        self.save(update_fields=['last_log']) 