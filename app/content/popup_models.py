from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, HelpPanel
from wagtail.images import get_image_model
from .locking import content_transaction


class Popup(models.Model):
    post = models.OneToOneField('content.Post', verbose_name='연결 게시글', on_delete=models.PROTECT, related_name='popup', error_messages={'unique':'이 게시글의 팝업 설정이 이미 있습니다. 기존 설정을 편집하세요.'})
    title = models.CharField('제목', max_length=200, blank=True)
    message = models.TextField('안내 문구', max_length=1000, blank=True)
    image = models.ForeignKey('wagtailimages.Image', verbose_name='이미지', null=True, blank=True, on_delete=models.PROTECT, related_name='popups')
    image_alt = models.CharField('이미지 대체 설명', max_length=200, blank=True)
    enabled = models.BooleanField('사용', default=False)
    starts_at = models.DateTimeField('시작 일시', null=True, blank=True)
    ends_at = models.DateTimeField('종료 일시', null=True, blank=True)
    priority = models.PositiveIntegerField('우선순위', default=0, help_text='작은 값이 먼저입니다.')
    edit_version = models.PositiveIntegerField(default=0)
    panels = [FieldPanel('edit_version', widget=forms.HiddenInput),
              MultiFieldPanel([FieldPanel(name) for name in ['post','title','message','image','image_alt','enabled','starts_at','ends_at','priority']], heading='기간제 팝업', help_text='저장하면 현재 설정에 즉시 반영됩니다. 연결 게시글의 공개 상태는 바뀌지 않습니다. 일시는 한국 시간입니다.'),
              HelpPanel(template='content/admin/popup_status.html', heading='현재 상태')]

    class Meta:
        verbose_name = '기간제 팝업'
        verbose_name_plural = '기간제 팝업'
        ordering = ['priority', '-starts_at', 'pk']
        constraints = [
            models.CheckConstraint(condition=Q(starts_at__isnull=True)|Q(ends_at__isnull=True)|Q(starts_at__lt=F('ends_at')), name='popup_valid_period'),
            models.CheckConstraint(condition=Q(enabled=False)|(Q(starts_at__isnull=False,ends_at__isnull=False)&~Q(title='')&(~Q(message='')|Q(image__isnull=False))), name='popup_enabled_complete'),
        ]

    def __str__(self):
        return self.title or '준비 중 팝업'

    def clean(self):
        for field in ['title','message','image_alt']:
            setattr(self,field,getattr(self,field).strip())
        errors = {}
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            errors['ends_at'] = '종료 일시는 시작보다 늦어야 합니다.'
        if self.enabled:
            for field, label in [('title','제목'),('starts_at','시작 일시'),('ends_at','종료 일시')]:
                if not getattr(self,field):errors[field]=f'사용하려면 {label}이 필요합니다.'
            if not self.message and not self.image_id:errors['message']='문구 또는 이미지가 필요합니다.'
        if self.image_id:
            image=get_image_model().objects.filter(pk=self.image_id).first()
            if image is None or not image.file.storage.exists(image.file.name):
                errors['image']='참조 이미지와 파일을 확인하세요. 복구하거나 새 자산을 선택하세요.'
        if errors:raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if kwargs.get('update_fields') is not None:
            raise ValidationError('팝업 설정은 전체 편집 단위로 저장하세요.')
        with content_transaction():
            current=type(self).objects.filter(pk=self.pk).first() if self.pk else None
            if current and current.edit_version != self.edit_version:
                raise ValidationError('다른 저장이 먼저 반영되었습니다. 다시 열어 확인하세요.')
            self.full_clean()
            self.edit_version += 1
            return super().save(*args,**kwargs)

    @property
    def display_status(self):
        if not self.enabled:return '비활성'
        if not self.post_id or not self.post.live or not self.post.live_revision_id:return '연결 글 비공개로 중지'
        now=timezone.now()
        if self.starts_at and now < self.starts_at:return '예약'
        if self.ends_at and now >= self.ends_at:return '종료'
        return '노출 가능'
