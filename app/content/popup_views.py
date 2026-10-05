from django.http import JsonResponse
from django.views.decorators.http import require_safe
from .popup_publication import popups_snapshot
from .views import error


@require_safe
def active(request):
    if request.GET:return error('INVALID_QUERY','지원하지 않는 조회 조건입니다.',400)
    return JsonResponse(popups_snapshot())
