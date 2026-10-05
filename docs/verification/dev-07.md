# DEV-07-A — 검증 추적·격리 복원·운영 후보 준비

## 최신 후속 — 제품 Post 초안 사용자 보고 (2026-10-05)

설계자가 일반 채팅으로 요청한 제품 관리자8766 검증에 사용자가 **“2. 정상”**으로 답했다고 전달받았다. 요청은 기존 TEST 공지 본문 끝에 “초안확인용” 표식을 추가하고 일부를 굵게 편집 → Save draft → 재열기·미리보기에서 유지 → 시크릿 `/posts/1/`에서 기존 공개 내용 유지였다. 이 범위만 **PASS(사용자 수동 보고)**로 기록한다. 에이전트 직접 관찰/자동 E2E가 아니며 확인 당시 제품 소스 버전·정확 리비전·브라우저 제품/버전은 미확인이다. 새로운 화면·DB 증거를 수집하지 않았고 이미 한 검증을 재요청하지 않는다.

사진 변경·Publish/Unpublish·과거 복원·다른 관리자 모델·무권한 이미지/JSON·반응형/200% 확대/키보드·새 디자인 시각 완성은 이 응답에 포함하지 않는다. 기존 공개 화면3묶음 보고와 별도이며 SPIKE 결과를 옮긴 것이 아니다. 전체 DEV-07·제품·운영 완료가 아니다.

Google 수동 지도 퍼가기 선택은 완료·다음 DEV-05 후속 구현 대기이며 기존 Naver는 비활성 유지다. 참고 HTML 관찰의 전달 근거·공식 안내는 [DEV-07-B 최신 기록](dev-07-b.md)을 따른다. 이번 후속은 문서 정합화만 수행하고 코드/DB/미디어/서버 변경·테스트 재실행·Git 쓰기 없이 다시 쓰기를 중지했다.

## 이전 후속 — 공개 화면 보고 (2026-10-05)

DEV-07-B 공개 화면3묶음은 **PASS(사용자 수동 브라우저 보고)**다: 홈 TEST 팝업 표시·닫기 후 같은 탭 새로고침 숨김·주소 직접 입력 새 탭 재등장·오늘숨김 후 다른 새 탭 숨김, 트레이너2명의 사진/약력, 공지·이벤트 필터와 상세 굵게/기울임/이미지/지점 안내 보기 링크. 정확한 요청과 “1. 정상 / 2. 정상 / 3. 정상” 답변은 [DEV-07-B 후속 기록](dev-07-b.md)에 기록했다.

에이전트 직접 관찰/자동 E2E PASS가 아니다. 창 좁히기·키보드·확대, 제품 관리자 Trainer/Post/Popup 편집·저장/공개/미리보기/복원, 무권한 이미지 경계 등 답변 밖의 항목은 미검증이다. SPIKE 결과를 제품 관리자 PASS로 확대하지 않는다. 전체 DEV-07·제품·운영 완료가 아니다.

DEV-05-B는 `ac7a48a3d1974e4fae5978fa65accb2c013ae5bf`로 검토·정상 push 완료했다. 설계자의 당시 실제 원격 main=HEAD=origin/main·0/0·clean 확인을 전달받았고 이번 시작 시 같은 HEAD/clean을 직접 확인했다. 지도계정 준비는 미응답이며 아이디/API 필요 여부에 관한 사용자 질문은 가입·키 발급·신청·호출·비용 승인이 아니다. 지도 disabled/키 빈 값·실제 연동 NOT_RUN 유지. 이번은 문서만 갱신하며 테스트/브라우저 재실행과 서버·데이터·환경·Git 변경이 없다. 아래 이전 NOT_RUN/PID/검토 대기 표현은 당시 이력이다.

2026-10-05 KST 최초 실행 이력. **DEV-07-A 로컬 준비물/검증 및 Git 검토·정상 push 완료(`af95456313b7070480aa2d3a7209def229fb5b81`). DEV-07 전체는 실제 제품 브라우저·운영 경계 미검증으로 미완료.**

## 1. 범위·시작 상태

