"""WSL development only; isolated peer-authenticated PostgreSQL and local media."""
import os
import secrets
from .base import *
RUNTIME.mkdir(mode=0o700, parents=True, exist_ok=True)
key = RUNTIME / 'django-secret'
try:
    fd = os.open(key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    pass
else:
    with os.fdopen(fd, 'w') as stream:
        stream.write(secrets.token_urlsafe(64))
SECRET_KEY = key.read_text()
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
PUBLIC_ORIGIN = 'http://127.0.0.1:8766'
WAGTAILADMIN_BASE_URL = PUBLIC_ORIGIN
SESSION_COOKIE_NAME = 'y3gym_dev_session'
CSRF_COOKIE_NAME = 'y3gym_dev_csrf'
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'y3gym_dev', 'USER': 'y3gym_dev', 'HOST': str(RUNTIME / 'pg-socket'), 'PORT': '55432', 'CONN_MAX_AGE': 0}}
MEDIA_ROOT = RUNTIME / 'private-media'
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
