# template
from django import template

register = template.Library()


@register.filter(name="replace")
def replace(value, arg):
    return value.replace(arg, " ")

@register.filter
def mul(value, arg):
    return value * arg