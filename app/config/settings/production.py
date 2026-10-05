"""Deployment candidate: explicit environment only; never imports local settings."""
import ipaddress
import os
import re
from urllib.parse import urlsplit
from django.core.exceptions import ImproperlyConfigured
from .base import *


def required(name):
    value = os.environ.get('Y3GYM_' + name, '')
    if not value or value != value.strip() or any(ord(c) < 32 for c in value):
        raise ImproperlyConfigured('Missing or invalid production setting: ' + name)
    return value


def domain(value):
    if not re.fullmatch(r'(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]*', value):
        raise ImproperlyConfigured('Exact DNS hostnames are required')
    if value.endswith('.localhost') or value == 'localhost':
        raise ImproperlyConfigured('Local development hosts are forbidden')
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return value
    raise ImproperlyConfigured('A deployment DNS hostname is required')


SECRET_KEY = required('SECRET_KEY')
if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith(('django-insecure-', 'test-only-')):
    raise ImproperlyConfigured('A unique strong production key is required')
ALLOWED_HOSTS = [domain(value) for value in required('ALLOWED_HOSTS').split(',')]
PUBLIC_ORIGIN = required('PUBLIC_ORIGIN')
origin = urlsplit(PUBLIC_ORIGIN)
if origin.scheme != 'https' or origin.netloc not in ALLOWED_HOSTS or origin.path or origin.query or origin.fragment or origin.username or origin.password:
    raise ImproperlyConfigured('PUBLIC_ORIGIN must be an exact allowed HTTPS origin without a path')
CSRF_TRUSTED_ORIGINS = [PUBLIC_ORIGIN]
WAGTAILADMIN_BASE_URL = PUBLIC_ORIGIN
WSGI_APPLICATION = 'config.wsgi.application'
DEBUG = False
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_NAME = '__Host-y3gym_session'
CSRF_COOKIE_NAME = '__Host-y3gym_csrf'
SECURE_SSL_REDIRECT = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
# HSTS starts disabled until actual TLS, subdomains and rollback have been checked.
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
# Gunicorn's explicit trusted peer list may set wsgi.url_scheme. Django never
# trusts arbitrary X-Forwarded-Proto/Host headers on its own.
SECURE_PROXY_SSL_HEADER = None
USE_X_FORWARDED_HOST = USE_X_FORWARDED_PORT = False


def directory(name):
    value = Path(required(name))
    if not value.is_absolute() or value != value.resolve() or not value.is_dir():
        raise ImproperlyConfigured(name + ' must be an existing absolute non-symlink directory')
    for parent in [value, *value.parents]:
        if parent.is_symlink():
            raise ImproperlyConfigured('Symlink storage paths are forbidden')
    if value.stat().st_uid != os.getuid() or value.stat().st_mode & 0o077:
        raise ImproperlyConfigured(name + ' must be owned by the app user with mode 0700')
    if value == BASE_DIR or BASE_DIR in value.parents or value in BASE_DIR.parents:
        raise ImproperlyConfigured('Production storage must be separate from the source/development tree')
    return value


MEDIA_ROOT = directory('MEDIA_ROOT')
STATIC_ROOT = directory('STATIC_ROOT')
FILE_UPLOAD_TEMP_DIR = directory('UPLOAD_TMP')
for a in [MEDIA_ROOT, STATIC_ROOT, FILE_UPLOAD_TEMP_DIR]:
    for b in [MEDIA_ROOT, STATIC_ROOT, FILE_UPLOAD_TEMP_DIR]:
        if a != b and (a in b.parents or b in a.parents):
            raise ImproperlyConfigured('Storage directories must be disjoint')
if len({MEDIA_ROOT, STATIC_ROOT, FILE_UPLOAD_TEMP_DIR}) != 3:
    raise ImproperlyConfigured('Storage directories must be distinct')
DB_NAME = required('DB_NAME')
DB_USER = required('DB_USER')
if not re.fullmatch(r'[a-z][a-z0-9_]{0,62}', DB_NAME) or not re.fullmatch(r'[a-z][a-z0-9_]{0,62}', DB_USER):
    raise ImproperlyConfigured('Invalid PostgreSQL database/role name')
if DB_NAME in {'postgres','template0','template1','y3gym_dev','y3gym_test'} or DB_USER in {'postgres','y3gym_owner','y3gym_dev'}:
    raise ImproperlyConfigured('Default/admin/development database credentials are forbidden')
DB_HOST = required('DB_HOST')
DB_PORT = required('DB_PORT')
if not DB_PORT.isdecimal() or not 1 <= int(DB_PORT) <= 65535:
    raise ImproperlyConfigured('Invalid PostgreSQL port')
options = {'connect_timeout': 5}
if DB_HOST.startswith('/'):
    socket = Path(DB_HOST)
    if socket != socket.resolve() or not socket.is_dir():
        raise ImproperlyConfigured('Invalid PostgreSQL Unix socket directory')
    DB_PASSWORD = ''  # explicitly selected local Unix peer boundary
else:
    domain(DB_HOST)
    DB_PASSWORD = required('DB_PASSWORD')
    certificate = Path(required('DB_SSLROOTCERT'))
    if not certificate.is_absolute() or certificate != certificate.resolve() or not certificate.is_file():
        raise ImproperlyConfigured('An existing non-symlink PostgreSQL CA certificate is required')
    options.update(sslmode='verify-full', sslrootcert=str(certificate))
DATABASES = {'default': {'ENGINE':'django.db.backends.postgresql', 'NAME':DB_NAME, 'USER':DB_USER,
                         'HOST':DB_HOST, 'PORT':DB_PORT, 'PASSWORD':DB_PASSWORD,
                         'OPTIONS':options, 'CONN_MAX_AGE':60}}
