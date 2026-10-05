# DEV-06 — 공개 화면 통합·완성

실행일: 2026-10-05 KST. **구현·서버 회귀·로컬 적용 완료 / 실제 브라우저 NOT_RUN / Git 검토 준비**.

## 1. 시작·범위

설계자의 DEV-06 배정과 AGENTS.md의 사용자 순차 개발 승인을 적용했다. 상위/하위 지침·README·최신 화면/데이터/API/검토 근거·두 ADR·DEV 결과·작업 기록을 확인했다. 시작 HEAD `0b3bccb790b6a42bc49da995de5c9d9b8fd5eec7`와 clean 작업 트리를 직접 확인했다. DEV-04 검토/정상 push 완료는 설계자 확인을 인계받았으며 이전 Git 대기 문구는 당시 이력이다.

DEV-05/Q-02는 기존 질문 답변 대기로 두고 독립된 DEV-06만 진행했다. Paragraph 관리자·모델 저장/공개 정책·API 계약은 유지했다. 새 패키지/폰트/CDN/이미지 생성/서비스, 지도 SDK/외부 요청·키·좌표 저장, 예시 행·seed·이관·권한/암호/세션 변경, 운영 배포는 없다. review-resolution과 SPIKE는 읽기 자료로 보존했다. Git stage/commit/push 및 DEV-07은 수행하지 않았다.

## 2. 구현·설계 판단

| 영역 | 적용 내용 |
|---|---|
| 공통 셸 | 공개 브랜드·선택 로고·헤더/푸터 메뉴, 현재 섹션 aria-current, 본문 바로가기·main 포커스 대상. 문의 대상은 공개 지점0개 숨김/1개 해당 branch 앵커/여러 개 지점 목록. 본점으로 임의 연락시키지 않음 |
| 조회 경계 | HTML 전용 public_shell은 브랜드/로고 ID·alt·크기 scalar, 공개 트레이너 EXISTS, 공개 지점 ID 최대2개를 shared lock 안에서 조회. 로고를 위해 사진 rendition/시설/약력/글 DTO를 만들지 않음. 홈/지점/트레이너는 기존 materialized snapshot에서 셸 재사용. Post+셸 조회의 shared 경계 유지 |
| 홈 | 대표 제목/문구·선택 사진·문의 → 소개 → 지점 미리보기 → 존재할 때 트레이너 안내 → 공개 최근3글 → 하단. 없는 자동 영역/사진 슬롯 숨김, Site 미준비503 유지. 최근글 h3, 목록 글 h2로 문맥 분리 |
| 지점 | 한 지점이면 선택 메뉴 숨김. 안정적인 포커스 가능한 앵커, 주소·상세주소, 복사 가능한 전화 텍스트 및 해당 지점 연락 버튼, 입력된 이용안내만 dl로 제공, 시설 사진/캡션·트레이너 연결. location=null이며 지도 대신 주소/연락처 안내 |
| 트레이너 | 공개 지점별 카드, 선택 직급·한줄소개·고정4종 약력의 제목/목록 간격. 비공개 지점·빈 섹션/직급/약력 제외 유지 |
| 게시글 | 분류 현재 상태·KST 공개일·제목·선택 대표사진·빈 결과·이전/다음 페이지. 상세 읽기 폭·긴 한글/URL 줄바꿈·기존 안전 서식/본문 이미지·목록 복귀. HTML에서만 본문 이미지 loading=lazy/decoding=async를 붙여 API body_html은 변경하지 않음 |
| 팝업 | 홈 전용 기존 data hooks/실제 버튼·비모달·내부 스크롤·본문 비가림·포커스 복원 유지. JS 로직 변경 없이 기존 녹색 스타일에 통합. 새로운 JS 없음 |
| 메타 | 화면별 title+공개 브랜드, 홈 공개 소개/지점·트레이너 공개 그룹/목록 분류·페이지/글 실제 공개 본문에서 description. 본문 태그 제거·엔티티 해석·블록 경계 공백/인라인 단어 유지·공백 정리·160코드 포인트 이내. 템플릿 escape, Preview·오류·503 noindex,nofollow. 제공할 홈 설명이 없으면 임의 문구 대신 description 생략 |
| 오류 | 400/404/500·Preview 검증 오류에 같은 공개 셸/상태 안내. DB 자체 장애만 브랜드/트레이너/문의/로고 없는 최소 셸로 처리. 내부 오류 내용 미노출 |

화면 디자인은 밝은 중립 배경 `#fafbf8`, 진한 본문 `#182b25`, 기존 녹색 `#175b47`, 시스템 글꼴로 정했다. 공통 최대72rem, 글 본문48rem, 유동 제목 크기와 섹션 간격, 모바일에서 열을 접고 메뉴를 줄바꿈한다. 고정·겹침 헤더나 추가 모바일 메뉴 JS를 만들지 않았다. 이미지 자체가 있을 때만 4:3/프로필4:5 영역을 사용하고 object-fit:contain으로 자르지 않는다. 대표 사진을 제외한 소개/지점/시설/프로필/목록/본문은 지연 로딩하며 크기·입력 alt를 유지한다. 외부 연락은 실행하지 않았다.

