# IPAS 브랜딩·저장소 변경 / Branding and repository migration

## 한국어

**IPAS · Integrated Printing Analysis System**, 시스템 **v0.5.25-ipas-branding**을 운영 API·analysis·viewer·worker에 배포했다. 상단 PrintOps/P 표기를 적층 심볼·IPAS 워드마크·전체 명칭으로 교체했다. 사이트 제목, 엔진 버전 표시, HTML/PDF 보고서, PDF 작성자·푸터, 통합 PDF·묶음 파일 이름에도 반영했다.

| 공식 엔진 표시 이름 | GitHub 저장소 | 수치 엔진 버전 |
|---|---|---|
| IPAS-GCODE ENGINE | [IPAS-GCODE-ENGINE](https://github.com/mk0000001/IPAS-GCODE-ENGINE) | 0.28.0 |
| IPAS-STRENGTH ENGINE | [IPAS-STRENGTH-ENGINE](https://github.com/mk0000001/IPAS-STRENGTH-ENGINE) | 0.24.0 |
| IPAS-QUOTE ENGINE | [IPAS-QUOTE-ENGINE](https://github.com/mk0000001/IPAS-QUOTE-ENGINE) | 0.13.0 |

GitHub 저장소의 실제 이름·설명과 로컬 원격 주소를 바꿨다. 기존 `print_*_engine` import 이름, 인증 쿠키·저장 키·호환 API, 저장 당시 엔진 버전은 유지한다. 수치 계산이나 보정 모델을 바꾼 릴리스가 아니므로 엔진 개정 횟수는 늘리지 않았다. 날짜별 과거 검증 문서의 PrintOps 표기는 당시 이름으로 남긴다.

[공개 브랜드 키트](../branding/ipas/README.md)는 밝은/어두운 배경용 SVG 로고·워드마크, 심볼, 다중 해상도 ICO, PNG 파비콘, 180px 터치 아이콘, 192/512px 웹 앱 아이콘과 manifest를 포함한다. README는 GitHub 테마에 맞는 로고를 선택한다. 명시적 아이콘 링크와 `/favicon.ico`를 모두 제공하며 브랜딩 파일만 허용 목록으로 공개한다. 예전 북마크의 저장 제목과 아이콘 캐시는 브라우저가 관리하며 갱신 시점이 다를 수 있다.

검증 결과:

- 브랜딩 동결 이미지에서 관련 시험 **71 passed, 1 skipped, 4 subtests passed**, 의존성 deprecation 경고 2건. 읽기 전용 시험 소스·컨테이너와 독립 시험 DB를 사용했다. skip은 이미지에 Node가 없는 기존 JS 시험이며, 다른 검토 에이전트가 로컬 Node로 해당 실제 회귀 **7개를 모두 통과**시켰다. 마지막 CSS 수정 이미지에서는 자산·UI 계약 시험 **27개가 통과**했다. 전체 물리 모델·대량 corpus 시험을 반복하지 않았다.
- API·analysis·viewer·worker의 **119개 runtime 해시·버전·이미지·네이티브 모듈 일치**. 관측 시 restart 0·OOM 없음, 배포 직전 진행 분석·뷰어 작업 0. 이전 이미지로 되돌릴 수 있는 태그를 보존했다.
- 실제 운영 아이콘·manifest·로고 10개 응답을 로컬 자산 바이트와 비교했다. 별도 시험은 12개 웹 자산과 root ICO의 MIME·무인증 접근·파일 형식·해상도, 비허용 파일·경로 접근 차단을 검증했다.
- 단일·통합 basic/detailed/admin **6종 PDF**를 생성·첫 페이지 시각 검토했다. 운영 저장 견적으로 단일 PDF 3종을 다시 내려받아 IPAS 작성자·명칭·고객/관리자 구분 및 모든 페이지의 텍스트 경계를 검사했다. 로컬 처리 안내는 최상단에 유지한다.
- 실제 브라우저에서 데스크톱 헤더·로드된 로고·아이콘 링크·세 엔진명·서버 연결을 확인했다. 최종 검토에서 320px 창의 세로 스크롤바가 상태 글자 5px를 가리는 문제를 찾아 본문 최소 폭을 `min(320px, 100%)`로 수정했다. 최종 320px 뷰포트의 실제 사용 폭·본문·헤더·문서 가로 폭은 모두 **305px**, 접속 상태 오른쪽은 **295px**로 잘리지 않는다. 운영 URL에서 캡처된 error/warning은 0건이다. 앞선 정적 미리보기의 API 404는 별도로 구분했다.
- 이번 변경 직전과 이후 저장 견적 100건 전체 응답이 바이트 단위로 동일하다. SHA-256: `aef9b7c63d5c2387a45b907b39d54bf4ac8ea628b5c5b88e65d15ddbd58f8afa`. 새 견적·업로드를 만들지 않았다.
- 독립 에이전트가 변경 범위·자산·인증·PDF·v3 동결·시험·네 서비스 배포와 운영 검증을 교차 검토했다. GitHub 다크 테마 로고 가독성 지적을 반영했다. 최종 판정은 **PASS**다.

최초 시험 실행 도우미는 설치된 Compose가 지원하지 않는 `--no-build` 옵션 때문에 pytest 시작 전에 중단됐다. 옵션을 제거하고 실패 기록을 보존했다. 이후 사용자 요청으로 엔진 표시 이름도 추가한 v3 소스를 동결·빌드·검증해 운영 배포했다. 마지막 화면 검토에서 발견한 CSS 한 줄만 별도 동결·집중 시험 후 추가 배포했으며, 이전·최종 이미지의 네 서비스 해시를 각각 확인했다. 수치 모델 변경은 없다.

브랜딩 v3 동결: `cd2995fc6ce95fbe0ba2cc2d0dd1d95ebbdedfe372e53bcbcc3dce0665955a9c`. **최종 CSS 포함 동결: `ab2b396d9e3d6c3aad112abebf0305967e76b21999fe47fc3b8b930c39905177`**, 운영 이미지: **`sha256:fdbae1e45c78f3afc0348cb2df7643411c1b36b7dec14e09a06f34819c7bb477`**. [호스트 표시 변경 패치](patches/ipas-branding-20261008.patch)는 직전 v0.5.24 소스에서 apply-check와 실제 임시 적용 비교를 통과했다. 브랜드 키트의 12개 웹 자산은 별도로 `app/web/`에 복사한다. 공개 자산·문서·표시 패치만 게시했으며 운영 정책·고객 자료·접속정보는 포함하지 않는다.

## English

**IPAS · Integrated Printing Analysis System**, host **v0.5.25-ipas-branding**, is deployed to API, analysis, viewer and worker. The layered symbol, IPAS wordmark and full name replace the current PrintOps/P identity in the web header, page title, engine display, HTML/PDF reports, PDF metadata/footers and bundled/combined download names.

GitHub repositories are now [IPAS-GCODE-ENGINE](https://github.com/mk0000001/IPAS-GCODE-ENGINE), [IPAS-STRENGTH-ENGINE](https://github.com/mk0000001/IPAS-STRENGTH-ENGINE) and [IPAS-QUOTE-ENGINE](https://github.com/mk0000001/IPAS-QUOTE-ENGINE). Descriptions, README headers and local remotes follow the new names. Import names, session/storage keys, compatible APIs and saved version provenance remain unchanged. Numerical versions stay at G-code 0.28.0, strength 0.24.0 and quote 0.13.0; a branding release does not add numerical revisions.

The [brand kit](../branding/ipas/README.md) includes theme-aware SVG lockups, a multi-resolution ICO, PNG/touch/web-app icons and a manifest. Explicit links and `/favicon.ico` are served with correct types through an allowlist. Previously saved bookmark titles/icon caches remain browser-managed.

Focused branding-image QA: **71 passed, 1 skipped, 4 subtests passed** with two dependency deprecations. A separate reviewer ran all seven actual Node history cases omitted by the Node-free image. The final CSS-only image passed **27 focused asset/UI contract tests**. All four services match the final frozen 119-file runtime identity and native modules, with zero observed restart/OOM and idle jobs before promotion. Rollback is retained. No full corpus or numerical suite was repeated.

All six synthetic single/combined report variants were rendered; three production report audiences were downloaded and checked for IPAS identity, metadata, audience separation and page text bounds. The local-processing notice remains first. Live browser checks confirm loaded artwork, icon links, all engine names and server connectivity. Final review caught a 5px status-text overlap with the desktop scrollbar at a 320px viewport; the CSS minimum-width fix now yields a 305px client/body/header/document width and a 295px right action boundary. No production-origin browser warnings/errors were captured; expected API 404s from the earlier static-only preview were excluded explicitly. The current 100-row full estimate response is byte-identical before/after, including after the CSS follow-up; no quote/upload was created.

The initial helper failed before pytest because this Compose installation rejects `--no-build`. Its receipt is retained; the supported command and final engine labels were frozen, rebuilt and tested before branding deployment. The discovered one-line CSS fix was separately frozen, tested and promoted with previous/final four-service identity checks. Independent cross-review is **PASS**, including the GitHub dark-mode logo and scrollbar corrections. Final freeze/image identities are listed above. The [presentation patch](patches/ipas-branding-20261008.patch) passed application checks against the preceding host; copy the twelve kit assets separately into `app/web/`. Public changes contain no private policy, customer data or credentials.
