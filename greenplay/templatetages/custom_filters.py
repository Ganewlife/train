# greenplay/templatetags/custom_filters.py
from django import template
register = template.Library()

@register.filter
def split(value, separator=","):
    return value.split(separator)