이는 명세 screens §3~7의 배치·문의·표현을 이번 단위에 한정 채택한 결과다. 새 실사업 문구/수치/후기/인물·사업자정보를 만들지 않았다. 운영 도메인 미정이므로 canonical/절대 OG URL·사이트맵·추적은 추가하지 않았다. 전체 Proposed·운영 배포를 일괄 Accepted로 바꾸지 않는다.

## 3. 실제 검증

WSL Ubuntu26.04.1 LTS / 6.18.40.1-microsoft-standard-WSL2 / ext4 / Linux Python3.14.4를 재확인하고 기존 제품 venv·전용 PostgreSQL18.6 클러스터를 사용했다. 새 설치/환경 이동/시스템·방화벽 변경 없음.

| 계층 | 실제 결과·범위 |
|---|---|
| 신규 전용 PG | **8개 / 2.529s PASS**. 0/1/여러 공개지점 문의 대상·숨긴 지점 제외·모든 공개 화면/오류, 공통 로고/메뉴/landmark/제목·escaping, 홈 고정 순서·빈영역·최근3공개글, 지점 주소/전화/선택안내/사진, 공개 리비전 메타와 초안/Preview 분리, 필터·페이지·제목 계층·HTML 전용 이미지 속성/API 불변, DB 장애/400/404/500/503 noindex·본문 발췌 |
| 전체 관련 PG 회귀 | **76개 / 45.399s PASS**(기존68+신규8), system check0. 공통 셸/템플릿·public_snapshot을 모든 콘텐츠 화면이 사용하므로 기존 Site/Branch/Trainer/Post/Popup·미디어/관리자/공개경계 및 PG 동시성을 함께 실행. 이전 셸6개도 로고 scalar/3 SELECT·지점ID LIMIT2·전체 콘텐츠 미조회 계약에 맞춰 보강 |
| 팝업 Node | **16개 / 372.024702ms PASS**. 새 홈 마크업/스타일에서도 기존 data hooks가 유지됨을 서버 HTML 검사와 함께 확인. Node 자체는 모의 상태/DOM 검사이며 브라우저 화면 증거가 아님. Paragraph 코드 미변경이므로 기존 편집기 Node7개는 반복하지 않음 |
| 스키마 | `makemigrations --check --dry-run`: **No changes detected**. migration/운영자 역할 적용 없음 |
| 로컬 HTTP | 무쿠키 공개 JSON5종의 meta 시각 제외 전후 동일. HTML7건의200/400/404·no-store·셸/메타/홈 전용 hook 확인. CSS와 기존 팝업 JS의 실제200 제공 bytes가 파일과 동일 |
| 실제 브라우저 | **NOT_RUN**. 320px~넓은 화면,200% 확대, 실제 키보드/초점·스크린리더, 모바일 사진 배치·오버플로·팝업 스크롤·닫기, 실제 JS 실행/렌더링은 CSS/HTML/Node 성공으로 대체하지 않음 |

실행 명령(app cwd):

```bash
.venv/bin/python manage.py test content.test_presentation --settings=config.settings.test --noinput -v 2
.venv/bin/python manage.py test content --settings=config.settings.test --noinput -v 2
node --test tests/popups.test.cjs
.venv/bin/python manage.py makemigrations --check --dry-run
```

초기 전용 실행은 테스트 파일 생성 명령의 작업 경로 오기로 모듈이 아직 없는 상태였다. 기존 셸6개 PASS·loader1개 ERROR(2.598s)를 보존하고 경로를 바로잡은 뒤 신규8개 및 전체76개를 정상 실행했다. 보존 스냅샷 최초 실행도 경로/명령 인수 오기로 실행되지 않아 바로잡고 새 로그에 성공 결과를 남겼다. 두 준비 오류는 제품 결함이나 통과 결과로 처리하지 않았다. 기존 실패/성공 로그를 덮어쓰지 않았다.

## 4. 로컬 적용·보존

기존 제품 PID511334의 uid1000/cwd app/절대 Linux venv/`127.0.0.1:8766 --noreload --insecure` 및 시작 tick을 대조한 뒤 해당 프로세스만 SIGINT로 종료했다. Python 조회 코드·캐시된 템플릿 적용을 위해 README의 같은 명령으로 **새 PID515502 / 127.0.0.1:8766**을 시작하여 통합 확인용으로 유지한다. PG456028·SPIKE452717/8765의 명령/cwd/uid/시작 tick은 전후 동일하다.

읽기 전용 전후 비교: Site1/Branch2/BranchPhoto1/Trainer0/Career0/Post0/PostImageUse0/Popup0·이미지3·Post리비전0의 콘텐츠 해시와 제품 미디어7파일이 동일했다. SPIKE A의 공개1/최신19·B공개3/최신3 및 해당 리비전 content 해시·미디어31파일도 동일했다. 스냅샷은 비밀값·암호 해시·세션을 조회하지 않았으며 전체 DB/계정/세션 바이너리가 같다고 확대 주장하지 않는다. 새 제품 예시 데이터/계정/권한·사진을 만들거나 삭제하지 않았다. 전용 테스트DB/합성 테스트미디어는 개발/실험 자료와 분리했다.

