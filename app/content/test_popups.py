from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone as dt_timezone
from threading import Event
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection, transaction, IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from wagtail.images import get_image_model
from wagtail.models import Collection
from .models import Popup, Post, SiteContent
from .popup_publication import popups_snapshot
from .locking import content_transaction
from .test_posts import PostFixture
from .tests import ConcurrencyMixin, png

NOW=datetime(2026,10,5,15,0,tzinfo=dt_timezone.utc)  # Korean midnight


class PopupFixture(PostFixture):
    def setUp(self):
        super().setUp()
        self.article=self.create_post(title='TEST PUBLIC',cover_image='',body='<p>TEST text</p>')

    def popup_data(self,obj=None,**changes):
        data={'post':self.article.pk,'title':'TEST POPUP','message':'TEST message','image':'','image_alt':'','enabled':'on','starts_at':(NOW-timedelta(hours=1)).isoformat(),'ends_at':(NOW+timedelta(hours=1)).isoformat(),'priority':0,'edit_version':0}
        if obj:
            data={name:getattr(obj,name) for name in ['title','message','image_alt','priority','edit_version']}
            data.update(post=obj.post_id,image=obj.image_id or '',starts_at=obj.starts_at.isoformat() if obj.starts_at else '',ends_at=obj.ends_at.isoformat() if obj.ends_at else '')
            if obj.enabled:data['enabled']='on'
        data.update(changes)
        return data

    def create_popup(self,**changes):
        response=self.post(self.admin_url(Popup,'add'),self.popup_data(**changes))
        self.assertEqual(response.status_code,302,str(getattr(response,'context_data',{}).get('form',''))[:2400])
        return Popup.objects.latest('pk')

    def candidates(self,now=NOW,client=None):
        with patch('content.popup_publication.timezone.now',return_value=now):
            return (client or self.anon).get('/api/v1/popups/active/')


