import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from content.operators import configure_operator

class Command(BaseCommand):
    help = '일반 운영자를 준비하거나 숨김 입력으로 암호를 설정합니다. 비밀번호 인자는 받지 않습니다.'
    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('--prepare',action='store_true',help='새 계정에 사용 불가 암호를 설정; 기존 암호는 변경하지 않음')
    def handle(self, username, prepare, **options):
        if not prepare and not __import__('sys').stdin.isatty():
            raise CommandError('암호 설정은 대화형 터미널에서 실행하세요.')
        with transaction.atomic():
            user, created = get_user_model().objects.get_or_create(username=username,defaults={'is_staff':True,'is_active':True})
            if user.is_superuser or not user.is_active: raise CommandError('기존 최고 관리자/비활성 계정은 변경하지 않습니다.')
            if prepare:
                if created: user.set_unusable_password()
            else:
                password=getpass.getpass('비밀번호(숨김): ')
                if password != getpass.getpass('비밀번호 확인(숨김): '): raise CommandError('입력이 다릅니다.')
                validate_password(password,user)
                user.set_password(password)
            user.is_staff=True
            user.save()
            configure_operator(user)
        self.stdout.write('일반 운영자 준비 완료. --prepare 사용 시 새 계정은 암호 설정 전 로그인할 수 없습니다.')
