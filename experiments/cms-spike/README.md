# SPIKE-01 — Post·CMS 이미지 격리 실험

제품용 홈페이지가 아닌 Django/Wagtail 후보 시험이다. P-01의 Post 정책과 P-03·P-04는 실험 가설이며 P-01~04/A-01 및 두 ADR은 계속 Proposed다. 실제 결과·미검증 범위는 [검증 보고서](../../docs/verification/cms-spike.md)에 있다.

2026-09-18 WSL Ubuntu 26.04.1 / Linux Python 3.14.4에서 실행했다. Django 5.2.17, Wagtail 7.4.3, Pillow 12.3.0을 격리 설치했다. SQLite는 CMS 동작 시험용이며 PostgreSQL·운영 배포 검증이 아니다. Windows 네이티브 Python이나 PowerShell용 가상환경을 사용하지 않는다.

## WSL 실행

현재 확인한 저장소에서:

```bash
cd /home/shlee/Workspace/ai/01.codex/y3gym/experiments/cms-spike
```

다른 위치에서는 실제 Git 루트 아래 `experiments/cms-spike`로 이동한다. 기존 `.venv`·DB·미디어를 삭제하거나 초기화하지 않는다. 아래 가상환경 생성은 `.venv`가 없는 최초 준비 때만 실행한다. 이 환경의 시스템 Python에는 ensurepip가 없었고, 기존 Linux uv 0.12.16으로 생성했다. 시스템 설치나 Python 다운로드는 하지 않았다.

```bash
uv venv --no-config --no-python-downloads --python /usr/bin/python3 .venv
uv --no-config --cache-dir .cache pip install --python .venv/bin/python --no-python-downloads --require-hashes -r requirements.lock
.venv/bin/python manage.py check
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py test posts --noinput -v 2
```

위 설치·check·마이그레이션·테스트는 실제 실행했다. 의존성 입력은 `requirements.in`, 전이 의존성을 포함한 35개 버전·해시 잠금은 `requirements.lock`이다. 잠금 생성에 사용한 명령은 다음이며 일반 재현 때 다시 풀 필요는 없다.

```bash
uv --no-config --cache-dir .cache pip compile --python .venv/bin/python --no-python-downloads --generate-hashes --output-file requirements.lock requirements.in
uv --no-config --cache-dir .cache pip check --python .venv/bin/python
```

테스트는 임시 메모리 SQLite DB와 `.runtime/test-media-*`를 사용한다. 현재 `.runtime/spike.sqlite3`와 데모 자료를 초기화하지 않는다. 테스트 미디어는 이번 작업에서 자동 삭제하지 않았으므로 재실행 때 용량이 늘어난다. 로그를 저장하려면 기존 로그를 덮어쓰지 않는 새 파일명을 사용한다.

## 관리자 확인 절차 — 실제 브라우저 검증은 NOT_RUN

최초 시험에서는 실제 클릭·서식 입력·선택창·미리보기 표시를 확인하지 못했다. 2026-09-18 후속 작업에서는 Computer Use 도구가 제공됐으나 공식 `node_repl` 초기화가 `sandboxCwd is not a local file URI: file:///home/shlee/Workspace/ai/01.codex/y3gym`로 실패하여 **BLOCKED**다. 서버 테스트는 브라우저 사용성을 대체하지 않는다. 상세 증거는 검증 보고서 §10에 있다.

이번 후속 초안 검증에서는 아래 6~7의 Publish/Unpublish를 수행하지 않는다. 도구 복구 후 계정 생성의 숨김 암호 입력 및 직접 로그인만 사용자가 수행한다. 편집 전에 A의 공개 HTML/JSON·live_revision·이미지 참조를 새 증거 디렉터리에 보존하고, 4~5에서 시험용 수정 표시·Bold/Italic·링크·두 이미지 선택창·새 자산 업로드·Save draft·재열기·Preview를 검증한다. 별도 비로그인 세션에서 공개본 유지 및 초안 새 이미지 접근 거부를 비교한다. HTML/JSON 뷰어 확인을 별도 JS 클라이언트 렌더링 PASS로 기록하지 않는다. 증거는 `.runtime/browser-followup-<새 시각>/`에 저장하며 비밀번호·세션·비밀값은 캡처하지 않는다.

