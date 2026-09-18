# ADR-0001 — 실행 환경과 배포 경계 v0.2 초안

상태: **Proposed**  
작성·근거 확인일: 2026-09-18  
근거: [검토 보완안 A-01](../review-resolution.md), [화면 명세](../screens.md), [데이터 모델](../data-model.md), [API 계약](../api-contract.md)  
변경 요약: A-01을 환경 분리·버전 선정·ENV 검증·배포/복구 경계로 구체화한 최초 ADR 초안이다. 제품 정책 승인·설치·실행 결과가 아니다.

## 1. 배경

현재 조건(2026-09-18 SPIKE-01 갱신)은 Windows 호스트 위 WSL Ubuntu 개발, 향후 별도 Linux 상용 서버 배포, 이후 고객 프론트 분리다. Windows는 편집·브라우저 접근 환경이며 개발 실행·가상환경·테스트는 WSL의 Linux Python·셸을 사용한다. 직접 확인한 환경은 Ubuntu 26.04.1 LTS / WSL2 커널 / Python 3.14.4 / ext4 저장소다. Windows 제품·버전, WSL 패키지 버전, 운영 Linux 배포판·버전·호스팅·실행 방식은 TBD다. `review-resolution.md`의 Windows 중심 설명은 원문 기록으로 보존한다.

단순 홍보 홈페이지의 고정 콘텐츠를 운영자가 관리한다. 가격·PT 연계·고객 로그인·지점별 게시판·별도 관리자 프론트·자유 페이지 빌더를 추가하지 않는다. 기존 화면·팝업·API 경로·페이지 크기·공개일 제안은 미확정이다. 이 ADR은 문서 작업이며 코드·환경 구축·배포를 승인하지 않는다.

## 2. 제안 — A-01 Proposed

### 2.1 애플리케이션과 환경 분리

Django + Wagtail + PostgreSQL, 초기 서버 템플릿, 환경별 하나의 애플리케이션과 DB를 권고한다. 관리 화면은 CMS 기능을 우선 활용한다. 공개 HTML과 향후 JSON API는 공통 공개 조회·출력 변환을 호출하며 내부 HTTP 재호출을 요구하지 않는다. 모델별 저장·공개와 미디어 보호는 [ADR-0002](0002-publication-and-media.md)의 Proposed 정책을 따른다.

| 영역 | WSL Ubuntu 개발 기준 | 별도 Linux 운영 권고 |
|---|---|---|
| 소스·의존성 | 승인 소스와 WSL Linux 전용 가상환경 | 같은 승인 소스, 대상 Linux에서 의존성 재설치 또는 Linux 이미지 빌드 |
| 실행 서버 | SPIKE-01은 루프백 개발 서버 | 운영용 WSGI/ASGI 서버; WSGI와 Gunicorn 우선 검토, 최종 선택 TBD |
| 웹 진입 | 명시된 로컬 개발 오리진, HTTP 예외 가능 | HTTPS 리버스 프록시, 운영 호스트·프록시 신뢰 경계 검증 |
| DB | 개발 전용 PostgreSQL, 테스트 데이터 | 운영 전용 PostgreSQL, 실제 콘텐츠; 개발과 지원 메이저 계열 일치 우선 |
| 설정·비밀값 | 개발 전용 설정·키·접근 정보 | DEBUG=False, 운영 전용 키·DB·미디어·쿠키/CSRF/로그 정책 |
| 미디어 | 개발 전용 저장소, 운영 자산과 분리 | 배포 경로 밖 영속 저장소, 비공개 원본·보호 전달·백업 |
| 검증 | WSL 실행·서버 테스트와 브라우저 편집 확인을 구분 | 별도 Linux 통합 검증, 배포 전 운영 설정 스모크 검증 |

