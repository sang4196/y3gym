# DEV-06-E — 승종 레퍼런스 기반 공개 화면 재구성

2026-10-05. 사용자 지정 [승종](https://www.seungjong.co.kr/)을 전체 디자인의 주 레퍼런스로 전환했다. BRO는 이전 이력이다. 시작 HEAD `76b36804ac63a1cca406d0be49ef6b10f0112c70`/clean 직접 확인; DEV-06-D Git 검토·정상 push/원격 일치는 설계자 전달 근거다.

## 변경

레퍼런스의 공개 HTML/CSS에서 확인한 네이비 첫 영역, 좌측 큰 제목·우측 사진, 비대칭 두 열·얇은 구분선·넓은 여백, 밝은 다열 푸터를 기존 콘텐츠로 독립 구현했다. 실제 브라우저 관찰은 아니다. 레퍼런스 이미지·문구·코드·폰트·추가 의존성을 제품에 가져오지 않았다.

홈 main만 전체 폭으로 바꾸고 내부 wrap에 제목·사진을 배치했다. 소개·지점·최근 글은 왼쪽 제목/오른쪽 내용, 트레이너 안내는 밝은 중립색으로 구성했다. 공통 카드의 테두리·그림자·둥근 모서리와 제목 굵기를 줄였고 푸터는 브랜드/메뉴/문의로 나눴다. 하늘색 주요 CTA와 작은 선, 흰색 본문·네이비 hero·따뜻한 중립색 사진 여백/푸터를 함께 사용한다.

홈 고정 순서·조건부 트레이너·최근3건·메뉴/문의0·1·N 경로, 기존 문구/TEST/사진/alt와 contain, 글/Preview 본문 읽기 폭을 유지했다. 긴 제목/설명은 줄바꿈·영역 확장을 허용한다. 태블릿 최근 글의 읽기 폭을 확보하기 위해 **60rem 이하에서 홈 섹션의 제목/내용 열을 접는다**. 기존 글 목록 썸네일 규칙은 건드리지 않았고36rem 단일열을 덮는 높은 specificity 규칙도 추가하지 않았다. hero/푸터는48rem 이하 단일열이다.

기존 reveal.js 및 popup/map JS는 변경하지 않았다. 홈 소개의 제목/본문을 별도 대상으로 배치하되 중첩하지 않고 hero·메뉴·팝업·지도·글/Preview 본문을 새 숨김 대상으로 넣지 않았다. 모델/API/관리자/마이그레이션·콘텐츠/계정 변경 없음.

## 검증·적용

Git 제외 증거: `app/.runtime/dev-06-e-20261005T113812018607Z/`(0700/파일0600). 기존 증거를 덮어쓰지 않았다.

- **PASS — 서버/HTML:** 기존 `content.test_presentation content.test_public_shell`16개, PostgreSQL 전용 test DB,7.361초. 고정 순서/조건부 화면, 문의0·1·N, 공개 셸/오류/Preview·공개본 분리, reveal 연결 검사. `presentation-tests.log`.
- **PASS — Node 모의 검사:** reveal16+popup16+Google map12=44개. 모션 fail-visible/reduce/focus/hash/print/bfcache 및 기존 기능 회귀. `node-tests.log`. 실제 브라우저 결과가 아니다.
- **PASS — 대비 계산:**37조합, 텍스트 최소4.57:1/목표4.5, UI 최소3.14:1/목표3. 새 hero 보조글/라벨과 밝은 푸터 포함. 이미지 내부/전체 WCAG 인증 아님. `contrast.json`.
- **PASS — 소스 점검:** CSS 괄호·변수 참조·수동 diff, 기존36rem/모션/print/reduce/지도 hidden 규칙 보존.60rem 섹션 단일열과 낮은 specificity 확인. 전체 CSS 엔진 파싱·실제 레이아웃은 미실행. `css-review.json`.
- **PASS — 실제 루프백 HTTP14건:** 공개 JSON5개(meta 제외) 시작과 동일, 홈/지점/트레이너/글 목록/상세 HTML5개에서 새 공통 구조/홈 main·중첩 reveal 부재 확인, CSS/JS4개 응답이 소스와 일치. `http-checks.json`, `page-0.html`~`page-4.html`.
- **NOT_RUN — 실제 브라우저:** 새 디자인의 미감·반응형/확대·키보드·모션/Google 위치/관리자 클릭. 공식 도구의 기존 WSL URI 장애는 BLOCKED이며 이번 재시도·우회·설치 없음. 이전 사용자 수동 PASS를 새 디자인 PASS로 확대하지 않는다.

UID/cwd/명령/starttick과8766 루프백 리스너 소유를 확인한 뒤 기존 제품572313만 SIGINT 종료했다. 같은 README 명령으로 **PID587307 / 127.0.0.1:8766**을 시작·적용해 사용자 확인용으로 유지한다. PG456028·SPIKE452717 신원은 그대로다. `processes-before.json`, `server-apply.json`, `server.log` 참조.

시작/적용전/종료 스냅샷이 동일하다:8콘텐츠 모델(지도 필드 포함)·Post 리비전/이미지 메타·비밀값 제외 계정/그룹/권한 메타·세션수, 제품 미디어16/SPIKE31·preview receipt. `before.json`, `preapply.json`, `after.json`, `preservation.json`. 실제 dev/SPIKE DB 쓰기·seed·Publish/Unpublish·계정/로그인 변경 없음. 암호 해시/세션내용/비밀파일은 조회하지 않았다.

## 인계

변경은 공개 CSS·base/home 템플릿3개와 이 보고서·README/screens/current/roadmap의 최신 안내다. 테스트 소스·기능/정책은 추가하지 않았다. DEV-06-D의76b3680 Git 완료와 이번 검토 대기를 구분한다. 사용자 확인 대기 heartbeat는 **PAUSED** 유지하며 예약 변경 없음. 최종 diff/링크·범위·Git 제외/인덱스 점검 후 개발 쓰기 중지, Git 검토 대기. staging/commit/push·다른 대화 직접 보고·다음 기능/운영 배포는 실행하지 않는다.
