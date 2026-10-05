# DEV-07-B — 임시 자료로 제품 통합 확인 준비

2026-10-05 KST. **새 TEST 자료 추가·관련 검사·보존 확인 완료, Git 검토 준비. 실제 브라우저·전체 DEV-07·제품·운영 배포 완료 아님.**

## 1. 범위와 시작 상태

설계자가 전달한 사용자 Q-03 승인에 따라 실제 자료 없이 임시 자료로 개발한다. 이번에는 기존 Site/Branch/시설사진/계정/미디어를 보존하고 **비어 있던 Trainer/Post/Popup에만** 한정 자료를 추가했다. 과거 create_dev_demo·초기화·seed 재실행은 하지 않았다. 실제 인물·경력·자격·행사·가격/영업정보를 만들어 사실처럼 쓰지 않았다. 실자료는 공개 준비 등 정말 필요한 단계에서만 다시 요청한다.

적용 지침/README/current/roadmap와 모델·리비전/발행·이미지 공개 규칙을 읽었다. 시작 HEAD `7f878bc9501ca2888f970949123532c58b058462`와 clean을 직접 확인했다. DEV-05-A 검토·정상 push 및 실제 원격 main=HEAD=origin/main·0/0·clean은 설계자가 확인해 전달했다.

WSL Linux·기존 제품 venv(Python3.14.4/Django5.2.17/Wagtail7.4.3/Pillow12.3.0)·전용 PostgreSQL을 사용했다. 시작 읽기 확인에서 Trainer/Career/Post/Popup은 모두0이었다. 기존 공개 본점은1, Site/Branch/시설사진·기존 이미지3개/미디어7파일·계정 메타데이터·권한·세션수1을 기준으로 기록했다. 비밀번호/계정 해시·세션값·비밀파일은 읽지 않았다.

## 2. 새 명령과 보존 경계

새 `add_local_preview_content` 명령은 이번 단위의 로컬 개발용 단발 명령이다. 아래는 **이미 수행한 실행 기록이며 반복하지 않는다.**

```bash
.venv/bin/python manage.py add_local_preview_content --confirm-test-content ADD-LOCAL-TEST-CONTENT-ONCE --server-pid 537403
```

- Linux·`config.settings.local`·app cwd/BASE_DIR/runtime·정확한 `y3gym_dev` DB/동명 최소역할·Unix socket55432를 요구한다. 실제 current_database/current_user/Unix접속과 non-superuser/no-createdb/no-createrole을 재확인한다. production/test/rehearsal 설정·다른DB/호스트/역할·접속옵션은 거부한다. 비밀값은 출력하지 않는다.
- PUBLIC_ORIGIN/ALLOWED_HOSTS를 개발 루프백으로 제한하고, 명시한 PID의 UID/cwd/정확한 runserver 명령과 시작tick 재대조·8766 단일127.0.0.1 리스너 inode 소유를 확인한다. 포트/다른 프로세스를 종료하거나 새 서버를 시작하지 않는다.
- `.runtime`/socket/미디어는 소유자 전용·symlink 없는 기존 경로, storage는 기존 PrivateStorage여야 한다. 기존 홈페이지 사진 컬렉션을 사용하고 컬렉션/역할/계정·암호·세션을 생성하거나 변경하지 않는다.
- 콘텐츠 exclusive advisory transaction 안에서 기존 Trainer/Career/Post/Popup, 예약된 TEST 이미지 제목/파일, 실행 receipt를 확인한다. 하나라도 있으면 **추가/갱신/중복 생성 없이 중단**한다. 삭제/강제/환경 우회 옵션은 없다. 기존 Site/Branch에 save를 호출하지 않는다.
- 새 원본은 UUID 파일명·정식 ImageField 저장/모델 검증을 사용한다. 480×480 프로필2개와960×540 안내1개에 TEMPORARY PROFILE/NOTICE·TEST ONLY·실제 인물/행사 아님을 표시했다. 외부 사진/폰트/네트워크·패키지 추가 없음.
- 글은 Post.save→save_revision→정식 publish를 호출해 live_revision 및 PostImageUse를 만든다. skip_permission_checks 플래그·DB의 직접 live 변경·원본 리비전 수정은 없다. 승인된 CLI 작업의 발행 actor는 null이며 계정을 가장하거나 로그인하지 않았다.
- 일반적인 생성 중 예외는 새 행을 rollback하고, 이번 실행에서 만든 파일 중 inode/hash가 같은 것만 삭제한다. 기존 파일·디렉터리 재귀 삭제는 없다. commit 불확실성/프로세스 강제 종료·파일 저장 중 부분 실패까지 원자적 복구를 보장하는 운영 도구는 아니다. 실행 receipt/예약 파일이 남으면 자동 재실행하지 않고 조사한다.

