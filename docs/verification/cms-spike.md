# SPIKE-01 — CMS 편집·공개본·미디어 실행 보고서

실행·확인일: **2026-09-18**. 범위: `experiments/cms-spike`의 Post 하나와 CMS 이미지, WSL Ubuntu, 로컬 SQLite·파일 저장소.

**현재 상태(2026-10-05 KST):** 새 Paragraph UI 표시 확인에 이어 사용자가 “입력·저장·미리보기 모두 정상”이라고 답했다. 질문 범위인 한글 두 줄·줄바꿈·일부 굵게·Save draft·재열기/Preview 유지만 사용자 보고로 PASS다(§20 후속 기록). 추가로 “이미지 옵션 → 이미지 선택·교체 창 열기 → 취소” 후 기존 이미지 유지도 “유지ㅇㅋ”라는 사용자 보고로 확인했다. 에이전트 직접 관찰·캡처는 없다. 실제 이미지 교체/모든 취소 경로/전체 SP 통과가 아니다. 서버17개/JS7개는 10/04 기록이며 이번에는 문서만 갱신했다.

후속 브라우저 검증(2026-09-18): **자동화 도구 BLOCKED / 수동 일부 확인(사용자 보고)**. 아래 §1~9는 이전 서버 검증 기록이며 이번 재실행 결과가 아니다. 도구 진단은 §10~11, 최신 수동 관찰 결과는 §13을 따른다.

**환경 문구 정정, 격리 코드 작성, 의존성 설치, 마이그레이션, 서버 테스트와 루프백 HTTP 검증까지 수행했다.** 서버 테스트16개 통과 기록이 있다. 최초 시험 당시 브라우저 편집/미리보기는 NOT_RUN이었으며, 이후 사용자 수동 확인 범위는 §13에 별도로 기록한다. 이 결과를 원안 전체 충족·제품 구현 완료·운영 적합성이나 정책 승인으로 합산하지 않는다. P-01~04/A-01 및 두 ADR은 계속 **Proposed**다.

## 1. 질문별 결과

| 질문 | 이번에 확인한 결과 | 남은 한계 |
|---|---|---|
| 기존 Wagtail에서 본문·이미지·미리보기 가능한가? | 기본 관리자 폼, Draftail 등록, 업로드/선택/다중 업로드, 초안 미리보기 요청과 저장 결과 PASS | 실제 브라우저의 클릭·서식 입력·선택창·이미지 표시 사용성 NOT_RUN |
| 수정 초안이 공개 제목·본문·이미지 참조를 보존하는가? | CMS 편집 POST로 새 초안을 저장해도 HTML/JSON 전체 표현과 live_revision ID 유지; 새 자산은 비공개. 새 공개 후만 교체됨 | Post에 한정, 다른 모델·동시 편집·복원 전체 미검증 |
| 같은 공개 조회/변환으로 HTML·JSON 가능한가? | `published_post`와 `serialize_post`를 공유. 관리자 세션도 공개 범위 불변. 본문 서식·이미지·외부 링크 변환 확인 | 실험 경로/DTO이며 제품 API 계약 아님. 실제 프론트·CMS page/document 링크 매핑 미구현 |
| P-04와 기존 CMS의 최소 연동 가능한가? | 인증된 CMS 파일 URL, 컬렉션별 권한, 공개본 대표·본문 참조 재판정, 공유/철회, no-store가 로컬 요청 시험에서 동작 | 맞춤 저장·전달·권한 코드 필요. 브라우저·운영 프록시·외부 저장소까지 보장하지 않음 |

## 2. 환경·작업 상태

사용자 보고: Windows 호스트 위 WSL Ubuntu 개발, 향후 별도 Linux 상용 배포. Windows는 편집·브라우저 접근 환경이다. Windows 호스트 제품·버전 및 실제 브라우저 접속은 직접 확인하지 않았다.

직접 확인한 사실:

| 항목 | 확인 결과 |
|---|---|
| 작업 디렉터리 / Git 루트 | 모두 `/home/shlee/Workspace/ai/01.codex/y3gym` |
| 저장소 정체 | README와 전체 명세의 헬스장 홍보 홈페이지. PT 관리 서비스와 연계하지 않는 명세 확인 |
| OS | `/etc/os-release`: Ubuntu 26.04.1 LTS (Resolute Raccoon), VERSION_ID 26.04 |
| 커널 | `Linux … 6.18.33.2-microsoft-standard-WSL2 … x86_64` |
| 파일시스템 | `findmnt -T .`: `/dev/sdd`, ext4, 마운트 `/`; Windows 드라이브 마운트가 아닌 현재 Linux 파일시스템 |
| Python | `/usr/bin/python3` → Linux ELF `/usr/bin/python3.14`, 3.14.4 |
| 셸 / Git | `/usr/bin/bash`, `/usr/bin/git`, Linux ELF. Windows 실행 파일 호출 없음 |
| 패키지 도구 | 기존 `/home/shlee/.local/bin/uv`, 0.12.16, Linux ELF |
| 가상환경 | `experiments/cms-spike/.venv/bin/python`, sys.prefix도 실험 경로 내부 |
| 초기 장애와 처리 | 시스템 `venv` 모듈은 있고 `ensurepip`·pip은 없음. 이미 설치된 Linux uv로 독립 venv 생성에 성공. 시스템 Python/venv 패키지 설치나 Python 다운로드 없음 |
| Git 시작 상태 | 커밋 1개, README 수정, AGENTS.md·docs 미추적. staging 변경 없음 |
| 기존 실험/작업 기록 | `experiments/cms-spike`, `tasks/current.md`, 루트 `.gitignore`는 시작 시 없었음 |
| 미확인 | WSL 배포 패키지 버전, Windows 호스트 버전, 상용 Linux 배포판·버전·호스팅·실행 방식 |

`pwd`, `git rev-parse --show-toplevel`, `git status --short`, `git ls-files --stage`, `git rev-list --count HEAD`, `/etc/os-release`, `uname -a`, `command -v`, `file`, `findmnt`, Python 버전·모듈 조회를 사용했다. 전체 프로세스의 이름만 읽기 확인했으며 다른 서버에 접속하거나 종료하지 않았다. PostgreSQL/Docker 설치·호환성은 이번 검증 항목으로 조사하거나 판정하지 않았다.

