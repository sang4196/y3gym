# DEV-06-H — 배경별 중립색 버튼

2026-10-05. **F+G+H 미커밋 / USER_ACCEPTED / GIT_REVIEW_PENDING**. 버튼 색 추가 수정 당시에는 F/G 미승인이었으나, 후속 사용자 “ㅇㅋ 일단 이정도면 되겠다”(2026-10-05)로 현재 누적 디자인을 수용했다(사용자 보고, 설계자 전달). HEAD92880bcbddb32b73079a4783319892b09e7bea9e와 기존 F폰트·G비율/간격·구조 포커스 수정을 보존했다. 이번 제품 변경은 `app/assets/site.css`의 버튼 색과 푸터 버튼 글자색 우선순위뿐이다.

## 적용

- 흰 본문 주요 행동/지점 전화: 잉크네이비 #1d303b·흰 글자. hover #304650 / active #14252e.
- 어두운 hero 문의: 오프화이트 #f7f6f2·잉크 글자. hover #eef1f2 / active #dce3e6.
- 헤더·푸터·trainer-callout 문의와 secondary(지도/카카오/목록/페이지 이동): 투명 바탕·잉크 테두리/글자. hover는 보조surface #f2f5f6, active #e3e9ec.
- 동적 popup button/a는 기존 흰색/중립회색 계열을 유지했다. 하늘색 버튼 채움·hover/active는 제거하고 작은 장식선과 어두운 배경의 키보드 focus만 유지했다.

기본 `.button`은 색 변수5개를 갖고 컨텍스트에서는 변수만 교체한다. hover→active→disabled 순서로 실제 색을 적용한다. `.button.secondary`는 중립색, hero의 밝은 강조는 `:not(.secondary)`에 한정한다. disabled의 실제 background/color/border 선언은 마지막에 있어 컨텍스트 변수·hover/active보다 우선한다. `.site-footer a:not(.button)`으로 일반 링크 색이 버튼 글자색을 덮지 않도록 했다. popup에는 기존 전용 중립 규칙이 적용된다.

높이44px 이상·초점 표시·구조 outline 제외·hidden/모션 규칙은 유지했다. 템플릿/JS·폰트 파일·레이아웃/본문/사진·관리자/모델/API·콘텐츠 변경 없음.

## 실행 검증

Git 제외 증거: `app/.runtime/dev-06-h-20261005T120926056933Z/`(0700/파일0600).

- **PASS — 색 대비75조합:** 본문/hero/header/callout/footer/secondary/popup의 normal·hover·active 글자/경계/focus, `.button` disabled 글자/경계. 최소 텍스트4.81:1(목표4.5), UI4.38:1(목표3). 투명 바탕은 실제 부모 배경으로 계산,5px 떨어진 focus outline은 주변 surface와 비교했다. disabled도 계산하되 실제 비활성 링크 상태를 구현했다는 뜻은 아니다. `contrast.json`.
- **PASS — CSS 소스 검토:** 실제 템플릿 사용처, 변수/상태·secondary/hero/푸터 우선순위, 기존 popup 규칙과 disabled 마지막 적용 확인. 버튼 하늘색 채움 제거, 버튼 크기/초점·반응형/모션 불변. `css-change.diff`, `verification.json`. 실제 브라우저 계산 스타일 검증과 구분한다.
- **PASS — HTTP11건:** 홈/지점/트레이너/글 목록/상세 HTML5개 시작과 바이트 동일, 공개 JSON5개 meta 제외 동일, 새 CSS200·소스 일치. `http-before.json`, `verification.json`.
- **NOT_RUN — 실제 UI:** 에이전트의 새 버튼 렌더링/클릭/키보드 직접 검사는 미실행이다. 후속 사용자 보고 디자인 수용을 모든 페이지·모바일·키보드·포커스/지도·자동 브라우저 검사 PASS로 확대하지 않는다. 기존 공식 WSL 브라우저 장애는 BLOCKED, 반복 진단·우회·설치 없음.
- CSS 색만 변경하여 PG/Node전체·새 정적 스냅샷 테스트·폰트 등 무관한 성공 검사를 반복하지 않았다.

제품 **PID587307/127.0.0.1:8766**·PG456028·SPIKE452717은 UID/cwd/argv/starttick 전후 동일하고 재시작/종료 없음. 이번 DB·계정·권한·미디어·seed/비밀값 조회·수정 요청 없음. 공개 데이터 유지 근거는 위 HTTP 비교이며 DB 전체/비공개 자료를 새로 비교했다고 주장하지 않는다.

## 사용자 수용·Git 검토 준비

CSS와 이 보고서·README/screens/current/roadmap 안내를 수정한 H 이후, 사용자 디자인 수용을 위 다섯 문서에만 반영했다. F/G 보고서는 당시 이력으로 보존한다. E92880bc는 Git 완료, 현재 F+G+H는 **USER_ACCEPTED / GIT_REVIEW_PENDING**이며 여전히 미커밋·Git 검토 전이다. 설계자가 이후 Git 담당에게 인계한다. 전체 DEV-06/제품 출시 완료가 아니다.

개발 쓰기를 중지한다. 이번 승인 기록 작업에서 코드/CSS/폰트·DB/서버/예약/Git 쓰기·새 테스트·다른 세션 메시지는 없었다. 앞으로도 새 디자인 수정은 사용자 승인 후 Git 검토 원칙을 유지한다. heartbeat PAUSED 유지.
