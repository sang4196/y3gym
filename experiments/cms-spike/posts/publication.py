"""One published revision selector and one representation for HTML/JSON.

O(n) live-reference scans are intentional for this tiny SQLite experiment.
This is not a production media authorization index.
"""
from urllib.parse import urlsplit
import bleach
from bs4 import BeautifulSoup
from django.http import Http404
from django.urls import reverse
from wagtail.images import get_image_model
from .models import Post

DISPLAY_FILTER = "max-800x600|format-png"


def public_posts():
    return Post.objects.filter(live=True, live_revision__isnull=False).select_related("live_revision")


def published_post(pk):
    try:
        record = public_posts().get(pk=pk)
    except Post.DoesNotExist as error:
        raise Http404 from error
    return record.live_revision.as_object()


def body_source(post):
    return str(post.body or "")


def image_ids(post):
    ids = {post.cover_image_id} if post.cover_image_id else set()
    soup = BeautifulSoup(body_source(post), "html.parser")
    for tag in soup.find_all("embed", embedtype="image"):
        value = tag.get("id", "")
        if value.isdecimal():
            ids.add(int(value))
    return ids


def is_public_image(image_id):
    return any(image_id in image_ids(row.live_revision.as_object()) for row in public_posts())


def image_dto(image_id, request, preview=False, alt=""):
    image = get_image_model().objects.get(pk=image_id)
    rendition = image.get_rendition(DISPLAY_FILTER)
    url = rendition.url if preview else reverse("display-image", args=[image_id])
    return {"url": request.build_absolute_uri(url), "alt": alt, "width": rendition.width, "height": rendition.height}


def safe_link(href):
    parsed = urlsplit(href)
    if parsed.scheme in {"https", "http"} and parsed.netloc:
        return href
    if parsed.scheme in {"mailto", "tel"}:
        return href
    if href.startswith("#"):
        return href
    # Only this experiment's public routes are valid internal destinations.
    if href.startswith("/spike/posts/") and not parsed.netloc:
        return href
    return None


def render_body(post, request, preview=False):
    soup = BeautifulSoup(body_source(post), "html.parser")
    # Raw image URLs cannot bypass CMS asset selection/authorization.
    for raw_image in soup.find_all("img"):
        raw_image.decompose()
    for tag in soup.find_all("embed"):
        if tag.get("embedtype") != "image" or not tag.get("id", "").isdecimal():
            tag.decompose()
            continue
        dto = image_dto(int(tag["id"]), request, preview, tag.get("alt", ""))
        image = soup.new_tag("img", src=dto["url"], alt=dto["alt"], width=str(dto["width"]), height=str(dto["height"]))
        tag.replace_with(image)
    for tag in soup.find_all("a"):
        # CMS page/document links have no public route in this Post-only spike.
        href = None if tag.has_attr("linktype") else safe_link(tag.get("href", ""))
        if href:
            tag.attrs = {"href": href}
        else:
            tag.unwrap()
    return bleach.clean(
        str(soup), tags={"p", "br", "h2", "strong", "em", "b", "i", "ol", "ul", "li", "a", "img"},
        attributes={"a": ["href"], "img": ["src", "alt", "width", "height"]},
        protocols={"http", "https", "mailto", "tel"}, strip=True,
    )


def serialize_post(post, request, preview=False):
    return {
        "id": str(post.pk), "title": post.title, "category": post.category,
        "body_html": render_body(post, request, preview),
        "cover_image": image_dto(post.cover_image_id, request, preview) if post.cover_image_id else None,
    }
