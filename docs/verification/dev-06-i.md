# DEV-06-I — 모바일 탐색·공개 화면 반응형 검토

2026-10-06 KST. **USER_ACCEPTED / GIT_COMPLETE**. 사용자 “ㅇㅋ 확인했다”를 이번 PC/모바일 탐색 디자인 수정안 수용·Git 인계 승인으로 기록한다(사용자 보고, 설계자 전달). 독립 Git 검토에서 차단 결함 없이 승인15파일을 `712377502d4deaa1d914db4391ef610284468f52`로 커밋·정상 push 완료했다. 구현 커밋 직후 HEAD·origin/main·실제 원격 main 일치, ahead/behind0/0·작업 트리 clean을 확인했다. 아래 개발 당시 대기 기록과 구분한다. 시작 HEAD `892bc214ccfbfb92ea73e9453e855da3ccb17d4a`/clean 확인. F+G+H는 사용자 수용 후 b4d3b40로 Git 완료,892bc21은 완료 기록이다. 이 승인을 이번 새 디자인 승인으로 승계하지 않는다.

최신 사용자 신고·자산 버전 보완과 실제 Linux Chromium 검증은 아래 **사용자 회귀 신고 후 보완** 절을 따른다. 최초 브라우저 미실행/PID610422 기록은 당시 이력이며 현재는 PID613857이다.

## 레퍼런스와 적용

