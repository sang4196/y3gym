from django.utils import timezone
from .locking import content_transaction
from .models import Popup
from .post_publication import timestamp


def active_popups(now):
    return Popup.objects.filter(enabled=True, starts_at__lte=now, ends_at__gt=now, post__live=True, post__live_revision__isnull=False)


def popup_dto(popup):
    from .publication import image_dto, optional
    post=popup.post
    return {'id':str(popup.pk), 'title':popup.title, 'message':optional(popup.message),
            'image':image_dto(popup.image,popup.image_alt), 'starts_at':timestamp(popup.starts_at), 'ends_at':timestamp(popup.ends_at),
            'post':{'id':str(post.pk), 'title':post.live_revision.content['title'], 'detail_path':post.get_absolute_url()}}


def popups_snapshot():
    with content_transaction(read=True):
        now=timezone.now()
        rows=active_popups(now).select_related('post__live_revision','image').order_by('priority','-starts_at','pk')
        return {'items':[popup_dto(popup) for popup in rows], 'meta':{'server_time':timestamp(now)}}
