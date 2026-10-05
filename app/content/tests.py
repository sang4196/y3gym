from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from threading import Barrier, Event
from unittest.mock import patch
from pathlib import Path
import tempfile

from bs4 import BeautifulSoup
from PIL import Image as PillowImage
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, connections, close_old_connections
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from wagtail.images import get_image_model
from wagtail.models import Collection
from .models import Branch, BranchPhoto, SiteContent
from .operators import configure_operator
from .publication import public_snapshot, public_images, DISPLAY_FILTER
from .locking import content_transaction


def png(name='test.png', color='red'):
    buf=BytesIO(); PillowImage.new('RGB',(64,48),color).save(buf,'PNG')
    return SimpleUploadedFile(name,buf.getvalue(),content_type='image/png')

class FixtureMixin:
    def setUp(self):
        super().setUp()
        from django.core.cache import cache
        cache.clear()
        self.media=Path(tempfile.mkdtemp(prefix='case-media-',dir=settings.RUNTIME))
        override=override_settings(MEDIA_ROOT=self.media);override.enable();self.addCleanup(override.disable)
        if Collection.get_first_root_node() is None: Collection.add_root(name='Root')
        self.user=get_user_model().objects.create_user(username='editor',is_staff=True)
        self.collection=configure_operator(self.user)
        self.image=get_image_model().objects.create(title='TEST red',file=png(),collection=self.collection)
        self.other_image=get_image_model().objects.create(title='TEST blue',file=png('blue.png','blue'),collection=self.collection)
        self.client=Client(enforce_csrf_checks=True);self.client.force_login(self.user)
        self.client.get(reverse('wagtailimages:add'))
        self.anon=Client()
    def admin_url(self,model,action,obj=None):
        return reverse(model.snippet_viewset.get_url_name(action),args=[obj.pk] if obj else [])
    def post(self,path,data):
        return self.client.post(path,data,HTTP_X_CSRFTOKEN=self.client.cookies['csrftoken'].value)
    def branch(self,**kwargs):
        obj=Branch(name='TEST A',address='TEST ADDRESS',phone='000-0000-0000',**kwargs);obj.save();return obj
    def form_data(self,branch,**changes):
        data={field.name:getattr(branch,field.name) for field in Branch._meta.fields if field.name not in ['id','cover_image']}
        data['cover_image']=branch.cover_image_id or ''
        data.update({'photos-TOTAL_FORMS':'0','photos-INITIAL_FORMS':'0','photos-MIN_NUM_FORMS':'0','photos-MAX_NUM_FORMS':'1000'})
        for name in ['is_main','is_public']:
            if not data[name]: data.pop(name)
        data.update(changes)
        return data
    def file_status(self,url,status,client=None):
        response=(client or self.anon).get(url)
        self.assertEqual(response.status_code,status,url)
        self.assertIn('no-store',response['Cache-Control'])
        if status==200:
            PillowImage.open(BytesIO(b''.join(response.streaming_content))).verify()

