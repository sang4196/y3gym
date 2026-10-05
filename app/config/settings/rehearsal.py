"""Only fresh restore_drill databases/media; not a user-selectable dev environment."""
import os
import re
from django.core.exceptions import ImproperlyConfigured
from .base import *
run_id = os.environ.get('Y3GYM_DRILL_ID', '')
side = os.environ.get('Y3GYM_DRILL_SIDE', '')
if not re.fullmatch('[a-f0-9]{24}', run_id) or side not in {'src','dst'}:
    raise ImproperlyConfigured('Use the isolated restore_drill runner')
root = RUNTIME / ('restore-drill-' + run_id)
if root.is_symlink() or root.resolve() != root or not root.is_dir() or root.stat().st_mode & 0o077 or root.stat().st_uid != os.getuid():
    raise ImproperlyConfigured('Invalid rehearsal directory')
MEDIA_ROOT = root / (side + '-media')
if not MEDIA_ROOT.is_dir() or MEDIA_ROOT.is_symlink():
    raise ImproperlyConfigured('Missing isolated media')
SECRET_KEY = os.environ['Y3GYM_DRILL_KEY']
ALLOWED_HOSTS = ['testserver','127.0.0.1']
PUBLIC_ORIGIN = 'http://testserver'
WAGTAILADMIN_BASE_URL = PUBLIC_ORIGIN
DATABASES = {'default': {'ENGINE':'django.db.backends.postgresql', 'NAME':f'y3gym_drill_{run_id}_{side}',
                         'USER':'y3gym_test','HOST':str(RUNTIME/'pg-socket'),'PORT':'55432','CONN_MAX_AGE':0,
                         'OPTIONS':{'passfile':str(root/'pgpass.empty'),'connect_timeout':5}}}
FILE_UPLOAD_TEMP_DIR = root
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
