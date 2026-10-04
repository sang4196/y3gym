# DEV-01 — 사이트 소개·지점 관리

승인된 첫 제품 단위다. Django/Wagtail 관리자에서 사이트 소개, 지점·시설 사진·이용안내를 저장하고 공개 홈(`/`)·지점 한 페이지(`/branches/`)·`/api/v1/site/`·`/api/v1/branches/`가 공통 공개 조회를 사용한다. 지도/트레이너/제품 게시글/팝업/완성 디자인/상용 배포는 포함하지 않는다. 지도와 트레이너 경로는 JSON null이다. 실행 결과는 [DEV-01 보고서](../docs/verification/dev-01.md)에 있다.

## 환경과 분리

- WSL Ubuntu 26.04.1, Linux Python3.14.4. 별도 `.venv`, PostgreSQL18.6, Django5.2.17, Wagtail7.4.3 LTS, Pillow12.3.0, psycopg[binary]3.3.6. `requirements.lock`은 전이 의존성35개와 해시를 고정한다.
- `.runtime/`는 Git 제외·소유자 전용이며 PG 데이터/패키지/로그·개발 미디어·개발 Django 키·테스트 증거를 보존한다. 내용 출력·환경변수 덤프·초기화/삭제를 하지 않는다. OS 간 venv 복사 없음.
- `config/settings/base.py` 공통 설정, `local.py` 개발 연결/키/미디어, `test.py` 별도 PG 테스트 role/DB/매 실행 별도 미디어. 운영 설정은 아직 제공하지 않는다. local의 HTTP·쿠키 설정을 운영에 사용하지 않는다.
- 기존 `experiments/cms-spike`와 DB·계정·미디어·venv·서버가 독립이다. SPIKE8765를 재사용/종료하지 않는다. 제품은127.0.0.1:8766, cookie 이름도 별도다.

## 최초 준비 (이미 준비된 환경에서는 반복하지 않음)

모든 명령은 저장소의 `app` 디렉터리에서 WSL Bash로 실행한다. 기존 `.venv`나 `.runtime`가 있으면 보존하고 필요한 실행 단계만 선택한다.

```bash
uv venv --no-config --no-python-downloads --python /usr/bin/python3 .venv
uv --no-config --cache-dir .cache pip install --python .venv/bin/python --no-python-downloads --require-hashes -r requirements.lock
```

PG는 이 환경에서 sudo 비대화형 인증이 불가능하여 **공식 Ubuntu 패키지를 설치 스크립트 실행 없이 프로젝트 경로에 추출**했다. `scripts/pg-packages.json`에 정확한 버전/해시를 기록했다. 다운로드 도구는 APT 패키지 인덱스의 해시와 파일 해시를 함께 검사하고 `dpkg-deb -x`로만 추출한다. apt source/시스템 패키지/서비스/방화벽을 바꾸지 않는다. matching Ubuntu amd64 인덱스/시스템 런타임이 필요하며 다른 배포판에 이 바이너리를 복사하지 않는다. 패키지가 저장소에서 사라지면 버전/지원/해시를 검토하고 기록을 갱신해야 하며 검증을 우회하지 않는다.

```bash
python3 scripts/download_postgres.py
python3 scripts/local_pg.py init
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py check
```

`init`은 기존 pg-data가 있으면 중단한다. 전용 `.runtime/pg-socket`(0700)의 socket port55432와 peer map만 쓰며 TCP는 비활성이다. OS 현재 사용자를 전용 owner/dev/test role로 매핑하며 암호는 사용하지 않는다. y3gym_dev는 non-superuser/no-createdb, y3gym_test는 non-superuser/createdb로 테스트DB 생성·폐기만 담당한다. test role의 dev DB CONNECT도 허용하지 않는다. 이 로컬 사용자·소켓 신뢰 경계는 상용 인증 설계가 아니다.

기존 클러스터 재사용:

```bash
python3 scripts/local_pg.py status
# 상태가 종료인 경우에만:
python3 scripts/local_pg.py start
```

## 일반 운영자·합성 개발 자료

계정 준비는 최고 관리자를 만들지 않는다. 필요하면 `--prepare`로 암호 미설정(로그인 불가) 상태를 만든다. 새 개발 계정 `dev-editor`는 이 방식으로 준비한 뒤 2026-10-05 사용자가 암호 설정·로그인 완료를 보고했다. 현재 계정은 다시 설정할 필요가 없다. 신규 준비나 사용자가 암호 변경을 원할 때만 다음 명령을 **대화형 WSL 터미널**에서 실행해 비밀번호를 두 번 숨김 입력한다. 비밀번호를 대화/명령줄/문서/로그로 전달하지 않는다.

```bash
.venv/bin/python manage.py create_operator dev-editor
```

