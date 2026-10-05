import mimetypes
from django.conf import settings
from django.db import DatabaseError
from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_safe
from wagtail.images import get_image_model
from wagtail.images.models import Rendition
from wagtail.images.permissions import permission_policy
from wagtail.images.views.images import EditView
from .publication import public_snapshot, public_images, public_shell, DISPLAY_FILTER
from .locking import content_transaction
from .presentation import page_meta
from .naver_maps import page_config

class ImageEditView(EditView):
    @property
    def can_delete(self): return False

def error(code, message, status):
    return JsonResponse({'error':{'code':code,'message':message}}, status=status)

def meta():
    return {'server_time':timezone.now().isoformat().replace('+00:00','Z')}

@require_safe
def site_api(request):
    if request.GET: return error('INVALID_QUERY','지원하지 않는 조회 조건입니다.',400)
    data=public_snapshot()['site']
    if data is None: return error('CONTENT_NOT_READY','사이트 소개를 준비 중입니다.',503)
    return JsonResponse({'data':data,'meta':meta()})

@require_safe
def branches_api(request):
    if request.GET: return error('INVALID_QUERY','지원하지 않는 조회 조건입니다.',400)
    return JsonResponse({'items':public_snapshot()['branches'],'meta':meta()})

@require_safe
def home(request):
    snapshot=public_snapshot()
    site = snapshot['site']
    snapshot['page'] = page_meta((site['hero_title'] or site['brand_name']) if site else '사이트 소개를 준비 중입니다.',
                                snapshot['public_shell'], (site['hero_description'] or site['introduction'] or '') if site else '',
                                section='home', noindex=not site)
    return render(request,'content/home.html',snapshot,status=200 if snapshot['site'] else 503)

@require_safe
def branches(request):
    snapshot = public_snapshot()
    snapshot['naver_maps'] = page_config(snapshot['branches'], enabled=settings.NAVER_MAPS_ENABLED,
                                        key_id=settings.NAVER_MAPS_PUBLIC_KEY_ID)
    snapshot['page'] = page_meta('지점 안내', snapshot['public_shell'],
                                ' · '.join(branch['name'] for branch in snapshot['branches']) + ' — 주소, 연락처와 이용안내' if snapshot['branches'] else '공개된 지점이 없습니다.', section='branches')
    return render(request,'content/branches.html',snapshot)

@require_safe
def trainers(request):
    snapshot = public_snapshot()
    snapshot['page'] = page_meta('트레이너 소개', snapshot['public_shell'],
                                ' · '.join(section['branch']['name'] for section in snapshot['trainer_sections']) + ' — 트레이너 프로필과 약력' if snapshot['trainer_sections'] else '공개된 트레이너 소개가 없습니다.', section='trainers')
    return render(request, 'content/trainers.html', snapshot)

@require_safe
def trainer_sections_api(request):
    if request.GET: return error('INVALID_QUERY','지원하지 않는 조회 조건입니다.',400)
    return JsonResponse({'items':public_snapshot()['trainer_sections'],'meta':meta()})

def file_response(field):
    try: stream=field.open('rb')
    except FileNotFoundError as error: raise Http404 from error
    return FileResponse(stream,content_type=mimetypes.guess_type(field.name)[0] or 'application/octet-stream')

@require_safe
def display_image(request, pk):
    with content_transaction(read=True):
        image=public_images().filter(pk=pk).first()
        if image is None: raise Http404
        return file_response(image.get_rendition(DISPLAY_FILTER).file)

@require_safe
def private_file(request, name):
    if not request.user.is_active or not request.user.has_perm('wagtailadmin.access_admin'):
        return HttpResponseForbidden('이미지 접근 권한이 필요합니다.')
    image=get_image_model().objects.filter(file=name).first()
    field=image.file if image else None
    if image is None:
        rendition=Rendition.objects.select_related('image').filter(file=name).first()
        if rendition: image,field=rendition.image,rendition.file
    if image is None: raise Http404
    if not permission_policy.user_has_any_permission_for_instance(request.user,['choose','change'],image):
        return HttpResponseForbidden('이미지 접근 권한이 필요합니다.')
    return file_response(field)

def render_public_error(request, message, status):
    try:
        shell = public_shell()
    except DatabaseError:
        # A database outage must not turn error rendering into another DB failure.
        shell = {'brand_name': '', 'has_trainers': False}
    return render(request, 'content/error.html', {'message': message, 'public_shell': shell,
                  'page': page_meta(message, shell, noindex=True), 'status_code': status}, status=status)

def not_found(request, exception):
    if request.path.startswith('/api/'): return error('NOT_FOUND','콘텐츠를 찾을 수 없습니다.',404)
    return render_public_error(request, '페이지를 찾을 수 없습니다.', 404)
def server_error(request):
    if request.path.startswith('/api/'): return error('SERVER_ERROR','일시적인 오류입니다.',500)
    return render_public_error(request, '일시적인 오류입니다.', 500)
