# 후보 카드 반응형 배치 검증 / Responsive candidate presentation

## 한국어

후속 범위 한정 배포: [PrintOps v0.5.24 견적 목록 지연 수정·실측 보정 적격성](history-calibration-review-20261007.md). 아래 v0.5.23 결과는 해당 릴리스 당시의 기록이다.

**PrintOps v0.5.23-responsive-candidates를 실제 운영 네 서비스에 배포했다.** 강도 **v0.24.0**, G-code **v0.28.0**, 가격 **v0.13.0**은 유지한다. [이전 품질 검토](commercial-quality-review-20261007.md)의 완료된 계산·보고서·성능 검증을 반복하지 않고, 이번 화면 변경에 필요한 확인만 수행했다.

기존 후보 영역은 515px 폭에서도 3열로 배치되어 카드가 약 156.9px까지 좁아졌다. 이제 후보 영역의 실제 content 폭에 따라 1·2·3열을 선택한다. 상세 설명을 열면 해당 카드가 전체 열을 사용하고, 닫으면 기존 배치로 돌아간다. 카드 번호와 문서 순서는 유지하며 빈칸을 채우려고 순서를 재배치하지 않는다.

변경은 호스트의 `app/web/styles.css`, `app/config.py`, `app/web/index.html` 세 파일뿐이다. CSS container query 경계는 content 폭 **468 / 706px**, padding·border를 포함한 영역 폭 **498 / 736px**이다. 앱 버전과 CSS cache key도 갱신했다. JS·DOM·계산·가격·PDF 구현과 세 엔진의 소스는 이전 동결 자료와 동일하다. [호스트 변경 패치](patches/responsive-candidates-20261007.patch)는 공개 코어 패키지의 새 물리 모델이 아니다. 강도 개정 24회·업데이트 23회 집계도 그대로다.

### 이번 변경의 검증

- 현재 동결 이미지의 asset-serving·health·batch 계약 시험 **4 passed**, 의존성 deprecation 경고 2건, 0.32초, 종료 0. 별도 시험 DB와 읽기 전용 시험 소스를 사용했다. 전체 시험을 다시 실행한 것으로 표시하지 않는다.
- 기존 공정·자동 하중·취약부 표시·소재 identity JS 회귀 **4개 스크립트 통과**. 변경 전후 100개 시험 소스 해시도 동일하다.
- 배포 전 분석·뷰어 진행 작업 0건. API·analysis·viewer·worker의 이미지, 106개 runtime 파일 해시, 앱/엔진 버전과 네이티브 스캐너가 동결 자료와 일치한다. 확인 시 재시작 0·OOM 없음. 이전 검증 버전으로 되돌릴 이미지도 보존했다.
- 실제 기존 H2C 파일로 **7개 화면 상태**를 확인했다. 기본 515px 후보 영역은 **2열 / 카드 239.34px**, 390px viewport의 후보 영역 307px은 **1열 / 279px**, 1920px viewport의 후보 영역 924px은 **3열 / 약 293.33px**였다. 기본 화면의 펼친 후보는 **486.69px**, 넓은 화면은 **896px**를 사용했다.
- 마우스·Enter 키의 펼침/닫힘, 화면 폭 복원, 후보 번호 순서와 6개 버튼의 전체 수치 문구 불변을 확인했다. 확인한 카드·후보 영역의 가로 넘침과 browser error/warning은 0건이다. 신규 업로드·견적 저장 없이 기존 캐시를 사용했다.
- 다른 한 에이전트의 최종 검토 **PASS**. 변경 범위·릴리스 gate·배포·실제 화면 기록을 교차 검토했고, 기존 A/B 검증 기록 84개 파일의 불변도 확인했다. 별도 에이전트가 새 브라우저 전수 시험을 실행한 것으로 표현하지 않는다.

동결 identity: `2eb0ab109346a5a6e640600a4cdb4be3327a78f1402175a95d568e919b31f948`.
운영 이미지: `sha256:be424ef1b1ef7241689ee56cfa5626d62d9e8e4dc02da3eaa9919f407972c06c`.

