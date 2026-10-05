"""One-time DEV-07-B synthetic data. Not an operational seed/import service."""
from datetime import timedelta
from io import BytesIO
from pathlib import Path
import hashlib
import json
import os
import sys
import uuid

from PIL import Image as PillowImage, ImageDraw
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import CommandError
from django.db import connection
from django.utils import timezone
from wagtail.images import get_image_model
from wagtail.models import Collection
from wagtail.snippets.models import get_snippet_models
from .locking import content_transaction
from .models import Branch, SiteContent, Trainer, TrainerCareer, Post, Popup
from .storage import PrivateStorage

PREFIX = 'DEV-07-B TEST'
CONFIRMATION = 'ADD-LOCAL-TEST-CONTENT-ONCE'
APP_ROOT = Path(__file__).resolve().parents[1]


def process_identity(pid):
    process = Path('/proc') / str(pid)
    return {'uid': process.stat().st_uid, 'cwd': str((process / 'cwd').resolve()),
            'argv': (process / 'cmdline').read_bytes().decode().rstrip('\0').split('\0'),
            'start': (process / 'stat').read_text().split()[21]}


def validate_environment(confirmation, server_pid):
    """Reject before connecting if any configured production/test boundary differs."""
    if confirmation != CONFIRMATION:
        raise CommandError('명시적인 로컬 TEST 추가 확인이 필요합니다.')
    runtime = APP_ROOT / '.runtime'
    db = connection.settings_dict
    if (sys.platform != 'linux' or settings.SETTINGS_MODULE != 'config.settings.local'
        or Path.cwd() != APP_ROOT or settings.BASE_DIR != APP_ROOT or settings.RUNTIME != runtime
        or settings.PUBLIC_ORIGIN != 'http://127.0.0.1:8766'
        or set(settings.ALLOWED_HOSTS) != {'127.0.0.1', 'localhost'}
        or settings.MEDIA_ROOT != runtime / 'private-media'
        or db['ENGINE'] != 'django.db.backends.postgresql' or db['NAME'] != 'y3gym_dev'
        or db['USER'] != 'y3gym_dev' or db['HOST'] != str(runtime / 'pg-socket')
        or str(db['PORT']) != '55432' or db.get('PASSWORD') or db.get('OPTIONS')):
        raise CommandError('정확한 로컬 개발 설정/DB/경로에서만 실행할 수 있습니다.')
    for directory in [runtime, runtime / 'pg-socket', settings.MEDIA_ROOT]:
        if directory != directory.resolve() or not directory.is_dir() or directory.stat().st_uid != os.getuid() or directory.stat().st_mode & 0o077:
            raise CommandError('개발 저장소 소유권/경로/접근 권한을 확인하세요.')
    if type(server_pid) is not int or server_pid <= 0:
        raise CommandError('현재 제품 개발 서버 PID가 필요합니다.')
    expected_argv = [str(APP_ROOT / '.venv/bin/python'), 'manage.py', 'runserver', '127.0.0.1:8766', '--noreload', '--insecure']
    try:
        identity = process_identity(server_pid)
        if identity['uid'] != os.getuid() or identity['cwd'] != str(APP_ROOT) or identity['argv'] != expected_argv:
            raise ValueError
        listeners = []
        for name in ['tcp', 'tcp6']:
            for line in (Path('/proc/net') / name).read_text().splitlines()[1:]:
                row = line.split()
                if row[1].split(':')[1] == f'{8766:04X}' and row[3] == '0A':
                    listeners.append((name, row[1], row[9]))
        if len(listeners) != 1 or listeners[0][:2] != ('tcp', '0100007F:223E'):
            raise ValueError
        sockets = {os.readlink(fd) for fd in (Path('/proc') / str(server_pid) / 'fd').iterdir()}
        if f'socket:[{listeners[0][2]}]' not in sockets or process_identity(server_pid) != identity:
            raise ValueError
    except (OSError, ValueError, IndexError):
        raise CommandError('지정 PID의 제품 개발 서버/루프백 리스너를 확인할 수 없습니다.') from None
    connection.ensure_connection()
    info = connection.connection.info
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_database(), current_user, inet_server_addr(), rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user')
        row = cursor.fetchone()
    if row != ('y3gym_dev', 'y3gym_dev', None, False, False, False) or info.host != str(runtime / 'pg-socket') or info.port != 55432:
        raise CommandError('실제 DB/역할/Unix 연결이 개발 전용 조건과 다릅니다.')
    return runtime / 'dev07b-preview-content-receipt.json'


def _png(kind):
    size = (480, 480) if kind != 'notice' else (960, 540)
    canvas = PillowImage.new('RGB', size, {'profile-a':'#244a61','profile-b':'#5b436c','notice':'#245747'}[kind])
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((24, 24, size[0]-24, size[1]-24), outline='white', width=3)
    draw.text((48, 70), 'TEMPORARY '+('NOTICE' if kind == 'notice' else 'PROFILE '+kind[-1].upper()), fill='white', font_size=28)
    draw.text((48, 140), 'TEST ONLY', fill='white', font_size=36)
    draw.text((48, 220), 'NOT A REAL PERSON / EVENT', fill='white', font_size=19)
    stream = BytesIO(); canvas.save(stream, 'PNG')
    return stream.getvalue()