설계자의 배정과 AGENTS.md의 순차 개발 승인을 적용했다. 상위/하위 지침·README·roadmap/current·두 ADR/명세 및 DEV01~06/SPIKE 결과를 확인했다. HEAD `285833feef65bca4ffa4fc52b2fbd9e8838df720`와 clean을 직접 확인했고 DEV-06 검토/정상 push 완료는 설계자 확인을 인계받았다. 지도Q-02 기존 질문은 답변 대기로 유지했다. 질문/지도키·외부지도 호출·무응답 승인·실콘텐츠 생성은 없다.

제품515502/8766·PG456028·SPIKE452717/8765는 시작/종료시 cwd/uid/명령/시작tick이 동일하다. 개발/SPIKE DB를 dump·복제·복원하거나 seed/migrate하지 않았다. 실계정·암호·세션/비밀파일은 조회·복사하지 않았다. 제품 코드/관리자/화면 동작은 변경하지 않고 새 운영 후보 설정·독립 연습 도구만 추가했다. 시스템/서비스·WSL/Docker/방화벽·외부자원 생성 없음.

## 2. 기존 검증 추적 — 이번 재실행과 구분

아래 표는 DEV-07-A 당시 추적이다. 최신 공개 화면·제품 Post 초안 사용자 보고는 위 후속 상태를 따른다. 그 밖의 관리자·접근성·이미지 경계 미검증은 유지한다. 아래 **과거 PASS**는 해당 실행 로그의 서버/DB/Node 계층에 한정한다. UX/API/RV/ENV 전체를 일괄 PASS로 만들지 않는다. 테스트 소스는 `app/content/` 기준이다. 최신 전체 PG76개는 DEV-06의 `app/.runtime/dev-06-20261005T030537172278Z/tests-all-01.log`에 있으며 이번에 반복하지 않았다.

