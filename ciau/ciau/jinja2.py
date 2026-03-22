from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': reverse,
    })
    env.filters.update({
        'fcfa': format_fcfa,
    })
    return env


def format_fcfa(value):
    """Format a number as FCFA: 1 500 000 FCFA"""
    if value is None:
        return '—'
    try:
        formatted = f"{int(value):,}".replace(',', ' ')
        return f"{formatted} FCFA"
    except (ValueError, TypeError):
        return str(value)
