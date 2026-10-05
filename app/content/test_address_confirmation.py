"""Dedicated PG/media; fake operator intent, never a provider request or real login."""
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.test import TestCase, Client, override_settings
from bs4 import BeautifulSoup
from .tests import FixtureMixin
from .models import Branch, BranchPhoto
from .publication import public_snapshot

@override_settings(NAVER_MAPS_ENABLED=True, NAVER_MAPS_PUBLIC_KEY_ID='TEST_PUBLIC')
class AddressConfirmationTests(FixtureMixin, TestCase):
    def submit(self, branch, **changes):
        return self.post(self.admin_url(Branch, 'edit', branch), self.form_data(branch, **changes))
    def confirmation(self, branch, **changes):
        return {'map_confirmation':'true', 'map_confirmation_address':branch.address,
                'map_confirmation_version':branch.edit_version, **changes}
    def confirm(self, branch):
        response = self.submit(branch, **self.confirmation(branch))
        self.assertEqual(response.status_code, 302, response.content[:1000])
        branch.refresh_from_db(); self.assertTrue(branch.address_confirmed)

    def test_new_branch_confirmation_and_empty_address_refusal(self):
        data={'name':'TEST new','address':'TEST new road','phone':'000-1111-2222','is_public':'on',
              'sort_order':0,'edit_version':0,'photos-TOTAL_FORMS':0,'photos-INITIAL_FORMS':0,
              'map_confirmation':'true','map_confirmation_address':'TEST new road','map_confirmation_version':0}
        self.assertEqual(self.post(self.admin_url(Branch,'add'),data).status_code,302)
        obj=Branch.objects.get();self.assertTrue(obj.address_confirmed)
        obj._map_confirmation=('',obj.edit_version);obj.address='';obj.is_public=False
        with self.assertRaises(ValidationError):obj.save()

    def test_confirmation_detail_preserves_base_address_invalidates_and_no_external_io(self):
        a=self.branch(is_public=True)
        with patch('content.naver_maps.http.client.HTTPSConnection') as network:
            self.confirm(a)
            version=a.edit_version
            self.assertEqual(self.submit(a,address_detail='TEST 2F').status_code,302)
            a.refresh_from_db();self.assertTrue(a.address_confirmed);self.assertEqual(a.edit_version,version+1)
            self.assertEqual(self.submit(a,address='TEST NEW ADDRESS').status_code,302)
            a.refresh_from_db();self.assertFalse(a.address_confirmed)
            a.address_confirmed=True;a.save();a.refresh_from_db();self.assertFalse(a.address_confirmed)
            network.assert_not_called()

    def test_new_changed_address_can_be_confirmed_in_same_parent_save(self):
        a=self.branch(is_public=True)
        response=self.submit(a,address='TEST NEW',**self.confirmation(a,map_confirmation_address='TEST NEW'))
        self.assertEqual(response.status_code,302)
        a.refresh_from_db();self.assertEqual(a.address,'TEST NEW');self.assertTrue(a.address_confirmed)

    def test_stale_address_version_disabled_and_invalid_key_rejected(self):
        a=self.branch(is_public=True)
        for changes in [{'map_confirmation_address':'OTHER'}, {'map_confirmation_version':a.edit_version+1}]:
            self.assertEqual(self.submit(a,**self.confirmation(a,**changes)).status_code,200)
            a.refresh_from_db();self.assertFalse(a.address_confirmed)
        old=self.form_data(a,**self.confirmation(a));a.summary='newer';a.save()
        self.assertEqual(self.post(self.admin_url(Branch,'edit',a),old).status_code,200)
        a.refresh_from_db();self.assertFalse(a.address_confirmed);self.assertEqual(a.summary,'newer')
        for settings in [dict(NAVER_MAPS_ENABLED=False),dict(NAVER_MAPS_PUBLIC_KEY_ID=''),dict(NAVER_MAPS_PUBLIC_KEY_ID='bad&key')]:
            with override_settings(**settings):
                self.assertEqual(self.submit(a,**self.confirmation(a)).status_code,200)
                self.assertEqual(self.submit(a,address_detail='TEST').status_code,302)
            a.refresh_from_db();self.assertFalse(a.address_confirmed)

    def test_invalid_parent_response_drops_intent_then_plain_save_does_not_confirm(self):
        a=self.branch(is_public=True)
        response=self.submit(a,phone='invalid',**self.confirmation(a))
        self.assertEqual(response.status_code,200)
        soup=BeautifulSoup(response.content,'html.parser')
        self.assertFalse(soup.select_one('[name=map_confirmation]').get('value'))
        a.refresh_from_db();self.assertFalse(a.address_confirmed)
        self.assertEqual(self.submit(a,phone='000-1111-2222').status_code,302)
        a.refresh_from_db();self.assertFalse(a.address_confirmed)

    def test_child_save_failure_rolls_back_parent_confirmation_and_main(self):
        a=self.branch(is_public=True)
        a._map_confirmation=(a.address,a.edit_version)
        a.photos.add(BranchPhoto(image=self.image,caption='TEST fail',sort_order=0))
        original=BranchPhoto.save
        def fail(obj,*args,**kwargs):
            original(obj,*args,**kwargs);raise RuntimeError('test child failure')
        with patch.object(BranchPhoto,'save',fail):
            with self.assertRaises(RuntimeError):a.save()
        a.refresh_from_db();self.assertFalse(a.address_confirmed);self.assertEqual(BranchPhoto.objects.filter(branch=a).count(),0)
        self.assertTrue(a.is_main)

    def test_permission_and_csrf_are_existing_admin_boundary(self):
        a=self.branch(is_public=True);url=self.admin_url(Branch,'edit',a);data=self.form_data(a,**self.confirmation(a))
        self.assertEqual(self.anon.post(url,data).status_code,302)
        self.assertEqual(self.client.post(url,data).status_code,403)
        self.user.groups.clear()
        response=self.post(url,data)
        self.assertIn(response.status_code,[302,403])
        a.refresh_from_db();self.assertFalse(a.address_confirmed)

    def test_only_confirmed_public_own_input_is_exposed_and_no_coordinates_or_result(self):
        a=self.branch(is_public=True);b=self.branch()
        self.confirm(a);self.confirm(b)
        payload=self.anon.get('/api/v1/branches/').json()['items']
        self.assertEqual(len(payload),1)
        self.assertIsNone(payload[0]['location']);self.assertEqual(payload[0]['map'],{'provider':'naver','query':a.address})
        self.assertNotIn('address_confirmed',payload[0]);self.assertNotIn('edit_version',payload[0])
        html=self.anon.get('/branches/');soup=BeautifulSoup(html.content,'html.parser')
        self.assertEqual(len(soup.select('[data-map-open]')),1)
        self.assertContains(html,'네이버지도 보기');self.assertContains(html,'제공·보관·활용')
        self.assertNotContains(html,'oapi.map.naver.com') # Only local JS until user action.
        with override_settings(NAVER_MAPS_ENABLED=False):
            self.assertNotContains(self.anon.get('/branches/'),'naver-map-config')
            self.assertEqual(self.anon.get('/api/v1/branches/').json()['items'][0]['map'],payload[0]['map'])
        a.address='TEST changed';a.save()
        self.assertIsNone(self.anon.get('/api/v1/branches/').json()['items'][0]['map'])

    def test_admin_has_local_widget_no_provider_data_and_no_confirmation_without_key(self):
        a=self.branch(is_public=True)
        with override_settings(NAVER_MAPS_ENABLED=False):
            response=self.client.get(self.admin_url(Branch,'edit',a));soup=BeautifulSoup(response.content,'html.parser')
            self.assertTrue(soup.select_one('[data-map-open]').has_attr('disabled'))
            self.assertTrue(soup.select_one('[data-map-confirm]').has_attr('disabled'))
            self.assertContains(response,'주소는 확인 없이 저장할 수 있습니다.')
            self.assertNotContains(response,'oapi.map.naver.com')
            for filename in ['naver-maps.js','branch-address.js']:
                self.assertEqual(len(soup.select(f'script[src="/static/{filename}"]')),1)

from django.test import TransactionTestCase
from .tests import ConcurrencyMixin

@override_settings(NAVER_MAPS_ENABLED=True, NAVER_MAPS_PUBLIC_KEY_ID='TEST_PUBLIC')
class ConfirmationConcurrencyTests(ConcurrencyMixin, TransactionTestCase):
    def test_address_change_and_confirmation_same_version_have_one_winner(self):
        a=Branch(name='TEST concurrent',address='TEST old',phone='000-1111-2222',is_public=True);a.save()
        confirming=Branch.objects.get(pk=a.pk);changing=Branch.objects.get(pk=a.pk)
        confirming._map_confirmation=(confirming.address,confirming.edit_version)
        changing.address='TEST new'
        result=self.parallel([confirming.save,changing.save])
        self.assertCountEqual(result,['ok','rejected'])
        a.refresh_from_db()
        self.assertEqual((a.address,a.address_confirmed),('TEST old',True) if result[0]=='ok' else ('TEST new',False))
