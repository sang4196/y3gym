from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from threading import Event
from unittest.mock import patch

from bs4 import BeautifulSoup
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection, IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from wagtail.images import get_image_model
from wagtail.models import Collection

from .locking import content_transaction
from .models import Branch, BranchPhoto, SiteContent, Trainer, TrainerCareer
from .publication import public_snapshot, public_images, DISPLAY_FILTER
from .tests import FixtureMixin, ConcurrencyMixin, png


class TrainerFixture(FixtureMixin):
    def trainer(self, branch, **changes):
        data = dict(branch=branch, name='TEST PROFILE', profile_image=self.image,
                    profile_alt='TEST non-person image', short_intro='TEST ONLY introduction', is_public=True)
        data.update(changes)
        trainer = Trainer(**data)
        trainer.save()
        return trainer

    def trainer_data(self, trainer, **changes):
        data = {name: getattr(trainer, name) for name in ['name', 'edit_version', 'job_title', 'profile_alt', 'short_intro', 'sort_order']}
        data.update(branch=trainer.branch_id or '', profile_image=trainer.profile_image_id or '')
        if trainer.is_public:
            data['is_public'] = 'on'
        careers = list(trainer.careers.all()) if trainer.pk else []
        data.update({'careers-TOTAL_FORMS': len(careers), 'careers-INITIAL_FORMS': len(careers),
                     'careers-MIN_NUM_FORMS': 0, 'careers-MAX_NUM_FORMS': 1000})
        for i, career in enumerate(careers):
            data.update({f'careers-{i}-id': career.pk, f'careers-{i}-category': career.category,
                         f'careers-{i}-text': career.text, f'careers-{i}-ORDER': i})
        data.update(changes)
        return data

    def sections(self, client=None):
        response = (client or self.anon).get('/api/v1/trainer-sections/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response['Cache-Control'])
        return response.json()['items']


class TrainerCmsTests(TrainerFixture, TestCase):
    def test_empty_contract_and_read_only_routes(self):
        self.assertEqual(connection.vendor, 'postgresql')
        self.assertEqual(self.sections(), [])
        self.assertContains(self.anon.get('/trainers/'), '공개된 트레이너 소개가 없습니다.')
        self.assertNotContains(self.anon.get('/branches/'), 'href="/trainers/')
        payload = self.anon.get('/api/v1/trainer-sections/').json()
        self.assertTrue(payload['meta']['server_time'].endswith('Z'))
        for verb in ['post', 'put', 'patch', 'delete']:
            response = getattr(self.anon, verb)('/api/v1/trainer-sections/')
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response.json()['error']['code'], 'METHOD_NOT_ALLOWED')
        self.assertEqual(self.anon.get('/api/v1/trainer-sections/?branch=1').status_code, 400)
        self.assertEqual(self.anon.head('/api/v1/trainer-sections/').status_code, 200)
        self.assertEqual(self.anon.get('/trainers/1/').status_code, 404)

    def test_cms_private_preparation_and_required_public_fields(self):
        branch = self.branch()
        unsaved = Trainer(branch=branch)
        path = self.admin_url(Trainer, 'add')
        data = self.trainer_data(unsaved)
        response = self.post(path, data)
        self.assertEqual(response.status_code, 302)
        trainer = Trainer.objects.get()
        self.assertFalse(trainer.is_public)
        self.assertIsNone(trainer.profile_image_id)
        path = self.admin_url(Trainer, 'edit', trainer)
        data = self.trainer_data(trainer, is_public='on')
        response = self.post(path, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue({'name', 'profile_image', 'short_intro'} <= response.context['form'].errors.keys())
        trainer.refresh_from_db()
        self.assertFalse(trainer.is_public)
        data = self.trainer_data(trainer, branch='')
        self.assertEqual(self.post(path, data).status_code, 200)
        trainer.refresh_from_db()
        self.assertEqual(trainer.branch_id, branch.pk)
        with self.assertRaises(ValidationError):
            Trainer().save()
        for field, value in [('name', ' '*5), ('name', 'X'*101), ('job_title', 'X'*101), ('short_intro', 'X'*301)]:
            data = self.trainer_data(trainer, name='TEST', short_intro='TEST', profile_image=self.image.pk, is_public='on')
            data[field] = value
            self.assertEqual(self.post(path, data).status_code, 200)
        # Public profile may be prepared under a private branch without leaking.
        data = self.trainer_data(trainer, name=' TEST ', short_intro=' TEST ', profile_image=self.image.pk, is_public='on')
        self.assertEqual(self.post(path, data).status_code, 302)
        trainer.refresh_from_db()
        self.assertTrue(trainer.is_public)
        self.assertEqual(trainer.name, 'TEST')
        self.assertEqual(self.sections(), [])
        self.file_status(f'/images/display/{self.image.pk}/', 404)

    def test_cms_create_careers_order_optional_groups_and_html_contract(self):
        site = SiteContent(brand_name='TEST SITE'); site.save()
        branch = self.branch(is_public=True)
        empty_branch = self.branch(is_public=True)
        trainer = Trainer(branch=branch, name='TEST <b>name</b>', short_intro='TEST intro', is_public=True, profile_image=self.image)
        data = self.trainer_data(trainer, job_title='   ', **{'careers-TOTAL_FORMS': 4})
        for i, (category, text, order) in enumerate([
            ('experience', 'TEST experience', 0), ('education', 'TEST later', 2),
            ('education', 'TEST first', 1), ('certification', 'TEST <script>plain text</script>', 0),
        ]):
            data.update({f'careers-{i}-category': category, f'careers-{i}-text': text, f'careers-{i}-ORDER': order})
        response = self.post(self.admin_url(Trainer, 'add'), data)
        self.assertEqual(response.status_code, 302, response.content[:1000])
        trainer = Trainer.objects.get()
        anon = self.sections(); self.assertEqual(anon, self.sections(self.client))
        self.assertEqual(len(anon), 1)
        self.assertEqual(anon[0]['branch'], {'id': str(branch.pk), 'name': branch.name, 'is_main': True, 'page_path': f'/branches/#branch-{branch.pk}'})
        dto = anon[0]['trainers'][0]
        self.assertEqual(set(dto), {'id','name','job_title','profile_image','short_intro','career_groups'})
        self.assertIsNone(dto['job_title'])
        self.assertEqual([g['category'] for g in dto['career_groups']], ['education','certification','experience'])
        self.assertEqual(dto['career_groups'][0]['items'], ['TEST first','TEST later'])
        self.assertEqual(dto['profile_image']['url'], f'http://testserver/images/display/{self.image.pk}/')
        snapshot = public_snapshot()
        self.assertEqual(snapshot['branches'][0]['trainer_section_path'], f'/trainers/#branch-{branch.pk}')
        self.assertIsNone(snapshot['branches'][1]['trainer_section_path'])
        html = self.anon.get('/trainers/')
        self.assertContains(html, f'id="branch-{branch.pk}"')
        self.assertNotContains(html, f'id="branch-{empty_branch.pk}"')
        soup = BeautifulSoup(html.content, 'html.parser')
        self.assertEqual([h.text for h in soup.select('h4')], ['학력', '자격증','주요 경력'])
        self.assertFalse(soup.select('.job-title'))
        self.assertFalse(soup.select('main script, main b'))
        self.assertContains(html, 'TEST &lt;b&gt;name&lt;/b&gt;')
        self.assertContains(self.anon.get('/'), '지점별 트레이너 보기')
        self.assertContains(self.anon.get('/branches/'), f'href="/trainers/#branch-{branch.pk}"')
        # Removing rows changes only placements, never the parent or image identity.
        trainer = Trainer.objects.get(pk=trainer.pk)
        data = self.trainer_data(trainer)
        for i in range(4): data[f'careers-{i}-DELETE'] = 'on'
        self.assertEqual(self.post(self.admin_url(Trainer,'edit',trainer), data).status_code, 302)
        self.assertEqual(self.sections()[0]['trainers'][0]['career_groups'], [])
        self.assertFalse(BeautifulSoup(self.anon.get('/trainers/').content,'html.parser').select('h4'))
        self.assertTrue(get_image_model().objects.filter(pk=self.image.pk).exists())

    def test_same_identity_move_branch_hide_and_job_title_not_sorting(self):
        a = self.branch(is_public=True); b = self.branch(is_public=True); hidden = self.branch()
        first = self.trainer(a, name='TEST first', sort_order=2)
        second = self.trainer(a, name='TEST second', sort_order=2)
        career = TrainerCareer.objects.create(trainer=first, category='award', text='TEST award', sort_order=0)
        before_permissions = self.user.get_all_permissions()
        self.assertEqual([t['id'] for t in self.sections()[0]['trainers']], [str(first.pk),str(second.pk)])
        data = self.trainer_data(first, job_title='ZZZ TEST arbitrary title')
        self.assertEqual(self.post(self.admin_url(Trainer,'edit',first),data).status_code,302)
        self.assertEqual(self.user.get_all_permissions(), before_permissions)
        self.assertEqual([t['id'] for t in self.sections()[0]['trainers']], [str(first.pk),str(second.pk)])
        first = Trainer.objects.get(pk=first.pk)
        data = self.trainer_data(first, branch=b.pk)
        self.assertEqual(self.post(self.admin_url(Trainer,'edit',first),data).status_code,302)
        first.refresh_from_db(); career.refresh_from_db()
        self.assertEqual((first.branch_id,career.trainer_id,first.profile_image_id),(b.pk,first.pk,self.image.pk))
        self.assertEqual(Trainer.objects.count(),2)
        self.assertEqual(TrainerCareer.objects.count(),1)
        self.assertEqual([s['branch']['id'] for s in self.sections()],[str(a.pk),str(b.pk)])
        own_version = first.edit_version
        data = self.form_data(b); data.pop('is_public')
        self.assertEqual(self.post(self.admin_url(Branch,'edit',b),data).status_code,302)
        first.refresh_from_db()
        self.assertTrue(first.is_public); self.assertEqual(first.edit_version,own_version)
        self.assertEqual([s['branch']['id'] for s in self.sections()],[str(a.pk)])
        self.assertEqual(TrainerCareer.objects.get(pk=career.pk).text,'TEST award')
        data = self.trainer_data(first, branch=hidden.pk)
        self.assertEqual(self.post(self.admin_url(Trainer,'edit',first),data).status_code,302)
        self.assertEqual(len(self.sections()),1)
        hidden.is_public=True;hidden.save()
        self.assertEqual(self.sections()[-1]['trainers'][0]['id'],str(first.pk))
        hidden.name='TEST renamed';hidden.save()
        self.assertEqual(self.sections()[-1]['branch']['name'],'TEST renamed')

    def test_foreign_child_ids_rejected_and_failed_cms_save_rolls_back(self):
        branch = self.branch(is_public=True)
        a = self.trainer(branch); b = self.trainer(branch)
        foreign = TrainerCareer.objects.create(trainer=b,category='education',text='TEST original',sort_order=0)
        path = self.admin_url(Trainer,'edit',a)
        for delete in [False,True]:
            data = self.trainer_data(a,short_intro='must not save',**{'careers-TOTAL_FORMS':1,'careers-INITIAL_FORMS':1,
                'careers-0-id':foreign.pk,'careers-0-category':'experience','careers-0-text':'ATTACK','careers-0-ORDER':0})
            if delete: data['careers-0-DELETE']='on'
            response=self.post(path,data)
            self.assertEqual(response.status_code,200)
            self.assertContains(response,'다른 콘텐츠에 속한')
            a.refresh_from_db();foreign.refresh_from_db()
            self.assertEqual(a.short_intro,'TEST ONLY introduction');self.assertEqual(foreign.text,'TEST original')
        data = self.trainer_data(a,short_intro='must rollback',**{'careers-TOTAL_FORMS':1,
            'careers-0-category':'award','careers-0-text':'TEST new','careers-0-ORDER':0})
        original = TrainerCareer.save
        def fail_after_child(instance,*args,**kwargs):
            original(instance,*args,**kwargs)
            raise RuntimeError('injected child failure')
        with patch.object(TrainerCareer,'save',fail_after_child), self.assertRaises(RuntimeError):
            self.post(path,data)
        a.refresh_from_db()
        self.assertEqual(a.short_intro,'TEST ONLY introduction')
        self.assertEqual(a.edit_version,1)
        self.assertFalse(TrainerCareer.objects.filter(trainer=a).exists())
        a.careers.add(foreign)
        with self.assertRaises(ValidationError):a.save()
        self.assertEqual(TrainerCareer.objects.get(pk=foreign.pk).trainer_id,b.pk)

    def test_stale_save_bad_career_and_missing_file_rejected(self):
        branch=self.branch(is_public=True);trainer=self.trainer(branch)
        path=self.admin_url(Trainer,'edit',trainer)
        old=self.trainer_data(trainer,name='stale')
        trainer.name='TEST current';trainer.save()
        response=self.post(path,old)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'다른 저장이 먼저 반영되었습니다.')
        trainer.refresh_from_db();self.assertEqual(trainer.name,'TEST current')
        for category,text in [('other','TEST'),('education','   '),('award','X'*501)]:
            data=self.trainer_data(trainer,name='must not save',**{'careers-TOTAL_FORMS':1,
                'careers-0-category':category,'careers-0-text':text,'careers-0-ORDER':0})
            self.assertEqual(self.post(path,data).status_code,200)
            trainer.refresh_from_db();self.assertEqual(trainer.name,'TEST current')
        self.image.file.name='missing-test-file.png';self.image.save(update_fields=['file'])
        response=self.post(path,self.trainer_data(trainer))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'참조 이미지 파일이 없습니다.')
        with self.assertRaises(ValidationError):trainer.save(update_fields=['name'])

    def test_database_constraints_and_single_branch_reference(self):
        branch=self.branch();trainer=self.trainer(branch,is_public=False,name='',short_intro='',profile_image=None)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Trainer.objects.filter(pk=trainer.pk).update(is_public=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Trainer.objects.filter(pk=trainer.pk).update(branch_id=None)
        with self.assertRaises(ProtectedError):branch.delete()
        for category,text in [('other','TEST'),('award','')]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                TrainerCareer.objects.create(trainer=trainer,category=category,text=text)

    def test_shared_media_last_reference_and_private_routes(self):
        site=SiteContent(brand_name='TEST',hero_image=self.image);site.save()
        a=self.branch(is_public=True,cover_image=self.image);b=self.branch(is_public=True)
        b.photos.add(BranchPhoto(image=self.image));b.save()
        trainer=self.trainer(b)
        url=f'/images/display/{self.image.pk}/'
        self.file_status(url,200)
        site.hero_image=None;site.save();a.cover_image=None;a.save()
        b.photos.clear();b.save();self.file_status(url,200)
        b.is_public=False;b.save();self.file_status(url,404)
        trainer.refresh_from_db();self.assertTrue(trainer.is_public)
        b.is_public=True;b.save();self.file_status(url,200)
        trainer.is_public=False;trainer.save();self.file_status(url,404,self.client)
        trainer.is_public=True;trainer.save();self.file_status(url,200)
        # A new selected asset changes only this profile's reference.
        trainer.profile_image=self.other_image;trainer.save()
        self.file_status(url,404);self.file_status(f'/images/display/{self.other_image.pk}/',200)
        self.assertTrue(get_image_model().objects.filter(pk=self.image.pk).exists())
        for path in [self.other_image.file.url,self.other_image.get_rendition('max-165x165').url,self.other_image.get_rendition(DISPLAY_FILTER).url]:
            self.file_status(path,403);self.file_status(path,200,self.client)
        self.assertIn('EXISTS',str(public_images().query))
        self.assertIn('content_trainer',str(public_images().query))

    def test_trainer_delete_csrf_and_image_permission_injection_denied(self):
        branch=self.branch(is_public=True);trainer=self.trainer(branch)
        path=self.admin_url(Trainer,'edit',trainer)
        hidden=Collection.get_first_root_node().add_child(name='not allowed')
        image=get_image_model().objects.create(title='TEST protected',file=png('hidden.png'),collection=hidden)
        response=self.post(path,self.trainer_data(trainer,profile_image=image.pk))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'선택 권한이 없는 이미지입니다.')
        trainer.refresh_from_db();self.assertEqual(trainer.profile_image_id,self.image.pk)
        self.assertEqual(self.client.post(path,self.trainer_data(trainer)).status_code,403)
        self.assertIn(self.post(self.admin_url(Trainer,'delete',trainer),{}).status_code,[302,403])
        bulk=reverse('wagtail_bulk_action',args=['content','trainer','delete'])
        self.assertEqual(self.post(bulk+f'?id={trainer.pk}',{}).status_code,403)
        self.assertTrue(Trainer.objects.filter(pk=trainer.pk).exists())
        self.assertFalse(Trainer.snippet_viewset.permission_policy.user_has_permission(self.user,'delete'))
        self.assertIn(self.anon.get(path).status_code,[302,403])

    def test_permission_extension_additive_idempotent_and_no_account_save(self):
        group=Group.objects.get(name='홈페이지 운영자')
        trainer_permissions=list(Permission.objects.filter(content_type__app_label='content',content_type__model='trainer',codename__in=['add_trainer','change_trainer','view_trainer']))
        group.permissions.remove(*trainer_permissions)
        # Existing unrelated group permission and collection permissions survive.
        extra=Permission.objects.get(content_type__app_label='content',codename='view_trainercareer')
        group.permissions.add(extra)
        before=set(group.permissions.values_list('pk',flat=True))
        membership=list(self.user.groups.values_list('pk',flat=True))
        with patch.object(type(self.user),'save',side_effect=AssertionError('must not save account')):
            call_command('extend_trainer_permissions',stdout=StringIO())
            call_command('extend_trainer_permissions',stdout=StringIO())
        self.assertEqual(set(group.permissions.values_list('pk',flat=True)),before|{p.pk for p in trainer_permissions})
        self.assertEqual(list(self.user.groups.values_list('pk',flat=True)),membership)
        self.assertFalse(group.permissions.filter(codename='delete_trainer').exists())


