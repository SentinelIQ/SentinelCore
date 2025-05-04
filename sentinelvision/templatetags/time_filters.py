from django import template

register = template.Library()

@register.filter
def intdiv(value, arg):
    """
    Performs integer division of value by arg.
    
    Usage:
    {{ value|intdiv:arg }}
    
    Example:
    {{ 125|intdiv:60 }} -> 2 (125 ÷ 60 = 2.08, returns 2)
    """
    try:
        return int(int(value) // int(arg))
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mod(value, arg):
    """
    Returns the remainder when value is divided by arg.
    
    Usage:
    {{ value|mod:arg }}
    
    Example:
    {{ 125|mod:60 }} -> 5 (125 % 60 = 5)
    """
    try:
        return int(int(value) % int(arg))
    except (ValueError, ZeroDivisionError):
        return 0 