| 추적 ID | 과거 실제 근거 / 해당 파일 | 남은 계층 또는 이번 추가 근거 |
|---|---|---|
| UX-01~03, API-01·02·19, RV-02·05~07·13 | DEV-01 PG14 및 DEV-06 전체 회귀: `tests.py`의 현재값/본점/시설사진·소유권·원자성/별도 PG 동시성. `app/.runtime/tests-05.log` | 소개/지점/시설사진 정상 흐름은 사용자 보고(DEV-01/README), 모든 브라우저 경로를 에이전트가 직접 확인한 것은 아님. 이번 합성 복원에서도 공개/비공개 관계·공개 DTO 비교 |
| UX-04, API-03 | 지도 미구현. location=null/주소·연락처 대체는 DEV-06 `test_presentation.py`/API 검사 | 지도조회·주소변경 응답경쟁·지도 SDK/실패 UX **NOT_RUN**, Q-02 **WAITING** |
| UX-05 | DEV-01 전화/카카오 값·href 검사, DEV-06 지점 수0/1/여러 문의 경로/주소·전화 텍스트 HTML PASS | 실제 외부 연락·모바일 앱 연결 **NOT_RUN**, 실전화/카카오 연락 미실행 |
| UX-06~10, API-04~06·20·21, RV-03·04·14 | DEV-02 PG28: `test_trainers.py`, `app/.runtime/dev-02-20261004T183704528405Z/tests-01.log`. 공개 소속/동일ID 이동·선택직급/약력·권한/정렬·동시성 | 실제 제품 트레이너 편집/모바일 **NOT_RUN**. 이번 합성 복원에서 공개/비공개 소속과 관계 재확인 |
| UX-11~14, API-10~13, RV-10 | DEV-04 PG68: `test_popups.py`, `app/.runtime/dev-04-20261005T023850336094Z/tests-all-01.log`. 글 독립/기간·철회·이미지 SQL EXISTS | 이번 복원 후 고정2030-01-01 UTC의 시작직전/정각/종료정각 후보·이미지 판정 PASS. 실제 브라우저/열린 화면 원격회수 보장 아님 |
| UX-15, API-14 | DEV-04/06 Node16: `app/tests/popups.test.cjs`, DEV-06 `tests-popups-js.log`. 한탭/닫기/오늘숨김·오류·시계·bfcache·Unicode 길이 모의검사 | 제품의 실제 브라우저 닫기/숨김/포커스·모바일 **NOT_RUN** |
| UX-16, API-07~09·18·22·24, RV-01·11 | DEV-03 PG46+후속셸6 및 DEV-06 전체: `test_posts.py`, `test_public_shell.py`; `app/.runtime/dev-03-20261005T021401622565Z/tests-all-01.log`, `app/.runtime/dev-03-shell-20261005T023314552503Z/tests-shell-01.log`. 공개리비전/초안·복원·파일유실·시각·원자성/잠금 | 이번 실제 DB/미디어 복원→공개본/초안/과거리비전·새초안 복원 PASS. 실제 운영 캐시/프록시·백업 정합성은 별도 미검증 |
| UX-17 | DEV-06 PG8/전체76의 의미 있는 HTML·현재메뉴/앵커/heading/조건부영역, 반응형 CSS 구현 | 실제320px/200% 확대·키보드/스크린리더·반응형 **NOT_RUN**. CSS/HTML 검사로 접근성 PASS 부여하지 않음 |
| UX-18, API-17, RV-15 | 고정 데이터/DTO·기능 범위에 가격/PT/고객계정 필드 없음(DEV01~06 소스·계약 검사) | 본문·이미지·팝업의 실사업 가격/문구/사진 수동검수 **NOT_RUN**, 자동OCR 없음 |
| API-15 | DEV-03 `test_posts.py` 안전 HTML/이미지 DTO, 편집기 Node7은 상태/계약 검사 | 제품 별도 프론트 브라우저 소비 **NOT_RUN**. SPIKE 별도 JS 소비자 A 정상 표시만 사용자 보고 PASS(아래); 제품/API 전체 소비 검증으로 확대하지 않음 |
| API-16 | DEV01~04 서버 API 쓰기405/오류/권한·no-store 검사, DEV-06 전체 회귀 | 운영 프록시/캐시 계층 **NOT_RUN** |
| API-23, RV-08~09·12 | DEV01~04 `tests.py`, `test_trainers.py`, `test_posts.py`, `test_popups.py`의 인증/공개범위·원본/표시본·삭제/덮어쓰기 차단 | 이번 복원자료의 보호 이미지/Preview·원본 및 Gunicorn 경계 PASS. 실제 운영 HTTPS/프록시 alias·브라우저 인증/방문자 대조 **NOT_RUN** |
| ENV-01 | WSL/Linux venv·Django/Wagtail/PG 실행 및 사용자 개발관리 로그인 보고. DEV01~06 보고서 | 이번 Python3.14.4/Gunicorn26.2 로컬 WSGI 후보 PASS. 별도 상용 Linux/운영 관리자 **NOT_RUN** |
| ENV-02 | Linux 경로/정적/사진 변환의 서버/HTTP PASS(DEV01~06) | 이번 collectstatic89파일·실제 WSGI 공개/보호미디어 PASS. 실제 외부정적/프록시/TLS **NOT_RUN** |
| ENV-03 | DEV-04 PG 시간경계/KST·Node 벽시계/monotonic PASS | 이번 고정 시각 복원 경계 PASS. 실제 Windows/모바일 sleep/시간·브라우저 **NOT_RUN** |
| ENV-04 | DEV-06 PG76개/45.399s 과거 PASS, 실제 별도 연결 동시성 포함 | 이번에는 전체76개 재실행 없음. 실제 별도PG DB 생성→dump/restore·복원자료 검사만 새 실측 |
| ENV-05 | 이전 개발 no-store·관리자/미디어 경계 | 이번 production 설정 fail-closed/securecookie/Host/CSRF·DEBUG=False·Gunicorn 모의proxy PASS, check --deploy **WARN1**. 실제 운영/TLS·상용DB연결/프록시 **NOT_RUN** |
| ENV-06 | DEV01~06 로컬 코드 적용 시 콘텐츠/미디어 보존 | 이번 합성 전용 실제 pg_dump/pg_restore·파일/참조/공개경계 **PASS(연습)**. 운영 재배포·실데이터 복원·RPO/RTO/보존/암호화/외부보관 **NOT_RUN/TBD** |

