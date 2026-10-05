from zoneinfo import ZoneInfo
from django import template
from django.utils.dateparse import parse_datetime

register = template.Library()


@register.filter
def seoul_date(value):
    if not value:
        return ''
    parsed = parse_datetime(value)
    return parsed.astimezone(ZoneInfo('Asia/Seoul')).strftime('%Y.%m.%d') if parsed else ''
