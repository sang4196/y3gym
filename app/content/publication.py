"""Shared public projection. No sessions, revisions, raw storage URLs or O(n) asset scans."""
from django.conf import settings
from django.db.models import Q, Exists, OuterRef
from wagtail.images import get_image_model
from .models import SiteContent, Branch, BranchPhoto
from .locking import content_transaction

DISPLAY_FILTER = 'max-1200x900|format-png'

def public_images():
    site = SiteContent.objects.exclude(brand_name='').filter(Q(logo_id=OuterRef('pk'))|Q(hero_image_id=OuterRef('pk'))|Q(introduction_image_id=OuterRef('pk')))
    branches = Branch.objects.filter(is_public=True, cover_image_id=OuterRef('pk'))
    photos = BranchPhoto.objects.filter(branch__is_public=True, image_id=OuterRef('pk'))
    return get_image_model().objects.alias(site_use=Exists(site), branch_use=Exists(branches), photo_use=Exists(photos)).filter(Q(site_use=True)|Q(branch_use=True)|Q(photo_use=True))

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
    return {'id':str(branch.pk), 'name':branch.name, 'is_main':branch.is_main, 'summary':optional(branch.summary), 'cover_image':image_dto(branch.cover_image,branch.cover_alt), 'address':branch.address, 'address_detail':optional(branch.address_detail), 'phone':phone, 'kakao_channel_url':optional(branch.kakao_channel_url), 'business_hours':optional(branch.business_hours), 'closed_days':optional(branch.closed_days), 'parking_info':optional(branch.parking_info), 'usage_notes':optional(branch.usage_notes), 'location':None, 'trainer_section_path':None, 'facility_photos':[{'image':image_dto(photo.image,photo.alt),'caption':optional(photo.caption)} for photo in branch.photos.all()]}

def public_snapshot():
    # All queries, child rows and DTO materialization complete under shared lock.
    with content_transaction(read=True):
        site = SiteContent.objects.select_related('logo','hero_image','introduction_image').first()
        branches = Branch.objects.filter(is_public=True).select_related('cover_image').prefetch_related('photos__image')
        return {'site':site_dto(site), 'branches':[branch_dto(branch) for branch in branches]}
