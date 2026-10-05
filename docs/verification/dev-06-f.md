# DEV-06-F — 승종과 같은 폰트 계열 적용

2026-10-05. **USER_REVIEW_PENDING**. 사용자 요청에 따라 디자인 변경은 개발/로컬 적용/필요 검증 → 사용자 실제 확인·명시적 승인 → Git 검토 순서로 바뀌었다. 이번 변경은 미커밋으로 보존하고 사용자 승인 전 Git 검토로 넘기지 않는다. 추가 수정 요청은 승인이 아니다.

시작 HEAD `92880bcbddb32b73079a4783319892b09e7bea9e`/clean 직접 확인. DEV-06-E는 이 커밋으로 Git 완료이며 이번 F의 사용자 확인과 구분한다. WSL Ubuntu/Linux의 기존 환경과 제품587307/8766·PG456028·SPIKE452717을 사용했다.

## 적용·출처

승종 공개 CSS를 확인한 설계자 전달 근거: SUIT Variable100–900을 기본으로, h1/h2/h3에는 IBM Plex Sans KR600·자간-.025em/행간1.25, hero 행간1.13을 사용한다. 공개 본문/버튼/메뉴는 SUIT Variable, 제목은 IBM Plex Sans KR600으로 변경했다. 본문 행간1.7, 제목/hero 자간·행간을 반영하고 기존 글자 크기·반응형·내용을 유지했다. `font-display: swap`과 Apple SD Gothic Neo/Noto Sans KR/Arial/sans-serif fallback을 선언했다. 새로운 강제 줄바꿈·고정 높이·말줄임 없음.

공식 [SUIT 저장소](https://github.com/sun-typeface/SUIT)와 [IBM Plex 저장소](https://github.com/IBM/plex)의 커밋을 고정해 WOFF2 원본 두 개만 받았다. SUIT2.040(624,536bytes), IBM Plex Sans KR SemiBold1.003 complete/hinted(434,484bytes). 변형/서브셋/변환·CDN/hotlink·새 의존성 없음. 같은 폰트 계열/굵기 적용이며 승종 파일과 버전·바이트 동일성은 미확인이다.

[폰트 출처·원본 URL·커밋·SHA-256·저작권](../../app/assets/fonts/README.md)에 상세 기록하고 OFL1.1 두 원문을 동봉했다. 파일별 라이선스/바이너리 저작권 연도·표기를 임의로 통일하지 않았다. 관리자/Paragraph·템플릿·사진/색상/레이아웃·JS·지도/팝업·모델/API/DB 변경 없음.

## 검증

Git 제외 증거: `app/.runtime/dev-06-f-20261005T115015843765Z/`(0700/파일0600).

- **PASS — 원본/폰트:** 공식 커밋 URL·크기·SHA-256 및 WOFF2 signature/길이 확인. 기존 fc-scan 및 설치된 FreeType의 읽기 API로 metadata 확인: SUIT wght100–900, IBM고정600·버전·가족명·저작권, 한글/라틴 표본 글리프 존재. `font-sources.json`, `font-metadata.txt`, `font-tables.json`. 렌더링 검증은 아니다. 폰트 파일 변환·패키지 설치 없음.
- **PASS — HTTP6건:** CSS·폰트2·라이선스2 응답200/소스 바이트 일치, 폰트 MIME `font/woff2`, CSS `text/css`·UTF-8 디코딩. 홈200·UTF-8이며 E 적용 당시 HTML과 동일. `verification.json`.
- **PASS — 정적 경로:** 기존 STATICFILES_DIRS/assets와 상대 fonts URL 연결, `collectstatic --dry-run --noinput --verbosity 2`에서 두 폰트/동봉 라이선스 수집 확인. 기존 static 산출물 쓰기·운영 배포는 하지 않았다. `collectstatic-dry-run.log`.
- **PASS — CSS 소스:** 제목600과 실제파일 대응, swap/fallback·긴문구 줄바꿈/영역 확장 유지, 기존60/48/36rem 및 reveal/print/reduce/map 규칙 동일. 변경 diff는 폰트/타이포그래피에 한정한다.
- **NOT_RUN — 실제 브라우저:** 폰트 로드 후 실제 렌더·줄바꿈/모바일/확대·미감. 기존 공식 WSL 도구 장애 BLOCKED, 재시도·비공식 우회·설치 없음. 사용자 실제 확인·승인 대기다.
- 기존 PG/Node/full tests·CSS 스냅샷 테스트는 추가/재실행하지 않았다. 폰트/CSS만 변경해 기존 성공 기능 검사를 반복할 이유가 없다. HTTP 점검 스크립트의 첫 실행은 작업 경로 오류로 중단됐고 경로를 바로잡아 위6건을 완료했다; 제품 결함은 아니다.

제품 **PID587307 / 127.0.0.1:8766**을 재시작 없이 유지한다. PG456028·SPIKE452717도 UID/cwd/argv/starttick 전후 동일. 이번 시작/종료 서버 없음. `processes-before.json`, `preservation.json` 참조.

읽기 전용 전후 스냅샷에서8콘텐츠 모델/지도 필드·Post 리비전·이미지 메타·비밀값 제외 계정/그룹/권한 메타·세션수, 제품 미디어16/SPIKE31가 동일하다. `before.json`, `after.json`. dev/SPIKE 데이터·계정/로그인/암호·seed 조작 없음. 비밀파일/암호 해시/세션내용 조회 없음.

## 변경 파일·대기

- `app/assets/site.css`: 자체 폰트 선언·공개 본문/제목 타이포그래피.
- `app/assets/fonts/`: WOFF2두개, OFL두개, 출처 README.
- `AGENTS.md`, `tasks/roadmap.md`: 디자인 사용자 승인 후 Git 검토 예외를 일반 인계 규칙보다 우선하도록 최소 병합.
- `README.md`, `docs/screens.md`, `tasks/current.md`, roadmap 최신 요약·이 보고서: E Git 완료와 F **USER_REVIEW_PENDING** 구분.

설계자가 실제 예약 프롬프트에 새 규칙을 반영하고 PAUSED/기존 이름·주기·대상을 유지했음을 확인했다고 전달했다. 개발 담당자는 예약을 변경하지 않았다. 최종 범위/diff·링크·증거 제외/빈 인덱스를 점검한 뒤 쓰기 중지. Git 검토 요청·staging/commit/push·다른 대화 메시지·새 세션·운영 배포 없음. 사용자 승인 전까지 미커밋 보존한다.
