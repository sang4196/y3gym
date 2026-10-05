# DEV-04 — 기간제 팝업

실행일: 2026-10-05 KST. **구현·실제 PostgreSQL/Node 검사·로컬 적용 완료 / 실제 브라우저 NOT_RUN / Git 검토 대기**.

## 1. 시작·승인

HEAD `e54d34fa27f90800a9c4bd9bf693fa990849ff86`와 clean을 확인했다. DEV-03은 Git 검토/정상 push까지 완료했으며 당시 PG46개/Node7개와 P2 PG6개는 별도 실행 기록이다. 이번 DEV-04의 전체 PG68개 실행과 혼동하지 않는다. 적용 지침은 루트 AGENTS.md이며 상위/하위 추가 지침 없음, README·tasks·screens§8/data§3·10·11/API§5~7·ADR-0002·DEV-03 결과를 대조했다. tasks/current 최상단에 배정·완료 조건부터 기록했다.

근거는 사용자의 순차 진행 승인과 Q-01 “모든 팝업에 게시글 연결 필수”, 설계자의 v1 Post당 최대1개 및 이번 세부 범위다. review-resolution과 SPIKE는 읽기 근거/기존 자료로 보존했다. 독립 팝업·고객계정·추적·외부쿠키·추가 운영서비스·DEV-05·상용 배포는 만들거나 시작하지 않았다.

## 2. 구현·지원 경로

| 영역 | 적용 결과 |
|---|---|
| 관계 | Popup.post 필수 OneToOne/PROTECT, Post당0..1. 중복 선택은 기존 설정 편집 안내. 글은 팝업 없이 공개 가능 |
| 입력 | title200/message1000 일반 텍스트·선택 image/alt200, enabled=false, 시작/종료, priority>=0 기본0. 비활성 준비는 Post 외 미완성 허용. 양쪽 기간이 있으면 항상 시작<종료. 활성은 제목 및 문구/이미지 중 하나와 양쪽 기간 필수 |
| 저장 | 기존 PG 콘텐츠 exclusive transaction lock과 edit_version으로 전체 현재값 저장. 유효한 저장은 즉시 후보 판정에 사용하며 Post 상태/시각/리비전은 변경하지 않음. 실패 rollback·stale 거부. Popup 초안/리비전/Preview 없음 |
| 관리자 | 기존 Wagtail 기간제 팝업 메뉴·일반 운영자 add/change/view. 상태는 비활성→연결 글 비공개→예약→종료→노출 가능 순서로 계산. 방문자별 실제 표시와 다름. 한국 시간 입력/표시, 읽기 전용 HelpPanel/목록에 계산 상태 표시 |
| 공개 API | `/api/v1/popups/active/`, 계약 PopupDTO의 id/title/message/image/starts_at/ends_at/post{id,title,detail_path}와 items/meta.server_time. 선택값 null·문자열ID·UTC Z·no-store. GET/HEAD·쓰기405·질의키400·빈200[]·실제실패500. 관리자도 동일 공개 범위 |
| 후보 | shared lock 후 now1회. Post live/live_revision AND enabled AND starts_at<=now<ends_at, priority ASC/starts_at DESC/PK ASC, 숨은 상한 없음. linked title은 live_revision.content, 수정 초안 제목/내부 우선순위/편집토큰은 응답하지 않음 |
| 이미지 | 동일 후보 조건 Popup.image SQL EXISTS를 기존 Site/Branch/Trainer/Post 공개 참조와 OR 결합. 판정은 shared lock 후 요청시각. 종료/비활성/글 철회 후 다른 공개 참조가 없으면 새 표시본404. 원본/관리자 썸네일은 인증+컬렉션 보호 유지 |
| 보존 | 팝업 영구삭제는 NoDeletePolicy/일괄 삭제 차단, 파일 교체는 새 자산 선택. 기존 파일 덮어쓰기/자동청소 없음. 관계/기간/활성필수/비음수 DB 제약. raw SQL/임의 bulk update는 지원 운영자 쓰기 경로가 아님 |

