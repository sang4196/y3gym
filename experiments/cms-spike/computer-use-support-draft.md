# Computer Use 지원 문의 초안 — 외부 전송하지 않음

작성일: 2026-09-18. 사용자가 검토하고 전달할 초안이다. 개인 로그·설정·환경 전체·DB·인증 자료를 첨부하지 않는다. 로컬 경로의 사용자명은 필요에 따라 가린다.

## 제목

WSL 프로젝트에서 node_repl이 sandboxCwd URI 검사에 실패함 — 커널 reset 이후에도 재현

## 환경과 영향

- Windows 호스트의 Codex 데스크톱 작업, 실행 cwd는 `/home/shlee/Workspace/ai/01.codex/y3gym`.
- WSL 배포 이름 환경값 `Ubuntu`, Ubuntu 26.04.1 LTS, 커널 `6.18.33.2-microsoft-standard-WSL2`, ext4. Windows 및 Codex 앱 정확한 버전은 미확인(사용자가 앱 정보 화면에서 추가 가능).
- 제공된 Computer Use 스킬 경로 버전 `26.915.31029`. 이는 설치 캐시 경로 정보이며 실행 helper의 바이너리 버전을 확인했다는 뜻은 아님.
- Linux exec_command는 정상. node_repl의 코드 실행만 실패하여 Windows 앱/브라우저 선택·캡처에 도달하지 못함.
- 프로젝트는 로컬 Django/Wagtail 실험이지만 서버 실행이나 계정 로그인 없이 오류가 재현됨.

## 최소 재현 및 실제 결과

1. 위 WSL cwd의 기존 작업에서 제공된 공식 `mcp__node_repl__js`를 호출:

   ```js
   nodeRepl.write("SPIKE01_NODE_PROBE");
   ```

   기대: 문자열 출력. 실제: 아래 오류, 문자열 출력 없음.
2. 공식 `mcp__node_repl__js_reset({})` 호출: `js kernel reset`, isError=false.
3. 공식 스킬 초기화 호출:

   ```js
   if (!globalThis.sky) {
     const { sky } = await import("@oai/sky");
     globalThis.sky = sky;
   }
   ```

   실제: 같은 오류, isError=true.

```text
Mcp error: -32602: js: codex/sandbox-state-meta: sandboxCwd is not a local file URI: file:///home/shlee/Workspace/ai/01.codex/y3gym
```

## 확인 사실과 추정

확인: sky를 import하지 않는 코드에서도 실패하므로 sky API 호출·브라우저·대상 사이트 인증과 독립적으로 node_repl의 sandbox-state-meta/cwd 처리에서 차단된다. reset만으로 복구되지 않는다. 도구 입력 스키마에는 cwd/host 지정 인자가 없다. Linux 셸의 cwd와 Git 루트는 일치한다. 개인 설정이나 내부 구현을 열어 보거나 수정하지 않았다.

추정: Windows 대상 Computer Use 실행 컨텍스트와 Linux `file:///home/...` URI 간 처리 불일치 가능성. 실제 node_repl 서버 OS·URI 변환 구현·오류 발생 코드 줄은 미확인이므로 확정 원인으로 보고하지 않는다. WSL 경로를 일반적으로 지원하지 않는다고 결론내리지 않는다.

요청: 현재 WSL 저장소를 이동하지 않고 공식 node_repl/Computer Use를 연결하는 지원 경로, 해당 URI 오류의 알려진 문제 여부, 수정 버전 또는 공식 비파괴 복구 절차를 알려 달라. 다른 호스트 지정이나 내부 패치가 필요한지 임의로 시도하지 않았다.

## 참고 및 수행하지 않은 조치

공식 [WSL 안내](https://developers.openai.com/es-419/docs/windows/wsl)는 WSL2에서 Linux 환경으로 실행함을 설명하며, [Computer Use 안내](https://developers.openai.com/es-419/docs/computer-use)는 Windows 대상 앱의 활성 데스크톱 사용을 안내한다. 2026-09-18 실제 페이지를 열어 확인했으나 이 정확한 오류의 원인/해결책은 확인하지 못했다. 프로젝트 이동·설치·방화벽/보안 설정 변경·내부 패치·비공식 helper·인증 우회·새 작업 생성은 하지 않았다.

관련 증거: `.runtime/browser-followup-20260918T134605640425Z/computer-use-error.txt` 및 이번 `.runtime/tool-diagnosis-*/results.json`. 이는 도구 오류 기록이며 브라우저 화면 증거가 아니다. 외부 전달 시 전체 `.runtime` 대신 검토한 최소 오류만 사용한다.
