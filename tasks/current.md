# SPIKE-01 — CMS 편집·공개본·미디어 최소 검증

- 상태: 이전 격리 서버 시험 실행·보고 완료. 2026-09-18 후속 실제 브라우저 검증은 **BLOCKED**(공식 Computer Use 초기화 오류 재현), 개별 브라우저 동작은 NOT_RUN. 이 파일 및 실험 경로가 없었다는 기록은 최초 시험 시작 당시다.
- 목표: 현재 WSL 환경을 문서에 반영하고 Post·CMS 이미지의 편집, 공개본 유지, 공통 HTML/JSON, 보호 미디어를 격리 시험한다.
- 승인 범위: `experiments/cms-spike/**`, `docs/verification/cms-spike.md`, 이 기록, 실험 산출물용 루트 `.gitignore`, 기존 허용 문서의 환경·실행 단계 안내.
- 기존 README·AGENTS·docs 미커밋 변경과 인덱스 보존. 자동 staging·commit·push 없음.
- 전체 제품 구현·운영 배포는 미승인. P-01~04/A-01 및 ADR은 계속 Proposed.
- 완료: WSL 환경 문구 정정 후 AGENTS.md 재확인, 독립 의존성 35개 설치·잠금, SQLite 마이그레이션, 서버 테스트 16개 PASS, 루프백 HTTP 스모크 및 시작한 서버 종료.
- 결과·제약: [검증 보고서](../docs/verification/cms-spike.md), [재현·관리자 확인 절차](../experiments/cms-spike/README.md). 브라우저·PostgreSQL·별도 상용 Linux 배포·전체 RV/ENV 검증으로 확대하지 않는다.
- 후속 재확인: 기존 Linux venv Python 3.14.4 / Django 5.2.17 / Wagtail 7.4.3 / Pillow 12.3.0, SQLite A 공개 리비전 1·초안 2, B 리비전 3, 합성 이미지 4개 보존. staff·superuser 각 0개. DB는 읽기 전용 조회.
- 장애: `mcp__node_repl__js`의 공식 `@oai/sky` 초기화에서 `sandboxCwd is not a local file URI: file:///home/shlee/Workspace/ai/01.codex/y3gym`. 브라우저 선택·로그인·캡처 전 실패. 증거는 `experiments/cms-spike/.runtime/browser-followup-20260918T134605640425Z/`에 신규 저장.
- 이번 서버·계정 생성·DB/미디어 변경 없음. 기존 테스트/HTTP 스모크 재실행 없음. SP-01·05·11 서버 PASS는 이전 기록이며 브라우저 BLOCKED, 별도 JS 렌더링 NOT_RUN. 공개 HTML/JSON 기준 수집·초안 저장 후 비교는 미실행.
- 다음 작업: 사용자가 공식 도구의 현재 WSL 컨텍스트 초기화 장애를 해결한 뒤 숨김 암호 입력·직접 로그인 준비, 편집 전 공개 HTML/JSON 기준 수집 후 승인된 브라우저 초안 검증 재개. Publish/Unpublish 제외. 전체 홈페이지 구현·기술 최종 채택·운영 배포를 자동 시작하지 않는다.
- 제한 진단 완료: sky import 없는 단순 JS도 같은 URI 오류. 공식 js_reset 성공 후 초기화 1회 재시도 실패. 실패 경계는 node_repl cwd 처리이며 Windows/WSL 컨텍스트 불일치는 추정, 내부 원인 미확정. 증거는 `.runtime/tool-diagnosis-*/results.json` 신규 파일.
- 수동 재개 준비 완료: 실험 README에 WSL 명령·Windows URL·fixture 경로·기대값·증거·종료 절차, `computer-use-support-draft.md`에 미전송 문의 초안, `manual-browser-results-template.md`에 M01~15 기록표 추가. 수동 결과는 아직 없으며 모두 NOT_RUN. 서버·계정 생성 및 데이터 변경 없음.
- Git 인계: 이 작업은 staging/commit/push 미수행. 후속 Git 담당자는 기존 변경까지 비교하며 `.runtime/`, `.venv/`, `.cache/`, `.env*`, DB/저널·미디어·비밀값·로그·Python 캐시를 제외한다. SP-01·05·11 브라우저 BLOCKED는 해소되지 않았다.
- 후속 Git 검토(2026-09-18): 사용자의 별도 커밋·푸시 승인에 따라 기존 설계·SPIKE-01 산출물 전체를 검토했다. fetch 후 main/origin/main은 같은 79e0c3f, 분기 없음. 이번 서버 테스트 16개(13.166s), Django check, 마이그레이션 차이 점검, 의존성 35개 호환 점검 통과. 기존 DB·미디어·fixture 11개 파일 해시 불변. 브라우저 BLOCKED/개별 동작·JS NOT_RUN 유지. 상세 재검증은 검증 보고서 §12, 최종 커밋·푸시 결과는 Git 담당 작업 완료 보고에서 확인한다.

- 사용자 보고 갱신(2026-09-18): 일반 운영자 로그인 성공, Codex 내장 브라우저, URL `http://127.0.0.1:8765/admin/`. 직접 화면 관찰/권한 재확인은 아님. 이전 staff 0개 기록은 과거 조회값. 사용자가 시작한 서버는 종료하지 않음.
- 현재 공식 도구에 내장 브라우저 조회/조작 기능은 확인되지 않음. 기존 node_repl 오류는 재시도하지 않음. 다음은 Snippets→Posts→A 초안 제목·대표/본문 선택창 목록·썸네일을 사용자에게 짧게 확인받는 단계. 저장/업로드 전 공개본 기준 수집 필요. SP-01·05·11 직접 브라우저 BLOCKED 및 로그인 이외 NOT_RUN 유지. 변경 파일은 이 기록과 검증 보고서 §13뿐이며 Git 쓰기 작업 없음.