content.0004_popup은 테이블/제약 추가만 수행한다. 기존 Site/Branch/Trainer/Post 콘텐츠를 변환하지 않는다. 운영자 최소 권한 명령은 기존 그룹이 없으면 실패하며 계정을 생성하거나 저장하지 않는다. 새 패키지·스케줄러·캐시 서비스는 추가하지 않았다.

## 3. 홈 표시·시간·접근성 경계

준비된 정상 홈에만 `popups.js`와 처음에는 숨긴 안내 영역을 포함한다. `/branches/`·`/trainers/`·`/posts/`·상세에는 자동 표시 스크립트가 없다. API를 no-store/자격증명 제외 GET으로 조회하고 서버 순서대로 오늘숨김 아닌 첫 유효 후보 한 개를 표시한다. 실제 DOM 표시 성공 후에만 sessionStorage의 탭 자동표시 플래그를 기록한다. 닫은 직후 다음 후보를 띄우지 않는다. 모두 숨김/빈목록/오류는 표시완료로 기록하지 않는다.

일반 닫기는 실제 표시 플래그로 같은 탭의 연속 탐색에서 유지된다. 오늘숨김은 Popup ID별 localStorage에 **서버시각 기준 한국 다음날00:00** 만료를 저장하며 문구 변경으로 초기화하지 않는다. 잘못된 문자열/비정상 먼 미래 만료값은 숨김으로 인정하지 않는다. 브라우저 저장소 읽기/쓰기/접근 예외를 잡고 현재 문서에서는 메모리로1회/숨김을 유지한다. 저장소를 쓸 수 없으면 새 문서/탭을 넘는 기억은 보장하지 않는다. 탭 복제/열기에서 브라우저가 sessionStorage를 복사하는 동작도 서버의 방문자 식별 기능으로 보정하지 않는다.

벽시계 Date.now 대신 meta.server_time + 요청 전체 monotonic 경과 + 이후 monotonic 경과로 보정한다. 요청 전체 경과를 더해 만료에 보수적인 판단을 하므로 종료 직전 후보를 일찍 제외할 수 있다. DTO/시각/고정 공개 링크·동일 오리진 표시 이미지 URL을 검증하고 삽입 직전 다시 만료를 검사한다. 잘못된 JSON/시각, 네트워크/500은 표시하지 않는다. 15초 넘는 응답/표시 전 만료에는 최대1회 재조회하며 무한 재시도·상시 polling은 없다. 요청 대기도15초에 abort한다. pagehide/탭 비가시성 전환에서 진행 요청과 후보를 무효화하고 표시 영역을 제거한다. bfcache/가시성 복귀 시 미표시 탭에만 새 응답을 사용한다. 이미 열린 화면의 원격 실시간 회수는 범위 밖이다.

안내는 본문 위를 덮는 overlay가 아닌 흐름 안의 작은 비모달 section이며 max-width/높이·내부 스크롤로 본문 접근을 유지한다. 제목/문구는 textContent, 링크·이미지는 검증한 속성으로 만들고 innerHTML을 사용하지 않는다. 제목 연결/aria-live=polite, 실제 button/link, 키보드용 focus-visible 및 스크롤 영역 tabindex가 있다. 표시 시 포커스를 옮기거나 가두지 않는다. 닫을 때 포커스가 사라지는 영역 안에 있을 경우에만 이전 연결된 요소 또는 홈 제목으로 복원한다. 홈 본문은 JS/네트워크 실패와 무관하게 서버 HTML로 이용 가능하다.

이는 구현 계약이다. 실제 Windows 브라우저·모바일 배치·보조기술·키보드·포커스 동작은 NOT_RUN이며 Node 모의 DOM을 브라우저 PASS로 바꾸지 않는다.

## 4. 실제 실행 결과

기존 WSL Ubuntu26.04.1/ext4/Linux Python3.14.4, Django5.2.17/Wagtail7.4.3/Pillow12.3.0/psycopg3.3.6, PG18.6 전용 소켓 클러스터와 Linux Node22.23.2를 사용했다. 새 의존성/시스템/WSL/방화벽/브라우저 설치·외부 바인딩 없음. 실제 브라우저 도구는 기존 WSL 초기화 BLOCKED를 재시도하지 않았다.