[승종 공개 홈페이지](https://www.seungjong.co.kr/)와 [공개 CSS](https://www.seungjong.co.kr/_next/static/immutable/chunks/34c6goc4gxdjl.css)를 GET해 소스 근거로 검토했다. 실제 브라우저 관찰이 아니다. 로고·사진·문구·전체 코드를 복제하지 않았다.

| 영역 | 레퍼런스/현재 문제 | 적용·유지 및 확인 범위 |
|---|---|---|
| 공통 헤더 | 레퍼런스는 모바일44px 토글/펼친 세로 메뉴. 기존은60rem 줄바꿈·36rem2열로 hamburger 누락 | 전체 폭 흰 header/공통 wrap, 브랜드+44px 토글, 메뉴/문의 한 영역. 한국어 메뉴와 긴 브랜드를 고려해 레퍼런스48rem 대신60rem 접힘. 링크 중복 없이 기존 include/current/조건부 트레이너·문의0/1/N 유지 |
| 메뉴 동작 | 모바일 숨김/aria-expanded·controls/열기·닫기 이름/3선→X 필요 | 비모달 disclosure. Esc·메뉴 선택·밖 클릭·focus 이탈·resize·pagehide/bfcache·중복 초기화. 숨길 요소의 초점은 보이는 toggle/첫 링크로 이동(preventScroll). Tab trap/inert/scroll lock 없음 |
| 홈 | 폰트·큰 hero 방향은 유지하되 모바일 사진이 큰 세로 영역을 차지할 수 있음 |48rem 이하 hero16:10·상한20rem/contain. 고정 영역 순서·조건부 섹션/최근3건·popup return/reveal 보존. 원본/TEST/alt 불변 |
| 지점 | 기존 G의 정보 상단 정렬/사진 보조 열은 적합 |60rem 이하 한 열·최대448px 사진·주소 줄바꿈·전화/지도버튼/앵커 유지. 공개 HTML main/이미지 비교, 문의0/1/N PG 확인 |
| 트레이너 | 작은 폭의 사진/약력 밀도와 지점 앵커 필요 |48rem 이하 한 열·사진 상한/contain·약력 줄바꿈 유지. 메타/텍스트 삭제 없음. 실제 레이아웃은 미관찰 |
| 글 목록·상세 | 필터/페이지 이동·본문 가독성 및 긴 제목 필요 |36rem 이하 목록 한 열, 상세52rem 제한/본문 줄바꿈·이미지 contain 유지. Preview/오류 셸은 관련 PG, 공개 글 main은 HTTP 비교 |
| 오류/빈 상태 | 모든 공개 셸에서 같은 탐색 fallback 필요 |400/404 실제 HTTP,500/503·DB 장애/Preview는 관련 PG에서 검사. main/skiplink·복귀 링크 유지 |
| 푸터 | 레퍼런스 모바일 브랜드 전체 행+메뉴/문의 두 열. 기존은 모두 한 열 |60rem 이하 브랜드 전체 행/두 열,22rem 이하 한 열. 긴 문구 min-width0/overflow-wrap 보존 |

헤더는 sticky 대신 **정상 문서 흐름**을 유지해 펼친 패널·확대·앵커/skiplink를 덮지 않는다. 폰트·승인된 중립 버튼색·G 제목/간격은 유지한다. 새 메뉴는 reveal 대상이 아니다. JavaScript 미실행/초기화 실패에는 SSR 메뉴가 보이고 toggle은 숨겨져 있다. 모든 필수 이벤트 등록 후에만 메뉴를 접으며 실패 시 다시 링크를 표시한다. 화면에서 hidden은 CSS display보다 우선한다. 인쇄에서만 CSS가 모든 메뉴 링크를 표시하고 토글을 숨기며, 화면 복귀 시 disclosure 상태/이벤트는 그대로다.

320/375/390/768/1024/1440px(16px 기준) 소스 점검에서 wrap은288/343/358/736/976/1184px, 앞4폭은 접힘 메뉴·뒤2폭은 PC 메뉴다. 모바일 header 브랜드 열은 toggle44px+gap16px를 제외하고 줄바꿈한다.320px 푸터는 한 열,375/390/768은 두 열이다. 홈·지점·트레이너·글·오류/푸터의 minmax(0)/min-width0/줄바꿈·사진 contain·44px 조작과 기존 조건부 영역을 검토했다. **계산식/소스 점검이며 실제 viewport 렌더·전체 가로 넘침 통과가 아니다.**

## 실제 실행 결과

Git 제외 증거 `app/.runtime/dev-06-i-20261005T150023187450Z/`(0700/파일0600).

- **PASS — 메뉴 Node15개:** 상태/aria·열기/닫기·Esc/자연스러운 Tab·링크 기본 이동·밖 클릭/초점 이탈·양방향 resize·pagehide/bfcache·중복 init·API/등록/콜백 실패 fallback·인쇄 취소 후 토글 유지. 최종 `navigation-tests-final.log`15/134.902494ms. 모의 DOM 결과다.
- **PASS — 공통 이벤트 회귀:** 기존 reveal16+popup16. `js-tests-final.log`는 메뉴15 포함47개/302.722873ms다. 이후 인쇄 수정과 preventScroll에는 메뉴15만 다시 실행했으며 반복 실행을 추가 개수로 합산하지 않는다. 지도/전체 PG는 무관해 반복하지 않았다.
- **PASS — PostgreSQL/HTML16개:** presentation/public_shell,6.747초. 메뉴 단일영역·SSR fallback·aria/스크립트/current/조건부 링크·문의0/1/N·공개본문/초안·오류/DB장애 셸. 새 구조 때문에 기존 header 직계 a 검사만 `.brand`로 맞추고 공통 셸 검사를 보강했다. `presentation-tests-01.log`.
- **PASS — 루프백 HTTP14경로:** 공개페이지5+400/404=HTML7, 공개JSON5(meta 제외),새 CSS/JS2. 모든 main 내용/이미지 src·alt와 JSON은 적용 전과 같고 새 공통 헤더·스크립트 전달을 확인했다. 최종 JS 수정 응답도 별도 재확인. `pages-before.json`, `page-0.html`~`page-6.html`, `http-checks.json`, `final-js-http.json`.
- **PASS — 소스/대비:** 위6폭 소스 검토·토글 normal/hover/active의 글자/경계/focus9조합(텍스트4.5/UI3 목표 충족). `responsive-source-review.json`, `toggle-contrast.json`. 실제 CSS 계산 스타일·렌더 결과가 아니다.
- **BLOCKED / NOT_RUN — 공식 브라우저/실제 UI:** 설계자가 이번 공식 초기화1회에서 같은 WSL local-file-URI 오류를 받았다고 전달했다. 창조회/캡처/조작 전 실패. 개발 담당 추가 재시도/우회/설치 없음. `browser-status.json`. 모바일 펼침/터치/키보드/확대·모든 화면 시각 검수·인쇄 출력은 사용자 확인 대기다.

중간 검토 결함: beforeprint에 영구 fallback을 연결한 초기 구현은 인쇄 취소 후 toggle을 복구하지 않았다. 이를 화면 상태를 건드리지 않는 print CSS로 분리하고 ‘인쇄 전후 열린/닫힌 상태와 다시 토글 가능’을 검사했다. 초기 로그는 보존했다. 서버/브라우저 결함 재현 PASS로 확대하지 않는다.

## 로컬 적용·보존·대기

UID/cwd/argv/starttick·루프백 리스너 소유를 확인한 제품587307만 SIGINT 종료하고 README의 같은 명령으로 **PID610422 / 127.0.0.1:8766**을 실행·유지한다. PG456028/SPIKE452717은 신원 동일. `processes-before.json`, `server-apply.json`, `server.log` 참조.

적용 전후 제품 미디어17/SPIKE31파일 해시 동일(`media-preapply.json`, `media-after.json`, `preservation.json`). 제품17은 이번 관찰값이며 이전 G의16과 같은 시점이라고 주장하지 않는다. 공개JSON·main/이미지는 앞의 비교 근거다. DB/계정/권한/암호/세션·비공개 리비전을 이번에 새로 조회/쓰기하거나 seed/migrate 하지 않았다. 테스트는 전용 test DB에만 실행했다. 기존 데이터 전체/비공개 초안 불변을 새 실측 결과로 주장하지 않는다.

변경: base 템플릿·CSS·navigation.js·메뉴 Node 검사·공통 셸 PG 검사, 이 보고서/README/screens/current/roadmap 최신 안내. 관리자·모델/API·폰트/미디어·의존성 변경 없음. 개발 쓰기 중지 후 **USER_REVIEW_PENDING**. 새 디자인 사용자 승인 전 Git 인계/검토·staging/commit/push 금지, 예약 PAUSED 유지. 다른 대화 메시지·예약/새 세션·운영 배포 조작 없음.


## 사용자 회귀 신고 후 보완 (2026-10-06)

**FAIL — 사용자 화면:** PC에서 브랜드 아래 메뉴/문의가 각각 내려가고 모바일에는 작은 빈 버튼이 보인다는 신고를 받았다. 첨부 두 장을 직접 열어 확인했다. 이전 소스/HTTP PASS만으로 실제 제공 경험을 충분히 검증하지 못했다.

증거 `app/.runtime/dev-06-i-assets-20261005T151617543626Z/`의 `user-before-pc.png`, `user-before-mobile.png`, `responses-before.json`, `cause-summary.json`을 따른다. fresh GET의 새 CSS는 소스와 같았지만 HTML은 `/static/site.css` 등 버전 없는 URL을 사용했고 CSS/JS 응답에는 Last-Modified만, Cache-Control/ETag는 없었다.

설계자가 기존 설치된 **Linux Chromium151 / Playwright1.62.1 독립 headless 컨텍스트**에서 새 HTML/JS에 HEAD의 FGH CSS를 공급하자 같은 증상이 실제 재현됐다. PC 헤더174.859px·nav/CTA가 왼쪽 아래, 모바일 토글16×6px·선0×0이다. 동일 검사에서 새 CSS는 PC 헤더85px/브랜드 왼쪽·nav/문의 오른쪽 같은 행, 모바일44×44px/선22×2px였다. `independent-before/`에 스크립트·결과 JSON·4캡처를 복사 보존했다. 이것은 **구 CSS/새 HTML 조합의 재현 근거**이며 사용자 브라우저 캐시 항목을 직접 확인한 것은 아니다. 새 설치·사용자 로그인/프로필 접근·Windows Computer Use 우회는 없었다.

### 최소 변경

1. 공개 전용 `public_static` 태그가 site.css/navigation/reveal/popups/google-maps의 **실제 파일 내용 SHA-256**을 URL의 v에 붙인다. 매 렌더에서 내용을 읽으므로 같은 크기/mtime의 수정과 no-reload 프로세스에서도 자동 변경된다. 수동 날짜 상수/임시 강력 새로고침 의존 없음. base/home/branches의 관련 참조 모두 전환했다. 관리자 static 저장소·공개미디어/폰트 URL은 바꾸지 않았다.
2. CSS가 헤더에 준비 표식을 제공하고 JS는 computed style에서 이를 확인한 뒤에만 메뉴를 접는다. CSS 누락/구버전/검사 API 실패에는 SSR 링크를 계속 표시하고 빈 native toggle은 숨긴다. JS 자체 미실행도 SSR 탐색을 유지한다. 준비된 CSS에서는 기존 PC 한 줄 배치와 모바일44px/3선·X를 유지한다.
3. 기존 StaticFilesStorage/collectstatic 구조를 유지한다. 배포 시 템플릿·assets 소스·수집된 static은 같은 배포 버전이어야 한다. 이번 query 버전은 새 HTML이 기존 캐시 키를 재사용하지 않게 하는 무효화 방식이며 과거 URL을 영구 보관하는 별도 자산 서비스는 아니다.

### 보완 실행 검증

- **PASS — 자산 회귀4+PG/HTML16=20개/7.966초:** 파일 크기·mtime를 보존한 내용 교체 시 URL 변경/구 URL 캐시 보존·새 URL 응답, 공개5자산의 수집 결과/URL 해시 일치, 관리자 URL 불변, 누락/비허용 경로의 무버전 fallback 금지. 공통 셸/관련 템플릿 검사도 버전 URL로 갱신했다. `server-tests.log`.
- **PASS — 메뉴 Node16개/116.451594ms:** 기존15와 CSS누락/구CSS/검사API없음의 탐색 유지. `navigation-tests.log`. 모의DOM 결과다.
- **PASS — 실제 HTTP16건:** HTML7·실제 링크된 버전 자산4(site/navigation/reveal/popups)·JSON5. HTML→URL→파일 바이트 SHA 일치, 홈 main은 script query를 제외하고 동일, 공개JSON meta 제외 동일. 현재 지점에 미등록인 Google 지도 스크립트의 버전/수집 계약은 위 자산 회귀에서 확인했다. `http-after.json`.
- **보존:** 제품17/SPIKE31 미디어 해시 전후 동일. DB/계정/세션/권한/비공개 리비전 조회·수정/seed 없음. `preservation.json`.

610422의 UID/cwd/argv/starttick·리스너 소유를 확인하고 해당 제품만 종료해 **PID613857 / 127.0.0.1:8766**으로 적용·유지한다. PG456028/SPIKE452717 보존. `server-apply.json` 참조. 공식 Windows Computer Use는 여전히 기존 WSL URI 오류이며 위 Linux 독립 렌더와 구분한다. 최종 보완본은 아래 독립 다폭/클릭 검사를 통과했다. 사용자 Windows 브라우저 재확인/디자인 승인은 아직 없다. **USER_REVIEW_PENDING**, Git 인계/쓰기·예약 변경 금지 유지.


### 최종 독립 Linux Chromium 실제 검사 — PASS

설계자가 PID613857을 대상으로 기존 설치 Chromium151/Playwright1.62.1의 독립 비로그인 컨텍스트에서 실행했다. 개발 담당자는 `after-results.json`/스크립트와 최종 CSS해시를 대조하고 PC·모바일 홈/열린 메뉴 캡처를 직접 열어 확인했다. 설계자는 지점·트레이너·글 배치도 캡처로 검토해 추가 차단 문제를 발견하지 않았다고 전달했다. 아래는 모의DOM/소스 검토와 **별도 실제 브라우저 근거**다.

- **36조합:**320/375/390/768/1024/1440px × 홈/지점/트레이너/글목록/글상세1/404. 가로 넘침 없음, PC 브랜드 왼쪽·메뉴/문의 오른쪽 같은 행, 모바일44×44px 토글/22×2px 선·초기 접힘 확인.
- **실제 조작:** Enter 열기·Tab 첫 링크·Esc 닫기/초점 복귀·밖 클릭·메뉴 링크 실제 이동·모바일↔PC resize·인쇄매체→화면 복귀 후 토글·960/961px 경계 통과.
- **실패 조건:** JavaScript 없음/CSS 요청 실패/강제 구 CSS 세 경우 모두 링크를 표시하고 빈 토글은 숨겼다.
- **실제 HTTP 캐시:** FGH CSS를 max-age로 브라우저 캐시에 저장한 뒤 수정 HTML을 일반 reload했다. 구CSS는 force-cache 재조회에서도 추가 서버 요청 없이 캐시에 남고, 새 SHA URL은 별도로 요청돼 정상44px 햄버거가 표시됐다. 사용자 브라우저 캐시를 직접 확인하거나 삭제한 것이 아니다.
- 브라우저 pageerror0. 증거 `independent-after/after.cjs`, `after-results.json`, `after-*.png`이며 `/tmp/y3gym-header-review/` 원본을 복사 보존했다. 최종 CSS SHA와36개 결과의 URL 버전이 일치한다.

Windows 사용자 브라우저·실제 휴대폰/터치·전체 관리자·비공개 미리보기·전체 제품/접근성 인증을 통과 처리하지 않는다. 사용자 확인·승인 전 Git 보류, 예약 PAUSED 유지. 새 설치/환경설정 변경/사용자 프로필 접근/DB 쓰기 없음. 반복 테스트 없이 기록 마감·개발 쓰기 중지한다.


### 사용자 수용·Git 인계 준비 (2026-10-06)

보완 완료 안내 후 사용자 원문 **“ㅇㅋ 확인했다”**를 이번 PC 한 줄 메뉴·모바일 햄버거·캐시 보완 수정안의 수용 및 기존 절차에 따른 Git 인계 승인으로 해석했다(설계자 전달). **USER_ACCEPTED / GIT_REVIEW_PENDING**, 기존15개 미커밋 변경과 HEAD892bc21을 보존한다. 정확한 사용자 브라우저/기기·모든 페이지·전체 접근성/관리자·제품 출시 검증 완료로 확대하지 않는다. 기존 테스트·독립 Chromium 근거와 개발 당시 상태는 이력으로 남긴다.

이번 마감은 README/screens/current/roadmap/이 보고서5개 문서만 갱신했다. 코드/디자인·DB/계정/미디어/서버·Git 쓰기·새 테스트/반복 검사·다른 세션 메시지 없음. 예약 PAUSED 유지. 개발 쓰기를 멈추며 설계자가 이후 Git 담당에게 인계한다. 새 디자인 변경에도 사용자 승인 후 Git 원칙을 유지한다.

## Git 독립 검토 완료 (2026-10-06)

사용자 수용 기록과 지정15파일만 검토·커밋했다. CSS/단일 메뉴·초점/실패 fallback·공개 자산 허용목록/내용 해시·템플릿/회귀 검사와 기록을 검토해 차단 결함을 발견하지 않았다. 서버20·메뉴 Node16 로그, HTTP16·독립 Linux Chromium36조합/조작/fallback/캐시 결과를 확인하고 HTTP 자산4개 및 Chromium CSS의 SHA-256을 현재 소스와 대조했다. 문서 로컬 링크·파일 목록·staged diff 공백 검사 PASS. 런타임 증거/비밀파일은 커밋 대상에 포함하지 않았다.

이번 Git 단계에서는 PG/Node/HTTP/브라우저 성공 검사를 재실행하지 않았고 DB·계정·미디어·서버·예약을 변경하지 않았다. 실제 사용자 기기/휴대폰·Windows Computer Use 복구·전체 접근성/관리자·제품 출시 검증 완료로 확대하지 않는다. 위 사용자 수용·Git 인계 준비 절은 인계 당시 기록이며 최신 Git 상태는 이 절과 머리말을 따른다. 완료 기록5개 문서만 별도 커밋·정상 push 대상으로 마감한다.