class CmsTests(FixtureMixin,TestCase):
    def test_real_postgresql_and_empty_contract(self):
        self.assertEqual(connection.vendor,'postgresql')
        self.assertEqual(self.anon.get('/api/v1/site/').status_code,503)
        payload=self.anon.get('/api/v1/branches/').json()
        self.assertEqual(payload['items'],[])
        self.assertTrue(payload['meta']['server_time'].endswith('Z'))
        self.assertEqual(self.anon.post('/api/v1/branches/').json()['error']['code'],'METHOD_NOT_ALLOWED')
        self.assertEqual(self.anon.get('/api/v1/branches/?anything=x').status_code,400)
        self.assertEqual(self.anon.get('/api/v1/nope/').json()['error']['code'],'NOT_FOUND')
    def test_site_admin_save_singleton_and_immediate_projection(self):
        response=self.post(self.admin_url(SiteContent,'add'),{'brand_name':'TEST SITE','edit_version':0,'hero_image':self.image.pk,'hero_alt':'red test'})
        self.assertEqual(response.status_code,302, response.content[:2000])
        obj=SiteContent.objects.get()
        self.assertEqual(self.anon.get('/api/v1/site/').json()['data']['brand_name'],'TEST SITE')
        self.assertContains(self.anon.get('/'),'TEST SITE')
        self.assertFalse(SiteContent.snippet_viewset.permission_policy.user_has_permission(self.user,'add'))
        response=self.post(self.admin_url(SiteContent,'edit',obj),{'brand_name':'TEST UPDATED','edit_version':obj.edit_version})
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.anon.get('/api/v1/site/').json()['data']['hero_image'],None)
        self.assertContains(self.anon.get('/'),'TEST UPDATED')
    def test_admin_main_switch_and_hide_with_replacement(self):
        a=self.branch(is_public=True);b=self.branch(is_public=True)
        response=self.post(self.admin_url(Branch,'edit',b),self.form_data(b,is_main='on'))
        self.assertEqual(response.status_code,302, response.content[:1000])
        a.refresh_from_db();b.refresh_from_db();self.assertFalse(a.is_main);self.assertTrue(b.is_main)
        data=self.form_data(b,replacement_main=a.pk);data.pop('is_public')
        response=self.post(self.admin_url(Branch,'edit',b),data)
        self.assertEqual(response.status_code,302, response.content[:1000])
        a.refresh_from_db();b.refresh_from_db();self.assertTrue(a.is_main);self.assertFalse(b.is_public);self.assertFalse(b.is_main)
        data=self.form_data(a);data.pop('is_public')
        response=self.post(self.admin_url(Branch,'edit',a),data)
        self.assertEqual(response.status_code,200)
        a.refresh_from_db();self.assertTrue(a.is_public)
    def test_cms_create_first_public_branch_and_stale_submit(self):
        response=self.post(self.admin_url(Branch,'add'),{'name':'TEST first','address':'TEST address','phone':'000-0000-0000','is_public':'on','sort_order':0,'edit_version':0,'photos-TOTAL_FORMS':0,'photos-INITIAL_FORMS':0,'photos-MIN_NUM_FORMS':0,'photos-MAX_NUM_FORMS':1000})
        self.assertEqual(response.status_code,302,response.content[:1000])
        obj=Branch.objects.get();self.assertTrue(obj.is_main)
        stale=self.form_data(obj,summary='stale')
        obj.summary='fresh';obj.save()
        response=self.post(self.admin_url(Branch,'edit',obj),stale)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'다른 저장이 먼저 반영되었습니다.')
        obj.refresh_from_db();self.assertEqual(obj.summary,'fresh')

    def test_parent_children_rollback_and_foreign_inline_ids(self):
        a=self.branch(is_public=True);b=self.branch()
        photo=BranchPhoto.objects.create(branch=b,image=self.image,caption='original')
        data=self.form_data(a,usage_notes='should not save',**{'photos-TOTAL_FORMS':'1','photos-INITIAL_FORMS':'1','photos-0-id':photo.pk,'photos-0-image':self.other_image.pk,'photos-0-caption':'ATTACK','photos-0-ORDER':'0'})
        response=self.post(self.admin_url(Branch,'edit',a),data)
        self.assertEqual(response.status_code,200)
        a.refresh_from_db();photo.refresh_from_db();self.assertEqual(a.usage_notes,'');self.assertEqual(photo.caption,'original')
        a.usage_notes='must rollback'
        a.photos.add(BranchPhoto(image=self.image,caption='never committed',sort_order=0))
        original=BranchPhoto.save
        def fail_after_child(instance,*args,**kwargs):
            original(instance,*args,**kwargs)
            raise RuntimeError('injected child failure')
        with patch.object(BranchPhoto,'save',fail_after_child):
            with self.assertRaises(RuntimeError):a.save()
        a.refresh_from_db();self.assertEqual(a.usage_notes,'');self.assertEqual(BranchPhoto.objects.filter(branch_id=a.pk).count(),0)
    def test_inline_add_reorder_remove_and_private_read_scope(self):
        a=self.branch(is_public=True);hidden=self.branch()
        data=self.form_data(a,usage_notes='TEST use',**{'photos-TOTAL_FORMS':'2','photos-0-image':self.image.pk,'photos-0-caption':'red','photos-0-alt':'red','photos-0-ORDER':'1','photos-1-image':self.other_image.pk,'photos-1-caption':'blue','photos-1-alt':'blue','photos-1-ORDER':'0'})
        response=self.post(self.admin_url(Branch,'edit',a),data)
        self.assertEqual(response.status_code,302,response.content[:1000])
        anon=self.anon.get('/api/v1/branches/').json()['items'];auth=self.client.get('/api/v1/branches/').json()['items']
        self.assertEqual(anon,auth);self.assertEqual(len(anon),1)
        self.assertEqual(anon[0]['id'],str(a.pk));self.assertIsNone(anon[0]['location']);self.assertIsNone(anon[0]['trainer_section_path'])
        self.assertEqual([p['caption'] for p in anon[0]['facility_photos']],['blue','red'])
        self.assertEqual(anon[0]['phone']['href'],'tel:00000000000')
        self.assertContains(self.anon.get('/branches/'),f'id="branch-{a.pk}"')
        self.assertNotContains(self.anon.get('/branches/'),f'id="branch-{hidden.pk}"')
        self.assertEqual(self.anon.get(f'/branches/{a.pk}/').status_code,404)
        a.refresh_from_db();photos=list(a.photos.all())
        data=self.form_data(a,**{'photos-TOTAL_FORMS':'2','photos-INITIAL_FORMS':'2'})
        for i,photo in enumerate(photos):
            data.update({f'photos-{i}-id':photo.pk,f'photos-{i}-image':photo.image_id,f'photos-{i}-ORDER':i})
        data['photos-0-DELETE']='on'
        self.assertEqual(self.post(self.admin_url(Branch,'edit',a),data).status_code,302)
        self.assertEqual(a.photos.count(),1);self.assertTrue(get_image_model().objects.filter(pk=self.other_image.pk).exists())
    def test_validation_missing_file_and_stale_form(self):
        a=self.branch(is_public=True)
        stale=Branch.objects.get(pk=a.pk)
        a.summary='new';a.save();stale.summary='old'
        with self.assertRaises(ValidationError):stale.save()
        a.refresh_from_db();self.assertEqual(a.summary,'new')
        bad=Branch(is_public=True,name='missing address')
        with self.assertRaises(ValidationError):bad.save()
        bad=Branch(kakao_channel_url='https://evil.example/')
        with self.assertRaises(ValidationError):bad.save()
        # Simulate missing file in test storage only; no user media is removed.
        self.image.file.name='does-not-exist.png';self.image.save(update_fields=['file'])
        a.cover_image=self.image
        with self.assertRaises(ValidationError):a.save()
    def test_shared_site_branch_media_revocation_and_protected_urls(self):
        site=SiteContent(brand_name='TEST',hero_image=self.image);site.save()
        a=self.branch(is_public=True,cover_image=self.image)
        b=self.branch(is_public=True)
        b.photos.add(BranchPhoto(image=self.image));b.save()
        public_snapshot()
        url=f'/images/display/{self.image.pk}/'
        self.file_status(url,200)
        site.hero_image=None;site.save();self.file_status(url,200)
        a.cover_image=None;a.save();self.file_status(url,200)
        b.is_public=False;b.save();self.file_status(url,404)
        self.file_status(url,404,self.client)
        original=self.image.file.url;thumb=self.image.get_rendition('max-165x165').url
        internal=self.image.get_rendition(DISPLAY_FILTER).url
        for path in [original,thumb,internal]:
            self.file_status(path,403);self.file_status(path,200,self.client)
        outsider=get_user_model().objects.create_user(username='outsider',is_staff=True)
        from django.contrib.auth.models import Permission
        outsider.user_permissions.add(Permission.objects.get(codename='access_admin'))
        client=Client();client.force_login(outsider);self.file_status(original,403,client)
        for path in ['/media/'+self.image.file.name,'/.runtime/private-media/'+self.image.file.name,'/images/signature/1/original/a.png']:
            self.assertEqual(self.anon.get(path).status_code,404)
    def test_overwrite_delete_and_permission_injection_blocked(self):
        before=self.image.file.read();self.image.file.close()
        url=reverse('wagtailimages:edit',args=[self.image.pk])
        response=self.client.get(url)
        self.assertTrue(response.context['form'].fields['file'].disabled)
        response=self.post(url,{'title':'TEST','collection':self.collection.pk,'file':png('new.png','blue')})
        self.assertEqual(response.status_code,200);self.assertTrue(response.context['form'].errors)
        self.image.refresh_from_db();self.image.file.open('rb');self.assertEqual(self.image.file.read(),before);self.image.file.close()
        a=self.branch(is_public=True)
        for endpoint in ['delete','delete_multiple','delete_upload_multiple']:
            path=reverse('wagtailimages:'+endpoint,args=[self.image.pk])
            self.assertEqual(self.client.get(path).status_code,403)
            self.assertEqual(self.post(path,{}).status_code,403)
        bulk=reverse('wagtail_bulk_action',args=['wagtailimages','image','delete'])
        self.assertEqual(self.post(bulk+f'?id={self.image.pk}',{}).status_code,403)
        self.assertNotContains(self.client.get(reverse('wagtailimages:index')),'/bulk/wagtailimages/image/delete/')
        self.assertNotContains(self.client.get(url),f'/images/{self.image.pk}/delete/')
        self.assertIn(self.post(self.admin_url(Branch,'delete',a),{}).status_code,[302,403])
        self.assertTrue(Branch.objects.filter(pk=a.pk).exists())
        root=Collection.get_first_root_node();secret=root.add_child(name='not allowed')
        image=get_image_model().objects.create(title='PRIVATE',file=png('private.png'),collection=secret)
        response=self.post(self.admin_url(Branch,'edit',a),self.form_data(a,cover_image=image.pk))
        self.assertEqual(response.status_code,200);a.refresh_from_db();self.assertIsNone(a.cover_image_id)
        self.assertEqual(self.client.post(self.admin_url(Branch,'edit',a),self.form_data(a)).status_code,403)

