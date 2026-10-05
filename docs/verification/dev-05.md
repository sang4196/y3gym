# DEV-05-A — 네이버지도 키 없는 준비·격리 검증

2026-10-05 KST. **한정 준비 코드/관련 검사 완료·Git 검토 준비. 전체 DEV-05와 실제 지도 연동은 미완료.**

## 1. 승인·범위

사용자는 Q-02 제공자를 네이버지도로 선택했고, Q-03 실제 브랜드/지점/사진/트레이너 자료가 없어도 임시 자료로 개발하고 정말 필요할 때만 다시 요청하도록 지시했다. 이번에는 TEST로 표시한 격리 합성 응답/DB만 사용했다. 기존 사용자 편집 콘텐츠·계정·세션·미디어를 초기화/덮어쓰거나 seed하지 않았다.

설계자가 DEV-05-A로 키 없는 어댑터/JS·오류 처리·mock/관련 PG 검사를 승인했다. HEAD `982f639d03cef25e57293a0312f18e51b99bfcce`/clean 직접 확인 후 시작했다. 적용 상위/하위 AGENTS/override·README·지도 명세/ADR·DEV07 기록과 현재 Branch 저장/공개 projection을 대조했다. 새 라이브러리/서비스/계정·외부자원·실제 지도 API 호출·비밀파일 열람·환경 이동은 없다. 전체 Proposed 채택이 아니다.

## 2. 확인한 공식 근거와 미확인 사항

