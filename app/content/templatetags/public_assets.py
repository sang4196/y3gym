"""Content-versioned URLs for the small, first-party public UI asset set.

Source assets and collectstatic output must belong to the same deployment.
This does not change Wagtail/admin storage or public media URLs.
"""
import hashlib
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()
PUBLIC_ASSETS = frozenset({'site.css', 'navigation.js', 'reveal.js', 'popups.js', 'google-maps.js'})


@register.simple_tag
def public_static(name):
    if name not in PUBLIC_ASSETS:
        raise template.TemplateSyntaxError('Unknown public UI asset')
    path = finders.find(name)
    if path is None:
        raise template.TemplateSyntaxError('Missing public UI asset')
    # Read content, not mtime/size or a process-cached version: runserver has no
    # autoreloader here and same-size edits must invalidate cached URLs too.
    version = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    url = urlsplit(static(name))
    query = [(key, value) for key, value in parse_qsl(url.query) if key != 'v']
    query.append(('v', version))
    return urlunsplit((url.scheme, url.netloc, url.path, urlencode(query), url.fragment))