class PopupCmsTests(PopupFixture,TestCase):
    def test_operator_current_value_save_and_post_independence(self):
        self.assertEqual(connection.vendor,'postgresql')
        before=Post.objects.values().get(pk=self.article.pk)
        popup=self.create_popup(image=self.image.pk,image_alt='TEST red')
        self.assertEqual(self.candidates().json()['items'][0]['title'],'TEST POPUP')
        response=self.client.get(self.admin_url(Popup,'edit',popup));self.assertEqual(response.status_code,200)
        self.assertContains(response,'현재 설정에 즉시 반영');self.assertNotContains(response,'action-publish')
        response=self.post(self.admin_url(Popup,'edit',popup),self.popup_data(popup,title='TEST CHANGED',message='<script>literal</script>',enabled=''))
        self.assertEqual(response.status_code,302);popup.refresh_from_db()
        self.assertEqual(popup.title,'TEST CHANGED');self.assertEqual(self.candidates().json()['items'],[])
        self.assertEqual(Post.objects.values().get(pk=self.article.pk),before)
        self.assertFalse(hasattr(popup,'save_revision'))

    def test_disabled_draft_requires_post_and_enabled_fields(self):
        popup=self.create_popup(enabled='',title='',message='',starts_at='',ends_at='')
        self.assertFalse(popup.enabled)
        for changes in [ {'post':''}, {'post':999999}, {'enabled':'on'}, {'title':'x'*201}, {'message':'x'*1001}, {'image_alt':'x'*201}, {'priority':-1}, {'starts_at':NOW.isoformat(),'ends_at':NOW.isoformat()} ]:
            response=self.post(self.admin_url(Popup,'edit',popup),self.popup_data(popup,**changes))
            self.assertEqual(response.status_code,200,changes)
            popup.refresh_from_db();self.assertFalse(popup.enabled);self.assertEqual(popup.title,'')
        self.assertEqual(self.post(self.admin_url(Popup,'edit',popup),self.popup_data(popup,enabled='on',title='TEST image only',image=self.image.pk,starts_at=NOW.isoformat(),ends_at=(NOW+timedelta(hours=1)).isoformat())).status_code,302)
        popup.refresh_from_db();self.assertTrue(popup.enabled)

    def test_unique_post_relation_and_database_constraints_protect(self):
        popup=self.create_popup()
        response=self.post(self.admin_url(Popup,'add'),self.popup_data())
        self.assertEqual(response.status_code,200);self.assertContains(response,'팝업 설정이 이미 있습니다')
        self.assertEqual(Popup.objects.count(),1)
        with self.assertRaises(ProtectedError):self.article.delete()
        for changes in [{'ends_at':popup.starts_at},{'priority':-1},{'title':''}]:
            with self.assertRaises(IntegrityError),transaction.atomic():Popup.objects.filter(pk=popup.pk).update(**changes)
        with self.assertRaises(IntegrityError),transaction.atomic():
            Popup.objects.bulk_create([Popup(post=self.article)])

    def test_stale_and_admin_save_failure_roll_back(self):
        popup=self.create_popup();data=self.popup_data(popup,title='TEST STALE')
        popup.title='TEST NEW';popup.save()
        response=self.post(self.admin_url(Popup,'edit',popup),data)
        self.assertEqual(response.status_code,200);self.assertContains(response,'다른 저장이 먼저')
        old=Popup.objects.values().get(pk=popup.pk);original=Popup.save
        def fail_after_save(obj,*args,**kwargs):
            original(obj,*args,**kwargs);raise ValidationError('TEST rollback after row write')
        with patch.object(Popup,'save',fail_after_save):
            response=self.post(self.admin_url(Popup,'edit',popup),self.popup_data(popup,title='TEST ROLLBACK'))
        self.assertEqual(response.status_code,200);self.assertEqual(Popup.objects.values().get(pk=popup.pk),old)

    def test_collection_file_and_destructive_paths_rejected(self):
        popup=self.create_popup()
        collection=Collection.get_first_root_node().add_child(name='TEST other collection')
        hidden=get_image_model().objects.create(title='TEST hidden',collection=collection,file=png('hidden.png'))
        response=self.post(self.admin_url(Popup,'edit',popup),self.popup_data(popup,image=hidden.pk))
        self.assertEqual(response.status_code,200);popup.refresh_from_db();self.assertIsNone(popup.image_id)
        with patch.object(self.image.file.storage,'exists',return_value=False):
            response=self.post(self.admin_url(Popup,'edit',popup),self.popup_data(popup,image=self.image.pk))
            self.assertEqual(response.status_code,200)
        self.assertEqual(self.client.post(self.admin_url(Popup,'edit',popup),self.popup_data(popup)).status_code,403)
        self.assertIn(self.post(self.admin_url(Popup,'delete',popup),{}).status_code,[302,403])
        self.assertTrue(Popup.objects.filter(pk=popup.pk).exists())
        url=reverse('wagtail_bulk_action',args=['content','popup','delete'])+'?id='+str(popup.pk)
        self.assertEqual(self.post(url,{}).status_code,403)
        self.assertFalse(self.user.has_perm('content.delete_popup'))

    def test_start_end_and_korean_midnight_server_boundaries(self):
        popup=self.create_popup(starts_at=NOW.isoformat(),ends_at=(NOW+timedelta(days=1)).isoformat())
        for time,expected in [(NOW-timedelta(microseconds=1),0),(NOW,1),(NOW+timedelta(days=1,microseconds=-1),1),(NOW+timedelta(days=1),0)]:
            response=self.candidates(time);self.assertEqual(len(response.json()['items']),expected)
            self.assertEqual(response.json()['meta']['server_time'],time.isoformat().replace('+00:00','Z'))
        # Naive administrator input is interpreted as Korean local time.
        response=self.post(self.admin_url(Popup,'edit',popup),self.popup_data(popup,starts_at='2026-10-06 00:00:00',ends_at='2026-10-06 01:00:00'))
        self.assertEqual(response.status_code,302);popup.refresh_from_db();self.assertEqual(popup.starts_at,NOW)

    def test_public_post_title_draft_unpublish_and_republish(self):
        popup=self.create_popup();first=self.candidates().json()['items'][0]
        self.save_draft(self.article,title='TEST PRIVATE TITLE')
        self.assertEqual(self.candidates().json()['items'][0],first)
        self.article.unpublish(user=self.user)
        self.assertEqual(self.candidates().json()['items'],[])
        popup=Popup.objects.get(pk=popup.pk)
        with patch('content.popup_models.timezone.now',return_value=NOW):self.assertEqual(popup.display_status,'연결 글 비공개로 중지')
        self.save_draft(self.article,**{'action-publish':'Publish'})
        self.assertEqual(self.candidates().json()['items'][0]['post']['title'],'TEST PRIVATE TITLE')
        popup.refresh_from_db();self.assertTrue(popup.enabled)

    def test_admin_computed_states_and_list(self):
        popup=self.create_popup(starts_at=NOW.isoformat(),ends_at=(NOW+timedelta(hours=1)).isoformat())
        for time,label in [(NOW-timedelta(seconds=1),'예약'),(NOW,'노출 가능'),(NOW+timedelta(hours=1),'종료')]:
            with patch('content.popup_models.timezone.now',return_value=time):self.assertEqual(popup.display_status,label)
        popup.enabled=False;popup.save();self.assertEqual(popup.display_status,'비활성')
        self.assertEqual(self.client.get(self.admin_url(Popup,'list')).status_code,200)

    def test_candidate_order_exact_contract_and_errors(self):
        a=self.create_popup(priority=2)
        b=self.create_popup(post=self.create_post().pk,priority=1,starts_at=(NOW-timedelta(minutes=30)).isoformat())
        c=self.create_popup(post=self.create_post().pk,priority=1,starts_at=(NOW-timedelta(minutes=15)).isoformat())
        d=self.create_popup(post=self.create_post().pk,priority=1,starts_at=c.starts_at.isoformat())
        response=self.candidates();payload=response.json();self.assertEqual([x['id'] for x in payload['items']],list(map(str,[c.pk,d.pk,b.pk,a.pk])))
        self.assertEqual(set(payload),{'items','meta'});self.assertIn('no-store',response['Cache-Control'])
        item=payload['items'][0];self.assertEqual(set(item),{'id','title','message','image','starts_at','ends_at','post'});self.assertIsNone(item['image'])
        self.assertEqual(set(item['post']),{'id','title','detail_path'})
        self.assertEqual(self.candidates(client=self.client).json(),payload)
        self.assertEqual(self.anon.get('/api/v1/popups/active/?foo=bar').json()['error']['code'],'INVALID_QUERY')
        self.assertEqual(self.anon.post('/api/v1/popups/active/').status_code,405)
        self.assertEqual(self.anon.head('/api/v1/popups/active/').content,b'')
        with patch('content.popup_views.popups_snapshot',side_effect=RuntimeError('TEST actual failure')):
            error=Client(raise_request_exception=False).get('/api/v1/popups/active/')
            self.assertEqual(error.status_code,500);self.assertEqual(error.json()['error']['code'],'SERVER_ERROR')
        with patch('content.popup_publication.timezone.now',return_value=NOW) as clock:
            popups_snapshot();self.assertEqual(clock.call_count,1)

    def test_popup_image_condition_shared_last_reference_and_private_storage(self):
        popup=self.create_popup(image=self.image.pk,starts_at=NOW.isoformat(),ends_at=(NOW+timedelta(hours=1)).isoformat())
        for time,status in [(NOW-timedelta(microseconds=1),404),(NOW,200),(NOW+timedelta(hours=1),404)]:
            with patch('content.publication.timezone.now',return_value=time):self.file_status(f'/images/display/{self.image.pk}/',status)
        with patch('content.publication.timezone.now',return_value=NOW):
            self.file_status(self.image.file.url,403);self.file_status(self.image.file.url,200,self.client)
            self.article.unpublish(user=self.user);self.file_status(f'/images/display/{self.image.pk}/',404)
            self.save_draft(self.article,**{'action-publish':'Publish'})
            self.file_status(f'/images/display/{self.image.pk}/',200)
            branch=self.branch(is_public=True,cover_image=self.image)
            popup.enabled=False;popup.save();self.file_status(f'/images/display/{self.image.pk}/',200)
            branch.cover_image=None;branch.save();self.file_status(f'/images/display/{self.image.pk}/',404)
        self.assertTrue(self.image.file.storage.exists(self.image.file.name))

    def test_permissions_extension_is_additive_without_account_save(self):
        group=Group.objects.get(name='홈페이지 운영자');wanted={'add_popup','change_popup','view_popup'}
        group.permissions.remove(*group.permissions.filter(codename__in=wanted));before=set(group.permissions.values_list('codename',flat=True))
        with patch.object(get_user_model(),'save',side_effect=AssertionError('account touched')):
            call_command('extend_popup_permissions',verbosity=0);call_command('extend_popup_permissions',verbosity=0)
        self.assertEqual(set(group.permissions.values_list('codename',flat=True))-before,wanted)

    def test_only_ready_home_includes_notice_script(self):
        self.assertNotContains(self.anon.get('/'),'popups.js',status_code=503)
        SiteContent(brand_name='TEST SITE').save()
        response=self.anon.get('/');self.assertContains(response,'popups.js');self.assertContains(response,'data-home-popup hidden')
        for path in ['/branches/','/trainers/','/posts/',self.article.get_absolute_url()]:
            self.assertNotContains(self.anon.get(path),'popups.js')


