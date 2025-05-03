import logging
from django.utils import timezone
from sentinelvision.models import ExecutionRecord
from incidents.models import TimelineEvent
from observables.models import Observable
from api.v1.sentinelvision.enums import ExecutionStatusEnum
from api.v1.incidents.enums import TimelineEventTypeEnum

logger = logging.getLogger('api')


class ModuleExecutor:
    """
    Service class for executing SentinelVision modules (analyzers/responders)
    against observables with proper tracking and logging.
    """
    
    @staticmethod
    def execute_analyzer(analyzer, observable, user, incident=None, alert=None, execution_args=None):
        """
        Execute an analyzer module against an observable.
        
        Args:
            analyzer: The analyzer module instance
            observable: The observable to analyze
            user: The user executing the analyzer
            incident: Optional related incident
            alert: Optional related alert
            execution_args: Optional execution arguments
            
        Returns:
            tuple: (ExecutionRecord, result)
        """
        if not analyzer.validate_compatibility(observable.type):
            logger.warning(
                f"Analyzer {analyzer.name} not compatible with observable type {observable.type}"
            )
            return None, {'error': 'Analyzer not compatible with observable type'}
        
        # Create execution record
        execution_record = ExecutionRecord.objects.create(
            module_type='analyzer',
            module_name=analyzer.name,
            company=observable.company,
            incident=incident,
            alert=alert,
            executed_by=user,
            status=ExecutionStatusEnum.PENDING.value,
            execution_arguments=execution_args or {},
            input_data={'observable_id': str(observable.id), 'observable_type': observable.type, 'observable_value': observable.value}
        )
        
        # Execute analyzer
        execution_record.start_execution()
        result = analyzer.analyze(observable, execution_record, **execution_args or {})
        
        # Log to incident timeline if applicable
        if incident:
            ModuleExecutor._log_to_timeline(
                incident, 
                observable, 
                analyzer.name, 
                execution_record.status,
                'analyze'
            )
        
        return execution_record, result
    
    @staticmethod
    def execute_responder(responder, observable, user, incident=None, alert=None, execution_args=None):
        """
        Execute a responder module against an observable.
        
        Args:
            responder: The responder module instance
            observable: The observable to respond to
            user: The user executing the responder
            incident: Optional related incident
            alert: Optional related alert
            execution_args: Optional execution arguments
            
        Returns:
            tuple: (ExecutionRecord, result)
        """
        if not responder.validate_compatibility(observable.type):
            logger.warning(
                f"Responder {responder.name} not compatible with observable type {observable.type}"
            )
            return None, {'error': 'Responder not compatible with observable type'}
        
        # Create execution record
        execution_record = ExecutionRecord.objects.create(
            module_type='responder',
            module_name=responder.name,
            company=observable.company,
            incident=incident,
            alert=alert,
            executed_by=user,
            status=ExecutionStatusEnum.PENDING.value,
            execution_arguments=execution_args or {},
            input_data={'observable_id': str(observable.id), 'observable_type': observable.type, 'observable_value': observable.value}
        )
        
        # Execute responder
        execution_record.start_execution()
        result = responder.respond(observable, execution_record, **execution_args or {})
        
        # Log to incident timeline if applicable
        if incident:
            ModuleExecutor._log_to_timeline(
                incident, 
                observable, 
                responder.name, 
                execution_record.status,
                'respond'
            )
        
        return execution_record, result
    
    @staticmethod
    def _log_to_timeline(incident, observable, module_name, status, action_type):
        """
        Log module execution to incident timeline.
        
        Args:
            incident: The incident to log to
            observable: The observable that was processed
            module_name: Name of the module that was executed
            status: Execution status
            action_type: Type of action (analyze/respond)
        """
        status_map = {
            ExecutionStatusEnum.SUCCESS.value: 'successfully',
            ExecutionStatusEnum.ERROR.value: 'with errors',
            ExecutionStatusEnum.SKIPPED.value: 'but was skipped',
            ExecutionStatusEnum.RUNNING.value: 'and is running'
        }
        
        status_text = status_map.get(status, '')
        
        if action_type == 'analyze':
            message = f"Analyzer '{module_name}' ran {status_text} on observable {observable.type}: {observable.value}"
            title = f"Analyzer: {module_name}"
        else:
            message = f"Responder '{module_name}' executed {status_text} against {observable.type}: {observable.value}"
            title = f"Responder: {module_name}"
        
        # Create timeline event
        TimelineEvent.objects.create(
            incident=incident,
            type=TimelineEventTypeEnum.SYSTEM.value,
            title=title,
            message=message,
            company=incident.company,
            metadata={
                'module': module_name,
                'observable_id': str(observable.id),
                'observable_type': observable.type,
                'observable_value': observable.value,
                'status': status,
                'action': action_type
            }
        ) 