이 명령은 기존 계정이면 암호를 변경하므로 사용자 의도 없이 재실행하지 않는다. 운영자는 Site/Branch 추가·변경·조회 및 전용 이미지 컬렉션의 업로드·선택·변경만 가능하며 사용자/사이트 구조/페이지/문서 관리 권한이 없다. 자산 영구 삭제는 직접 경로에서도 차단한다.

초기 검증용 `DEV-01 TEST ONLY`, `TEST 본점`, `TEST 준비 지점`과 청록/주황/보라 합성PNG를 만들었다. 주소·전화는 **실제 정보가 아니므로 연락하지 않는다**. 합성 생성 명령 `create_dev_demo --confirm-test-data`는 Site/Branch가 있으면 중단하며, 사용자 편집 시작 뒤 재실행하지 않는다. 실사업 자료나 SPIKE 내용을 이관하지 않았다.

## 로컬 실행·사용

```bash
.venv/bin/python manage.py runserver 127.0.0.1:8766 --noreload --insecure
```

`--insecure`는 DEBUG=False인 로컬 시험에서 정적 자산만 제공하기 위한 옵션이다. 미디어 경로는 직접 서빙하지 않는다. 상용 서버 명령이 아니다. 시작 전 포트/소유 프로세스를 확인하고 충돌 시 다른 서버를 종료하지 않는다.

- 관리: `http://127.0.0.1:8766/admin/`
- 공개: `http://127.0.0.1:8766/`, `http://127.0.0.1:8766/branches/`
- JSON: `http://127.0.0.1:8766/api/v1/site/`, `http://127.0.0.1:8766/api/v1/branches/`

홈페이지 기본정보/공개 지점은 **저장 즉시 반영**한다. 비공개 준비 지점은 빈 이름·주소로 보관할 수 있으나 공개할 때 이름·주소·유효한 전화/카카오 중1개가 필요하다. 최초 공개는 자동 본점이다. 다른 공개 지점에서 본점을 체크하면 기존 본점이 해제된다. 현재 본점을 비공개로 만들 때는 같은 폼의 `비공개 전환 시 새 본점`을 선택한다. 마지막 공개 지점 비공개는 거부한다. 오래된 폼은 충돌 안내 후 다시 열어야 한다.

사진은 새 자산 업로드 후 선택하여 교체한다. 시설 사진의 배치 제거는 허용하되 원본 영구삭제와 다르다. 원본·내부 썸네일은 운영자 권한 경로, 공개 표시는 현재 Site/공개지점/시설배치 참조가 있는 경우에만 제공한다. 공유 사진은 한 공개 사용처라도 남으면 공개다.

## 검증

```bash
.venv/bin/python manage.py test content --settings=config.settings.test --noinput -v 2
.venv/bin/python manage.py makemigrations --check --dry-run
uv --no-config --cache-dir .cache pip check --python .venv/bin/python
```

테스트는 **실제 PostgreSQL** y3gym_test DB를 생성/폐기하며 dev DB를 초기화하지 않는다. 테스트 미디어 디렉터리는 증거로 남고 누적되므로 자동 삭제하지 않는다. 로그는 새 파일명으로 보존한다. 실패한 이전 로그도 유지한다. 서버/CMS test client·DB 동시성·HTTP는 실제 브라우저 확인과 구분한다.

본점 쓰기는 PostgreSQL advisory transaction exclusive lock(19372001,1), 공개 projection은 같은 shared lock을 DTO 생성까지 유지한다. 최초 빈 상태에서도 동작하고 부모/사진이 섞인 조회를 막는다. 동시 최초 공개/본점변경/비공개, writer→reader 및 reader→writer 양방향 대기를 별도 연결에서 검증한다. 이미지 판정은 관계 FK의 SQL EXISTS이며 모든 Post를 읽는 실험 스캔을 사용하지 않는다. 소규모 사이트용 잠금 범위이므로 대량 트래픽/큰 이미지 변환 때의 대기·성능은 후속 검토 대상이다.

## 종료·보존

제품 runserver를 시작한 터미널에서는 Ctrl-C로 해당 서버만 종료한다. 백그라운드 PID는 보고서의 실행 기록과 현재 cwd/uid/명령을 대조한 후에만 SIGINT를 보낸다. 사용자 브라우저 확인 중인 서버는 조율 없이 종료하지 않는다. PG를 종료할 때는 제품 서버/테스트가 사용하지 않는지 확인한 다음:

```bash
python3 scripts/local_pg.py stop
```

이는 프로젝트 pg-data의 pg_ctl만 사용한다. DB·미디어·로그·venv를 지우지 않는다. 운영용 백업/복원·HTTPS/프록시/배포는 아직 검증하지 않았다.
