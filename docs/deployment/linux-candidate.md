# 단일 앱 Linux 운영 후보 — 미적용 준비 절차

2026-10-05 DEV-07-A 범위다. 실제 호스팅·Linux 배포판·도메인·비용·운영 책임자·복구 기준은 **TBD**이며 운영 배포 승인이 아니다. 현재 제품8766·SPIKE8765는 개발 서버로 그대로 유지한다. 아래 절차를 그 서버나 개발DB에 실행하지 않는다. 실제 대상·변경·비용·복구안을 검토한 뒤 승인된 운영 환경에서만 적용한다.

## 후보 구성·검증 경계

기존 Django5.2/Wagtail7.4/PostgreSQL 앱에 `config.settings.production`, `config.wsgi:application`, `config/gunicorn.conf.py`를 준비했다. local/test를 import하지 않고 환경 입력을 명시적으로 요구한다. Gunicorn26.2.0 sync worker2·loopback bind·timeout30초·umask077·access log 기본꺼짐·제어소켓 꺼짐이다. 실제 worker 수/timeout은 운영 메모리·미디어 변환·트래픽 시험 후 결정한다.

공식 Django5.2의 [Gunicorn WSGI 실행 안내](https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/gunicorn/)를 근거로 선택한 **로컬검증 후보**다. [26.2.0 배포 메타데이터](https://pypi.org/project/gunicorn/26.2.0/) 및 [해당 태그 pyproject](https://github.com/benoitc/gunicorn/blob/26.2.0/pyproject.toml)의 Python>=3.10 조건에 맞고, 기존37개 버전을 바꾸지 않고 Gunicorn1개/해시만 잠갔다. [태그 CI](https://github.com/benoitc/gunicorn/blob/26.2.0/.github/workflows/tox.yml)는3.13까지이므로3.14 공식 CI 통과를 주장하지 않는다. 이 WSL/Python3.14.4에서 실제 기동·WSGI 스모크는 통과했다. [현재 설치 문서](https://gunicorn.org/install/)는 이후 문서 기준 Python3.12+를 안내하므로 고정 태그와 구분한다.

실제 TLS·리버스프록시·운영 Linux·외부 DB TLS·실정적 서빙·운영 계정/부하·로그 보관/경보는 NOT_RUN이다. 로컬 HTTP에 `X-Forwarded-Proto: https`를 넣은 모의검사를 TLS 성공으로 취급하지 않는다. [실행 근거](../verification/dev-07.md)를 따른다.

## 필수 설정 계약

실제 값은 저장소·대화·명령행 인수에 넣지 않고 승인된 운영 비밀 주입 수단으로 프로세스 환경에 제공한다. 코드가 임의 `.env`를 열거나 개발 키를 읽지 않는다. env/settings 전체 덤프·Gunicorn `--print-config` 등으로 키가 유출되지 않게 한다. 테스트에서는 메모리에서 만든 임시 키만 사용했다.

| 환경 변수 | 요구 조건 |
|---|---|
| Y3GYM_SECRET_KEY | 운영 전용 무작위 키,50자 이상·충분한 문자 다양성. 개발/다른 앱 키 재사용 금지. 코드의 길이 검사는 실제 엔트로피/재사용 확인을 대신하지 않음 |
| Y3GYM_ALLOWED_HOSTS | 소문자 정확한 DNS 이름의 쉼표 목록. wildcard/선행점/localhost/IP/포트/공백 없음 |
| Y3GYM_PUBLIC_ORIGIN | 목록에 있는 정확한 `https://` 오리진,경로/쿼리/fragment/사용자정보 없음. CSRF_TRUSTED_ORIGINS와 관리자 기준주소에 동일 적용 |
| Y3GYM_MEDIA_ROOT | 소스/개발트리 밖의 기존 절대경로·앱 사용자 소유0700·symlink 없는 비공개 영속 디렉터리 |
| Y3GYM_STATIC_ROOT | 소스/개발트리 밖의 별도 기존 절대경로·앱 사용자 소유0700 정적 수집 디렉터리 |
| Y3GYM_UPLOAD_TMP | 위 두 경로와 겹치거나 포함하지 않는 기존 절대경로0700 업로드 임시 디렉터리 |
| Y3GYM_DB_NAME / DB_USER | 명시적인 PG 이름/최소권한 앱 역할. postgres/template/dev/test 기본DB와 알려진 admin/dev역할 거부. 이번 probe만 고유 drill DB와 test role 사용; 운영에 CREATEDB/test role을 사용하지 않음 |
| Y3GYM_DB_HOST / DB_PORT | 명시적인 Unix socket 절대경로 또는 DNS DB 호스트와1~65535 포트. Unix socket은 별도 검토한 로컬 peer 경계; TCP는 다음 두 항목 필수 |
| Y3GYM_DB_PASSWORD / DB_SSLROOTCERT | TCP DB 비밀번호 및 실제 존재하는 절대경로 CA 파일,sslmode=verify-full. 실제 인증서/원격 연결은 미검증 |
| Y3GYM_BIND | 승인된 `127.0.0.1:포트`,1024~65535. 기존8765/8766과 충돌시키지 않음. 앱을0.0.0.0으로 직접 공개하지 않음 |
| Y3GYM_TRUSTED_PROXY_IPS | 기본은 빈 목록. 실제 프록시의 정확한 IP만 명시,`*` 금지. bind/네트워크 격리와 함께 검토 |

DEBUG=False, secure/HttpOnly 세션·secure CSRF 쿠키·host-only `__Host-` 이름, HTTPS redirect, nosniff, DENY framing, same-origin referrer를 적용한다. Django의 SECURE_PROXY_SSL_HEADER/forwarded host/port 신뢰는 끈다. Gunicorn이 **허용한 peer**의 X-Forwarded-Proto=https만 wsgi.url_scheme에 반영한다. 프록시는 방문자 헤더를 그대로 전달하지 않고 덮어쓰며, 미허용 Host를 먼저 거부해야 한다. 앱 포트에 신뢰받지 않은 외부 클라이언트가 접근할 수 있는 상태에서 이 설정을 적용하지 않는다.

HSTS는0초, includeSubDomains/preload는false다. 이 때문에 `check --deploy`의 **security.W004 경고1개**가 남는다. 운영 인증서·HTTPS redirect·프록시 경계·복구를 실제 검증한 후 짧은 기간부터 단계적으로 올리는 변경을 별도 검토한다. 모든 하위 도메인의 HTTPS 준비와 되돌리기 영향을 확인하기 전 includeSubDomains/preload를 켜거나 등록하지 않는다. [Django 배포 점검](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)은 구성 검사의 근거이며 실제 운영 보안을 보증하지 않는다.

## 실제 대상 승인 후 실행 순서 — 이번에는 미실행

1. 대상 배포판/아키텍처·도메인/DNS·TLS종단·PG/스토리지·비용·담당자·중단허용/복구 목표를 정한다. 런타임 호환성·경로 대소문자·파일 소유/권한·앱/DB 최소권한·로그/비밀 주입을 대상에서 재검증한다. Windows/WSL venv/개발DB를 복사하지 않는다.
2. 검토된 커밋의 새 릴리스 디렉터리와 대상 Linux용 venv를 준비하고 `requirements.lock`의 버전·해시로 의존성을 재설치한다. 의존성 검사와 운영 설정의 누락/위험값 시작실패를 확인한다. 운영 데이터·영속 미디어는 릴리스와 분리한다.
3. 신규 서비스라면 빈 운영DB·계정을 별도 승인으로 준비한다. 기존 운영이라면 모든 콘텐츠/업로드 쓰기를 중지·진행 중 요청을 완료시킨 뒤 DB+미디어의 정합 복구점을 만든다. 개발 데이터 자동이관·seed를 하지 않는다. 아래 백업 정책을 먼저 확정한다.
4. 주입된 **운영 설정/대상 확인 후** 아래 점검·명시적 migration·정적 수집을 수행한다. 프로세스 시작 때 자동 migration하지 않는다. DB 스키마 변경은 diff/계획·역호환/중단시간을 검토한 경우만 적용한다.

```bash
# 승인된 대상의 app 디렉터리에서, 비밀값은 명령줄에 넣지 않는다.
.venv/bin/python manage.py check --deploy --settings=config.settings.production
.venv/bin/python manage.py migrate --plan --settings=config.settings.production
# 검토한 계획만 명시적으로 실행:
.venv/bin/python manage.py migrate --noinput --settings=config.settings.production
.venv/bin/python manage.py collectstatic --noinput --settings=config.settings.production
.venv/bin/gunicorn --config=config/gunicorn.conf.py config.wsgi:application
```

5. 정적 수집 결과만 별도 읽기 전용 배포 artifact로 게시하고 프록시의 `/static/`에 연결한다. 수집 root는 현재0700/파일0600이므로 다른 프록시 UID가 그대로 읽을 수 있다고 가정하지 않는다. 실제 게시 디렉터리/읽기 권한은 정적 artifact에만 별도로 부여·검증한다. **MEDIA_ROOT·원본/변환본·업로드tmp를 static alias 또는 `/media/`로 노출하지 않는다.** `/cms-files/`와 `/images/display/`는 앱의 인증·현재공개 사용처 판정을 통과해야 한다. 이번 Gunicorn의 `/static/`404는 의도한 앱 경계이며 실제 정적 서빙 PASS가 아니다.
6. 프로세스 관리/프록시/TLS 설정은 대상에 맞춰 검토한 뒤 적용한다. 이번에는 systemd/nginx 설정·서비스를 생성/설치하지 않았다. 실제 HTTPS·Host/CSRF·세션·관리진입·게시/초안·보호/공개 이미지·404/500·정적 자산을 브라우저와 HTTP로 검증한다. 스모크 중 실연락 버튼을 누르거나 예시 정보를 실제 콘텐츠처럼 공개하지 않는다.
7. 실패 시 새 트래픽/쓰기를 중지하고 원인·데이터 변경 여부를 판단한다. 코드만 이전 릴리스로 전환할 수 있는지 스키마·자료 호환성을 먼저 확인한다. DB/미디어를 변경했다면 **정합 복구점으로 함께 복원**하는 별도 승인 절차와 검수 후 재개한다. 코드 rollback만으로 DB가 복구된다고 가정하지 않는다.

## 백업·복원 정책 대기

이번 `scripts/restore_drill.py`는 **합성 자료 전용 일회성 연습 도구**다. CLI에 DB명/경로/backup을 받지 않으며 이전 backup을 입력받는 복원 기능도 없다. 운영 복구 도구로 일반화하거나 개발/SPIKE 대상으로 재사용하지 않는다. PG custom dump+미디어 manifest의 참조/파일 비교를 검증한 것이고 운영 용량/부하/RPO/RTO 보장이 아니다. [PG18 pg_dump](https://www.postgresql.org/docs/18/app-pgdump.html), [pg_restore](https://www.postgresql.org/docs/18/app-pgrestore.html)의 실제 도구를 사용했다.

운영 백업은 쓰기/업로드 중지 경계·일관된 DB/미디어 쌍, dump 도구/서버 호환·복원대상 격리·체크섬과 신뢰할 manifest/서명 보관, 암호화·키 관리·접근권한, 보존기간/삭제승인·책임자·외부/오프사이트 보관·복구주기/복구시험을 결정해야 한다. dump에는 실행 가능한 DB 객체가 포함될 수 있으므로 불신 backup을 임의 실행하지 않는다. 현재 manifest 신뢰 기준은 같은 연습 프로세스의 메모리 해시이며 외부 서명·보관 시스템이 아니다. 합성 증거는 암호화하지 않았고 실제 개인정보/계정 자료를 포함하지 않는다. 운영 DB·미디어를 개발 환경으로 복제하는 절차는 포함하지 않는다.