WSL에서 Linux 도구로 작업할 때 Linux 파일시스템과 Windows 파일시스템을 구분해야 한다는 Microsoft 안내도 확인했다. 현재 위치는 실제 `findmnt` 결과로 기록했으며 문서의 예시 경로를 사실로 사용하지 않았다. [Microsoft WSL 파일시스템](https://learn.microsoft.com/en-us/windows/wsl/filesystems)

## 3. 후보·설치 버전과 공식 근거

아래 자료는 2026-09-18 확인했다. 최신 stable 문서는 Wagtail 8.0으로 연결되므로 실험 기능 자료는 **7.4.3** 버전 문서를 사용했다. 프리릴리스나 지원 종료 계열을 선택하지 않았다. 운영 채택 버전은 미정이다.

| 구성 | 실제 설치/사용 | 호환·지원 확인 |
|---|---|---|
| Python | 기존 Linux 3.14.4 | 3.14는 유지보수 중인 정식 계열, 공식 일정의 EOL 2030-10. 시스템 패치를 변경하지 않았고 최신 마이크로 버전이라고 주장하지 않음. [Python 상태](https://devguide.python.org/versions/) |
| Django | 5.2.17 | 5.2 LTS는 2028-04까지 연장 지원, Python 3.14는 5.2.8부터 지원. [지원 표](https://www.djangoproject.com/download/), [호환표](https://docs.djangoproject.com/en/5.2/faq/install/) |
| Wagtail | 7.4.3 | 7.4 LTS는 Django 5.2/6.0, Python 3.10~3.14 조합 명시; 지원 종료 2027-11-02. [버전별 호환표](https://docs.wagtail.org/en/v7.4.3/releases/upgrading.html), [지원 일정](https://github.com/wagtail/wagtail/wiki/Release-schedule), [7.4.3 릴리스](https://docs.wagtail.org/en/v7.4.3/releases/7.4.3.html) |
| Pillow | 12.3.0 | Pillow 12의 Python 3.14 지원과 정식 릴리스 확인. Linux wheel 설치 및 실제 PNG 960×720 → 800×600 변환 실행. [호환표](https://pillow.readthedocs.io/en/stable/installation/python-support.html), [릴리스](https://pillow.readthedocs.io/en/stable/releasenotes/12.3.0.html) |
| Willow / pillow-heif | 1.12.0 / 1.7.0 | Wagtail 의존성으로 설치. 공식 Willow 1.12.0 설정의 Python ≥3.10·3.14 분류, Pillow/HEIF 의존성 확인. 설치된 두 배포의 Python 3.14 분류도 확인. HEIF 파일 동작은 시험하지 않음. [Willow 설정](https://github.com/wagtail/Willow/blob/v1.12.0/pyproject.toml), [pillow-heif 설치 자료](https://pillow-heif.readthedocs.io/en/stable/installation.html) |
| tzdata | 2026.4 | 설치 메타데이터 확인. 실제 ZoneInfo Asia/Seoul의 UTC+9 확인; 팝업 경계 전체 검증은 아님 |

`requirements.in`은 직접 후보 입력, `requirements.lock`은 실제 해석한 35개 의존성의 버전·해시 잠금이다. 설치는 이 잠금에 `--require-hashes`를 적용했다. uv의 의존성 점검은 35개 호환을 보고했고, 이것을 취약점 전수 점검이나 운영 승인으로 해석하지 않는다. 모든 설치·캐시는 실험 내부 `.venv`·`.cache`에 한정했다.

Wagtail은 Snippet 등록, 리비전·초안·미리보기 기능을 제공한다. 이번 코드는 DraftStateMixin/RevisionMixin/PreviewableMixin과 기존 패널을 사용하고 별도 버전 관리 시스템을 만들지 않았다. PublishingPanel·WorkflowMixin은 추가하지 않았다. [Snippet 등록](https://docs.wagtail.org/en/v7.4.3/topics/snippets/registering.html), [선택 기능](https://docs.wagtail.org/en/v7.4.3/topics/snippets/features.html)

컬렉션 privacy만으로 이미지를 보호할 수 없다는 공식 설명에 따라 원본을 직접 제공하지 않는 전달 경로를 구현했다. 본문도 CMS 저장 표현을 그대로 JSON에 넣지 않고 이미지·링크를 변환했다. [Privacy](https://docs.wagtail.org/en/v7.4.3/advanced_topics/privacy.html), [Headless](https://docs.wagtail.org/en/v7.4.3/advanced_topics/headless.html)

## 4. 변경 내용과 구현 분류

| 구분 | 구현/설정 |
|---|---|
| 기본 제공 재사용 | CMS 등록·수정·목록, Draftail 서식, 이미지 업로드·선택창·다중 업로드, 리비전·공개/비공개, 미리보기 폼 상태 |
| 설정·모델 등록 | Post 제목·분류·본문·대표 이미지, 공개 관련 mixin, 패널, 미리보기 템플릿, SQLite, 제한된 PNG/JPEG 입력, 로컬 비밀값 생성 |
| 맞춤 코드 | 공개 리비전 선택, HTML/JSON 공통 표현, 본문 embed 변환·안전한 링크/서식 정리, 대표+본문 참조 검사, 인증/컬렉션 권한 파일 전달, 공개 참조 재판정 |
| 맞춤 권한 연동 | 이미지 파일 교체 거부 폼, 권한 없는 이미지 ID를 게시글 폼에 주입하는 요청 거부, 이미지 삭제/다중 삭제/일괄 삭제 경로 차단, 일반 운영자 삭제 UI 일부 숨김, no-store |
| 실험 보조 | 합성 PNG 생성, 데모 seed, 암호 숨김 입력의 일반 운영자 생성 명령, 서버 테스트·루프백 스모크 |
| 미구현 | 지점·트레이너·팝업·지도·고객 로그인·예약·결제·별도 프론트·페이지 빌더·새 워크플로·제품 API 전체·운영 전달/백업 |

Wagtail 7.4.3 설치 소스에서 기본 이미지 권한의 delete가 change와 연결되고, 기존 파일 교체가 원본과 변환본을 지우는 동작을 확인했다. 따라서 삭제 권한 체크박스만 제거하는 방식으로 해결했다고 보고하지 않는다. 파일 교체는 공식 `WAGTAILIMAGES_IMAGE_FORM_BASE` 확장점으로 막고, 삭제는 고정 버전의 URL 이름을 확인하는 실험 미들웨어로 차단했다. 기존 CMS 패키지 파일은 수정하지 않았다. [이미지 폼 설정](https://docs.wagtail.org/en/v7.4.3/reference/settings.html#wagtailimages-image-form-base)

환경·단계 설명만 수정한 기존 파일:

- `README.md`: 현재 단계·WSL 개발/별도 Linux 운영 설명, 실행 안내/보고서 링크. 기존 소개·문서 목록·과거 변경 요약 보존.
- `AGENTS.md`: 현재 개발 환경, 별도 승인된 격리 시험과 전체 구현 미승인 구분. 보안·비밀값 보호·상위 지침 변경 없음. 수정 직후 실제 파일을 다시 읽어 확인함.
- `docs/screens.md` §1: 현재 환경 조건 문단.
- `docs/data-model.md` §12: 실행 환경·SQLite 시험과 PostgreSQL 검증 구분.
- `docs/adr/0001-runtime-and-deployment.md` §1·2.1·2.2·3·5·6: WSL 기준·과거 Windows 대안·실행 단계. ENV-01은 WSL 개발/별도 Linux 운영을 구분하고 ID 유지.
- `docs/adr/0002-publication-and-media.md` §5: 전체 RV 계획과 이번 제한된 SP 실행 결과를 구분하는 안내만 추가.

`docs/api-contract.md`는 변경할 현재형 환경 문구가 없어 원문 유지했다. `docs/review-resolution.md`도 원문 그대로이며 과거 Windows 환경 기록의 갱신은 후속 문서에서만 알렸다. 명세 버전·제품 정책·API 계약·ADR 상태를 승격하거나 변경하지 않았다.

## 5. 실제 실행과 증거

전체 재현 명령 및 브라우저 절차는 [실험 README](../../experiments/cms-spike/README.md)에 있다. 아래 명령은 실험 디렉터리에서 실제 실행했다. venv 최초 생성은 저장소 루트에서 실험 경로를 인자로 지정했다.

```bash
uv venv --no-config --no-python-downloads --python /usr/bin/python3 experiments/cms-spike/.venv
# 이후 cwd: experiments/cms-spike
uv --no-config --cache-dir .cache pip compile --python .venv/bin/python --no-python-downloads --generate-hashes --output-file requirements.lock requirements.in
uv --no-config --cache-dir .cache pip install --python .venv/bin/python --no-python-downloads --require-hashes -r requirements.lock
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations posts
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py test posts --noinput -v 2
.venv/bin/python manage.py makemigrations --check --dry-run
uv --no-config --cache-dir .cache pip check --python .venv/bin/python
.venv/bin/python manage.py seed_demo
.venv/bin/python smoke_http.py
```

실행 결과:

- check: 문제 0건. 마이그레이션 적용 완료, 잔여 모델 변경 없음.
- 최종 `manage.py test`: **16 tests / 9.363s / OK**. `.runtime/tests-final.log`에 전체 실행 기록. 테스트는 메모리 SQLite와 별도 `.runtime/test-media-*` 사용.
- 서버 테스트는 일반 운영자 세션·CSRF 검증을 사용했다. 로그인 세션 생성은 Django test client의 `force_login`이며 암호 로그인·브라우저 인증 UX 시험이 아니다.
- 실제 HTTP 스모크: 관리자 로그인 페이지·정적 CSS·공개 HTML/JSON·대표/본문 표시본 200, 초안 표시본 404, 원본 보호 경로 403, 기본 미디어·런타임 경로 404. 최종 실행 PID 37862, `127.0.0.1:49637`; 자기 프로세스를 종료하고 `stopped: true` 확인. 앞선 스모크 PID 37316도 종료했다.
- 로그/증거: `.runtime/migrate.log`, `.runtime/tests*.log`, `.runtime/http-server.log`, `.runtime/http-smoke-*.json`. 실제 비밀값·암호를 기록하지 않으며 이 디렉터리는 Git 제외.
- 초기 실패 기록도 보존했다. 테스트 DB/저장소 간 Wagtail 변환본 캐시 격리, CMS 미리보기의 POST→GET 순서, 폼 모듈 초기화 순서, 기본 권한 거부 302 응답, 선택창 업로드 필드 prefix를 수정했다. 파일 제공/비제공·공개본 유지 기대값을 낮추지 않았다.
- `seed_demo`를 재실행해 동일 게시글·이미지 ID가 보존됨을 확인했다. 실제 인물·사진·경력·운영 DB는 사용하지 않았다.

## 6. SP-01~12 결과

PASS는 아래 명시한 실행 계층만 뜻한다. 브라우저 계층을 합산한 종합 PASS는 부여하지 않는다.

| ID | 상태 / 계층 | 실행 증거 |
|---|---|---|
| SP-01 | **PASS 서버 / NOT_RUN 브라우저** | CMS 작성·목록·편집 폼, Draftail 등록, 단일·다중·선택창 업로드, 이미지 선택 응답·썸네일 접근 검증. 실제 서식 입력/선택창 클릭 사용성 미실행 |
| SP-02 | **PASS** CMS·DB·HTML/JSON·이미지 요청 | A 최초 공개 POST 후 두 표현의 제목·본문 일치, 대표·본문 이미지 실제 디코딩. 루프백 HTTP에서도 이미지 200 |
| SP-03 | **PASS** CMS·DB·공개 요청 | 새 제목·본문·서로 다른 새 대표/본문 이미지로 초안 저장. 공개 HTML bytes·JSON 및 live_revision ID 유지. 새 자산 공개 표시 404·원본 403 |
| SP-04 | **PASS** CMS·DB·공개 요청 | 수정본 Publish 후 새 제목·본문·이미지 반영. 과거 리비전만 참조하는 옛 이미지의 표시 URL은 404, 원본 파일은 보존 |
| SP-05 | **PASS 서버 / NOT_RUN 브라우저** | CMS preview 폼 상태 POST 후 GET에 최신 초안/이미지. 운영자 파일 200, 비로그인 파일 403, 미리보기 진입 302. 공개 조회는 기존 공개본. 실제 브라우저 렌더링 미실행 |
| SP-06 | **PASS** 인증·스토리지·HTTP | 원본/썸네일/변환본 무권한 403, 권한 운영자 200; 기본·추정 우회·서명 serve 경로 404. 컬렉션 권한 없는 관리자도 원본 403 |
| SP-07 | **PASS** CMS·DB·이미지 요청 | A·B 공유 이미지가 B 본문에만 남아도 A 비공개 후 표시본 200 |
| SP-08 | **PASS** CMS·DB·이미지 요청 | B도 비공개 후 동일 URL의 새 방문자/관리자 공개 요청 모두 404. 재공개 후 200. 과거 외부 복사본 회수 미보장 |
| SP-09 | **PASS** 공개 HTML/JSON | 관리자·방문자 응답 동일. 미공개 Post는 모두 404. 허용 DTO 필드만 반환 |
| SP-10 | **PASS** CMS·DB·파일 | 직접 파일 교체 POST는 오류 폼, 원본 bytes 불변. 단일/다중/일괄 이미지 삭제 403·객체 보존. 새 자산 선택으로 교체 성공. 최고 관리자/DB 조작 차단 주장은 안 함 |
| SP-11 | **PASS 서버 / NOT_RUN 브라우저** | JSON 본문에 정상 서식·외부 링크·표시 이미지 URL. 내부 embed/linktype·관리자/로컬 경로 없음. 이미지 요청/디코딩 및 위험 태그/링크 제거 검증. 실제 JS 클라이언트 표시 미실행 |
| SP-12 | **PASS WSL 실행** | Linux Python·현재 WSL 커널, 경로 대소문자 구분, PNG 변환, Asia/Seoul 시간대, 마이그레이션·16개 테스트 실행. 별도 상용 Linux·Windows 네이티브는 NOT_RUN |

추가 검증: 권한 없는 컬렉션의 ID를 게시글 대표·본문에 직접 주입한 공개 요청 거부, Post 삭제 거부(302와 객체 보존), CSRF 없는 편집 POST 403, 공개 HTML/JSON 쓰기 405. 기본 관리자 권한 거부는 Wagtail의 `/admin/` 302 응답인 경우가 있어 보호 파일의 직접 403과 구분했다.

## 7. URL별 접근 및 우회 경로

| URL 종류 | 방문자 / 무권한 | 자산 권한 운영자 | 비고 |
|---|---|---|---|
| `image.file.url` → `/cms-files/original_images/...` | 403 | 200 | 업로드 원본. 로그인만 있고 컬렉션 권한이 없으면 403 |
| 관리자 썸네일 `.url` → `/cms-files/images/...max-165x165...` | 403 | 200 | chooser가 생성한 URL도 같은 인증 전달 사용 |
| 표시 크기의 내부 변환본 `.url` → `/cms-files/images/...max-800x600.format-png...` | 403 | 200 | 공개 사용처가 있더라도 이 내부 URL은 관리자용 |
| 공개 HTML/JSON 대표·본문 → `/spike/display/{id}/` | 공개 참조 있으면 200, 없으면 404 | 같은 판정 | 원본 대신 고정 PNG 변환본. 초안·과거 리비전은 공개 참조에 포함하지 않음 |
| `/media/{실제 파일명}` | 404 | 정적 미디어 서빙 없음 | 실제 루프백 서버도 404 |
| `/private-media/...`, `/.runtime/private-media/...` | 404 | 공개 라우트 없음 | test client 요청 |
| `/cms-files/../secret-key` | 403 | 404 | DB의 정확한 파일명으로 조회하며 경로 합성 안 함. 비밀값 본문은 읽거나 출력하지 않음 |
| `/images/{유효 생성 서명}/{id}/original/...` | 404 | 해당 공개 serve 라우트 미등록 | 서명만으로 파일을 공개하지 않음 |
| CMS `/admin/images/{id}/preview/{filter}/` | 비로그인 302 | 200·no-store | CMS 기본 인증/이미지 편집 권한 경로 |
| CMS Post 미리보기 | 비로그인 302, Post 권한 없는 관리자 302 | 최신 초안 HTML 200·no-store | 공개 JSON의 범위를 넓히지 않음 |

정적 CSS를 제외한 위 앱 응답은 `Cache-Control: max-age=0, no-cache, no-store, must-revalidate, private`를 확인했다. 표시용 공개 이미지에도 이번 실험에서는 no-store를 적용했다. 서명 URL 만료를 기다리는 설계가 아니라 요청마다 현재 공개본 참조를 판정한다. 이미 내려받은 파일·진행 중 요청·외부 캐시는 회수 대상으로 보장하지 않는다.

## 8. P-04 유지 시 추가 작업·운영 제약

- 실제 브라우저에서 SP-01·05·11을 확인해야 한다. 서버 HTML 200만으로 편집 사용성을 판정하지 않았다. 절차는 실험 README에 있으며 이번에는 스크린샷 증거가 없다.
- 공개 참조 검사에 모든 공개 Post의 리비전을 읽는 O(n) 방식을 사용했다. 운영 규모에서는 참조 색인·일관성·동시 변경·성능을 검증해야 한다. 별도 권한 플랫폼·캐시 서버를 이번에 만들지 않았다.
- 별도 Linux 웹 서버/리버스 프록시가 원본·변환본 디렉터리를 직접 제공하지 않는지, HTTPS·캐시·스토리지 우회·전달 중 실패를 검증해야 한다. 이번에는 로컬 Django 개발 서버만 시험했다.
- Post만 공개 사용처다. SiteContent·지점·트레이너·팝업으로 확장할 경우 각 공개 조건과 기간 경계 검증이 필요하다.
- 이미지 파일 교체·삭제는 제한했지만 최고 관리자·직접 DB/파일 조작까지 막지 않는다. 과거 리비전 복원·파일 유실 복구·유지보수 삭제의 전체 참조 검사는 미검증이다. 자동 미참조 삭제·리비전 정리는 만들지 않았다.
- CMS의 다중 업로드 직후 삭제/중복 정리 버튼까지 모두 바꾸지는 않았다. 직접 삭제는 차단되며 편집 UX 정리는 후속 확인 대상이다. 정상 PNG 업로드를 시험했으며 실패한 임시 업로드의 모든 복구 경로·HEIF/SVG 등은 검증하지 않았다.
- 안전한 외부 링크는 변환했지만 CMS page/document 내부 링크는 이 실험에 대응하는 공개 페이지가 없어 텍스트로 변환한다. 제품 내부 링크 설계로 승인하지 않았다.
- ‘업로드 즉시 전체 공개’로 P-04를 완화하지 않았다. 운영 비용을 줄이기 위한 그러한 대안은 **별도 명시적 정책 승인 필요**이며 이번에 적용하지 않았다.

## 9. 미검증·재사용·종료 상태

**NOT_RUN:** 실제 브라우저 편집/미리보기·Windows 브라우저 접근, Windows 네이티브 Python, 별도 Linux 서버/컨테이너·Gunicorn·리버스 프록시·HTTPS·CDN/객체 저장소, PostgreSQL 잠금·본점 동시성, 지점·트레이너·팝업·지도, DB/미디어 백업·복구. SQLite는 PostgreSQL의 `select_for_update` 검증을 대체하지 않는다. [Django QuerySet](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update)

재사용 후보: 공개 리비전과 최신 수정 초안을 구분하는 방식, HTML/JSON 공통 변환, 대표·본문 참조 및 새 자산 교체/철회 테스트, 컬렉션 권한을 확인하는 로컬 저장·전달 연동. 정책 승인과 운영 설계 후 다시 검토해야 한다.

실험 전용: SQLite·단순 템플릿·`/spike/` 경로/DTO·고정 PNG 크기·O(n) 참조 검사·일괄 no-store·버전별 URL 미들웨어·합성 자료·데모 명령·개발 서버 설정. 제품 코드로 자동 승격하지 않는다.

이번 추가 파일은 `experiments/cms-spike/**`의 소스·테스트·마이그레이션·의존성 정의/잠금·안내, 이 보고서, `tasks/current.md`, 실험 산출물 전용 `.gitignore`다. 기존 문서 수정은 §4의 여섯 파일에 한정했다. `.venv`·DB·미디어·키·캐시·로그는 실험 내부에서 Git 제외이며 소스·테스트·마이그레이션·의존성은 제외하지 않았다.

기존 사용자 변경을 보존했다. 종료 점검에서도 커밋 1개, 인덱스의 README blob `84ec26e035a6cd54f407d656fec4d5313fa9c2bd`와 빈 staged diff가 유지됐다. `review-resolution.md` SHA-256 `39b81f230cf3ac524a6476ac0f5b651eb027c4aec08c52845537940341f4311a`, `api-contract.md` SHA-256 `8b52316e4098792efff806bad753cae64ff30513b9df339bb0be5d7be19754b2`는 시작 시와 동일하다. 자동 staging·commit·push, reset/clean/restore/stash, 저장소 이동·Windows 복사본 삭제는 하지 않았다.

환경 정정 **완료**, 격리 시험 코드 **작성·실행 완료**, 브라우저 확인 **NOT_RUN**으로 종료한다. 전체 홈페이지 구현·정책 최종 승인·운영 배포로 이어서 진행하지 않는다.

## 10. 실제 브라우저 후속 검증 — 2026-09-18

### 시작 점검과 증거

상위 경로 및 저장소 하위의 AGENTS.md/AGENTS.override.md를 검색했다. 적용 파일은 루트 AGENTS.md 하나이며 README, 세 명세, review-resolution, 두 ADR, 이 보고서, 실험 README, tasks/current.md를 다시 읽었다. Git 루트와 cwd는 `/home/shlee/Workspace/ai/01.codex/y3gym`, 파일시스템은 ext4, OS는 Ubuntu 26.04.1 LTS, 커널은 `6.18.33.2-microsoft-standard-WSL2`다. 기존 Linux 가상환경에서 Python 3.14.4 / Django 5.2.17 / Wagtail 7.4.3 / Pillow 12.3.0을 직접 재확인했다. 설치·마이그레이션·기존 성공 테스트·HTTP 스모크를 반복하지 않았다.

Git 시작 상태는 README 수정 및 `.gitignore`, AGENTS.md, docs/, experiments/, tasks/ 미추적이며 staged diff는 비어 있었다. 기존 변경을 보존했다. SQLite를 `mode=ro`로 조회했으며 비밀번호·세션·비밀값 필드는 조회하지 않았다. 계정은 총 1개, staff 0개, superuser 0개다. 따라서 사용할 관리자 계정은 없으며 기존 계정의 암호 로그인 가능 여부는 확인하지 않았다. `create_spike_editor`의 숨김 입력과 일반 권한 부여 절차를 읽었으나 도구 장애로 생성은 진행하지 않았다.

증거 디렉터리: `experiments/cms-spike/.runtime/browser-followup-20260918T134605640425Z/` (Git 제외).

- `preflight.json`: 환경·버전·Git·읽기 전용 DB 기준 상태, 리비전별 본문/이미지 참조, 이미지 파일 존재, DB 해시.
- `computer-use-error.txt`: 실제 공식 초기화 호출과 도구 오류를 기록한 텍스트. 브라우저 스크린샷이 아니다.

A(ID 1)는 공개 리비전 1(`SPIKE PUBLIC A`, 대표 1·본문 2), 최신 수정 초안 2(`SPIKE DRAFT A`, 대표 3·본문 4)다. B(ID 2)는 공개/최신 리비전 3이며 본문 이미지 2를 공유한다. 이미지 자산 1~4의 원본 및 합성 PNG fixture 4개가 존재한다. 이는 DB 기준 상태이며 공개 HTML/JSON 응답 비교 기준은 이번에 수집하지 않았다. 브라우저가 복구되면 편집 전에 응답 기준을 새로 기록해야 한다.

### 도구 장애

Computer Use SKILL.md와 guidance/api/confirmations를 읽고, 제공된 도구 목록에서 `mcp__node_repl__js`를 확인했다. 별도 브라우저 조작 도구는 확인되지 않았고 `open_in_codex`는 탭 표시 기능이므로 조작·검증의 대체로 사용하지 않았다. 공식 초기화 코드를 실행했으나 JavaScript 세션 초기화 단계에서 실패했다.

```text
Mcp error: -32602: js: codex/sandbox-state-meta: sandboxCwd is not a local file URI: file:///home/shlee/Workspace/ai/01.codex/y3gym
```

이전 보고와 같은 오류가 재현됐다. 앱/창 목록 조회·브라우저 선택·로그인·화면 캡처에 도달하지 못했다. 실제 브라우저 종류·버전과 Windows→WSL 루프백 접근은 미확인이다. 이는 도구 장애이며 Wagtail 기능 FAIL로 판정하지 않는다. 비공식 우회 도구·환경 이동·설치·방화벽 변경·외부 바인딩은 수행하지 않았다.

### 계층별 결과

| 항목 | 이전 서버 계층 기록 | 이번 브라우저 계층 |
|---|---|---|
| SP-01 | PASS 기록 유지, 이번 재실행 없음 | BLOCKED; Snippets→Posts, 최신 초안 표시, Bold/Italic·링크 입력, 대표/본문 chooser·보호 썸네일, 새 자산 업로드/선택, 덮어쓰기 비활성 확인, Save draft·재열기 모두 NOT_RUN |
| SP-05 | PASS 기록 유지, 이번 재실행 없음 | BLOCKED; 최신 초안 서식·링크·대표/본문 이미지 Preview 표시와 인증/방문자 접근 차이 모두 NOT_RUN |
| SP-11 | PASS 서버 변환 기록 유지, 이번 재실행 없음 | BLOCKED 브라우저 HTML/JSON 확인; 별도 JS 클라이언트 렌더링 NOT_RUN |
| 초안 저장 후 공개본 유지 | SP-03 PASS 기록 유지 | NOT_RUN; 새 초안을 저장하지 않았으며 비로그인 별도 세션 HTML/JSON·리비전 비교도 미실행 |
| 초안 새 이미지·보호 이미지 무권한 접근 | SP-03·06 PASS 기록 유지 | NOT_RUN; 이번 업로드·이미지 선택·방문자 접근 없음 |

PASS는 위 환경/자료의 읽기 점검과 이전 기록에 한정한다. 브라우저 검증 PASS나 제품 결함 FAIL은 새로 부여하지 않는다. Publish/Unpublish는 수행하지 않았고 공개·철회 서버 검증을 브라우저 초안 검증으로 합산하지 않는다.

### 종료·재개 조건

이번 변경은 이 보고서, tasks/current.md, 실험 README의 후속 절차 및 새 Git 제외 증거 파일뿐이다. 실험 코드 수정·회귀 테스트는 없으며 DB·미디어·가상환경·기존 로그는 보존했다. 이번에 시작한 서버는 없어 종료 대상도 없다. 계정 생성·편집·업로드·초안 저장·Publish·Unpublish는 모두 미실행이다.

필요한 사용자 조치: 현재 WSL 작업 경로에서 공식 Computer Use의 `node_repl` 초기화가 가능하도록 도구 연결/실행 컨텍스트 오류를 해결하거나 지원 담당자에게 위 오류를 전달한다. 저장소 이동이 해결책이라고 단정하지 않는다. 복구 후 기존 `create_spike_editor local-editor` 명령의 숨김 암호 입력과 브라우저 직접 로그인을 사용자에게 맡기고, README의 루프백 서버 명령으로 실제 검증을 재개한다. 비밀번호는 대화·명령 인자·증거에 남기지 않는다.

PostgreSQL, 상용 Linux 배포, 전체 제품 기능은 계속 미검증이며 P-01~04·A-01 및 두 ADR은 Proposed, 전체 구현·운영 배포·정책 최종 승인은 미승인이다.

## 11. 도구 제한 진단·수동 재개 준비 — 2026-09-18

적용 지침·README·현재 작업 기록·실험 절차·이 보고서를 다시 확인했다. OpenAI Docs 및 Computer Use 스킬을 적용했다. 공식 도구 입력 스키마에는 cwd/host 변경 인자가 없다. Linux 셸은 기존 cwd에서 정상 동작하고 `WSL_DISTRO_NAME`은 `Ubuntu`, `wslpath -w`는 `\\wsl.localhost\Ubuntu\home\shlee\Workspace\ai\01.codex\y3gym\experiments\cms-spike\.runtime\fixtures`를 반환했다. 이는 경로 변환 결과이며 Windows 파일 선택창 접근 성공 증거는 아니다.

진단은 동일 호출 반복 대신 sky import 없는 `nodeRepl.write("SPIKE01_NODE_PROBE");`로 의존 범위를 줄였다. 이 호출도 §10과 동일한 `codex/sandbox-state-meta` URI 오류로 실패했다. 공식 `mcp__node_repl__js_reset({})`는 `js kernel reset` 성공을 반환했다. reset 후 공식 sky 초기화를 한 번 재시도했으나 동일 오류였다. 추가 반복·내부 패치·설정 변경은 하지 않았다. 새 증거는 `experiments/cms-spike/.runtime/tool-diagnosis-*/results.json`의 해당 시각 파일이며 이전 증거는 유지했다.

확인된 실패 경계는 브라우저나 Wagtail 이전의 node_repl 작업 경로 처리다. Windows 대상 도구 컨텍스트와 Linux URI 간 불일치는 **추정**이며 실제 서버 OS/내부 코드 원인은 미확인이다. 공식 [WSL 안내](https://developers.openai.com/es-419/docs/windows/wsl)와 [Computer Use 안내](https://developers.openai.com/es-419/docs/computer-use)를 실제로 열어 확인했으나 해당 오류의 공식 해결책은 확인하지 못했다. 저장소 이동이나 설정 변경이 해결책이라고 주장하지 않는다.

지원 문의 초안 `experiments/cms-spike/computer-use-support-draft.md`에 환경·최소 재현·실제 오류·reset 결과·지원 요청을 정리했다. 외부로 전송하지 않았다. 실험 README에 사용자용 WSL 명령, 직접 숨김 암호 입력/로그인, Windows URL·fixture 경로, 편집 전후 공개 HTML/JSON·DB 리비전 기준, Bold/Italic·링크·두 chooser·새 자산 업로드·Save draft·Preview·독립 방문자 접근 비교·자기 서버 종료 절차를 추가했다. `manual-browser-results-template.md`의 모든 결과는 NOT_RUN이며 사용자 보고와 Codex 직접 관찰을 분리한다.

SP-01·05·11의 이전 서버 PASS는 유지하고 재실행하지 않았다. 실제 브라우저는 계속 BLOCKED, 개별 동작 및 별도 JS 클라이언트 렌더링은 NOT_RUN이다. 사용자 수동 결과는 아직 받지 않았다. 이번에는 서버·계정·브라우저를 실행하지 않았고 DB·이미지·초안을 변경하지 않았다. 문서·진단 기록만 변경했으므로 애플리케이션 회귀 테스트는 실행하지 않았다.

Git 인계: 이 단계 변경은 실험 README, 지원 문의 초안, 수동 결과 양식, 이 보고서와 tasks/current.md 및 Git 제외 새 진단 증거다. staging/commit/push는 수행하지 않았다. `.runtime/` 전체(DB·미디어·키·증거·로그), `.venv/`, `.cache/`, `.env`/`.env.*`, SQLite 및 저널, Python 캐시는 기존 .gitignore대로 제외해야 한다. 다른 기존 미커밋 파일은 별도 Git 담당자가 현재 상태를 검토해야 하며 이번 변경으로 단정하지 않는다.

## 12. Git 검토 단계 재검증 — 2026-09-18

사용자의 별도 커밋·푸시 승인에 따라 기존 설계 문서와 SPIKE-01 산출물 39개 파일을 검토했다. fetch 후 `main`, 추적 브랜치 `origin/main`, 원격 기본 브랜치 `main`은 모두 `79e0c3f0066d0e460fdf34780ddaec8d7a7fec35`였으며 ahead/behind는 0/0, 다른 원격 브랜치는 없었다. 이전 단계의 staging·commit·push 미수행 기록은 당시 결과로 보존한다.

이번에 기존 Linux 가상환경에서 실제 재실행한 결과:

- `manage.py test posts --noinput -v 2`: **16 tests / 13.166s / OK**. 임시 메모리 SQLite와 새 테스트 미디어 경로를 사용했다.
- `manage.py check`: 문제 0건.
- `manage.py makemigrations --check --dry-run`: 변경 없음.
- `uv --no-config --cache-dir .cache pip check --python .venv/bin/python`: 설치된 35개 패키지 호환 확인.
- 기존 DB·private-media·fixture 총 11개 파일의 실행 전후 SHA-256 일치. 기존 DB 마이그레이션·seed·계정 생성·HTTP 스모크·브라우저 검증은 실행하지 않았다.

소스·테스트·마이그레이션·의존성 잠금·문서의 실험 경계와 결과 표현을 검토했고, 로컬 Markdown 링크의 대상 파일 누락 및 커밋 후보의 알려진 인증값 패턴은 발견하지 못했다. 이는 비밀값 탐지의 완전성이나 취약점 전수 검증을 의미하지 않는다. `.runtime`·가상환경·캐시·환경값 파일·DB/저널·미디어·키·로그·Python 캐시 제외 규칙을 확인했다. `review-resolution.md`와 `api-contract.md`의 해시는 §9 기록과 동일하다.

실제 브라우저는 계속 BLOCKED, 개별 동작과 별도 JS 클라이언트 렌더링은 NOT_RUN이다. 이번 서버 재검증으로 브라우저 결과나 P-01~04/A-01·ADR의 Proposed 상태를 승격하지 않는다. 최종 커밋 SHA와 push 확인 결과는 Git 담당 작업의 완료 보고에 남긴다.


## 13. 사용자 로그인 성공 보고 — 2026-09-18

사용자가 일반 운영자로 로그인에 성공했고 브라우저는 **Codex 내장 브라우저**, 현재 URL은 `http://127.0.0.1:8765/admin/`이라고 보고했다. 로그인 성공은 사용자 보고이며 Codex의 직접 화면 관찰·계정 권한 점검 결과가 아니다. 정확한 브라우저 버전과 계정 권한은 이번에 직접 확인하지 않았다. 이전 staff 0개 기록은 이전 조회 시점의 사실이며 현재 계정 상태로 재사용하지 않는다.

현재 제공된 도구 목록을 다시 확인했다. `open_in_codex`는 탭 열기만 제공하며 DOM·화면 조회·클릭 도구는 제공하지 않는다. Windows Computer Use용 node_repl은 이전 실패 이후 복구 근거가 없어 재시도하지 않았다. 음성 전용 화면 도구는 이 텍스트 작업에서 사용하지 않았다. 인증·세션을 추출하거나 대체 도구로 우회하지 않았다.

다음 수동 검사는 기존 README의 Snippets → Posts에서 A 편집 화면의 최신 초안 제목, 대표 이미지 선택창 및 본문 이미지 도구의 목록·썸네일 표시를 확인하는 것이다. 아직 서식 변경·업로드·저장·Publish/Unpublish를 하지 않고 관찰 결과를 먼저 받는다. 메뉴 명칭이 다르면 실제 표시 문구를 사용자에게 받아 이어간다. 편집 전에 공개 HTML/JSON 기준 수집 단계도 완료해야 한다.

SP-01·05·11의 이전 서버 PASS는 유지한다. Codex 직접 브라우저 검증은 BLOCKED, 로그인 이외의 수동 검사는 NOT_RUN/사용자 관찰 대기다. 로그인 성공만으로 편집·선택·Preview 또는 SP 전체를 PASS로 바꾸지 않았다. 서버는 사용자가 시작한 것이므로 종료하지 않았으며 이번 서버 실행·계정 생성·DB/미디어 변경·테스트·staging/commit/push는 없다.

### 사용자 수동 관찰 추가 — 초안·선택창

이후 사용자 보고: Codex 내장 브라우저의 A 편집 제목이 `SPIKE DRAFT A`인지 묻자 “ㅇㅇ”로 확인했고, 대표 이미지는 초록색·본문 이미지는 보라색이라고 보고했다. 대표/본문 두 이미지 선택창 각각에서 다른 색상 이미지 목록과 작은 썸네일이 보이는지 확인 요청 후 “보여”라고 답했다. 이 두 선택창의 목록·썸네일 표시 성공은 **사용자 보고**로 기록한다. 직접 화면/스크린샷을 관찰한 PASS 또는 SP-01 전체 PASS로 확대하지 않는다.

저장소의 `seed_demo.py`에는 공개 대표 red·본문 blue, 초안 대표 green·본문 purple이 정의되어 있다. `Post.serve_preview`는 `serialize_post(..., preview=True)`로 제목·대표·본문을 상세 템플릿에 전달한다. 따라서 기존 초안 Preview의 제목·초록/보라 이미지와 독립 비로그인 창 공개 HTML의 `SPIKE PUBLIC A`·빨강/파랑 이미지를 비교하는 다음 순서가 소스 기준에 맞는다. 소스 확인은 현재 브라우저 렌더링 결과가 아니며 seed나 서버 요청을 실행하지 않았다.

다음 요청은 기존 초안 Preview를 열어 제목·대표/본문 이미지 렌더링을 확인한 뒤, 별도 Windows 브라우저의 InPrivate/시크릿 창(관리자 로그인하지 않음)에서 `http://127.0.0.1:8765/spike/posts/1/`의 공개 제목·이미지 색상을 확인하는 것이다. 같은 내장 브라우저의 새 탭만으로 비로그인 세션이라고 판단하지 않는다. 이는 변경 전 시각적 기준 확인이며 새 초안 저장 후 공개본 불변 검증은 아직 아니다.

현재 서식 편집·새 자산 업로드/선택·초안 저장·Preview·방문자 HTML/JSON 비교·무권한 파일 접근·별도 JS 렌더링은 NOT_RUN이다. SP-01은 위 사용자 보고 부분만 추가되었고, SP-01·05·11의 Codex 직접 브라우저 검증은 계속 BLOCKED다. 이번 변경은 이 절과 tasks/current.md뿐이다. 사용자 서버 종료, 계정/DB/미디어 변경, Publish/Unpublish 및 Git staging/commit/push는 수행하지 않았다.

### 최신 사용자 보고 — 기존 Preview·방문자 공개본

사용자의 명시적 보고: “미리보기에서 초록대표, 보라 본문보임. 시크릿창에서 SPIKE PUBLIC A 제목과 빨강 대표·파랑 본문 보임”. Codex 내장 브라우저의 기존 초안 Preview에서 두 이미지가 실제 표시됐고, 별도 비로그인 시크릿 창 공개 HTML에서 공개 제목과 두 이미지가 표시됐다는 **사용자 관찰**로 기록한다. Preview 제목은 이번 답변에 없으므로 확인됐다고 추정하지 않는다. 앞선 NOT_RUN 표현은 해당 관찰 이전의 이력이다.

| 범위 | 현재 확인 수준 |
|---|---|
| 로그인·A 편집 초안 제목/이미지·두 chooser 목록/썸네일 | 사용자 보고 확인, Codex 직접 화면 관찰 아님 |
| SP-05 일부: 기존 초안 Preview 대표/본문 이미지 | 사용자 보고 확인. Preview 제목·서식·링크 및 무권한 Preview 접근은 미확인, 전체 PASS 아님 |
| 기존 공개 HTML 제목·대표/본문 이미지 | 독립 시크릿 창의 사용자 보고 확인. 새 수정·Save draft 후 불변 비교가 아닌 기존 데모 기준 확인 |
| 서식 편집·새 자산 업로드/선택·초안 저장 후 재열기/Preview/공개본 비교 | NOT_RUN |
| 공개 JSON 전후 비교·공개 리비전 불변·무권한 파일 접근·별도 JS 클라이언트 | NOT_RUN(이번 수동 검증 기준) |

SP-01·05·11의 이전 서버 PASS 기록은 유지하며 자동화 도구는 계속 BLOCKED다. 수동 검증은 일부 진행 중이다. 새 화면 캡처·직접 관찰 증거는 없으며 사용자 보고를 SP 전체 PASS로 바꾸지 않는다.

다음은 제목에 `TEST-DRAFT-01`, 본문 끝에 `TEST-BODY-01`을 추가하고 Save draft 후 Posts에서 재열기·Preview를 확인한 뒤 시크릿 공개 HTML에 두 표식이 없는지 비교하는 최소 사용자 검사다. 이미지 업로드는 다음 단계다. 설치된 Wagtail 7.4.3의 `generic/form.html`은 하단 footer에 액션 메뉴를 배치하고, snippet `action_menu/save.html`은 DraftStateMixin을 쓰는 일반 편집에서 `Save draft`로 표시한다. 이 안내는 소스 확인이며 실제 화면 관찰이 아니다. 저장 전 공개 HTML/JSON 원문 기준을 보존하지 못한 경우 bytes/JSON 불변 검증까지 PASS로 주장하지 않는다.

이번 작업은 문서 두 파일만 갱신했고 사용자 서버·계정·DB·미디어를 자동 수정하지 않았다. Publish/Unpublish·테스트 재실행·Git staging/commit/push는 하지 않았다.

### 최신 사용자 보고 — 텍스트 수정 초안 저장 후 공개본 유지

직전 검사 전체에 사용자가 “ㅇㅇ 다 됨”이라고 명시적으로 답했다. 해당 검사는 A 제목 끝에 `TEST-DRAFT-01`, 본문 끝에 `TEST-BODY-01` 추가 → Save draft → A 재열기 및 Preview에서 두 표식 유지 → 시크릿 공개 페이지 새로고침 후 `SPIKE PUBLIC A`·빨강 대표·파랑 본문 유지 및 두 표식 없음이었다. 이 범위의 **사용자 수동 관찰 확인**으로 기록한다. 사용자가 기존 시험 초안의 제목·본문을 수정하고 저장한 상태이며 원복하지 않는다. 실제 최신 리비전 ID·DB 내용은 이번에 직접 조회하지 않았다.

SP-01 일부의 텍스트 편집·초안 저장·재열기, SP-05 일부의 수정 표식 Preview 표시, SP-03 관련 공개 HTML의 시각적 유지가 사용자 보고로 확인됐다. Codex 직접 실행/화면 관찰이나 SP 전체 PASS는 아니다. HTML bytes·JSON·live_revision 불변을 확인한 것으로 확대하지 않는다. 위 표의 해당 NOT_RUN은 이전 시점 기록이다. 자동화 도구 BLOCKED와 사용자 수동 일부 확인 상태는 유지한다.

다음은 기존 합성 PNG를 새 자산으로 업로드·선택하고 Save draft 후 재열기/Preview 및 시크릿 공개본을 비교하는 단계다. 시각적으로 구분하려면 새 대표에 `public-body.png`(파랑), 새 본문에 `draft-cover.png`(초록)를 각각 새 자산으로 업로드할 수 있다. 파일명에 public이 있어도 새 자산의 공개 여부는 새 ID의 공개 참조에 따라 별도 판정하며, 실제 무권한 접근은 후속 검사다. 기존 원본 덮어쓰기·개인 사진·Publish/Unpublish는 사용하지 않는다.

현재 `wslpath -w`가 반환한 fixture 경로는 `\\wsl.localhost\Ubuntu\home\shlee\Workspace\ai\01.codex\y3gym\experiments\cms-spike\.runtime\fixtures`이며 파일 4개 존재를 확인했다. Windows 파일 선택창에서의 접근 성공은 아직 사용자 확인 전이다. 경로를 파일 선택창 주소 표시줄에 붙여 넣어 파일을 고르게 안내하며, 접근 오류면 그대로 보고받고 환경 설정을 변경하지 않는다.

아직 미검증: 새 이미지 업로드/선택·그 이후 초안 저장 비교, Bold/Italic·링크 편집, 기존 파일 덮어쓰기 비활성 UI, 공개 JSON/리비전 비교, 무권한 미리보기·파일 접근, 별도 JS 렌더링. 이번 에이전트 작업은 보고서·작업 기록만 갱신했고 서버·계정·DB·미디어를 자동 수정하거나 테스트/도구 장애 재진단·Git 쓰기 작업을 하지 않았다.

## 14. 본문 이미지 사용성 피드백·제한 개선 — 2026-09-18

사용자 보고: **파랑 대표 변경 완료**, 본문 이미지 변경은 불편하여 중단. 대표 변경 이후 Save draft·재열기·Preview·공개본 유지까지 확인됐다고 해석하지 않는다. 새 대표 자산 ID/업로드 경로/저장 여부는 직접 조회하지 않았다. 사용자에게 미저장 편집이 있을 수 있으므로 서버 재시작·종료·브라우저 새로고침·DB/초안/미디어 자동 변경을 하지 않았다.

사용자가 아래 세 불편 모두에 해당한다고 답했다. 이는 후보 CMS의 사용성 문제 보고이며 사용자 오류로 분류하지 않는다.

| 불편 | 소스로 확인한 구조 / 미확인 요소 | 이번 대응과 한계 |
|---|---|---|
| 기존 본문 이미지 선택·교체를 찾기 어려움 | 설치 Draftail의 ImageBlock은 이미지 선택 후 Edit/Delete를 제공한다. ImageModalWorkflowSource는 기존 entity의 Edit를 해당 이미지의 `select_format/`로 연결한다. 이 모달에는 표시 형식·대체 설명·Insert image만 있고 다른 파일을 고르는 버튼이 없다. 따라서 기본 Edit를 파일 교체로 이해하기 어렵다. 실제 사용자 클릭 순서는 미관찰 | 본문 바로 위에 교체 안내를 상시 표시. 새 이미지 삽입을 먼저 확인하고 기존 배치만 제거하는 순서를 제공. 대표/본문 필드 제목·설명을 구분. 교체 전용 버튼은 추가하지 않음 |
| 이미지 선택·업로드 클릭 수가 많음 | 신규 삽입의 chooser(`select_format=true`)와 형식/대체 설명 확인은 별도 단계. 합성 파일 재업로드 시 중복 확인도 추가된다. 한 번에 파일 교체를 끝내는 지원 설정은 조사한 설치 소스에서 확인되지 않음 | 이미 올린 자산은 목록 선택으로 업로드·중복 확인을 생략할 수 있음을 화면에 안내. 새 자산 업로드 시험 자체는 계속 필요. 기본 단계 수를 줄였다고 주장하지 않음 |
| 편집 영역이 좁거나 클릭·입력이 잘 안 됨 | Preview는 별도 사이드패널이며 닫을 수 있다. 실제 창 크기·패널 열림·포커스·오류 상태를 관찰하지 못했으므로 좁음/입력 불량 원인은 미확정. Draftail 위젯은 일반 textarea가 아닌 HiddenInput과 JS 편집기이므로 rows 설정으로 높이를 해결할 수 없음 | 화면 내 접힌 보조 안내에 Preview 닫기/다시 열기 및 입력 이상 시 새로고침하지 않는 안내. 크기 강제 CSS·포커스 조작·패키지 수정 없음. 입력 불량 수정으로 판정하지 않음 |

### 구현과 공식 확장점

- `experiments/cms-spike/posts/models.py`: 공식 HelpPanel과 FieldPanel의 heading/help_text만 사용하여 본문 편집 안내와 대표/본문 구분을 추가했다. 모델 필드·본문 포맷·공개/권한 로직은 동일하다.
- `experiments/cms-spike/templates/posts/admin/body_image_help.html`: 본문 바로 위의 짧은 2단계 교체 안내, 상세 설명은 기본 HTML details로 접어 긴 안내가 편집을 밀어내는 양을 줄였다. 자체 JS·CSS·별도 프론트는 없다.
- 공식 [Panels](https://docs.wagtail.org/en/v7.4.3/reference/panels.html)의 HelpPanel/패널 도움말 확장점을 사용했다. [Draftail 확장 문서](https://docs.wagtail.org/en/v7.4.3/extending/extending_draftail.html)도 확인했으며 이미지 entity의 source/block 컴포넌트를 변경하는 것은 작은 패널 안내보다 연동 범위가 크다.

직접 클릭 수를 줄이는 후속 후보는 기존 이미지에 “다른 이미지 선택” 동작을 추가하는 것이다. 그러나 Draftail entity 선택 유지, chooser 취소 시 기존 참조 보존, alt/format 보존, 업로드/중복 흐름, 키보드·포커스·보호 이미지와 브라우저 재검증이 필요하다. 현재 직접 화면 검증이 막힌 상태에서 이를 패키지 내부 덮어쓰기나 미검증 JS로 구현하지 않았다. 기본 편집 흐름이 계속 수용 불가능하면 이 제한 확장과 CMS 후보 재평가의 비용을 비교할 사용자 선택이 남는다. 새 에디터·페이지 빌더·제품 구현을 자동 도입하지 않는다.

### 검증·적용 상태

기존 서버 회귀 중 패널/편집/공개 분리에 관련된 SP-01·03·05 세 테스트만 실행했다: **3 tests / 2.850s / OK**, system check 문제 0건. 임시 테스트 DB와 별도 새 테스트 미디어를 사용했으며 사용자 SQLite·업로드 자료는 자동 변경하지 않았다. `makemigrations --check --dry-run`: **No changes detected**. `git diff --check` 통과. 실행 요약은 새 Git 제외 `.runtime/editor-ux-*/verification.json`에 저장했다. 테스트는 폼·서버 계층이며 새 안내의 브라우저 표시/클릭 개선은 **NOT_RUN**이다.

README 명령의 `--noreload`로 실행 중인 서버에는 Python 패널 변경 적용을 위해 재시작이 필요하다. 이번에는 사용자 서버를 재시작/종료하지 않았다. 사용자에게 먼저 현재 변경을 Save draft로 보존하고 성공 여부를 알려 달라고 안내한다. 보존 확인 후 사용자가 자기 서버를 재시작하여 새 편집 화면을 열었을 때 본문 안내 표시와 이미지 교체 흐름을 재확인해야 한다. 현재 페이지를 바로 새로고침하도록 요청하지 않는다.

SP-01·05·11 전체 브라우저 PASS는 부여하지 않는다. 이전 사용자 텍스트 초안 검증 결과와 이번 대표 변경 보고·본문 검사 중단을 분리한다. 자동화 도구는 계속 BLOCKED. Git staging/commit/push 없음. P-01~04·A-01 및 ADR은 Proposed이고 전체 제품 구현·운영 배포로 확대하지 않았다.

## 15. 재개 점검 — 2026-10-04

적용 상위/하위 지침·README·작업 기록·실험 절차·기존 검증 기록을 재확인했다. 시작 HEAD `291eafd`, 작업 트리와 staged diff는 비어 있었다. WSL Ubuntu 26.04.1 LTS, 커널 `6.18.40.1-microsoft-standard-WSL2`; 기존 Linux venv Python 3.14.4 / Django 5.2.17 / Wagtail 7.4.3 / Pillow 12.3.0. `manage.py check` 문제 0건, `migrate --check` exit 0(미적용 마이그레이션 없음). 설치·마이그레이션 적용·기존 성공 테스트 반복은 하지 않았다.

SQLite를 `mode=ro`로 직접 조회한 현재 상태:

| 구분 | 제목·표식 | 이미지 참조 |
|---|---|---|
| A 공개 리비전 1 | `SPIKE PUBLIC A`, 두 TEST 표식 없음 | 대표 1(빨강), 본문 2(파랑) |
| A 최신 수정 초안 리비전 8 | `SPIKE DRAFT A TEST-DRAFT-01`, 본문 `TEST-BODY-01` 존재 | 대표 6 `TEST-UPLOAD-COVER-01`(파랑), 본문 4(보라)와 7 `TEST-UPLOAD-BODY-01`(빨강) |

색상은 해당 합성 이미지 파일 좌상단 픽셀로 재확인했다. 과거 안내의 초록 본문 예상과 달리 현재 새 본문 자산은 빨강이며 기존 보라 배치도 남아 있다. 정상 사용자 변경일 수 있으므로 원복·삭제·정정하지 않았다. 파랑 대표는 **이미 초안으로 저장됨**을 확인했고, 본문 새 업로드·삽입도 저장 상태로 존재한다. 따라서 동일 업로드나 표식 추가를 다시 요구하지 않는다. 저장된 데이터는 실제 브라우저 교체 사용성 통과와 다르다.

이미지 자산 1~7 모두 원본 파일 존재. `local-editor` 존재·active=true·staff=true·superuser=false·사용 가능한 암호 형식=true를 boolean으로만 확인했다. 암호/해시는 출력·기록하지 않았으며 실제 암호 로그인 재시험이나 암호 재설정은 하지 않았다.

시작 전 8765 리스너가 없고 루프백 bind도 가능한 것을 확인하여 README의 기존 명령으로 서버를 시작했다. **PID 401045**, 사용자 shlee, cwd는 현재 실험 경로, executable `/usr/bin/python3.14`, 리스너 **127.0.0.1:8765만** 확인. URL `http://127.0.0.1:8765/admin/`. stdin 없이 독립 세션으로 실행했고 사용자 브라우저 재개를 위해 실행 상태로 남긴다. 종료할 때 먼저 PID의 cwd/명령이 이 서버인지 확인한 후 `kill -INT 401045`로 이번 서버만 종료한다(PID 재사용 시 실행 금지). 기존 사용자 서버를 종료·재시작한 것이 아니다.

비인증 HTTP 가용성 확인: 로그인 페이지·공개 HTML·JSON 모두 200. 공개 JSON 제목 `SPIKE PUBLIC A`, 대표 display/1, 두 TEST 표식 없음. 공개 응답을 다음 비교 기준으로 저장했다. 로그인 페이지의 쿠키/폼/토큰은 저장하지 않았다. 이 요청은 서버 가용성과 공개 기준 수집이며 브라우저 검증 대체가 아니다.

갱신된 Computer Use 스킬 캐시 `26.924.22138`을 읽고 공식 초기화를 1회 시도했으나 기존과 같은 `sandboxCwd is not a local file URI: file:///home/shlee/Workspace/ai/01.codex/y3gym` 오류가 발생했다. 반복 reset·우회·설정 변경 없음. 자동화는 계속 BLOCKED이며 현재 브라우저 로그인·편집 화면은 직접 관찰하지 않았다.

증거: `experiments/cms-spike/.runtime/resume-20261004T093833518795Z/`의 `preflight.json`, `checks-and-tool.txt`, `server-process.json`, `server.log`, `http-status.json`, `public-before.html`, `public-before.json`(모두 Git 제외). 이전 증거는 보존했다.

현재 서버는 최신 패널 코드/안내 템플릿이 있는 checkout에서 새로 시작했다. 다만 인증된 실제 화면의 안내 표시·사용성은 아직 미확인이다. 다음 사용자 행동은 기존 계정으로 A를 열어 **“본문 이미지 바꾸기” 안내와 파랑 대표·보라/빨강 본문 두 이미지가 보이는지 확인**하는 한 단계다. 새 업로드·저장·Publish/Unpublish는 아직 요구하지 않는다. 이미 열린 미저장 탭이 있다면 그 탭은 새로고침하지 않는다.

§14의 세 불편은 안내/패널 이름 변경만 적용한 평가 상태로, 해결 판정하지 않는다. SP-01·05·11의 기존 서버 결과·과거 사용자 보고는 유지하고 이번 DB/HTTP 점검을 브라우저 PASS로 확대하지 않는다. 이번 변경은 보고서·작업 기록·README 안내 및 신규 Git 제외 증거뿐이며 Git staging/commit/push 없음. PostgreSQL·상용 Linux·전체 제품 기능·정책 최종 승인은 계속 미검증/미승인이다.

### 사용자 화면 확인 후 다음 검사 — 2026-10-04

사용자가 Post A 편집 URL 컨텍스트에서 “ㅇㅇ 이미지 확인완료”라고 보고했다. 직전 요청 대상인 파랑 대표·보라/빨강 본문 이미지의 **사용자 화면 확인**으로 기록하며 위 직접 DB 조회와 구분한다. 비밀번호 변경 실행/완료, 도움말 표시·숙지, 사용성 개선, 새로운 Save draft 성공까지 추정하지 않는다. 인증 정보·암호·계정 해시는 이번에 조회하지 않았다.

현재 저장된 초안에 본문 이미지4(보라)와7(빨강)이 함께 있고, 기존 HelpPanel도 새 이미지 삽입 확인 후 기존 배치만 제거하도록 안내한다. 따라서 다음 최소 검사는 본문 안의 보라 이미지 배치만 Delete → Save draft → Preview에서 파랑 대표·빨강 본문만 확인 → 독립 시크릿 공개 HTML에서 기존 `SPIKE PUBLIC A`·빨강 대표·파랑 본문 유지 확인이다. Images 메뉴의 자산 영구 삭제와 다르며 재업로드·Publish/Unpublish는 하지 않는다. 선택/삭제 메뉴를 찾기 어렵거나 예상과 다르면 반복 조작하지 않고 해당 본문 부분 화면을 관찰한 후 진행한다.

이 새 검사 결과는 아직 NOT_RUN이다. 이번 에이전트 작업은 이 보고서와 tasks/current.md 갱신 및 기존 소스/문서 확인뿐이며 서버·DB·미디어 자동 변경·Git staging/commit/push는 없다.


## 16. 이미지 교체 저장 후 검증 — 2026-10-04

### 사용자 수동 관찰과 직접 점검 구분

사용자는 저장 완료 후 진행을 요청했다. 편집 화면은 파랑 대표·빨강 본문, Preview도 파랑 대표·빨강 본문이며 시크릿 공개 화면은 빨강 대표·파랑 본문이라고 보고했다. **사용자 직접 관찰·보고 범위에서 이미지 교체/초안 저장/Preview 이미지 표시/독립 비로그인 공개 HTML 유지 PASS**다. 에이전트가 화면을 직접 보거나 캡처한 결과가 아니다. 편집·Preview는 기존 사용자 보고상 Codex 내장 브라우저(이번 별도 재질문/버전 확인 없음)이며, 시크릿 브라우저 제품·버전은 미확인이다. 이전 확인된 일반 운영자 `local-editor`(staff, 비최고관리자) 컨텍스트를 따르되 이번에는 인증정보·계정·세션을 조회하지 않았다. 암호 재설정 여부도 추정하지 않는다.

직접 읽기 전용 SQLite 조회 결과 A는 live=true, 공개 리비전 **1**, 최신 수정 초안 **10**이다. 공개본 제목 `SPIKE PUBLIC A`·대표1·본문2와 B의 공개 리비전3·공유 본문2는 유지된다. 최신 초안은 `SPIKE DRAFT A TEST-DRAFT-01`, 본문 `TEST-BODY-01`, 대표6(파랑)·본문7(빨강)만 참조한다. 본문4 배치는 제거됐지만 이미지 자산1~7과 기존 원본·변환본은 보존되어 있다. 신규 업로드를 반복하지 않았다.

### 비로그인 HTTP 계층 — PASS

인증 헤더·쿠키·세션 없는 urllib GET **36건**을 현재 루프백 서버에 실행했다. 브라우저 검증 대체가 아니다.

- 공개 HTML/JSON 각200. §15의 편집 전 응답과 **각각 바이트 단위 동일**, 제목/본문 HTML의 공통 표현 일치, 두 TEST 표식 없음.
- 전체 공개 Post의 공개 리비전 참조를 기준으로 이미지1·2 display200, PNG 디코딩 성공(대표 빨강/본문 파랑). 이미지3~7 display404. 같은 파일 내용의 공개 자산이 있어도 초안의 새 자산6·7은 공개되지 않음.
- DB에 이미 존재하는 원본7개와 변환본19개의 `/cms-files/...` 경로는 모두403. 새 변환본을 만들지 않음.
- 설치된 Wagtail 라우트에 해당하는 `/admin/snippets/posts/post/preview/1/` GET302, `/admin/login/?next=...`로 전환. 인증된 Preview 렌더링의 직접 재시험은 아님.
- HTTP 점검 전후 SQLite 파일 해시·선택한 Post/리비전/이미지/변환본 데이터·전체 미디어 파일 목록/해시 동일. 이 점검으로 DB·미디어 변경 없음. 사용자 저장으로 바뀐 초안10과 점검에 의한 변경을 구분함.

신규 증거: `experiments/cms-spike/.runtime/post-save-20261004T095154444368Z/`의 `before.json`, `after.json`, `results.json`, `public-after.html`, `public-after.json`. 비교 기준은 §15의 `resume-20261004T093833518795Z/public-before.*`. 모두 Git 제외이며 기존 증거를 덮어쓰지 않았다. 인증 페이지 내용·쿠키·비밀값·스크린샷은 저장하지 않았다.

| 항목 | 기존 서버 테스트 | 이번 직접 점검 | 실제 브라우저 범위 |
|---|---|---|---|
| SP-01 편집/초안 | 이전 PASS 기록 유지, 이번 재실행 없음 | 초안10 저장·참조 분리 확인 PASS | 사용자 보고: 이미지 교체·저장 PASS. 과거 chooser/업로드 보고 범위 유지. Bold/Italic/링크 편집과 저장 후 서식 재열기·파일 덮어쓰기 비활성 UI NOT_RUN. 에이전트 직접 관찰 BLOCKED |
| SP-05 권한 있는 초안 미리보기 | 이전 PASS 기록 유지 | 비로그인 Preview302 로그인 요구 PASS. 인증된 Preview 직접 재시험 없음 | 사용자 보고: 최신 초안 Preview 이미지 표시 PASS. 서식·링크 및 비로그인 Preview의 브라우저 접근 대조 NOT_RUN |
| SP-06 보호 파일 경로 검증 | 이전 PASS 기록 유지 | 공개1·2 200, 비공개3~7 404, 보호 원본7·변환본19 모두403 PASS | 동일 보호 URL의 관리자/방문자 브라우저 대조 NOT_RUN |
| SP-11 HTML/JSON | 이전 PASS 기록 유지 | 공개 HTML/JSON 바이트 불변·본문 일치 PASS | 사용자 시크릿 HTML 유지 PASS. 이번 JSON 브라우저 관찰 NOT_RUN, 별도 JS 클라이언트 렌더링 NOT_RUN |

전체 SP 항목을 일괄 PASS로 합산하지 않는다. 새 기능 결함을 발견해 수정한 것은 없고 테스트/코드 변경도 없다. §14의 세 사용성 불편에 대한 만족도는 미평가다.

### 남은 최소 수동 검사와 서버 상태

다음 한 묶음: A 본문의 시험용 단어에 Bold/Italic 및 `https://example.com/` 링크 적용 → Save draft → 목록에서 다시 열고 Preview에서 서식/링크 유지 확인 → 기존 이미지1 편집 화면에서 파일 교체 입력이 비활성인지 확인만 한다. Publish/Unpublish·자산 삭제·파일 교체·재업로드는 하지 않는다. 이미지 확인을 반복할 필요는 없다. 이후 동일 보호 이미지 URL의 관리자/시크릿 비교와 브라우저 JSON 확인은 별도 미검증 항목이며 자동 HTTP PASS로 대체하지 않는다.

이번 변경 파일은 검증 보고서와 tasks/current.md뿐이다(위 신규 Git 제외 증거 별도). staging/commit/push 없음. 현재 PID401045 서버는 사용자 후속 검사를 위해 **종료하지 않고 127.0.0.1:8765에서 유지**한다. DB·초안·자산·기존 로그 보존. PostgreSQL·상용 Linux 배포·전체 제품 기능·정책 최종 승인은 계속 미검증/미승인, P-01~04·A-01 및 두 ADR은 Proposed다.


## 17. 익숙한 글쓰기 UI 시안 — 2026-10-04

### 요청·근거·범위

사용자가 제시한 참고 이미지를 직접 열어 확인했다. 한 줄 상단 툴바와 넓은 본문 영역을 목표로 하되 폰트·색·밑줄·취소선·정렬·표 등 참고 이미지의 모든 버튼을 신규 기능 요구로 해석하지 않았다. 기존 Bold/Italic/H2/번호·글머리 목록/링크/이미지만 사용한다. 이번 승인 범위는 Post 편집 시안이며 CMS·정책 최종 채택이나 전체 제품 구현이 아니다.

[Wagtail 7.4.3 Draftail 확장 문서](https://docs.wagtail.org/en/stable-7.4.x/extending/extending_draftail.html) 및 [rich text widget 계약](https://docs.wagtail.org/en/stable-7.4.x/extending/rich_text_internals.html)을 참고하고 **설치된 7.4.3 소스**에서 실제 계약을 확인했다. `DraftailRichTextArea`의 media/template·ContentstateConverter, `w-draftail:init` 초기화, 옵션의 topToolbar 및 per-instance entityTypes 병합, ImageModalWorkflowSource/ModalWorkflowSource의 선택·완료, DraftUtils.updateBlockEntity, generic panel/preview template와 CSS 선택자를 읽었다. 설정 OPTIONS의 임의 값을 넣으면 적용된다고 가정하지 않았다. 해당 위젯은 features 외 OPTIONS를 버리므로 Post FieldPanel에 위젯 클래스를 지정하고 초기화 이벤트에서 해당 위젯의 옵션만 보완한다. 설치 패키지·전역 feature registry·다른 모델 에디터는 수정하지 않는다.

### 구현한 시안

- **상단 고정 위치의 상시 툴바:** Draftail의 topToolbar 확장점에 한국어 실제 버튼을 모았다. Tab/Shift+Tab·Enter/Space를 위한 일반 button, 눌림 상태 aria-pressed, 서식 그룹 이름을 제공한다. 마우스 선택을 잃지 않도록 mousedown 기본 포커스 이동을 막고 click에서 Draftail 콜백을 호출한다. 키보드 실사용 검증은 별도다.
- **넓은 입력 영역:** Post 본문 패널의 840px 제한을 해당 클래스 아래에서 해제하고, 본문 최소24rem(작은 창16rem), 내부 스크롤 최대65vh(작은 창60vh)로 구성했다. 툴바는 스크롤 본문 바깥에 남고 작은 창에서는 버튼이 줄바꿈한다. Wagtail 색상 변수를 사용하며 포커스 외곽선을 표시한다. 화면 전체 스크롤에서도 항상 화면 위에 붙는 sticky 헤더는 아니다.
- **실제 이미지 교체 동작:** 본문 이미지마다 `이미지 선택·교체`와 `본문에서 제거` 버튼을 항상 표시한다. 교체는 보호된 기존 chooser와 형식/alt 단계를 재사용하고 새 자산 또는 기존 자산을 골라 해당 embed의 데이터만 바꾼다. 현재 커서의 블록이 아닌 entityKey에 대응하는 이미지 블록을 찾아 DraftUtils.updateBlockEntity를 호출한다. 취소·삽입은 기본 source 흐름을 유지하고 본문 배치 제거는 기본 onRemoveEntity 콜백이다. 자산 삭제·파일 덮어쓰기 기능이 아니다.
- **대표 이미지 구분:** 본문 아래 기존 별도 대표 필드를 유지하고 설명을 보존했다. 장문의 상시 도움말은 접을 수 있는 설명으로 줄였다.
- **새 탭 미리보기:** 본문 위 버튼이 Wagtail의 기존 `newTab` 링크를 클릭해 공식 preview controller의 미저장 폼 POST 및 새 탭 동작을 이용한다. 인증 우회·별도 미리보기 저장소·직접 공개 GET 대체 없음. 기존 사이드 패널도 남겨 두며 자동으로 닫거나 사용자 설정을 바꾸지 않는다. 팝업 차단/실제 새 탭 동작은 미검증이다.

`RichTextField` 정의·DB 마이그레이션·저장 포맷·이미지 ID 표현·Sanitizer·공개 DTO·권한은 그대로다. 새 에디터 라이브러리/패키지·폰트/색/표 기능은 도입하지 않았다. 기존 콘텐츠를 변환하지 않았다. 위젯 지정·정적 파일·도움말을 이전 형태로 되돌리는 것만으로 롤백 가능하며 데이터 역마이그레이션은 필요 없다.

### 실제 검증·수정 과정

초기 실행은 모델 import 중 위젯 인스턴스를 생성해 feature registry가 너무 일찍 로딩되는 오류로 중단됐다. FieldPanel에 **위젯 클래스**를 전달해 폼 생성 시점에 인스턴스화하도록 수정했다. 이어서 Django widget renderer가 프로젝트 templates 디렉터리를 탐색하지 않아 발생한 TemplateDoesNotExist를 앱 내부 `posts/templates/posts/widgets/`로 옮겨 수정했다. 이후 최종 전체 서버 테스트 **17개 PASS (8.182s)**, Django check 문제0건. 기존16개에 위젯 로딩 순서/폼 마크업·서식/목록/링크/이미지ID 왕복 검증1개를 추가했다. 테스트는 기존 임시 메모리 DB와 별도 test-media 경로를 사용했으며 기존 사용자 인증을 이용하지 않았다.

Node 내장 test runner 단위 테스트 **3개 PASS**: Post에만 옵션 적용·실제 버튼 콜백, 기존 preview 동작 위임, 커서 위치와 다른 이미지 entity의 교체 대상 선택. 브라우저/React DOM을 실행하는 시험이 아니라 명시적 stub 기반 연결·분기 테스트다. `node --check` 통과, `makemigrations --check --dry-run`은 No changes detected. CSS 렌더링·IME 입력·실제 이미지 chooser 취소/교체·키보드/스크린리더·작은 창·Preview 새 탭·사용성 만족도는 **NOT_RUN**이다. 공식 Computer Use는 기존 URI 장애로 BLOCKED이며 반복 호출하지 않았다. 시안을 일반 글쓰기 에디터의 사용성 검증 완료로 표현하지 않는다.

증거(Git 제외): `.runtime/composer-tests-20261004-1.log`, `.runtime/composer-js-tests-20261004-1.log`, `.runtime/composer-integrity-20261004-1.json`. 초기 오류는 위 원인/수정 기록이며 실패 실행 원문 로그를 별도 파일로 저장하지는 않았다. private-media 전체 목록/해시는 §16 기준과 동일하다. 다만 SQLite 해시는 다르며 읽기 전용 조회에서 A 공개 리비전1·최신 초안11, B 공개/최신3, 이미지7개·변환본19개·리비전11개를 확인했다. UI 작업 시작 시 DB 해시를 따로 수집하지 않아 변경 시점·원인은 미확정이다. 이번 작업은 실험 DB에 저장/계정/마이그레이션 요청을 실행하지 않았지만 DB 전체 불변을 주장하지 않는다. 사용자 편집일 가능성도 추정으로만 남기며 내용을 원복하지 않는다. 테스트가 만든 별도 test-media는 보존한다.

### 적용 대기·인계

PID401045의 127.0.0.1:8765 서버를 재시작·종료하지 않았다. `--noreload`이므로 현재 모델/위젯 코드는 새 프로세스 시작 전 적용되지 않는다. 사용자 미저장 편집을 먼저 보존했는지 확인하고 별도 조율 후 해당 서버만 재시작해야 한다. 지금 브라우저 새로고침을 요청하거나 실행하지 않았다. 서버 적용 후 최소 검사는 상시 툴바/넓은 입력·키보드와 한글 입력, 두 이미지 중 커서와 다른 이미지 교체 및 취소, 초안 저장/재열기, 새 탭 Preview, 공개본 유지다. CSS/DOM 의존부는 Wagtail 업그레이드 시 재확인해야 한다.

변경은 실험의 models.py/widgets.py/tests.py, composer.js/css, 앱 위젯 템플릿, 본문 도움말, JS 단위 테스트 및 README와 이 보고서/tasks/current.md 기록이다. Git staging/commit/push 없음. PostgreSQL·상용 Linux 배포·전체 제품 기능·정책 최종 승인은 미검증/미승인이며 Proposed 상태를 유지한다.


## 18. 검토에서 재현된 이미지 결함 수정 — 2026-10-04

Git 검토 담당자가 초기 UI의 실질 결함2건을 재현해 staging/commit/push를 중단했다. §17의 초기 테스트3개는 실제 entity 변경을 stub으로 대체하여 이를 검출하지 못했다. §17의 `entityKey로 블록 find + updateBlockEntity` 구현 설명은 아래 수정으로 대체한다.

| 초기 FAIL | 원인 | 최소 수정 |
|---|---|---|
| 링크 안의 커서에서 이미지 넣기 후 완료·모달 닫기 미호출 | Draftail onRequestSource는 요청 종류와 별개로 커서의 LINK entity도 source props로 전달한다. 기존 코드가 이를 이미지 교체로 판단하고 atomic 블록을 못 찾으면 반환함 | 명시적 이미지 교체 버튼의 요청이 없는 경우 항상 새 IMMUTABLE IMAGE entity를 만들고 실제 AtomicBlockUtils.insertAtomicBlock으로 삽입. LINK entity는 수정하지 않음 |
| 공유 entityKey의 두 이미지 배치가 함께 바뀜 | updateBlockEntity는 공유 entity 데이터를 merge하며 entityKey만으로는 첫/두 번째 배치를 구분하지 못함 | 버튼의 실제 block.getKey()/blockProps.entityKey 쌍을 위젯별 closure에 전달. source 생성 때 한 번 소비하고 해당 블록 검증 후 새 독립 IMAGE entity를 Modifier.applyEntity로 그 배치에만 연결. 다른 배치의 entity는 그대로 보존 |

설치된 Draftail의 blockRenderer는 React 블록에 `block` 및 `blockProps.entityKey/onEditEntity/onRemoveEntity`를 제공하지만 renderSource props에는 blockKey가 없다. 따라서 selection을 먼저 강제로 바꾸는 방식이나 entityKey 첫 검색 대신 **명시적인 배치 요청을 위젯별로 전달**한다. source 생성 후 요청을 비워 취소 뒤 신규 삽입에 낡은 대상이 남지 않는다. 대상이 현재 atomic IMAGE 배치와 일치하지 않으면 다른 블록을 추정해 수정하지 않고 chooser를 닫아 기존 상태로 완료한다. 기존 모달·형식/alt 선택·보호 chooser URL·취소 lifecycle은 상속한다. 삽입/교체의 상태 전환만 구분하며 권한/저장 converter/Sanitizer/DTO/의존성은 바꾸지 않는다.

교체는 새 entity 데이터로 선택 결과의 ID/src/alt/format을 적용하고, 원래 selectionBefore/After와 EditorState selection을 유지해 다른 본문·선택·undo를 보호한다. 실제 DOM 포커스가 동일하게 돌아오는지는 브라우저 확인이 필요하다.

### 회귀 증거

`node --test tests/composer.test.cjs tests/composer-library.test.cjs`: **8개 PASS**.

- 모의 연결 검사2개: Post 전용 초기화/툴바·이미지 콜백 연결, 기존 새 탭 Preview 호출.
- 실제 설치 라이브러리 상태 전환6개: LINK 커서에서 IMAGE 삽입·완료/close, 공유 entity 첫 번째 배치만 교체, 두 번째 배치만 교체, 삽입/첫 배치/두 번째 배치 chooser 취소 불변 및 이후 삽입 독립성. 다른 이미지 ID/alt/format, 본문, 링크, 선택, 원래 상태 및 undo를 검증한다.

새 테스트 로더는 설치된 vendor.js/draftail.js를 **Node VM 메모리 안에서만** 읽어 실제 Draft.js 모듈과 Wagtail의 source/filter/cancel 및 onRequestSource/getSelectionEntity 메서드를 사용한다. 설치 파일·브라우저 프로토콜을 변경하거나 도구 장애를 우회하지 않는다. webpack bootstrap/메서드 추출 문자열은 설치 버전 의존 테스트 어댑터이며 바뀌면 실패하여 검토를 요구한다. 실제 DOM/ModalWorkflow UI는 띄우지 않고 chooser 결과·close 콜백 경계를 주입하므로 브라우저 통합 테스트는 아니다.

관련 서버5개 **PASS (2.807s)**: 위젯/저장 왕복, SP-01 관리자/chooser, SP-03 공개본 보존, SP-05 인증 Preview, SP-06 보호 파일. 기존 메모리 테스트 DB/별도 test-media 사용. 초기17개 전체 PASS는 §17 기록이며 이번에 전체 재실행한 것은 아니다. JS syntax 및 git diff --check 통과.

증거는 `experiments/cms-spike/.runtime/composer-fix-20261004T100822523110Z/`의 test-1.log(JS), test-2.log(서버), before.json/after.json/results.json에 신규 보존했다. 테스트 전후 private-media 목록/해시는 동일하지만 **실험 SQLite 파일 해시는 달라 전체 불변 검사는 통과하지 못했다**. 후속 읽기 전용 Post 조회는 A 공개1/최신11, B 공개3/최신3으로 이전과 같다. 원인은 미확정이며 사용자 서버가 계속 실행 중인 조건이다. 계정·세션·비밀값은 조사하지 않았고 실험 DB 저장·마이그레이션·원복 요청은 실행하지 않았다. 데이터 무결성 전체 PASS로 확대하지 않는다.

이번 후속 수정 파일: composer.js, 기존 composer.test.cjs, 신규 composer-library.test.cjs, README 및 검증보고서/tasks/current.md 기록. 기존 미커밋 시안 전체는 보존. 서버 PID401045의 127.0.0.1:8765 리스너를 확인했으며 서버·브라우저 재시작/종료/새로고침 없음, Git 쓰기 없음. 재검토 후 사용자 편집 보존·서버 적용을 별도로 조율한다. 실제 브라우저의 링크 커서 삽입·공유 이미지 배치별 교체·취소·포커스·한글 입력·미리보기는 여전히 NOT_RUN, 공식 도구는 BLOCKED다.


## 19. 사용자 승인 후 새 편집기 서버 적용 — 2026-10-04

사용자가 저장 확인/재시작 안내에 “ㄱㄱ진행”으로 지시해 추가 확인 없이 적용했다. 시작 HEAD는 검토·push 완료 코드 `b6bfbdf`, 작업 트리는 깨끗했다. 기존 PID401045의 cwd가 현재 실험 경로이며 명령이 `.venv/bin/python manage.py runserver 127.0.0.1:8765 --noreload --insecure`인 것을 확인하고 그 프로세스에만 SIGINT를 보냈다. 종료를 확인한 뒤 같은 가상환경·기존 DB/미디어·동일 README 명령으로 새 서버를 시작했다. **새 PID417652**, cwd 동일, 리스너 **127.0.0.1:8765만** 확인. 사용자 새 UI 확인을 위해 실행 상태로 유지한다.

비인증 HTTP 가용성 점검: 로그인200, 공개 A HTML/JSON 각200, `/static/posts/composer.js`와 `composer.css` 각200 및 현재 checkout 파일과 바이트 동일. 인증 페이지 본문·쿠키·세션은 저장하지 않았다. 새 Python 프로세스의 최신 코드 로드와 정적 파일 제공 확인이며 로그인·실제 편집 화면·클릭 성공 증거가 아니다. 기존 관련 회귀 테스트는 반복하지 않았다. 계정 생성·migrate·seed·게시/철회·콘텐츠 저장·설정 변경 없음.

적용 직전/직후 읽기 전용 점검에서 Post 참조·전체 리비전 content 해시·이미지 목록·SQLite 파일 해시·private-media 파일 목록/해시 모두 동일. A 공개1/최신11, B 공개3/최신3 유지. 이는 이번 재시작 구간의 비교 결과이며 §18의 이전 해시 차이 원인을 해결했다는 뜻이 아니다.

증거(Git 제외): `experiments/cms-spike/.runtime/composer-apply-20261004T114740438915Z/`의 before.json, after.json, results.json, server-process.json, server.log. 기존 서버 로그/증거는 보존했다. 이번 문서 변경은 이 보고서와 tasks/current.md뿐이며 Git staging/commit/push 없음.

사용자 다음 동작: 기존 관리자 A 편집 화면을 새로고침해 상단 서식 버튼·넓은 본문·이미지 선택/교체·본문에서 제거·새 탭 미리보기를 확인한다. 실제 클릭·키보드/한글입력·공유 이미지 배치 교체·취소·새 탭 Preview는 미검증이며 도구 BLOCKED 유지. URL은 `http://127.0.0.1:8765/admin/`. 종료가 필요할 때는 PID417652의 cwd/명령을 다시 확인하고 **그 서버만** `kill -INT 417652`로 종료한다(PID 재사용 시 실행 금지). 전체 제품 구현·상용 배포·정책 승인으로 확대하지 않는다.


## 20. Paragraph 입력 중심 재작업·로컬 적용 — 2026-10-04

사용자가 영상의 “paragraph형식으로 글을쓰는게 사용자에게 익숙한 ui같음”이라고 특정하여 재작업했다. 설계자 제공 storyboard sheet7~9를 직접 확인했고, 특히 sheet9(6:45 부근)의 얇은 아이콘 툴바·본문 입력·우측 Preview를 참고했다. 영상 전체 재생/음성 확인은 아니다. 블록 메뉴/Starter 전체/StreamField 도입은 요구로 확장하지 않았다.

### 최소 구현

설치된 Wagtail7.4.3 번들의 `window.Draftail.Toolbar` export와 topToolbar 옵션 적용을 확인해 **기본 Toolbar를 본문 위에서 직접 사용**한다. 기본 icon/description/control 옵션은 그대로 두며, 기존 큰 한국어 버튼을 생성하던 커스텀 Toolbar/label 매핑은 제거했다. CSS는 Post에만 적용하고 본문 최소12rem(작은 창10rem)·기본 툴바 줄바꿈만 유지한다. 추가 외곽선·중첩 스크롤·본문 작성 바·새 탭 Preview 버튼/클릭 위임·장문의 HelpPanel을 제거했다. 사용하지 않는 도움말 템플릿도 제거했다. 기존 Wagtail 우측 Preview/기본 관리자 흐름은 그대로다.

이미지 아래에는 접힌 native details/summary **이미지 옵션**만 보이며 열면 `이미지 선택·교체`, `본문에서 제거`와 설명을 확인할 수 있다. 이미지 추가는 기본 툴바의 이미지 아이콘을 쓴다. §18의 정확한 blockKey 대상 지정·독립 entity 교체·LINK 커서 삽입·취소 처리 로직은 유지했다. 대표 이미지는 별도 필드와 한 줄 설명으로 구분한다.

RichTextField/필드명/ContentState 요청 형식/저장 HTML/리비전/이미지 권한/공개 DTO는 변경하지 않았다. StreamField·본문 분할·새 의존성·데이터 변환은 없다. 열린 구버전 폼도 같은 요청 형식을 사용할 수 있도록 하위호환을 유지했다.

### 검증

- **서버17개 PASS, 15.032s**, Django check 문제0건. 기존 이미지/공개/Preview 회귀 유지. 위젯 회귀에 이전 폼과 같은 payload를 새 서버 코드로 저장하여 초안 제목/이미지 유지·live revision/공개 JSON 불변을 확인하는 검사를 보강했다. 기존 테스트용 메모리 DB만 사용했으며 사용자 폼을 실제 저장한 것은 아니다.
- **JS7개 PASS**: 실제 설치 라이브러리 상태 전환6개(링크 안 삽입, 공유 이미지 첫/두 배치 독립 교체, 각 취소 및 이후 삽입) 유지. 모의 연결1개에서 native Toolbar 참조·원래 컨트롤 옵션·접힌 이미지 옵션·새 탭 클릭 위임 제거를 검사한다. 실제 라이브러리 로더도 설치된 Toolbar export를 대조한다. 이전 별도 새 탭 Preview 테스트는 해당 기능 제거와 함께 제거했다.
- `makemigrations --check --dry-run`: No changes detected. JS syntax/git diff --check 통과.
- 실제 DOM 렌더링·기본 툴바 키보드 접근·연속 한글/IME 입력·이미지 옵션 클릭/교체/취소·우측 Preview 사용성·작은 창은 **NOT_RUN**. 위 시험을 브라우저 PASS로 보고하지 않는다. 공식 Computer Use의 기존 URI 장애는 BLOCKED이며 반복 호출하지 않았다.

테스트 증거: `experiments/cms-spike/.runtime/paragraph-20261004T121851887348Z/`의 js.log, server.log(테스트 로그), migration.log, before-tests.json/after-tests.json. 테스트 구간 private-media 해시는 동일하지만 SQLite 전체 해시는 달랐으므로 DB 전체 불변 PASS로 처리하지 않는다. 계정/세션/비밀값을 조사하지 않았다.

### 적용·보존·다음 확인

기존 PID417652의 소유 uid/cwd/명령과 127.0.0.1:8765 리스너를 확인 후 해당 프로세스만 SIGINT로 종료했다. 첫 재시작 시도는 신규 서버 로그명이 기존 테스트 server.log와 겹쳐 `open('xb')`에서 중단됐다. 기존 로그를 덮어쓰지 않았으며 포트가 비어 있음을 확인하고 새 증거 폴더·다른 로그명으로 다시 시작했다. **새 PID422764**, 기존 venv·동일 README 명령 `runserver 127.0.0.1:8765 --noreload --insecure`, loopback만 리스닝. 사용자 확인을 위해 유지한다. 브라우저 탭 새로고침/이동·계정·콘텐츠 저장·migrate·seed·publish/unpublish·Git 쓰기 없음.

로그인 HTTP200은 가용성만 확인. composer JS/CSS 각200·checkout 바이트 동일. 공개 A HTML/JSON 각200이며 §16 저장 응답과 바이트 동일하다. 재시작 직전/후 Post 참조·모든 리비전 content 해시·이미지 목록·private-media 목록/해시는 동일하고 A 공개1/최신12, B 공개3/최신3이다. 이전 기록11보다 최신 초안이 늘어난 상태를 새 기준으로 존중했으며 원복하지 않았다. **전체 SQLite 해시는 다르므로 계정/세션 등 포함 DB 전체 불변은 미확정**이다. 해시 차이를 콘텐츠 손실로 단정하지 않으며 비밀값 조사로 확대하지 않는다.

적용 증거: `experiments/cms-spike/.runtime/paragraph-apply-20261004T122005146194Z/`의 server-process.json, development-server.log, after-apply.json, results.json, public-after.html/json. 비교용 before-apply.json은 위 테스트 증거 폴더에 보존했다. 기존 로그와 증거는 유지했다.

사용자는 입력 중인 내용이 있으면 먼저 Save draft한 뒤 A 편집 화면을 새로고침해 기본 아이콘 툴바·자연스러운 연속 입력·접힌 이미지 옵션·우측 Preview를 확인한다. 구버전 화면을 강제로 이동시키지 않았다. URL `http://127.0.0.1:8765/admin/`. 종료가 필요하면 PID422764의 cwd/명령/소유권 확인 후 그 프로세스만 `kill -INT 422764`로 종료한다. ADR/P-01~04/A-01은 Proposed, 전체 제품·운영 배포는 미승인이다.


### 사용자 적용 확인 — 2026-10-05 KST

사용자 최신 보고 “ok 적용됐다”를 **새 Paragraph UI가 화면에 표시됐다는 사용자 직접 보고**로만 기록한다. 에이전트 직접 관찰·화면 캡처는 없다. 사용성 만족, 한글/IME 입력, 서식, Save draft, 재열기, Preview, 이미지 선택·교체 전체 PASS로 확대하지 않는다.

위 적용 확인 후 설계자가 한글 두 줄과 일부 굵게 입력 → Save draft → 재열기/미리보기 유지 여부를 질문했다. 후속 답변은 아래에 별도로 기록하며 적용 확인 발언 자체의 의미를 확대하지 않는다. 기존 서버17개/JS7개는 10/04 실행 기록을 유지한다. 이번에는 문서 사실 구분과 diff만 점검했고 새 테스트·서버/계정/DB/미디어/브라우저/인증정보 점검 또는 변경·코드 수정·Git 쓰기는 하지 않았다. PID422764는 이전 실행 기록이며 오늘 재확인하지 않았다. P-01~04/A-01·두 ADR은 Proposed, 전체 제품 구현·운영 배포는 미승인이다.


### 사용자 입력·저장·미리보기 확인 — 2026-10-05 KST

질문: “새 본문에서 한글 두 줄을 쓰고 일부를 굵게 만든 뒤, Save draft → 다시 열기·미리보기에서도 그대로 유지되나요? 자동 브라우저 도구가 막혀 있어 이 실제 입력 확인만 부탁드립니다.” 사용자 선택 답변: **“입력·저장·미리보기 모두 정상”**.

이 질문·답변의 범위에서 새 Paragraph UI의 **한글 두 줄 입력·줄바꿈·일부 굵게·Save draft·재열기/Preview 유지 PASS(사용자 직접 보고)**로 기록한다. 에이전트 직접 화면 관찰·캡처는 없으며 전체 한글 IME 조합, Italic·링크, 접힌 이미지 옵션의 교체·취소, 좁은 창, 이번 공개 HTML/JSON 비교, 무권한 접근, 파일 덮어쓰기 비활성 UI 또는 전체 SP PASS로 확대하지 않는다.

사용자 저장으로 초안이 달라졌을 수 있으나 이번 DB 직접 조회는 없으므로 최신 리비전 번호·내용을 추정하지 않는다. §20의 리비전12는 10/04 당시 확인값으로 보존한다. 다음 최소 미확인 항목은 Italic/링크, 새 이미지 옵션의 교체·취소, 독립 방문자 공개본 유지다. 사용자에게 여기서 추가 질문을 보내지 않았다. 이번 작업은 문서만 수정했으며 서버17/JS7은 이전 기록이고 새 실행은 없다. 코드·서버·DB/미디어·브라우저·계정·인증정보·Git은 조작하지 않았다. 기존 Proposed/전체 제품 미승인 상태를 유지한다.


### 사용자 이미지 선택창 취소 확인 — 2026-10-05 KST

요청한 동작은 “이미지 옵션 → 이미지 선택·교체 창을 열었다가 취소했을 때 기존 이미지가 그대로 유지되는지 확인”이며, 사용자 답변은 **“유지ㅇㅋ”**다. 이 특정 선택창 열기·취소 후 **기존 이미지 유지 PASS(사용자 직접 보고)**로만 기록한다. 에이전트 직접 관찰·화면 캡처는 없다. 실제 이미지 교체, 모든 취소 경로, 공유 entity, Undo, 키보드·포커스, 보호 접근 또는 전체 SP PASS로 확대하지 않는다. 앞선 한글 두 줄·줄바꿈·굵게·초안 저장·재열기/Preview의 사용자 보고는 유지한다.

남은 최소 항목은 Italic/링크, 이미지 옵션에서 실제 이미지 교체, 독립 방문자 공개본 유지다. 전체 IME·좁은 창·무권한 접근·덮어쓰기 비활성 UI 등 기존 미검증도 유지한다. 위 이전 절의 취소 미확인 기록은 이번 보고 이전 시점이며, 이번에 확인한 특정 취소 경로에 한해서만 갱신한다. DB·리비전·서버 PID를 재조회하지 않았고 현재값을 추정하지 않는다. 문서 사실 구분·diff만 점검했으며 새 테스트·도구 장애 재시도·코드/서버/DB/미디어/브라우저/계정/인증정보 조회·변경·Git 쓰기는 없다. P-01~04/A-01·두 ADR Proposed 및 전체 제품 미승인을 유지한다.