**사용자 보고와 직접 관찰:** SPIKE 보고서 §23의 기본 편집·chooser/교체·Save draft·Preview 서식/링크/이미지·기존 시크릿 HTML·파일 덮어쓰기 비활성 UI는 한정 사용자 보고 PASS다. §24 후속 사용자 보고는 별도 JS 소비자의 A 정상 글/굵은서식/이미지 표시만 PASS다. 링크 실제 이동·공개본에 없는 Italic·실패 분기·모든 상태·별도 비로그인 JSON/보호URL 대조는 포함하지 않는다. §25의 공식 Computer Use WSL `sandboxCwd ... local file URI` 장애는 **BLOCKED**, 이번 직접 브라우저 작업은 **NOT_RUN**이며 환경 변화 없이 재시도/우회하지 않았다. 이미 보고된 성공 기본 흐름은 다시 요구하지 않는다.

## 3. 실제 백업·복원 연습

재현 명령은 app cwd의 `.venv/bin/python scripts/restore_drill.py`다. DB/경로/기존백업 인수를 받지 않는 합성 연습 전용이며 운영 복원 도구가 아니다. 실행마다 새24자리 무작위ID와 `y3gym_drill_{id}_src/dst`, `.runtime/restore-drill-{id}/`를 만든다. 실제 프로젝트 test role·정확한0700 Unix socket/port55432, current_user·Unix연결·non-superuser/non-createrole/createdb 조건을 확인한다. PostgreSQL 식별자는 psycopg Identifier로 구성한다.

이번 실행 소유 DB명·OID·owner와 대상의 빈 DB를 확인한다. root/미디어는 현재UID0700·절대경로·symlink 없음, 파일은0600/단일 hardlink/정규파일, manifest는 현재 실행의 정확한ID/경로/필드·덤프/모든 미디어 해시·메모리의 manifest 해시를 대조한다. 실제 restore/미디어 쓰기 전에 검사한다. 기존 DB/backup/디렉터리를 덮어쓰지 않고 dump 파일도 exclusive 생성한다. `--clean`, pg_dumpall, role/system 설정 변경·다른 실행의 DB 청소는 없다.

합성 구성: Site1·공개/비공개Branch2·시설배치1·공개/비공개소속 Trainer2·약력1·Post1(과거공개/현재공개/수정초안 리비전3)·Popup1·합성이미지5(공통/공유/초안전용/과거전용/팝업전용). 유일한 시험 운영자는 non-superuser·unusable password이며 실계정/암호/세션을 읽거나 복제하지 않는다. 본문/인물/연락처는 TEST 자료이고 외부 연락하지 않는다.

원본 migration/seed/snapshot 프로세스가 종료된 쓰기 중지 상태에서 **PG18.6 pg_dump custom**과 미디어복사를 실행했다. 빈 별도DB에 **pg_restore --exit-on-error --single-transaction --no-owner --no-acl** 후 별도미디어에 복사했다. 동일한 고정 시각에서 공개 snapshot/Post/Popup DTO·콘텐츠8모델/관련리비전 해시·미디어 manifest를 비교했다. 정확한 모의시각과 실제 경과시간을 구분했다.

**최종 실행:** `app/.runtime/restore-drill-586076022263344727c98e28/`.

| 검사 | 실제 결과 |
|---|---|
| 도구 | pg_dump/pg_restore PostgreSQL18.6 (Ubuntu18.6-0ubuntu0.26.04.1) |
| 복구점 | `database.dump`467,297bytes·합성 원본/변환본 미디어8파일·SHA-256 manifest. root0700/덤프·manifest0600 직접 확인 |
| 전후 일치 | src/dst snapshot JSON bytes 동일, 공개 DTO·콘텐츠/리비전 참조 해시·미디어 파일 목록/내용 동일 **PASS** |
| 실패 경로 | **11건 PASS(거부)**: dev DB,원본DB,기존DB 생성,경로이탈 manifest변조,manifest symlink,다른 backup root,별도복사본 dump checksum변조,추가 미디어파일,미디어 symlink,비어있지 않은 DB,기존미디어 대상. 잘못된 입력을 pg_restore에 전달하지 않음 |
| 복원 후 실제자료 검사 | **5묶음 PASS**: 공개 HTML/JSON과 최신초안/과거3리비전/관계; 초안·과거전용이미지 비공개/공유이미지 공개/인증 Preview·원본; 고정 팝업 시작전/시작/종료 및 이미지권한; 공유배치 하나 제거 후유지→마지막 공개참조 철회 후차단; 과거리비전→새초안·공개미반영 |
| 경과 | backup0.119700s·restore0.367174s·전체39.138756s. migration/16설정프로세스/WSGI/검증 포함 전체시간이며 **운영 RPO/RTO가 아님** |
| 정리 | 생성한 src/dst만 소유/OID확인 후DROP, 모든 시도에서 가능한8개 DB명이 최종 부재. 합성 backup/미디어/성공·실패로그는 보존 |

