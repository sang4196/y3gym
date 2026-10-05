# DEV-02 — 트레이너·약력과 지점별 공개 소개

실행일: 2026-10-05 KST. 상태: **구현·PostgreSQL 서버 검사·로컬 적용 완료 / 실제 브라우저 NOT_RUN / Git 검토 대기**.

## 1. 승인·시작 상태

사용자의 남은 고정 홈페이지 기능 순차 개발 승인과 설계자의 DEV-02 지시를 적용했다. 기준은 루트 AGENTS.md, tasks/roadmap.md, tasks/current.md 현재 배정, screens §6, data-model §8·11, api-contract §4.3, 두 ADR이다. 상위 경로와 하위 지침을 확인했으며 적용 파일은 루트 AGENTS.md다. 직전 SPIKE 브라우저 재점검과 그 문서·증거는 별도 이력으로 보존했다. 이번 DEV-02의 선결조건으로 도구 복구를 요구하지 않았다.

시작 HEAD `9df2f686c3634f006352e1942cea7b15653384bc`. 설계자의 AGENTS.md/README.md/tasks/roadmap.md/tasks/current.md와 직전 SPIKE 보고서/current 변경을 보존·병합했다. staged diff는 비어 있었고 개발 담당자는 staging/commit/push/reset/clean/restore/stash를 수행하지 않았다. Git 검토는 쓰기 중지 보고 후 별도 담당자가 수행한다.

## 2. 구현한 동작

| 영역 | 결과 |
|---|---|
| Trainer | 필수 단일 Branch FK, 이름·선택 직급·프로필 사진/alt·한줄소개·자체 공개·지점 내 순서·edit_version |
| TrainerCareer | 학력/수상경력/자격증/주요 경력의 고정4분류, 텍스트·순서, 한국어 부모 인라인 편집. 독립 관리 메뉴 없음 |
| 입력 | 지점은 비공개 준비에도 필수. 비공개는 이름/사진/소개 미완성 허용. 프로필 자체 공개 시 이름/지점/사진/소개 필수, 소속 지점이 비공개여도 이 검증 유지. 직급/약력 선택 |
| 길이·표현 | 이름/직급100, 한줄소개300, 사진 alt200, 약력 한 항목500자. 앞뒤 공백 정리, 일반 텍스트·HTML escape. 직급이 순서/권한을 바꾸지 않음 |
| 저장 | 기존 PG 콘텐츠 exclusive advisory transaction lock 안에서 부모+약력 전체 저장, 실패 전체 rollback·stale edit_version 거부·타부모 약력ID 주입 거부. 유효 저장은 즉시 반영, Post식 초안/Preview 없음 |
| 공개 | `/trainers/` 한 페이지의 안정적인 `branch-{id}` 섹션/카드와 `/api/v1/trainer-sections/` DTO. 프로필·지점 모두 공개인 경우만 포함 |
| 관계·정렬 | 동일 ID로 소속 이동, 사진/약력 복제 없음. 지점 비공개는 Trainer 자체 공개·버전·약력을 보존. 지점은 본점/순서/ID, 프로필은 지점 내 순서/ID, 약력은 고정 분류 및 분류 내 순서/ID |
| 빈 영역·링크 | 빈 지점 섹션/약력 분류·직급 숨김. BranchDTO.trainer_section_path 및 홈 메뉴/안내·지점 연결은 실제 유효 공개 프로필 있을 때만 표시. Trainer 상세 페이지 없음 |
| 이미지 | 기존 public_images에 Trainer.profile_image와 프로필/지점 공개 조건의 SQL EXISTS 추가. Site/Branch/사진 공유·마지막 공개 참조 철회 및 보호 원본/썸네일 정책 유지 |
| 권한 | 기존 NoDeletePolicy/CSRF/컬렉션 선택권한·파일 덮어쓰기 차단 재사용. 기존 `홈페이지 운영자` 그룹에 Trainer 추가/변경/조회만 additive 확장. 약력 제거는 부모 편집으로 허용 |

`0002_trainer_and_career`는 새 테이블2개 및 공개 필수값·약력 고정분류/빈텍스트 제약만 추가한다. Branch/이미지 FK는 PROTECT다. 기존 테이블의 사용자 콘텐츠를 변환하지 않는다. Form 소유권 오류 문구를 사진/약력 공통으로 바꿨다. 기존 configure_operator는 새 기능 권한을 포함하면서 기존 그룹 권한을 지우는 set 대신 add를 사용한다. 새 `extend_trainer_permissions`는 기존 그룹에 세 권한만 추가하며 그룹이 없거나 migration 권한이 준비되지 않으면 오류로 멈춘다. 계정 생성/저장·암호·로그인 세션 변경을 하지 않는다.

public_snapshot은 지점·프로필·약력 prefetch와 DTO/이미지 변환까지 기존 shared lock 안에서 완료한다. API와 HTML은 같은 materialized 결과를 사용한다. 관리자의 공개 API 조회도 범위를 넓히지 않는다. PostgreSQL DB 제약은 방어 수단이며 raw SQL/임의 ORM bulk update·약력 직접 저장을 지원하는 운영자 편집 경로로 보장하지 않는다.

