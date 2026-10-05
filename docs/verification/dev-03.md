# DEV-03 — 공지·이벤트 제품 구현

실행일: 2026-10-05 KST. 상태: **구현·PostgreSQL 서버 검사·로컬 적용 완료 / 실제 브라우저 NOT_RUN / Git 검토 대기**.

## 1. 승인·시작 기준

사용자의 고정 홈페이지 남은 기능 순차 개발 승인과 설계자의 DEV-03 배정을 적용했다. DEV-02의 Git 완료 HEAD `d8bdec0ef8e08f1facb060101fa3f800f5c5c526`와 clean 작업 트리를 직접 확인하고 시작했다. 현재 경로의 상위/하위 지침과 README·명세·두 ADR·기존 검증/작업 기록을 확인했다. 루트 AGENTS.md의 순차 승인과 tasks/current.md의 DEV-03 범위가 유효하며, 이전 SPIKE 한정/DEV-02 착수 전 문구는 이력이다.

쓰기 범위는 app/**와 관련 명세·ADR·README·AGENTS·tasks·이 보고서다. review-resolution 및 SPIKE 소스/SQLite/계정/미디어/venv/서버는 보존했다. 개발 담당자는 Git staging/commit/push/reset/clean/restore/stash를 수행하지 않았다. 새 대화/하위 에이전트·DEV-04·상용 배포를 시작하지 않았다.

## 2. 구현과 지원 경로

| 영역 | 구현 결과 |
|---|---|
| 편집 | notice/event, 제목200자·대표alt200자, 선택 대표 이미지, 연속 RichText Paragraph. SPIKE에서 검토한 native Draftail topToolbar·접힌 이미지 옵션을 제품 경로에 연결. h2/Bold/Italic/목록/안전한 링크/본문 이미지 |
| 공개 검증 | 빈 제목/본문 초안 허용. 공개에는 제목·분류·텍스트 또는 본문 이미지가 필요하며 대표 이미지만 있는 빈 본문은 거부. 이미지 선택권한·행·실제 파일을 저장/복원/공개 시 재검증 |
| 리비전 | 실제 Wagtail DraftStateMixin/RevisionMixin/PreviewableMixin. live_revision이 공개 내용의 기준. 명시적 저장마다 새 리비전; 수정 초안·Preview·과거 버전 복원은 공개본을 바꾸지 않음 |
| 시각 | first_published_at 최초 공개 때 설정·철회/재공개에도 보존. last_published_at은 공개 때만 갱신, Detail.updated_at에 사용. API UTC Z, 화면 최초 공개일 Asia/Seoul |
| 복원 | 기존 revision을 덮어쓰지 않고 새 수정 초안 생성. 복원 화면 Publish 메뉴/위조 POST 차단, 다시 열어 명시적으로 공개. 파일 유실이면 복원/공개 오류·공개본 유지 |
| 원자성 | 관리자 form/revision 저장부터 publish까지 공통 exclusive PG advisory transaction lock(19372001,1). 단건 철회도 같은 경계. stale edit_version 거부. 인덱스 실패 시 내용/시각/리비전/인덱스 전체 rollback |
| 이미지 | PostImageUse(post,revision,image)의 현재 공개 대표/본문 집합만 저장. live 및 index revision=actual live_revision의 SQL EXISTS로 기존 Site/Branch/Trainer 참조와 합침. 전체 Post 스캔 없음. 초안 전용 이미지 비공개, 공유 마지막 참조 철회 때 차단 |
| 공개 조회 | `/posts/`, `/posts/{id}/`, `/api/v1/posts/`, `/api/v1/posts/{id}/`, 홈 최근3건. 동일 공통 projection, 내부 HTTP 호출 없음. 필터/total은 공개 revision category, first_published_at DESC/PK DESC |
| 계약 | Summary/Detail 정확한 필드·문자열ID·null·meta/no-store. category 생략/notice/event, page1·page_size10/최대50. 미지원/중복/잘못된 질의400, 유효 범위 밖 page200 빈목록, 비공개/미존재 동일404·관리자 공개 범위 불변·쓰기405 |
| HTML | p/br/h2/강조/목록/안전한 링크/생성 이미지 allowlist. raw img/script/style·이벤트·위험한 스킴 제거, CMS embed→공개 표시 URL, Preview→인증 보호 URL. 대표/본문 alt escape |
| 권한 | 비최고관리자 운영자 역할에 add/change/view/publish_post만 추가. 계정/암호/세션 save 없음. 기존 이미지 업로드·컬렉션 선택권한·파일 덮어쓰기/삭제 차단 재사용 |

설치 Wagtail7.4.3의 일반 edit/publish/revert/단건 unpublish/bulk 경로를 조사했다. generic 단건 UnpublishView는 모델 unpublish를 직접 호출하지 않으므로 제품 view에서 버전 검사 후 공통 모델 처리로 연결했다. 기본 UnpublishAction은 Page의 permissions_for_user를 기대하므로 제품 모델에서 content.publish_post를 검사한 뒤 내부 action의 중복 검사를 생략한다. 이는 인증 우회가 아니며 무권한 모델 호출 거부를 검사했다.

자동저장/기존 revision 덮어쓰기, 예약/수동 공개 날짜, workflow, Post 일괄 작업 및 copy는 제공하지 않는다. 설치 버전의 snippet bulk는 delete뿐이지만 Post의 모든 bulk action 요청을 명시 차단한다. 일반 삭제는 NoDeletePolicy 및 직접 경로 차단, image 삭제/덮어쓰기 차단은 기존 구현을 유지한다. 과거 revision 직접 publish는 모델에서도 거부한다. raw SQL·임의 ORM bulk update·기본 action 클래스 직접 실행·수동 인덱스 조작은 지원 편집 경로가 아니다. 신규 관리 명령도 공통 모델 경계를 사용해야 한다.

## 3. 실제 검사 결과와 수정 이력

WSL Ubuntu26.04.1 LTS/ext4, 커널6.18.40.1-microsoft-standard-WSL2, Linux Python3.14.4. 기존 제품 Django5.2.17/Wagtail7.4.3/Pillow12.3.0/psycopg3.3.6과 PostgreSQL18.6 전용 소켓 클러스터를 재사용했다. bleach6.4.0/webencodings0.6.1만 제품 venv/해시 lock에 추가했다. 기존35개 패키지 버전 변경 없음, 최종37개 호환 검사 PASS. 시스템/WSL/방화벽/브라우저 설치·외부 바인딩 없음.

최종 실행(app cwd):

```bash
.venv/bin/python manage.py test content --settings=config.settings.test --noinput -v 2
node --test tests/composer*.test.cjs
```

**실제 PostgreSQL46 tests / 32.140s / OK**: 기존 Site/Branch/Trainer28개 + Post18개(일반 CMS/계약14·별도 PG 연결 동시성4). 전용 y3gym_test DB/role와 매 실행 격리 테스트 미디어를 사용했다. 시험 텍스트는 TEST, 사진은 비인물 합성 PNG이며 dev DB에 Post를 만들지 않았다. 테스트 DB는 Django runner의 전용 테스트 수명주기로 생성/폐기하며 기존 dev/실험 DB는 초기화하지 않았다.

| 계층 | 실제 결과·근거 |
|---|---|
| CMS 서버 POST | PASS: 비최고관리자 생성/초안 저장/재열기/공개/철회, 최신 초안 폼값, 새 PNG 업로드/선택, 새 초안 유지와 공개본문/분류/이미지/시각 불변 |
| 복원·검증 | PASS: 과거 리비전 GET·새 초안 복원·별도 재공개, 직접 old publish/복원 중 publish 차단, 빈 초안/공개 필수·길이·분류, 파일 유실 오류와 기존 공개본 유지 |
| Preview·미디어 | PASS(서버): 권한 있는 최신 초안 HTML·보호 이미지 byte검사, 방문자/무권한 Preview 거부, 보호 URL 방문자403·초안 이미지 표시 URL404. 관리자 공개 API는 기존 공개본만 반환 |
| 공유·철회 | PASS: Post간 및 Branch와 공유, 마지막 공개 참조 후 차단, 재공개 시 최초 시각 유지, 잘못된 다른 revision 인덱스가 초안 공개 권한을 주지 않음 |
| API/HTML | PASS(응답): DTO 필드·UTC/null/ID/no-store, 공개 category/total/순서·동률 PK·홈3건·페이지·오류·비공개404, HTML/JSON 같은 공개본, 악성 본문의 실제 공개 출력 allowlist |
| 권한·변경 방어 | PASS: 컬렉션 ID 주입·직접/일괄 삭제·일괄 publish/unpublish·CSRF·overwrite revision 차단. 역할4권한 additive/멱등·계정 save 미호출 |
| 원자성·동시성 | PASS: 실제 관리자 공개 중 인덱스 갱신 실패 전체 rollback. 별도 pg_backend_pid의 동시 publish/publish·publish/unpublish 중 stale1개 거부. writer→reader 완성 커밋 대기와 reader→unpublish 전체 projection 완료 대기 |
| 기존28개 | PASS: Site/Branch/Trainer의 정상·거부·공유 미디어·부모 원자성·동시성 회귀 |
| 편집기 JS | PASS: Linux Node v22.23.2의 Node7개/584.284296ms. 제품 JS 연결의 모의 계약1개 + 실제 설치 Wagtail/Draft 라이브러리 state transition6개. 클릭/화면/포커스/IME/브라우저 렌더링 근거가 아님 |
| 최종 템플릿 | PASS: API UTC machine datetime 보존 및 한국 날짜 경계(UTC16시→다음날 KST), 두 게시글 템플릿 직접 렌더. 실제 브라우저 아님 |
| 실제 브라우저 | NOT_RUN. 공식 Computer Use 기존 WSL 경로 초기화 BLOCKED를 재시도하지 않음. 사용자 DEV-03 결과 보고/캡처도 아직 없음 |

초기 Post16개 실행은 실패1/오류10이었다. 위젯 템플릿을 프로젝트 공용 DIR에 두어 Django 폼 위젯 렌더러가 찾지 못한 문제는 content 앱 templates로 옮겼다. UnpublishAction의 Page 권한 API 차이는 위의 명시적 snippet 권한 검사로 수정했다. Wagtail이 PermissionDenied를 관리자 redirect로 처리하는 경로는 미지원 동작에 명시403을 반환하도록 수정했다. 두 번째 Post16개는 목록의 존재하지 않는 status 속성 오류1개가 남아 실제 DraftStateMixin.status_string으로 수정했다. 이후 복원 자료·권한 추가·동률 정렬 검사를 강화한 최종46개가 모두 통과했다. 실패 로그도 보존했다. 수정 후 실제 브라우저 재검증은 NOT_RUN이다.

check 문제0, makemigrations --check --dry-run 차이 없음. migrate --plan은 content.0003_posts만; 실제 적용 OK. 모델 두 개/제약만 additive하며 기존 콘텐츠 변환 없음. 제품 로컬 적용 전 성공 검사를 이유 없이 반복하지 않았다.

## 4. 로컬 적용·보존 증거

content.0003_posts와 기존 `홈페이지 운영자` 그룹의 add/change/view/publish_post4권한만 적용했다. 기존권한 삭제0, 계정/암호/세션 변경·create_operator 재실행·seed/초기화·실험 이관 없음. 개발 Post/PostImageUse는 **0/0**이다.

기존 제품 PID464276의 uid1000/cwd app/실제 절대 venv 명령을 검증한 뒤 SIGINT로 종료하고 같은 README 명령으로 **PID506850 / 127.0.0.1:8766**을 시작했다. 최초 재시작 스크립트는 상대/절대 명령 표기 차이 검증에서 중단하여 프로세스를 건드리지 않았으며, 실제 절대 경로를 정확히 대조한 재시도로 처리했다. 새 서버는 사용자 통합 확인을 위해 유지한다. PG456028과 SPIKE452717/127.0.0.1:8765는 계속 유지했다.

읽기 전용 전후 비교: Site1/Branch2/사진배치1/Trainer0/Career0/이미지3의 행 해시 동일, 제품 미디어7파일 동일. SPIKE A 공개1/최신19·B3/3와 해당 리비전 content 해시·미디어31파일 동일. 전체 DB/계정/세션 바이너리 동일을 주장하지 않으며 암호/암호 해시를 조회하지 않았다.

무쿠키 공개 HTTP는 적용 전 Site/Branch/Trainer JSON3건, 적용 후 정상8건·404두건·잘못된 query400한건 총11건 확인했다. 모두 기대 상태/no-store. 기존3개 JSON은 meta.server_time을 제외하고 동일, 새 Post API는 정확한 빈 목록/total0, 목록 HTML은 빈 안내다. 실제 브라우저나 별도 JS 소비자 PASS가 아니다.

증거 루트: `app/.runtime/dev-03-20261005T021401622565Z/` (Git 제외).

- `before.json`, `after.json`, `preservation.json`: 콘텐츠/미디어/실험 해시·최소 그룹권한·개발Post0건·HTTP 결과.
- `http-before.json`: 기존 무쿠키 공개 JSON 기준. 응답본문 전체/쿠키/자격증명을 로그로 출력하지 않음.
- `tests-posts-01.log`, `tests-posts-02.log`, `tests-all-01.log`: 실패 이력과 최종 PG46개 결과.
- `tests-js-01.log`: 제품 편집기 Node7개 결과.
- `checks.log`, `dependencies-compile.log`, `dependencies-install.log`, `migrate.log`, `permissions.log`: 최종 점검/해시 의존성/적용.
- `server-process.json`, `server.log`: 확인한 이전 PID·새 PID·루프백 리스너 및 새 서버 로그. 기존 서버 로그를 덮어쓰지 않음.

스크린샷은 만들지 않았다. 비밀번호/세션/비밀값을 문서·코드·로그에 넣지 않았다. 테스트 미디어·기존 로그는 삭제하지 않는다.

## 5. 설계자에게 전달할 최소 수동 확인 묶음

공식 도구는 기존 BLOCKED이며 이 목록은 **미실행 계획**이다. 설계자가 새 제품 흐름의 확인을 한 번에 안내하며 이미 확인된 SPIKE/DEV-01 기본 흐름을 다시 요구하지 않는다. 개발 담당자는 사용자의 기존 브라우저 로그인/탭을 조작하지 않았다.

1. 기존 dev-editor로 `http://127.0.0.1:8766/admin/`의 공지·이벤트에서 사용자가 구분 가능한 TEST 글을 작성한다. Paragraph 서식/링크와 대표·본문 사진을 확인한 뒤 명시적으로 공개한다. `/posts/`, 상세/홈/JSON에서 최초 공개본을 확인한다. 현재 개발 DB에는 자동 생성한 Post가 없다.
2. 같은 글을 수정하여 새 자산 선택·분류/제목 변경 후 Save draft→다시 열기→Preview를 한 번 확인한다. 별도 비로그인 세션은 이전 공개 HTML/JSON과 날짜를 유지하고 초안 전용 표시 URL은 차단되는지 대조한다. 인증 Preview의 보호 이미지 URL은 비로그인에서 차단되어야 한다.
3. 제품 공개/철회 흐름을 확인할 때만 명시적 재공개 후 첫 공개일 유지·분류/본문 갱신을 확인하고 단건 철회로 비공개404를 확인한다. 과거 버전은 새 초안 복원 후 다시 열어 공개하는 흐름이다. 기존 실제 콘텐츠나 SPIKE 글에는 수행하지 않는다.

## 6. 인계·남은 범위

최종 문서·변경 목록·Git 제외 경로·staged diff 비어 있음과 `git diff --check`를 확인했다. 개발 쓰기를 중지하고 설계자→Git 담당자 검토로 인계한다. 주요 변경은 Post 모델/마이그레이션/관리자/폼/본문 변환·조회/권한·미디어/라우트·템플릿/편집기 자산·테스트/의존성 및 관련 문서다. 별도 관리자 프론트/자유 페이지 빌더/고객 로그인/가격/PT 연계 없음.

실제 브라우저/IME·모바일·접근성, 대량 데이터/이미지 변환 성능, 별도 제품 JS 소비자, Popup·지도·완성 디자인, 상용 Linux/HTTPS/운영 프록시/백업복원·운영 배포는 미검증 또는 후속 범위다. Post 표시 URL은 이미 받은 파일을 회수하지 않으며 새 요청의 권한을 판정한다. 두 ADR 및 전체 Proposed를 일괄 Accepted로 승격하지 않는다. DEV-04는 이번에 시작하지 않았다.

## 7. Git P2 검토 후 공통 셸 회귀 수정 — 2026-10-05

Git 담당자는 HEAD d8bdec0/staged 비어 있음에서 검토를 멈추고, 게시글 목록/상세가 base.html의 site/trainer_sections를 전달하지 않아 브랜드가 ‘홈’/빈 footer로 바뀌고 트레이너 메뉴가 누락되는 P2를 보고했다. 설계자 재배정으로 개발 담당자만 수정을 수행했다. 이전 §3의46개 PASS는 이 회귀를 포함하지 않은 당시 기록이며 전체 Git 검토 완료를 뜻하지 않는다.

수정은 HTML 전용 `public_shell`(brand_name, has_trainers)로 공통 헤더/푸터/메뉴의 입력을 명시한 것이다. 게시글 목록/상세는 동일 PG shared lock 안에서 공개 Post projection과 셸을 완성한다. 셸 조회는 Site의 브랜드명 scalar 조회와 Trainer.is_public AND Branch.is_public의 EXISTS 두 건뿐이며 Site 전체 내용·이미지 rendition·약력·다른 게시글 본문을 다시 생성하지 않는다. 기존 홈/지점/트레이너는 이미 읽은 공개 Site/Branch/Trainer 결과에서 셸을 만들어 추가 DB 조회 없이 사용한다. API DTO에 UI 필드를 추가하지 않았다.

관리자 Preview는 공개 브랜드/유효 공개 트레이너 메뉴를 사용하는 확인 가능한 공통 셸을 채택했다. Preview 본문만 인증된 수정 초안이며 이를 공개 조회에 섞지 않는다. Preview의 이미지 검증 오류도 같은 셸이다. 일반400·404·500 HTML 오류는 DB가 가능하면 동일 셸을 유지하며, DB 자체 장애로 셸을 조회할 수 없을 때만 브랜드 fallback ‘홈’과 기본 메뉴/빈 footer를 사용한다. 이 fallback은 실제 조회 실패에 한정하며 미공개 트레이너 링크나 내부 오류 정보를 노출하지 않는다. API 오류는 기존 JSON을 유지한다.

관련 검사만 실제 전용 PostgreSQL에서 실행했다:

```bash
.venv/bin/python manage.py test content.test_public_shell --settings=config.settings.test --noinput -v 2
```

**6 tests / 2.770s / OK**, system check 문제0. TEST 브랜드/비인물 합성 사진·별도 test DB/미디어를 사용했다. 공개 프로필+공개 지점/비공개 프로필/비공개 지점 소속에서 홈·지점·트레이너·게시글 목록·상세의 실제 템플릿 헤더/푸터/메뉴를 비교했다. 정상 및 검증 오류 Preview의 셸, 초안 공개본 불변·방문자 Preview 거부,400/404/500·DB장애fallback, 작은2개 콘텐츠 SELECT·불필요한 이미지/전체 projection 생성 금지, 게시글 API 필드·별도 셸 조회 없음도 확인했다. 이 실행은 서버 렌더링 검사이며 실제 브라우저는 계속 NOT_RUN이다. 무관한 기존46개·Node7개 성공 검사는 반복하지 않았고 새52개 전체 실행으로 합산 보고하지 않는다.

현재 제품 PID506850의 uid1000/cwd/절대 venv runserver 명령을 확인하고 그 PID만 SIGINT 종료 후 **새 PID508585 / 127.0.0.1:8766**으로 재시작·유지했다. migration/의존성/역할 권한 적용은 필요 없었고 실행하지 않았다. 전후 Site/Branch/사진/Trainer/Career/Post/PostImageUse/이미지 행 해시·운영자 권한·제품 미디어7개·SPIKE A1/19·B3/3/해당 리비전·미디어31개는 동일하다. 개발 Post/PostImageUse는0/0, PG456028·SPIKE452717은 그대로다. 계정/암호/세션/시드·운영 환경 쓰기 없음.

적용 후 무쿠키 HTTP11건은 기대200/404/400 및 no-store를 유지했다. 기존 공개 JSON3개는 meta 시각 제외 동일했다. 실제 홈/지점/트레이너/게시글 빈 목록/게시글404의 브랜드·푸터·트레이너 메뉴가 같은 공개 Site/Trainer 데이터와 일치함을 추가 확인했다. 현재 실제 dev Post/Trainer가0건이므로 유효 상세와 트레이너 있음 경로는 위 전용 PG 회귀가 근거다.

증거는 새 Git 제외 경로 `app/.runtime/dev-03-shell-20261005T023314552503Z/`의 `tests-shell-01.log`, `before-full.json`, `after-full.json`, `preservation.json`, `http-before.json`, `server-process.json`, `server.log`다. 기존 증거를 덮어쓰지 않았다. 이번 수정 파일은 publication.py/post_views.py/views.py/post_models.py/base.html과 새 test_public_shell.py 및 이 결과·현재 작업/운영 PID 안내 문서다. 최종 diff 점검 후 다시 개발 쓰기를 중지하고 설계자에게 재인계한다. Git 전체 검토·commit/push·DEV-04는 아직 완료/실행하지 않았다.
