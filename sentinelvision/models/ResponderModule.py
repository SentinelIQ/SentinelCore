from django.db import models
from sentinelvision.models import BaseModule
from sentinelvision.logging import get_structured_logger

logger = get_structured_logger('sentinelvision.responders')

class ResponderModule(BaseModule):
    """
    Responder Module for taking automated actions based on analysis results.
    """
    # Response Configuration
    response_type = models.CharField('Response Type', max_length=50)
    severity_threshold = models.CharField(
        'Severity Threshold',
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical')
        ],
        default='medium'
    )
    auto_respond = models.BooleanField('Auto Respond', default=False)
    
    # Response Metrics
    total_responses = models.PositiveIntegerField('Total Responses', default=0)
    total_successful = models.PositiveIntegerField('Total Successful', default=0)
    total_failed = models.PositiveIntegerField('Total Failed', default=0)
    
    class Meta:
        verbose_name = 'Responder Module'
        verbose_name_plural = 'Responder Modules'
        ordering = ['name']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_type = 'responder'
    
    def save(self, *args, **kwargs):
        self.module_type = 'responder'
        super().save(*args, **kwargs)
    
    def execute(self, incident, analysis_results, *args, **kwargs):
        """
        Execute response actions based on incident and analysis results.
        
        Args:
            incident: The incident to respond to
            analysis_results: Analysis results to base response on
            
        Returns:
            dict: Response results
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
            
            # Check if response is needed based on severity
            if not self.should_respond(incident, analysis_results):
                return {
                    'status': 'skipped',
                    'message': 'Severity below threshold'
                }
            
            # Execute response
            result = self.respond(incident, analysis_results, *args, **kwargs)
            
            # Update metrics
            self.total_responses += 1
            if result.get('status') == 'success':
                self.total_successful += 1
            else:
                self.total_failed += 1
            
            # Update status
            self.update_status(
                success=result.get('status') == 'success',
                error=result.get('error')
            )
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Error executing responder module {self.name}: {error_msg}",
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
    
    def should_respond(self, incident, analysis_results):
        """
        Determine if response is needed based on severity.
        
        Args:
            incident: The incident
            analysis_results: Analysis results
            
        Returns:
            bool: True if response is needed
        """
        severity_order = ['low', 'medium', 'high', 'critical']
        incident_severity = incident.severity.lower()
        threshold_index = severity_order.index(self.severity_threshold)
        incident_index = severity_order.index(incident_severity)
        return incident_index >= threshold_index
    
    def respond(self, incident, analysis_results, *args, **kwargs):
        """
        Execute response actions.
        This method should be implemented by specific responder types.
        
        Args:
            incident: The incident to respond to
            analysis_results: Analysis results to base response on
            
        Returns:
            dict: Response results
        """
        raise NotImplementedError("Responder types must implement respond()")
    
    def validate_configuration(self):
        """
        Validate responder configuration.
        
        Returns:
            bool: True if configuration is valid
        """
        return bool(self.response_type)
    
    def get_metrics(self):
        """
        Get responder-specific metrics.
        
        Returns:
            dict: Responder metrics
        """
        base_metrics = super().get_metrics()
        responder_metrics = {
            'total_responses': self.total_responses,
            'total_successful': self.total_successful,
            'total_failed': self.total_failed,
            'success_rate': self.total_successful / self.total_responses if self.total_responses > 0 else 0,
            'severity_threshold': self.severity_threshold
        }
        return {**base_metrics, **responder_metrics} 