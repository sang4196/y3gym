# SPIKE-01 수동 브라우저 기록 양식

이 파일은 미실행 양식이다. `.runtime/manual-browser-<시각>/results.md`로 복사해 채운다. 예상값을 관찰값으로 복사하지 않는다. 상태는 PASS / FAIL / BLOCKED / NOT_RUN, 관찰자는 `사용자 직접 관찰·보고` 또는 `Codex 직접 관찰`로 구분한다. 사용자 보고만 받으면 Codex 직접 검증 PASS로 바꾸지 않는다.

- 수행 일시/시간대: 미기록
- 관찰자/결과 전달자: 미기록
- Windows/브라우저 이름·버전: 미기록
- 일반 운영자명(암호 금지)/권한 확인: 미기록
- 독립 방문자 세션 방식: 미기록
- 서버 실행자/터미널/시작·종료 시각: 미기록
- 실행 전 A live/latest revision 및 이미지 ID: 미기록
- 실행 후 A live/latest revision 및 새 이미지 ID: 미기록
- 시험 표식: 미기록

| 번호 / SP | 검사 | 상태 | 실제 관찰·오류·HTTP 상태(확인한 경우만) | 증거 파일 / 관찰자 |
|---|---|---|---|---|
| M01 | Windows 루프백 접속·일반 계정 로그인 | NOT_RUN | | |
| M02 | 편집 전 방문자 공개 HTML/JSON 및 DB 기준 | NOT_RUN | | |
| M03 / 01 | Snippets→Posts A 최신 초안 표시 | NOT_RUN | | |
| M04 / 01 | Bold/Italic·링크 편집 | NOT_RUN | | |
| M05 / 01 | 대표 chooser 목록·보호 썸네일·新 업로드 선택 | NOT_RUN | | |
| M06 / 01 | 본문 chooser 목록·보호 썸네일·이미지 선택 | NOT_RUN | | |
| M07 / 01 | 기존 이미지 파일 덮어쓰기 비활성 | NOT_RUN | | |
| M08 / 01 | Save draft·다시 열기·선택 유지 | NOT_RUN | | |
| M09 / 05 | Preview 서식·링크·대표/본문 이미지 표시 | NOT_RUN | | |
| M10 / 03 | 독립 방문자 HTML/JSON·공개 리비전 유지 | NOT_RUN | | |
| M11 / 05·06 | 인증/방문자 보호 이미지·preview 차이 | NOT_RUN | | |
| M12 / 03·06 | 새 초안 이미지 공개 display 거부 | NOT_RUN | | |
| M13 / 11 | 공개 HTML 및 JSON 뷰어 확인 범위 | NOT_RUN | | |
| M14 / 11 | 별도 JS 클라이언트 렌더링(이번 절차 밖) | NOT_RUN | | |
| M15 | 자기 서버 종료·자료 보존 | NOT_RUN | | |

실패/차단 시 마지막 성공 단계, 기대와 실제 차이, 재현 순서를 적는다. 로그인/암호 화면·쿠키·Authorization·CSRF 값·전체 HAR/스토리지 덤프는 기록하지 않는다. Publish/Unpublish는 하지 않는다.
