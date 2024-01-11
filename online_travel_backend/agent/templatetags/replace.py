# template
from django import template

register = template.Library()


@register.filter(name="replace")
def replace(value, arg):
    return value.replace(arg, " ")


@register.filter
def mul(value, arg):
    return value * arg


def calculate_total_bill(bill, commissions):
    commission1, commission2 = commissions
    return bill + (bill * commission1 * 0.01) + (bill * commission2 * 0.01)
