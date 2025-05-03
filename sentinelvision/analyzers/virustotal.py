import requests
import time
from django.db import models
from django.utils import timezone
from sentinelvision.models import AnalyzerModule, ExecutionRecord
from observables.models import Observable
from api.v1.sentinelvision.enums import ExecutionStatusEnum
from api.v1.observables.enums import ObservableTypeEnum
from api.core.utils.enum_utils import enum_to_choices


class VirusTotalAnalyzer(AnalyzerModule):
    """
    Analyzer module for enriching observables using the VirusTotal API.
    Supports IP, domain, URL, and hash observables.
    """
    # Default module type
    module_type = 'analyzer'
    
    # Add analyzermodule_ptr with a default value to fix migration
    analyzermodule_ptr = models.OneToOneField(
        AnalyzerModule,
        on_delete=models.CASCADE,
        parent_link=True,
        primary_key=True,
        auto_created=True,
        default=1  # Default value for migration
    )
    
    # Configuration fields
    api_key = models.CharField('API Key', max_length=255)
    use_premium_api = models.BooleanField(
        'Use Premium API',
        default=False
    )
    request_rate_limit = models.PositiveIntegerField(
        'Request Rate Limit (per minute)',
        default=4,  # Default for free API
        help_text='Requests per minute allowed by your VirusTotal API tier'
    )
    
    class Meta:
        verbose_name = 'VirusTotal Analyzer'
        verbose_name_plural = 'VirusTotal Analyzers'
    
    def save(self, *args, **kwargs):
        # Ensure module_type is always 'analyzer'
        self.module_type = 'analyzer'
        super().save(*args, **kwargs)
    
    def analyze(self, observable, execution_record, **kwargs):
        """
        Analyze an observable using the VirusTotal API.
        
        Args:
            observable (Observable): The observable to analyze
            execution_record (ExecutionRecord): The execution record to update
            **kwargs: Additional parameters for analysis
            
        Returns:
            dict: Analysis results
        """
        if not self.validate_compatibility(observable.type):
            error_message = f"Observable type {observable.type} not supported by VirusTotal analyzer"
            self._update_execution_record(
                execution_record, 
                ExecutionStatusEnum.ERROR.value, 
                execution_log=error_message
            )
            return {'error': error_message}
        
        # Update execution record status to running
        self._update_execution_record(
            execution_record,
            ExecutionStatusEnum.RUNNING.value,
            started_at=timezone.now()
        )
        
        try:
            # Get VirusTotal data for the observable
            result = self._get_virustotal_data(observable)
            
            # Update observable enrichment data
            if 'data' in result and not 'error' in result:
                observable.enrichment_data.update({
                    'virustotal': result.get('data', {})
                })
                observable.save(update_fields=['enrichment_data'])
            
            # Calculate duration and update execution record
            completed_at = timezone.now()
            duration_seconds = (completed_at - execution_record.started_at).total_seconds()
            
            self._update_execution_record(
                execution_record,
                ExecutionStatusEnum.SUCCESS.value,
                completed_at=completed_at,
                duration_seconds=duration_seconds,
                output_data=result
            )
            
            return result
        
        except Exception as e:
            error_message = f"Error analyzing with VirusTotal: {str(e)}"
            
            # Update execution record with failure status
            self._update_execution_record(
                execution_record,
                ExecutionStatusEnum.ERROR.value,
                completed_at=timezone.now(),
                duration_seconds=(timezone.now() - execution_record.started_at).total_seconds(),
                error_message=error_message
            )
            
            return {'error': error_message}
    
    def _get_virustotal_data(self, observable):
        """
        Query the VirusTotal API for data about the observable.
        
        Args:
            observable (Observable): The observable to query
            
        Returns:
            dict: VirusTotal API response
        """
        headers = {
            'x-apikey': self.api_key,
            'Accept': 'application/json'
        }
        
        base_url = 'https://www.virustotal.com/api/v3'
        
        # Determine endpoint based on observable type
        if observable.type == ObservableTypeEnum.IP.value:
            endpoint = f"{base_url}/ip_addresses/{observable.value}"
        elif observable.type == ObservableTypeEnum.DOMAIN.value:
            endpoint = f"{base_url}/domains/{observable.value}"
        elif observable.type == ObservableTypeEnum.URL.value:
            endpoint = f"{base_url}/urls/{self._encode_url(observable.value)}"
        elif observable.type in [ObservableTypeEnum.HASH_MD5.value, ObservableTypeEnum.HASH_SHA1.value, ObservableTypeEnum.HASH_SHA256.value]:
            endpoint = f"{base_url}/files/{observable.value}"
        else:
            return {'error': f"Unsupported observable type: {observable.type}"}
        
        # Rate limiting
        time.sleep(60 / self.request_rate_limit)
        
        # Make API request
        response = requests.get(endpoint, headers=headers, timeout=60)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                'error': f"VirusTotal API error: {response.status_code}",
                'details': response.text
            }
    
    def _encode_url(self, url):
        """
        Encode a URL for use with the VirusTotal API.
        
        Args:
            url (str): The URL to encode
            
        Returns:
            str: The encoded URL identifier
        """
        import base64
        return base64.urlsafe_b64encode(url.encode()).decode().strip('=')
    
    def _update_execution_record(self, execution_record, status, **kwargs):
        """
        Update the execution record with new data.
        
        Args:
            execution_record (ExecutionRecord): The execution record to update
            status (str): The new status
            **kwargs: Additional fields to update
        """
        execution_record.status = status
        
        for key, value in kwargs.items():
            if hasattr(execution_record, key):
                setattr(execution_record, key, value)
        
        execution_record.save() 