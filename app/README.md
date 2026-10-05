# DEV-01~03 — 사이트·지점·트레이너·공지 관리

승인된 제품 단위다. Django/Wagtail 관리자에서 사이트 소개, 지점·시설 사진·이용안내, 트레이너·약력을 저장한다. 공개 홈(`/`)·지점(`/branches/`)·트레이너(`/trainers/`)와 공개 JSON이 같은 조회를 사용한다. DEV-02는 지점과 프로필이 모두 공개일 때만 트레이너 섹션·링크·사진 표시본을 제공한다. 지도는 location=null이며 팝업/완성 디자인/상용 배포는 후속 단위다. DEV-03은 공지·이벤트의 수정 초안/공개 리비전/인증 Preview와 `/posts/`·상세/공개 JSON을 추가했다. 실행 결과는 [DEV-01](../docs/verification/dev-01.md), [DEV-02](../docs/verification/dev-02.md), [DEV-03 보고서](../docs/verification/dev-03.md)를 따른다.

## 환경과 분리

- WSL Ubuntu 26.04.1, Linux Python3.14.4. 별도 `.venv`, PostgreSQL18.6, Django5.2.17, Wagtail7.4.3 LTS, Pillow12.3.0, psycopg[binary]3.3.6, bleach6.4.0. `requirements.lock`은 전이 의존성37개와 해시를 고정한다.
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

이 명령은 기존 계정이면 암호를 변경하므로 사용자 의도 없이 재실행하지 않는다. 운영자는 Site/Branch/Trainer 추가·변경·조회, Post 추가·변경·조회·공개/철회 및 전용 이미지 컬렉션의 업로드·선택·변경만 가능하며 사용자/사이트 구조/페이지/문서 관리 권한이 없다. 약력은 트레이너 부모 안에서만 편집한다. 자산 영구 삭제는 직접 경로에서도 차단한다.

기존 환경에 DEV-02·03을 적용할 때는 아래 명령으로 테이블과 역할 권한만 추가한다. 현재 환경에는 이미 적용했다. 기존 Site/Branch/사진 행이나 사용자·암호·세션을 변경하지 않고, 기존 그룹 권한도 제거하지 않는다. 그룹이 없으면 자동 계정 생성 없이 오류를 반환한다.

```bash
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py extend_trainer_permissions
# DEV-03 기존 운영자 그룹에 Post 권한4개만 추가(현재 적용 완료):
.venv/bin/python manage.py extend_post_permissions
```

초기 검증용 `DEV-01 TEST ONLY`, `TEST 본점`, `TEST 준비 지점`과 청록/주황/보라 합성PNG를 만들었다. 주소·전화는 **실제 정보가 아니므로 연락하지 않는다**. 합성 생성 명령 `create_dev_demo --confirm-test-data`는 Site/Branch가 있으면 중단하며, 사용자 편집 시작 뒤 재실행하지 않는다. 실사업 자료나 SPIKE 내용을 이관하지 않았다.

## 로컬 실행·사용

```bash
.venv/bin/python manage.py runserver 127.0.0.1:8766 --noreload --insecure
```

`--insecure`는 DEBUG=False인 로컬 시험에서 정적 자산만 제공하기 위한 옵션이다. 미디어 경로는 직접 서빙하지 않는다. 상용 서버 명령이 아니다. 시작 전 포트/소유 프로세스를 확인하고 충돌 시 다른 서버를 종료하지 않는다.

- 관리: `http://127.0.0.1:8766/admin/`
- 공개: `http://127.0.0.1:8766/`, `http://127.0.0.1:8766/branches/`, `http://127.0.0.1:8766/trainers/`, `http://127.0.0.1:8766/posts/`
- JSON: `http://127.0.0.1:8766/api/v1/site/`, `http://127.0.0.1:8766/api/v1/branches/`, `http://127.0.0.1:8766/api/v1/trainer-sections/`, `http://127.0.0.1:8766/api/v1/posts/`

