"""CMS body allowlist and asset selection; no public-reference scans."""
import re
from urllib.parse import urlsplit

import bleach
from bs4 import BeautifulSoup
from django.core.exceptions import PermissionDenied, ValidationError
from wagtail.images import get_image_model
from wagtail.images.permissions import permission_policy


def body_soup(post):
    return BeautifulSoup(str(post.body or ''), 'html.parser')


def image_ids(post):
    ids = {post.cover_image_id} if post.cover_image_id else set()
    for tag in body_soup(post).find_all('embed'):
        value = tag.get('id', '')
        if tag.get('embedtype') != 'image' or not re.fullmatch(r'[0-9]{1,18}', value) or int(value) <= 0:
            raise ValidationError('본문 이미지 참조를 확인하세요.')
        ids.add(int(value))
    return ids


def validate_images(post, user=None):
    ids = image_ids(post)
    images = get_image_model().objects.in_bulk(ids)
    if set(images) != ids:
        raise ValidationError('참조 이미지가 없습니다. 복구하거나 다른 사진을 선택하세요.')
    for image in images.values():
        if user is not None and not permission_policy.user_has_any_permission_for_instance(user, ['choose', 'change'], image):
            raise PermissionDenied('선택 권한이 없는 이미지입니다.')
        if not image.file.storage.exists(image.file.name):
            raise ValidationError('참조 이미지 파일이 없습니다. 복구하거나 다른 사진을 선택하세요.')
    return images


def has_body(post):
    soup = body_soup(post)
    for tag in soup.find_all(['script', 'style', 'img']):
        tag.decompose()
    return bool(soup.get_text(strip=True) or soup.find('embed', embedtype='image'))


def safe_link(href):
    if not href or any(ord(char) < 32 for char in href) or '\\' in href:
        return None
    try:
        parsed = urlsplit(href)
    except ValueError:
        return None
    if parsed.scheme in {'https', 'http'} and parsed.netloc:
        return href
    if parsed.scheme in {'mailto', 'tel'} and parsed.path:
        return href
    if href.startswith('#'):
        return href
    if not parsed.scheme and not parsed.netloc and not parsed.query and (
        re.fullmatch(r'/posts/[0-9]+/', parsed.path) or parsed.path in {'/', '/posts/', '/branches/', '/trainers/'}
    ):
        return href
    return None


def post_image_dto(image, alt='', preview=False):
    from django.conf import settings
    from .publication import image_dto, DISPLAY_FILTER
    if not preview:
        return image_dto(image, alt)
    rendition = image.get_rendition(DISPLAY_FILTER)
    return {'url': settings.PUBLIC_ORIGIN + rendition.url, 'alt': alt, 'width': rendition.width, 'height': rendition.height}


def render_body(post, *, images, preview=False):
    soup = body_soup(post)
    for tag in soup.find_all(['img', 'script', 'style']):
        tag.decompose()
    for tag in soup.find_all('embed'):
        value = tag.get('id', '')
        if tag.get('embedtype') != 'image' or not value.isdecimal() or int(value) not in images:
            tag.decompose()
            continue
        dto = post_image_dto(images[int(value)], tag.get('alt', ''), preview)
        tag.replace_with(soup.new_tag('img', src=dto['url'], alt=dto['alt'], width=str(dto['width']), height=str(dto['height'])))
    for tag in soup.find_all('a'):
        href = None if tag.has_attr('linktype') else safe_link(tag.get('href', ''))
        if href:
            tag.attrs = {'href': href}
        else:
            tag.unwrap()
    return bleach.clean(str(soup), tags={'p','br','h2','strong','em','b','i','ol','ul','li','a','img'},
                        attributes={'a':['href'], 'img':['src','alt','width','height']},
                        protocols={'http','https','mailto','tel'}, strip=True)
