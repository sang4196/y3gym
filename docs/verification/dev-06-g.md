# DEV-06-G — 구조 대상 외곽선·공개 화면 비율 보정

2026-10-05. **F+G 미커밋 / USER_REVIEW_PENDING**. 추가 수정 요청은 F 승인이 아니다. 시작 HEAD92880bcbddb32b73079a4783319892b09e7bea9e와 F의 CSS·폰트/라이선스·지침·문서를 보존했다. 이번 제품 변경은 `app/assets/site.css`뿐이며 사용자 승인 전 Git 검토로 넘기지 않는다.

## 관찰·수정

사용자 첨부1404×870 이미지를 직접 열었다. 지점 전체를 감싼 파란 외곽선, 큰 제목과 소개/지점 사이 여백, 큰 사진과 세로 중앙에 배치된 정보를 관찰했다. 저장된 `user-before.png`는 **사용자 제공 변경 전 화면**이다. 직접 클릭 재현이나 수정 후 스크린샷이 아니다.

소스에서 전역 `:focus-visible`이 `tabindex=-1`인 main·지점 article·트레이너 section·홈 popup-return h1에도 적용됨을 확인했다. 해당 네 구조 대상을 태그/ID·클래스/속성으로 명시한 선택자에만 `:focus`와 `:focus-visible`의 outline:none을 적용했다. 더 높은 specificity의 author 규칙이 기존 전역 및 기본 UA outline을 덮는다. 링크/button/input/select/textarea/summary/skiplink·tabindex0 팝업은 이 선택자에 포함되지 않으며 기존3px focus-visible은 유지한다. id/tabindex·스크롤/Tab순서·hash/reveal·popup return과 JS는 바꾸지 않았다. 실제 브라우저에서의 수정 성공은 미확인이다.

전체 공개 화면을 CSS로 정리했다.

- 공통 폭80→74rem. 내부 h1 최대52px/모바일32–36px, hero 최대64px, h2 최대38px·h3 22px. SUIT 본문·IBM 제목600을 유지한다.
- 섹션/페이지 제목/푸터 간격은32–64px, 내용 간격24–32px 변수로 통일했다. 첫 지점 위 중복 여백도 줄였다. 긴 문구를 자르거나 강제 개행하지 않는다.
- 지점 정보/사진 상단 정렬, 사진 보조 열 최대28rem(448px)·4:3 contain.60rem 이하에서는 지점도 단일열로 바꿔 태블릿 정보 폭을 확보한다. 홈 hero는4:3·높이 상한24rem, 트레이너 사진은 폭24rem·4:5, 글 목록 썸네일은 최대13rem로 줄였다. 시설 사진/기존 이미지의 contain·원본/TEST/alt는 보존했다.
- 보조 surface는 옅은 중립회색 #f2f5f6으로 통일하고 흰색·잉크네이비·sky CTA를 유지했다. 버튼 상태/44px 이상 높이·라운드를 정리하고, 헤더 메뉴는 현재 위치/hover/키보드 focus에서만 밑줄을 표시한다. 본문 링크 밑줄은 유지한다.

사진이 합성 TEST 자료인 한계는 그대로다. 자료를 교체하거나 색/필터/crop으로 숨기지 않았다. 템플릿·JS/지도/팝업·관리자/Paragraph·폰트 바이너리·모델/API/DB정책 변경 없음.

## 검증·증거

Git 제외 `app/.runtime/dev-06-g-20261005T120202017278Z/`(0700/파일0600).

- **PASS — HTTP13건:** 홈/지점/트레이너/글목록/상세 HTML5개는 시작과 바이트 동일, 공개 JSON5개는 meta 제외 동일. 새 CSS·폰트2개 응답200/소스 바이트 일치, font/woff2 확인. `http-before.json`, `verification.json`.
- **PASS — 소스/선택자 검토:** 실제 HTML의 구조 tabindex=-1 대상은 제외 선택자에 포함되고 조작 요소는 미포함. 음수 tabindex를 준 가상 link/button/input/select/textarea/summary도 제외 선택자에 미포함. 전역 focus-visible 규칙·폰트 선언/파일·reveal/print/reduce/지도 hidden 규칙 보존. CSS cascade 검토이지 실제 focus 상태/계산 스타일 검증은 아니다.
- **PASS — CSS 폭 검토:**16px 기준320px 화면에서 wrap288px, 지점/hero/트레이너/푸터 단일열·사진 width100%와 상한으로 수축.60rem 이하 지점 단일열, 이를 넘는961px 기준 지점 내용은 약417px+사진448px+간격48px로 구성된다. 글 목록은36rem 이하 단일열 유지. minmax(0,…)·min-width0·overflow-wrap:anywhere와 높이 자동 확장을 유지했다. 실제320px/태블릿 렌더·전체 오버플로 검증이 아니다.
- **PASS — 대비40조합 계산:** 텍스트 최소4.81:1(목표4.5), UI최소3.14:1(목표3). 밝은 보조surface/버튼 상태·본문/라벨·hero/focus 포함. 이미지 내부/전체 WCAG 인증 아님. `contrast.json`.
- **NOT_RUN — 실제 UI:** 변경 후 클릭·같은/다른페이지 앵커·직접fragment·Tab/키보드/모바일·폰트/미감. 공식 브라우저 기존 WSL 장애 BLOCKED; 이번 재시도·우회·설치 없음. 사용자 첨부 한 장을 새 화면 성공 근거로 쓰지 않는다.
- CSS만 변경했으므로 PG/Node/full tests·새 스냅샷 테스트는 추가/재실행하지 않았다. 템플릿/데이터 훅은 HTML 동일로 확인했다.

제품 **PID587307/127.0.0.1:8766**·PG456028·SPIKE452717은 UID/cwd/argv/starttick이 그대로이며 재시작/종료 없음. 전후 읽기 전용 스냅샷의8콘텐츠 모델/지도필드·Post리비전·이미지메타·비밀값 제외 계정/그룹/권한메타·세션수, 제품미디어16/SPIKE31 동일. `before.json`, `after.json`, `preservation.json`. seed/DB 쓰기·로그인/암호 변경이나 비밀값 조회 없음.

## 사용자 확인 대기

이번 변경 파일: CSS·이 보고서·README/screens/current/roadmap의 최신 요약. F의 WOFF2 두 개·OFL/출처·AGENTS 승인 규칙·F보고서 등 미커밋 자료를 보존했다. 전체 누적 변경은 F+G다. DEV-06-E의92880bc Git 완료와 F+G 미승인을 구분한다.

개발 쓰기 중지 후 **USER_REVIEW_PENDING** 유지. 사용자 실제 확인·명시적 승인 전 Git 담당 인계/검토·staging/commit/push 없음. 추가 수정이면 개발을 계속한다. 예약 PAUSED 유지, 다른 대화 메시지/새 세션/운영 배포·예약 조작 없음.