홈페이지 기본정보/공개 지점은 **저장 즉시 반영**한다. 비공개 준비 지점은 빈 이름·주소로 보관할 수 있으나 공개할 때 이름·주소·유효한 전화/카카오 중1개가 필요하다. 최초 공개는 자동 본점이다. 다른 공개 지점에서 본점을 체크하면 기존 본점이 해제된다. 현재 본점을 비공개로 만들 때는 같은 폼의 `비공개 전환 시 새 본점`을 선택한다. 마지막 공개 지점 비공개는 거부한다. 오래된 폼은 충돌 안내 후 다시 열어야 한다.

트레이너는 지점 하나를 항상 선택한다. 비공개 준비는 이름·사진·한줄소개가 없어도 저장할 수 있으나 공개할 때는 모두 필요하다. 직급·약력은 선택이며 이름/직급100자, 한줄소개300자, 대체설명200자, 약력 한 항목500자다. 약력은 학력/수상경력/자격증/주요 경력의 고정 구분이며 순서를 변경하거나 항목을 제거할 수 있다. 같은 폼에서 부모와 함께 저장되고 공개 중인 내용은 즉시 반영된다. Post식 수정 초안·Preview는 제공하지 않는다.

프로필과 지점이 모두 공개일 때만 지점별 섹션이 생긴다. 지점 비공개는 프로필 자체의 공개 설정·약력을 바꾸지 않는다. 소속을 옮겨도 같은 프로필이며 빈 직급·약력 구분·지점 섹션과 연결 링크는 숨긴다. 개발 DB에 트레이너 예시는 생성하지 않았으며 실제 인물·경력을 임의로 채우지 않는다.

공지·이벤트는 새 글/수정본을 **Save draft → 다시 열기 → Preview → 명시적 Publish**로 관리한다. 제목200자·대표alt200자, 대표 사진은 선택이다. 빈 초안은 보관할 수 있지만 공개에는 제목·분류·본문 텍스트 또는 본문 이미지와 실제 참조 파일이 필요하다. 대표 사진만 있는 빈 본문은 공개되지 않는다. 본문은 검토한 Paragraph 편집/기본 아이콘 도구막대/접힌 이미지 옵션이며 이미지별 교체·삭제는 해당 배치만 바꾼다.

수정 초안의 제목/분류/본문/사진은 기존 공개본을 바꾸지 않는다. Preview는 로그인·컬렉션 권한이 있는 운영자에게 보호 이미지를 표시한다. 최초 공개일은 철회/재공개에도 유지하고 공개 updated_at은 마지막 Publish 때만 바뀐다. 목록/상세와 홈 최근3건은 공개 리비전만 읽는다. 과거 버전은 새 초안으로 복원한 뒤 다시 열어 검수·공개한다. 파일이 유실됐으면 복원/공개 전에 복구하거나 다른 자산을 선택해야 한다.

Post 자동저장·기존 리비전 덮어쓰기·수동 날짜·예약·workflow·일괄 작업·영구 삭제는 제공하지 않는다. 개별 철회에는 게시 권한과 최신 폼 버전이 필요하다. 오래된 폼 오류가 나오면 다시 열어 변경 내용을 확인한다. `/posts/`는 전체/공지/이벤트 필터·페이지 분할, `/posts/{id}/`와 대응 API는 공개 상세다. 개발 DB에 Post 예시 글은 자동 생성하지 않았다.

사진은 새 자산 업로드 후 선택하여 교체한다. 시설 사진의 배치 제거는 허용하되 원본 영구삭제와 다르다. 원본·내부 썸네일은 운영자 권한 경로, 공개 표시는 현재 Site/공개지점/시설배치/지점과 프로필 모두 공개인 트레이너 또는 Post 실제 공개 리비전 참조가 있는 경우에만 제공한다. 공유 사진은 한 공개 사용처라도 남으면 공개다.

## 검증

