from django.http import HttpResponseForbidden, JsonResponse
from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin

class BoundaryMiddleware(MiddlewareMixin):
    def process_view(self, request, view, args, kwargs):
        match = request.resolver_match
        if match.namespace == 'wagtailsnippets_content_post' and match.url_name in {'delete', 'revisions_unschedule'}:
            return HttpResponseForbidden('게시글 영구 삭제·예약 작업은 제공하지 않습니다.')
        if match.url_name == 'wagtail_bulk_action' and kwargs.get('app_label') == 'content' and kwargs.get('model_name') == 'post':
            return HttpResponseForbidden('게시글은 한 건씩 편집·공개·철회하세요. 일괄 작업은 제공하지 않습니다.')
        # Explicitly block destructive Wagtail paths even if permission is later misassigned.
        if match.namespace == 'wagtailimages' and match.url_name in {'delete','delete_multiple','delete_upload_multiple'}:
            return HttpResponseForbidden('원본 이미지 영구 삭제는 제공하지 않습니다.')
        if match.url_name == 'wagtail_bulk_action' and kwargs.get('action') == 'delete' and kwargs.get('app_label') in {'content','wagtailimages'}:
            return HttpResponseForbidden('영구 삭제는 제공하지 않습니다.')
    def process_response(self, request, response):
        if request.path.startswith('/api/v1/') and response.status_code == 405:
            response = JsonResponse({'error': {'code':'METHOD_NOT_ALLOWED','message':'조회만 지원합니다.'}}, status=405)
            response['Allow'] = 'GET, HEAD'
        if not request.path.startswith('/static/'):
            add_never_cache_headers(response)
        return response
