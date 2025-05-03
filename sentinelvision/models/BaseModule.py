from django.db import models
from django.utils import timezone
from sentinelvision.logging import get_structured_logger
from api.core.models import CoreModel

logger = get_structured_logger('sentinelvision.modules')

class BaseModule(CoreModel):
    """
    Base class for all SentinelVision modules.
    Provides common fields and behaviors for all module types.
    """
    # Module Identification
    name = models.CharField('Module Name', max_length=100)
    module_type = models.CharField('Module Type', max_length=50, choices=[
        ('feed', 'Feed Module'),
        ('analyzer', 'Analyzer Module'),
        ('responder', 'Responder Module')
    ])
    description = models.TextField('Description', blank=True)
    
    # Module Configuration
    is_active = models.BooleanField('Active', default=True)
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='%(class)s_modules',
        null=True,
        blank=True,
        help_text='Leave empty for global modules accessible only to superadmins'
    )
    cron_schedule = models.CharField(
        'Cron Schedule',
        max_length=100,
        blank=True,
        help_text='Cron expression for scheduled execution (e.g., "0 */12 * * *" for every 12 hours)'
    )
    
    # Module Status
    last_run = models.DateTimeField('Last Run', null=True, blank=True)
    last_error = models.TextField('Last Error', blank=True)
    error_count = models.PositiveIntegerField('Error Count', default=0)
    
    # Module Metrics
    total_processed = models.PositiveIntegerField('Total Processed', default=0)
    success_rate = models.FloatField('Success Rate', default=0.0)
    
    class Meta:
        abstract = True
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'module_type']),
            models.Index(fields=['last_run']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.module_type})"
    
    def activate(self):
        """Activate the module."""
        self.is_active = True
        self.save(update_fields=['is_active'])
        logger.info(
            f"Module {self.name} activated",
            extra={'module_name': self.name, 'module_type': self.module_type}
        )
    
    def deactivate(self):
        """Deactivate the module."""
        self.is_active = False
        self.save(update_fields=['is_active'])
        logger.info(
            f"Module {self.name} deactivated",
            extra={'module_name': self.name, 'module_type': self.module_type}
        )
    
    def update_status(self, success=True, error=None):
        """
        Update module status after execution.
        
        Args:
            success (bool): Whether the execution was successful
            error (str): Error message if execution failed
        """
        self.last_run = timezone.now()
        
        if success:
            self.error_count = 0
            self.last_error = ''
            self.success_rate = ((self.success_rate * self.total_processed) + 1) / (self.total_processed + 1)
        else:
            self.error_count += 1
            self.last_error = error or 'Unknown error'
            self.success_rate = (self.success_rate * self.total_processed) / (self.total_processed + 1)
        
        self.total_processed += 1
        self.save(update_fields=[
            'last_run', 'error_count', 'last_error',
            'total_processed', 'success_rate'
        ])
    
    def execute(self, *args, **kwargs):
        """
        Execute the module's main functionality.
        This method should be implemented by subclasses.
        
        Returns:
            dict: Execution results
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def validate_configuration(self):
        """
        Validate module configuration.
        This method can be overridden by subclasses.
        
        Returns:
            bool: True if configuration is valid
        """
        return True
    
    def get_metrics(self):
        """
        Get module metrics.
        
        Returns:
            dict: Module metrics
        """
        return {
            'total_processed': self.total_processed,
            'success_rate': self.success_rate,
            'error_count': self.error_count,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'is_active': self.is_active
        } 