# DEV-05-B — 결과를 저장하지 않는 주소 확인·지도 표시

2026-10-05 KST. **키 없는 구현·격리검사·로컬 적용 완료, Git 검토 준비. 실제 지도 인증/위치/브라우저와 전체 DEV-05·운영 공개는 미완료.**

## 범위와 공식 근거

기존 순차 개발 승인·Q-02 네이버 선택에 따라 설계자가 배정한 B 단위다. 시작 HEAD `c221e08b230eee2aa213e23c473e5fb0d2e062d5`/clean을 직접 확인했다. DEV-07-B 검토·정상 push 및 실제 원격일치/0·0/clean은 설계자가 확인해 전달했다. 적용 지침·README/current/roadmap와 세 명세·두 ADR의 지도 관련 절을 대조했다. `review-resolution.md`는 읽기 근거로 보존하며 전체 Proposed를 Accepted로 바꾸지 않는다.

2026-10-05 공식 자료 재확인:

- [Maps 약관 페이지](https://www.ncloud.com/policy/terms/maps)가 연결하는 [Maps 전용 PDF](https://xv-ncloud.pstatic.net/images/provision/%5B%EB%AF%BC%EA%B0%84%5DMaps%EC%84%9C%EB%B9%84%EC%8A%A4%EC%9D%B4%EC%9A%A9%EC%95%BD%EA%B4%80_v0.4_(CLEAN)_1742433558704.pdf): 페이지의 application/json에서 MAPS/KR/version1/nextVersion0/applyYmd20250320과 PDF URL을 확인했다. PDF 전체를 읽었고 부칙 시행일은 **2025-03-20**이다. 제7조9·11항을 근거로 결과의 별도 저장·DB화·재사용을 피하고 현재 표시 요청에서 즉시 사용한다. 제7조5항의 이용 정보 제공 안내·동의,10항의 표시는 실제 런칭 전에 별도 검토한다. 짧은 화면 안내나 버튼 클릭만으로 법률적 전면 적합/필요 동의 완료를 주장하지 않는다.
- [공식 Geocoder 사용법](https://navermaps.github.io/maps.js.ncp/docs/tutorial-Geocoder-Geocoding.html): `oapi.map.naver.com`의 `ncpKeyId`와 `submodules=geocoder`, `Service.geocode({query}, callback)`, `response.v2.addresses/meta` 및 등록 서비스 URL 제한을 따른다.
- [Geocoder 모듈](https://navermaps.github.io/maps.js.ncp/docs/module-geocoder.html): SDK 경유 조회도 Geocoding API의 사용량·요금 대상이다. 실제 계정/무료 적용/쿼터를 확인한 것은 아니다.

웹 도구에서 약관 HTML/PDF를 가져오지 못해 동일 공식 URL을 직접 내려받아 확인했다. 새 Git 제외 증거의 `terms.html`, `terms.pdf`, `terms.txt`, `source-metadata.json`에 연결/시행일/파일 해시를 남겼다. DEV-05-A의 구2020약관·현행 미확인은 당시 이력이며 위 새 근거로 보완한다. 실제 API 호출은 없었다.

## 구현과 제한

- Branch에 **`address_confirmed` Boolean(default=False, editable=False)** 하나만 추가했다. 자체 기본주소와 운영자의 확인 의사만 저장한다. 좌표·반환 주소/후보·원본 응답·서명 결과토큰·세션·캐시·localStorage·hidden input에 제공자 결과를 저장하지 않는다.
- 기존 Wagtail Branch 폼 안에 `입력 주소 위치 확인`→`이 위치 확인`을 넣었다. 조회와 표시 후 확인 버튼을 누르고 지점 전체를 저장해야 반영된다. 부모 폼에는 자체 입력주소·기존 edit_version·확인 의사만 전달한다. 일반 운영자의 기존 add/change 권한과 CSRF를 사용하고 새 서비스/공개 주소 proxy/권한 확대는 없다.
- 확인은 **권한 있는 운영자의 의사**다. 서버가 SDK 조회 성공을 암호학적으로 증명하거나 지리적 정확성을 보장하는 기능이 아니다. 서버는 유효한 표시 설정, 비어 있지 않은 저장 대상 기본주소, 제출한 확인 주소/버전 및 DB의 현재 edit_version을 기존 exclusive 잠금 안에서 검증한다. 외부 조회/REST 호출은 서버 저장 경로에 없다.
- 기본주소가 바뀌면 같은 트랜잭션에서 미확인으로 바뀐다. 새 주소를 이번 폼에서 확인한 경우에만 새 주소로 확인된다. 상세주소만 바꾸면 기존 확인을 유지한다. stale 저장·부모/사진 실패 시 부분 반영하지 않는다. 폼 오류 응답은 확인 의사 값을 비워 새 확인을 요구한다. 모델의 확인 필드를 폼에서 직접 편집할 수 없고 임의 bool 대입만으로 save해도 기존 유효 상태에서 재계산한다.
- 공개 BranchDTO의 `location`은 항상 null. **`map`은 확인된 공개 지점에만 `{provider:'naver', query:현재 기본주소}`**, 나머지는 null이다. SDK 설정과 무관한 자체 콘텐츠이며 지도 성공/좌표가 아니다. 기존 공개 필터/정렬/필드는 유지한다. 향후 분리 프론트도 이 주소를 사용해 표시할 때 새 조회해야 한다.
- 공개 지점 화면은 표시 설정과 확인된 주소가 있을 때 안내와 `네이버지도 보기`를 제공한다. 버튼을 누르기 전에는 SDK 요청도 없다. 네이버 연결·지점 주소/이용 정보 제공·보관·활용 가능성을 먼저 알리며 현재위치 수집은 없다. 주소/연락처는 항상 유지한다. SDK 기본 로고/저작권을 변경하지 않는다.
- SDK의 성공 status/v2, totalCount/count/page=1, addresses 한 개, 유한·범위 내 위경도를 모두 요구한다. 입력과 반환 roadAddress 또는 jibunAddress를 **NFC·양끝 공백 제거·연속 공백 정리 후 전체 문자열 일치**로 비교한다. 첫 후보·접두어·유사도·시도 별칭·건물명/번지 생략 매칭은 하지 않는다. 실제로 같은 주소라도 표기가 다르면 거부될 수 있으며 전체 기본주소를 점검하도록 안내한다. 상세주소를 자동 보정하거나 반환 주소를 저장하지 않는다.
- 페이지당 SDK 로더1개를 공유하고 각 지점은 진행 중 중복 요청을 막는다.10초 응답 제한·주소 변경/세대·늦은 콜백·인증/네트워크/쿼터/빈값/다중 결과/잘못된 좌표는 마커를 표시하지 않는다. 제공자 내부 오류/주소 응답을 로그로 남기지 않는다. pagehide에서 Map/Marker·확인 의사를 정리하고 bfcache 복귀는 자동 재조회 없이 버튼을 다시 눌러 새 조회해야 한다. 외부 전송 취소 자체를 보장하지 않으며 이미 보낸 요청의 늦은 결과를 무시한다.
- 지도 설정은 **NAVER_MAPS_ENABLED=False / NAVER_MAPS_PUBLIC_KEY_ID=''** 그대로다. 키 없는 관리자 UI는 위치 확인 불가와 주소 저장 가능을 구분한다. DEV-05-A REST 어댑터는 비활성 준비 코드로 남고 호출 경로를 추가하지 않았다. 실제 키/환경값·Secret 파일을 읽거나 설정하지 않았다.

표시 설정을 나중에 구성할 때는 전용 설정의 두 값만 사용한다. enabled가 정확히 True이고 공개 SDK 식별값이 ASCII 영숫자/밑줄/하이픈1~128자일 때만 표시 설정을 만든다. 누락·잘못된 형식은 비활성으로 처리한다. Secret을 이 값에 넣지 않는다. 실제 계정/지도 API 선택·허용 URL·요금/쿼터·고지/동의·실인증 확인 및 명시적 활성화가 별도 필요하다. 이번에는 활성화하지 않았다.

## 실제 검사와 발견 사항

환경: WSL Ubuntu26.04.1/WSL2 kernel6.18.40.1, Linux Python3.14.4, Django5.2.17/Wagtail7.4.3/Pillow12.3.0, 기존 전용 PostgreSQL18.6. 패키지/시스템/호스트/방화벽 변경 없음. 테스트는 별도 y3gym_test role/DB와 매 실행 격리 media이며 실제 운영자 로그인/키/외부 Geocoding을 사용하지 않았다.

| 계층 | 결과와 근거 |
|---|---|
| 관련 회귀 | `manage.py test content.test_address_confirmation content.test_naver_maps content.tests content.test_presentation --settings=config.settings.test --noinput -v 2`: **40개/17.681s PASS**, `pg-02.log`. PG/HTML33+기존 REST mock7. 기본주소 무효화/상세 유지·stale·권한·CSRF·부모/사진 rollback·DTO 경계·기존 본점/공개/사진/동시성·HTML 회귀 |
| 주소 확인 최종 보강 | `manage.py test content.test_address_confirmation --settings=config.settings.test --noinput -v 2`: **10개/3.869s PASS**, `pg-03.log`. 앞선8개에 최초 생성 확인·별도 PG 연결에서 같은 버전의 주소 변경/확인 경쟁2개 추가. 전체 고유 검사 수는42이며40+10을50개로 세지 않는다. |
| 표시 설정 검사 보완 | `content.test_naver_maps.MapPageTests` **3개/0.261s PASS**, `pg-04.log`. A의 좌표 DTO 테스트를 현재 자체주소 map 계약 검증으로 바꿨다. 앞선40개에 포함된 테스트의 재검증이다. |
| fake SDK/DOM | `node --test tests/naver-maps.test.cjs`: **18개/142.474802ms PASS**, `node-03.log`. 단일/다중/잘못된 주소·좌표·실패/timeout·역전·중복·부분 생성 실패·pagehide/bfcache·관리자 확인/입력 변경/버전/submit 변경·키 없음 요청0. 저장/네트워크 제출 API 접근을 금지한 가짜 window에서 실행. 실제 브라우저/SDK 성공이 아니다. |
| 스키마 | `0005_branch_address_confirmed`만 additive 생성·적용, `migrate.log`. `makemigrations --check --dry-run --settings=config.settings.test`: 차이 없음, `schema-check.log` |
| 실제 HTTP | **9건 PASS**, `http-after.json`: 공개 JSON4종과 지점HTML 전후 비교(map:null 추가만 허용), 실제 팝업 후보1건, 새 JS2/CSS1이 checkout 바이트와 일치. 지도 설정/외부 SDK 노출 없음. |
| 외부/브라우저 | 실제 네이버 인증·주소 정확성·타일 표시·허용 URL·쿼터 및 관리자/공개 실제 브라우저 **NOT_RUN**. 공식 Computer Use 기존 **BLOCKED** 재시도/비공식 우회 없음. |

실패를 보존하고 수정했다:

1. `pg-01.log`:40개 중7ERROR/1FAIL. 기본 Django widget renderer가 앱 내부 templates를 검색하므로 최초 루트 templates 위치에서는 관리자 위젯이 누락됐다. `content/templates/content/widgets/`로 수정했다. 사진 rollback 검사는 ClusterableModel의 메모리 사진 목록을 DB 저장 결과로 혼동해 실패했으며 실제 BranchPhoto DB 쿼리로 고쳤다. 최종 관련40개와 전용 보강10개 통과.
2. `node-01.log`:16개 중15PASS/1FAIL. fake SDK LatLng 인스턴스를 일반 객체와 strict 비교한 테스트 오류로 좌표와 옵션 키를 검사하도록 수정했다. `node-02.log`16PASS 후 부분 생성/입력 재변경2개를 추가해 최종18PASS.
3. 시작 PDF 터미널 출력의 Windows cp949 인코딩 실패는 UTF-8 파일 추출로 재확인했다. 소스 메타데이터 파싱에 시스템 Python(bs4 없음)을 잘못 사용한 뒤 기존 앱 venv로 읽었다. 패키지 설치 없음.
4. 적용 전 snapshot 스크립트를 새 필드 제외 방식으로 바꾸면서 FK의 필드 이름과 기존 attname 키가 달라 비교가 실패했다. DB 변화가 아니라 수집 형식 차이임을 확인하고 attname으로 고쳐 `before.json == preapply-02.json == after.json`을 확인했다. 첫 `preapply.json`도 보존했다.
5. 루프백 점검에서 잘못된 `/api/v1/popups/` 경로가404였다. 실제 계약 `/api/v1/popups/active/`에서 후보1개를 확인했다. 이 경로의 사전 비교는 없으며 전후5종 동일로 확대하지 않는다. 앞선404와 후속 실제 성공을 구분한다.

이미 성공한 전체 제품 테스트/팝업JS/SPIKE 검사를 근거 없이 반복하지 않았다. 새 브라우저 검사 묶음도 사용자에게 중복 요청하지 않았다.

## 로컬 적용·보존·인계

증거: **`app/.runtime/dev-05-b-20261005T064227992213Z/`**, Git 제외/소유자 전용. 기존 로그를 덮어쓰지 않았다. before/preapply-02/after snapshot은 기존 콘텐츠8모델·이미지/공개 Post 리비전, 기존 Site/Branch/사진 행, 안전한 계정 메타데이터/권한/세션수, 제품미디어13·SPIKE미디어31/리비전 해시가 동일하다. 새 필드는 비교에서 분리해 기존 Branch1·2 모두False임을 별도 확인했다. 기존 edit_version/사용자 주소를 바꾸지 않았다. DEV-07-B TEST 자료와 receipt SHA-256 동일. 계정 암호/세션값/비밀파일은 미열람이며 DB 전체 바이너리 불변을 주장하지 않는다.

신원을 재대조한 기존 제품537403만 SIGINT로 종료하고 README 명령으로 **PID544255·127.0.0.1:8766**을 시작해 유지했다. 새 process identity와 단일 loopback listener/socket inode를 확인했다. PG456028·SPIKE452717/8765는 동일 UID/cwd/argv/starttick 유지. 새 계정·권한/암호·세션 쓰기·seed/임시 생성명령·SPIKE 쓰기 없음. [지점 화면](http://127.0.0.1:8766/branches/)은 지도 비활성으로 주소·연락처를 유지한다.

실제 브라우저, 실제 네이버 계정/키·URL/쿼터·주소/타일·고지/동의, 상용 Linux/TLS·호스팅/비용·배포는 별도 대기다. 사용자에게 방금 요청된 TEST 화면 확인은 설계자가 조율하며 이번 재요청하지 않았다. 전체 DEV-05/DEV-07·제품 완료나 전체 정책 채택으로 표시하지 않는다.

최종 문서/diff/증거 제외를 점검하고 개발 쓰기를 중지해 설계자에게 인계한다. staging/commit/push는 Git 담당자가 검토하며 운영 배포나 다음 단위를 자동 착수하지 않는다.