보안 경계는 같은 사용자가 실행하는 단일 로컬 연습이다. manifest를 외부 서명으로 인증하거나 악성 로컬 동일UID와 경쟁하는 복원 서비스를 만든 것이 아니다. 부모 검사 이후 경로를 악의적으로 바꾸는 비신뢰 다중사용자 환경/운영 입력을 지원하지 않는다. 파일 백업과 DB dump의 정합성은 이 연습의 쓰기 중지 조건으로 검증했으며, 실제 사용자 업로드가 진행 중인 운영 백업 절차를 완성했다고 하지 않는다.

## 4. 운영 후보 새 검증

Gunicorn26.2.0 한 패키지만 제품 venv/해시 lock에 추가했다. 기존37개 버전 변경 없음, 총38개 pip check PASS. 공식 버전/WSGI/Python 조건·3.14 CI 한계는 [배포 후보 문서](../deployment/linux-candidate.md)에 출처와 함께 기록했다. 새 의존성이 생겼지만 현재 runserver515502는 재시작하지 않았다.

`production.py`/`config.wsgi`/Gunicorn config는 local/test fallback 없이 명시 호스트/HTTPS origin/strong key/PG·분리저장경로를 요구한다. Django는 임의 forwarded 헤더를 신뢰하지 않고 Gunicorn의 정확한 프록시peer allowlist만 반영한다. Gunicorn 제어소켓은 명시적으로 껐다. `rehearsal.py`는 오직 고유 연습DB/media에만 연결한다.

최종 `production-result.json`의 **16개 잘못된 설정**(누락/약한키·wildcard/localhost·HTTP/불일치origin·누락/devDB/adminrole/포트·누락/dev/동일/상대/symlink미디어·원격DB암호누락) 시작거부 PASS. 새 subprocess마다 메모리 생성 시험키·가짜 `gym.invalid`·별도 합성DB·소스트리 밖 임시0700 media/static/tmp만 사용했다. 키/전체settings/env를 출력하지 않았다.

- `check --deploy`: 오류0, **security.W004 WARN1**(HSTS0). 실제 TLS/하위도메인·복구 확인 전 HSTS includeSubDomains/preload를 적용하지 않았으며 경고를 숨기지 않았다.
- `collectstatic`: 새 격리root에 실제파일89개, site.css bytes 일치. 실제 프록시 정적서빙은 NOT_RUN.
- Django 서버검사: secure/host-only CSRF·Secure/HttpOnly 세션쿠키, 일반500 응답의 내부오류/traceback 미노출, nosniff/DENY, 임의 proxy trust없음 PASS. 생성한 세션은 연습DB의 합성자료뿐이다.
- 실제 Gunicorn HTTP **14항목**: 미신뢰peer HTTPS헤더 무시301 / 명시 loopback peer 신뢰200, 공개 site/posts API200, 관리진입302/login200, 보호원본403, 없는경로404, 직접static/media404, 복원공개이미지200, 잘못된Host400, CSRF없는POST403, 실제HTTP redirect301. 본문을 받아 종료했으며 실제 TLS검증은 아님.
- 별도 진입거부 **4건**: restore CLI의 임의 DB인수, WSGI local fallback, 외부bind, wildcard proxy trust. `entry-guards.json`.
- 최종 시험 Gunicorn master **518739/518745**와 자식 workers를 정상 SIGTERM/대기 종료(returncode0), 기본control socket 생성없음을 로그에서 확인. 제품/PG/SPIKE는 보존.

