"""Only the dedicated PostgreSQL test role may create/drop a test database."""
import tempfile
from .base import *
SECRET_KEY = 'test-only-not-used-by-development-or-production'
ALLOWED_HOSTS = ['testserver', '127.0.0.1', 'localhost']
PUBLIC_ORIGIN = 'http://testserver'
WAGTAILADMIN_BASE_URL = PUBLIC_ORIGIN
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'postgres', 'USER': 'y3gym_test', 'HOST': str(RUNTIME / 'pg-socket'), 'PORT': '55432', 'TEST': {'NAME': 'y3gym_test'}, 'CONN_MAX_AGE': 0}}
MEDIA_ROOT = Path(tempfile.mkdtemp(prefix='test-media-', dir=RUNTIME))
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