def _populate_preview_content(receipt):
    """Internal content transaction, tested directly in isolated PG/media.

    The command has no test bypass; environment validation precedes this function.
    Only files from this invocation with unchanged inode/hash are removed on an
    ordinary pre-commit failure. Commit uncertainty/crash leaves its receipt for
    inspection and rejects reruns instead of guessing what was committed.
    """
    # Management commands can run before admin URLs load wagtail_hooks.py.
    # Register snippets first so ordinary save signals update ReferenceIndex.
    get_snippet_models()
    image_model = get_image_model()
    storage = image_model._meta.get_field('file').storage
    if not isinstance(storage, PrivateStorage) or Path(storage.location) != Path(settings.MEDIA_ROOT).resolve():
        raise CommandError('개발 전용 비공개 파일 저장소가 필요합니다.')
    files = []
    run_id = uuid.uuid4().hex
    with content_transaction():
        if receipt.exists() or receipt.is_symlink():
            raise CommandError('이 단위의 실행 기록이 이미 있습니다. 재실행하지 않습니다.')
        if Trainer.objects.exists() or TrainerCareer.objects.exists() or Post.objects.exists() or Popup.objects.exists():
            raise CommandError('기존 트레이너/게시글/팝업 보존: 추가를 중단합니다.')
        if image_model.objects.filter(title__startswith=PREFIX).exists() or any(Path(settings.MEDIA_ROOT).rglob('dev07b-*')):
            raise CommandError('임시 자료 이름/파일 충돌: 추가를 중단합니다.')
        branch = Branch.objects.filter(is_public=True, is_main=True).first()
        if branch is None or not SiteContent.objects.exists():
            raise CommandError('기존 사이트와 공개 본점이 필요합니다.')
        collection = Collection.objects.filter(name='홈페이지 사진', depth=2).first()
        if collection is None:
            raise CommandError('기존 홈페이지 사진 컬렉션이 필요합니다. 권한은 변경하지 않습니다.')
        try:
            fd = os.open(receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            raise CommandError('동일 단위 실행 기록이 이미 있습니다.') from None
        receipt_inode = os.fstat(fd).st_ino
        try:
            images = []
            for kind in ['profile-a', 'profile-b', 'notice']:
                image = image_model(title=f'{PREFIX} 임시 {kind}', collection=collection)
                image.file.save(f'dev07b-{run_id}-{kind}.png', ContentFile(_png(kind)), save=False)
                path = Path(image.file.path)
                record = {'file':image.file.name, 'inode':path.stat().st_ino, 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
                files.append(record)
                image.full_clean(); image.save()
                images.append(image)
            trainers = []
            for index, image in enumerate(images[:2], 1):
                trainer = Trainer(branch=branch, name=f'{PREFIX} 임시 트레이너 {index}',
                                  short_intro='임시 화면 확인 자료입니다. 실제 인물이나 자격을 나타내지 않습니다.',
                                  profile_image=image, profile_alt=f'TEST 임시 프로필 {index} 글자가 있는 합성 이미지',
                                  is_public=True, sort_order=index)
                trainer.careers.add(TrainerCareer(category='experience', text='TEST 임시 약력 — 목록 배치 확인용이며 실제 경력이 아닙니다.', sort_order=0))
                trainer.save(); trainers.append(trainer)
            posts = []
            for category, label in [('notice','공지'),('event','이벤트')]:
                post = Post(title=f'{PREFIX} 임시 {label}', category=category, cover_image=images[2],
                            cover_alt='TEST 임시 안내 글자가 있는 합성 이미지',
                            body=f'<h2>TEST 임시 {label}</h2><p><b>화면 확인용</b> <i>임시 자료</i>입니다. 실제 행사나 영업 안내가 아닙니다.</p>'
                                 '<p><a href="/branches/">지점 안내 보기</a></p>'
                                 f'<embed embedtype="image" id="{images[2].pk}" format="fullwidth" alt="TEST 임시 안내 이미지"/>')
                post.save()
                revision = post.save_revision()
                post.publish(revision)  # normal revision/publication/derived reference actions, no skip flag
                posts.append(post)
            start = timezone.now()
            popup = Popup(post=posts[0], title=f'{PREFIX} 임시 팝업',
                          message='TEST 화면 확인용 임시 안내입니다. 실제 행사나 영업 안내가 아닙니다.',
                          image=images[2], image_alt='TEST 임시 안내 합성 이미지', enabled=True,
                          starts_at=start, ends_at=start+timedelta(days=7), priority=0)
            popup.save()
            result = {'unit':'DEV-07-B', 'run_id':run_id, 'created_at':start.isoformat(), 'branch_id':branch.pk,
                      'trainers':[{'id':t.pk,'name':t.name,'career_ids':list(t.careers.values_list('pk',flat=True))} for t in trainers],
                      'posts':[{'id':p.pk,'title':p.title,'category':p.category,'live_revision_id':p.live_revision_id} for p in posts],
                      'popup':{'id':popup.pk,'post_id':popup.post_id,'starts_at':start.isoformat(),'ends_at':popup.ends_at.isoformat()},
                      'images':[{'id':image.pk,'title':image.title,**{k:v for k,v in record.items() if k!='inode'}} for image,record in zip(images,files)]}
            payload = json.dumps(result, ensure_ascii=False, indent=2).encode()
            while payload:
                written = os.write(fd, payload)
                if written <= 0: raise OSError('Receipt write failed')
                payload = payload[written:]
            os.fsync(fd)
        except Exception:
            # No recursive cleanup and no existing file/row deletion. The DB rolls back.
            complete = True
            for record in files:
                path = Path(storage.path(record['file']))
                try:
                    if path.is_symlink() or path.stat().st_ino != record['inode'] or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
                        complete = False
                    else: path.unlink()
                except OSError: complete = False
            if complete and not receipt.is_symlink() and receipt.stat().st_ino == receipt_inode:
                receipt.unlink()
            raise
        finally:
            os.close(fd)
    return result
