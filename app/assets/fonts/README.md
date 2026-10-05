# 공개 화면 자체 제공 폰트

DEV-06-F (2026-10-05). 공식 저장소의 아래 커밋에서 WOFF2 원본 두 개만 받아 수정·변환·서브셋 없이 배포한다. 런타임 CDN/승종 hotlink 없음. 승종에서 확인한 같은 폰트 계열/굵기를 적용했으며 승종 파일과 버전·바이트 동일성은 미확인이다.

- 본문/버튼/메뉴: SUIT Variable, normal, 가변 wght100–900.
- 공개 h1/h2/h3: IBM Plex Sans KR SemiBold, normal, 고정600. IBM 공식 complete/hinted 배포본을 선택했다.
- 두 폰트 모두 SIL Open Font License 1.1. 폰트 단독 판매 금지, 재배포 시 저작권/라이선스 동봉 등 원문의 조건을 유지한다. 프로젝트 코드의 라이선스로 대체하지 않는다.

## SUIT-Variable.woff2

- 공식 저장소: [sun-typeface/SUIT](https://github.com/sun-typeface/SUIT)
- 고정 커밋: `55118d981336d8fce005eb62888c12c0568ef7b0`
- [원본 다운로드](https://raw.githubusercontent.com/sun-typeface/SUIT/55118d981336d8fce005eb62888c12c0568ef7b0/fonts/variable/woff2/SUIT-Variable.woff2)
- 폰트 내부 버전: `Version 2.040;Glyphs 3.2.3 (3260)`
- 크기: 624536 bytes
- SHA-256: `aa894a204d5a6fbae259dac6868d350cbd373a390caee0313f92946af741df23`
- 동봉 라이선스: [SUIT-OFL.txt](SUIT-OFL.txt) ([동일 커밋 원문](https://raw.githubusercontent.com/sun-typeface/SUIT/55118d981336d8fce005eb62888c12c0568ef7b0/LICENSE))

라이선스 저작권: Copyright (c) 2022, SUNN (http://sun.fo/suit), with Reserved Font Name SUIT. 바이너리 내부 표기: Copyright © 2022 Sun.

## IBMPlexSansKR-SemiBold.woff2

- 공식 저장소: [IBM/plex](https://github.com/IBM/plex)
- 고정 커밋: `763c36ef9117782905ae010056dfbe8fd2653a25`
- [원본 다운로드](https://raw.githubusercontent.com/IBM/plex/763c36ef9117782905ae010056dfbe8fd2653a25/packages/plex-sans-kr/fonts/complete/woff2/hinted/IBMPlexSansKR-SemiBold.woff2)
- 폰트 내부 버전: `Version 1.003`
- 크기: 434484 bytes
- SHA-256: `5ad7db28ba74d59fe14c260205c62ddb701320f4f098d8a45ef2757bebc29666`
- 동봉 라이선스: [IBM-Plex-OFL.txt](IBM-Plex-OFL.txt) ([동일 커밋 원문](https://raw.githubusercontent.com/IBM/plex/763c36ef9117782905ae010056dfbe8fd2653a25/packages/plex-sans-kr/fonts/complete/woff2/hinted/license.txt))

라이선스 저작권: Copyright © 2017 IBM Corp. with Reserved Font Name "Plex". 바이너리 내부 표기: Copyright 2018 IBM Corp. All rights reserved. 두 원본 표기를 변경하지 않았다.

## 제공 경로·검증

`site.css`의 상대 URL `fonts/*.woff2`는 `/static/fonts/`로 해석된다. 기존 Django `STATICFILES_DIRS`의 `app/assets`에서 수집되므로 별도 빌드/의존성 설치가 없다. CSS에서 `font-display: swap`과 한글/라틴 시스템 fallback을 선언한다. 파일명은 원본 그대로이며 교체 시 버전·해시·캐시 정책을 다시 확인한다. 실제 폰트 렌더링은 사용자 확인 대기다.
