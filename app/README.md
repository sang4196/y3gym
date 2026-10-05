# DEV-01~04·06 — 콘텐츠 관리·공개 홈페이지

## DEV-07-B 임시 통합 확인 자료 (2026-10-05)

사용자의 Q-03 승인에 따라 기존 콘텐츠를 보존하면서 비어 있던 트레이너·공지/이벤트·팝업에만 새 TEST 자료를 추가했다. 기존 공개 본점에 임시 트레이너2명/약력2개, 임시 공지·이벤트 각1건, 공지에 연결한7일 팝업1개와 합성PNG3개다. 실제 인물/자격/행사 정보가 아니다. 기존 create_dev_demo/초기화/seed를 재실행하지 않았다.

전용 검사10개(환경2·PG8)/6.809s 및 실제 루프백 HTTP23건을 확인했다. 실제 브라우저는 NOT_RUN이며 전체 DEV-07·제품·운영 완료가 아니다. 제품537403/8766·PG456028·SPIKE452717/8765는 재시작 없이 유지했다. 기존 Site/Branch/시설사진·계정 메타데이터/권한·기존 미디어7파일과 SPIKE31파일은 보존했다. 새 원본3·변환본3이 늘어 제품미디어는13개다.

DEV-05-A는 `7f878bc9501ca2888f970949123532c58b058462`로 검토·정상 push 완료했다. 네이버 지도 키·현행 저장/재사용 정책·실제 지도 성공은 미완료이며 호스팅·비용·배포는 미선정/미승인이다. 아래 이전 실행 기록과 구분한다.

[DEV-07-B 생성 자료·검증·브라우저 확인 준비](../docs/verification/dev-07-b.md)를 따른다. Git 검토 대기다.

이번 전용 명령은 이미 한 번 적용했다. **재실행하지 않는다.** 실행 기록:

```bash
.venv/bin/python manage.py add_local_preview_content --confirm-test-content ADD-LOCAL-TEST-CONTENT-ONCE --server-pid 537403
```

local 설정·정확한 y3gym_dev DB/역할/Unix socket·비공개 로컬 저장소·현재127.0.0.1:8766 서버 신원/리스너를 검사한다. production/test CLI 실행은 거부한다. 기존 Trainer/Post/Popup·임시 이름/파일·`.runtime/dev07b-preview-content-receipt.json`이 있으면 무변경 중단하며 삭제/갱신/강제 실행 옵션은 없다. 새 이미지/리비전/발행·참조 관계는 정식 모델 경로를 사용한다. 실제 계정 생성·로그인·암호/권한 변경 없음. 전용 테스트는 명령 guard와 내부 생성 로직을 분리해 y3gym_test/격리미디어에서 실행한다.

```bash
.venv/bin/python manage.py test content.test_preview_content --settings=config.settings.test --noinput -v 2
```

현재 팝업1은 KST 2026-10-05 15:28:43.547972부터10-12 15:28:43.547972 직전까지다. 시간이 지나면 기존 종료 규칙을 따르며 자동 연장/재생성하지 않는다. 임시 글/트레이너·새 자산은 사용자가 검수할 수 있도록 보존한다.

## DEV-05-A 한정 준비 (2026-10-05)

사용자는 Q-02 지도 제공자를 **네이버지도**로 선택했다. Q-03 실제 자료가 없어도 TEST/임시 자료로 개발하도록 승인했으며, 이번 자료는 격리 합성 검증에 한정했다. 기존 사용자 콘텐츠·계정·사진 초기화/덮어쓰기·seed 재실행 승인이 아니다. 실자료는 공개 준비 등 정말 필요한 단계에서 다시 요청한다.

