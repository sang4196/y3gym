from urllib.parse import urlencode
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe
from .post_publication import parse_query, posts_snapshot, post_snapshot
from .views import error, meta, render_public_error
from .publication import public_shell
from .locking import content_transaction
from .presentation import page_meta, post_meta


@require_safe
def posts_api(request):
    try:
        data = posts_snapshot(*parse_query(request.GET))
    except ValueError:
        return error('INVALID_QUERY', '조회 조건을 확인하세요.', 400)
    return JsonResponse({**data, 'meta': meta()})


@require_safe
def post_api(request, pk):
    if request.GET:
        return error('INVALID_QUERY', '지원하지 않는 조회 조건입니다.', 400)
    return JsonResponse({'data': post_snapshot(pk), 'meta': meta()})


@require_safe
def posts(request):
    try:
        category, page, page_size = parse_query(request.GET)
    except ValueError:
        return render_public_error(request, '조회 조건을 확인하세요.', 400)
    with content_transaction(read=True):
        data = posts_snapshot(category, page, page_size)
        data['public_shell'] = public_shell()
    def link(target_page, target_category):
        params = {'page': target_page, 'page_size': page_size}
        if target_category:
            params['category'] = target_category
        return '/posts/?' + urlencode(params)
    data.update(
        category=category,
        filters=[{'label': label, 'url': link(1, value), 'current': value == category} for value, label in [(None,'전체'),('notice','공지사항'),('event','이벤트')]],
        previous_url=link(page-1,category) if page > 1 else None,
        next_url=link(page+1,category) if data['pagination']['has_next'] else None,
    )
    label = {'notice': '공지사항', 'event': '이벤트'}.get(category, '공지·이벤트')
    data['page'] = page_meta(f'{label} · {page} 페이지' if page > 1 else label, data['public_shell'],
                             f'{label} 공개 게시글 목록', section='posts')
    return render(request, 'content/posts.html', data)


@require_safe
def post_detail(request, pk):
    with content_transaction(read=True):
        data = {'post': post_snapshot(pk), 'public_shell': public_shell()}
    data['page'] = post_meta(data['post'], data['public_shell'])
    return render(request, 'content/post_detail.html', data)
