import json
from django.core.management.base import BaseCommand, CommandError
from content.preview_content import validate_environment, _populate_preview_content


class Command(BaseCommand):
    help = 'DEV-07-B: 비어 있는 트레이너/글/팝업에 로컬 TEST 자료를 한 번만 추가합니다.'
    requires_system_checks = []  # reject wrong environments before any content checks

    def add_arguments(self, parser):
        parser.add_argument('--confirm-test-content', required=True)
        parser.add_argument('--server-pid', type=int, required=True)

    def handle(self, **options):
        receipt = validate_environment(options['confirm_test_content'], options['server_pid'])
        try:
            result = _populate_preview_content(receipt)
        except CommandError:
            raise
        except Exception:
            raise CommandError('임시 자료 추가 실패. 새 실행 기록/파일을 확인하세요. 자동 재시도하지 않습니다.') from None
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
