"""Separate test DB/media; command itself always rejects test settings."""
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import timedelta
import hashlib
import json
import tempfile
import subprocess
import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.management import call_command, CommandError
from django.db import connection, close_old_connections
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from wagtail.images import get_image_model
from wagtail.models import Collection, Revision, ReferenceIndex
from django.contrib.contenttypes.models import ContentType
from .models import SiteContent, Branch, BranchPhoto, Trainer, TrainerCareer, Post, PostImageUse, Popup
from .preview_content import _populate_preview_content, validate_environment, CONFIRMATION, PREFIX, APP_ROOT
from .tests import png
from .publication import public_snapshot, public_images
from .post_publication import post_snapshot
from .popup_publication import popups_snapshot


class EnvironmentTests(SimpleTestCase):
    def test_command_rejects_missing_confirmation_and_test_or_production_settings(self):
        for module in ['config.settings.test','config.settings.production','config.settings.rehearsal']:
            with override_settings(SETTINGS_MODULE=module), patch('content.preview_content.connection') as db:
                with self.assertRaises(CommandError):
                    call_command('add_local_preview_content',confirm_test_content=CONFIRMATION,server_pid=1,stdout=StringIO())
                db.ensure_connection.assert_not_called()
        with self.assertRaises(CommandError): validate_environment('wrong',1)

    def test_each_wrong_declared_boundary_is_rejected_before_database_connection(self):
        runtime=APP_ROOT/'.runtime'
        good={'ENGINE':'django.db.backends.postgresql','NAME':'y3gym_dev','USER':'y3gym_dev','HOST':str(runtime/'pg-socket'),'PORT':'55432','PASSWORD':'','OPTIONS':{}}
        base={'SETTINGS_MODULE':'config.settings.local','BASE_DIR':APP_ROOT,'RUNTIME':runtime,'MEDIA_ROOT':runtime/'private-media',
              'PUBLIC_ORIGIN':'http://127.0.0.1:8766','ALLOWED_HOSTS':['127.0.0.1','localhost']}
        for key,value in [('ENGINE','sqlite3'),('NAME','y3gym_test'),('NAME','production'),('USER','postgres'),('HOST','127.0.0.1'),('PORT','5432'),('PASSWORD','TEST'),('OPTIONS',{'service':'TEST'})]:
            db=MagicMock();db.settings_dict={**good,key:value}
            with override_settings(**base),patch('content.preview_content.connection',db),patch('pathlib.Path.cwd',return_value=APP_ROOT):
                with self.assertRaises(CommandError):validate_environment(CONFIRMATION,1)
            db.ensure_connection.assert_not_called()
        for key,value in [('PUBLIC_ORIGIN','https://gym.invalid'),('ALLOWED_HOSTS',['*']),('MEDIA_ROOT',runtime/'other'),('BASE_DIR',Path('/tmp/other')),('RUNTIME',Path('/tmp/other'))]:
            db=MagicMock();db.settings_dict=good
            with override_settings(**{**base,key:value}),patch('content.preview_content.connection',db),patch('pathlib.Path.cwd',return_value=APP_ROOT):
                with self.assertRaises(CommandError):validate_environment(CONFIRMATION,1)
            db.ensure_connection.assert_not_called()


class PreviewFixture:
    def setUp(self):
        super().setUp()
        self.media=Path(tempfile.mkdtemp(prefix='preview-content-test-',dir=settings.RUNTIME))
        override=override_settings(MEDIA_ROOT=self.media);override.enable();self.addCleanup(override.disable)
        self.receipt=self.media/'receipt.json'
        root=Collection.get_first_root_node() or Collection.add_root(name='Root')
        self.collection=root.add_child(name='홈페이지 사진')
        self.image=get_image_model().objects.create(title='Existing TEST',collection=self.collection,file=png('existing.png'))
        SiteContent(brand_name='Existing TEST Site').save()
        self.branch=Branch(name='Existing TEST Branch',address='Existing TEST address',phone='000-0000-0000',is_public=True)
        self.branch.save()
        BranchPhoto.objects.create(branch=self.branch,image=self.image,alt='Existing TEST photo')
        # Synthetic test account; no login or password/session fixture needed.
        get_user_model().objects.create_user(username='existing-test-editor',is_staff=True,password=None)

    def files(self):
        return {str(p.relative_to(self.media)):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.media.rglob('*') if p.is_file()}

    def old_rows(self):
        return {m.__name__:list(m.objects.order_by('pk').values()) for m in [SiteContent,Branch,BranchPhoto]}

    def assert_empty(self):
        for model in [Trainer,TrainerCareer,Post,PostImageUse,Popup]:self.assertEqual(model.objects.count(),0)
        self.assertEqual(Revision.objects.filter(content_type__app_label='content',content_type__model='post').count(),0)
        self.assertEqual(get_image_model().objects.count(),1)


