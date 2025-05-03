import requests
from django.db import models
from django.utils import timezone
from sentinelvision.models import ResponderModule, ExecutionRecord
from observables.models import Observable
from api.v1.sentinelvision.enums import ExecutionStatusEnum, ResponderIntegrationTypeEnum
from api.v1.observables.enums import ObservableTypeEnum
from api.core.utils.enum_utils import enum_to_choices


class BlockIPResponder(ResponderModule):
    """
    Responder module for blocking malicious IP addresses through security integrations.
    Supports various security systems via API or custom connectors.
    """
    # Default module type
    module_type = 'responder'
    
    # Add respondermodule_ptr with a default value to fix migration
    respondermodule_ptr = models.OneToOneField(
        ResponderModule,
        on_delete=models.CASCADE,
        parent_link=True,
        primary_key=True,
        auto_created=True,
        default=1  # Default value for migration
    )
    
    integration_type = models.CharField(
        'Integration Type',
        max_length=20,
        choices=enum_to_choices(ResponderIntegrationTypeEnum),
        default=ResponderIntegrationTypeEnum.FIREWALL.value
    )
    api_url = models.URLField('API URL')
    api_key = models.CharField('API Key', max_length=255)
    verify_ssl = models.BooleanField('Verify SSL', default=True)
    additional_params = models.JSONField(
        'Additional Parameters',
        default=dict,
        blank=True,
        help_text='Additional parameters required by the integration'
    )
    
    class Meta:
        verbose_name = 'Block IP Responder'
        verbose_name_plural = 'Block IP Responders'
    
    def save(self, *args, **kwargs):
        # Ensure module_type is always 'responder'
        self.module_type = 'responder'
        super().save(*args, **kwargs)
    
    def respond(self, observable, execution_record, **kwargs):
        """
        Block an IP address using the configured security integration.
        
        Args:
            observable (Observable): The observable to block
            execution_record (ExecutionRecord): The execution record to update
            **kwargs: Additional parameters for response
            
        Returns:
            dict: Response results
        """
        if observable.type != ObservableTypeEnum.IP.value:
            error_message = f"Observable type {observable.type} not supported by Block IP responder"
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
            # Block the IP address through the appropriate integration
            if self.integration_type == ResponderIntegrationTypeEnum.FIREWALL.value:
                result = self._block_via_firewall(observable)
            elif self.integration_type == ResponderIntegrationTypeEnum.SOAR.value:
                result = self._block_via_soar(observable)
            elif self.integration_type == ResponderIntegrationTypeEnum.WAF.value:
                result = self._block_via_waf(observable)
            elif self.integration_type == ResponderIntegrationTypeEnum.CUSTOM.value:
                result = self._block_via_custom(observable)
            else:
                result = {'error': f"Unknown integration type: {self.integration_type}"}
            
            # Calculate duration and update execution record
            completed_at = timezone.now()
            duration_seconds = (completed_at - execution_record.started_at).total_seconds()
            
            status = ExecutionStatusEnum.SUCCESS.value if 'error' not in result else ExecutionStatusEnum.ERROR.value
            
            self._update_execution_record(
                execution_record,
                status,
                completed_at=completed_at,
                duration_seconds=duration_seconds,
                output_data=result,
                execution_log=result.get('logs', '')
            )
            
            return result
        
        except Exception as e:
            error_message = f"Error executing block IP responder: {str(e)}"
            
            # Update execution record with failure status
            self._update_execution_record(
                execution_record,
                ExecutionStatusEnum.ERROR.value,
                completed_at=timezone.now(),
                duration_seconds=(timezone.now() - execution_record.started_at).total_seconds(),
                error_message=error_message
            )
            
            return {'error': error_message}
    
    def _block_via_firewall(self, observable):
        """
        Block IP via firewall API.
        
        Args:
            observable (Observable): The IP observable to block
            
        Returns:
            dict: API response details
        """
        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        payload = {
            'ip': observable.value,
            'reason': f"Blocked by SentinelVision - {observable.description}",
            'source': 'SentinelVision',
            **self.additional_params
        }
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            verify=self.verify_ssl,
            timeout=60
        )
        
        if response.status_code in (200, 201, 202, 204):
            return {
                'status': 'success',
                'message': f"Successfully blocked IP {observable.value}",
                'integration_response': response.json() if response.content else {},
                'logs': f"Successfully blocked IP {observable.value} via {self.integration_type}"
            }
        else:
            return {
                'error': f"Failed to block IP: {response.status_code}",
                'details': response.text,
                'logs': f"Failed to block IP {observable.value} via {self.integration_type}: {response.status_code}"
            }
    
    def _block_via_soar(self, observable):
        """
        Create a blocking action in SOAR platform.
        
        Args:
            observable (Observable): The IP observable to block
            
        Returns:
            dict: API response details
        """
        # Implementation for SOAR platform integration
        pass
    
    def _block_via_waf(self, observable):
        """
        Block IP in Web Application Firewall.
        
        Args:
            observable (Observable): The IP observable to block
            
        Returns:
            dict: API response details
        """
        # Implementation for WAF integration
        pass
    
    def _block_via_custom(self, observable):
        """
        Block IP using custom integration.
        
        Args:
            observable (Observable): The IP observable to block
            
        Returns:
            dict: API response details
        """
        # Implementation for custom integration
        pass
    
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