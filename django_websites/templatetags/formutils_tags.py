from django import template
from django.forms import CheckboxInput, Textarea

register = template.Library()


@register.filter(name='is_checkbox')
def is_checkbox(field):
    return isinstance(field.field.widget, CheckboxInput)


@register.filter(name='is_textarea')
def is_textarea(field):
    return isinstance(field.field.widget, Textarea)
