import json
import logging
import sys
import traceback
from datetime import datetime
from django.conf import settings

# Default context fields for each log entry
DEFAULT_CONTEXT = {
    'app': 'sentinelvision',
    'environment': getattr(settings, 'ENVIRONMENT', 'development'),
}


class StructuredJsonFormatter(logging.Formatter):
    """
    Format logs as structured JSON objects for improved monitoring and searching.
    """
    
    def format(self, record):
        """
        Format the log record as a JSON object with standardized fields.
        
        Args:
            record: Log record to format
            
        Returns:
            str: JSON-formatted log entry
        """
        # Start with default context
        log_object = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            **DEFAULT_CONTEXT
        }
        
        # Include exception info if available
        if record.exc_info:
            log_object['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Include extra context from logger.info(..., extra={...})
        if hasattr(record, 'feed_name'):
            log_object['feed_name'] = record.feed_name
        if hasattr(record, 'observable_type'):
            log_object['observable_type'] = record.observable_type
        if hasattr(record, 'incident_id'):
            log_object['incident_id'] = record.incident_id
        if hasattr(record, 'alert_id'):
            log_object['alert_id'] = record.alert_id
        if hasattr(record, 'execution_id'):
            log_object['execution_id'] = record.execution_id
        if hasattr(record, 'tenant_id'):
            log_object['tenant_id'] = record.tenant_id
        
        # Include any other extra attributes
        for key, value in record.__dict__.items():
            if key not in ('args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                           'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
                           'msecs', 'message', 'msg', 'name', 'pathname', 'process',
                           'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName'):
                log_object[key] = value
        
        return json.dumps(log_object)


def get_structured_logger(name):
    """
    Get a logger configured with structured JSON formatting.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    
    # Only add handler if it doesn't already exist
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
    
    return logger 