네이버 Geocoding 어댑터와 공개 Map/Marker JS의 키 없는 준비·모의 검증만 수행했다. 기본 비활성이고 현재 공개 `location=null`을 유지하므로 실제 지도 요청은 없다. 관리자 확인/좌표·결과·후보토큰 저장, migration, 공개 임의주소 proxy는 추가하지 않았다. 실제 인증·위치·쿼터·브라우저 및 **전체 DEV-05는 미완료**다. 구2020 약관의 저장금지와 현행 적용 미확인을 구분하며 좌표 저장/재사용·공개 JSON 전달 정책을 후속 확정한다. 기존 카카오 정책을 적용하지 않는다. 전체 Proposed를 일괄 채택하지 않는다.

[DEV-05-A 보고서](../docs/verification/dev-05.md)에 설정 경계·검사·정책 출처와 미검증을 기록했다. 아래 Q-02 대기 문구는 이전 실행 이력이다. DEV-07-A 코드 검토·push는 `af954563`으로 완료됐으며 상태 정리는 `982f639`에 반영됐다.

준비 코드: `content/naver_maps.py`의 `GeocodingConfig()`는 disabled이며 제품 호출 경로/환경 키 로더가 없다. 명시 설정으로만 호출 가능한 어댑터를 mock으로 검사했다. `NAVER_MAPS_ENABLED=False`, `NAVER_MAPS_PUBLIC_KEY_ID=''`가 기본이고 실제 설정 변경은 하지 않았다. Secret을 SDK 식별값 설정에 넣지 않는다. `assets/naver-maps.js`는 공개 DTO 기반 데이터가 있을 때만 SDK를 한 번 로드하고 실패 시 지도만 숨긴다. 주소·연락처는 항상 남는다.

이번 관련 검사(실제 브라우저 아님):

```bash
.venv/bin/python manage.py test content.test_naver_maps content.test_presentation --settings=config.settings.test --noinput -v 2
node --test tests/naver-maps.test.cjs
```

승인된 제품 단위다. Django/Wagtail 관리자에서 사이트 소개, 지점·시설 사진·이용안내, 트레이너·약력을 저장한다. 공개 홈(`/`)·지점(`/branches/`)·트레이너(`/trainers/`)와 공개 JSON이 같은 조회를 사용한다. DEV-02는 지점과 프로필이 모두 공개일 때만 트레이너 섹션·링크·사진 표시본을 제공한다. 지도는 Q-02 답변 대기로 location=null이며 상용 배포는 후속 단위다. 공개 화면 통합은 DEV-06에서 적용했으나 실제 브라우저 검수는 NOT_RUN이다. DEV-03은 공지·이벤트의 수정 초안/공개 리비전/인증 Preview와 `/posts/`·상세/공개 JSON을 추가했다. 실행 결과는 [DEV-01](../docs/verification/dev-01.md), [DEV-02](../docs/verification/dev-02.md), [DEV-03](../docs/verification/dev-03.md), [DEV-04 보고서](../docs/verification/dev-04.md)를 따른다.

## DEV-06 공개 화면 적용

밝은 중립 배경·녹색 강조·시스템 글꼴로 공통 헤더/푸터·메뉴·본문 바로가기, 고정 홈 순서·지점/프로필/글 화면을 통합했다. 문의는 공개 지점1개면 해당 앵커, 여러 개면 목록,0개면 숨김이다. 지점 주소/전화 텍스트·연락 버튼을 유지하며 지도 성공으로 표시하지 않는다. 사진 없는 영역은 빈 이미지 대신 텍스트/영역 숨김으로 표시한다.

게시글 메타는 실제 공개 리비전만 사용하고 인증 Preview/오류/준비중에는 noindex를 붙인다. 홈 설명이 없으면 임의 홍보 문구를 만들지 않는다. HTML의 본문 사진만 lazy 속성을 추가하며 공개 JSON 형식은 그대로다. 새 폰트/CDN/JS/패키지·관리자 편집 변경·모델 migration/권한 적용은 없다.

