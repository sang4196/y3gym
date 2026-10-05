"""Public UI cache keys; no database or browser-rendering claims."""
import hashlib
import os
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from django.core.management import call_command
from django.template import Context, Template, TemplateSyntaxError
from django.templatetags.static import static
from django.test import SimpleTestCase, RequestFactory, override_settings
from django.contrib.staticfiles.views import serve as serve_source
from django.views.static import serve as serve_collected
from .templatetags.public_assets import PUBLIC_ASSETS, public_static


class PublicAssetTests(SimpleTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'source'
        self.target = Path(self.temp.name) / 'collected'
        self.source.mkdir()
        for name in PUBLIC_ASSETS:
            (self.source / name).write_bytes(b'/* old UI */')
        self.settings_override = override_settings(
            STATICFILES_DIRS=[self.source], STATIC_ROOT=self.target,
            STATICFILES_FINDERS=['django.contrib.staticfiles.finders.FileSystemFinder'],
            STATIC_URL='/static/',
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

    def rendered_url(self, name):
        return Template("{% load public_assets %}{% public_static name %}").render(Context({'name': name}))

    def body(self, response):
        try:
            return b''.join(response.streaming_content)
        finally:
            response.close()

    def test_same_size_same_timestamp_edit_replaces_cached_url_without_restart(self):
        asset = self.source / 'site.css'
        old_url = self.rendered_url('site.css')
        old_body = asset.read_bytes()
        browser_cache = {old_url: old_body}
        timestamp = asset.stat()
        asset.write_bytes(b'/* new UI */')
        os.utime(asset, ns=(timestamp.st_atime_ns, timestamp.st_mtime_ns))
        new_url = self.rendered_url('site.css')
        self.assertNotEqual(old_url, new_url)
        self.assertNotIn(new_url, browser_cache)
        request = RequestFactory().get(new_url)
        body = self.body(serve_source(request, 'site.css', insecure=True))
        self.assertEqual(body, b'/* new UI */')
        self.assertEqual(browser_cache[old_url], old_body)
        self.assertEqual(self.rendered_url('site.css'), new_url)

    def test_every_public_asset_version_matches_content_and_collected_response(self):
        call_command('collectstatic', interactive=False, verbosity=0)
        for name in PUBLIC_ASSETS:
            with self.subTest(name=name):
                url = self.rendered_url(name)
                parsed = urlsplit(url)
                response = serve_collected(RequestFactory().get(url), name, document_root=self.target)
                self.assertEqual(response.status_code, 200)
                body = self.body(response)
                self.assertEqual(body, (self.source / name).read_bytes())
                self.assertEqual(parse_qs(parsed.query)['v'], [hashlib.sha256(body).hexdigest()])
                self.assertEqual(parsed.path, '/static/' + name)

    def test_unrelated_admin_static_urls_are_unchanged(self):
        self.assertEqual(static('wagtailadmin/css/core.css'), '/static/wagtailadmin/css/core.css')

    def test_missing_or_unapproved_path_never_falls_back_to_an_unversioned_url(self):
        for name in ['../private-file', 'wagtailadmin/css/core.css', 'unknown.js']:
            with self.assertRaises(TemplateSyntaxError):
                public_static(name)
        (self.source / 'navigation.js').unlink()
        with self.assertRaises(TemplateSyntaxError):
            public_static('navigation.js')