class TrainerConcurrencyTests(TrainerFixture, ConcurrencyMixin, TransactionTestCase):
    def test_concurrent_stale_profile_saves(self):
        branch=self.branch(is_public=True);trainer=self.trainer(branch)
        left=Trainer.objects.get(pk=trainer.pk);right=Trainer.objects.get(pk=trainer.pk)
        left.short_intro='TEST left';right.short_intro='TEST right'
        self.assertEqual(sorted(self.parallel([left.save,right.save])),['ok','rejected'])
        trainer.refresh_from_db();self.assertEqual(trainer.edit_version,2)
        self.assertIn(trainer.short_intro,['TEST left','TEST right'])

    def test_concurrent_move_and_branch_hide(self):
        a=self.branch(is_public=True);b=self.branch(is_public=True)
        trainer=self.trainer(a)
        def move():
            obj=Trainer.objects.get(pk=trainer.pk);obj.branch_id=b.pk;obj.save()
        def hide():
            obj=Branch.objects.get(pk=b.pk);obj.is_public=False;obj.save()
        self.assertEqual(self.parallel([move,hide]),['ok','ok'])
        trainer.refresh_from_db();self.assertTrue(trainer.is_public);self.assertEqual(trainer.branch_id,b.pk)
        self.assertEqual(public_snapshot()['trainer_sections'],[])
        self.assertFalse(public_images().filter(pk=self.image.pk).exists())

    def test_reader_waits_for_move_and_complete_career_commit(self):
        a=self.branch(is_public=True);b=self.branch(is_public=True)
        trainer=self.trainer(a);trainer.careers.add(TrainerCareer(category='education',text='TEST old'));trainer.save()
        writer_inside=Event();release=Event();reader_started=Event();reader_done=Event();result={}
        def write():
            with content_transaction():
                obj=Trainer.objects.get(pk=trainer.pk);obj.branch_id=b.pk;obj.short_intro='TEST new'
                obj.careers.set([TrainerCareer(category='experience',text='TEST new career',sort_order=0)]);obj.save()
                writer_inside.set();self.assertTrue(release.wait(timeout=10))
        def read():
            reader_started.set();result.update(public_snapshot());reader_done.set()
        with ThreadPoolExecutor(max_workers=2) as pool:
            writer=pool.submit(self.worker,write);self.assertTrue(writer_inside.wait(timeout=10))
            reader=pool.submit(self.worker,read);self.assertTrue(reader_started.wait(timeout=10))
            try:self.assertFalse(reader_done.wait(timeout=.3))
            finally:release.set()
            wr=writer.result(timeout=10);rr=reader.result(timeout=10)
            self.assertEqual((wr[0],rr[0]),('ok','ok'));self.assertNotEqual(wr[1],rr[1])
        self.assertIsNone(result['branches'][0]['trainer_section_path'])
        self.assertEqual(result['branches'][1]['trainer_section_path'],f'/trainers/#branch-{b.pk}')
        sections=result['trainer_sections'];self.assertEqual(len(sections),1)
        self.assertEqual(sections[0]['branch']['id'],str(b.pk))
        dto=sections[0]['trainers'][0]
        self.assertEqual(dto['id'],str(trainer.pk));self.assertEqual(dto['short_intro'],'TEST new')
        self.assertEqual(dto['career_groups'],[{'category':'experience','items':['TEST new career']}])

    def test_branch_hide_waits_until_trainer_materialization_finishes(self):
        self.branch(is_public=True);branch=self.branch(is_public=True)
        trainer=self.trainer(branch);trainer.careers.add(TrainerCareer(category='award',text='TEST award'));trainer.save()
        reader_inside=Event();release=Event();writer_started=Event();writer_done=Event();result={}
        from .publication import trainer_dto
        def paused_dto(obj):
            reader_inside.set();self.assertTrue(release.wait(timeout=10));return trainer_dto(obj)
        def read():result.update(public_snapshot())
        def hide():
            writer_started.set();obj=Branch.objects.get(pk=branch.pk);obj.is_public=False;obj.save();writer_done.set()
        with patch('content.publication.trainer_dto',paused_dto),ThreadPoolExecutor(max_workers=2) as pool:
            reader=pool.submit(self.worker,read);self.assertTrue(reader_inside.wait(timeout=10))
            writer=pool.submit(self.worker,hide);self.assertTrue(writer_started.wait(timeout=10))
            try:self.assertFalse(writer_done.wait(timeout=.3))
            finally:release.set()
            rr=reader.result(timeout=10);wr=writer.result(timeout=10)
            self.assertEqual((rr[0],wr[0]),('ok','ok'));self.assertNotEqual(rr[1],wr[1])
        self.assertEqual(result['trainer_sections'][0]['trainers'][0]['career_groups'],[{'category':'award','items':['TEST award']}])
        self.assertEqual(public_snapshot()['trainer_sections'],[])
        trainer.refresh_from_db();self.assertTrue(trainer.is_public)
