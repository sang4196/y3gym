from io import BytesIO
from PIL import Image as PillowImage, ImageDraw
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from wagtail.images import get_image_model
from content.models import SiteContent, Branch, BranchPhoto
from content.operators import configure_operator

class Command(BaseCommand):
    help='새 개발 DB에만 명백한 합성 DEV-01 자료를 생성합니다. 기존 콘텐츠를 변경하지 않습니다.'
    def add_arguments(self, parser): parser.add_argument('--confirm-test-data',action='store_true',required=True)
    @transaction.atomic
    def handle(self, **options):
        if SiteContent.objects.exists() or Branch.objects.exists(): raise CommandError('기존 콘텐츠 보존: 생성 중단')
        operator=get_user_model().objects.get(username='dev-editor')
        collection=configure_operator(operator)
        images=[]
        for color in ['teal','orange','purple']:
            image=PillowImage.new('RGB',(960,640),color)
            ImageDraw.Draw(image).text((30,30),'DEV-01 SYNTHETIC TEST ONLY',fill='white')
            stream=BytesIO(); image.save(stream,'PNG')
            images.append(get_image_model().objects.create(title=f'DEV-01 TEST {color}',collection=collection,file=ContentFile(stream.getvalue(),name=f'dev-test-{color}.png')))
        SiteContent(brand_name='DEV-01 TEST ONLY',hero_title='개발 검증용 합성 자료',hero_description='실제 지점·시설 정보가 아닙니다.',hero_image=images[0],hero_alt='개발 검증용 청록색 사각형',introduction='이 화면은 DEV-01 로컬 검증 자료입니다.').save()
        branch=Branch(name='TEST 본점',is_public=True,address='TEST ONLY — 실제 주소 아님',phone='000-0000-0000',cover_image=images[0],cover_alt='검증용 청록색 이미지',business_hours='TEST 운영시간',usage_notes='TEST ONLY — 전화하지 마세요.')
        branch.photos.add(BranchPhoto(image=images[1],alt='검증용 주황색 이미지',caption='TEST 시설 사진',sort_order=0))
        branch.save()
        Branch(name='TEST 준비 지점',cover_image=images[2],cover_alt='검증용 보라색 이미지').save()
        self.stdout.write('DEV-01 합성 자료 생성 완료; 기존 SPIKE는 사용하지 않았습니다.')