실제 PG **76개/45.399s PASS**(기존68+신규8), 팝업 Node **16개/372.024702ms PASS**, 공개 JSON5종/콘텐츠·미디어 전후 동일. 제품은 **PID515502/127.0.0.1:8766**으로 적용했으며 PG456028·SPIKE452717은 유지했다. 아래 이전 PID·검토 대기는 이력이다. 실제320px/200% 확대·키보드·모바일은 NOT_RUN, [DEV-06 보고서](../docs/verification/dev-06.md)에 계층별 증거와 한 묶음 후속 확인을 기록했다. Git 검토·정상 push는 `285833fe`로 완료했다.

## DEV-07-A 격리 복원·운영 후보 준비

[DEV-07-A 결과](../docs/verification/dev-07.md)와 [Linux 배포 후보](../docs/deployment/linux-candidate.md)를 따른다. 운영 대상/도메인·비용·키·복구정책은 TBD이며 실제 운영 배포·DEV-07 전체 완료가 아니다. 현재 local/test와 제품515502/8766·PG456028·SPIKE452717은 변경/재시작하지 않았다.

```bash
# app cwd. 기존 DB/경로/백업을 인수로 받지 않는 합성 연습 전용:
.venv/bin/python scripts/restore_drill.py
```

매 실행 새로운 test-role DB2개·합성자료/미디어만 만들고 pg_dump/pg_restore·체크섬/manifest·공개/초안/리비전·이미지권한과 운영후보를 검사한다. 생성 DB는 owner/OID 확인 후 정리하고 `.runtime/restore-drill-{id}/`의 합성 backup·media·로그는 보존한다. 개발/SPIKE·운영 DB 복원에 사용하지 않는다. production 설정은 소스트리 밖0700 임시저장소·시험키·가짜도메인과 복원된 합성DB로만 검증한다. 해당 임시자산도 결과경로에 남고 실제 비밀값을 읽지 않는다.

최종11안전거부·5복원시나리오·16설정거부·14실제 Gunicorn HTTP 항목 PASS, 추가진입거부4건 PASS. 실제HTTPS/프록시 성공을 뜻하지 않는다. HSTS는 TLS검증 전0으로 두어 `check --deploy` security.W004 경고1개를 기록했다. 시험 Gunicorn master/worker는 종료했고 제어소켓은 꺼져 있다. 기존 PG76/팝업Node16은 DEV-06 실행이력이며 이번 전체재실행하지 않았다. 실제 브라우저/지도·실콘텐츠·운영환경은 대기한다.

## 환경과 분리

- WSL Ubuntu 26.04.1, Linux Python3.14.4. 별도 `.venv`, PostgreSQL18.6, Django5.2.17, Wagtail7.4.3 LTS, Pillow12.3.0, psycopg[binary]3.3.6, bleach6.4.0. `requirements.lock`은 Gunicorn26.2.0을 포함한38개 패키지와 해시를 고정한다. 기존37개 버전은 변경하지 않았다.
- `.runtime/`는 Git 제외·소유자 전용이며 PG 데이터/패키지/로그·개발 미디어·개발 Django 키·테스트 증거를 보존한다. 내용 출력·환경변수 덤프·초기화/삭제를 하지 않는다. OS 간 venv 복사 없음.
- `config/settings/base.py` 공통 설정, `local.py` 개발 연결/키/미디어, `test.py` 별도 PG 테스트 role/DB/매 실행 별도 미디어. `production.py`/WSGI·Gunicorn은 DEV-07-A에서 별도 로컬검증 후보로 준비했으며 실제 운영 적용은 미실행이다. local의 HTTP·쿠키 설정을 운영에 사용하지 않는다.
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

이 명령은 기존 계정이면 암호를 변경하므로 사용자 의도 없이 재실행하지 않는다. 운영자는 Site/Branch/Trainer 추가·변경·조회, Post 추가·변경·조회·공개/철회, Popup 추가·변경·조회 및 전용 이미지 컬렉션의 업로드·선택·변경만 가능하며 사용자/사이트 구조/페이지/문서 관리 권한이 없다. 약력은 트레이너 부모 안에서만 편집한다. 자산 영구 삭제는 직접 경로에서도 차단한다.