class PreviewContentTests(PreviewFixture,TestCase):
    def test_create_preserves_existing_and_uses_standard_publication_and_private_originals(self):
        before=self.old_rows();files=self.files();users=list(get_user_model().objects.values('pk','username','is_active','is_staff','is_superuser'))
        result=_populate_preview_content(self.receipt)
        self.assertEqual(connection.vendor,'postgresql')
        self.assertEqual(self.old_rows(),before)
        self.assertTrue(all(self.files()[key]==value for key,value in files.items()))
        self.assertEqual(list(get_user_model().objects.values('pk','username','is_active','is_staff','is_superuser')),users)
        self.assertEqual(Session.objects.count(),0)
        self.assertEqual([Trainer.objects.count(),TrainerCareer.objects.count(),Post.objects.count(),Popup.objects.count()],[2,2,2,1])
        self.assertEqual(json.loads(self.receipt.read_text()),result)
        self.assertEqual(self.receipt.stat().st_mode & 0o777,0o600)
        self.assertEqual(get_image_model().objects.count(),4)
        for trainer in Trainer.objects.all():
            self.assertTrue(trainer.is_public);self.assertEqual(trainer.branch_id,self.branch.pk)
            self.assertIn('TEST',trainer.name);self.assertIn('실제 경력이 아닙니다',trainer.careers.get().text)
        for post in Post.objects.all():
            self.assertTrue(post.live);self.assertEqual(post.live_revision_id,post.latest_revision_id)
            self.assertEqual(post.revisions.count(),1);self.assertEqual(post.public_image_uses.count(),1)
            self.assertEqual(post.public_image_uses.get().revision_id,post.live_revision_id)
            self.assertIsNone(post.live_revision.user_id)
            self.assertIn('TEST',post_snapshot(post.pk)['body_html'])
            self.assertEqual(self.client.get(post.get_absolute_url()).status_code,200)
        for image in get_image_model().objects.exclude(pk=self.image.pk):
            self.assertTrue(public_images().filter(pk=image.pk).exists())
            self.assertEqual(self.client.get(image.file.url).status_code,403)
            response=self.client.get(f'/images/display/{image.pk}/')
            self.assertEqual(response.status_code,200);b''.join(response.streaming_content)
        self.assertEqual(len(public_snapshot()['trainer_sections'][0]['trainers']),2)

    def test_second_execution_and_existing_receipt_are_unchanged(self):
        _populate_preview_content(self.receipt)
        before=self.files();counts=[m.objects.count() for m in [Trainer,Post,Popup,Revision,get_image_model()]]
        with self.assertRaises(CommandError):_populate_preview_content(self.receipt)
        self.assertEqual(self.files(),before)
        self.assertEqual([m.objects.count() for m in [Trainer,Post,Popup,Revision,get_image_model()]],counts)

    def test_preexisting_content_or_asset_name_collision_aborts_before_any_new_file(self):
        cases=[Trainer(branch=self.branch,name='USER existing'),Post(title='USER existing')]
        for obj in cases:
            obj.save();before=self.files();old=self.old_rows()
            with self.assertRaises(CommandError):_populate_preview_content(self.receipt)
            self.assertEqual(self.files(),before);self.assertEqual(self.old_rows(),old)
            obj.delete()  # only this isolated synthetic fixture
        image=get_image_model().objects.create(title=PREFIX+' collision',collection=self.collection,file=png('collision.png'))
        before=self.files()
        with self.assertRaises(CommandError):_populate_preview_content(self.receipt)
        self.assertEqual(self.files(),before);self.assertFalse(self.receipt.exists())

    def test_popup_failure_rolls_back_revisions_refs_all_rows_and_only_new_files(self):
        before=self.old_rows();files=self.files()
        with patch('content.preview_content.Popup.save',side_effect=RuntimeError('TEST fault after publication')):
            with self.assertRaises(RuntimeError):_populate_preview_content(self.receipt)
        self.assert_empty();self.assertEqual(self.old_rows(),before);self.assertEqual(self.files(),files)

    def test_image_validation_failure_cleans_new_file_and_rolls_back(self):
        before=self.files()
        with patch.object(get_image_model(),'full_clean',side_effect=RuntimeError('TEST validation fault')):
            with self.assertRaises(RuntimeError):_populate_preview_content(self.receipt)
        self.assert_empty();self.assertEqual(self.files(),before)

    def test_popup_seven_day_window_and_reference_expiry(self):
        result=_populate_preview_content(self.receipt);popup=Popup.objects.get()
        self.assertEqual(popup.ends_at-popup.starts_at,timedelta(days=7))
        for instant,count in [(popup.starts_at-timedelta(microseconds=1),0),(popup.starts_at,1),(popup.ends_at,0)]:
            with patch('django.utils.timezone.now',return_value=instant):
                self.assertEqual(len(popups_snapshot()['items']),count)
        # Shared notice image remains public through its published Post after popup expiry.
        with patch('django.utils.timezone.now',return_value=popup.ends_at):
            self.assertTrue(public_images().filter(pk=popup.image_id).exists())


class PreviewConcurrencyTests(PreviewFixture,TransactionTestCase):
    def test_fresh_process_registers_all_snippet_reference_signals_before_writes(self):
        code = '''
import os,sys
from pathlib import Path
os.environ['DJANGO_SETTINGS_MODULE']='config.settings.test'
from django.conf import settings
assert settings.DATABASES['default']['USER']=='y3gym_test'
settings.DATABASES['default']['NAME']='y3gym_test'
settings.MEDIA_ROOT=Path(sys.argv[1])
import django
django.setup()
from content.preview_content import _populate_preview_content
_populate_preview_content(Path(sys.argv[1])/'receipt.json')
'''
        result=subprocess.run([sys.executable,'-c',code,str(self.media)],cwd=APP_ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        for model,field in [(Trainer,'profile_image'),(Post,'cover_image'),(Popup,'image')]:
            ct=ContentType.objects.get_for_model(model)
            for obj in model.objects.all():
                self.assertTrue(ReferenceIndex.objects.filter(base_content_type=ct,object_id=str(obj.pk),content_path=field).exists(),f'{model.__name__} {obj.pk}')

    def test_concurrent_attempt_creates_exactly_one_set(self):
        # Content advisory lock serializes preconditions and writes, even in separate connections.
        def attempt():
            close_old_connections()
            try:
                try:_populate_preview_content(self.receipt);return 'created'
                except CommandError:return 'rejected'
            finally:connection.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:attempt(),range(2)))
        self.assertCountEqual(results,['created','rejected'])
        self.assertEqual([Trainer.objects.count(),Post.objects.count(),Popup.objects.count()],[2,2,1])
