# DEV-05-C — Google 지도 수동 퍼가기 전환

2026-10-05 KST. 구현·격리 검사·로컬 적용 완료, 실제 Google 지도 표시/위치·관리자 클릭·새 디자인 시각 검수는 미검증. 전체 DEV-05/DEV-07·운영 완료가 아니다.

## 승인·시작 근거

사용자의 네이버에서 Google로 전환 요청과 “https://www.seungjong.co.kr/about … 이렇게 하면 되지않을까”를 설계자가 수동 퍼가기 선택으로 해석·안내한 배정을 따른다. 주소 자동조회 대신 지점별 퍼가기 등록·수동 위치 확인으로 변경한다. 추가 계정/키/결제 요청 없음. 시작 HEAD `5c4432ca7d609ef87110d15abbf2b513e4a04614`/clean 직접 확인. 적용 상위/하위 지침은 루트 AGENTS만 존재했고 README/tasks·관련 명세/ADR·기존 지도 구현을 확인했다. WSL Linux6.18.40.1/Python3.14.4의 기존 app Linux venv/전용 PostgreSQL을 사용했다. 패키지/시스템/브라우저 설치·환경 이동 없음.

[Google 공유·퍼가기 안내](https://support.google.com/maps/answer/7101463?hl=ko)는 공유/지도 퍼가기에서 HTML을 복사하는 절차를 제공한다. [Embed API 안내](https://developers.google.com/maps/documentation/embed/usage-and-billing)는 API 요청에 키가 필요하다고 명시한다. 이번은 API v1 대신 공유 퍼가기 `/maps/embed?pb=…`를 사용하므로 API 키/Cloud 가입·결제를 구성하지 않는다. 전체 약관/UI/운영 고지 검토 완료를 뜻하지 않는다.

[참고사이트](https://www.seungjong.co.kr/about)의 공개 HTML을 읽기 전용으로 다시 확보했다. iframe host=`www.google.com`, path=`/maps/embed`, 단일 query=`pb`를 확인했고 실제 복사 형태가 새 파서로 승인되는지 검사했다. 해당 URL을 제품 DB/TEST 자료로 등록하거나 iframe/Google SDK를 로드하지 않았다. 실제 렌더링 관찰이 아니다.

## 구현과 경계

- `content/google_maps.py`: 순수 HTMLParser/URL 파싱. 원문8192자·URL4096자 제한, HTTPS/정확한 www.google.com/정확한 /maps/embed/단일 pb만 허용한다. userinfo·포트·fragment·제어문자·위장호스트·중복 src/속성/query·script/srcdoc/event·다른 HTML·일반 공유/단축 URL·API v1/키 URL을 거부한다. pb는 불투명 문자열로 보존하며 좌표 추출·재조합·서버 fetch/redirect/geocode는 없다.
- 정식 iframe의 width/height/style/loading/allowfullscreen/referrerpolicy/title/class/frameborder는 파싱 허용하되 모두 버린다. src만 검증·저장한다. 사용자 원문을 live DOM·innerHTML·template safe로 실행하지 않는다. 오류 textarea도 기본 escaping을 유지한다. 브라우저 쪽은 DOMParser 없이 문자열로만 입력을 파싱하고 서버가 최종 검증한다.
- Branch additive0006의 `google_embed_url`(빈 문자열), `google_map_address`(확인 시 자체 기본주소, 빈 문자열), `google_map_confirmed`(False)를 추가했다. 기존 `address_confirmed`는 Naver 이력이며 승계·활성화하지 않는다. 기존 주소/상세주소/사진/연락처/본문/팝업과 계정 권한은 그대로다.
- 기존 Branch 폼에서 코드/URL을 선택 입력한다. 열기→실제 위치를 살펴본 운영자의 확인→부모 전체 저장이다. 입력 삭제 후 저장은 지도 제거, URL 교체/기본주소 변경은 확인 무효화, 상세주소만 변경은 확인 유지다. 기본주소를 저장한 뒤 원래 주소로 돌려도 자동 확인 복원되지 않는다. 미확인 URL은 보관할 수 있지만 공개하지 않는다.
- 확인 intent는 주소+검증 URL+edit_version을 모두 비교한다. 기존 add/change 권한·CSRF·stale 거부·PG 잠금·부모/시설사진 트랜잭션을 유지한다. URL/주소가 바뀐 뒤 새로 직접 확인한 경우 같은 부모 저장에 새 확인을 반영할 수 있다. 오류 응답은 확인 intent를 비우고 다시 확인하게 한다. 확인은 운영자의 의사이며 지리적 일치나 iframe 내용의 성공을 서버가 보증하지 않는다.
- 공통 공개 projection의 `location=null` 유지. 공개 지점·등록 URL·유효한 확인주소/상태가 모두 맞을 때만 `map={provider:'google',mode:'embed',embed_url:검증URL}`, 그 외 null이다. 기존 `{provider:'naver',query:주소}` 계약을 대체했다. 다른 DTO·정렬·이미지 권한은 바꾸지 않았다.
- 공개/관리자 실제 경로에서 Naver SDK/REST/설정을 사용하지 않는다. 이전 adapter/JS/설정·역사 문서는 보존하며 비활성 설정은 그대로다. Naver 결과 비저장 정책을 Google 퍼가기 URL 저장에 그대로 적용하지 않는다.
- 방문자 버튼 전 iframe/외부 요청0. 안내 후 클릭해야 고정 속성 iframe을 생성한다. 지점명 title, 반응형 전체 폭/높이·전체화면 허용, 제공자 내부 위치·로고/attribution을 가리지 않는다. 닫기/재시도, 15초 타임아웃, 이전 프레임 제거·늦은 이벤트 무시, pagehide 정리·bfcache 복귀 자동 로드 금지를 구현했다. 주소/연락처 영역은 계속 보인다. cross-origin load는 실제 지도 내용 성공이 아니므로 위치 확인 성공으로 자동 표시하지 않는다.
- 디자인 팔레트·팝업 hook·Post 편집/Preview는 유지한다. CSS는 지도 iframe 크기만 추가했으며 의존성/새 서버 서비스는 없다.

## 실제 검증

Git 제외 증거: `app/.runtime/dev-05-c-20261005T093703830426Z/`(디렉터리0700/파일0600). 테스트는 별도 y3gym_test PostgreSQL/합성 미디어이며 실제 운영자 로그인/Google 브라우저 검증이 아니다.

| 계층 | 실행·결과 | 증거 |
|---|---|---|
| 관련 첫 검사 | 45개/23.491s 중43 PASS·2 FAIL. Branch/public shell/presentation/Naver 비활성/새 parser·확인 흐름 범위만 실행 | tests-01.log |
| 보정·보강 후 관련 검사 | Google parser/확인15개/4.812s PASS. textarea 선행 줄바꿈 비교를 trim, 롤백 후 사진 수를 modelcluster 메모리 관계 대신 실제 DB로 확인하도록 테스트 수정. 오류 입력 폼 무변경과 URL 제어문자 검사를 추가 | tests-focused-02.log |
| 최종 범위 집계 | 첫 실행의 영향 없는32개 PASS + 최종15개 PASS = 서로 다른47개(43 PG/HTML·4 순수 파서). 중복 실행 건수를 합산하지 않음. 전체 제품 검사 재실행 아님 | 위 두 로그 |
| 모의 DOM 상태 | 최초11개 PASS, URL 제어문자/후행 query 구분 보강 후12개/140.143997ms PASS. 클릭 전0·고정 속성·raw HTML 금지·교체/중복 load·timeout/late event·닫기/재시도·pagehide/bfcache·관리자 주소/URL/버전 변경·submit 검사 | node-01.log, node-02.log |
| 마이그레이션 | dry-run 변경누락 없음, plan은0006/필드3개뿐. local migrate content0006 PASS | migration-check.log, migration-plan.log, migration-apply.log |
| 읽은 참고 iframe | 정식 공개 코드 파싱 PASS, URL을 저장/로드하지 않음 | reference.html, reference-validation.json |
| 실제 로컬 HTTP | JSON5종·공개 페이지5/관리자 로그인1·정적 파일3 =14건 PASS. 기존 JSON5종(meta 제외) 동일. 미등록 지점에 iframe/지도버튼/Naver script 없음, 주소/연락·팝업 hook 유지. 제공된 새 JS/CSS와 소스 일치 | http-before.json, http-after.json, http-checks.json |
| 실제 브라우저/Google 내용·위치 | NOT_RUN. 기존 공식 WSL 경로 장애 BLOCKED 유지, 재시도/비공식 우회/설치 없음. HTTP200/서버·모의 검사를 브라우저 PASS로 대체하지 않음 | 기존 장애 이력 |

부모/사진 오류 롤백, 새 등록/교체/제거, 새주소 확인·상세주소 유지, 오래된 폼/주소/URL/버전 불일치, 실제 별도 PG 연결 경쟁, 권한/CSRF, HTML escaping/공개 필터를 검사했다. 최초 파일 편집 보조 명령은 템플릿의 종료 문자열을 못 찾아 ValueError로 중단했고 해당 파일을 정확히 다시 편집한 뒤 검사를 실행했다. 실패 로그·기존 자료를 삭제/덮어쓰지 않았다.

## 로컬 적용·보존

시작 제품564413/8766·PG456028·SPIKE452717의 UID/cwd/명령/starttick을 기록하고 적용 전 동일 신원·8766 loopback 리스너 inode 소유를 확인했다. 제품564413에만 SIGINT·종료 확인 후0006을 적용하고 README runserver 명령으로 **제품 PID569586/127.0.0.1:8766**을 시작·유지했다. 최종 IPv4 loopback 단일 리스너·PG/SPIKE 동일 프로세스·기존 제품 종료 PASS(`processes-before.json`, `server-start.json`, `processes-after.json`). 이번 서버는 사용자 확인을 위해 켜 두었다.

지점1·2의 새 필드는 URL/확인주소 빈 값·False다(`new-fields.log`). 실제지도/참고회사위치/seed/새예시·권한/계정/암호/세션/팝업 기간을 넣거나 변경하지 않았다. 기존8콘텐츠 모델(신규 google_*만 제외한 해시)·Post리비전/기존 Site/Branch/시설사진·이미지 메타·비밀값 제외 계정 메타/그룹/권한/세션수·SPIKE 상태·receipt가 적용 전후 동일하다.

제품 미디어는 **시작15개→적용직전16개→적용후16개**였다. 이전 DEV-06-B의13개는 당시 기록이다. 시작부터 적용 전 사이에 `dev07b-…-prof.max-165x165.png` 썸네일1개가 추가됐으며 생성 주체/시점을 단정하지 않는다. 시작15개 모두 해시 동일·삭제/교체 없음, 적용직전/후16개는 완전히 동일하다. SPIKE31파일도 동일하다. 사용자 동시 작업 가능성을 보존하고 해당 차이를 원복하지 않았다. `before.json`, `preapply.json`, `after.json`, `preservation.json`이 근거다. 비밀파일/암호 해시/세션키·내용은 읽지 않았다.

## 관리자 이용과 남은 확인

1. 제품 관리자8766의 지점을 열고 기본주소를 확인한다. Google 지도에서 해당 위치의 공유 → 지도 퍼가기 → HTML 복사 코드를 `Google 지도 퍼가기`에 붙인다. 일반 공유 링크/단축 링크는 사용하지 않는다.
2. 입력한 지도 열기를 누르고 외부 지도에 실제로 표시된 위치가 기본주소와 맞는지 직접 살핀다. 주소와 이 지도 위치 확인을 누르고 지점 전체를 저장한다. 미확인 저장은 방문자 지도에 나오지 않는다.
3. 공개 지점 화면에서 Google 지도 보기를 눌러 지도/위치/attribution·닫기/재시도와 좁은 화면·키보드를 확인한다. 기본주소 변경 때 새 지도를 등록·확인한다. 지도를 제거하려면 입력을 비우고 저장한다.

위 절차의 실제 사용자 수행·지도 내용/위치·관리자 클릭·모바일/확대/키보드와 운영 고지/정책 검수는 아직 미검증이다. 실자료를 새로 요청하지 않았고 임의 지도도 채우지 않았다. 이전 제품 Post 초안의 “2. 정상”은 한정 사용자 보고 PASS로 유지하며 재검증을 요청하지 않는다. 운영 호스팅/HTTPS/상용Linux·비용/배포 및 전체 Proposed 채택은 범위 밖이다. 최종 diff·링크/범위 점검 후 쓰기 중지·설계자/Git 검토 대기. 자동 staging/commit/push·다른 대화 직접 보고 없음.

최종 검토: 변경27파일의 허용 범위·로컬 문서 링크·diff 공백·staged empty/HEAD 불변·증거 Git 제외를 확인했다(`final-review.json`). CSS의 button display가 기본 hidden 표시를 덮지 않도록 닫기 버튼의 hidden 규칙을 명시하고 최종 CSS 응답2건을 별도 확인했다(`final-static-check.json`, 초기HTTP14와 중복 합산하지 않음). 새 하늘색/스크롤 진입 효과 요청은 tasks/current의 다음 DEV-06-C 배정 예정에만 기록했다. 지도 Git 검토·커밋 후 별도 배정 전에는 디자인을 시작하지 않는다. 개발 쓰기 중지.
