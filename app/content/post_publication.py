"""Bounded public queries; the actual live Revision supplies all post content."""
import re
from django.http import Http404
from wagtail.images import get_image_model
from .locking import content_transaction
from .models import Post
from .post_body import image_ids, post_image_dto, render_body


def timestamp(value):
    return value.isoformat().replace('+00:00', 'Z') if value else None


def post_dto(post, *, images=None, detail=True, preview=False):
    if images is None:
        images = get_image_model().objects.in_bulk(image_ids(post))
    cover = images.get(post.cover_image_id)
    data = {
        'id': str(post.pk), 'category': post.category, 'title': post.title,
        'cover_image': post_image_dto(cover, post.cover_alt, preview) if cover else None,
        'published_at': timestamp(post.first_published_at), 'detail_path': post.get_absolute_url(),
    }
    if detail:
        data.update(body_html=render_body(post, images=images, preview=preview), updated_at=timestamp(post.last_published_at))
    return data


def public_posts(category=None):
    query = Post.objects.filter(live=True, live_revision__isnull=False).select_related('live_revision')
    if category:
        query = query.filter(live_revision__content__category=category)
    return query.order_by('-first_published_at', '-pk')


def parse_query(query):
    if set(query) - {'category', 'page', 'page_size'} or any(len(query.getlist(key)) != 1 for key in query):
        raise ValueError('Unknown or repeated query')
    category = query.get('category')
    if category is not None and category not in {'notice', 'event'}:
        raise ValueError('Invalid category')
    values = []
    for key, default in [('page', '1'), ('page_size', '10')]:
        raw = query.get(key, default)
        if not re.fullmatch(r'[0-9]+', raw):
            raise ValueError('Positive integer required')
        value = int(raw)
        if value < 1:
            raise ValueError('Positive integer required')
        values.append(value)
    page, page_size = values
    if page_size > 50:
        raise ValueError('Maximum page size is 50')
    return category, page, page_size


def recent_posts():
    # Caller holds the shared content lock through complete home materialization.
    return [post_dto(row.live_revision.as_object(), detail=False) for row in public_posts()[:3]]


def posts_snapshot(category=None, page=1, page_size=10):
    with content_transaction(read=True):
        query = public_posts(category)
        total = query.count()
        offset = (page - 1) * page_size
        # No enormous SQL OFFSET even for a valid very distant page.
        rows = query[offset:offset + page_size] if offset < total else []
        return {
            'items': [post_dto(row.live_revision.as_object(), detail=False) for row in rows],
            'pagination': {'page': page, 'page_size': page_size, 'total': total, 'has_next': offset + page_size < total},
        }


def post_snapshot(pk):
    with content_transaction(read=True):
        row = public_posts().filter(pk=pk).first()
        if row is None:
            raise Http404
        return post_dto(row.live_revision.as_object())
