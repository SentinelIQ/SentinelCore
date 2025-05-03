from django.db import models
from sentinelvision.models import BaseModule
from sentinelvision.logging import get_structured_logger

logger = get_structured_logger('sentinelvision.feeds')

class FeedModule(BaseModule):
    """
    Feed Module for collecting and processing threat intelligence feeds.
    """
    # Feed Configuration
    feed_url = models.URLField('Feed URL', max_length=500)
    interval_hours = models.PositiveIntegerField('Update Interval (hours)', default=24)
    auto_mark_as_ioc = models.BooleanField('Auto-mark as IOC', default=True)
    
    # Feed Processing
    last_successful_fetch = models.DateTimeField('Last Successful Fetch', null=True, blank=True)
    total_iocs_imported = models.PositiveIntegerField('Total IOCs Imported', default=0)
    
    class Meta:
        verbose_name = 'Feed Module'
        verbose_name_plural = 'Feed Modules'
        ordering = ['name']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_type = 'feed'
    
    def save(self, *args, **kwargs):
        self.module_type = 'feed'
        super().save(*args, **kwargs)
    
    def execute(self, *args, **kwargs):
        """
        Execute feed update process.
        
        Returns:
            dict: Update results
        """
        try:
            if not self.is_active:
                return {
                    'status': 'skipped',
                    'message': 'Module is not active'
                }
            
            # Validate configuration
            if not self.validate_configuration():
                return {
                    'status': 'error',
                    'error': 'Invalid configuration'
                }
            
            # Update feed
            result = self.update_feed()
            
            # Update status
            self.update_status(
                success=result.get('status') == 'success',
                error=result.get('error')
            )
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Error executing feed module {self.name}: {error_msg}",
                extra={
                    'module_name': self.name,
                    'module_type': self.module_type,
                    'error': error_msg
                },
                exc_info=True
            )
            
            self.update_status(success=False, error=error_msg)
            return {
                'status': 'error',
                'error': error_msg
            }
    
    def update_feed(self):
        """
        Update the feed by fetching and processing new data.
        This method should be implemented by specific feed types.
        
        Returns:
            dict: Result of the update operation
        """
        raise NotImplementedError("Feed types must implement update_feed()")
    
    def validate_configuration(self):
        """
        Validate feed configuration.
        
        Returns:
            bool: True if configuration is valid
        """
        return bool(self.feed_url and self.interval_hours > 0)
    
    def get_metrics(self):
        """
        Get feed-specific metrics.
        
        Returns:
            dict: Feed metrics
        """
        base_metrics = super().get_metrics()
        feed_metrics = {
            'total_iocs_imported': self.total_iocs_imported,
            'last_successful_fetch': self.last_successful_fetch.isoformat() if self.last_successful_fetch else None,
            'interval_hours': self.interval_hours
        }
        return {**base_metrics, **feed_metrics} 