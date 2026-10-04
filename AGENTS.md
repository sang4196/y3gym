# 프로젝트 작업 지침 — 설계 문서 v0.2 초안

변경 요약 (2026-09-18): 현재 설계 단계·승인 구분·Windows/Linux 작업 경계를 안내하기 위해 작성했다.

- 작업 시작 시 현재 경로에 적용되는 상위·하위 `AGENTS.md`/`AGENTS.override.md`와 README를 다시 확인한다. 기존 사용자 수정은 보존하고 필요한 절만 병합한다.
- 현재는 승인된 DEV-01 구현·검증 단계다(아래 2026-10-05 한정 승인 참조). 이전 설계·SPIKE 기록은 이력으로 보존한다. 별도로 승인된 격리 시험 SPIKE-01은 승인 범위에서 코드·로컬 의존성·실험 DB·테스트 실행이 가능하며, 전체 제품 구현은 아직 미승인이다. 기존 문서 작업의 코드 미승인은 이번 승인된 시험에 적용하지 않는다.
- 기준 문서: `docs/screens.md`, `docs/data-model.md`, `docs/api-contract.md`, `docs/review-resolution.md`. ADR: `docs/adr/0001-runtime-and-deployment.md`, `docs/adr/0002-publication-and-media.md`. 누락된 내용은 추정하지 않는다.
- 확정 제품 기준과 C 보정, P-01~04·A-01 및 기존 Proposed 제안을 구분한다. 파일 저장·이번 작업 실행은 제품 정책 승인이 아니다. 제안을 임의로 Accepted로 바꾸지 않는다.
- 고정 구조의 홍보 홈페이지 범위를 유지한다. 가격·PT 연계·고객 로그인·지점별 게시판·별도 관리자 프론트·자유 페이지 빌더·불필요한 운영 서비스를 추가하지 않는다.
- Windows는 호스트·편집/브라우저 접근 환경이며 개발 실행·가상환경·테스트는 WSL Ubuntu 기준이다. 별도 Linux 상용 서버의 배포판·버전·호스팅·실행 방식은 미정이다. OS 간 가상환경을 복사하지 않는다. Docker/WSL 설치·실행환경 이동·설정 변경을 자동 수행하지 않는다.
- 이전 문서 작업의 쓰기 범위는 세 명세, 위 두 ADR, 루트 `AGENTS.md`, `README.md`였다. `review-resolution.md`는 계속 읽기 근거다. SPIKE-01은 사용자 지시의 `experiments/cms-spike/**`, 검증 보고서, 작업 기록, 제한된 `.gitignore` 추가 및 기존 문서의 환경·단계 안내만 허용한다. 전체 구현·운영 배포·자동 staging·commit·push는 범위 밖이다.
- 비밀값 파일을 열람·출력하거나 비밀값을 문서·코드·로그에 넣지 않는다. 환경 점검도 실제 비밀값 없이 수행한다.
- 검증 계획·문서 점검·실제 테스트 실행을 구분하여 보고한다. 미실행 테스트·미확인 설치를 통과·완료라고 보고하지 않는다. 문서 작업 보고 후 구현을 자동 시작하지 않는다.

## WSL 이전 후 개발 환경 (2026-09-18)

사용자의 명시적인 이전 지시로 개발 위치를 `/home/shlee/Workspace/ai/01.codex/y3gym`으로 옮겼다. Orca 실행 환경은 WSL Ubuntu다. 위 Windows 개발 및 설치 미확인 기록은 이전 당시 기록이며 현재 개발 환경에는 적용하지 않는다. 기존 제품 정책의 승인 상태와 구현 범위는 유지한다. Git 기록과 기존 미커밋 문서를 보존했으며 이번 이전은 새 제품 구현 승인이 아니다.

SPIKE-01 시작 시 직접 확인: 같은 경로가 Git 루트이고 ext4에 있으며, Ubuntu 26.04.1 LTS / `microsoft-standard-WSL2` 커널 / Linux Python 3.14.4 / Bash다. WSL 배포 패키지 버전과 Windows 호스트 버전은 미확인이다. 이번 격리 시험 승인은 정책 채택·전체 구현 승인과 다르다. 다음 세션도 상위·하위 지침과 실제 환경을 다시 확인한다.


## DEV-01 한정 구현 승인 (2026-10-05)

사용자가 설계자의 범위 제안을 읽고 “ㅇㅇ 진행해”로 승인했다. Django/Wagtail/PostgreSQL·초기 서버 템플릿/공통 공개 조회, SiteContent·Branch·시설 사진·이용안내 관리, 최초 홈/지점 HTML과 `/api/v1/site/`, `/api/v1/branches/`를 `app/**`에 구현·검증한다. WSL 프로젝트 전용 PostgreSQL 준비·로컬 실행·별도 Linux venv/dev·test DB·미디어도 포함한다. 정확한 결과는 `docs/verification/dev-01.md`, 실행은 `app/README.md`를 따른다.

이 단위에서는 Site/Branch 즉시 저장 반영·부모/사진 원자성, 최초0개/첫 공개본점/공개 본점 정확히1/마지막 비공개 차단, 일반 운영자 영구 삭제·기존 파일 덮어쓰기 금지, 현재 공개 사용처 기반 표시본·비공개 원본/썸네일 보호를 구현 기준으로 채택했다. 공개 지점명·주소·전화 또는 카카오 연락수단은 필수, 시설 사진은 선택이다. 두 ADR에는 한정 채택 기록을 추가하며 전체 Proposed를 일괄 Accepted로 바꾸지 않는다.

쓰기 범위는 `app/**`, 필요한 `.gitignore`, AGENTS/README/tasks/current, 관련 두 ADR·세 명세 정합화·`docs/verification/dev-01.md`다. review-resolution은 읽기 근거로 보존한다. SPIKE의8765 서버·SQLite·리비전·계정·미디어·venv·열린 탭은 보존하고 새 제품 서버는8766 루프백을 쓴다. 제품 DB의 사용자 편집이 시작된 뒤 demo/초기화를 재실행하지 않는다.

지도는 다음 단위이며 location=null, 트레이너 미구현으로 trainer_section_path=null이다. Trainer/제품 Post/Popup/완성 디자인/운영 배포는 범위 밖이다. Docker/WSL·방화벽/호스트 변경·타 프로젝트 DB 조작과 자동 Git 쓰기는 금지한다. Git 비교/staging/commit/push는 별도 담당자가 수행한다. 기존 설계 단계의 코드 미승인 문구는 이번 DEV-01 한정 승인에 적용하지 않는다.
