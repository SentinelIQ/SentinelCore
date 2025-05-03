"""
Utilities for working with enums in Django models and DRF serializers.
"""
from enum import Enum
from typing import Type, List, Tuple, Any


def enum_to_choices(enum_class: Type[Enum]) -> List[Tuple[Any, str]]:
    """
    Convert an Enum class to Django model choices format.
    
    Args:
        enum_class: The Enum class to convert
        
    Returns:
        List of tuples in Django choices format (value, display_name)
        
    Example:
        class StatusEnum(str, Enum):
            OPEN = "open"
            CLOSED = "closed"
            
        class MyModel(models.Model):
            status = models.CharField(
                max_length=20,
                choices=enum_to_choices(StatusEnum)
            )
    """
    return [(item.value, item.name.replace('_', ' ').title()) for item in enum_class]


def enum_values(enum_class: Type[Enum]) -> List[Any]:
    """
    Get a list of all values from an Enum class.
    
    Args:
        enum_class: The Enum class to extract values from
        
    Returns:
        List of enum values
        
    Example:
        class StatusEnum(str, Enum):
            OPEN = "open"
            CLOSED = "closed"
            
        # Returns ["open", "closed"]
        values = enum_values(StatusEnum)
    """
    return [item.value for item in enum_class] 