# y3gym
The y3gym website made solely with Codex

현재 단계: **설계 문서 v0.2 초안 검토 및 승인된 격리 시험 SPIKE-01**. 제품용 홈페이지는 아직 구현하지 않았다. Post·CMS 이미지의 시험 코드와 실행 결과는 [실험 안내](experiments/cms-spike/README.md) 및 [검증 보고서](docs/verification/cms-spike.md)에서 구분한다.

현재 환경은 **Windows 호스트 위 WSL Ubuntu 개발 / 별도 Linux 상용 서버 운영 예정**이다. Windows는 편집·브라우저 접근 환경이며 개발 실행·가상환경·테스트는 WSL의 Linux Python과 셸을 사용한다. 직접 확인한 환경은 Ubuntu 26.04.1 LTS, WSL2 커널, Python 3.14.4, ext4의 현재 저장소다. 운영 배포판·버전·호스팅·실행 방식은 미정이다. Django + Wagtail + PostgreSQL과 초기 서버 템플릿은 계속 **Proposed**이며 격리 실험 설치는 기술 채택이 아니다. `review-resolution.md`의 Windows 중심 설명은 이전 기록으로 보존한다.

## 문서

| 경로 | 내용·상태 |
|---|---|
| [docs/screens.md](docs/screens.md) | v0.2 초안: 확정 제품 기준, 화면 제안, UX-01~18 추적 |
| [docs/data-model.md](docs/data-model.md) | v0.2 초안: 관계·저장 단위·공개·삭제·미디어 정책 제안 |
| [docs/api-contract.md](docs/api-contract.md) | v0.2 초안: 공개 조회 계약, API-01~24 검증 계획 |
| [docs/review-resolution.md](docs/review-resolution.md) | 기존 v0.1 검토 근거: C 보정 / P-01~04·A-01 Proposed, 이번 작업에서 변경하지 않음 |
| [ADR-0001](docs/adr/0001-runtime-and-deployment.md) | v0.2 Proposed: 실행·배포·버전 선정과 ENV-01~06 |
| [ADR-0002](docs/adr/0002-publication-and-media.md) | v0.2 Proposed: P-01~04 대안·대가와 RV-01~15 |
| [AGENTS.md](AGENTS.md) | 현재 설계 단계의 작업 범위·승인 구분·환경 주의 |

문서 저장은 정책 승인이 아니다. C 항목은 기존 의미 보정이며 P-01~04·A-01과 기존 화면·팝업·공개일·API 경로·페이지 크기 제안은 승인 대기다. 가격·PT 연계·고객 로그인·지점별 게시판·별도 관리자 프론트·자유 페이지 빌더는 범위에 추가하지 않는다.

변경 요약 (2026-09-18): 기존 소개를 유지하고 현재 단계·실제 문서 경로·Windows/Linux 방향을 추가했다. 다음 작업은 정책 결정과 별도 승인된 기술 검증이며 이번 문서 작업에서 자동으로 구현을 시작하지 않는다.