class PopupConcurrencyTests(ConcurrencyMixin,PopupFixture,TransactionTestCase):
    def test_two_stale_popup_saves_one_rejected(self):
        popup=self.create_popup();a=Popup.objects.get(pk=popup.pk);b=Popup.objects.get(pk=popup.pk)
        def write(obj,title):obj.title=title;obj.save()
        self.assertEqual(sorted(self.parallel([lambda:write(a,'TEST A'),lambda:write(b,'TEST B')])),['ok','rejected'])

    def test_popup_save_and_post_unpublish_serialize_without_changing_each_other(self):
        popup=self.create_popup()
        def write():
            obj=Popup.objects.get(pk=popup.pk);obj.message='TEST UPDATED';obj.save()
        self.assertEqual(self.parallel([write,lambda:Post.objects.get(pk=self.article.pk).unpublish(user=self.user)]),['ok','ok'])
        popup.refresh_from_db();self.assertTrue(popup.enabled);self.assertEqual(popup.message,'TEST UPDATED')
        self.assertEqual(self.candidates().json()['items'],[])

    def test_reader_waits_for_complete_popup_and_post_publication(self):
        popup=self.create_popup();self.save_draft(self.article,title='TEST NEW POST')
        inside=Event();release=Event();started=Event();done=Event();result={}
        def write():
            with content_transaction():
                obj=Popup.objects.get(pk=popup.pk);obj.title='TEST NEW POPUP';obj.image=self.image;obj.save()
                post=Post.objects.get(pk=self.article.pk);post.publish(post.latest_revision,user=self.user)
                inside.set();self.assertTrue(release.wait(10))
        def read():started.set();result.update(popups_snapshot());done.set()
        with patch('content.popup_publication.timezone.now',return_value=NOW),ThreadPoolExecutor(max_workers=2) as pool:
            writer=pool.submit(self.worker,write);self.assertTrue(inside.wait(10))
            reader=pool.submit(self.worker,read);self.assertTrue(started.wait(10))
            try:self.assertFalse(done.wait(.3))
            finally:release.set()
            self.assertEqual(writer.result(10)[0],'ok');self.assertEqual(reader.result(10)[0],'ok')
        self.assertEqual(result['items'][0]['title'],'TEST NEW POPUP');self.assertEqual(result['items'][0]['post']['title'],'TEST NEW POST')
        self.assertIn(f'/images/display/{self.image.pk}/',result['items'][0]['image']['url'])

    def test_unpublish_and_popup_update_wait_for_reader(self):
        popup=self.create_popup();inside=Event();release=Event();started=Event();done=Event();result={}
        from .popup_publication import popup_dto
        def pause(obj):inside.set();self.assertTrue(release.wait(10));return popup_dto(obj)
        def read():result.update(popups_snapshot())
        def write():
            started.set()
            with content_transaction():
                obj=Popup.objects.get(pk=popup.pk);obj.enabled=False;obj.save()
                Post.objects.get(pk=self.article.pk).unpublish(user=self.user)
            done.set()
        with patch('content.popup_publication.timezone.now',return_value=NOW),patch('content.popup_publication.popup_dto',side_effect=pause),ThreadPoolExecutor(max_workers=2) as pool:
            reader=pool.submit(self.worker,read);self.assertTrue(inside.wait(10))
            writer=pool.submit(self.worker,write);self.assertTrue(started.wait(10))
            try:self.assertFalse(done.wait(.3))
            finally:release.set()
            self.assertEqual(reader.result(10)[0],'ok');self.assertEqual(writer.result(10)[0],'ok')
        self.assertEqual(len(result['items']),1);self.assertEqual(self.candidates().json()['items'],[])
