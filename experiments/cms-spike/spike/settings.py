"""Local SPIKE-01 only. No production settings or external services."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RUNTIME = BASE_DIR / ".runtime"
RUNTIME.mkdir(mode=0o700, exist_ok=True)
key_path = RUNTIME / "secret-key"
try:
    key_fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    pass
else:
    with os.fdopen(key_fd, "w") as key_file:
        key_file.write(secrets.token_urlsafe(64))
SECRET_KEY = key_path.read_text()
DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
INSTALLED_APPS = [
    "posts", "wagtail.snippets", "wagtail.users", "wagtail.images",
    "wagtail.documents", "wagtail.embeds", "wagtail.sites", "wagtail.search",
    "wagtail.admin", "wagtail", "modelcluster", "taggit",
    "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "django.contrib.staticfiles",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "posts.middleware.SpikeBoundaryMiddleware",
]
ROOT_URLCONF = "spike.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": RUNTIME / "spike.sqlite3"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "Asia/Seoul"
LANGUAGE_CODE = "en-us"
STATIC_URL = "/static/"
STATIC_ROOT = RUNTIME / "static"
MEDIA_ROOT = RUNTIME / "private-media"
MEDIA_URL = "/media/"  # deliberately never served
STORAGES = {
    "default": {"BACKEND": "posts.storage.PrivateMediaStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
FILE_UPLOAD_PERMISSIONS = 0o600
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o700
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_TEMP_DIR = RUNTIME
WAGTAIL_SITE_NAME = "SPIKE-01 TEST CONTENT ONLY"
WAGTAILADMIN_BASE_URL = "http://127.0.0.1:8765"
WAGTAILIMAGES_IMAGE_FORM_BASE = "posts.image_forms.ImmutableImageForm"
WAGTAILIMAGES_EXTENSIONS = ["png", "jpg", "jpeg"]
WAGTAILIMAGES_MAX_UPLOAD_SIZE = 5 * 1024 * 1024
WAGTAILIMAGES_MAX_IMAGE_PIXELS = 16_000_000
WAGTAIL_USAGE_COUNT_ENABLED = True
WAGTAILSEARCH_BACKENDS = {"default": {"BACKEND": "wagtail.search.backends.database"}}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]