현재 개발 DB에 트레이너/게시글/팝업이 없으므로 해당 공개 페이지의 빈 상태와 홈의 영역 숨김은 정상이다. 기능을 보여주기 위한 가상 사업 자료를 채우지 않았다. 실제 공개 데이터가 있는 경우는 전용 test DB 회귀로 확인했다.

Git 제외 증거: `app/.runtime/dev-06-20261005T030537172278Z/`.

- `tests-presentation-01.log` 초기 준비 오류, `tests-presentation-02.log` 신규8개, `tests-all-01.log` 최종76개, `tests-popups-js.log`, `migration-check.log`.
- `snapshot.py`, `snapshot-before.log` 초기 준비 오류, `snapshot-before-02.log`, `snapshot-after.log`, `before.json`, `after.json`, `preservation.json`: 한정 콘텐츠·미디어 비교/해시, 계정·세션·비밀값 제외.
- `http-before.json`, `http-after.json`: 공개 JSON·HTML 검사 요약·정적 자산 SHA-256. 브라우저 화면/스크린샷 증거 아님.
- `processes-before.json`, `server-start.json`, `server.log`: 이전 제품 종료·신규 제품 실행, PG/SPIKE 유지 근거.

## 5. 실제 브라우저 후속 묶음 — 미실행 계획

공식 Computer Use의 알려진 WSL 경로 초기화 장애는 환경 변화가 없어 재시도하지 않았다. 우회 도구·브라우저 설치·WSL/호스트 이동도 하지 않았다. 설계자에게 아래 새 화면 통합 확인만 전달하며 사용자에게 기존 성공 흐름을 다시 요구하지 않는다.

1. 기존 자료로 홈/지점/트레이너/글을 큰 화면과320px,200% 확대에서 확인: 가로 넘침·사진 비율·긴 한글/URL·빈영역·지점 문의 대상/주소/전화 텍스트. 실제 전화/카카오 연락은 실행하지 않음.
2. 키보드만으로 본문 바로가기·현재 메뉴·지점 앵커·필터/페이지·목록 복귀를 이동해 초점 표시와 읽기 순서를 확인. 브랜드/사진 alt의 실제 적절성은 실자료 검수에 포함.
3. 이후 사용자가 명시적으로 준비한 TEST 공개 글/팝업이 있을 때 홈 안내의 본문 비가림·스크롤·닫기/오늘숨김·포커스 복원을 기존 DEV-04 계획과 한 번에 확인. 공개 상세/인증 Preview와 오류의 화면 상태도 함께 확인. 이번 작업에서 dev 예시 생성/게시하지 않았으므로 빈 팝업을 표시 성공으로 기록하지 않음.

## 6. DEV-05/Q-02 지도 대기 근거

설계자가2026-10-05 확인하여 전달한 조사 결과를 보존한다(이번 DEV-06에서 재조사·키 열람·연동하지 않음).

- [Kakao 공식 Map 답변](https://devtalk.kakao.com/t/api/151497): 주소 지오코딩 좌표의 지속 저장을 허용하지 않고 실시간 호출만 허용한다는 안내.
- [Kakao Maps 공통 안내](https://developers.kakao.com/docs/ko/kakaomap/common): 개발자 계정당 첫 활성 앱만 무료 쿼터, 이후 앱/초과는 BizWallet·유료 활성화 필요.
- [JavaScript SDK 가이드](https://apis.map.kakao.com/web/guide/): JS키·SDK 도메인 등록 요구.

카카오를 선택하면 운영자 입력 주소와 확인 여부만 보관하고 좌표는 라이브 조회하는 안을 검토해야 한다. 사용자에게 기존 ‘카카오맵/네이버지도/나중 결정’ 질문이 전달됐고 답변은 아직 없다. 무응답은 선택 승인이 아니며 지도 정책·계정 자격/키·실제 연결은 미확정/미검증이다. DEV-06은 location=null과 주소·연락처를 유지한다.

## 7. 인계·한계

변경은 공통 공개 셸/HTML 메타 helper·공개 view/Preview 표시 문맥·HTML 전용 lazy 이미지 filter, 공개 템플릿/메뉴/CSS, 전용 PG 검사/기존 셸 검사, 관련 명세·ADR·README·tasks·이 보고서다. 모델 필드/DB 마이그레이션/공개 API 구조/관리자 편집 JS·팝업 JS는 변경하지 않았다.

최종 diff·Git 제외 증거·staged 비어 있음을 점검하고 개발 쓰기를 중지하여 설계자→Git 담당자 재검토로 인계한다. 실제 브라우저 접근성/화면 통합, 실사업 콘텐츠·사진/alt 검수, 지도, 상용 Linux/도메인/HTTPS/프록시·성능·백업복원/운영 배포는 별도 미검증이며 전체 제품의 최종 완료를 뜻하지 않는다.
