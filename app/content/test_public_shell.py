"""DEV-03 review regression: real templates with isolated PostgreSQL content."""
from unittest.mock import patch
from bs4 import BeautifulSoup
from django.db import OperationalError, connection
from django.core.exceptions import ValidationError
from django.test import TestCase, RequestFactory
from django.test.utils import CaptureQueriesContext
from .test_posts import PostFixture
from .models import SiteContent, Trainer, Post
from .publication import public_shell
from .views import server_error


class PublicShellTests(PostFixture, TestCase):
    def setUp(self):
        super().setUp()
        SiteContent(brand_name='TEST SHELL BRAND', hero_image=self.image).save()
        self.branch_row = self.branch(is_public=True)
        self.hidden_branch = self.branch()
        self.trainer = Trainer(branch=self.branch_row, name='TEST TRAINER', short_intro='TEST INTRO', profile_image=self.image, is_public=True)
        self.trainer.save()
        self.article = self.create_post(title='TEST PUBLIC ARTICLE', body='<p>TEST text</p>', cover_image='')

    def assert_shell(self, response, has_trainers, status=200):
        self.assertEqual(response.status_code, status)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(soup.select_one('header .brand').get_text(), 'TEST SHELL BRAND')
        self.assertEqual(soup.select_one('footer .brand').get_text(), 'TEST SHELL BRAND')
        self.assertEqual(bool(soup.select_one('header nav a[href="/trainers/"]')), has_trainers)
        panel = soup.select_one('#primary-navigation')
        toggle = soup.select_one('[data-menu-toggle]')
        self.assertEqual(len(soup.select('#primary-navigation')), 1)
        self.assertNotIn('hidden', panel.attrs)  # no-JS/failed-script fallback
        self.assertIn('hidden', toggle.attrs)
        self.assertEqual(toggle['aria-controls'], panel['id'])
        self.assertEqual(toggle['aria-expanded'], 'false')
        self.assertEqual(toggle['aria-label'], '메뉴 열기')
        self.assertEqual(len(soup.select('header nav')), 1)
        self.assertEqual(len(soup.select('script[src^="/static/navigation.js?v="][defer]')), 1)
        self.assertIsNone(panel.select_one('[data-reveal], [hidden]'))
        self.assertEqual(soup.select('header .contact-cta'), panel.select('.contact-cta'))
        for path in ['/', '/branches/', '/posts/']:
            self.assertIsNotNone(soup.select_one(f'header nav a[href="{path}"]'))

    def test_brand_and_navigation_match_across_public_pages_with_and_without_trainers(self):
        paths = ['/', '/branches/', '/trainers/', '/posts/', self.article.get_absolute_url()]
        for public, branch, expected in [
            (True,self.branch_row,True), (False,self.branch_row,False),
            (True,self.hidden_branch,False), (True,self.branch_row,True),
        ]:
            self.trainer.is_public=public; self.trainer.branch=branch; self.trainer.save()
            for path in paths:
                with self.subTest(public=public,branch=branch.pk,path=path):
                    self.assert_shell(self.anon.get(path), expected)

    def test_public_errors_preserve_shell_when_database_available(self):
        for visible in [True, False]:
            self.trainer.is_public=visible;self.trainer.save()
            for path, status in [('/posts/?page=bad',400),('/posts/999999/',404),('/missing/',404)]:
                self.assert_shell(self.anon.get(path), visible, status)
            self.assert_shell(server_error(RequestFactory().get('/posts/')), visible, 500)

    def test_error_page_survives_database_outage(self):
        with patch('content.views.public_shell', side_effect=OperationalError('TEST database unavailable')):
            response=server_error(RequestFactory().get('/posts/'))
        self.assertEqual(response.status_code,500)
        soup=BeautifulSoup(response.content,'html.parser')
        self.assertEqual(soup.select_one('header .brand').get_text(),'홈')
        self.assertIsNone(soup.select_one('header nav a[href="/trainers/"]'))
        self.assertNotIn(b'TEST database unavailable',response.content)

    def test_preview_uses_public_shell_without_publishing_draft(self):
        before=self.api(self.article)
        self.save_draft(self.article,title='TEST PRIVATE REVISION')
        url=self.admin_url(Post,'preview_on_edit',self.article)
        self.assertTrue(self.post(url,self.post_data(self.article)).json()['is_valid'])
        for visible in [True, False]:
            self.trainer.is_public=visible;self.trainer.save()
            response=self.client.get(url);self.assert_shell(response,visible)
            self.assertContains(response,'TEST PRIVATE REVISION')
            self.assertEqual(self.api(self.article),before)
            request=RequestFactory().get(url);request.user=self.user
            with patch('content.post_models.validate_images',side_effect=ValidationError('TEST missing file')):
                self.assert_shell(self.article.serve_preview(request,''),visible,400)
        self.assertEqual(self.anon.get(url).status_code,302)

    def test_shell_projection_is_small_and_posts_do_not_build_unrelated_content(self):
        with patch('content.publication.image_dto',side_effect=AssertionError('unneeded rendition')), \
             patch('content.publication.site_dto',side_effect=AssertionError('unneeded site content')), \
             patch('content.publication.trainer_dto',side_effect=AssertionError('unneeded trainer content')):
            with CaptureQueriesContext(connection) as queries:
                shell=public_shell()
            self.assertEqual(shell,{'brand_name':'TEST SHELL BRAND','has_trainers':True,
                                   'logo':None,'contact_path':f'/branches/#branch-{self.branch_row.pk}'})
            selects=[q['sql'] for q in queries if q['sql'].startswith('SELECT') and 'pg_advisory' not in q['sql']]
            self.assertEqual(len(selects),3)
            self.assertNotIn('wagtailimages_rendition', ' '.join(selects))
            self.assertNotIn('content_branchphoto', ' '.join(selects))
            self.assertNotIn('content_trainercareer', ' '.join(selects))
            self.assertTrue(any('LIMIT 2' in sql and 'content_branch' in sql for sql in selects))
            self.assertNotIn('wagtailcore_revision', ' '.join(selects))
            self.assert_shell(self.anon.get('/posts/'),True)
            self.assert_shell(self.anon.get(self.article.get_absolute_url()),True)
            self.assert_shell(self.anon.get('/posts/?page=bad'),True,400)

    def test_post_api_contract_has_no_ui_shell_or_additional_shell_queries(self):
        with patch('content.post_views.public_shell',side_effect=AssertionError('HTML-only shell')):
            listing=self.anon.get('/api/v1/posts/').json()
            detail=self.api(self.article)
        self.assertEqual(set(listing),{'items','pagination','meta'})
        self.assertEqual(set(detail),{'id','title','category','cover_image','published_at','detail_path','body_html','updated_at'})
        self.assertNotIn('TEST SHELL BRAND',str(listing))