```bash
# app cwd, 별도 test role/DB/매 실행 격리 미디어
.venv/bin/python manage.py test content --settings=config.settings.test --noinput -v 2
node --test tests/popups.test.cjs
```

**PostgreSQL68 tests / 45.162s / OK** — 기존52개와 새 Popup16개(일반 CMS/API12·별도 PG 연결 동시성4)를 이번에 함께 실행했다. 공통 이미지 권한/운영자 역할/홈이 변경되어 기존 Site/Branch/Trainer/Post·공통 셸 회귀도 포함했다. 테스트는 TEST 텍스트·비인물 합성 PNG·전용 y3gym_test DB/role/미디어만 사용했고 dev DB에 예시를 만들지 않았다.

| 검사 | 결과 |
|---|---|
| CMS POST | PASS: 생성/현재값 변경/비활성 준비, Post 필수·위조/중복ID·활성필수·기간·길이·음수우선순위 거부, 컬렉션 ID 주입·파일 유실 거부, CSRF·삭제/일괄삭제 방어, stale 및 실제 저장 뒤 주입 오류 rollback |
| 관계/글 독립 | PASS: OneToOne/PROTECT/DB 제약, 팝업 변경 후 Post 전체 행 불변. 비공개 글 제외·수정 초안 제목 불변·재공개 후 최신 공개 제목, 팝업 자체 enabled 유지 |
| 시간/API | PASS: 시작 직전/시작/종료 직전/종료정각(마이크로초), KST 자정·관리자 현지 입력, 단일 now, 순위/시작/ID 동률 순서, 정확한 DTO/null·관리자동일·GET/HEAD/405/400/500/no-store |
| 이미지 | PASS: 시작/종료 경계·글 철회/재공개·비활성·다른 지점 공유/마지막 참조 차단, 보호 원본 인증 차이, 실제 이미지 bytes 검증 |
| 동시성 | PASS: 동일 토큰 동시 저장1개 거부, 팝업 저장/글 철회 모두 직렬 커밋·상호 상태 보존, Popup+Post 공개 writer→reader 완성 커밋 대기, 후보 DTO reader→Popup 비활성/글 철회 대기. 별도 pg_backend_pid 확인 |
| 역할 | PASS: add/change/view_popup3개만 추가·멱등·기존 권한 유지, 계정 save 호출 시 실패하는 검사 |
| 홈/기존 회귀 | PASS: 정상 홈에만 스크립트/숨김 영역, 미준비503 및 다른 페이지 미포함, 기존52개 콘텐츠·미디어·PG 동시성·셸 회귀 |

초기 Popup16개는10.779s에 오류5개였다. 계산 property를 DB FieldPanel에 넣어 폼 렌더링이 실패한 원인이다. DB 상태 컬럼을 만들지 않고 기존 HelpPanel+전용 작은 템플릿으로 바꿨다. 수정 후 위68개 통과, 초기 실패 로그 보존. 모델 migration 차이 없음/check0·migration plan은0004만, 실제0004 적용 OK다.

**새 팝업 Node13 tests / 88.501501ms / PASS**. 서버 순서+ID 숨김·한 탭/새 탭·닫기 후 연쇄 금지, 모두 숨김/빈목록 미소비, KST 만료 정각/문구변경·틀린 벽시계, 저장소 예외/손상, 전송 중 만료·늦은 응답 한 번 재조회, pagehide/bfcache 오래된 응답 무효화, 숨긴 탭/DOM 미표시, 네트워크/500/잘못된시간·URL, 삽입 직전 monotonic 역행 거부, textContent/실제 controls/포커스 복원을 모의 DOM·상태기계로 확인했다. 앞선12개/397.915322ms PASS 뒤 시간 역행 방어를 보강하여13개를 재실행했다. 변경하지 않은 편집기 Node7개는 이번 반복하지 않았다. 브라우저 클릭/화면 PASS가 아니다.

## 5. 적용·보존

content.0004_popup 및 기존 운영자 그룹 add/change/view_popup만 적용했다. 권한 삭제0, 계정/암호/세션 저장·create_operator·seed·초기화·자동 이관 없음. 개발 Post/PostImageUse/Popup은 **0/0/0**이다.

