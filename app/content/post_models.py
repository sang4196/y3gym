from django import forms
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models
from django.shortcuts import render
from wagtail.actions.publish_revision import PublishRevisionAction
from wagtail.actions.unpublish import UnpublishAction
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import DraftStateMixin, RevisionMixin, PreviewableMixin

from .locking import content_transaction
from .post_body import has_body, validate_images
from .widgets import PostRichTextArea

STALE_POST = '다른 저장이나 공개 변경이 먼저 반영되었습니다. 다시 열어 확인하세요.'


class Post(DraftStateMixin, RevisionMixin, PreviewableMixin, models.Model):
    live = models.BooleanField(default=False, editable=False)
    title = models.CharField('제목', max_length=200, blank=True)
    category = models.CharField('분류', max_length=10, choices=[('notice','공지사항'),('event','이벤트')], default='notice')
    body = RichTextField('본문', blank=True, features=['h2','bold','italic','ol','ul','link','image'])
    cover_image = models.ForeignKey('wagtailimages.Image', verbose_name='대표 이미지', null=True, blank=True, on_delete=models.PROTECT, related_name='post_covers')
    cover_alt = models.CharField('대표 이미지 대체 설명', max_length=200, blank=True)
    edit_version = models.PositiveIntegerField(default=0)
    panels = [FieldPanel('edit_version', widget=forms.HiddenInput), FieldPanel('title'), FieldPanel('category'),
              FieldPanel('body', widget=PostRichTextArea, classname='product-post-body'),
              FieldPanel('cover_image', help_text='선택 입력입니다. 본문 이미지는 본문에서 넣습니다.'), FieldPanel('cover_alt')]

    class Meta:
        verbose_name = '공지·이벤트'
        verbose_name_plural = '공지·이벤트'
        permissions = [('publish_post', 'Can publish post')]
        constraints = [models.CheckConstraint(condition=models.Q(category__in=['notice','event']), name='post_fixed_category')]

    def __str__(self):
        return self.title or '제목 없는 초안'

    def clean(self):
        self.title = self.title.strip()
        self.cover_alt = self.cover_alt.strip()
        if self.go_live_at or self.expire_at:
            raise ValidationError('게시글 예약 공개·자동 종료는 제공하지 않습니다.')

    def validate_content(self, *, user=None, public=False):
        self.full_clean()
        images = validate_images(self, user)
        if public:
            if not self.title:
                raise ValidationError('공개하려면 제목이 필요합니다.')
            if not has_body(self):
                raise ValidationError('공개하려면 본문 텍스트 또는 본문 이미지가 필요합니다.')
        return images

    def current_for_write(self):
        current = type(self).objects.filter(pk=self.pk).first() if self.pk else None
        if current and current.edit_version != self.edit_version:
            raise ValidationError(STALE_POST)
        return current

    def save(self, *args, **kwargs):
        with content_transaction():
            current = self.current_for_write()
            # Wagtail's publication actions alone may change publication metadata.
            if not getattr(self, '_publication_write', False):
                for field in ['live', 'live_revision_id', 'first_published_at', 'last_published_at']:
                    expected = getattr(current, field) if current else (False if field == 'live' else None)
                    if getattr(self, field) != expected:
                        raise ValidationError('공개 상태는 공개·철회 동작으로만 변경하세요.')
            self.edit_version += 1
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'edit_version'}
            return super().save(*args, **kwargs)

    def with_content_json(self, content):
        obj = super().with_content_json(content)
        # These belong to the aggregate, not to a historical content revision.
        for field in ['edit_version', 'live_revision_id', 'last_published_at']:
            setattr(obj, field, getattr(self, field))
        return obj

    def save_revision(self, *args, **kwargs):
        if kwargs.get('overwrite_revision') or kwargs.get('approved_go_live_at'):
            raise PermissionDenied('기존 리비전 덮어쓰기·예약 공개는 제공하지 않습니다.')
        with content_transaction():
            self.current_for_write()
            self.validate_content(user=kwargs.get('user'))
            return super().save_revision(*args, **kwargs)

    def publish(self, revision, user=None, changed=True, log_action=True, previous_revision=None, skip_permission_checks=False):
        with content_transaction():
            current = self.current_for_write()
            if not current or revision.pk != current.latest_revision_id or previous_revision is not None:
                raise ValidationError('이전 버전은 먼저 초안으로 복원한 뒤 다시 열어 공개하세요.')
            revision = current.revisions.get(pk=revision.pk)
            candidate = current.with_content_json(revision.content)
            images = candidate.validate_content(user=user, public=True)
            action = PublishRevisionAction(revision, user=user, changed=changed, log_action=log_action)
            action.object = candidate
            candidate._publication_write = True
            action.execute(skip_permission_checks=skip_permission_checks)
            PostImageUse.objects.filter(post_id=self.pk).delete()
            PostImageUse.objects.bulk_create([PostImageUse(post_id=self.pk, revision=revision, image=image) for image in images.values()])
            self.refresh_from_db()

    def unpublish(self, set_expired=False, commit=True, user=None, log_action=True):
        if set_expired or not commit:
            raise ValidationError('예약 종료·부분 철회는 제공하지 않습니다.')
        if user is not None and not user.has_perm('content.publish_post'):
            raise PermissionDenied('게시글 공개·철회 권한이 필요합니다.')
        with content_transaction():
            self.current_for_write()
            self._publication_write = True
            try:
                # Wagtail's generic action expects Page permissions_for_user; snippets use model permissions.
                UnpublishAction(self, user=user, log_action=log_action).execute(skip_permission_checks=True)
                PostImageUse.objects.filter(post_id=self.pk).delete()
            finally:
                self._publication_write = False

    def get_absolute_url(self):
        return f'/posts/{self.pk}/'

    def get_preview_template(self, request, mode_name):
        return 'content/post_detail.html'

    def serve_preview(self, request, mode_name):
        from .post_publication import post_dto
        from .publication import public_shell
        from .presentation import page_meta, post_meta
        with content_transaction(read=True):
            shell = public_shell()
            try:
                images = self.validate_content(user=request.user)
            except ValidationError:
                message = '참조 이미지와 본문을 확인하세요.'
                return render(request, 'content/error.html', {'message': message, 'public_shell': shell,
                              'page': page_meta(message, shell, noindex=True), 'status_code': 400}, status=400)
            post = post_dto(self, images=images, preview=True)
            return render(request, 'content/post_detail.html', {'post': post, 'preview': True, 'public_shell': shell,
                          'page': post_meta(post, shell, preview=True)})


class PostImageUse(models.Model):
    """Derived live-only asset index. Revision is authoritative, not this table."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='public_image_uses')
    revision = models.ForeignKey('wagtailcore.Revision', on_delete=models.PROTECT, related_name='+')
    image = models.ForeignKey('wagtailimages.Image', on_delete=models.PROTECT, related_name='public_post_uses')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['post','image'], name='post_image_use_unique')]
