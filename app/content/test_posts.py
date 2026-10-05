"""Dedicated PostgreSQL/CMS HTTP tests. These are not actual browser results."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch
from bs4 import BeautifulSoup
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import connection
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from wagtail.admin.rich_text.converters.contentstate import ContentstateConverter
from wagtail.images import get_image_model
from wagtail.models import Collection
from .models import Post, PostImageUse, SiteContent
from .locking import content_transaction
from .post_body import render_body, safe_link
from .post_publication import post_snapshot, posts_snapshot
from .publication import public_images, public_snapshot
from .tests import FixtureMixin, ConcurrencyMixin, png


class PostFixture(FixtureMixin):
    def body(self, image=None, text='TEST BODY'):
        body = f'<h2>{text}</h2><p><b>Bold</b> <i>Italic</i> <a href="https://example.com/">Test link</a></p>'
        return body + (f'<embed embedtype="image" id="{image.pk}" format="fullwidth" alt="TEST rectangle"/>' if image else '')

    def post_data(self, obj=None, **changes):
        obj = obj.get_latest_revision_as_object() if obj else Post()
        data = {'title':obj.title, 'category':obj.category, 'cover_image':obj.cover_image_id or '', 'cover_alt':obj.cover_alt, 'edit_version':obj.edit_version, 'body':obj.body}
        data.update(changes)
        data['body'] = ContentstateConverter(features=['h2','bold','italic','ol','ul','link','image']).from_database_format(data['body'])
        return data

    def create_post(self, publish=True, **changes):
        data = {'title':'TEST PUBLIC', 'body':self.body(self.other_image), 'cover_image':self.image.pk}
        if publish:
            data['action-publish'] = 'Publish'
        data.update(changes)
        response = self.post(self.admin_url(Post,'add'), self.post_data(**data))
        self.assertEqual(response.status_code,302, str(getattr(response,'context_data',{}).get('form', ''))[:3000])
        return Post.objects.latest('pk')

    def save_draft(self, obj, **changes):
        response = self.post(self.admin_url(Post,'edit',obj), self.post_data(obj, **changes))
        self.assertEqual(response.status_code,302,str(getattr(response,'context_data',{}).get('form',''))[:3000])
        obj.refresh_from_db()
        return obj

    def api(self,obj):
        return self.anon.get(f'/api/v1/posts/{obj.pk}/').json()['data']


class PostCmsTests(PostFixture,TestCase):
    def test_editor_lifecycle_public_revision_and_native_widget(self):
        self.assertEqual(connection.vendor,'postgresql')
        obj=self.create_post(); before=self.api(obj); live=obj.live_revision_id
        response=self.client.get(self.admin_url(Post,'edit',obj))
        self.assertContains(response,'data-product-post-editor')
        self.assertContains(response,'content/composer.js')
        self.assertFalse(response.context_data['autosave_enabled'])
        self.assertNotContains(response,'name="go_live_at"')
        self.save_draft(obj,title='TEST DRAFT',category='event',body=self.body(self.image,'DRAFT BODY'),cover_image=self.other_image.pk)
        self.assertNotEqual(obj.latest_revision_id,live);self.assertEqual(obj.live_revision_id,live)
        response=self.client.get(self.admin_url(Post,'edit',obj))
        self.assertEqual(response.context_data['form'].initial['title'],'TEST DRAFT')
        self.assertEqual(self.api(obj),before)
        self.assertEqual(self.client.get(f'/api/v1/posts/{obj.pk}/').json()['data'],before)
        self.assertContains(self.anon.get(obj.get_absolute_url()),'TEST PUBLIC')
        self.assertNotContains(self.anon.get(obj.get_absolute_url()),'TEST DRAFT')
        first=obj.first_published_at;last=obj.last_published_at
        self.save_draft(obj, **{'action-publish':'Publish'})
        after=self.api(obj)
        self.assertEqual(after['title'],'TEST DRAFT');self.assertEqual(after['category'],'event')
        self.assertEqual(obj.first_published_at,first);self.assertGreater(obj.last_published_at,last)
        self.assertEqual(after['published_at'],before['published_at']);self.assertNotEqual(after['updated_at'],before['updated_at'])
        self.assertEqual(set(after),{'id','category','title','cover_image','published_at','detail_path','body_html','updated_at'})
        self.assertNotIn('<embed',after['body_html']);self.assertNotIn('cms-files',after['body_html'])
        self.assertIn('<b>',after['body_html']);self.assertIn('<i>',after['body_html']);self.assertIn('https://example.com/',after['body_html'])
        self.assertTrue(all(r.revision_id==obj.live_revision_id for r in obj.public_image_uses.all()))

    def test_authenticated_preview_and_new_upload_remains_private(self):
        obj=self.create_post();before=self.api(obj)
        response=self.post(reverse('wagtailimages:add'),{'title':'TEST new asset','file':png('draft.png','green'),'collection':self.collection.pk})
        self.assertEqual(response.status_code,302)
        image=get_image_model().objects.latest('pk')
        self.save_draft(obj,title='TEST PRIVATE DRAFT',cover_image=image.pk,body=self.body(image,'PRIVATE BODY'))
        url=self.admin_url(Post,'preview_on_edit',obj)
        state=self.post(url,self.post_data(obj));self.assertTrue(state.json()['is_valid'])
        response=self.client.get(url);self.assertContains(response,'TEST PRIVATE DRAFT');self.assertContains(response,'PRIVATE BODY')
        for tag in BeautifulSoup(response.content,'html.parser').find_all('img'):
            self.file_status(tag['src'],200,self.client);self.file_status(tag['src'],403)
        self.assertEqual(self.anon.get(url).status_code,302)
        self.file_status(f'/images/display/{image.pk}/',404)
        self.file_status(image.file.url,403);self.file_status(image.file.url,200,self.client)
        self.assertEqual(self.api(obj),before)
        self.assertIn('no-store',response['Cache-Control'])

    def test_restore_is_new_draft_and_requires_separate_publish(self):
        obj=self.create_post();original=obj.live_revision_id
        self.save_draft(obj,title='TEST SECOND',cover_image=self.other_image.pk,**{'action-publish':'Publish'})
        current=self.api(obj);live=obj.live_revision_id
        url=reverse(Post.snippet_viewset.get_url_name('revisions_revert'),args=[obj.pk,original])
        get=self.client.get(url);self.assertEqual(get.status_code,200)
        self.assertEqual(get.context_data['form'].initial['title'],'TEST PUBLIC')
        self.assertNotContains(get,'name="action-publish"')
        old=obj.revisions.get(pk=original).as_object()
        data=self.post_data(obj,title=old.title,body=old.body,cover_image=old.cover_image_id,cover_alt=old.cover_alt,category=old.category)
        self.assertEqual(self.post(url,{**data,'action-publish':'Publish'}).status_code,403)
        self.assertEqual(self.post(url,data).status_code,302)
        obj.refresh_from_db();self.assertEqual(obj.live_revision_id,live);self.assertNotEqual(obj.latest_revision_id,original)
        self.assertEqual(self.api(obj),current)
        with self.assertRaises(ValidationError):obj.publish(obj.revisions.get(pk=original),user=self.user)
        self.save_draft(obj,**{'action-publish':'Publish'})
        self.assertEqual(self.api(obj)['title'],'TEST PUBLIC')
        self.assertIn(f'/images/display/{self.image.pk}/',self.api(obj)['cover_image']['url'])

    def test_missing_file_blocks_restore_and_publish_without_partial_changes(self):
        obj=self.create_post();old=obj.live_revision_id
        self.save_draft(obj,cover_image='',body='<p>TEST text only</p>',**{'action-publish':'Publish'})
        before=self.api(obj);latest=obj.latest_revision_id
        # Simulate loss with a storage probe; retain every real test file.
        storage=self.image.file.storage;exists=storage.exists
        def absent(name):return False if name==self.image.file.name else exists(name)
        url=reverse(Post.snippet_viewset.get_url_name('revisions_revert'),args=[obj.pk,old])
        with patch.object(storage,'exists',side_effect=absent):
            data=self.post_data(obj,cover_image=self.image.pk)
            response=self.post(url,data);self.assertEqual(response.status_code,200)
            response=self.post(self.admin_url(Post,'edit',obj),{**data,'action-publish':'Publish'});self.assertEqual(response.status_code,200)
        obj.refresh_from_db();self.assertEqual(obj.latest_revision_id,latest);self.assertEqual(self.api(obj),before)

    def test_empty_draft_public_required_fields_and_image_only_policy(self):
        obj=self.create_post(publish=False,title='',body='',cover_image='')
        self.assertFalse(obj.live)
        for changes in [{'title':'','body':'<p>text</p>'},{'title':'TEST','body':'<p> </p>','cover_image':self.image.pk}]:
            response=self.post(self.admin_url(Post,'edit',obj),self.post_data(obj,**changes,**{'action-publish':'Publish'}))
            self.assertEqual(response.status_code,200)
            obj.refresh_from_db();self.assertFalse(obj.live)
        body=f'<embed embedtype="image" id="{self.image.pk}" format="fullwidth" alt="TEST"/>'
        self.save_draft(obj,title='TEST image only',body=body,**{'action-publish':'Publish'})
        self.assertTrue(obj.live)
        for changes in [{'title':'x'*201},{'cover_alt':'x'*201},{'category':'other'}]:
            response=self.post(self.admin_url(Post,'edit',obj),self.post_data(obj,**changes));self.assertEqual(response.status_code,200)

    def test_filter_count_sort_pagination_and_home_use_public_revisions(self):
        SiteContent(brand_name='TEST SITE').save()
        a=self.create_post(title='TEST A');b=self.create_post(title='TEST B',category='event');c=self.create_post(title='TEST C');d=self.create_post(publish=False,title='TEST PRIVATE')
        self.save_draft(a,category='event',title='TEST HIDDEN')
        data=self.anon.get('/api/v1/posts/?category=notice&page_size=1').json()
        self.assertEqual(data['pagination'],{'page':1,'page_size':1,'total':2,'has_next':True})
        self.assertEqual(data['items'][0]['id'],str(c.pk))
        self.assertEqual(self.anon.get('/api/v1/posts/?category=notice&page=2&page_size=1').json()['items'][0]['title'],'TEST A')
        self.assertEqual(self.anon.get('/api/v1/posts/?category=event').json()['pagination']['total'],1)
        self.assertEqual(posts_snapshot(page=10**50)['items'],[])
        for query in ['category=','category=other','page=0','page=-1','page=1.0','page=+2','page_size=51','page_size=0','x=y','page=1&page=2','category=notice&category=notice']:
            response=self.anon.get('/api/v1/posts/?'+query);self.assertEqual(response.status_code,400,query);self.assertEqual(response.json()['error']['code'],'INVALID_QUERY')
        self.assertEqual(self.anon.get('/api/v1/posts/?page=999').json()['pagination'],{'page':999,'page_size':10,'total':3,'has_next':False})
        summary=posts_snapshot()['items'][0];self.assertEqual(set(summary),{'id','category','title','cover_image','published_at','detail_path'})
        self.assertIsInstance(summary['id'],str);self.assertTrue(summary['published_at'].endswith('Z'))
        self.assertEqual([p['id'] for p in public_snapshot()['recent_posts']],[str(c.pk),str(b.pk),str(a.pk)])
        self.assertContains(self.anon.get('/'),'TEST A');self.assertNotContains(self.anon.get('/'),'TEST HIDDEN')
        response=self.anon.get('/posts/?category=notice&page=2&page_size=1');self.assertContains(response,'TEST A');self.assertContains(response,'page=1&amp;page_size=1&amp;category=event')
        self.assertEqual(self.anon.get('/posts/?page=bad').status_code,400)
        for client in [self.anon,self.client]:
            self.assertEqual(client.get(f'/api/v1/posts/{d.pk}/').json(),client.get('/api/v1/posts/999999/').json())
            self.assertEqual(client.get(d.get_absolute_url()).status_code,404)
        self.assertEqual(self.anon.get(f'/api/v1/posts/{a.pk}/?x=y').status_code,400)
        self.assertEqual(self.anon.post('/api/v1/posts/').status_code,405)

    def test_shared_image_last_reference_and_normal_unpublish(self):
        a=self.create_post();b=self.create_post();first=a.first_published_at
        for obj in [a,b]:
            url=self.admin_url(Post,'unpublish',obj)
            self.assertContains(self.client.get(url),'name="edit_version"')
            self.assertEqual(self.post(url,{'edit_version':obj.edit_version}).status_code,302)
            obj.refresh_from_db();self.assertFalse(obj.live);self.assertIsNone(obj.live_revision_id);self.assertFalse(obj.public_image_uses.exists())
            self.file_status(f'/images/display/{self.image.pk}/',200 if obj is a else 404)
        self.assertEqual(a.first_published_at,first)
        self.save_draft(a,**{'action-publish':'Publish'});self.assertEqual(a.first_published_at,first)
        branch=self.branch(is_public=True,cover_image=self.image)
        a.unpublish(user=self.user);self.file_status(f'/images/display/{self.image.pk}/',200)
        branch.cover_image=None;branch.save();self.file_status(f'/images/display/{self.image.pk}/',404)
        self.assertTrue(self.image.file.storage.exists(self.image.file.name))

    def test_stale_edit_publish_and_unpublish_are_rejected(self):
        obj=self.create_post();stale=self.post_data(obj,title='TEST STALE');version=obj.edit_version
        self.save_draft(obj,title='TEST FRESH')
        for changes in [{},{'action-publish':'Publish'}]:
            response=self.post(self.admin_url(Post,'edit',obj),{**stale,**changes})
            self.assertEqual(response.status_code,200);self.assertContains(response,'다른 저장이나 공개 변경')
        self.assertEqual(self.post(self.admin_url(Post,'unpublish',obj),{'edit_version':version}).status_code,409)
        obj.refresh_from_db();self.assertTrue(obj.live);self.assertEqual(obj.get_latest_revision_as_object().title,'TEST FRESH')

    def test_index_failure_rolls_back_complete_admin_publication(self):
        obj=self.create_post();before=self.api(obj);latest=obj.latest_revision_id;version=obj.edit_version
        with patch('content.post_models.PostImageUse.objects.bulk_create',side_effect=ValidationError('TEST index failure')):
            response=self.post(self.admin_url(Post,'edit',obj),self.post_data(obj,title='TEST rollback',**{'action-publish':'Publish'}))
        self.assertEqual(response.status_code,200)
        obj.refresh_from_db();self.assertEqual(obj.latest_revision_id,latest);self.assertEqual(obj.edit_version,version)
        self.assertEqual(self.api(obj),before);self.assertEqual(obj.public_image_uses.count(),2)

    def test_allowlist_and_cross_collection_injection(self):
        obj=self.create_post();old=self.api(obj)
        hidden_collection=Collection.get_first_root_node().add_child(name='TEST forbidden')
        hidden=get_image_model().objects.create(title='TEST hidden',file=png('hidden.png'),collection=hidden_collection)
        response=self.post(self.admin_url(Post,'edit',obj),self.post_data(obj,body=self.body(hidden),**{'action-publish':'Publish'}))
        self.assertEqual(response.status_code,200);self.assertEqual(self.api(obj),old)
        with self.assertRaises(PermissionDenied):
            candidate=obj.get_latest_revision_as_object();candidate.cover_image=hidden;candidate.save_revision(user=self.user)
        raw='<script>alert(1)</script><img src="https://evil.test/" onerror="x"><p onclick="x">TEST<a href="javascript:alert(1)">bad</a><a href="//evil.test/">bad2</a><iframe src="x">inner</iframe></p><a href="/posts/1/">safe</a>'
        candidate=Post(body=raw)
        html=render_body(candidate,images={});soup=BeautifulSoup(html,'html.parser')
        self.assertIsNone(soup.find(['script','img','iframe']));self.assertNotIn('onclick',html);self.assertNotIn('javascript:',html)
        self.assertEqual([a['href'] for a in soup.find_all('a')],['/posts/1/'])
        self.assertIsNone(safe_link('https://example.com/\\evil'));self.assertIsNone(safe_link('/admin/'))
        self.assertEqual(safe_link('mailto:test@example.com'),'mailto:test@example.com')
        self.assertEqual(safe_link('tel:0000000000'),'tel:0000000000')
        with self.assertRaises(ValidationError):Post(body='<embed embedtype="image" id="999999999"/>').validate_content(user=self.user)
        with self.assertRaises(ValidationError):Post(body='<embed embedtype="other" id="1"/>').validate_content(user=self.user)
        obj.refresh_from_db();candidate=obj.get_latest_revision_as_object();candidate.body=raw
        revision=candidate.save_revision(user=self.user);candidate.publish(revision,user=self.user)
        public=self.api(obj)['body_html']
        self.assertNotIn('javascript:',public);self.assertNotIn('<img',public);self.assertNotIn('onclick',public)

    def test_role_extension_no_account_save_and_auth_boundaries(self):
        group=Group.objects.get(name='홈페이지 운영자')
        wanted={'add_post','change_post','view_post','publish_post'}
        group.permissions.remove(*group.permissions.filter(codename__in=wanted))
        before=set(group.permissions.values_list('codename',flat=True))
        with patch.object(get_user_model(),'save',side_effect=AssertionError('account changed')):
            call_command('extend_post_permissions',verbosity=0)
            call_command('extend_post_permissions',verbosity=0)
        self.assertEqual(set(group.permissions.values_list('codename',flat=True))-before,wanted)
        obj=self.create_post()
        outsider=get_user_model().objects.create_user(username='outsider',is_staff=True)
        other=Client();other.force_login(outsider)
        self.assertEqual(other.get(self.admin_url(Post,'preview_on_edit',obj)).status_code,302)
        with self.assertRaises(PermissionDenied):obj.unpublish(user=outsider)
        obj.refresh_from_db();self.assertTrue(obj.live)

    def test_same_first_publication_timestamp_uses_id_descending(self):
        a=self.create_post();b=self.create_post()
        # Test-only tie fixture, not a supported operator write path.
        Post.objects.filter(pk=b.pk).update(first_published_at=a.first_published_at)
        self.assertEqual([x['id'] for x in posts_snapshot()['items']],[str(b.pk),str(a.pk)])

    def test_unsupported_paths_permissions_csrf_and_immutable_revisions(self):
        obj=self.create_post();before=self.api(obj)
        self.assertFalse(self.user.is_superuser);self.assertFalse(self.user.has_perm('content.delete_post'))
        self.assertEqual(self.client.post(self.admin_url(Post,'edit',obj),self.post_data(obj)).status_code,403)
        self.assertEqual(self.post(self.admin_url(Post,'delete',obj),{}).status_code,403)
        for action in ['delete','publish','unpublish']:
            url=reverse('wagtail_bulk_action',args=['content','post',action])+'?id='+str(obj.pk)
            self.assertEqual(self.post(url,{}).status_code,403)
        self.assertEqual(self.post(self.admin_url(Post,'edit',obj),self.post_data(obj,overwrite_revision_id=obj.latest_revision_id)).status_code,403)
        with self.assertRaises(PermissionDenied):obj.save_revision(user=self.user,overwrite_revision=obj.latest_revision)
        obj.go_live_at=obj.first_published_at
        with self.assertRaises(ValidationError):obj.save_revision(user=self.user)
        self.assertEqual(self.api(obj),before)
        index=self.client.get(self.admin_url(Post,'list'));self.assertEqual(index.status_code,200)
        self.assertNotContains(index,'data-bulk-action-type="delete"')

    def test_mismatched_index_revision_never_grants_draft_image_access(self):
        obj=self.create_post();self.save_draft(obj,title='TEST DRAFT')
        self.assertNotEqual(obj.latest_revision_id,obj.live_revision_id)
        PostImageUse.objects.filter(post=obj).update(revision=obj.latest_revision)
        self.assertFalse(public_images().filter(pk=self.image.pk).exists())


class PostConcurrencyTests(ConcurrencyMixin,PostFixture,TransactionTestCase):
    def test_two_simultaneous_publications_one_stale(self):
        obj=self.create_post(publish=False)
        a=Post.objects.get(pk=obj.pk);b=Post.objects.get(pk=obj.pk)
        results=self.parallel([lambda:a.publish(a.latest_revision,user=self.user),lambda:b.publish(b.latest_revision,user=self.user)])
        self.assertEqual(sorted(results),['ok','rejected']);obj.refresh_from_db()
        self.assertTrue(obj.live);self.assertEqual(obj.public_image_uses.count(),2)

    def test_concurrent_publish_and_unpublish_one_stale(self):
        obj=self.create_post();self.save_draft(obj,title='TEST NEW')
        a=Post.objects.get(pk=obj.pk);b=Post.objects.get(pk=obj.pk)
        results=self.parallel([lambda:a.publish(a.latest_revision,user=self.user),lambda:b.unpublish(user=self.user)])
        self.assertEqual(sorted(results),['ok','rejected']);obj.refresh_from_db()
        self.assertEqual(obj.public_image_uses.count(),2 if obj.live else 0)
        if obj.live:self.assertEqual(post_snapshot(obj.pk)['title'],'TEST NEW')

    def test_reader_waits_for_publication_and_index_commit(self):
        obj=self.create_post();self.save_draft(obj,title='TEST NEW',body='<p>TEST NEW</p>',cover_image=self.other_image.pk)
        inside=Event();release=Event();started=Event();done=Event();result={}
        def write():
            with content_transaction():
                row=Post.objects.get(pk=obj.pk);row.publish(row.latest_revision,user=self.user)
                inside.set();self.assertTrue(release.wait(10))
        def read():
            started.set();result.update(post_snapshot(obj.pk))
            with content_transaction(read=True):result['images']=list(public_images().values_list('pk',flat=True))
            done.set()
        with ThreadPoolExecutor(max_workers=2) as pool:
            writer=pool.submit(self.worker,write);self.assertTrue(inside.wait(10))
            reader=pool.submit(self.worker,read);self.assertTrue(started.wait(10))
            try:self.assertFalse(done.wait(.3))
            finally:release.set()
            self.assertEqual(writer.result(10)[0],'ok');self.assertEqual(reader.result(10)[0],'ok')
        self.assertEqual(result['title'],'TEST NEW');self.assertEqual(result['images'],[self.other_image.pk])

    def test_unpublish_waits_for_complete_public_materialization(self):
        obj=self.create_post();inside=Event();release=Event();started=Event();done=Event();result={}
        from .post_publication import post_dto
        def paused(*args,**kwargs):inside.set();self.assertTrue(release.wait(10));return post_dto(*args,**kwargs)
        def read():result.update(post_snapshot(obj.pk))
        def write():
            started.set();Post.objects.get(pk=obj.pk).unpublish(user=self.user);done.set()
        with patch('content.post_publication.post_dto',side_effect=paused),ThreadPoolExecutor(max_workers=2) as pool:
            reader=pool.submit(self.worker,read);self.assertTrue(inside.wait(10))
            writer=pool.submit(self.worker,write);self.assertTrue(started.wait(10))
            try:self.assertFalse(done.wait(.3))
            finally:release.set()
            self.assertEqual(reader.result(10)[0],'ok');self.assertEqual(writer.result(10)[0],'ok')
        self.assertEqual(result['title'],'TEST PUBLIC');self.assertEqual(posts_snapshot()['pagination']['total'],0)
        self.assertFalse(PostImageUse.objects.filter(post=obj).exists())
