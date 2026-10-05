# DEV-06-C — 하늘색 디자인·스크롤 진입 효과

2026-10-05 KST. 공개 디자인/모션 구현·로컬 적용 완료, 쓰기 중지·Git 검토 대기. 실제 렌더링·시각 완성·접근성 전체 PASS가 아니다.

## 근거·변경

사용자가 승종 홈페이지의 스크롤 진입 효과와 BRO를 복제한 느낌이 없는 독립 구성·하늘색 주색을 요청했다. 시작 HEAD `525ec2cf0bd73564d41b4dd8baa848b0bd9eed3d`/clean을 직접 확인했다. DEV-05-C Git 검토·정상 push 완료는 설계자 전달과 현재 HEAD를 근거로 기록한다. 적용 지침/README/tasks·DEV-06-B 디자인·DEV-05-C 지도 보고서를 읽었으며 기존 WSL Linux venv/전용 PG를 사용했다. 상위 지침은 앞선 확인과 같고 저장소 하위 지침은 없다.

[참고 홈페이지](https://www.seungjong.co.kr/)의 공개 HTML/CSS를 읽었다. CSS에서 기본 opacity1/transform none, 준비 뒤 opacity0/translateY24px·1초 transition을 확인했다. IntersectionObserver/그룹약80ms 설명은 설계자의 소스 조사 전달 근거다. 실제 브라우저를 관찰하거나 소스를 복제하지 않았다. 증거 `reference.html`·`reference.css`는 제품 자산으로 쓰지 않는다.

- 주색 `#78D3F8`, 얼음색 `#F2FAFD`·흰색, 남색 `#132B40`, 작은 링크 `#075B83`로 교체했다. hover/배지/필터/푸터/팝업/지도 버튼·focus까지 공개 CSS의 오렌지·크림을 제거했다. 시스템 글꼴 유지, 새 폰트/CDN/패키지 없음.
- 첫 화면은 제목/설명/문의 버튼을 중심으로 위에 배치하고 넓은 사진을 아래에 둔다. 지점 소개는 가로형 사진+안내 행, 트레이너는 단순한 사진/약력 카드, 공통 제목·얇은 선·절제한 라운드·밝은 트레이너 연결 영역으로 정리했다. 본문 폭52rem·모바일 단일 열/긴 문자열 줄바꿈·44px 이상 주요 조작/skiplink/focus를 유지한다.
- 기존 문구/사진·TEST 표식·alt/치수·이미지 contain·고정 순서/조건부 영역·문의/메뉴를 보존했다. 사진 없는 hero는 기존 브랜드/사진 준비 안내와 단순한 CSS 원호를 사용한다. 가상 사업 수치/문구·사진/로고 생성·복제 없음. 관리자 Paragraph/모델/DB/지도 계약 변경 없음.

## 모션과 내용 복구

`assets/reveal.js`를 독립 vanillaJS로 추가했다. 명시한 소개/섹션 제목·지점/트레이너/글 목록 카드만 한 번, 18px 상승·680ms ease-out·같은 부모70ms 간격/상한210ms다. 문장/한글/HTML 내용을 다시 쓰지 않는다. 첫 화면 hero 전체·화면 안/이미 지난 대상, 헤더/푸터/팝업/지도/관리자/글 상세·Preview 본문과 중첩 대상은 제외한다.

SSR/CSS 기본은 전부 보임이다. JS 초기화와 observer 등록에 성공한 화면 아래 대상만 waiting 상태로 바꾼다. API 미지원/초기화·등록·콜백·geometry 오류에는 모든 내용을 즉시 보이고 중지한다. 250ms 검사에서 실제 화면에 들어온 뒤500ms 유예를 주고도 콜백이 없으면 즉시 보인다. 이미 화면 위로 지나갔으면 유예 없이 보인다. 정상 observer 동작을 먼저 허용하면서 콜백 단절을 복구하는 장치이며 브라우저 타이머 스케줄링의 절대 시간 보장은 아니다.

reduced-motion 시작/실행 중 변경, 기존 포커스·focusin(대상 조상 포함), 직접 hash/페이지 내 anchor/hashchange, print, pagehide/pageshow·bfcache, 문서 숨김에서 내용이 남지 않게 표시한다. CSS에도 reduced-motion/print 표시 fallback이 있다. 해당 페이지에서는 다시 감추지 않는다. 스크롤/터치/휠/히스토리 제어·패럴랙스·반복 효과·외부 요청 없음. 기존 popup/Google 지도 스크립트는 수정하지 않았고 스크롤로 지도를 열지 않는다.

설계자 코드 검토에서 두 경계를 보강했다. 처음 구현은 waiting 대상만 focus/hash에 반응해 entering 지연/전환 중 초점이 잠시 희미할 수 있었다. armed 전체에서 전환/지연도 즉시 제거하도록 수정했다. 또 최초 복구 검사가 정상 observer보다 앞서 효과를 생략할 수 있어500ms 유예를 추가했다. 두 항목을 모의 회귀에 추가해 최종 통과했다. 실제 브라우저 재현으로 보고하지 않는다.

## 검증·증거

Git 제외 경로: `app/.runtime/dev-06-c-20261005T095151775692Z/`(0700/파일0600). 테스트 미디어/기존 증거를 보존했다.

| 계층 | 결과 | 증거 |
|---|---|---|
| 공개 presentation/shell | **16개/10.417s PASS**. 기존15+SSR visible/영역 제외/로컬 script1회/본문 유지1개. 전용 PG·미디어, 전체 제품 재실행 없음 | presentation-01.log |
| 새 reveal 모의DOM | 최초14개 PASS, 검토 보강 후 **16개/165.161496ms PASS**. 최초보임/1회/지연상한/중복 초기화·API/observer 오류·watchdog/grace·reduce·focus/hash/앵커·print/bfcache·중첩/제외·geometry 복구 | reveal-01.log, reveal-02.log |
| 기존 상호작용 회귀 | **28개/510.487398ms PASS** = popup16+Google지도12. CSS/공통 script 추가에 따른 관련 모의 회귀이며 실제 클릭 아님 | interaction-regression.log |
| 계산 대비 | 주요16조합 PASS. 본문10조합 최소5.26:1(목표4.5), UI/focus6조합 최소3.62:1(목표3). 실제 이미지 배경/전체 WCAG 인증이 아님 | contrast.json |
| 실제 루프백 HTTP | **15건 PASS** = 공개JSON5/HTML6(404 포함)/CSS·JS4. JSON5(meta 제외) 동일, 새 hero/로컬 reveal1회·SSR 숨김 없음·주소/문의/팝업 hook·정적 소스 일치 | http-before.json, http-after.json, http-checks.json |
| 실제 브라우저 | 새 디자인/모션·320px/200% 확대/키보드·실제 Google 지도 위치 **NOT_RUN**. 기존 공식 WSL 경로 장애 **BLOCKED**, 재시도/우회/설치 없음 | 기존 이력 |

상태/대비 계산·모의DOM·서버 HTML PASS를 실제 렌더링 PASS로 대체하지 않는다. Post 초안 저장/Preview/시크릿 공개본 유지의 이전 사용자 한정 보고는 유지하지만 새 디자인 검수로 확대하지 않는다. DEV-05-C 지도 실제 위치/관리자·방문자 브라우저 검증도 별도 미완료다.

## 적용·보존·인계

기존 제품569586의 UID/cwd/전체 명령/starttick 및8766 리스너 inode 소유를 기록과 대조했다. 제품에만 SIGINT·종료 확인 후 README runserver 명령으로 **PID572313 / 127.0.0.1:8766**을 시작·유지했다. 최종 loopback 단일 리스너·PG456028/SPIKE452717 동일 프로세스·기존 제품 종료 PASS. 이번 서버는 사용자 확인용으로 켜 두었다(`processes-before.json`, `server-start.json`, `preservation.json`).

시작/적용직전/적용후 snapshot이 모두 동일하다. Google 새 필드를 포함한8콘텐츠 모델/기존 행·Post 리비전·이미지 메타·비밀값 제외 계정 메타/그룹/권한·세션수·제품미디어16/SPIKE31파일·receipt를 보존했다. 비밀파일·암호 해시/세션키·내용은 조회하지 않았다. migration/seed/개발DB·계정/권한/사진 쓰기 없음. `before.json`, `preapply.json`, `after.json`, `receipt-before.sha256` 참조.

변경은 공개 CSS1·새 revealJS1·템플릿5·관련 검사2와 README/tasks/screens/이 보고서뿐이다. 최종 diff/로컬 문서 링크·범위·Git 제외 증거·staged empty/HEAD 불변을 점검하고 개발 쓰기를 중지한다. 설계자/Git 검토 대기이며 stage/commit/push·다른 채팅으로 직접 보고·다음 기능/운영 배포 없음. 실제 화면/모션 확인과 운영 대상·실자료 검수는 남아 있다.
