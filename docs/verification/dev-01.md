# DEV-01 — 사이트·지점 최초 구현 검증

확인일: 2026-10-05 KST. 시작 HEAD `b8aa5d2`, 작업 트리 깨끗함. 사용자가 설계자의 한정 범위에 “ㅇㅇ 진행해”로 승인했고, 개발 세션에서 구현·검증했다. 전체 홈페이지/정책/운영 배포 승인이 아니다. 적용 지침은 상위/하위 확인 결과 루트 AGENTS.md 하나였으며 README·세 명세·review-resolution·두 ADR·tasks/current를 재확인했다.

## 현재 결론

- **실제 PostgreSQL 서버/CMS 회귀 14개 PASS, 12.091초**(`tests-05.log`). Site/Branch 저장·본점 전환·원자성·동시성·공개 조회·보호 미디어의 아래 범위다. Django test client/force_login 결과는 실제 암호 로그인·브라우저 결과와 구분한다.
- **사용자 브라우저 보고 PASS:** `dev-editor` 숨김 암호 설정과 `8766/admin/` 로그인. 사용자 답변 “암호 설정·로그인 완료”만 근거다. 비밀번호/해시를 조회하지 않았고 에이전트 직접 화면 관찰·캡처는 없다. 후속 답변 “두 흐름 모두 정상”으로 사이트 소개 저장→홈 반영, TEST 본점 이용안내·시설 사진 선택/추가/순서 변경 저장→공개 지점 반영도 **사용자 보고 PASS**다. 실제 브라우저 본점 전환/오류/접근 차단은 별도 미검증이다. 이전 공식 Computer Use BLOCKED를 반복 시도하지 않았다.
- **로컬 HTTP PASS:** 14개 공개·정적·이미지·보호 경로 응답, 별도 재시작 후 공개4경로 동일 콘텐츠. 제품 서버 **PID458245 /127.0.0.1:8766**, 프로젝트 PG **PID456028 /전용 소켓55432**를 사용자 확인용으로 유지한다. PostgreSQL TCP 리스너 없음.
- 기존 SPIKE PID452717/8765·A 공개1/최신19·B3/3·관련 리비전 content 해시·미디어31개 해시가 이전 증거와 일치한다. 계정/세션·전체 DB 불변 주장이 아니다. 기존 코드/자료·열린 탭을 조작하지 않았다.

## 채택 범위와 구현

SiteContent singleton(브랜드명 필수, 나머지 소개/이미지 선택), Branch·BranchPhoto의 한국어 관리자 폼, 공개 홈과 지점 한 페이지의 안정적인 ID 앵커, `/api/v1/site/`·`/api/v1/branches/`를 구현했다. Site/공개 Branch는 저장 즉시 반영한다. 본점 선택과 현재 본점 비공개+대체 공개본점 선택을 **실제 Wagtail 폼**에서 수행한다. 시설 사진은 부모 폼에서 추가·정렬·배치 제거하고 원본 자산은 보존한다.

브랜드100자, 대표소개제목160/문구2000/소개5000, Branch 공개이름100/주소255/전화30/카카오URL300, 짧은소개1000/운영시간1000/휴무255/주차2000/이용안내5000, 사진설명255/alt200자로 정했다. 공개 연락수단은 전화 또는 `https://pf.kakao.com/채널ID` 중 하나다. 사진은PNG/JPEG,5MiB,16M픽셀 제한. DTO 문자열ID/null/[]/UTC server_time/전화 display+href/고정 오류 구조를 적용한다. location과 trainer_section_path는 null이며 지도/Trainer 구현을 뜻하지 않는다.

저장에는 PostgreSQL advisory transaction exclusive lock(19372001,1), 공개 DTO 전체 생성에는 같은 shared lock을 사용한다. 최초 행0개에서도 쓰기를 직렬화한다. 본점 unique/check DB 제약, 최종 상태의 `super().validate_constraints()`와 공개 본점 존재 검사, edit_version 충돌 거부를 병행한다. 폼 선검사에서 본점 유일성을 지연하는 것은 기존 본점 해제 전 새 본점 선택이 거절되는 것을 막기 위해서다. 잠금 내 최종 Model 제약 검사까지 생략하지 않는다.

