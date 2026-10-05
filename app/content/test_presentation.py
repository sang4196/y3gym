"""DEV-06 server HTML and PostgreSQL boundaries; these are not browser tests."""
from unittest.mock import patch
from bs4 import BeautifulSoup
from django.db import connection, OperationalError
from django.test import TestCase, RequestFactory
from django.core.exceptions import ValidationError
from .test_posts import PostFixture
from .models import SiteContent, Trainer, BranchPhoto
from .publication import public_shell, public_snapshot
from .presentation import excerpt
from .views import server_error


class PresentationTests(PostFixture, TestCase):
    def setUp(self):
        super().setUp()
        self.site = SiteContent(brand_name='TEST <브랜드> & "이름"', hero_title='TEST 소개',
                               hero_description='TEST 공개 소개', logo=self.image, logo_alt='TEST 로고')
        self.site.save()

    def soup(self, path, status=200):
        response = self.anon.get(path)
        self.assertEqual(response.status_code, status)
        return BeautifulSoup(response.content, 'html.parser')

    def test_contact_targets_zero_one_multiple_on_every_page_and_error(self):
        self.assertEqual(connection.vendor, 'postgresql')
        post = self.create_post(body='<p>TEST PUBLIC</p>')
        paths = ['/', '/branches/', '/trainers/', '/posts/', post.get_absolute_url()]
        hidden = self.branch()
        for count in range(3):
            if count: branch = self.branch(is_public=True)
            expected = None if count == 0 else (f'/branches/#branch-{branch.pk}' if count == 1 else '/branches/')
            self.assertEqual(public_shell()['contact_path'], expected)
            self.assertEqual(public_snapshot()['public_shell']['contact_path'], expected)
            for path in paths + ['/missing/']:
                with self.subTest(count=count, path=path):
                    soup = self.soup(path, 404 if path == '/missing/' else 200)
                    contacts = soup.select('.contact-cta')
                    self.assertEqual(bool(contacts), bool(expected))
                    self.assertTrue(all(a['href'] == expected for a in contacts))
                    self.assertNotIn(f'branch-{hidden.pk}', str(soup))
            self.assertEqual(bool(self.soup('/branches/').select('nav[aria-label="지점 바로가기"]')), count > 1)

    def test_shared_logo_landmarks_current_menu_and_escape(self):
        branch = self.branch(is_public=True)
        Trainer(branch=branch, name='TEST trainer', short_intro='TEST', profile_image=self.image, is_public=True).save()
        post = self.create_post()
        for path, section_path in [('/', '/'),('/branches/', '/branches/'),('/trainers/', '/trainers/'),('/posts/', '/posts/'),(post.get_absolute_url(), '/posts/')]:
            soup = self.soup(path)
            self.assertEqual(soup.html['lang'], 'ko')
            self.assertEqual(len(soup.select('main')), 1)
            self.assertEqual(soup.select_one('.skip-link')['href'], '#main-content')
            self.assertEqual(soup.select_one('main')['tabindex'], '-1')
            self.assertEqual(len(soup.select('h1')), 1)
            for region in ['header', 'footer']:
                self.assertEqual(soup.select_one(region+' .brand span').text, self.site.brand_name)
                logo = soup.select_one(region+' .logo')
                self.assertEqual(logo['src'], f'/images/display/{self.image.pk}/')
                self.assertEqual(logo['alt'], 'TEST 로고')
                self.assertEqual([a['href'] for a in soup.select(region+' nav [aria-current="page"]')], [section_path])
            self.assertIn(self.site.brand_name, soup.title.text)
            self.assertIsNone(soup.select_one('브랜드, link[rel="canonical"], meta[property^="og:"]'))
            self.assertIsNone(soup.select_one('meta[name="robots"]'))
            for image in soup.select('img'):
                self.assertTrue(all(name in image.attrs for name in ['src','alt','width','height']))
            self.assertTrue(all(not script.get('src','').startswith('http') for script in soup.select('script')))

    def test_home_fixed_order_conditional_sections_and_three_public_posts(self):
        soup = self.soup('/')
        self.assertIsNone(soup.select_one('#intro-title, #branches-title, #trainers-title, #recent-title, .hero-image'))
        self.site.introduction='TEST 소개 본문'; self.site.introduction_image=self.image
        self.site.hero_image=self.other_image; self.site.save()
        branch=self.branch(is_public=True,cover_image=self.image)
        Trainer(branch=branch,name='TEST',short_intro='TEST',profile_image=self.image,is_public=True).save()
        for n in range(4): self.create_post(title=f'TEST PUBLIC {n}',body='<p>TEST</p>')
        self.create_post(publish=False,title='TEST PRIVATE')
        soup=self.soup('/')
        self.assertEqual([h['id'] for h in soup.select('main h2[id]')],['intro-title','branches-title','trainers-title','recent-title'])
        self.assertEqual(len(soup.select('.post-summary h3')),3)
        self.assertEqual(len(soup.select('.post-summary h2')),0)
        self.assertNotIn('TEST PRIVATE',soup.text)
        self.assertIsNone(soup.select_one('.hero-image').get('loading'))
        self.assertTrue(all(image.get('loading')=='lazy' for image in soup.select('main img:not(.hero-image)')))
        popup=soup.select_one('[data-home-popup]')
        self.assertIn('hidden',popup.attrs);self.assertEqual(popup['aria-labelledby'],'home-popup-title')
        self.assertEqual(soup.select_one('[data-popup-return]').name,'h1')

    def test_branch_address_contacts_usage_photos_and_no_map(self):
        branch=self.branch(is_public=True, business_hours='TEST 오전\nTEST 오후', parking_info='TEST 주차', usage_notes='TEST 기타')
        BranchPhoto.objects.create(branch=branch,image=self.image,alt='TEST 시설',caption='TEST <caption>')
        article=self.soup('/branches/').select_one(f'#branch-{branch.pk}')
        self.assertEqual(article['tabindex'],'-1')
        self.assertIn(branch.address,article.address.text)
        self.assertEqual(article.select_one('.phone-number span').text,branch.phone)
        self.assertEqual(article.select_one('a[href^="tel:"]')['href'],'tel:00000000000')
        self.assertIsNone(article.select_one('a[href^="https://pf.kakao.com/"]'))
        self.assertEqual([t.text for t in article.select('dt')],['운영시간','주차 안내','기타 안내'])
        self.assertEqual(article.figcaption.text,'TEST <caption>')
        self.assertIsNone(article.select_one('caption, iframe, script'))
        self.assertEqual(article.select_one('.photos img')['loading'],'lazy')
        self.assertIsNone(self.anon.get('/api/v1/branches/').json()['items'][0]['location'])

    def test_post_metadata_uses_public_revision_plain_text_and_safe_attributes(self):
        title='TEST "제목" <meta name="oops"> & 기호'
        post=self.create_post(title=title,body='<p>공개 <b>본</b>문 &amp; 설명</p><p>다음 문단 '+('가😀'*100)+'</p>',cover_image='')
        before=self.api(post); soup=self.soup(post.get_absolute_url())
        description=soup.select_one('meta[name="description"]')['content']
        self.assertTrue(description.startswith('공개 본문 & 설명 다음 문단 '))
        self.assertEqual(len(description),160);self.assertTrue(description.endswith('…'))
        self.assertEqual(soup.title.text,title+' | '+self.site.brand_name)
        self.assertIsNone(soup.select_one('meta[name="oops"]'))
        self.save_draft(post,title='TEST PRIVATE DRAFT',body='<p>TEST PRIVATE BODY</p>')
        after=self.soup(post.get_absolute_url())
        self.assertEqual(after.head,soup.head);self.assertNotIn('TEST PRIVATE',str(after))
        self.assertEqual(self.api(post),before)
        request=RequestFactory().get('/admin/preview/');request.user=self.user
        response=post.get_latest_revision_as_object().serve_preview(request,'')
        preview=BeautifulSoup(response.content,'html.parser')
        self.assertIn('noindex',preview.select_one('meta[name="robots"]')['content'])
        self.assertIn('TEST PRIVATE DRAFT',preview.title.text)
        self.assertEqual(preview.select_one('meta[name="description"]')['content'],'TEST PRIVATE BODY')
        with patch('content.post_models.validate_images',side_effect=ValidationError('TEST')):
            invalid=post.serve_preview(request,'')
        self.assertEqual(invalid.status_code,400)
        self.assertIn('noindex',BeautifulSoup(invalid.content,'html.parser').select_one('meta[name="robots"]')['content'])

    def test_post_headings_filters_pagination_body_lazy_images_and_api_unchanged(self):
        post=self.create_post(body=self.body(self.other_image))
        self.create_post(title='TEST SECOND');self.create_post(category='event')
        soup=self.soup('/posts/?category=notice&page_size=1&page=2')
        self.assertEqual(soup.select_one('.filter-nav [aria-current="page"]').text,'공지사항')
        self.assertEqual(len(soup.select('.post-summary h2')),1)
        self.assertEqual(len(soup.select('.post-summary h3')),0)
        self.assertEqual(soup.select_one('.pagination a')['href'],'/posts/?page=1&page_size=1&category=notice')
        self.assertIn('2 페이지',soup.title.text)
        dto=self.api(post); detail=self.soup(post.get_absolute_url())
        self.assertEqual(detail.select_one('.post-body img')['loading'],'lazy')
        self.assertEqual(detail.select_one('.post-body img')['alt'],'TEST rectangle')
        self.assertIsNotNone(detail.select_one('.post-body b'));self.assertIsNotNone(detail.select_one('.post-body i'))
        self.assertEqual(detail.select_one('.post-body a')['href'],'https://example.com/')
        self.assertNotIn('loading=',dto['body_html'])
        self.assertEqual(detail.select_one('.back-link a')['href'],'/posts/')
        self.assertIn('등록된 게시글이 없습니다.',self.soup('/posts/?page=99999').text)

    def test_errors_and_unready_are_noindex_including_database_failure(self):
        for path,status in [('/missing/',404),('/posts/?page=bad',400)]:
            soup=self.soup(path,status)
            self.assertIn('noindex',soup.select_one('meta[name="robots"]')['content'])
            self.assertIn(self.site.brand_name,soup.title.text)
        for fail_db in [False,True]:
            with patch('content.views.public_shell',side_effect=OperationalError('TEST private DB detail')) if fail_db else patch('content.views.public_shell',wraps=public_shell):
                response=server_error(RequestFactory().get('/'))
            self.assertEqual(response.status_code,500)
            soup=BeautifulSoup(response.content,'html.parser')
            self.assertIn('noindex',soup.select_one('meta[name="robots"]')['content'])
            self.assertNotIn('TEST private DB detail',soup.text)
        SiteContent.objects.all().delete()  # isolated test DB only
        soup=self.soup('/',503)
        self.assertIn('noindex',soup.select_one('meta[name="robots"]')['content'])
        self.assertIsNone(soup.select_one('[data-home-popup], script[src$="popups.js"]'))

    def test_excerpt_does_not_emit_markup_or_join_block_words(self):
        self.assertEqual(excerpt('<h2>제목</h2><p>앞<strong>중간</strong>끝<br>다음</p><script>숨김</script>',html=True),'제목 앞중간끝 다음')
        self.assertEqual(excerpt('TEST <일반 텍스트> & "값"'),'TEST <일반 텍스트> & "값"')