production 임시 저장소 `/tmp/y3gym-production-probe-ihh18xi3/`는 합성 media·수집정적89파일·tmp만 남겼다. 해당 source copy의 원본 합성미디어와 manifest는 위 Git제외 .runtime에도 보존한다. 임시 키는 파일에 저장하지 않았다. 실제 운영 파일/계정/비밀값을 임시 디렉터리에 복사한 것은 아니다.

### 실패·수정 이력

1. `drill-01.log` / run `962b49661ff5f8978fd20ce2`: dump/restore/일치·거부9건 뒤 Gunicorn `forwarder_headers=[]` 타입 오류로 시작실패. 설치버전은 문자열을 요구하므로 빈문자열로 최소수정. 이때 복원 후5묶음은 아직 NOT_RUN. 시험DB 정리·실패로그 보존.
2. `drill-02.log` / run `f35ea605c809f1f41e56c1b1`: 기존9거부·복원5묶음·후보검사 성공. 로그에서26.x 기본 control socket이 `/run/user/1000/gunicorn.ctl`에 잠시 생성된 것을 발견했다. 해당 시험 프로세스 종료 후 socket부재를 확인했고, 후보에는 `control_socket_disable=True`를 추가했다. 시스템 서비스/설정은 변경하지 않았다. 이를 최종 제한된 후보와 동일한 구성으로 보지 않는다.
3. `drill-03.log` / run `b094c78d081b7cab462890ed`: 소켓 확인 보강 중 test role이 `unix_socket_directories`를 읽을 권한이 없어 DB생성 전에 중단. 권한을 추가하지 않고 libpq 연결host/port·Unix서버주소NULL·current_user와 기존 역할속성 검사로 대체했다.
4. `drill-04.log`: 최종11거부/5복원/16설정/14HTTP·제어소켓꺼짐으로 전체 연습 PASS. 최초 libpq `/dev/null` passfile 경고는 빈0600 `pgpass.empty`를 이번 run에 생성하는 방식으로 제거했다. 실비밀번호를 읽거나 담지 않는다.

이 반복은 발견한 후보/안전 경계 변경에 대한 재검증이며 기존76개 전체 서버검사를 이유 없이 반복한 것이 아니다.

## 5. 보존·증거

집계/준비·보존 증거는 새 Git제외 **`app/.runtime/dev-07-20261005T031750484503Z/`**에 있다. `lock-02.log`, `install.log`, `drill-01~04.log`, `entry-guards.json`, `processes-before.json`, `preservation-snapshot.py`, `before.json`/`after.json`, `preservation.json`, `cleanup.json`. 이 폴더 파일0600/디렉터리0700이며 기존 증거를 덮어쓰지 않았다.

각 `.runtime/restore-drill-{id}/`에는 pg_dump/restore log·dump/manifest·src/backup/dst 합성미디어·src/dst snapshot·production-check-deploy/collectstatic/Django checks·Gunicorn log·result가 남는다. 최종 `verification.json`/`production-result.json`도 확인한다. 악성입력 시험용 복사본/의도된 symlink는 해당 run 내부 증거로 남기며 실제 restore에는 사용되지 않았다.

개발 콘텐츠 해시(Site1/Branch2/BranchPhoto1/Trainer0/Career0/Post0/PostImageUse0/Popup0/이미지3/제품Post리비전0)·미디어7파일, SPIKE A공개1/최신19·B3/3/해당content 해시·미디어31파일이 작업 중 전후 및 DEV-06 종료 증거와 동일했다. 실계정/암호/세션은 조회하지 않았으며 DB 전체 바이너리 불변으로 확대하지 않는다. 제품/PG/SPIKE의 동일 프로세스·루프백4개200도 확인했다. 새 제품 예시/권한/계정·실미디어·dev migration/seed 없음.

## 6. 대기 입력·실제 검증을 위한 최소 인계