1. 다음 데모 명령은 실제 실행했다. 최초 실행은 명확한 테스트 PNG 4개와 게시글 A·B를 만든다. 재실행은 기존 manifest·자료를 보존한다. 현재 A는 공개본과 별도 수정 초안이 있고, B는 A의 기존 본문 이미지를 공유한다.

   ```bash
   .venv/bin/python manage.py seed_demo
   ```

2. 일반 운영자 계정은 아래 명령으로 직접 만든다. 암호는 숨김 입력이며 명령줄·문서·로그에 넣지 않는다. 기존 계정이면 변경 없이 중단한다. 이 대화에서는 로그인 가능한 계정을 생성하지 않았다. 명령의 대화형 입력은 미실행이다.

   ```bash
   .venv/bin/python manage.py create_spike_editor local-editor
   ```

3. WSL에서 루프백 서버를 시작하고 브라우저에서 `http://127.0.0.1:8765/admin/`에 접속한다. Windows 브라우저에서 WSL 루프백으로 접근 가능한지는 이 작업에서 확인하지 않았다. 접근 실패 시 바인딩·방화벽을 확대하지 않는다.

   ```bash
   .venv/bin/python manage.py runserver 127.0.0.1:8765 --noreload --insecure
   ```

   `DEBUG=False`에서 CMS 정적 자산만 개발 서버로 제공하기 위한 `--insecure`다. 미디어 URL은 정적 서빙하지 않는다. 이 명령 형태는 자동 HTTP 스모크에서 빈 루프백 포트로 실행했다. 운영 서버 설정으로 사용하지 않는다.

4. Snippets → Posts에서 A를 연다. 최신 초안 제목·본문과 다른 색상 이미지를 확인한다. Bold/Italic·링크를 편집하고 대표 이미지와 본문 이미지 선택창을 각각 연다. 새 업로드에는 `.runtime/fixtures/*.png` 테스트 자료를 사용한다. 이미지 편집 화면에서 기존 파일 교체가 비활성인지 확인한다.
5. Save draft 후 별도 방문자 세션에서 `/spike/posts/1/`, `/spike/posts/1/json/`을 확인한다. 현재 데모 A의 ID는 1, B는 2이며 `seed_demo` 출력으로 재확인한다. 공개본은 `SPIKE PUBLIC A`, 미리보기는 최신 초안이어야 한다. Preview에서 새 이미지가 실제 표시되는지 확인한다.
6. Publish 후 새 공개 내용과 이미지를 확인한다. 이미지 URL을 방문자 세션에 붙여 넣어 공개/미공개 차이를 확인한다. 새 자산 선택으로 교체하며 기존 파일 덮어쓰기를 사용하지 않는다.
7. 공유 이미지 실험에서는 A·B가 같은 이미지를 참조하는 상태를 확인한 후 A만 Unpublish한다. B가 남으면 표시 이미지가 열리고, B도 Unpublish하면 같은 URL의 새로운 방문자 요청은 404여야 한다. 과거 다운로드나 이미 열린 화면을 회수한다는 의미는 아니다.
8. 일반 운영자로 이미지 영구 삭제 직접 경로에 접근하면 403이어야 한다. 기본 이미지 편집의 삭제 버튼·목록의 일괄 작업은 일반 운영자에게 숨겼다. 다중 업로드 직후의 CMS 기본 삭제/중복 정리 UI까지 개조하지 않았으므로 해당 버튼이 남을 수 있고 요청은 차단된다.
9. 종료할 때 이 터미널에서 시작한 서버만 Ctrl+C로 종료한다.

## 자동 HTTP 스모크

이번 수동 브라우저 후속 검증에는 아래 스모크를 실행하지 않는다. 공개·철회 검증 및 최초 데모 기대값과 혼동하지 않도록 아래의 별도 수동 절차를 사용한다.

데모 최초 상태에서 실행한다. 데모를 수동 편집한 뒤에는 기대 제목이 달라 실패할 수 있으며 DB를 자동 원복하지 않는다.

```bash
.venv/bin/python smoke_http.py
```

