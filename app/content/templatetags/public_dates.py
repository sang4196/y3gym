from zoneinfo import ZoneInfo
from django import template
from django.utils.dateparse import parse_datetime

register = template.Library()


@register.filter
def lazy_images(value):
    """Annotate already-sanitized DTO HTML without changing the public API body."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(value or '', 'html.parser')
    for image in soup.find_all('img'):
        image['loading'] = 'lazy'
        image['decoding'] = 'async'
    return str(soup)


@register.filter
def seoul_date(value):
    if not value:
        return ''
    parsed = parse_datetime(value)
    return parsed.astimezone(ZoneInfo('Asia/Seoul')).strftime('%Y.%m.%d') if parsed else ''
