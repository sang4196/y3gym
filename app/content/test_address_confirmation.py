"""Google replacement for DEV-05-B intent tests; isolated PG/media, no provider I/O."""
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase, override_settings
from bs4 import BeautifulSoup
from .tests import FixtureMixin, ConcurrencyMixin
from .models import Branch, BranchPhoto

URL = 'https://www.google.com/maps/embed?pb=!1m18!2m3!1d123!2d456!3d789!2sTEST'
OTHER = URL + '!5sTEST2'
HTML = f'<iframe src="{URL}" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>'

class AddressConfirmationTests(FixtureMixin, TestCase):
    def submit(self, branch, **changes):
        return self.post(self.admin_url(Branch,'edit',branch),self.form_data(branch,google_map_input=branch.google_embed_url,**changes))
    def confirmation(self, branch, **changes):
        return dict(map_confirmation='true',map_confirmation_address=branch.address,
                    map_confirmation_version=branch.edit_version,map_confirmation_url=URL,**changes)
    def confirm(self, branch):
        response=self.post(self.admin_url(Branch,'edit',branch),self.form_data(branch,google_map_input=HTML,**self.confirmation(branch)))
        self.assertEqual(response.status_code,302)
        branch.refresh_from_db();self.assertTrue(branch.google_map_confirmed)

    def test_new_branch_html_confirmation_stores_only_url_and_no_legacy_promotion(self):
        data={'name':'TEST new','address':'TEST road','phone':'000-1111-2222','is_public':'on','sort_order':0,'edit_version':0,
              'photos-TOTAL_FORMS':0,'photos-INITIAL_FORMS':0,'google_map_input':HTML,'map_confirmation':'true',
              'map_confirmation_address':'TEST road','map_confirmation_version':0,'map_confirmation_url':URL}
        self.assertEqual(self.post(self.admin_url(Branch,'add'),data).status_code,302)
        b=Branch.objects.get();self.assertEqual(b.google_embed_url,URL);self.assertTrue(b.google_map_confirmed)
        old=self.branch();Branch.objects.filter(pk=old.pk).update(address_confirmed=True)
        old.refresh_from_db();old.google_embed_url=URL;old.google_map_confirmed=True;old.save();old.refresh_from_db()
        self.assertFalse(old.google_map_confirmed);self.assertTrue(old.address_confirmed)

    def test_detail_preserves_base_change_and_return_stay_unconfirmed_no_network(self):
        b=self.branch(is_public=True)
        with patch('content.naver_maps.http.client.HTTPSConnection') as network:
            self.confirm(b);old=b.address
            self.assertEqual(self.submit(b,address_detail='TEST 2F').status_code,302)
            b.refresh_from_db();self.assertTrue(b.google_map_confirmed)
            self.assertEqual(self.submit(b,address='TEST NEW').status_code,302)
            b.refresh_from_db();self.assertFalse(b.google_map_confirmed);self.assertEqual(b.google_map_address,'')
            b.address=old;b.save();b.refresh_from_db();self.assertFalse(b.google_map_confirmed)
            network.assert_not_called()

    def test_registration_replacement_removal_and_changed_address_confirmation(self):
        b=self.branch(is_public=True);url=self.admin_url(Branch,'edit',b)
        self.assertEqual(self.post(url,self.form_data(b,google_map_input=HTML)).status_code,302)
        b.refresh_from_db();self.assertEqual(b.google_embed_url,URL);self.assertFalse(b.google_map_confirmed)
        self.confirm(b)
        self.assertEqual(self.post(url,self.form_data(b,google_map_input=OTHER)).status_code,302)
        b.refresh_from_db();self.assertFalse(b.google_map_confirmed)
        data=self.form_data(b,google_map_input=OTHER,address='TEST NEW',map_confirmation='true',map_confirmation_address='TEST NEW',map_confirmation_version=b.edit_version,map_confirmation_url=OTHER)
        self.assertEqual(self.post(url,data).status_code,302);b.refresh_from_db();self.assertTrue(b.google_map_confirmed)
        self.assertEqual(self.post(url,self.form_data(b,google_map_input='')).status_code,302)
        b.refresh_from_db();self.assertFalse(b.google_map_confirmed);self.assertEqual(b.google_embed_url,'');self.assertEqual(b.google_map_address,'')

    def test_wrong_address_url_version_and_stale_rejected(self):
        b=self.branch(is_public=True);url=self.admin_url(Branch,'edit',b)
        for key,value in [('map_confirmation_address','OTHER'),('map_confirmation_url',OTHER),('map_confirmation_version',99)]:
            intent=self.confirmation(b);intent[key]=value
            self.assertEqual(self.post(url,self.form_data(b,google_map_input=HTML,**intent)).status_code,200)
            b.refresh_from_db();self.assertFalse(b.google_map_confirmed);self.assertEqual(b.google_embed_url,'')
        stale=self.form_data(b,google_map_input=HTML,**self.confirmation(b));b.summary='fresh';b.save()
        self.assertEqual(self.post(url,stale).status_code,200)
        b.refresh_from_db();self.assertEqual(b.summary,'fresh');self.assertFalse(b.google_map_confirmed)

    def test_parent_invalid_clears_intent_and_persists_nothing(self):
        b=self.branch(is_public=True)
        data=self.form_data(b,phone='invalid',google_map_input=HTML,**self.confirmation(b))
        response=self.post(self.admin_url(Branch,'edit',b),data)
        self.assertEqual(response.status_code,200)
        soup=BeautifulSoup(response.content,'html.parser')
        self.assertFalse(soup.select_one('[name=map_confirmation]').get('value'))
        b.refresh_from_db();self.assertEqual(b.google_embed_url,'');self.assertFalse(b.google_map_confirmed)

    def test_child_invalid_form_and_save_failure_rollback_map_parent_and_main(self):
        b=self.branch(is_public=True);version=b.edit_version
        data=self.form_data(b,google_map_input=HTML,**self.confirmation(b))
        data.update({'photos-TOTAL_FORMS':1,'photos-0-image':self.image.pk,'photos-0-caption':'x'*256,'photos-0-ORDER':0})
        self.assertEqual(self.post(self.admin_url(Branch,'edit',b),data).status_code,200)
        b.refresh_from_db();self.assertEqual(b.edit_version,version);self.assertEqual(b.google_embed_url,'')
        b.google_embed_url=URL;b._google_map_confirmation=(b.address,URL,b.edit_version)
        b.photos.add(BranchPhoto(image=self.image,caption='TEST',sort_order=0))
        original=BranchPhoto.save
        def fail(obj,*args,**kwargs):original(obj,*args,**kwargs);raise RuntimeError('TEST child failure')
        with patch.object(BranchPhoto,'save',fail):
            with self.assertRaises(RuntimeError):b.save()
        b.refresh_from_db();self.assertEqual(b.google_embed_url,'');self.assertEqual(b.edit_version,version);self.assertTrue(b.is_main)
        self.assertEqual(BranchPhoto.objects.filter(branch_id=b.pk).count(),0)

    def test_permission_and_csrf_boundary(self):
        b=self.branch(is_public=True);url=self.admin_url(Branch,'edit',b);data=self.form_data(b,google_map_input=HTML,**self.confirmation(b))
        self.assertEqual(self.anon.post(url,data).status_code,302)
        self.assertEqual(self.client.post(url,data).status_code,403)
        self.user.groups.clear();self.assertIn(self.post(url,data).status_code,[302,403])
        b.refresh_from_db();self.assertEqual(b.google_embed_url,'')

    @override_settings(NAVER_MAPS_ENABLED=True,NAVER_MAPS_PUBLIC_KEY_ID='UNUSED')
    def test_public_projection_filter_escaping_and_no_iframe_until_click(self):
        b=self.branch(is_public=True);private=self.branch();self.confirm(b);self.confirm(private)
        b.name='TEST </script><script>attack</script>';b.save()
        data=self.anon.get('/api/v1/branches/').json()['items'];self.assertEqual(len(data),1)
        self.assertIsNone(data[0]['location']);self.assertEqual(data[0]['map'],dict(provider='google',mode='embed',embed_url=URL))
        self.assertNotIn('google_map_address',data[0]);self.assertNotIn('edit_version',data[0])
        response=self.anon.get('/branches/');soup=BeautifulSoup(response.content,'html.parser')
        self.assertIsNone(soup.select_one('iframe'));self.assertEqual(len(soup.select('[data-google-map]')),1)
        self.assertEqual(soup.select_one('[data-google-map]')['data-embed-url'],URL)
        self.assertNotContains(response,'naver-maps.js');self.assertNotContains(response,'<script>attack</script>')
        self.assertContains(response,b.address);self.assertContains(response,'tel:')
        b.address='TEST CHANGED';b.save();self.assertIsNone(self.anon.get('/api/v1/branches/').json()['items'][0]['map'])
        self.assertNotContains(self.anon.get('/branches/'),'google-maps.js')

    def test_bad_input_error_never_renders_markup_or_partially_saves(self):
        b=self.branch(is_public=True);version=b.edit_version
        for raw in [HTML+'<script>attack()</script>', HTML.replace('loading=', 'onload='), URL+'&key=TEST']:
            response=self.post(self.admin_url(Branch,'edit',b),self.form_data(b,google_map_input=raw,summary='must not save'))
            self.assertEqual(response.status_code,200)
            self.assertNotContains(response,'<script>attack()</script>')
            self.assertIsNone(BeautifulSoup(response.content,'html.parser').select_one('iframe'))
            b.refresh_from_db();self.assertEqual(b.edit_version,version);self.assertEqual(b.summary,'');self.assertEqual(b.google_embed_url,'')

    def test_admin_widget_is_local_no_external_frame_and_no_key_requirement(self):
        b=self.branch(is_public=True);self.confirm(b)
        response=self.client.get(self.admin_url(Branch,'edit',b));soup=BeautifulSoup(response.content,'html.parser')
        self.assertEqual(soup.select_one('textarea[name=google_map_input]').text.strip(),URL)
        self.assertIsNone(soup.select_one('iframe'))
        self.assertFalse(soup.select_one('[data-map-open]').has_attr('disabled'))
        self.assertTrue(soup.select_one('[data-map-confirm]').has_attr('disabled'))
        self.assertNotContains(response,'naver-maps.js')
        for filename in ['google-maps.js','branch-google-map.js']:
            self.assertEqual(len(soup.select(f'script[src="/static/{filename}"]')),1)

class ConfirmationConcurrencyTests(ConcurrencyMixin, TransactionTestCase):
    def test_address_change_and_confirmation_same_version_have_one_winner(self):
        b=Branch(name='TEST',address='TEST old',phone='000-1111-2222',is_public=True);b.save()
        confirming=Branch.objects.get(pk=b.pk);changing=Branch.objects.get(pk=b.pk)
        confirming.google_embed_url=URL;confirming._google_map_confirmation=(confirming.address,URL,confirming.edit_version)
        changing.address='TEST new'
        result=self.parallel([confirming.save,changing.save]);self.assertCountEqual(result,['ok','rejected'])
        b.refresh_from_db();self.assertEqual((b.address,b.google_map_confirmed),('TEST old',True) if result[0]=='ok' else ('TEST new',False))