Django는 Windows 개발 안내를 제공한다. Gunicorn은 Unix용 서버이므로 Windows 네이티브 실행 전제로 두지 않는다. 개발 서버를 운영 서버로 사용하지 않는다. [Django Windows](https://docs.djangoproject.com/en/5.2/howto/windows/), [Gunicorn 안내](https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/gunicorn/), [배포 점검](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)

### 2.2 OS 차이와 선택 수단

- 경로는 OS 독립적으로 처리하고 파일 경로와 URL 생성을 분리한다. Windows 드라이브 경로·개인 디렉터리를 앱에 고정하지 않는다. 파일명·import·템플릿·정적 자산의 대소문자를 Linux에서 검증한다.
- 주 실행 안내는 확인된 WSL Bash·Linux Python 기준이다. Windows 네이티브/PowerShell 안내는 교차 OS 대안으로 구분하고 실행 검증을 추정하지 않는다. 소스·문서는 UTF-8, Linux 셸 파일은 LF 기준으로 확인한다.
- `.venv`·Windows 바이너리·로컬 의존성 폴더를 Linux로 복사하지 않는다. 가상환경은 일반적으로 이식 가능한 배포물이 아니므로 OS별 재구성을 전제로 한다. [Python venv](https://docs.python.org/3/library/venv.html)
- 시간은 timezone-aware로 처리하고 API·내부 비교는 UTC, 입력·표시·오늘 숨김은 Asia/Seoul로 정한다. Windows를 포함한 시간대 데이터 확보를 위해 tzdata 의존성을 명시하는 안이다. 설치 여부는 미확인이다. [Python zoneinfo](https://docs.python.org/3/library/zoneinfo.html#data-sources)
- 운영 이미지는 절대 HTTPS URL, 로컬 개발은 명시된 HTTP 개발 오리진만 예외로 허용한다. HTTP 예외를 운영 설정에 상속하지 않는다. 이미지 접근 권한은 HTTPS 여부와 별도로 검증한다.
- WSL2 커널의 Ubuntu 실행은 이번에 직접 확인했다. Linux 컨테이너는 별도 선택 수단이며 이번 시험에서 사용하지 않는다. Docker Desktop은 Windows Server 지원 경로로 안내하지 않는다. OS·지원 상태·가상화·권한 확인 전 설치를 전제하지 않는다. [Docker Windows 요구사항](https://docs.docker.com/desktop/setup/install/windows-install/)
- Docker/WSL 설치·OS 기능 활성화·저장소 이동은 별도 작업이다. Linux 검증은 승인된 별도 Linux 환경도 가능하다. Kubernetes·Redis·메시지 큐 등 운영 서비스를 자동 추가하지 않는다.

### 2.3 버전 호환 조합 선정과 조사 근거

확인일은 **2026-09-18**이다. 아래는 공식 문서의 호환·지원 근거이며 설치 조사나 채택 결과가 아니다. `stable` 문서가 바뀔 수 있으므로 채택 시 버전별 문서를 다시 확인하고 정확한 패치·드라이버·이미지 의존성을 고정한다.

| 구성 | 확인한 공식 근거 | 선정 기준 / 미정 값 |
|---|---|---|
| Wagtail | 호환표의 7.4 LTS는 Django 5.2/6.0, Python 3.10~3.14 지원을 명시한다. 공식 일정은 7.4 LTS 지원 종료를 2027-11-02로 기재한다. [호환표](https://docs.wagtail.org/en/stable/releases/upgrading.html#compatible-django-python-versions), [공식 일정](https://github.com/wagtail/wagtail/wiki/Release-schedule) | LTS 후보로 검토 가능하나 채택 계열·패치 TBD. 운영 시작일과 유지보수 기간에 지원 여유가 있는지 재확인 |
| Django | 5.2 LTS의 연장 지원 종료는 2028년 4월이다. Python 호환표에는 3.10~3.14가 있으며 3.14 지원은 5.2.8부터다. [지원 상태](https://www.djangoproject.com/download/), [Python 호환표](https://docs.djangoproject.com/en/5.2/faq/install/#what-python-version-can-i-use-with-django) | Wagtail과 공통 지원 조합을 우선, 계열·정확한 패치 TBD |
| PostgreSQL·드라이버 | Django 5.2는 PostgreSQL 14 이상을 지원한다. PostgreSQL 공식 표에서 14의 지원 종료는 2026-11-12, 16은 2028-11-09, 17은 2029-11-08이다. [Django DB 지원](https://docs.djangoproject.com/en/5.2/ref/databases/#postgresql-notes), [PostgreSQL 지원 정책](https://www.postgresql.org/support/versioning/) | 최소 호환 버전만으로 선정하지 않는다. 호스팅·지원 기간·드라이버·백업 도구 호환 확인 후 메이저·패치 TBD |
| Python·이미지 처리 | 위 Django/Wagtail 교집합과 Windows/Linux 지원, 이미지 처리 라이브러리의 wheel·코덱·보안 지원을 함께 확인해야 함 | Python 정확한 버전·지원 종료일, Pillow/이미지 의존성 버전·OS 패키지 TBD; 이번에는 완전한 조합 검증을 하지 않음 |
| 서버·호스팅 | 운영용 서버와 보호 미디어 전달이 가능한 Linux 구성이 필요 | Linux 배포판·서버 버전·리버스 프록시·스토리지·호스팅 TBD |

공식 호환표에 나온 조합도 이 프로젝트의 이미지 보호·리비전·원자성을 검증한 조합은 아니다. 패키지 ‘최신’을 추정하거나 문서 버전을 설치 버전으로 기록하지 않는다. 승인된 구현 단계에서 재현 가능한 의존성 기록과 OS별 차이를 남긴다.

### 2.4 배포·백업·복구 경계

개발 DB·운영 DB는 별개다. 개발 DB로 운영 DB를 덮어쓰지 않는다. 최초 실제 콘텐츠 이관이 필요하면 자료를 선별하고 별도 검수·승인을 받는 작업으로 정의한다. 배포물·재생성 가능한 정적 자산과 업로드 미디어를 분리한다. 컨테이너를 택해도 DB·미디어를 임시 쓰기 계층에 보관하지 않는다.

배포 실행 순서는 별도 승인된 작업에서 사전 Linux 검증 → DB/미디어 복구점 확보 → 스키마 호환·변경 계획 확인 → 배포·명시적 마이그레이션 → 운영 설정/공개·관리·미디어 스모크 검증 → 유지 또는 복구 판단으로 구체화한다. 프로세스 시작마다 임의 스키마 변경을 수행하지 않는다. 코드 되돌리기만으로 DB 변경이 복구된다고 가정하지 않는다.

DB의 콘텐츠·리비전·자산 참조와 원본/변환본 복구 전략을 함께 설계한다. 백업 시점 정합성, 암호화·접근권한·보관 기간·복구 책임자·RPO/RTO는 TBD다. 복구 연습은 격리된 승인 환경에서 수행하고 운영 데이터를 개발 DB로 무단 복제하지 않는다. 복원 후 공개/비공개·이미지 접근 정책도 다시 확인한다.

향후 프론트 분리에서도 기존 CMS·DB·공개 조회를 유지하는 안이다. 별도 프론트 캐시·사전 렌더링 때문에 공개 변경이나 팝업 기간이 고정되지 않도록 API §7 조건을 검증한다.

## 3. 대안

| 대안 | 선택 시 영향 |
|---|---|
| Windows 네이티브 개발 + 별도 Linux 검증 | 과거 검토 대안; 현재 주 개발 기준이 아니며 이번 필수 검증에서 제외 |
| WSL2 또는 Linux 컨테이너 개발 | WSL Ubuntu는 현재 개발 기준으로 확인; 컨테이너 전환·설치는 별도 승인 필요 |
| 다른 CMS/프레임워크·DB | 기존 관리자와 공개·미디어 정책 충족 가능성을 비교해야 함; 현재 Django/Wagtail 채택이 확정이라는 뜻은 아님 |
| 처음부터 고객 프론트 분리 | API 소비 검증이 빠르지만 배포·인증·미리보기·미디어 연결 부담 증가; 현재 우선 권고는 초기 템플릿 |
| 개발 SQLite | 가벼운 실험에는 가능하나 본점 동시성 검증의 대체가 아님. SQLite에서 select_for_update는 효과가 없다. [Django SQLite 제한](https://docs.djangoproject.com/en/5.2/ref/databases/#queryset-select-for-update-not-supported) |

## 4. 장단점

기존 CMS 관리 화면과 공통 공개 조회를 재사용하면 고정 홍보 화면의 편집과 향후 프론트 분리를 함께 준비할 수 있다. 개발/운영 분리와 Linux 검증은 로컬 경로·DB·시간대 차이로 인한 배포 오류를 줄인다.

반면 PostgreSQL·CMS의 버전 호환과 패치 유지보수, 두 OS 검증 비용이 든다. 미디어 보호는 기본 설치만으로 완성되지 않아 ADR-0002의 제한된 연동 검증이 필요하다. 호스팅 선택에 따라 운영 서버·백업·미디어 전달 방식이 달라진다.

## 5. 검증 조건 — 모두 미실행

아래 ENV ID는 검토 보완안의 ID를 보존한다. 배포 계층은 OS·실행 설정·배포·복구 환경을 포함한다. WSL 개발과 별도 Linux 상용 검증을 구분한다. SPIKE-01의 제한된 실행 결과는 [검증 보고서](../verification/cms-spike.md)에 기록하며 아래 전체 ENV 통과로 확대하지 않는다.

| ID | 검증 계층 | 조건과 필요한 증거 | 연결 |
|---|---|---|---|
| ENV-01 | 배포·관리자 | 승인 소스·호환 의존성으로 WSL 개발과 별도 Linux 운영 환경 각각 실행, 관리자 진입·편집 확인; OS/버전·실행 결과 기록, 대상 간 venv 복사 없음 | A-01, §2.1~2.3 |
| ENV-02 | 배포·스토리지·API·브라우저 | Linux 경로·대소문자·정적 자산·이미지 변환 확인, Windows 바이너리/로컬 경로 유출 없음; 운영 HTTPS·명시된 로컬 HTTP 구분 | API-15·23, UX-17 |
| ENV-03 | 배포·API·브라우저 | 양 OS에서 같은 UTC 기준 시작 직전/시작/종료·KST 자정 판정, tzdata 가용성, 클라이언트 시간 오차·오늘 숨김 검증 | UX-12·15, API-11·14 |
| ENV-04 | DB·관리자·API | PostgreSQL에서 부모 저장 실패 롤백·동시 본점 변경·첫 공개 경쟁·마지막 지점 차단·관계 제약 확인, 커밋 전후 조회 혼합 방지 | RV-02·03·05~07, API-22 |
| ENV-05 | 배포·API·관리자·스토리지·브라우저 | 운영 설정 점검과 스모크: DEBUG=False, 호스트·CSRF·쿠키·비밀값 미노출, 운영 서버·HTTPS·보호 미디어 정상, HTTP 예외 차단 | API-23, RV-08~10 |
| ENV-06 | 배포·DB·스토리지·API | 재배포 때 DB/업로드 유지, 격리 복원 연습으로 콘텐츠·리비전·자산 참조·접근 제어 검증, 복구점·소요시간 기록 | P-03·04, RV-10·11 |

## 6. 미결정 사항

- 사용자 결정 대기: A-01의 스택·초기 템플릿 권고, P-01~04, 개발 실행 수단·호스팅과 운영 책임. 기존 화면·팝업·공개일·API 경로·페이지 크기는 계속 Proposed다.
- 기술 검증 대기: 정확한 Windows 제품/버전·도구 설치 상태, 지원되는 전체 버전 조합, Linux 환경과 PostgreSQL 동시성, 관리자 최소 연동·미디어 전달, 지도 제공자·좌표 저장 정책·쿼터, 배포·복원 절차와 RPO/RTO.
- 실행 단계: ADR 저장 자체는 구현 승인이 아니다. 별도 승인된 SPIKE-01은 격리 경로의 코드·로컬 의존성·SQLite·마이그레이션·테스트만 허용한다. 전체 구현·운영 환경 구축·배포는 미승인이며 저장소 이동은 수행하지 않는다.
