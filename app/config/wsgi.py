"""Production candidate entrypoint; never falls back to local/test settings."""
import os
from django.core.exceptions import ImproperlyConfigured
if os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.production') != 'config.settings.production':
    raise ImproperlyConfigured('Use the production settings with this WSGI entrypoint')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
