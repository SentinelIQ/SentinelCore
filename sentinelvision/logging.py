import logging
import os
from pathlib import Path
from django.conf import settings

def get_structured_logger(name):
    """
    Get a structured logger with proper configuration.
    
    Args:
        name (str): The name of the logger
        
    Returns:
        logging.Logger: A configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path(settings.BASE_DIR) / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Configure the logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create handlers
    api_handler = logging.FileHandler(logs_dir / 'api.log')
    error_handler = logging.FileHandler(logs_dir / 'error.log')
    django_handler = logging.FileHandler(logs_dir / 'django.log')
    
    # Set log levels
    api_handler.setLevel(logging.INFO)
    error_handler.setLevel(logging.ERROR)
    django_handler.setLevel(logging.INFO)
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    json_formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s", "extra": %(extra)s}'
    )
    
    # Add formatters to handlers
    api_handler.setFormatter(json_formatter)
    error_handler.setFormatter(formatter)
    django_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(api_handler)
    logger.addHandler(error_handler)
    logger.addHandler(django_handler)
    
    return logger 