공개 패치는 호스트 워크트리 대상이다. VERSION·cache key의 zero-context hunk를 적용할 때는 `git apply --unidiff-zero`가 필요하다. 패치 SHA-256: `af3152e40aa67d309adb2bf5607c5dae923d3cee3e09e9d1adbdf82af3398cb8`.

이 검증은 한 운영 파일의 화면 표시와 수치 보존에 대한 것이다. 실측 파단 정확도, 전체 입력의 UI 무결함, 특허 가능성 또는 상용 인증을 입증하지 않는다. 큰 견적 이력 응답의 지연과 물리 보정 데이터 부족은 [이전 검토의 한계](commercial-quality-review-20261007.md)로 남는다. 사용자 요청에 따라 자동 실행을 **PAUSED**로 바꾸었으며, 이번 마지막 작업 턴 후 추가 예약 작업을 진행하지 않는다.

## English

Subsequent bounded deployment: [PrintOps v0.5.24 history latency and empirical qualification](history-calibration-review-20261007.md). The v0.5.23 results below remain historical release evidence.

**PrintOps v0.5.23-responsive-candidates is deployed to the actual four-service installation.** Strength **v0.24.0**, G-code **v0.28.0** and quote **v0.13.0** remain unchanged. Completed numerical, report and performance validation from the [previous quality review](commercial-quality-review-20261007.md) was not repeated.

The 515px candidate pane previously forced three approximately 156.9px cards. Named container queries now select one, two or three columns from the pane's actual content width. A card with an open detail spans the grid; closing it restores normal layout. Source/rank order is preserved without dense placement.

Exactly three host files changed: candidate CSS, app version and the CSS cache key. Content-width thresholds are **468 / 706px**, or **498 / 736px** including existing padding/borders. JS, DOM, calculations, pricing, PDF implementation and all three engine sources match the previous freeze. The [host patch](patches/responsive-candidates-20261007.patch) is not a new physical model or core package release; strength remains at 24 code revisions / 23 updates after initial import.

Focused frozen-image tests passed **4 tests**, with two dependency deprecation warnings, exit zero in **0.32 seconds**, using isolated test DB and read-only test sources. Four existing UI behavioral regression scripts passed. All 100 test-source hashes are unchanged. Deployment had no active jobs; all four service images, 106 runtime hashes, versions and native scanner modules match the freeze, with zero observed restarts/OOM and a preserved rollback image.

Seven actual browser states on one existing H2C file confirmed **515px pane → two 239.34px cards**, **390px viewport / 307px pane → one 279px card**, and **1920px viewport / 924px pane → three approximately 293.33px cards**. Expanded cards used **486.69px / 896px** in default/wide layouts. Mouse/Enter toggles, original viewport restoration and source order passed. All six complete button texts, including numerical values, exactly matched the pre-deployment baseline. Observed card/region overflow and captured browser errors/warnings were zero. No new upload or quote was saved.

Freeze identity: `2eb0ab109346a5a6e640600a4cdb4be3327a78f1402175a95d568e919b31f948`.
Deployed image: `sha256:be424ef1b1ef7241689ee56cfa5626d62d9e8e4dc02da3eaa9919f407972c06c`.

A different agent's final cross-review **passed**, covering scope, release gates, deployment and recorded actual browser evidence; 84 existing A/B evidence files are unchanged. This is not an independently repeated exhaustive browser session. The public patch targets the host worktree and requires `git apply --unidiff-zero` for its VERSION/cache-key hunks. Patch SHA-256: `af3152e40aa67d309adb2bf5607c5dae923d3cee3e09e9d1adbdf82af3398cb8`.

This is presentation and preserved-value verification for one live fixture, not proof of empirical fracture accuracy, all-input UI correctness, patentability or commercial certification. Large-history response latency and missing physical calibration data remain bounded limitations from the previous review. The automation is **PAUSED** at the user's request; no further scheduled work follows this final turn.
