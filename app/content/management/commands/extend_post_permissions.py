from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = '기존 홈페이지 운영자 그룹에 게시글 추가·변경·조회·공개 권한만 추가합니다. 계정·암호·세션은 변경하지 않습니다.'

    def handle(self, **options):
        with transaction.atomic():
            try:
                group = Group.objects.get(name='홈페이지 운영자')
            except Group.DoesNotExist as error:
                raise CommandError('기존 홈페이지 운영자 그룹이 없습니다. 계정을 자동 생성하지 않습니다.') from error
            permissions = list(Permission.objects.filter(
                content_type__app_label='content', content_type__model='post',
                codename__in=['add_post', 'change_post', 'view_post', 'publish_post'],
            ))
            if len(permissions) != 4:
                raise CommandError('Post 마이그레이션과 권한 생성이 먼저 필요합니다.')
            group.permissions.add(*permissions)
        self.stdout.write('게시글 추가·변경·조회·공개 권한 추가 완료. 기존 계정·권한·암호·세션 유지.')