스크립트는 빈 `127.0.0.1` 포트에서 자기 개발 서버만 시작해 관리자 로그인 페이지·정적 CSS·공개 HTML/JSON·표시 이미지·미공개/우회 경로를 요청하고, finally에서 해당 PID만 종료한다. 결과는 `.runtime/http-smoke-*.json`, 서버 로그는 `.runtime/http-server.log`에 남는다. 실제 브라우저 편집 검증은 아니다.

## 구현 경계

- 기본 CMS 기능: 등록·수정·목록·Draftail·이미지 업로드/선택·리비전·공개/비공개·미리보기 요청 흐름.
- 설정·등록: Post 하나, 고정 필드 패널, PreviewableMixin, 로컬 SQLite, 비공개 FileSystemStorage. CMS 내부 계정·페이지 테이블은 제품 기능이 아니다.
- 맞춤 코드: 공개 리비전 선택·HTML/JSON 공통 변환, 본문/대표 이미지 참조 검사, 인증·컬렉션 권한을 확인하는 파일 전달, 공개 사용처 재판정, 폼의 덮어쓰기·잘못된 참조 차단, 삭제 경로 차단·제한된 기본 UI 조정, no-store.
- 링크: 외부 HTTP(S)·mailto·tel·앵커 및 실험 Post 경로만 출력한다. CMS page/document 링크는 공개 라우트가 없어 텍스트로 바꾼다. 실제 사이트 내부 링크 매핑은 미구현이다.
- 미구현: 지점·트레이너·팝업·지도·고객 계정·별도 프론트·페이지 빌더·예약 공개·다단계 승인·운영 웹 서버·CDN·외부 저장소·복구.

원본·변환본은 `.runtime/private-media`에 있다. 공개 전달 경로는 정해진 PNG 표시본만 생성하며 원본 다운로드 경로가 아니다. CMS 파일 URL은 공개 여부와 무관하게 자산 권한을 요구한다. 공개 표시본도 모든 공개 참조가 사라지면 이후 요청을 거부한다. 현재는 매 요청 전체 공개 Post 리비전을 확인하는 작은 실험이며 운영 규모 성능을 검증하지 않았다. 비공개 프록시/스토리지 설정, 고장·동시성·복원·보존 정책은 별도 검증 대상이다.

## 도구 장애 시 사용자 수동 브라우저 검증 — 실행 결과 아님

자동 도구 복구를 기다리지 않고 사용자가 기존 Windows 브라우저로 수행할 수 있는 절차다. 아래 예상 결과는 소스·기존 서버 검증에서 도출한 검사 기준이며 실제 화면을 보았다는 뜻이 아니다. Publish/Unpublish, 삭제, 초기화, seed 재실행, 설치는 포함하지 않는다. [결과 양식](manual-browser-results-template.md), [지원 문의 초안](computer-use-support-draft.md)을 함께 사용한다.

### 1. WSL에서 준비하고 사용자 직접 로그인

기존 WSL Ubuntu 터미널에서 실행한다. 새 증거 폴더를 만들고 Windows에서 접근할 경로를 출력한다. 아래 명령은 아직 실행하지 않은 사용자용 절차다.

```bash
cd /home/shlee/Workspace/ai/01.codex/y3gym/experiments/cms-spike
spike_evidence=$(mktemp -d "$PWD/.runtime/manual-browser-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
cp manual-browser-results-template.md "$spike_evidence/results.md"
wslpath -w "$spike_evidence"
.venv/bin/python manage.py create_spike_editor local-editor
```

마지막 명령의 암호를 사용자가 숨김 입력으로 두 번 입력한다(12자 이상). 비밀번호를 대화로 보내거나 명령 인자·파일·로그에 넣지 않는다. 기존 계정이라는 오류면 변경 없이 중단하므로 기존 계정 소유자가 직접 로그인한다. 최고 관리자를 만들지 않는다. 이 명령은 staff 일반 운영자와 `SPIKE-01 content editor` 그룹을 만든다. 이 그룹에는 실험 Post 공개 권한도 있으므로 버튼이 보여도 이번에는 사용하지 않는다. 이미지 권한은 시험 컬렉션의 추가·수정·선택이며 삭제 차단은 별도 실험 코드가 담당한다.

```bash
.venv/bin/python manage.py runserver 127.0.0.1:8765 --noreload --insecure
```

