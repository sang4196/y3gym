import re
from django import forms
from urllib.parse import urlsplit
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, F
from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.models import Orderable
from .locking import content_transaction

SAVE_NOTICE = '저장하면 공개 중인 내용에 즉시 반영됩니다.'

def image_field(label, related):
    return models.ForeignKey('wagtailimages.Image', verbose_name=label, null=True, blank=True, on_delete=models.PROTECT, related_name=related)

def strip_text(instance):
    for field in instance._meta.fields:
        if isinstance(field, (models.CharField, models.TextField)):
            setattr(instance, field.name, getattr(instance, field.name).strip())

def check_image(image):
    if image and not image.file.storage.exists(image.file.name):
        raise ValidationError('참조 이미지 파일이 없습니다. 복구 후 저장해 주세요.')

class SiteContent(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    edit_version = models.PositiveIntegerField(default=0)
    brand_name = models.CharField('브랜드명', max_length=100)
    logo = image_field('로고', 'site_logos')
    logo_alt = models.CharField('로고 대체 설명', max_length=200, blank=True)
    hero_title = models.CharField('대표 소개 제목', max_length=160, blank=True)
    hero_description = models.TextField('대표 소개 문구', max_length=2000, blank=True)
    hero_image = image_field('대표 사진', 'site_heroes')
    hero_alt = models.CharField('대표 사진 대체 설명', max_length=200, blank=True)
    introduction = models.TextField('소개 문구', max_length=5000, blank=True)
    introduction_image = image_field('소개 사진', 'site_introductions')
    introduction_alt = models.CharField('소개 사진 대체 설명', max_length=200, blank=True)
    panels = [FieldPanel('edit_version', widget=forms.HiddenInput), MultiFieldPanel([FieldPanel(x) for x in ['brand_name','logo','logo_alt','hero_title','hero_description','hero_image','hero_alt','introduction','introduction_image','introduction_alt']], heading='홈페이지 기본 정보', help_text=SAVE_NOTICE)]
    class Meta:
        verbose_name = '홈페이지 기본 정보'
        verbose_name_plural = '홈페이지 기본 정보'
        constraints = [models.CheckConstraint(condition=Q(id=1), name='single_site_content')]
    def __str__(self):
        return self.brand_name or '홈페이지 기본 정보'
    def clean(self):
        strip_text(self)
        if not self.brand_name:
            raise ValidationError({'brand_name': '브랜드명을 입력하세요.'})
        for name in ['logo','hero_image','introduction_image']:
            check_image(getattr(self,name))
    def save(self, *args, **kwargs):
        if kwargs.get('update_fields') is not None:
            raise ValidationError('콘텐츠는 부모 편집 단위 전체로 저장해야 합니다.')
        with content_transaction():
            current = type(self).objects.filter(pk=1).first()
            if current and (self._state.adding or current.edit_version != self.edit_version):
                raise ValidationError('다른 저장이 먼저 반영되었습니다. 다시 열어 확인하세요.')
            self.pk = 1
            self.full_clean()
            self.edit_version += 1
            return super().save(*args, **kwargs)

class Branch(ClusterableModel):
    name = models.CharField('지점명', max_length=100, blank=True)
    edit_version = models.PositiveIntegerField(default=0)
    is_public = models.BooleanField('공개', default=False, help_text='최초 공개는 본점으로 지정됩니다. 공개 후 저장은 즉시 반영됩니다.')
    is_main = models.BooleanField('본점', default=False, help_text='공개 지점을 본점으로 지정하면 기존 본점 지정이 함께 해제됩니다.')
    sort_order = models.PositiveIntegerField('표시 순서', default=0)
    summary = models.TextField('짧은 소개', max_length=1000, blank=True)
    cover_image = image_field('대표 사진', 'branch_covers')
    cover_alt = models.CharField('대표 사진 대체 설명', max_length=200, blank=True)
    address = models.CharField('기본 주소', max_length=255, blank=True)
    address_detail = models.CharField('상세 주소', max_length=255, blank=True)
    phone = models.CharField('전화번호', max_length=30, blank=True)
    kakao_channel_url = models.URLField('카카오톡 채널', max_length=300, blank=True)
    business_hours = models.TextField('운영시간', max_length=1000, blank=True)
    closed_days = models.CharField('휴무 안내', max_length=255, blank=True)
    parking_info = models.TextField('주차 안내', max_length=2000, blank=True)
    usage_notes = models.TextField('기타 이용안내', max_length=5000, blank=True)
    class Meta:
        ordering = ['-is_main', 'sort_order', 'id']
        verbose_name = '지점'
        verbose_name_plural = '지점'
        constraints = [models.UniqueConstraint(fields=['is_main'], condition=Q(is_main=True), name='one_main_branch'), models.CheckConstraint(condition=Q(is_main=False)|Q(is_public=True), name='main_must_be_public')]
    def validate_constraints(self, exclude=None):
        # The old main is cleared under the content lock before the DB constraint runs.
        # Form-time validation must allow that atomic transition.
        pass
    def __str__(self):
        return self.name or f'비공개 준비 지점 {self.pk or ""}'
    def clean(self):
        strip_text(self)
        errors = {}
        if self.phone and not re.fullmatch(r'\+?[0-9][0-9 ()-]{5,28}[0-9]', self.phone):
            errors['phone'] = '숫자·공백·괄호·하이픈으로 전화번호를 입력하세요.'
        if self.kakao_channel_url:
            url = urlsplit(self.kakao_channel_url)
            if url.scheme != 'https' or url.netloc != 'pf.kakao.com' or not re.fullmatch(r'/[A-Za-z0-9_-]+', url.path) or url.query or url.fragment:
                errors['kakao_channel_url'] = 'https://pf.kakao.com/채널ID 형식의 채널 주소를 입력하세요.'
        if self.is_public:
            if not self.name: errors['name'] = '공개하려면 지점명이 필요합니다.'
            if not self.address: errors['address'] = '공개하려면 기본 주소가 필요합니다.'
            if not self.phone and not self.kakao_channel_url: errors['phone'] = '공개하려면 전화 또는 카카오톡 연락수단이 필요합니다.'
        if errors: raise ValidationError(errors)
        check_image(self.cover_image)
    def save(self, *args, **kwargs):
        if kwargs.get('update_fields') is not None:
            raise ValidationError('콘텐츠는 부모 편집 단위 전체로 저장해야 합니다.')
        with content_transaction():
            cls = type(self)
            current = cls.objects.filter(pk=self.pk).first() if self.pk else None
            if current and current.edit_version != self.edit_version:
                raise ValidationError('다른 저장이 먼저 반영되었습니다. 다시 열어 확인하세요.')
            others = cls.objects.filter(is_public=True).exclude(pk=self.pk)
            if current and current.is_public and not self.is_public and not others.exists():
                raise ValidationError('마지막 공개 지점은 비공개로 바꿀 수 없습니다.')
            replacement = getattr(self, '_replacement_main_id', None)
            if current and current.is_main and not self.is_public:
                target = others.filter(pk=replacement).first() if replacement else None
                if not target:
                    raise ValidationError('본점을 비공개로 바꾸려면 다른 공개 지점을 새 본점으로 선택하세요.')
                cls.objects.filter(pk=current.pk).update(is_main=False)
                cls.objects.filter(pk=target.pk).update(is_main=True, edit_version=F('edit_version')+1)
                self.is_main = False
            elif self.is_public and not others.exists():
                self.is_main = True
            elif current and current.is_main and not self.is_main:
                raise ValidationError('다른 공개 지점에서 본점을 지정하거나 비공개 전환 시 새 본점을 선택하세요.')
            if not self.is_public and self.is_main:
                raise ValidationError('비공개 지점을 본점으로 지정할 수 없습니다.')
            if self.is_main:
                cls.objects.filter(is_main=True).exclude(pk=self.pk).update(is_main=False, edit_version=F('edit_version')+1)
            self.full_clean()
            # Form-time checks are deferred, but every model constraint is
            # validated against the final state under the exclusive lock.
            super().validate_constraints()
            for photo in self.photos.all():
                if photo.pk and BranchPhoto.objects.filter(pk=photo.pk).exclude(branch_id=self.pk).exists():
                    raise ValidationError('다른 지점의 시설 사진 배치를 수정할 수 없습니다.')
                photo.full_clean(exclude=['branch'])
            self.edit_version += 1
            result = super().save(*args, **kwargs)
            if cls.objects.filter(is_public=True).exists() and cls.objects.filter(is_public=True, is_main=True).count() != 1:
                raise ValidationError('공개 본점은 정확히 하나여야 합니다.')
            return result

class BranchPhoto(Orderable):
    branch = ParentalKey(Branch, related_name='photos', on_delete=models.CASCADE)
    image = models.ForeignKey('wagtailimages.Image', verbose_name='시설 사진', on_delete=models.PROTECT, related_name='branch_photos')
    caption = models.CharField('사진 설명', max_length=255, blank=True)
    alt = models.CharField('대체 설명', max_length=200, blank=True)
    panels = [FieldPanel('image'), FieldPanel('caption'), FieldPanel('alt')]
    class Meta(Orderable.Meta):
        ordering = ['sort_order', 'id']
    def clean(self):
        strip_text(self)
        if self.image_id: check_image(self.image)


class Trainer(ClusterableModel):
    branch = models.ForeignKey(Branch, verbose_name='소속 지점', related_name='trainers', on_delete=models.PROTECT)
    name = models.CharField('이름', max_length=100, blank=True)
    edit_version = models.PositiveIntegerField(default=0)
    job_title = models.CharField('직급', max_length=100, blank=True, help_text='선택 입력입니다. 표시 순서나 권한에 영향을 주지 않습니다.')
    profile_image = image_field('프로필 사진', 'trainer_profiles')
    profile_alt = models.CharField('프로필 사진 대체 설명', max_length=200, blank=True)
    short_intro = models.CharField('한줄소개', max_length=300, blank=True)
    is_public = models.BooleanField('공개', default=False, help_text='소속 지점도 공개일 때 표시됩니다. 비공개로 바꾸면 기존 소개도 고객 화면에서 사라집니다.')
    sort_order = models.PositiveIntegerField('지점 내 표시 순서', default=0)

    panels = [
        FieldPanel('edit_version', widget=forms.HiddenInput),
        MultiFieldPanel([FieldPanel(x) for x in ['branch', 'name', 'job_title', 'profile_image', 'profile_alt', 'short_intro', 'is_public', 'sort_order']], heading='트레이너 소개', help_text=SAVE_NOTICE),
        InlinePanel('careers', label='약력'),
    ]

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = '트레이너'
        verbose_name_plural = '트레이너'
        constraints = [models.CheckConstraint(
            condition=Q(is_public=False) | (Q(profile_image__isnull=False) & ~Q(name='') & ~Q(short_intro='')),
            name='public_trainer_required_fields',
        )]

    def __str__(self):
        return self.name or f'비공개 준비 트레이너 {self.pk or ""}'

    def clean(self):
        strip_text(self)
        if self.is_public:
            errors = {}
            for field, label in [('name', '이름'), ('branch_id', '소속 지점'), ('profile_image_id', '프로필 사진'), ('short_intro', '한줄소개')]:
                if not getattr(self, field):
                    errors[field.removesuffix('_id')] = f'공개하려면 {label} 항목이 필요합니다.'
            if errors:
                raise ValidationError(errors)
        check_image(self.profile_image)

    def save(self, *args, **kwargs):
        if kwargs.get('update_fields') is not None:
            raise ValidationError('콘텐츠는 부모 편집 단위 전체로 저장해야 합니다.')
        with content_transaction():
            current = type(self).objects.filter(pk=self.pk).first() if self.pk else None
            if current and current.edit_version != self.edit_version:
                raise ValidationError('다른 저장이 먼저 반영되었습니다. 다시 열어 확인하세요.')
            self.full_clean()
            for career in self.careers.all():
                if career.pk and TrainerCareer.objects.filter(pk=career.pk).exclude(trainer_id=self.pk).exists():
                    raise ValidationError('다른 트레이너의 약력을 수정할 수 없습니다.')
                career.full_clean(exclude=['trainer'])
            self.edit_version += 1
            return super().save(*args, **kwargs)


class TrainerCareer(Orderable):
    class Category(models.TextChoices):
        EDUCATION = 'education', '학력'
        AWARD = 'award', '수상경력'
        CERTIFICATION = 'certification', '자격증'
        EXPERIENCE = 'experience', '주요 경력'

    trainer = ParentalKey(Trainer, related_name='careers', on_delete=models.CASCADE)
    category = models.CharField('구분', max_length=20, choices=Category.choices)
    text = models.CharField('약력 내용', max_length=500)
    panels = [FieldPanel('category'), FieldPanel('text')]

    class Meta(Orderable.Meta):
        ordering = ['sort_order', 'id']
        verbose_name = '약력'
        verbose_name_plural = '약력'
        constraints = [
            models.CheckConstraint(condition=Q(category__in=['education', 'award', 'certification', 'experience']), name='trainer_career_fixed_category'),
            models.CheckConstraint(condition=~Q(text=''), name='trainer_career_nonempty_text'),
        ]

    def clean(self):
        strip_text(self)
        if not self.text:
            raise ValidationError({'text': '약력 내용을 입력하거나 빈 항목을 제거하세요.'})

# Forms are imported lazily by Wagtail after app initialization.
from django import forms
Branch.panels = [FieldPanel('edit_version', widget=forms.HiddenInput), MultiFieldPanel([FieldPanel(x) for x in ['name','is_public','is_main','replacement_main','sort_order']], heading='공개와 본점', help_text=SAVE_NOTICE), MultiFieldPanel([FieldPanel(x) for x in ['summary','cover_image','cover_alt','address','address_detail','phone','kakao_channel_url','business_hours','closed_days','parking_info','usage_notes']], heading='지점 안내', help_text='지도 연동은 준비 중입니다. 주소와 연락처는 표시됩니다.'), InlinePanel('photos', label='시설 사진')]

from .post_models import Post, PostImageUse

from .popup_models import Popup