이미지는 Site/공개 Branch/BranchPhoto FK에 대한 SQL EXISTS로 공개 사용처를 확인한다. Post 전체 리비전을 읽는 O(n) 실험 스캔을 승격하지 않았다. 원본·내부 썸네일/변환본은 인증·컬렉션 권한 경로, 공개 표시본은 고정PNG 변환과 매 요청 현재 참조 확인이다. 모든 동적 응답은 no-store다. 영구삭제/덮어쓰기 직접 경로를 차단하고 이미지 목록 bulk 삭제 메뉴도 제거했다. 권한/파일 누락 시 잘못된 이미지로 대체하지 않는다.

## 실제 환경·준비

WSL Ubuntu26.04.1 / Linux6.18.40.1-microsoft-standard-WSL2 / Python3.14.4 / Bash. 기존 SPIKE venv를 복사하지 않고 app/.venv에 독립 설치했다.

| 구성 | 실제 버전·확인 | 선정 근거 |
|---|---|---|
| Django | 5.2.17 | [공식 다운로드/지원표](https://www.djangoproject.com/download/)의5.2 LTS·패치 확인 |
| Wagtail | 7.4.3 LTS | [공식 호환표](https://docs.wagtail.org/en/stable/releases/upgrading.html#compatible-django-python-versions)의Django5.2/Python3.14 교집합 및 [7.4.3 릴리스](https://docs.wagtail.org/en/v7.4.3/releases/7.4.3.html) |
| Pillow | 12.3.0 | [Pillow Python 지원표](https://pillow.readthedocs.io/en/stable/installation/python-support.html)의12계열/Python3.14, 실제 PNG 처리 |
| PostgreSQL | 18.6, Ubuntu `18.6-0ubuntu0.26.04.1` | [Django PostgreSQL 지원](https://docs.djangoproject.com/en/5.2/ref/databases/#postgresql-notes)14+ 및 [PostgreSQL Ubuntu 안내](https://www.postgresql.org/download/linux/ubuntu/)의 배포 패키지 경로 |
| Psycopg | psycopg/psycopg-binary3.3.6, 실제 libpq180006 | [공식 릴리스](https://www.psycopg.org/psycopg3/docs/news.html)·[binary 설치 안내](https://www.psycopg.org/psycopg3/docs/basic/install.html), 실제 PG18.6 연결·트랜잭션 검사 |

35개 전이 패키지를 requirements.lock 버전/해시로 고정했고 `uv pip check` PASS. 이 조합의 상용 환경/부하/백업 호환을 완료한 것은 아니다.

시스템에 PG/psql/컴파일러 경로가 없었고 `sudo -n true`는 대화형 인증 필요로 실패했다. 암호를 요청하거나 권한을 우회하지 않았다. 공식 Ubuntu APT의 PostgreSQL/client/libpq와 libnuma1/libicu78/liburing2를 다운로드하고 파일 SHA256를 APT 메타데이터와 대조한 뒤 `app/.runtime/pg-root`에 `dpkg-deb -x`로 추출했다. 시스템 패키지 설치·관리 스크립트·APT source 변경·다른 DB서비스 조작 없음. 재현 도구와 정확한 버전/해시는 `app/scripts/download_postgres.py`, `pg-packages.json`에 있다. JIT는 사용하지 않는다.

[공식 initdb](https://www.postgresql.org/docs/18/app-initdb.html)·pg_ctl을 일반 사용자 소유 `.runtime/pg-data`에서 실행했다. `.runtime/pg-socket`0700·peer map·TCP 비활성으로 제한한다. 전용 y3gym_dev는 non-superuser/no-createdb/no-createrole, 별도 y3gym_test는 non-superuser/createdb/no-createrole이며 dev DB CONNECT는 제한했다. 개발용 Django 키는 앱이 로컬 파일에 생성/로드하고 출력하지 않는다. OS 사용자가 소켓과 DB를 소유하는 개발 신뢰 경계이지 상용 접근제어/백업 설계가 아니다.

## 실행 결과와 근거 계층

| 검사 | 결과 | 실제 범위 |
|---|---|---|
| PG migrate/system check | PASS | 실제 y3gym_dev에 마이그레이션 적용, check 문제0, 미반영 모델 변경 없음 |
| 초기/오류 DTO | PASS 서버 | Site 미준비503, 지점 빈items, UTC meta, 알 수 없는질의400/경로404/쓰기405 및 고정 error 구조 |
| Site 폼 저장 | PASS 서버·DB·HTML/JSON | Wagtail POST 생성/수정, singleton 추가 제한, 즉시 반영/이미지 제거 |
| 지점 생성·본점 전환 | PASS 서버·DB | 실제 Wagtail POST 첫공개 자동본점, 다른 공개지점 본점선택, 현재본점 비공개+대체 선택, 마지막 지점 비공개 거부, 오래된 폼 거부 |
| 지점+사진 원자성/소유권 | PASS 서버·DB | 타 부모 inline ID 거부, 하위 저장 후 인위적 예외 시 부모/자식 DB rollback, 실제 폼 추가·순서·배치삭제, 원본 보존 |
| 공개 projection | PASS 서버·DB·HTML/JSON | 관리자세션/익명 동일 items, 비공개 지점 미노출, ID앵커/상세페이지 미제공, null/전화 DTO, SQL 참조 범위 |
| 동시 첫 공개 | PASS PG 별도 연결 | 서로 다른 pg_backend_pid에서 동시 시작, 두 저장 후 본점 정확히1 |
| 동시 본점 변경/비공개 | PASS PG 별도 연결 | 승자 저장/오래된 버전 거부를 허용하면서 본점 부재·중복/비공개본점 없음, 두 지점 동시비공개 중 마지막은 거부 |
| 다중 쿼리 읽기 일관성 | PASS PG 별도 연결 | writer가 미커밋 부모/사진 보유 중 reader 대기→새값 함께; reader가 DTO 생성 중 writer 대기→옛값 함께/이후 새조회 새값 |
| 공유 이미지·마지막 참조 | PASS 서버·PG·파일 | Site와 지점/시설배치 중 하나 남으면200, 마지막 참조 철회 시 익명/관리자 공개 경로404 |
| 보호 미디어 | PASS 서버·파일 | 원본·썸네일·내부변환본 익명403/권한운영자200·디코딩, 컬렉션권한 없는staff403, 기본media/추측/서명형 경로404 |
| 삭제/파일 덮어쓰기 | PASS 서버·파일 | 폼file비활성·교체POST거부/bytes불변; 단일/다중/임시업로드/bulk삭제 GET/POST거부, 지점삭제거부, CSRF/타컬렉션 이미지주입거부 |
| 로컬 HTTP | PASS HTTP·파일 | 공개/정적/로그인가용성200, 공개합성이미지200·PNG확인/비공개표시404, 원본·내부변환본403. 로그인페이지200은 로그인 증거 아님 |
| 일반 운영자 암호 설정·로그인 | PASS 사용자 보고 | 설계자가 전달한 사용자 답변 “암호 설정·로그인 완료”. 직접 관찰/캡처·콘텐츠 편집까지 확대하지 않음 |
| 실제 콘텐츠 폼/공개 화면 | PASS 사용자 보고 | 소개 문구 저장→공개 홈 반영, TEST 본점 이용안내·시설 사진 선택/추가/순서 변경 저장→공개 지점 문구/사진/순서 확인. “두 흐름 모두 정상”. 본점 전환/오류/접근 차단은 포함하지 않음 |

최종 전체14개 실행은 `app/.runtime/tests-05.log`의12.091초 PASS다. 앞선 `tests-04.log`의14개/10.498초 PASS 이후 설계 검토에서 최종 Model 제약 검증을 보강하여 재실행했다. `media-regression-01.log`는 삭제 메뉴/경로 보강 후 관련1개/0.900초 PASS이며 최종 전체14개에 포함되는 검사다. 성공 건수를15개로 합산하지 않는다.

초기 실패 로그 tests-01~03도 보존했다. 테스트 도구의 응답context 접근/닫힌 파일·연결/TransactionTestCase 초기 collection/cluster 메모리상태 검사를 정정했다. 실제 폼 결함은 (1) 저장 거부 후 Wagtail 오류 메시지 속성 누락으로500, (2) 신규 부모의 modelcluster FakeQuerySet이 `values_list('pk')`를 지원하지 않음이었다. 최소 변경으로 오류 속성을 설정하고 객체의 pk를 열거하도록 고쳤으며 최종 폼 회귀가 통과했다. 설계자의 제약 검토를 반영해 폼 선검사 지연과 잠금 내 최종 상위 제약 검증을 분리했다.

## 데이터·프로세스·증거 보존

새 개발 자료만 명백한 TEST로 생성했다: Site1, Branch2(공개 TEST본점/비공개 TEST준비지점), 시설배치1, 합성PNG3개. 주소/전화는 테스트 표식이며 실제 정보가 아니다. 사용자가 암호를 설정한 후에는 demo·계정/권한 수정·seed·초기화를 재실행하지 않는다. 사용자 편집이 시작되면 위 개수는 생성 당시 기록으로 취급한다.

초기 제품PID457075를 최종 폼/문구/삭제메뉴 적용을 위해 소유uid/cwd/명령 확인 후 SIGINT로 정상종료하고 PID458245로 같은 loopback 명령을 재시작했다. 직전/직후 Site/Branch/BranchPhoto 전체 모델값 hash·이미지목록·미디어5개 hash 동일, 공개홈/지점HTML bytes와 JSON data/items 동일(meta.server_time은 요청별 차이). 계정·세션이나 전체 PG DB 해시는 조사하지 않았다. 새 PID도 127.0.0.1:8766만 리스닝 확인. PG PID456028은 전용소켓으로 유지, SPIKE PID452717은 그대로다. 현재 사용자 확인을 위해 제품 서버/PG를 종료하지 않았다. 종료 절차는 앱 README에 있다.

Git 제외 증거:

- `app/.runtime/resolve.log`, `install.log`, `pg-packages-manifest.json`, `pg-init.log`, `migrate-01.log`, `environment-01.json` — 준비/버전/role 속성·DB연결 결과. 비밀번호 없음.
- `app/.runtime/tests-01.log`~`tests-05.log`, `media-regression-01.log` — 실패 포함 실제 PG 검사 기록. test DB는 테스트 러너가 생성/폐기하며 테스트 미디어는 남긴다.
- `app/.runtime/spike-preservation-01.json` — SPIKE의 제한된 읽기 전용 content/ref·미디어/프로세스 대조. 비밀값/계정 테이블 조회 없음.
- `app/.runtime/dev-01-20261004T175933016512Z/` — 초기·최종 서버 PID/로그, 공개 HTML/JSON/CSS, HTTP14응답, before/after-restart.json 및 restart-check.json. 기존 로그 덮어쓰기 없음.

스크린샷은 없고 실제 브라우저 근거는 사용자 보고뿐이다. staging/commit/push/reset/clean/restore/stash는 수행하지 않았다. review-resolution과 SPIKE 코드/보고서/README는 이번에 수정하지 않았다.

## 미검증·다음 작업

설계자에게 전달한 후보 중 실제 사용자 질문은 두 정상 흐름으로 한정됐다: (1) 홈페이지 기본 정보 소개 문구 수정·저장→공개 홈 새로고침 반영, (2) TEST 본점 이용안내 수정·시설 사진 선택/추가/순서 변경·저장→공개 지점 문구·사진·순서 확인. 사용자 답변 **“두 흐름 모두 정상”**으로 이 두 흐름만 사용자 보고 PASS다. 에이전트 직접 화면 관찰·캡처는 없으며 신규 자산 업로드의 세부 단계·본점 전환·마지막 비공개 거부·오류/권한 차단의 실제 브라우저 동작을 포함하지 않는다. 이번 브라우저 제품/버전·독립 비로그인 세션 여부도 추가 확인하지 않았다. 서버 POST/PG 동시성/HTTP 근거와 합산하지 않는다.

사용자 편집 이후 현재 내용·버전·사진 개수를 다시 조회하지 않았고 생성/재시작 당시 값으로 되돌리지 않았다. 새 결함이 없어 사용자 재검증 질문이나 성공 테스트 반복은 하지 않는다. 코드/문서 최종 점검 후 쓰기를 멈추고 설계자에게 일괄 Git 검토를 인계한다.

지도/트레이너/제품 게시글/팝업/전체홈 디자인, 전체 UX/API/RV/ENV, 상용 Linux·운영 HTTPS/프록시/스토리지·부하·백업복구·배포는 미검증이다. 소규모 단일 콘텐츠 잠금은 큰 이미지 변환/다수 읽기에서 쓰기 대기를 늘릴 수 있다. raw SQL/임의 ORM bulk update·유지보수 권한은 운영자 폼 보장의 범위 밖이며 같은 저장 경계를 지키는 별도 유지보수 절차가 필요하다. P-01~04/A-01 및 두 ADR은 DEV-01 해당 부분만 한정 채택했으며 다른 부분은 기존 Proposed/TBD다.