기존 제품 PID508585의 uid1000/cwd app/절대 venv runserver `127.0.0.1:8766 --noreload --insecure`를 다시 확인한 뒤 그 프로세스만 SIGINT 종료했다. 같은 README 명령으로 **새 PID511334 / 127.0.0.1:8766**을 시작해 사용자 통합 확인용으로 유지한다. PG456028·SPIKE452717/127.0.0.1:8765는 그대로다.

전후 읽기 전용 비교에서 Site1/Branch2/사진1/Trainer0/Career0/Post0/PostImageUse0/이미지3의 행 해시, 제품 미디어7파일, SPIKE A공개1/최신19·B3/3/해당 revision content·미디어31파일이 동일했다. 전체 DB/계정/세션 바이너리 동일을 주장하거나 암호 해시를 읽지 않았다.

적용 전 기존 Site/Branch/Trainer JSON3건 기준, 적용 후 무쿠키 공개HTTP13건은 기대200/404/400 및 no-store를 유지한다. 기존 JSON3개는 meta 시각 제외 동일하며 팝업은 items=[]이다. 정상 홈만 새 스크립트/숨김 영역을 포함한다. 실제 `/static/popups.js`·site.css의200 응답 bytes도 제품 파일과 동일하다. 이는 HTTP/서버 응답이며 브라우저에서 JS 실행했다는 근거가 아니다.

증거: Git 제외 `app/.runtime/dev-04-20261005T023850336094Z/`.

- `tests-popups-01.log`(실패), `tests-all-01.log`(최종68), `tests-js-01.log`, `tests-js-02.log`.
- `before.json`, `after.json`, `preservation.json`, `http-before.json`: 기존 콘텐츠/미디어·권한·개발 빈 데이터·공개 HTTP 대조.
- `migration-check.log`, `migration-plan.log`, `migrate.log`, `permissions.log`.
- `server-process.json`, `server.log`, `static-assets.json`: 새 서버/리스너/자산 bytes.

기존 로그를 덮어쓰거나 미디어·DB·venv를 삭제하지 않았다. 비밀번호/세션/비밀값을 기록하지 않았고 스크린샷도 생성하지 않았다.

## 6. 설계자에게 전달할 최소 실제 브라우저 확인

아래는 **NOT_RUN인 수동 계획**이다. 공식 Computer Use의 동일 오류를 재현하지 않았다. 사용자가 만들기로 한 명확한 TEST 자료로 한 묶음만 확인하며 실제 운영 자료나 SPIKE에 실행하지 않는다. 자동 dev 예시가 없으므로 현재 후보가 없는 것은 정상이다.

1. 기존 dev-editor로 제품 Post 한 건을 명시 공개한 뒤 기간제 팝업에 그 글을 선택한다. 현재를 포함한 기간·제목·문구 또는 합성 사진·사용을 저장하고 계산 상태/기간·중복 Post 안내를 확인한다. 비공개 글은 중지로 표시되어야 한다.
2. 새 방문자 탭의 정상 홈에서 작은 안내·제목/문구/사진·자세히 보기와 키보드 닫기/포커스를 확인한다. 닫기→다른 페이지→홈은 재노출하지 않고 다른 화면에서는 자동 표시하지 않는다. 모바일에서도 본문·안내 버튼에 접근 가능해야 한다.
3. 별도 새 탭에서 오늘숨김→다른 새 탭 홈의 숨김을 확인하고, 테스트 설정의 비활성/종료/글 철회 후 새 후보/이미지 요청이 제외되는지 확인한다. 저장소 제한 환경에서는 닫기 동작과 탐색 간 기억 제한을 구분한다. 실제 KST 자정/시계 오차/모든 브라우저 예외는 Node 검사와 별개 미확인이다.

## 7. 인계·미검증