class ConcurrencyMixin:
    def worker(self, action):
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_backend_pid()');pid=cursor.fetchone()[0]
            try: action();return ('ok',pid)
            except ValidationError:return ('rejected',pid)
        finally:connections.close_all()
    def parallel(self, actions):
        barrier=Barrier(len(actions))
        def wrap(action):
            return self.worker(lambda:(barrier.wait(timeout=10),action()))
        with ThreadPoolExecutor(max_workers=len(actions)) as pool:
            results=list(pool.map(wrap,actions))
        self.assertEqual(len({r[1] for r in results}),len(actions))
        return [r[0] for r in results]

class ConcurrencyTests(ConcurrencyMixin,FixtureMixin,TransactionTestCase):
    def test_concurrent_first_publication(self):
        a=self.branch();b=self.branch()
        def publish(pk):
            obj=Branch.objects.get(pk=pk);obj.is_public=True;obj.save()
        statuses=self.parallel([lambda:publish(a.pk),lambda:publish(b.pk)])
        self.assertEqual(statuses,['ok','ok'])
        self.assertEqual(Branch.objects.filter(is_public=True).count(),2)
        self.assertEqual(Branch.objects.filter(is_main=True).count(),1)
    def test_concurrent_main_switch_and_hide(self):
        a=self.branch(is_public=True);b=self.branch(is_public=True);c=self.branch(is_public=True)
        def main(pk):
            obj=Branch.objects.get(pk=pk);obj.is_main=True;obj.save()
        statuses=self.parallel([lambda:main(b.pk),lambda:main(c.pk)])
        self.assertIn('ok',statuses)
        self.assertEqual(Branch.objects.filter(is_main=True).count(),1)
        current=Branch.objects.get(is_main=True)
        target=Branch.objects.filter(is_public=True).exclude(pk=current.pk).first()
        def hide():
            obj=Branch.objects.get(pk=current.pk);obj.is_public=False;obj._replacement_main_id=target.pk;obj.save()
        statuses=self.parallel([hide,lambda:main(target.pk)])
        self.assertIn('ok',statuses)
        self.assertEqual(Branch.objects.filter(is_main=True).count(),1)
        self.assertFalse(Branch.objects.filter(is_main=True,is_public=False).exists())
    def test_concurrent_last_branch_hide(self):
        a=self.branch(is_public=True);b=self.branch(is_public=True)
        def hide(pk,replacement):
            obj=Branch.objects.get(pk=pk);obj.is_public=False;obj._replacement_main_id=replacement;obj.save()
        result=self.parallel([lambda:hide(a.pk,b.pk),lambda:hide(b.pk,a.pk)])
        self.assertEqual(sorted(result),['ok','rejected'])
        self.assertEqual(Branch.objects.filter(is_public=True,is_main=True).count(),1)
    def test_public_read_waits_for_complete_parent_children_commit(self):
        a=self.branch(is_public=True);a.photos.add(BranchPhoto(image=self.image,caption='old'));a.save()
        writer_inside=Event();release=Event();reader_started=Event();reader_done=Event();result={}
        def write():
            with content_transaction():
                obj=Branch.objects.get(pk=a.pk);obj.usage_notes='new'
                obj.photos.set([BranchPhoto(image=self.other_image,caption='new',sort_order=0)]);obj.save()
                writer_inside.set();self.assertTrue(release.wait(timeout=10))
        def read():
            reader_started.set();result.update(public_snapshot());reader_done.set()
        with ThreadPoolExecutor(max_workers=2) as pool:
            writer=pool.submit(self.worker,write);self.assertTrue(writer_inside.wait(timeout=10))
            reader=pool.submit(self.worker,read);self.assertTrue(reader_started.wait(timeout=10))
            try:self.assertFalse(reader_done.wait(timeout=.3))
            finally:release.set()
            self.assertEqual(writer.result(timeout=10)[0],'ok');self.assertEqual(reader.result(timeout=10)[0],'ok')
        self.assertEqual(result['branches'][0]['usage_notes'],'new')
        self.assertEqual(result['branches'][0]['facility_photos'][0]['caption'],'new')

    def test_writer_waits_until_reader_materializes_old_snapshot(self):
        a=self.branch(is_public=True);a.photos.add(BranchPhoto(image=self.image,caption='old'));a.save()
        reader_inside=Event();release=Event();writer_started=Event();writer_done=Event();result={}
        from .publication import branch_dto
        def paused_dto(branch):
            reader_inside.set()
            self.assertTrue(release.wait(timeout=10))
            return branch_dto(branch)
        def read():
            result.update(public_snapshot())
        def write():
            writer_started.set()
            obj=Branch.objects.get(pk=a.pk);obj.usage_notes='new'
            obj.photos.set([BranchPhoto(image=self.other_image,caption='new',sort_order=0)])
            obj.save();writer_done.set()
        with patch('content.publication.branch_dto',paused_dto), ThreadPoolExecutor(max_workers=2) as pool:
            reader=pool.submit(self.worker,read);self.assertTrue(reader_inside.wait(timeout=10))
            writer=pool.submit(self.worker,write);self.assertTrue(writer_started.wait(timeout=10))
            try:self.assertFalse(writer_done.wait(timeout=.3))
            finally:release.set()
            self.assertEqual(reader.result(timeout=10)[0],'ok');self.assertEqual(writer.result(timeout=10)[0],'ok')
        self.assertIsNone(result['branches'][0]['usage_notes'])
        self.assertEqual(result['branches'][0]['facility_photos'][0]['caption'],'old')
        self.assertEqual(public_snapshot()['branches'][0]['facility_photos'][0]['caption'],'new')