| 항목 | 상태·이유 | 다음 작업 |
|---|---|---|
| Q-02 지도 | WAITING. 기존 카카오/네이버/나중결정 질문 미응답. 정책/키/쿼터/도메인 미확정 | 기존 답변을 기다림. 반복질문/선택 추정 없음. 조사 근거는 DEV-06 §6 보존 |
| Q-03 실사업 자료 | 브랜드/지점/연락처/사진/프로필·약력/alt·가격내용 수동검수 미완료 | 사용자가 입력한 자료만 선별검수. 가상 사업정보·가격/PT·고객계정/예약을 추가하지 않음 |
| Q-04 운영 대상 | 호스팅/도메인/비용/권한/운영책임/RPO·RTO·보존/암호화·외부보관 TBD | [배포 후보](../deployment/linux-candidate.md)의 대상·비용·복구안을 구체화한 뒤 운영 실행 승인 |
| 실제 브라우저 | 직접 도구 BLOCKED, 제품 통합 NOT_RUN | 공식환경 복구 후 새 화면의320px/확대·키보드 메뉴/앵커/문의 경로/사진→제품 관리자 최신초안/보호URL 인증·방문자 대조→TEST 글/팝업 닫기/오늘숨김/포커스를 한 묶음으로 확인. 이미 성공 보고된 SPIKE 기본편집 재요청 안 함 |
| 실제 운영 경계 | TLS·프록시헤더 덮어쓰기/Host·정적alias·원본우회·리눅스 배포/복원 NOT_RUN | 대상에서 별도 스모크·정합 복구 검증. 루프백 모의https 결과를 실제HTTPS PASS로 쓰지 않음 |

최초 개발 인계 당시에는 사용자에게 질문하지 않고 설계자에게 위 대기와 최소묶음만 전달했다. DEV-08·운영 배포를 시작하지 않았고 전체 Proposed/ENV/UX 또는 DEV-07 전체를 완료로 표시하지 않았다.

## 7. 현재 완료·대기 및 인계 이력

DEV-07-A는 추가 결함 없이 위 커밋으로 검토·정상 push를 완료했다. Git 담당자의 쓰기 종료와 실제 원격 main=HEAD=origin/main·0/0·clean은 설계자가 확인해 전달했다. 이번 문서 정리 시작 시 개발 담당자도 해당 HEAD와 clean을 확인했다. DEV-07 전체·제품 완료나 Proposed 전체 채택을 뜻하지 않는다.

Q-02는 기존 질문 미응답 WAITING으로 재질문하지 않았다. 설계자는 Q-03/04를 한 번 묶어 실제 브랜드·지점·사진·트레이너 자료의 저장 폴더 경로(없으면 준비 중), 보유 도메인/호스팅(없으면 월 운영비 예산)을 요청했고 현재 답변 대기다. 비밀번호/API키는 요청하지 않았다. 사용자 자료·운영 대상 결정과 공식 도구 장애에 의존하는 해당 단계만 대기하며, 기존 성공 확인을 반복 요청하지 않는다.

전체 승인 범위가 남아 heartbeat는 유지한다. 상태 변화 없는 반복 실행은 조용히 종료하고 문서 작업용 새 개발 단위를 만들지 않는다. 이번 상태 정리는 지정된 세 문서만 수정하며 새 구현·테스트·서버 변경·브라우저 재시도·사용자 데이터/계정/미디어 변경 없이 최소 diff/링크 확인 후 쓰기를 중지한다. Git 쓰기는 별도 담당자가 맡는다.

**최초 검토 준비 당시 인계 이력:**

변경은 `app/config/{settings/production.py,settings/rehearsal.py,wsgi.py,gunicorn.conf.py}`, `app/scripts/{restore_drill.py,drill_content.py,production_probe.py}`, Gunicorn requirements/lock, 관련 README·ADR·tasks·배포문서·이 보고서다. review-resolution/SPIKE 및 제품 콘텐츠/공개 코드·화면은 수정하지 않았다. 최종 diff/비밀파일 제외·staged 비어 있음을 점검하고 개발 쓰기를 중지해 설계자→Git 담당자 검토로 인계한다. stage/commit/push는 수행하지 않았다.