최종 변경 목록·문서·Git 제외 경로·staged 비어 있음·git diff --check를 확인하고 개발 쓰기를 중지했다. 설계자→Git 담당자에게 검토를 인계한다. 변경은 Popup 모델/관리자/마이그레이션·API/미디어·역할, 홈 JS/CSS/템플릿, 서버/Node 테스트, 세 명세/두 ADR/README/AGENTS/tasks 및 이 보고서다. Q-01을 반영해 ‘글의 팝업 추가는 선택, 모든 팝업의 글 연결은 필수’로 정합화했고 review-resolution은 수정하지 않았다.

실제 브라우저·보조기술/모바일/키보드, 네트워크/OS sleep에 따른 실제 브라우저 monotonic/저장소 동작, 대량 후보/트래픽 성능, 상용 Linux/HTTPS/프록시·스토리지·백업복원/운영 배포는 미검증이다. 이미 받은 파일/열린 화면의 원격 회수는 보장하지 않는다. 전체 Proposed를 일괄 Accepted로 승격하지 않았고 Git 쓰기/DEV-05는 수행하지 않았다.


## 8. Git P2 후속 — Unicode 길이 기준 일치 (2026-10-05)

Git 검토에서 제목·문구·이미지 대체설명의 JS String.length가 UTF-16 코드 단위를 세어 Django의 코드 포인트 길이와 다른 결함을 확인했다. 예를 들어 제목 `가 × 199 + 😀`는 서버200자지만 JS201자여서 거부되고, items.every(valid) 때문에 같은 응답의 다른 정상 후보까지 표시되지 않았다.

세 필드의 길이 검사만 Array.from(value).length로 바꿨다. 한도200/1000/200 및 타입 검사·응답 전체 검증은 유지한다. 사용자 눈에 보이는 글자 묶음(grapheme)이나 정규화 기준으로 바꾸지 않았다. 서버·모델·DB·권한·공개 정책 변경은 없다.

관련 Node 회귀는 필드별 BMP 단독, BMP/non-BMP 혼합, non-BMP 단독의 정확한 허용 경계와 1코드 포인트 초과를 검사한다. 경계 후보를 앞/뒤에 놓은 응답에서 실제 createController.load가 첫 정상 후보를 render에 전달하는지 확인하고, 초과 응답은 계속 거부하며 표시 기록을 남기지 않는지 확인했다.

- 수정 전 새 검사 포함 **16개 중13 PASS/3 FAIL, 121.515802ms**: 세 필드의 혼합 경계에서 재현했다.
- 수정 후 **16개 PASS/0 FAIL, 94.3442ms**. 기존13개도 포함한다. Node의 모의 상태/렌더 함수 검사이며 실제 브라우저 실행은 **NOT_RUN**이다.
- 서버 코드는 변경하지 않아 이전 PostgreSQL68개 성공 검사는 반복하지 않았다. 이번에 PG 검사까지 재통과했다고 보고하지 않는다.
- `http://127.0.0.1:8766/static/popups.js` 무쿠키 GET **200**, 제공 bytes와 수정 파일 bytes 동일. SHA-256 `4f6cced507d6f77ce56641d7ab1d51c19a28cd4010146bbf54d8825cdc615dda`. 정적 자산 적용 PASS이며 브라우저 표시 근거는 아니다.
- 제품511334·PG456028·SPIKE452717의 cwd/명령/uid/시작 tick이 요청 전후 동일했다. 서버 시작·종료·재시작 없음. DB/콘텐츠/계정/암호/세션/미디어를 쓰거나 조회하지 않았다. 이번에는 전체 데이터 해시 비교를 반복하지 않았다.

새 Git 제외 증거: `app/.runtime/dev-04-unicode-20261005T025757206979Z/`의 `tests-before.log`, `tests-after.log`, `static-and-processes.json`. 기존 실패/성공 증거는 보존했다.

이번 후속 수정 파일은 `app/assets/popups.js`, `app/tests/popups.test.cjs`, 이 보고서, `tasks/current.md` 네 개다. 기존 DEV-04 변경은 보존했다. 최종 diff 공백 검사·증거 Git 제외·staged 비어 있음을 확인하고 개발 쓰기를 중지하여 설계자에게 Git 재검토를 인계한다. commit/push·DEV-05·실제 브라우저 검증·상용 배포는 수행하지 않았다.