`.runtime/dev07b-preview-content-receipt.json`(0600)은 이번 run/생성 ID/원본 파일·해시/팝업 기간 기록이다. 생성 명령은 한 번만 실행했다. 재실행 거부는 테스트 DB에서 검증했으며, 개발 DB에서 생성 명령을 다시 실행하지 않았다.

## 3. 생성 자료와 확인 경로

| 종류 | 새 ID·내용 |
|---|---|
| Trainer | 1·2, `DEV-07-B TEST 임시 트레이너 1/2`, 기존 공개 본점1 소속, 각 약력1개. 실제 인물/자격이 아니라는 소개·약력 |
| TrainerCareer | 1·2, 주요 경력 분류의 TEST 배치 확인 문구. 실제 경력이 아님을 명시 |
| Post | 1 `DEV-07-B TEST 임시 공지` / 2 `DEV-07-B TEST 임시 이벤트`. Bold/Italic·내부 지점 링크·합성 안내 이미지가 있는 공개본 |
| Revision / PostImageUse | 각각1·2. 글마다 공개=최신 리비전1개, 안내 이미지6을 참조하는 공개관계1개 |
| Popup | 1→Post1. `DEV-07-B TEST 임시 팝업`, TEST 안내. KST **2026-10-05 15:28:43.547972 이상~2026-10-12 15:28:43.547972 미만**(7일) |
| Image | 4 profile-a·5 profile-b·6 notice, 기존 컬렉션2에 새 자산. 원본3개 |
| Rendition | 5·6·7, 새 이미지의 max-1200x900/PNG 표시본3개 |
| Wagtail 부수 기록 | 새 발행 ModelLogEntry3·4(actor null). 최종 새 ReferenceIndex8~19(12개), 아래 보정 이력 포함 |

정확한 행/참조 목록은 증거 `created-rows-final.json`에 있고 모든 새 원본/변환본 **6개 파일의 상대경로·SHA-256**은 `preservation.json`의 new_files에 있다. receipt의 run_id는 `2bb8d76cfea943a6811a5f0e3f520600`이다. 생성/확인 후 임시 자료와 미디어를 보존했다. 팝업은 기한 뒤 기존 후보 규칙으로 사라지며 자동 연장/재생성하지 않는다. 안내 이미지는 여전히 공개 글이 참조하므로 팝업 만료만으로 비공개가 되지는 않는다.

