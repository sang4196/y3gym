"""Shared public projection. No sessions, revisions, raw storage URLs or O(n) asset scans."""
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Exists, OuterRef, Prefetch, F
from wagtail.images import get_image_model
from .models import SiteContent, Branch, BranchPhoto, Trainer, TrainerCareer, PostImageUse
from .locking import content_transaction
from .google_maps import map_dto

DISPLAY_FILTER = 'max-1200x900|format-png'

def public_shell():
    """HTML-only scalars, an optional logo and at most two contact target IDs."""
    with content_transaction(read=True):
        site = SiteContent.objects.values('brand_name', 'logo_id', 'logo_alt', 'logo__width', 'logo__height').first()
        has_trainers = Trainer.objects.filter(is_public=True, branch__is_public=True).exists()
        branch_ids = list(Branch.objects.filter(is_public=True).values_list('pk', flat=True)[:2])
        return shell_dto(site, has_trainers, branch_ids)

def shell_dto(site, has_trainers, branch_ids):
    brand = site['brand_name'] if site else ''
    logo = None
    if brand and site['logo_id']:
        # The protected display route keeps the original aspect ratio. No rendition
        # or storage URL is needed merely to build navigation.
        logo = {'url': f"/images/display/{site['logo_id']}/", 'alt': site['logo_alt'],
                'width': site['logo__width'], 'height': site['logo__height']}
    contact_path = None
    if branch_ids:
        contact_path = f'/branches/#branch-{branch_ids[0]}' if len(branch_ids) == 1 else '/branches/'
    return {'brand_name': brand, 'logo': logo, 'has_trainers': has_trainers, 'contact_path': contact_path}

def public_images():
    from .popup_publication import active_popups
    # Callers hold the shared content lock before this request-time decision.
    now = timezone.now()
    popups = active_popups(now).filter(image_id=OuterRef('pk'))
    site = SiteContent.objects.exclude(brand_name='').filter(Q(logo_id=OuterRef('pk'))|Q(hero_image_id=OuterRef('pk'))|Q(introduction_image_id=OuterRef('pk')))
    branches = Branch.objects.filter(is_public=True, cover_image_id=OuterRef('pk'))
    photos = BranchPhoto.objects.filter(branch__is_public=True, image_id=OuterRef('pk'))
    trainers = Trainer.objects.filter(is_public=True, branch__is_public=True, profile_image_id=OuterRef('pk'))
    posts = PostImageUse.objects.filter(post__live=True, revision_id=F('post__live_revision_id'), image_id=OuterRef('pk'))
    return get_image_model().objects.alias(site_use=Exists(site), branch_use=Exists(branches), photo_use=Exists(photos), trainer_use=Exists(trainers), post_use=Exists(posts), popup_use=Exists(popups)).filter(Q(site_use=True)|Q(branch_use=True)|Q(photo_use=True)|Q(trainer_use=True)|Q(post_use=True)|Q(popup_use=True))

def image_dto(image, alt=''):
    if image is None: return None
    # URLs are stable public display routes; generating JSON never emits storage URLs.
    rendition = image.get_rendition(DISPLAY_FILTER)
    return {'url': settings.PUBLIC_ORIGIN + f'/images/display/{image.pk}/', 'alt': alt, 'width': rendition.width, 'height': rendition.height}

def optional(value): return value or None

def site_dto(site):
    if site is None or not site.brand_name: return None
    return {'brand_name': site.brand_name, 'logo':image_dto(site.logo,site.logo_alt), 'hero_title':optional(site.hero_title), 'hero_description':optional(site.hero_description), 'hero_image':image_dto(site.hero_image,site.hero_alt), 'introduction':optional(site.introduction), 'introduction_image':image_dto(site.introduction_image,site.introduction_alt)}

def branch_dto(branch):
    import re
    phone = {'display':branch.phone, 'href':'tel:'+re.sub(r'[^+0-9]', '', branch.phone)} if branch.phone else None
    return {'id':str(branch.pk), 'name':branch.name, 'is_main':branch.is_main, 'summary':optional(branch.summary), 'cover_image':image_dto(branch.cover_image,branch.cover_alt), 'address':branch.address, 'address_detail':optional(branch.address_detail), 'phone':phone, 'kakao_channel_url':optional(branch.kakao_channel_url), 'business_hours':optional(branch.business_hours), 'closed_days':optional(branch.closed_days), 'parking_info':optional(branch.parking_info), 'usage_notes':optional(branch.usage_notes), 'location':None, 'map':map_dto(branch), 'trainer_section_path':f'/trainers/#branch-{branch.pk}' if branch.public_trainers else None, 'facility_photos':[{'image':image_dto(photo.image,photo.alt),'caption':optional(photo.caption)} for photo in branch.photos.all()]}

def trainer_dto(trainer):
    groups = {category: [] for category in TrainerCareer.Category.values}
    for career in trainer.careers.all():
        groups[career.category].append(career.text)
    return {
        'id': str(trainer.pk), 'name': trainer.name, 'job_title': optional(trainer.job_title),
        'profile_image': image_dto(trainer.profile_image, trainer.profile_alt),
        'short_intro': trainer.short_intro,
        'career_groups': [{'category': category, 'items': items} for category, items in groups.items() if items],
    }

def trainer_section_dto(branch):
    return {
        'branch': {'id': str(branch.pk), 'name': branch.name, 'is_main': branch.is_main, 'page_path': f'/branches/#branch-{branch.pk}'},
        'trainers': [trainer_dto(trainer) for trainer in branch.public_trainers],
    }

def public_snapshot():
    from .post_publication import recent_posts
    # All queries, child rows and DTO materialization complete under shared lock.
    with content_transaction(read=True):
        site = SiteContent.objects.select_related('logo','hero_image','introduction_image').first()
        trainers = Trainer.objects.filter(is_public=True).select_related('profile_image').prefetch_related('careers')
        branches = list(Branch.objects.filter(is_public=True).select_related('cover_image').prefetch_related('photos__image', Prefetch('trainers', queryset=trainers, to_attr='public_trainers')))
        return {'site':site_dto(site), 'branches':[branch_dto(branch) for branch in branches], 'trainer_sections':[trainer_section_dto(branch) for branch in branches if branch.public_trainers], 'recent_posts':recent_posts(),
                'public_shell': shell_dto(
                    {'brand_name': site.brand_name, 'logo_id': site.logo_id, 'logo_alt': site.logo_alt,
                     'logo__width': site.logo.width if site.logo else None, 'logo__height': site.logo.height if site.logo else None} if site else None,
                    any(branch.public_trainers for branch in branches), [branch.pk for branch in branches[:2]])}