기존 환경에 DEV-02~04를 적용할 때는 아래 명령으로 테이블과 역할 권한만 추가한다. 현재 환경에는 이미 적용했다. 기존 Site/Branch/사진 행이나 사용자·암호·세션을 변경하지 않고, 기존 그룹 권한도 제거하지 않는다. 그룹이 없으면 자동 계정 생성 없이 오류를 반환한다.

```bash
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py extend_trainer_permissions
# DEV-03 기존 운영자 그룹에 Post 권한4개만 추가(현재 적용 완료):
.venv/bin/python manage.py extend_post_permissions
# DEV-04 현재 환경 적용 완료: Popup add/change/view만 추가
.venv/bin/python manage.py extend_popup_permissions
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

## 기간제 팝업

모든 팝업은 게시글 하나에 필수 연결하며 글당 최대1개 설정을 재사용한다. 게시글에 팝업을 추가하는 것은 선택이다. 기존 Wagtail ‘기간제 팝업’에서 제목200/일반 문구1000/선택 이미지·alt200/사용/시작·종료(한국시간)/우선순위(작을수록 먼저)를 관리한다. 비활성 준비는 Post 외 미완성을 허용하되 양쪽 기간이 있으면 시작<종료여야 한다. 활성은 제목과 문구 또는 이미지 및 시작/종료가 필수다. 저장 즉시 현재 설정에 반영되지만 Post의 공개 상태/초안은 바꾸지 않는다. ‘연결 글 비공개로 중지’면 글의 공개 상태를 확인한다. 방문자별 숨김을 관리자 상태로 표시하지 않는다.

`/api/v1/popups/active/`는 활성/기간/실제 공개 Post를 만족하는 후보만 서버시각으로 반환한다. 연결 글 제목은 공개 리비전이다. 팝업 이미지는 같은 조건의 SQL EXISTS로 판정하며 종료/비활성/글 철회 때 다른 공개 참조가 없으면 새 표시본 접근을 차단한다. 방문자 숨김은 이미지 권한과 별개다.

준비된 홈에만 비모달 안내를 자동 표시한다. 서버 순서에서 오늘숨김 아닌 첫 유효 후보1개를 실제 표시한 뒤 탭의 표시완료를 기록한다. 닫은 직후 다음 안내는 띄우지 않는다. 오늘숨김은 ID별 한국 다음날00:00까지이며 문구 수정으로 초기화되지 않는다. 저장소가 막히면 현재 문서 안의 닫기/1회는 유지되나 새 문서/탭의 기억은 보장하지 않는다. 서버시각과 monotonic 경과로 벽시계 오차를 보정하고 bfcache/오래된 응답을 재사용하지 않는다. 상시 polling·실시간 원격 회수는 없다. JS/네트워크 실패에도 홈 본문은 유지한다.

개발 DB에 Popup/Post 예시는 생성하지 않았다. 실제 브라우저/키보드/모바일은 NOT_RUN이며 수동 확인 계획과 저장소 제한은 DEV-04 보고서를 따른다.

## 검증

```bash
.venv/bin/python manage.py test content --settings=config.settings.test --noinput -v 2
.venv/bin/python manage.py makemigrations --check --dry-run
node --test tests/composer*.test.cjs
node --test tests/popups.test.cjs
uv --no-config --cache-dir .cache pip check --python .venv/bin/python
```

테스트는 **실제 PostgreSQL** y3gym_test DB를 생성/폐기하며 dev DB를 초기화하지 않는다. 테스트 미디어 디렉터리는 증거로 남고 누적되므로 자동 삭제하지 않는다. 로그는 새 파일명으로 보존한다. 실패한 이전 로그도 유지한다. 서버/CMS test client·DB 동시성·HTTP는 실제 브라우저 확인과 구분한다.

본점 쓰기는 PostgreSQL advisory transaction exclusive lock(19372001,1), 공개 projection은 같은 shared lock을 DTO 생성까지 유지한다. 최초 빈 상태에서도 동작하고 부모/사진이 섞인 조회를 막는다. 동시 최초 공개/본점변경/비공개, writer→reader 및 reader→writer 양방향 대기를 별도 연결에서 검증한다. 이미지 판정은 관계 FK의 SQL EXISTS이며 모든 Post를 읽는 실험 스캔을 사용하지 않는다. 소규모 사이트용 잠금 범위이므로 대량 트래픽/큰 이미지 변환 때의 대기·성능은 후속 검토 대상이다.

DEV-02도 같은 잠금 경계에서 Trainer+Career 저장·조회 전체를 처리한다. 실제 PostgreSQL28개(기존14+신규14) PASS이며 일반 운영자 Wagtail POST, 약력 소유권/롤백, 동시 이동·지점 비공개·오래된 저장·양방향 조회 대기까지 포함한다. 실제 트레이너 브라우저 조작은 NOT_RUN, 공식 Computer Use는 기존 BLOCKED이며 서버 검사로 대체 PASS를 부여하지 않는다.

DEV-03은 실제 PG46개(기존28+Post18)와 편집기 Node7개 PASS다. PG 검사는 공개/철회·복원·시각·필터/페이지·권한/파일·인덱스 실패 rollback·동시성, Node는 모의 계약1개와 실제 설치 라이브러리 상태 전이6개다. 브라우저 클릭/화면/포커스 검증은 NOT_RUN이다. `PostImageUse`는 공개 대표/본문 참조의 파생 관계 인덱스이며 실제 live_revision과 일치할 때만 공개 권한에 포함한다. 전체 공개 Post를 읽는 스캔은 없다. 기본 action 직접 호출·raw SQL/임의 bulk update·인덱스 수동 변경은 지원 편집 경로가 아니다.

Git P2 후속에서 게시글/Preview/공개 오류 화면의 공통 브랜드·트레이너 메뉴를 복구했다. 셸은 브랜드명과 공개 지점의 공개 트레이너 존재만 조회하고 기존 홈/지점/트레이너는 이미 읽은 결과를 재사용한다. DB 자체 장애 때만 최소 오류 셸로 표시한다. 관련 PG6개 PASS와 제품 PID508585/8766 재적용·보존 근거는 DEV-03 보고서 §7을 따른다. 전체 검토는 재개 대기이며 실제 브라우저는 NOT_RUN이다.

DEV-04 실제 PG68개(기존52+팝업16)/45.162s 및 최초 팝업 Node13개 PASS. Unicode 길이 수정 후 Node16개 PASS는 DEV-04 보고서 §8의 별도 후속 실행 결과다. 기존 공통 이미지·운영자·홈 변경에 따른 회귀를 함께 검사했다. 계산 상태 FieldPanel 오류는 HelpPanel로 수정하고 초기 실패 로그를 보존했다. 현재 제품 PID511334/127.0.0.1:8766, PG456028·SPIKE452717 유지. 원본 데이터/미디어 보존과 적용 후 HTTP13건은 보고서에 기록했다.

## 종료·보존

제품 runserver를 시작한 터미널에서는 Ctrl-C로 해당 서버만 종료한다. 백그라운드 PID는 보고서의 실행 기록과 현재 cwd/uid/명령을 대조한 후에만 SIGINT를 보낸다. 사용자 브라우저 확인 중인 서버는 조율 없이 종료하지 않는다. PG를 종료할 때는 제품 서버/테스트가 사용하지 않는지 확인한 다음:

```bash
python3 scripts/local_pg.py stop
```

이는 프로젝트 pg-data의 pg_ctl만 사용한다. DB·미디어·로그·venv를 지우지 않는다. 운영용 백업/복원·HTTPS/프록시/배포는 아직 검증하지 않았다.
