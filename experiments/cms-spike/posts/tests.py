import platform
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from datetime import datetime

from bs4 import BeautifulSoup
from PIL import Image as PillowImage
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from wagtail.admin.rich_text.converters.contentstate import ContentstateConverter
from wagtail.images import get_image_model
from wagtail.models import Collection
from .models import Post
from .publication import DISPLAY_FILTER
from .test_support import configure_editor, test_png


class CmsSpikeTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        # DB IDs repeat across TestCase transactions; rendition cache must share
        # the same test isolation boundary as DB and per-test storage.
        cache.clear()
        # New run-specific media directory; never delete/initialise another run.
        self.media_dir = Path(tempfile.mkdtemp(prefix="test-media-", dir=settings.RUNTIME))
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.editor = get_user_model().objects.create_user(username="test-editor", is_staff=True)
        self.collection = configure_editor(self.editor)
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.editor)
        self.client.get(reverse("wagtailimages:add"))
        self.anon = Client()
        self.cover = self.upload("cover-public.png", "red")
        self.body_image = self.upload("body-public.png", "blue")
        self.old_body = self.body(self.body_image, "PUBLIC BODY")
        self.a = self.create_post("PUBLIC A", self.old_body, self.cover, publish=True)

    def post(self, path, data):
        return self.client.post(path, data, HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value)

    def upload(self, name, color):
        response = self.post(reverse("wagtailimages:add"), {
            "title": "TEST " + name, "file": test_png(name, color), "collection": self.collection.pk,
        })
        self.assertEqual(response.status_code, 302)
        return get_image_model().objects.latest("pk")

    def body(self, image, text):
        return f'<h2>{text}</h2><p><b>Bold</b> <i>Italic</i> <a href="https://example.com/">Test link</a></p><embed embedtype="image" id="{image.pk}" format="fullwidth" alt="TEST colored rectangle"/>'

    def form_data(self, title, body, cover, publish=False):
        data = {"title": title, "category": "notice", "body": ContentstateConverter(features=["h2", "bold", "italic", "ol", "ul", "link", "image"]).from_database_format(body), "cover_image": cover.pk if cover else ""}
        if publish:
            data["action-publish"] = "Publish"
        return data

    def admin_url(self, action, post=None):
        return reverse(Post.snippet_viewset.get_url_name(action), args=[post.pk] if post else [])

    def create_post(self, title, body, cover, publish=False):
        response = self.post(self.admin_url("add"), self.form_data(title, body, cover, publish))
        self.assertEqual(response.status_code, 302)
        return Post.objects.latest("pk")

    def draft(self):
        cover = self.upload("cover-draft.png", "green")
        body_image = self.upload("body-draft.png", "purple")
        response = self.post(self.admin_url("edit", self.a), self.form_data("DRAFT A", self.body(body_image, "DRAFT BODY"), cover))
        self.assertEqual(response.status_code, 302)
        self.a.refresh_from_db()
        return cover, body_image

    def public_data(self, post=None, client=None):
        response = (client or self.anon).get(reverse("post-json", args=[(post or self.a).pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        return response.json()["data"]

    def image_bytes(self, client, url, expected):
        path = urlsplit(url).path
        response = client.get(path)
        self.assertEqual(response.status_code, expected, path)
        self.assertIn("no-store", response["Cache-Control"])
        if expected == 200:
            data = b"".join(response.streaming_content)
            PillowImage.open(BytesIO(data)).verify()
        else:
            self.assertFalse(response.get("Content-Type", "").startswith("image/"))
        response.close()
        return response

    def test_sp01_cms_create_upload_choose_server(self):
        add = self.client.get(self.admin_url("add"))
        self.assertContains(add, "draftail")
        self.assertContains(add, "action-publish")
        self.assertContains(add, "cover_image")
        chooser = self.client.get(reverse("wagtailimages_chooser:choose"))
        self.assertEqual(chooser.status_code, 200)
        chosen = self.client.get(reverse("wagtailimages_chooser:chosen", args=[self.body_image.pk]))
        self.assertEqual(chosen.status_code, 200)
        self.assertIn("/cms-files/", chosen.content.decode())
        self.assertContains(self.client.get(self.admin_url("list")), "PUBLIC A")
        for rendition in self.body_image.renditions.all():
            self.image_bytes(self.client, rendition.url, 200)

    def test_sp02_first_publish_same_html_json(self):
        data = self.public_data()
        response = self.anon.get(reverse("post-html", args=[self.a.pk]))
        self.assertContains(response, data["title"])
        self.assertContains(response, data["body_html"], html=True)
        self.assertEqual(data["title"], "PUBLIC A")
        self.image_bytes(self.anon, data["cover_image"]["url"], 200)
        for image in BeautifulSoup(data["body_html"], "html.parser").find_all("img"):
            self.image_bytes(self.anon, image["src"], 200)

    def test_sp03_draft_preserves_published_revision(self):
        before = self.public_data()
        html_before = self.anon.get(reverse("post-html", args=[self.a.pk])).content
        live_revision_id = self.a.live_revision_id
        cover, body_image = self.draft()
        self.assertEqual(self.public_data(), before)
        self.assertEqual(self.anon.get(reverse("post-html", args=[self.a.pk])).content, html_before)
        self.assertEqual(self.a.live_revision_id, live_revision_id)
        self.assertNotEqual(self.a.latest_revision_id, live_revision_id)
        for image in (cover, body_image):
            self.image_bytes(self.anon, reverse("display-image", args=[image.pk]), 404)
            self.image_bytes(self.anon, image.file.url, 403)

    def test_sp04_publish_modified_revision(self):
        cover, body_image = self.draft()
        response = self.post(self.admin_url("edit", self.a), self.form_data("DRAFT A", self.body(body_image, "DRAFT BODY"), cover, True))
        self.assertEqual(response.status_code, 302)
        data = self.public_data()
        self.assertEqual(data["title"], "DRAFT A")
        self.assertIn("DRAFT BODY", data["body_html"])
        self.assertContains(self.anon.get(reverse("post-html", args=[self.a.pk])), "DRAFT A")
        self.image_bytes(self.anon, data["cover_image"]["url"], 200)
        # Old assets survive in revisions but no longer authorize public access.
        for old in (self.cover, self.body_image):
            self.image_bytes(self.anon, reverse("display-image", args=[old.pk]), 404)
            self.assertTrue(old.file.storage.exists(old.file.name))

    def test_sp05_authorized_draft_preview_server(self):
        cover, body_image = self.draft()
        url = self.admin_url("preview_on_edit", self.a)
        state = self.post(url, self.form_data("DRAFT A", self.body(body_image, "DRAFT BODY"), cover))
        self.assertEqual(state.status_code, 200)
        self.assertTrue(state.json()["is_valid"])
        response = self.client.get(url)
        self.assertContains(response, "DRAFT A")
        self.assertContains(response, "DRAFT BODY")
        self.assertIn("no-store", response["Cache-Control"])
        for image in BeautifulSoup(response.content, "html.parser").find_all("img"):
            self.image_bytes(self.client, image["src"], 200)
            self.image_bytes(self.anon, image["src"], 403)
        self.assertEqual(self.anon.get(url).status_code, 302)
        self.assertEqual(self.public_data()["title"], "PUBLIC A")

    def test_sp06_private_files_and_bypass_paths(self):
        cover, image = self.draft()
        thumbnail = image.get_rendition("max-165x165")
        display = image.get_rendition(DISPLAY_FILTER)
        for label, url in [("original", image.file.url), ("thumbnail", thumbnail.url), ("rendition", display.url)]:
            self.image_bytes(self.anon, url, 403)
            self.image_bytes(self.client, url, 200)
            print(f"SP-06 {label}: anonymous=403 authorized=200 no-store")
        for name in [image.file.name, thumbnail.file.name, display.file.name]:
            for prefix in ["/media/", "/private-media/", "/.runtime/private-media/"]:
                self.assertEqual(self.anon.get(prefix + name).status_code, 404)
        self.assertEqual(self.anon.get("/cms-files/../secret-key").status_code, 403)
        self.assertEqual(self.client.get("/cms-files/../secret-key").status_code, 404)
        from wagtail.images.utils import generate_signature
        signature = generate_signature(image.pk, "original")
        self.assertEqual(self.anon.get(f"/images/{signature}/{image.pk}/original/test.png").status_code, 404)
        self.image_bytes(self.anon, reverse("display-image", args=[image.pk]), 404)
        preview_url = reverse("wagtailimages:preview", args=[image.pk, "max-165x165"])
        self.assertEqual(self.anon.get(preview_url).status_code, 302)
        self.image_bytes(self.client, preview_url, 200)

    def test_sp07_shared_body_reference_remains_public(self):
        b = self.create_post("PUBLIC B", self.body(self.body_image, "B BODY"), None, True)
        self.post(self.admin_url("unpublish", self.a), {})
        self.a.refresh_from_db()
        self.assertFalse(self.a.live)
        self.image_bytes(self.anon, reverse("display-image", args=[self.body_image.pk]), 200)
        self.assertEqual(self.public_data(b)["title"], "PUBLIC B")

    def test_sp08_last_reference_revoked_old_url_and_republish(self):
        b = self.create_post("PUBLIC B", self.body(self.body_image, "B BODY"), None, True)
        url = reverse("display-image", args=[self.body_image.pk])
        self.image_bytes(self.anon, url, 200)
        for post in (self.a, b):
            response = self.post(self.admin_url("unpublish", post), {})
            self.assertEqual(response.status_code, 302)
            post.refresh_from_db()
            self.assertFalse(post.live)
            self.assertEqual(self.anon.get(reverse("post-json", args=[post.pk])).status_code, 404)
        self.image_bytes(self.anon, url, 404)
        self.image_bytes(self.client, url, 404)
        b.get_latest_revision().publish(user=self.editor)
        self.image_bytes(self.anon, url, 200)

    def test_sp09_admin_session_public_scope_unchanged(self):
        self.draft()
        draft = self.create_post("NEVER PUBLIC", self.old_body, self.cover)
        self.assertEqual(self.public_data(client=self.client), self.public_data())
        html = reverse("post-html", args=[self.a.pk])
        self.assertEqual(self.client.get(html).content, self.anon.get(html).content)
        self.assertEqual(set(self.public_data()), {"id", "title", "category", "body_html", "cover_image"})
        for client in (self.client, self.anon):
            for endpoint in ("post-html", "post-json"):
                self.assertEqual(client.get(reverse(endpoint, args=[draft.pk])).status_code, 404)

    def test_sp10_overwrite_delete_blocked_new_asset_allowed(self):
        original = Path(self.cover.file.path).read_bytes()
        response = self.post(reverse("wagtailimages:edit", args=[self.cover.pk]), {"title": "TEST overwrite", "collection": self.collection.pk, "file": test_png("replacement.png", "black")})
        self.assertContains(response, "Existing image files cannot be replaced")
        self.assertEqual(Path(self.cover.file.path).read_bytes(), original)
        for endpoint in ["delete", "delete_multiple"]:
            url = reverse("wagtailimages:" + endpoint, args=[self.cover.pk])
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.post(url, {}).status_code, 403)
        bulk = reverse("wagtail_bulk_action", args=["wagtailimages", "image", "delete"])
        self.assertEqual(self.post(bulk + f"?id={self.cover.pk}", {}).status_code, 403)
        self.assertTrue(get_image_model().objects.filter(pk=self.cover.pk).exists())
        self.assertNotContains(self.client.get(reverse("wagtailimages:edit", args=[self.cover.pk])), f'/images/{self.cover.pk}/delete/')
        self.assertNotContains(self.client.get(reverse("wagtailimages:index")), '/bulk/wagtailimages/image/delete/')
        replacement = self.upload("replacement.png", "black")
        self.assertNotEqual(replacement.pk, self.cover.pk)
        self.assertEqual(self.post(self.admin_url("edit", self.a), self.form_data("NEW COVER", self.old_body, replacement, True)).status_code, 302)
        self.assertIn(str(replacement.pk), self.public_data()["cover_image"]["url"])

    def test_sp11_json_body_rendering_and_links_server(self):
        body = self.public_data()["body_html"]
        soup = BeautifulSoup(body, "html.parser")
        self.assertEqual(soup.a["href"], "https://example.com/")
        self.assertIsNotNone(soup.find(["b", "strong"]))
        self.assertIsNotNone(soup.find(["i", "em"]))
        for forbidden in ["<embed", "embedtype=", "linktype=", "/admin/", "/cms-files/", str(settings.BASE_DIR)]:
            self.assertNotIn(forbidden, body)
        self.image_bytes(self.anon, soup.img["src"], 200)

    def test_sp12_linux_paths_timezone_and_image_conversion(self):
        self.assertEqual(platform.system(), "Linux")
        self.assertIn("microsoft", platform.release().lower())
        self.assertTrue(Path(sys.prefix).is_relative_to(settings.BASE_DIR))
        self.assertEqual(datetime(2026, 9, 18, tzinfo=ZoneInfo("Asia/Seoul")).utcoffset().total_seconds(), 32400)
        upper = self.media_dir / "CaseCheck.txt"
        upper.write_text("SPIKE TEST", encoding="utf-8")
        self.assertFalse((self.media_dir / "casecheck.txt").exists())
        rendition = self.body_image.get_rendition(DISPLAY_FILTER)
        with PillowImage.open(rendition.file.path) as image:
            self.assertEqual(image.size, (800, 600))
            self.assertEqual(image.format, "PNG")
        self.assertTrue(Path(rendition.file.path).is_relative_to(self.media_dir))

    def test_collection_permission_is_not_just_staff_login(self):
        other = get_user_model().objects.create_user(username="unprivileged-staff", is_staff=True)
        other.user_permissions.add(Permission.objects.get(content_type__app_label="wagtailadmin", codename="access_admin"))
        unauthorized = Client()
        unauthorized.force_login(other)
        self.image_bytes(unauthorized, self.cover.file.url, 403)
        denied = unauthorized.get(self.admin_url("preview_on_edit", self.a))
        self.assertEqual(denied.status_code, 302)
        self.assertEqual(denied["Location"], "/admin/")
        private_collection = Collection.get_first_root_node().add_child(name="No editor permission")
        hidden = get_image_model().objects.create(title="PRIVATE COLLECTION", collection=private_collection, file=test_png("no-access.png", "gray"))
        self.image_bytes(self.client, hidden.file.url, 403)
        chosen = self.client.get(reverse("wagtailimages_chooser:chosen", args=[hidden.pk]))
        self.assertEqual(chosen.status_code, 302)
        self.assertEqual(chosen["Location"], "/admin/")
        before = self.public_data()
        forged = self.post(self.admin_url("edit", self.a), self.form_data("FORGED", self.body(hidden, "HIDDEN"), hidden, True))
        self.assertContains(forged, "Every selected image requires collection permission")
        self.assertEqual(self.public_data(), before)

    def test_post_delete_denied_and_csrf_enforced(self):
        response = self.post(self.admin_url("delete", self.a), {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/admin/")
        self.assertTrue(Post.objects.filter(pk=self.a.pk).exists())
        response = self.client.post(self.admin_url("edit", self.a), self.form_data("NO CSRF", self.old_body, self.cover))
        self.assertEqual(response.status_code, 403)

    def test_multiple_upload_and_chooser_upload(self):
        response = self.post(reverse("wagtailimages:add_multiple"), {"files[]": test_png("multi-upload.png", "orange"), "collection": self.collection.pk})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        image = get_image_model().objects.latest("pk")
        self.image_bytes(self.client, image.file.url, 200)
        self.image_bytes(self.anon, image.file.url, 403)
        chooser_response = self.post(reverse("wagtailimages_chooser:create"), {"image-chooser-upload-title": "CHOOSER TEST", "image-chooser-upload-file": test_png("chooser-upload.png", "brown"), "image-chooser-upload-collection": self.collection.pk})
        self.assertEqual(chooser_response.status_code, 200)
        self.assertEqual(chooser_response.json()["step"], "chosen")
        image = get_image_model().objects.latest("pk")
        self.assertEqual(image.title, "CHOOSER TEST")
        for rendition in image.renditions.all():
            self.image_bytes(self.client, rendition.url, 200)
            self.image_bytes(self.anon, rendition.url, 403)

    def test_output_sanitization_and_public_methods(self):
        from .publication import render_body
        from django.test import RequestFactory
        post = Post(title="TEST", category="notice", body='<p onclick="evil()">Text <a href="javascript:alert(1)">unsafe</a><a href="/admin/">admin</a><script>evil()</script><img src="file:///secret"></p>')
        body = render_body(post, RequestFactory().get("/"))
        for forbidden in ["onclick", "javascript:", "<script", "file:", "/admin/"]:
            self.assertNotIn(forbidden, body)
        for endpoint in ("post-html", "post-json"):
            self.assertEqual(self.anon.post(reverse(endpoint, args=[self.a.pk])).status_code, 405)