| 근거 | 확인 내용·적용 경계 |
|---|---|
| [네이버 JS SDK 시작하기](https://navermaps.github.io/maps.js.ncp/docs/tutorial-2-Getting-Started.html) | 새 SDK는 `https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=...`. 과거 ncpClientId/govClientId/finClientId와 구분한다. callback 비동기 로드·navermap_authFailure 지원. Map/Marker 기본 UI의 로고·저작권을 제거하거나 서비스 명칭을 변경하지 않는다. |
| [Geocoding REST](https://api.ncloud-docs.com/docs/application-maps-geocoding) | 공식 maps.apigw.ntruss.com/map-geocode/v2/geocode GET의 query는 기본주소. 인증 ID/Secret은 공식 서버 헤더, x는 경도·y는 위도 문자열, addresses와 totalCount를 검사한다. 이번 요청은 전부 mock이다. |
| [Application 등록·한도](https://guide.ncloud-docs.com/docs/application-maps-app-vpc) | API 선택·Web URL 등록·대표계정 확인·일/월 한도 설정이 필요하다. URL 최대10개, http/https 미구분·www 제외·대표도메인 규칙을 안내한다. 현재 사용자의 계정/권한·8766 개발 URL 등록·실제 인증은 미확인이다. Secret은 서버 전용이며 브라우저에는 SDK 식별값만 사용한다. |
| [공식 요금표](https://m.ncloud.com/charge/price/ko) | Dynamic Map 0.1원/건, 대표계정 월600만 무료. Geocoding 0.5원/건, 대표계정 월300만 무료. VAT 별도. 사용자 계정에 무료 적용된다고 단정하지 않는다. |
| [대표계정 개요](https://guide.ncloud-docs.com/docs/maps-overview), [무료 한도 FAQ](https://www.ncloud.com/support/faq/all/2828) | 개인 전화번호/사업자번호당 대표계정1개, 첫 Maps 이용계정 기준. 앱 여러 개의 사용량은 합산하며 비대표계정은 과금될 수 있다. 카카오의 정책을 네이버에 적용하지 않았다. |
| [사용 주의사항](https://guide.ncloud-docs.com/docs/maps-spec) | 정식 API 호출 경로와 서비스 명칭 준수. SDK 우회·타일 수집·자체 지도 서비스는 만들지 않는다. |
| [2020 AI·Naver API 약관 PDF](https://xv-ncloud.pstatic.net/images/provision/AI%C2%B7NaverAPI%EC%84%9C%EB%B9%84%EC%8A%A4%EC%9D%B4%EC%9A%A9%EC%95%BD%EA%B4%80_1602470390248.pdf) | Maps 특약은 결과 즉시1회 사용과 별도 저장/DB화/재사용 금지를 명시한다. **구문서이며 새 Maps에 대한 현행 적용·좌표 예외/TTL·공개 JSON 전달 허용은 확인하지 못했다.** 현행 약관 페이지의 웹 조회 오류와 제한적인 검색 결과 때문에 최신 정책으로 단정하지 않는다. |

추가 공식 검색에서도 현행 Geocoding 좌표 저장/재사용·공개 JSON 전달 허용 근거를 확보하지 못했다. 실제 API/로그인·고객지원 메시지/메일은 보내지 않았다. 이 미확인을 이유로 준비 코드를 막지는 않되, 결과 저장 방식·실제 계정 활성화는 후속 조율 대상이다.

## 3. 실제 변경

- `content/naver_maps.py`: 기본 disabled인 명시 `GeocodingConfig`, 고정 HTTPS host/path·헤더 인증·프록시/redirect/재시도 없음. timeout4초, 읽기 사이 경과 확인과 64KiB 상한, MIME/JSON/최대10후보·빈/다중 결과·문자열 좌표의 유한값/범위 검증. socket timeout과 읽기 사이 deadline은 DNS 등 전체 실행시간의 엄격한4초 보장을 뜻하지 않는다.
- 실패는 disabled/not_configured/invalid_address/empty/multiple/authentication/quota/timeout/connection_error/upstream_error/invalid_response/response_too_large 등 고정 코드다. 내부 URL·조회 주소·원본 오류/응답/예외 문자열을 반환하거나 로그로 쓰지 않는다. 설정 repr에서도 두 키를 숨긴다. 공식 GET query로 제공자에게 주소를 보내는 계약과 자체 공개 URL/로그 노출을 구분했다. 실제 전송은 없다.
- 어댑터에 연결된 제품 view/관리자 action/환경 키 로더가 없다. `NAVER_MAPS_ENABLED=False`, SDK 식별값 빈문자열이 기본이다. 실제 설정 변경 없음. 서버 Secret을 페이지 설정에 넘기는 경로가 없으며 공개 페이지 입력은 공개 식별값·지점ID·검증된 latitude/longitude만 허용한다.
- `assets/naver-maps.js`: 키/유효좌표/대상DOM 없으면 외부요청0, 페이지당 SDK1회, 기본 Map/Marker, 중복ID/초기화 정리, 새 render 세대보다 늦은 결과 무시, timeout/스크립트/인증/생성오류 시 지도 숨김. 로드 후 인증 실패도 기존 지도를 제거한다. 주소·연락처 DOM은 건드리지 않는다. pagehide 정리와 bfcache 재표시를 준비했다.
- 지점 HTML은 `json_script`로 whitelist 데이터만 전달하며 준비된 값이 있을 때만 로컬 JS와 숨김 지도컨테이너를 넣는다. 기존 실제 공개 BranchDTO의 `location=null`은 그대로여서 현재 화면에 지도/SDK가 나오지 않는다. 정적 링크로 지도 요구를 완료 처리하지 않았다.
- 현재 Branch 모델·관리자 저장 폼·공개 API·권한은 변경하지 않았다. confirmed 변경/좌표·결과·후보토큰 DB/캐시 저장·migration·임의주소 공개 proxy는 없다. 기존 기본주소 편집은 계속 location=null이다.

## 4. 실제 검사 결과

증거는 새 Git 제외 `app/.runtime/dev-05-a-20261005T061142545427Z/`에 보존했다. 기존 로그/증거를 덮어쓰지 않았다.

| 계층 | 실행·결과 |
|---|---|
| 어댑터 mock | `content.test_naver_maps.GeocodingTests` **7개 PASS**. disabled/설정·주소 오류 외부요청0, 공식 호스트·query/헤더와 xy변환, 빈/다중/잘린 후보, malformed/비유한/범위초과, 인증·quota·redirect·서버오류의 body 미열람, 크기/MIME, timeout/연결·고정 오류/무출력 검증. 실제 네트워크 없음. |
| PostgreSQL/HTML | 새 MapPageTests3 + 영향받는 기존 PresentationTests8 = **11개 PASS**. 기본 disabled, 키가 있어도 현재 null/주소변경에서 요청0, 합성 future DTO의 whitelist/escape/숨김컨테이너·JS1개, 현재 문의·공개 셸/메타·이미지 회귀. 전용 y3gym_test 생성/폐기, 사용자 DB 변경 없음. |
| 합계/명령 | `.venv/bin/python manage.py test content.test_naver_maps content.test_presentation --settings=config.settings.test --noinput -v 2`: **18개/4.236s PASS**, `tests-01.log`. 이를 PG18개로 세지 않는다. 이전 전체76개는 반복하지 않았다. |
| JS fake SDK | `node --test tests/naver-maps.test.cjs`: 최종 **11개/94.561101ms PASS**, `node-03.log`. null/키/비정상좌표 요청0, 다중·중복지점, 세대경쟁·pagehide, timeout/인증·network·늦은성공, 일부생성 실패정리, 분리DOM/다른키 거부 및 로드후 인증실패. 최초10개 PASS는 `node-01.log`, 로드후 인증실패 보강11개 PASS는 `node-02.log`로 보존. 최종 키/ID 줄바꿈 거부도 확인했다. |
| 스키마 | `makemigrations --check --dry-run --settings=config.settings.test`: **No changes detected**, `migration-check.log`. dev migrate 실행 없음. |
| 실제 루프백 | 적용 후 지점HTML200·지도설정/SDK 없음, 공개 JSON5종(meta제외) 이전해시 동일, 로컬JS/CSS200 bytes 일치. 실제 지도 브라우저 PASS로 확대하지 않는다. |
| 실제 외부/브라우저 | Naver API 인증/위치/허용URL/쿼터·브라우저 지도/키보드/모바일 **NOT_RUN**. 공식 Computer Use 기존 장애는 **BLOCKED** 이력이며 이번 재시도 없음. |

테스트 실패는 없었다. 최초 JS10개 통과 후 SDK 로드 이후 인증실패 처리와 관련1개를 추가해11개를 실행했다. 마지막으로 키 타입/끝 줄바꿈·ID 공백 검증을 엄격히 하고 관련 입력을 추가해11개를 재실행했다. 해당 Python 코드가 달라지지 않아 이미 통과한18개를 반복하지 않았다. 별도 팝업/편집기 코드·서버전체76개는 이번 변경 영향이 없어 재실행하지 않았다.

## 5. 로컬 적용·보존

실제 환경은 WSL Linux의 기존 제품 venv(Python3.14.4/Django5.2.17/Wagtail7.4.3)와 기존 전용 PG다. 의존성 추가/변경은 없다. `/proc`에서 UID/cwd/명령/starttick으로 기존 제품515502의 신원을 대조한 뒤 SIGINT로 종료하고 README 명령으로 **PID537403·127.0.0.1:8766**을 시작해 유지했다. `--noreload --insecure` 로컬 전용 실행이며 외부 바인딩/운영 배포가 아니다. PG456028·SPIKE452717/8765 동일 프로세스를 유지했다.

`processes-before.json`, `server-start.json`/`server.log`, `http-before.json`/`http-after.json`/`http-final.json`, `snapshot.py`, `before.json`/`after.json`, `preservation.json` 및 실행로그가 근거다. 전후 제품 콘텐츠8모델/이미지/제품 Post 리비전 해시·제품미디어7파일, SPIKE A공개1/초안19·B3/3/해당리비전·미디어31파일 동일. 실계정/암호/세션을 읽거나 DB전체 바이너리 불변을 주장하지 않는다. 제품/PG/SPIKE를 종료 상태로 남기지 않았다.

## 6. 다음 경계·결정

후속 관리자 조회를 연결할 때 일반 운영자의 admin 접근+Branch add/change 권한·CSRF를 요구하며 공개 임의주소 proxy는 만들지 않는다. 외부 조회는 콘텐츠 트랜잭션/PG 잠금 밖에서 수행한다. 저장 시 조회를 시작한 기본주소와 edit_version을 잠금 안에서 다시 비교하고, 변경됐으면 거부한다. 기본주소 변경은 기존 확인/위치를 무효화하고 상세주소와 구분한다. 여러 후보를 자동 확정하지 않는다. 이 관리자 경계/상태 저장 흐름은 이번 구현·검사 대상이 아니며, 실제 저장정책 결정 뒤 구현한다. 서명 후보토큰 저장도 정책 우회로 사용하지 않는다.

사용자 Q-03 임시자료 승인으로 실자료는 개발 차단요인이 아니다. 실제 공개 준비 시 필요한 자료만 다시 요청한다. 기존 사용자 콘텐츠/계정/미디어 보존 조건은 유지한다.

Q-04: 도메인 구매 예정이고 호스팅은 미선정이다. 설계자가 전달한 공식 조사에서는 [Vercel Django 지원](https://vercel.com/docs/frameworks/full-stack/django)과 [Hobby의 개인/비상업 제한](https://vercel.com/docs/plans/hobby), [OCI 무료 자원·용량/유휴 제약](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm), [Lightsail 요금](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-bundles.html), [Render 무료 제약](https://render.com/docs/free)을 비교했다. 이는 후보 조사 인계이며 개발 담당자가 실제 호스팅을 검증·선택한 것이 아니다. 계정생성/비용/유료등록·운영배포 승인은 없고 이번 작업으로 환경을 바꾸지 않았다.

최종 diff/링크·Git 제외 증거를 확인하고 개발 쓰기를 중지한 뒤 설계자에게 인계한다. Git staging/commit/push는 별도 담당자의 검토에 맡긴다. DEV-05-B/운영 배포/다른 단위를 자동 착수하지 않는다.