## 3. 실제 환경·검사 결과

WSL Ubuntu26.04.1 LTS, 커널6.18.40.1-microsoft-standard-WSL2, ext4, Linux Python3.14.4. 기존 제품 venv의 Django5.2.17/Wagtail7.4.3/Pillow12.3.0/psycopg3.3.6과 PostgreSQL18.6 전용 소켓 클러스터를 재사용했다. 새 패키지·시스템/WSL/방화벽 설정·외부 바인딩은 없다.

테스트 명령(app cwd):

```bash
.venv/bin/python manage.py test content --settings=config.settings.test --noinput -v 2
```

**28 tests / 22.089s / OK**, system check 문제0건. DEV-01의 기존14개와 신규14개(일반 CMS/계약10개·별도 PG 연결 동시성4개)를 한 번 실행했다. 실패한 실행은 없으며 문서 수정 뒤 성공 검사를 반복하지 않았다. 전용 `y3gym_test` role/DB와 격리된 테스트 미디어를 사용했고 개발 DB를 seed/초기화하지 않았다. 시험 인물/경력은 명확한 TEST 텍스트, 사진은 비인물 합성 PNG다. 실제 브라우저 조작을 포함한 검사가 아니다.

| 검사 계층 | 실제 결과·범위 |
|---|---|
| 일반 운영자 CMS POST | PASS: 새 트레이너·약력 등록, 미완성 비공개/공개 필수 검증, 공백·길이·분류·파일 유실 오류, 직급·소속 변경, inline 순서/제거, 오래된 폼 거부 |
| 소유권·원자성 | PASS: 타부모 약력 ID(DELETE 포함) 거부·원본 보존, 모델 경로의 타부모 방어, 실제 CMS 저장 중 child save 이후 주입 실패로 부모/자식/version 전체 rollback |
| 공개 API/HTML 응답 | PASS: 양쪽 공개 필터·빈 상태·null/[]·DTO 필드·문자열ID·시각·read-only/no-store·미지원 질의, 관리자/방문자 동일, HTML escape·조건부 링크·빈 분류/직급/섹션 숨김 |
| 관계·DB 제약 | PASS: 같은 ID 소속 이동/약력 유지·복제 없음, 지점 비공개 시 자체 상태/버전 보존, 재공개 섹션 생성, 필수 단일 FK/PROTECT·공개 필수값·분류/내용 DB 제약 |
| 미디어·권한 | PASS: Site/Branch/사진/Trainer 공유 후 마지막 참조 차단, 지점/프로필 비공개 각각 차단·재공개 재판정·새 자산 교체, 보호 원본/썸네일/변환본 인증 차이, 컬렉션 ID 주입·영구삭제·CSRF 거부 |
| 역할 추가 | PASS: 세 권한만 추가·멱등·기존 권한/그룹 관계 유지, 계정 save가 호출되면 실패하는 검사. 실제 적용 전후 permission 목록도 정확히3개 추가/삭제0 확인 |
| 동시성 | PASS: 동일 버전 두 저장 중1개 거부, 소속 이동과 대상 지점 비공개 동시 커밋 후 미노출, writer→reader에서 부모/약력/지점 링크 완성 커밋 대기, reader→writer에서 Trainer DTO 완성 전 지점 숨김 대기. 서로 다른 pg_backend_pid 확인 |
| 기존14개 회귀 | PASS: Site singleton/현재값, Branch 본점·마지막 공개/부모사진·소유권·stale/동시성, 기존 미디어 공유·보호/덮어쓰기·삭제 차단 |

`manage.py check`: 문제0건. `makemigrations --check --dry-run`: No changes detected. `migrate --plan`: content.0002만 계획. 실제 `migrate --noinput`: content.0002 OK. `extend_trainer_permissions`: 성공. 의존성 변경이 없어 설치/기존 의존성 검사는 반복하지 않았다. 최종 `git diff --check` 통과.

## 4. 제품 적용·데이터 보존

기존 제품 PID458245의 uid1000/cwd app/venv runserver `127.0.0.1:8766 --noreload --insecure` 명령을 직전에 다시 확인한 뒤 그 프로세스만 SIGINT로 종료했다. 포트 해제 후 동일 명령으로 **새 PID464276**을 시작했다. **127.0.0.1:8766만 리스닝**하며 사용자 통합 확인을 위해 유지한다. 브라우저 탭 이동/새로고침·로그인·비밀번호 변경은 하지 않았다. PG PID456028 및 SPIKE PID452717/127.0.0.1:8765는 계속 유지했다.

무쿠키 공개 HTTP GET: 적용 전 Site/Branch JSON2건, 적용 후 Site/Branch/Trainer JSON·홈/지점/트레이너 HTML6건. 이후6건 모두200/no-store이며 기존 Site/Branch 공개 payload는 meta.server_time을 제외하고 전후 동일하다. Trainer JSON은 items=[], HTML은 준비된 빈 상태, 홈/지점의 빈 트레이너 링크는 없다. 이는 HTTP 응답 확인이며 실제 화면 렌더링/클릭 PASS가 아니다.