```bash
.venv/bin/python manage.py test content --settings=config.settings.test --noinput -v 2
.venv/bin/python manage.py makemigrations --check --dry-run
node --test tests/composer*.test.cjs
uv --no-config --cache-dir .cache pip check --python .venv/bin/python
```

테스트는 **실제 PostgreSQL** y3gym_test DB를 생성/폐기하며 dev DB를 초기화하지 않는다. 테스트 미디어 디렉터리는 증거로 남고 누적되므로 자동 삭제하지 않는다. 로그는 새 파일명으로 보존한다. 실패한 이전 로그도 유지한다. 서버/CMS test client·DB 동시성·HTTP는 실제 브라우저 확인과 구분한다.

본점 쓰기는 PostgreSQL advisory transaction exclusive lock(19372001,1), 공개 projection은 같은 shared lock을 DTO 생성까지 유지한다. 최초 빈 상태에서도 동작하고 부모/사진이 섞인 조회를 막는다. 동시 최초 공개/본점변경/비공개, writer→reader 및 reader→writer 양방향 대기를 별도 연결에서 검증한다. 이미지 판정은 관계 FK의 SQL EXISTS이며 모든 Post를 읽는 실험 스캔을 사용하지 않는다. 소규모 사이트용 잠금 범위이므로 대량 트래픽/큰 이미지 변환 때의 대기·성능은 후속 검토 대상이다.

DEV-02도 같은 잠금 경계에서 Trainer+Career 저장·조회 전체를 처리한다. 실제 PostgreSQL28개(기존14+신규14) PASS이며 일반 운영자 Wagtail POST, 약력 소유권/롤백, 동시 이동·지점 비공개·오래된 저장·양방향 조회 대기까지 포함한다. 실제 트레이너 브라우저 조작은 NOT_RUN, 공식 Computer Use는 기존 BLOCKED이며 서버 검사로 대체 PASS를 부여하지 않는다.

DEV-03은 실제 PG46개(기존28+Post18)와 편집기 Node7개 PASS다. PG 검사는 공개/철회·복원·시각·필터/페이지·권한/파일·인덱스 실패 rollback·동시성, Node는 모의 계약1개와 실제 설치 라이브러리 상태 전이6개다. 브라우저 클릭/화면/포커스 검증은 NOT_RUN이다. `PostImageUse`는 공개 대표/본문 참조의 파생 관계 인덱스이며 실제 live_revision과 일치할 때만 공개 권한에 포함한다. 전체 공개 Post를 읽는 스캔은 없다. 기본 action 직접 호출·raw SQL/임의 bulk update·인덱스 수동 변경은 지원 편집 경로가 아니다.

Git P2 후속에서 게시글/Preview/공개 오류 화면의 공통 브랜드·트레이너 메뉴를 복구했다. 셸은 브랜드명과 공개 지점의 공개 트레이너 존재만 조회하고 기존 홈/지점/트레이너는 이미 읽은 결과를 재사용한다. DB 자체 장애 때만 최소 오류 셸로 표시한다. 관련 PG6개 PASS와 제품 PID508585/8766 재적용·보존 근거는 DEV-03 보고서 §7을 따른다. 전체 검토는 재개 대기이며 실제 브라우저는 NOT_RUN이다.

## 종료·보존

제품 runserver를 시작한 터미널에서는 Ctrl-C로 해당 서버만 종료한다. 백그라운드 PID는 보고서의 실행 기록과 현재 cwd/uid/명령을 대조한 후에만 SIGINT를 보낸다. 사용자 브라우저 확인 중인 서버는 조율 없이 종료하지 않는다. PG를 종료할 때는 제품 서버/테스트가 사용하지 않는지 확인한 다음:

```bash
python3 scripts/local_pg.py stop
```

이는 프로젝트 pg-data의 pg_ctl만 사용한다. DB·미디어·로그·venv를 지우지 않는다. 운영용 백업/복원·HTTPS/프록시/배포는 아직 검증하지 않았다.
