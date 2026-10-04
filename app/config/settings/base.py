"""Common application settings. Environment credentials belong in local/test/prod."""
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[2]
RUNTIME = BASE_DIR / '.runtime'
DEBUG = False
INSTALLED_APPS = [
    'content', 'wagtail.snippets', 'wagtail.users', 'wagtail.images',
    'wagtail.documents', 'wagtail.embeds', 'wagtail.sites', 'wagtail.search',
    'wagtail.admin', 'wagtail', 'modelcluster', 'taggit',
    'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions',
    'django.contrib.messages', 'django.contrib.staticfiles',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware', 'content.middleware.BoundaryMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True,
 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
TIME_ZONE = 'Asia/Seoul'
LANGUAGE_CODE = 'ko'
STATIC_URL = '/static/'
STATIC_ROOT = RUNTIME / 'static'
STATICFILES_DIRS = [BASE_DIR / 'assets']
MEDIA_URL = '/media/'  # never mounted
STORAGES = {'default': {'BACKEND': 'content.storage.PrivateStorage'}, 'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}}
FILE_UPLOAD_PERMISSIONS = 0o600
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o700
WAGTAIL_SITE_NAME = '홈페이지 관리'
WAGTAILIMAGES_IMAGE_FORM_BASE = 'content.forms.ImmutableImageForm'
WAGTAILIMAGES_EXTENSIONS = ['png', 'jpg', 'jpeg']
WAGTAILIMAGES_MAX_UPLOAD_SIZE = 5 * 1024 * 1024
WAGTAILIMAGES_MAX_IMAGE_PIXELS = 16_000_000
WAGTAILSEARCH_BACKENDS = {'default': {'BACKEND': 'wagtail.search.backends.database'}}
AUTH_PASSWORD_VALIDATORS = [
 {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
 {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
 {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
]