읽기 전용 전후 비교에서 Site1/Branch2/시설배치1/이미지3 행의 내용 해시 및 제품 private-media 목록/해시가 동일했다. `홈페이지 운영자` 그룹에는 add_trainer/change_trainer/view_trainer만 추가되고 기존 권한 삭제는0이다. 새 개발 Trainer/Career 행은 **0/0**이며 자동 예시 생성·실제 인물/경력 작성은 없다. SPIKE는 A공개1/최신19·B3/3, 해당 리비전 해시·미디어31개 목록/해시·서버 프로세스가 유지됐다. 전체 DB·계정/세션 테이블을 덤프하거나 비밀값을 열람하지 않았으며 전체 DB 불변을 주장하지 않는다. 의도된 새 테이블/권한 적용과 콘텐츠 보존을 구분한다.

증거는 **`app/.runtime/dev-02-20261004T183704528405Z/`**에 새로 저장했고 Git 제외다. UTC 폴더 시각은 KST10/05다.

- `tests-01.log`: 실제28개 테스트 전체 실행.
- `checks-01.json`, `local-apply.json`: check/모델 차이/계획 및 실제 migration/역할 확장.
- `snapshot.py`, `before.json`, `after.json`, `preservation.json`: 제한된 읽기 전용 보존 비교. 인증정보 조회·원복 기능 없음.
- `before-site.json`, `before-branches.json`, `after-*.json/html`, `http-results.json`: 공개 응답 및 비교. 쿠키/인증 헤더 없음.
- `server-process.json`, `product-server.log`: 기존 PID 확인·정상 종료·새 서버/루프백 확인. 기존 서버 로그와 SPIKE 증거 보존.

## 5. 실제 브라우저·잔여 범위

**실제 Trainer 브라우저 검증 NOT_RUN.** 공식 Computer Use는 기존 URI 오류 BLOCKED이며 DEV-02에서는 재시도하지 않았다. 테스트 클라이언트의 일반 운영자 force_login/CMS POST와 HTTP200은 실제 브라우저 로그인·이미지 chooser·inline 조작·렌더링 증거가 아니다. 새 스크린샷이나 실제 브라우저 제품/버전 확인은 없다. 서버 계층 실패나 브라우저 PASS를 새로 꾸미지 않는다.

설계자에게만 다음 사용자 통합 확인용 한 묶음을 전달한다. DEV-01에서 이미 확인한 소개·지점/사진 편집은 반복하지 않는다.

1. 기존 일반 운영자로 `/admin/snippets/content/trainer/`에서 명확한 TEST 프로필 하나를 추가한다. 공개 지점 하나·TEST 이름/한줄소개·기존 비인물 합성 사진을 선택하고, 약력은 실제 경력으로 오인하지 않는 TEST 항목으로 추가/순서 변경 후 저장한다. 직급과 일부 약력 분류는 비워 둔다. 기존 지점 필드·사진은 수정하지 않는다.
2. 다시 열어 저장 유지와 `/trainers/`의 해당 지점 카드·사진/약력 순서·빈 분류/직급 숨김, `/branches/`의 연결·공개 JSON을 확인한다.
3. 그 TEST 프로필의 소속만 기존 비공개 준비 지점으로 옮기고 같은 ID/약력·자체 공개 설정이 유지되는지, 방문자 페이지/JSON에서 제외되는지 확인한다. 기존 지점 자체의 공개/본점 설정은 바꾸지 않는다. 시험 자료는 임의 삭제·초기화하지 않는다.

위는 미실행 시나리오이며 결과를 받은 뒤 관찰자·범위대로 갱신한다. 브라우저 대기는 Git 검토 및 설계자가 승인할 다음 독립 단위의 선결조건이 아니다. 지도·제품 Post/Popup·전체 홈페이지 완성·상용 Linux/HTTPS/프록시/백업복원·부하 시험은 이번 결과에 포함하지 않는다. 전체 Proposed 정책을 Accepted로 바꾸지 않았다.

## 6. 변경 범위·인계

제품 변경은 models/forms/admin/hooks, 공개 projection/views/URLs, 기존 템플릿과 새 trainers.html/CSS, additive migration, 운영자 권한/확장 명령, 신규 test_trainers.py 및 기존 테스트의 동시성 helper 분리에 한정한다. 공통 helper 분리는 기존14개 시나리오를 변경하거나 중복 실행하지 않는다. 의존성·기존 migration·SPIKE 코드는 변경하지 않았다.

관련 세 명세·두 ADR에 DEV-02 적용/한정 채택을 추가하고 app README·루트 README/AGENTS·tasks/current/roadmap을 현재 구현과 맞췄다. 기존 설계자 변경 및 직전 SPIKE 보고서는 인계 범위에 그대로 포함한다. docs/review-resolution.md는 읽기 근거로 보존한다. 최종 문서/diff 점검을 완료하고 개발 쓰기를 중지해 설계자에게 Git 검토를 요청한다. DEV-03 제품 게시글은 다음 후보이며 이 작업에서 시작하지 않았다.