- [홈](http://127.0.0.1:8766/): 최근 TEST 글2건·TEST 팝업 후보.
- [트레이너](http://127.0.0.1:8766/trainers/): 본점 임시 프로필2명.
- [공지](http://127.0.0.1:8766/posts/?category=notice), [이벤트](http://127.0.0.1:8766/posts/?category=event).
- [임시 공지 상세](http://127.0.0.1:8766/posts/1/), [임시 이벤트 상세](http://127.0.0.1:8766/posts/2/).

## 4. 실제 검사·결함 처리

전용 증거는 Git 제외 `app/.runtime/dev-07-b-20261005T062411054291Z/`에 새로 저장했다.

| 계층 | 실제 결과 |
|---|---|
| 명령 환경 거부 | SimpleTestCase2개: 명시확인·test/production/rehearsal 거부, DB/역할/호스트/포트/옵션/경로/루프백 설정 불일치 시 DB 연결 전 거부 |
| PostgreSQL·격리미디어 | 8개: 기존 행/파일 보존·정식 공개/이미지 보호, 중복실행/이름충돌 거부, 이미지검증 실패·팝업 생성 실패 시 신규 행/파일 rollback,7일 경계, 별도 연결 동시실행 중 한 번만 생성, 새 Python 프로세스의 Snippet 참조 등록 |
| 최종 합계 | `.venv/bin/python manage.py test content.test_preview_content --settings=config.settings.test --noinput -v 2`: **10개/6.809s PASS**, `tests-03.log`. 테스트 runner가 y3gym_test를 생성/폐기하며 CLI의 test 실행 우회 옵션은 없다. 내부 생성 로직만 별도 test DB/media에서 호출했다. |
| 로컬 적용 | 시작/적용직전 baseline 동일 확인 후 새 명령 **1회 exit0**, `apply-01.log`·receipt. 새 의존성/migration·기존 초기화 명령 실행 없음 |
| 실제 루프백HTTP | **23건 기대결과 PASS**, `http-after.json`. 홈/트레이너/글/필터/상세7경로200·TEST, JSON7경로의2프로필/공지·이벤트/팝업 후보, 새 표시본3개200·원본3개403·직접media3개404. 주소/지도 location=null 유지 |
| 브라우저 | 실제 클릭·레이아웃·팝업JS/키보드·모바일 **NOT_RUN**. 기존 공식 Computer Use 장애 BLOCKED를 재시도/우회하지 않았다. HTTP나 테스트 클라이언트를 브라우저 PASS로 대체하지 않는다. |

기존 전체76개/기존JS 검사·기존 성공 사용자 확인은 반복하지 않았다. 새 명령이 기존 공개 렌더링/팝업 코드를 변경하지 않아 관련 전용 검사와 새 실제 HTTP 결과를 사용했다.

발견·수정 이력:

1. 첫9개 검사에서 스트리밍 test response를 읽은 뒤 다시 close해 테스트 DB 연결이 닫혔다. 최초1개 오류 뒤 나머지5개가 같은 연결 오류로 중단됐다. 테스트의 중복close를 제거해 **9개/3.017s PASS**. `tests-01.log`/`tests-02.log` 모두 보존했다.
2. 최초 로컬 생성 후 행 목록을 검사하니 공개용 PostImageUse는 정상이지만 일부 새 Trainer/Post의 Wagtail 보조 ReferenceIndex가 없었다. `requires_system_checks=[]`로 환경을 먼저 거부하는 관리 명령에서는 admin URL의 hook 로딩이 늦어지는 것이 원인이었다. `_populate_preview_content` 시작에 정식 `get_snippet_models()` 호출을 추가해 hook/참조 신호를 선등록했다. 기존 테스트 runner는 이미 hook을 로드하므로 이 문제를 잡지 못했다. **새 Python 프로세스**에서 전용 DB/media로 생성하고 모든 새 모델의 이미지 참조가 기록되는 회귀1개를 추가해 최종10개가 통과했다.
3. 생성 명령을 재실행하지 않았다. 개발 환경/receipt run ID와 생성 후 모든 콘텐츠 해시가 그대로인지 확인한 뒤 **이번 새 Trainer/Post/Popup/Image만** Wagtail의 `ReferenceIndex.create_or_update_for_object`로 정합화했다. 보조 참조14~19의6개만 추가했고 이전 참조13개는 그대로임을 트랜잭션 안에서 확인했다. 콘텐츠/리비전/파일/계정 메타데이터·권한/세션수는 보정 전후 동일, 재발행/재저장 없음. `repair-new-references.py`·`reference-repair.log`·`afterrepair.json`이 근거다.
4. 보정 결과 JSON 기록에서 UUID 직렬화 오류가 발생했다. DB 보정은 이미 완료된 상태였으며, 변경 작업은 반복하지 않고 읽기 전용으로 `reference-repair-02.json`/`created-rows-final.json`을 새로 기록했다. 부분 JSON과 실패 기록도 덮어쓰지 않고 남겼다.

## 5. 보존·현재 환경

`before.json`/`preapply.json`이 동일했고, 최종 기존 Site/Branch/BranchPhoto 행·이미지1~3 메타데이터·기존 미디어7파일 해시가 동일하다. 계정1개의 안전한 메타데이터(암호 제외), 그룹/권한/컬렉션권한, 세션수1도 동일하다. 실제 암호/세션 내용의 해시를 읽거나 DB 전체 불변으로 확대하지 않는다. 새계정/로그인·기존 계정/암호/권한/세션 쓰기 없음.

제품 미디어는 기존7+새6=13파일, SPIKE A공개1/초안19·B3/3/해당리비전·미디어31파일은 동일하다. `preservation.json`에 비교 결과·새파일 목록을 보존했다. 보조참조 보정 뒤에도 `after.json`과 `afterrepair.json`의 콘텐츠/미디어/계정 관련 전체 기록이 동일하다.

제품 **PID537403·127.0.0.1:8766**, PG456028, SPIKE452717·127.0.0.1:8765를 같은 UID/cwd/명령/starttick으로 유지했다. 이번에 서버를 시작/종료/재시작하지 않았다. 사용자 파일·프로세스·로그/증거·venv를 삭제하거나 초기화하지 않았다.

## 6. 설계자에게 남기는 최소 브라우저 확인

새 임시 자료로만 아래를 한 묶음 확인한다. 이미 성공한 SPIKE 편집/이미지 선택/로그인을 다시 요청하지 않는다.

1. 홈의 최근 TEST 글과 TEST 팝업이 읽히는지, 팝업 닫기/같은 탭1회·오늘숨김/링크 이동이 동작하는지. 키보드 포커스와 좁은 화면/확대 시 가림도 함께 확인한다.
2. 트레이너에서 임시 프로필2개/약력이 본점 아래 표시되고 합성 이미지가 실제 사진으로 오해되지 않는지.
3. 공지/이벤트 필터와 상세에서 굵게·기울임·지점 링크·대표/본문 이미지가 표시되는지. 실제 브라우저 인증/방문자 이미지 경계는 기존 잔여 검사와 구분한다.

키/현행 저장·재사용 정책·실제 네이버지도는 미완료, 호스팅/비용·배포는 미선정/미승인이다. PostgreSQL 로컬 검사를 상용 환경 검증으로 확대하지 않는다. DEV-07 전체·정책 전체 채택·운영 공개를 완료 처리하지 않는다.

최종 diff/링크·Git 제외 증거를 확인하고 개발 쓰기를 중지해 설계자→Git 담당자에게 인계한다. Git staging/commit/push·다음 단위/운영 자동 착수는 하지 않았다.
