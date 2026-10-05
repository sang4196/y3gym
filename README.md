# y3gym
The y3gym website made solely with Codex

현재 단계: **제품 기능 순차 구현·검증**. DEV-01 사이트 소개·지점·시설 사진·이용안내와 첫 공개 HTML/JSON은 구현·검토·커밋·푸시를 완료했다(`9df2f68`). 2026-10-05 사용자가 남은 작업의 목록화와 자동 순차 진행을 승인했다. 다음 범위·완료 조건·사용자 결정 항목은 [작업 목록](tasks/roadmap.md), 최신 진행은 [현재 작업](tasks/current.md)을 따른다. 실행은 [제품 앱 안내](app/README.md), DEV-01 결과는 [검증 보고서](docs/verification/dev-01.md)에 있다. 이전 Post·CMS 이미지 SPIKE는 [실험 안내](experiments/cms-spike/README.md)와 [보고서](docs/verification/cms-spike.md)에 별도 보존한다. 전체 홈페이지·상용 배포 완료를 뜻하지 않는다.

현재 환경은 **Windows 호스트 위 WSL Ubuntu 개발 / 별도 Linux 상용 서버 운영 예정**이다. Windows는 편집·브라우저 접근 환경이며 개발 실행·가상환경·테스트는 WSL의 Linux Python과 셸을 사용한다. 직접 확인한 환경은 Ubuntu 26.04.1 LTS, WSL2 커널, Python 3.14.4, ext4의 현재 저장소다. 운영 배포판·버전·호스팅·실행 방식은 미정이다. Django + Wagtail + PostgreSQL과 초기 서버 템플릿/공통 공개 조회는 2026-10-05 승인으로 **DEV-01에 한정 채택**했다. Site/Branch 저장·본점·삭제/미디어 정책의 한정 채택은 두 ADR의 추가 기록을 따른다. 나머지 정책·운영 구성은 계속 Proposed/TBD다. `review-resolution.md`의 Windows 중심 설명은 이전 기록으로 보존한다.

## 문서

DEV-02 트레이너·약력 관리와 지점별 공개 HTML/JSON·이미지 권한을 추가했다. 실제 PostgreSQL28개 검사와 로컬8766 적용을 완료했고 실제 트레이너 브라우저는 NOT_RUN이며 Git 검토·정상 push는 `d8bdec0`으로 완료했다. 세부 결과·보존·검증 계층은 [DEV-02 보고서](docs/verification/dev-02.md)를 따른다. DEV-01의 한정 채택 기술과 해당 저장/이미지 정책을 Trainer 범위로 확장했으며 전체 Proposed나 운영 배포를 일괄 승인하지 않는다.

DEV-03 공지·이벤트 수정 초안/공개/Preview·복원, 홈 최근3건·목록/상세 HTML/JSON·공개 이미지 관계 인덱스를 구현했다. 실제 PostgreSQL46개와 편집기 Node7개 PASS, 로컬8766 적용·기존 콘텐츠/SPIKE 보존 확인을 마쳤다. 실제 브라우저는 NOT_RUN이며 Git 검토·정상 push는 `e54d34f`로 완료했다. [DEV-03 보고서](docs/verification/dev-03.md)에서 계층별 근거와 남은 범위를 확인한다.

DEV-04 기간제 팝업을 구현했다. 모든 팝업의 게시글 연결은 필수이며 글당 최대1개 설정, 현재값 저장·기간 후보/API·조건부 이미지 권한·정상 홈 안내/닫기/오늘숨김을 적용했다. 실제 PG68개 PASS 및 Unicode 길이 수정 후 팝업 Node16개 PASS, 로컬8766 적용/자료 보존 완료, 실제 브라우저 NOT_RUN이며 Git 검토·정상 push는 `0b3bccb`로 완료했다. [DEV-04 보고서](docs/verification/dev-04.md)를 따른다.

DEV-06 공개 화면·공통 문의 동선·메타데이터를 통합했다. PG76개·팝업 Node16개 PASS, 로컬8766 적용과 기존 자료 보존을 확인했다. 실제 브라우저는 NOT_RUN, Git 검토·정상 push는 `285833fe`로 완료했고 지도(Q-02)는 답변 대기다. [DEV-06 보고서](docs/verification/dev-06.md)를 따른다.

DEV-07-A는 검증 추적·합성 전용 PG 백업/복원과 별도 운영 설정/Gunicorn 후보를 로컬에서 검증했다. 기존 개발/SPIKE 자료·서버는 보존했고 실제 운영 배포·DEV-07 전체 완료는 아니다. [검증/미검증 추적](docs/verification/dev-07.md)과 [배포 후보 절차](docs/deployment/linux-candidate.md)를 참조한다. Git 검토 대기다.

| 경로 | 내용·상태 |
|---|---|
| [docs/screens.md](docs/screens.md) | v0.2 초안: 확정 제품 기준, 화면 제안, UX-01~18 추적 |
| [docs/data-model.md](docs/data-model.md) | v0.2 초안: 관계·저장 단위·공개·삭제·미디어 정책 제안 |
| [docs/api-contract.md](docs/api-contract.md) | v0.2 초안: 공개 조회 계약, API-01~24 검증 계획 |
| [docs/review-resolution.md](docs/review-resolution.md) | 기존 v0.1 검토 근거: C 보정 / P-01~04·A-01 Proposed, 이번 작업에서 변경하지 않음 |
| [ADR-0001](docs/adr/0001-runtime-and-deployment.md) | v0.2 Proposed + DEV-01 한정 채택: 실행·배포·버전·ENV-01~06 |
| [ADR-0002](docs/adr/0002-publication-and-media.md) | v0.2 Proposed + DEV-01 한정 채택: P-01~04·RV-01~15 |
| [AGENTS.md](AGENTS.md) | 현재 설계 단계의 작업 범위·승인 구분·환경 주의 |

문서 저장 자체는 정책 승인이 아니다. 후속 개발은 사용자의 자동 진행 승인과 작업별 설계 결정에 근거하며, 실제 요구 충돌과 사용자 정보가 필요한 항목은 작업 목록에서 별도 대기한다. 기존 Proposed 전체를 일괄 승인·검증 완료로 바꾸지 않는다. 가격·PT 연계·고객 로그인·지점별 게시판·별도 관리자 프론트·자유 페이지 빌더는 범위에 추가하지 않는다.

변경 요약 (2026-09-18): 기존 소개를 유지하고 현재 단계·실제 문서 경로·Windows/Linux 방향을 추가했다. 다음 작업은 정책 결정과 별도 승인된 기술 검증이며 이번 문서 작업에서 자동으로 구현을 시작하지 않는다.