서버는 이 터미널에서 전경 실행한다. 포트 사용 중이면 다른 프로세스를 종료하지 말고 오류만 기록한다. Windows 브라우저에서 [관리자](http://127.0.0.1:8765/admin/)를 열고 사용자가 직접 로그인한다. 암호/로그인 화면은 캡처하지 않는다. Windows 접속이 실패하면 접속 오류와 WSL 서버 시작 여부만 기록하고 BLOCKED로 멈춘다. 외부 바인딩·방화벽 변경으로 우회하지 않는다.

### 2. 편집 전 비교 기준 수집

관리자와 분리된 InPrivate/시크릿 창을 열어 로그인하지 않은 상태로 [A 공개 HTML](http://127.0.0.1:8765/spike/posts/1/)과 [A 공개 JSON](http://127.0.0.1:8765/spike/posts/1/json/)을 확인한다. 현재 기록의 예상값은 `SPIKE PUBLIC A`, 대표 이미지 1, 본문 이미지 2다. 다르면 초기화하지 말고 실제 현재값을 기준으로 기록한다. 공개 HTML의 페이지 소스와 JSON 응답 본문을 각각 `before-public.html`, `before-public.json`으로 새 증거 폴더에 저장하고 화면도 남긴다. 인증된 관리자 페이지 소스 전체를 저장하지 않는다.

두 번째 WSL 터미널에서 아래 읽기 전용 DB 명령을 편집 전과 후에 실행해 결과표에 기록한다. 이 조회는 브라우저 검증이 아니며 공개 리비전·참조 비교만 보조한다.

```bash
cd /home/shlee/Workspace/ai/01.codex/y3gym/experiments/cms-spike
.venv/bin/python - <<'PY'
import sqlite3, json
c = sqlite3.connect('file:.runtime/spike.sqlite3?mode=ro', uri=True)
r = c.execute('SELECT id, live, live_revision_id, latest_revision_id FROM posts_post WHERE id=1').fetchone()
print('A id/live/live_revision/latest_revision:', r)
for rid in sorted(set(r[2:])):
    d = json.loads(c.execute('SELECT content FROM wagtailcore_revision WHERE id=?', (rid,)).fetchone()[0])
    print(rid, {k:d.get(k) for k in ['title','cover_image','body']})
print('image ids/titles:', c.execute('SELECT id,title FROM wagtailimages_image ORDER BY id').fetchall())
c.close()
PY
```

### 3. 실제 편집·선택·초안 저장

1. 일반 운영자 창의 Snippets → Posts → A를 연다. 최신 초안 `SPIKE DRAFT A`, 대표 3·본문 4가 보이는지 기록한다(현재값이 바뀌었다면 DB 최신 리비전과 비교). 목록의 공개 제목과 편집 초안 제목을 구분한다.
2. 제목 끝과 본문에 `BROWSER TEST <실행시각>` 표식을 추가한다. 본문에 별도 단어를 입력하고 선택 후 Bold, 다른 단어는 Italic을 누른다. 링크 도구로 `https://example.com/` 링크를 편집한다. 기존 시험 내용을 모두 지우지 않는다.
3. 대표 이미지 선택창을 연다. 기존 합성 이미지 목록·썸네일이 실제 보이는지 확인하고 Upload에서 아래 경로의 `draft-cover.png`를 **새 자산**으로 올린다. 제목에 실행 표식을 붙이고 `SPIKE-01 test images` 컬렉션을 선택한다. 중복 자산 선택을 제안하면 기존 자산으로 대체하지 말고 새 자산 생성 가능 여부를 기록한다.
4. 본문 이미지 도구에서도 별도 선택창을 열어 목록·썸네일을 확인한다. `draft-body.png`를 새 자산으로 올리고 본문에 선택·삽입한다. 새 이미지 ID는 관리자 이미지 편집 URL과 위 DB 조회로 기록한다. 예상 ID를 고정하지 않는다.

   ```text
   \\wsl.localhost\Ubuntu\home\shlee\Workspace\ai\01.codex\y3gym\experiments\cms-spike\.runtime\fixtures
   ```

   이 경로는 현재 `wslpath -w`의 결과다. Windows 파일 선택창에서 실제 열림은 미확인이다. 열리지 않으면 오류를 기록하고 임의 파일 복사·새 이미지 생성 없이 해당 업로드를 BLOCKED로 남긴다.
5. 편집 화면에서 **Save draft**를 누른다. Posts 목록으로 나왔다가 다시 A를 열어 표식·서식·링크·대표/본문 선택 유지 여부를 확인한다. Publish 메뉴는 선택하지 않는다.
6. 초안 저장 후 별도 관리자 탭에서 기존 이미지 1의 편집 화면 `/admin/images/1/`을 연다. 기존 파일 교체 입력이 비활성인지 확인만 하고 변경·삭제하지 않는다. 접근 불가나 활성 입력이 보이면 실제 상태를 FAIL로 기록한다.

### 4. Preview·방문자 비교

1. A 편집 화면 Preview에서 최신 표식과 굵게/기울임·링크·대표 및 본문 이미지가 실제 렌더링되는지 확인한다. 링크는 목적지를 확인하고 외부 사이트 이동은 필요 없다. 편집 화면·chooser·재열기·Preview 각각 별도 스크린샷을 저장한다.
2. 비로그인 InPrivate/시크릿 창에서 공개 HTML/JSON을 새로고침하고 `after-public.html`, `after-public.json` 및 화면을 저장한다. 공개 제목·본문·서식·이미지 URL은 before와 같고 새 시험 표식은 없어야 한다. DB의 live_revision은 편집 전과 같아야 한다. latest_revision은 새 초안으로 바뀔 수 있다.
3. Preview 이미지나 chooser 썸네일에서 관찰한 `/cms-files/...` 주소를 기록한다. 관리자 창에서는 이미지 표시, 방문자 창의 같은 주소는 403이어야 한다. 원본·썸네일·표시 크기 변환본 중 실제로 확인한 종류만 기록한다. 브라우저 개발자 도구 Network의 URL·상태 열로 상태 코드를 확인할 수 있지만 요청 헤더·쿠키·전체 HAR는 저장하지 않는다.
4. Preview에서 실제 사용된 경로가 세션 토큰 없는 관리자 경로일 때만 방문자 창에 주소를 붙여 넣어 로그인 요구를 확인한다. 토큰/비밀값 포함 여부를 판단할 수 없으면 URL을 공유·기록하지 말고 미검증으로 남긴다. 미리보기용 인증을 우회하거나 새 세션을 주입하지 않는다.
5. 새로 업로드한 각 이미지 ID의 `http://127.0.0.1:8765/spike/display/<ID>/`는 방문자에게 404여야 한다. 같은 ID의 인증된 Preview 이미지는 표시되어야 한다. 기존 공개 이미지 1·2의 display 경로는 계속 표시되어야 한다. 이미지 깨짐만으로 403/404를 추정하지 않는다.
6. HTML 표시와 JSON 뷰어 확인은 SP-11의 해당 부분만 기록한다. 별도 JS 앱이 JSON을 받아 렌더링하는 검증은 NOT_RUN으로 남긴다.

### 5. 기록·종료·결과 전달

`results.md`의 M01~M15를 실제 관찰값으로 채우고 사용자 수행이면 관찰자를 `사용자 직접 관찰·보고`로 쓴다. 미수행 항목은 NOT_RUN, 선행 장애로 못 하면 BLOCKED다. 증거 파일은 처음 만든 Git 제외 폴더에 고유 이름으로 저장한다. 브라우저 개발자 도구의 인증 헤더·쿠키·비밀번호·관리자 폼의 숨김 토큰은 캡처하지 않는다. 스크린샷은 화면 동작의 증거이며 공개본 bytes 불변은 저장한 응답 비교와 별도로 판정한다.

원래 서버를 시작한 터미널에서 Ctrl+C로 **그 서버만** 종료하고 종료 시각을 적는다. DB/미디어/새 초안/업로드 자산은 남겨 두고 원복·삭제하지 않는다. 결과를 전달할 때는 실행시각, 브라우저 버전, 마지막 완료 단계, 실패 내용, 새 이미지 ID, 증거 폴더 경로, 서버 종료 여부를 알려 준다. 암호는 전달하지 않는다. 도구가 복구되면 Codex의 직접 관찰 결과를 별도로 추가한다.
