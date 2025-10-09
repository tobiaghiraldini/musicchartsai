"""
Custom template filters for ACRCloud app
"""
import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='divide')
def divide(value, arg):
    """
    Divides the value by the argument.
    
    Usage: {{ value|divide:1000 }}
    """
    try:
        return int(value) // int(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0


@register.filter(name='ms_to_seconds')
def ms_to_seconds(value):
    """
    Converts milliseconds to seconds.
    
    Usage: {{ value|ms_to_seconds }}
    """
    try:
        return int(value) / 1000
    except (ValueError, TypeError):
        return 0


@register.filter(name='to_json')
def to_json(value):
    """
    Converts a Python object to JSON string.
    
    Usage: {{ dict_value|to_json }}
    """
    try:
        return mark_safe(json.dumps(value))
    except (TypeError, ValueError):
        return '{}'

