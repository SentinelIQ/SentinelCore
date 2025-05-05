from django.db import models
from sentinelvision.models import BaseModule
from sentinelvision.logging import get_structured_logger

logger = get_structured_logger('sentinelvision.analyzers')

class AnalyzerModule(BaseModule):
    """
    Analyzer Module for analyzing observables and generating insights.
    """
    # Analysis Configuration
    analysis_type = models.CharField('Analysis Type', max_length=50)
    confidence_threshold = models.FloatField('Confidence Threshold', default=0.7)
    max_analysis_time = models.PositiveIntegerField('Max Analysis Time (seconds)', default=30)
    
    # Analysis Results
    total_analyses = models.PositiveIntegerField('Total Analyses', default=0)
    total_findings = models.PositiveIntegerField('Total Findings', default=0)
    average_confidence = models.FloatField('Average Confidence', default=0.0)
    
    class Meta:
        verbose_name = 'Analyzer Module'
        verbose_name_plural = 'Analyzer Modules'
        ordering = ['name']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_type = 'analyzer'
    
    def save(self, *args, **kwargs):
        """
        Ensure module_type is set to 'analyzer' before saving.
        """
        # Only set module_type if it's not already set or if it's different
        if not self.module_type or self.module_type != 'analyzer':
            self.module_type = 'analyzer'
        
        # Call parent save method
        super().save(*args, **kwargs)
    
    def execute(self, observable, *args, **kwargs):
        """
        Execute analysis on an observable.
        
        Args:
            observable: The observable to analyze
            
        Returns:
            dict: Analysis results
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
            
            # Perform analysis
            result = self.analyze(observable, *args, **kwargs)
            
            # Update metrics
            self.total_analyses += 1
            if result.get('findings'):
                self.total_findings += len(result['findings'])
                confidences = [f.get('confidence', 0) for f in result['findings']]
                if confidences:
                    self.average_confidence = (
                        (self.average_confidence * (self.total_analyses - 1)) + 
                        sum(confidences) / len(confidences)
                    ) / self.total_analyses
            
            # Update status
            self.update_status(
                success=result.get('status') == 'success',
                error=result.get('error')
            )
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Error executing analyzer module {self.name}: {error_msg}",
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
    
    def analyze(self, observable, *args, **kwargs):
        """
        Analyze an observable.
        This method should be implemented by specific analyzer types.
        
        Args:
            observable: The observable to analyze
            
        Returns:
            dict: Analysis results
        """
        raise NotImplementedError("Analyzer types must implement analyze()")
    
    def validate_configuration(self):
        """
        Validate analyzer configuration.
        
        Returns:
            bool: True if configuration is valid
        """
        return bool(
            self.analysis_type and
            0 <= self.confidence_threshold <= 1 and
            self.max_analysis_time > 0
        )
    
    def get_metrics(self):
        """
        Get analyzer-specific metrics.
        
        Returns:
            dict: Analyzer metrics
        """
        base_metrics = super().get_metrics()
        analyzer_metrics = {
            'total_analyses': self.total_analyses,
            'total_findings': self.total_findings,
            'average_confidence': self.average_confidence,
            'confidence_threshold': self.confidence_threshold
        }
        return {**base_metrics, **analyzer_metrics} 