# 품질 개선과 운영 검증 / Quality improvements and deployed verification — 2026-10-07

## 한국어

후속 화면 수정 배포: [PrintOps v0.5.23 후보 카드 반응형 검증](responsive-candidates-release-20261007.md). 아래 v0.5.22 결과는 해당 릴리스 당시의 검증 기록이며, 좁은 후보 카드 문제는 후속 수정에서 해결했다.

**강도 v0.24.0 / PrintOps v0.5.22-commercial-quality를 실제 운영 서비스에 배포했다.** 최종 동결 이미지의 전체 시험, 네 서비스, 실제 HTML/PDF, 브라우저 및 읽기 전용 API 검증을 수행했다. 완료된 [v0.23 전체 엔진 검토](whole-engine-review-20261007.md)의 물리 계산 수정에 이어 출처 감사·표시·견적 이력 응답을 보완한다. 이전 운영 결과를 새 릴리스의 증명으로 대신하지 않는다.

강도 **v0.24.0**, 코드 개정 **24회**·최초 등록 이후 업데이트 **23회**, 패키지 소스 `d065d560a24028c93055540c769096174feb1d75`를 대상으로 한다. [집계 규칙](../VERSION_HISTORY.json)은 패키지 변경 비병합 커밋 기준이며 개정 수는 정확도·인증 등급이 아니다. 승인된 공정 전이 모델 **0**, 독립 외부 target-part 최초 파손 검증 **0**은 유지된다.

### 변경과 검증의 경계

| 범위 | 이번 변경 / 의미 |
|---|---|
| 관측 provenance | publication/version DOI, canonical campaign, 원 raw specimen 및 published aggregate/derived summary를 구분한다. 선택적인 observation map으로 알려진 alias를 같은 campaign에 묶고 원 outcome 재사용을 검사한다. DOI·저자·동일 수치만으로 시편 동일성을 만들지 않는다. |
| 신뢰 경계 | map은 curator/caller가 제공한 metadata의 내부 정합성 검사를 받는다. 출처 진위·실험 독립성의 외부 인증은 아니다. map이 없는 기존 감사는 `CALLER_DECLARED_UNVERIFIED`로 유지한다. aggregate는 specimen 감사에서 제외하며 n만큼 가짜 행으로 늘리지 않는다. |
| 미해결 관측 | M05/M06/M07의 반복 ABS 집계와 상충 공정 조건은 unresolved overlap으로 보류한다. 동일 시편 ID를 발명하거나 해당 평균을 런타임 강도로 수입하지 않는다. 독립으로 식별된 실험의 우연히 같은 수치는 허용한다. |
| 보고서의 선택 평면 | 주표는 축방향·굽힘의 선택 조건에 맞는 면적/기하학을 표시한다. 다른 평면의 축방향 면적을 굽힘 면적으로 대신 쓰지 않는다. 해당 mode 면적이 없으면 미기록으로 표시한다. 후보 간 비교 가능한 거리만 주표의 제목에 반영한다. |
| 보고서 가독성 | 주표는 compact summary로 위치·선택 조건·참고 하중을 읽기 쉽게 정리한다. 대체 기하학, 거리, 공정 명령, 가정·한계는 technical appendix에 보존한다. 내부 역학 참고값은 실측 파단하중으로 표시하지 않는다. |
| 웹 표시 | 공간적으로 분리해 선별한 최대 6개 후보와 같은 25 mm 비교 조건 내 순서를 명시한다. 전체 취약점 전수 검출·실제 파손 순위로 표시하지 않는다. 기하학 비교의 면적은 인장 경로 단면으로 명시한다. |
| 저장 견적 이력 | 저장된 JSON을 직접 응답하는 경로로 재귀 인코딩 비용을 줄인다. 예약 `_sa` dictionary key가 있는 legacy 자료는 기존 encoder 경로로 돌아가 호환성을 보존한다. 응답 내용·순서와 원본 입력을 바꾸지 않는다. |

세부 provenance 계약은 [공정 보정 감사](process-calibration.md)에 있다. `PROCESS_CALIBRATION_AUDIT_V2_OBSERVATION_PROVENANCE`, `PRIMARY_LITERATURE_COMPARISONS_V3_OBSERVATION_PROVENANCE`, `PROVENANCE_OBSERVATION_MAP_V1`은 출처 표현의 변경이며 새 물리 강도 모델이 아니다. geometry/capacity/scanner 계약을 바꿔 전체 원본 재스캔을 유발하지 않는다. 통계 후보 통과가 모델 설치를 뜻하지 않으며 `APPROVED_MODEL_IDS = ()`다.

### 실행한 검증

- **공개 코어:** 실제 agent tool 실행에서 focused **56개**, full **281개**가 통과했다. full은 준비된 Python **3.12.14**와 기존 geometry runtime에서 실행했다. 원본 stdout 로그는 저장되지 않아 사후 tool-result receipt로 한계를 기록했다. 이를 새 최종 이미지 시험으로 표현하지 않는다.
- **최종 동결 이미지:** **651 passed, 20 skipped, 164 subtests passed**, 276.57초, 종료 0. 별도 시험 DB와 읽기 전용 시험 소스를 사용했다. 의존성 deprecation 경고 2건이며 skip은 통과 수에 포함하지 않는다. 앞선 stale-label 실패 기록도 보존했다.
- **운영 배포:** API·analysis·viewer·worker 네 서비스의 이미지·106개 runtime 파일 해시·버전·네이티브 스캐너 일치. 배포 전 진행 작업 0, 확인 시 재시작 0·OOM 없음. 로컬·빌드·네 서비스의 R6 ZIP, 로드된 가격 문서, 소재 카탈로그 해시도 일치한다. 비공개 정책 원문·접속정보는 공개하지 않는다.
- **기존 자료:** 견적 100건 input/result snapshot과 기존 viewer manifest 불변. 신규 견적을 저장하지 않았고 전체 원본을 재스캔하지 않았다. 실제 PDF 첫 페이지 금액도 이전 보고서와 같다.
- **실제 PDF:** 운영 폰트의 고객 상세 **9쪽**, 관리자 **12쪽** 전부 렌더링·시각 검토했다. 이전 10/14쪽에서 줄었으며 페이지 밖 글자 0, 보고서마다 그림 2개 유지. 후보 4의 선택 면적 **굽힘 13.09 / 축방향 12.51 mm²**, 1.80 N·중력 환산 단위, 최상단 로컬 분석 고지와 고객/관리자 내용 경계를 확인했다. 한 운영 fixture의 결과이며 모든 가능한 입력에 대한 증명은 아니다.
- **실제 웹:** 기존 H2C/Vortek 파일의 280/110/65 °C 명령, 6개 선별 후보, 첫 25 mm 굽힘 참고 **183 g / 1.80 N**, 후보 4의 축방향 면적 라벨과 공정·거리 펼침을 확인했다. 확인한 browser error/warning 0, 후보 영역 가로 넘침 0이다.
- **로컬 이력 인코딩:** 실제 저장 견적 100건의 동일 스냅샷을 seven alternating-order pairs로 비교했다. median **0.8870276000 → 0.1746041000 s**, 인코딩 경과시간 **80.3158% 감소**였다. 두 경로 모두 원본 응답 **14,437,579 bytes**, SHA-256 `96419583b33b8c4cbc641bb680f046c4271bb208ff75bb42a3953c56417048cd`와 바이트 단위로 일치했다. Python 3.12의 로컬 인코딩만 측정했으며 DB·LAN·브라우저 parsing, 드문 legacy fallback, 전체 시스템 속도·tail SLA는 이 비율에 포함되지 않는다.

동결 identity는 `3a418320a51d42cb4adce75477804b7e473e36755271f254b09f5bb0f13655d4`, 운영 이미지 ID는 `sha256:a73bb812da32e4b68a91257d4144dac9b02ed77671f1b6e830edfc67eeb2ea84`다. G-code **v0.28.0**, 가격 **v0.13.0**은 유지했다.

같은 일정의 **읽기 전용 GET 72건**을 전후 측정했다. 단독 요청은 endpoint별 8건, 혼합 동시 요청은 동시성 4·endpoint별 16건이다. 전후 요청 오류 0이며 p95는 보존된 원본 행에서 nearest-rank 방식으로 계산했다.

| 견적 이력 100건 | 이전 중앙값 | 배포 후 중앙값 | 관측 경과시간 감소 |
|---|---:|---:|---:|
| 단독 요청 | 2.5340초 | 1.2974초 | 48.80% |
| 혼합 동시 요청 | 9.0129초 | 2.3505초 | 73.92% |

혼합 동시 부하의 최대/p95는 config **0.540초**, viewer **1.317초**, 이력 **4.355초**였다. 큰 이력 응답의 지연은 여전히 남아 있다. config 중앙값은 **0.0571 → 0.2633초**로 증가해 모든 endpoint가 빨라졌다고 주장하지 않는다. 전후 측정은 시간 순서가 다른 운영 snapshot이며 LAN·운영 부하를 통제한 paired experiment, 전체 시스템 향상률 또는 tail-SLA 인증이 아니다.

좁은 화면에서는 후보 영역 폭 515px에 3열 카드가 약 156.9px씩 배치되어 펼친 기술 설명이 지나치게 길어진다. 가로 넘침은 없지만 반응형 배치·가독성 개선이 필요하다. 대량 이력 payload와 지연도 후속 최적화 대상으로 남긴다.

[재료 근거](material-evidence-review-20261007.md), [접합·파괴 근거](fracture-evidence-review-20261007.md), [D01 Supporting 데이터 검토](d01-supporting-data-qualification-20261007.md)를 함께 읽어야 한다. D01은 작은 supporting ZIP과 35조건을 확인했지만 원시 CSV의 force/stress/strain 단위·gauge area·first-failure는 미확인이다. 이 작업은 calibrated physical accuracy, 안전 설계 하중, 특허 가능성 또는 상용 인증을 입증하지 않는다.

## English

Subsequent presentation deployment: [PrintOps v0.5.23 responsive candidate verification](responsive-candidates-release-20261007.md). The v0.5.22 results below are historical release evidence; the narrow-card issue is resolved by the follow-up.

**Strength v0.24.0 / PrintOps v0.5.22-commercial-quality is deployed to the actual four-service installation.** Final-frozen host tests, live services, HTML/PDF, browser and read-only API checks were performed. Following the physical fixes in the [v0.23 review](whole-engine-review-20261007.md), this release improves provenance, presentation and history responses; prior deployed results are not substituted as proof for this release.

This review targets strength **v0.24.0**, **24** package code revisions and **23** updates after initial import, source `d065d560a24028c93055540c769096174feb1d75`. The [commit-counting rule](../VERSION_HISTORY.json) is not an accuracy or certification rating. Approved process-transfer models and independent external target-part first-failure validations both remain **zero**.

The observation contract separates publication/version identity, canonical campaigns, raw specimens, aggregates and derivatives. An optional curator/caller map groups known aliases and detects original-outcome reuse. Equal values, shared authors or one DOI never establish specimen identity. Map validation checks metadata consistency, not source authenticity or independent experiment certification. Legacy caller-only audits remain `CALLER_DECLARED_UNVERIFIED`; aggregate n is not expanded into invented specimens. M05/M06/M07 remain unresolved overlap with their conflicting conditions, without invented specimen IDs or imported runtime strengths. Independently identified campaigns may have identical rounded outcomes.

Report summaries use the selected axial/bending mode's plane and geometry; missing bending area is explicitly unrecorded and not substituted from the axial plane. Comparable distances qualify summary headings. A compact summary preserves the useful position, scenario and reference loads, while alternative geometry, distances, process commands and assumptions remain in a technical appendix. These loads remain conditional mechanics references. Stored estimate history uses direct JSON response encoding, with legacy encoder fallback for reserved `_sa` dictionary keys, preserving legacy response contents/order and inputs.

The [calibration contract](process-calibration.md) documents `PROCESS_CALIBRATION_AUDIT_V2_OBSERVATION_PROVENANCE`, `PRIMARY_LITERATURE_COMPARISONS_V3_OBSERVATION_PROVENANCE` and `PROVENANCE_OBSERVATION_MAP_V1`. Geometry/capacity/scanner contracts and numerical material models are unchanged. A passing statistical candidate does not install a model: `APPROVED_MODEL_IDS = ()`.

### Executed verification

- Actual agent tool results show **56 focused / 281 full core** tests passing; the full run used prepared Python **3.12.14**. The focused run's exact interpreter/version was not retained. Original stdout was not saved; a retrospective tool-result receipt records those limitations. This is separate from final-image host proof.
- The final frozen image passed **651 tests and 164 subtests**, with **20 skipped**, two dependency deprecation warnings and exit zero in **276.57 seconds**, using an isolated test database and read-only tests. Earlier stale-label failure receipts are retained.
- All four deployed services match the final image, 106 runtime hashes, versions and native scanner modules. Deployment had no active jobs; verification found zero restarts/OOM. Local/build/service identities match for the R6 archive, loaded private pricing document and material catalogue without publishing private contents.
- Existing 100-estimate input/result snapshots and cached viewer geometry are unchanged, with no whole-corpus rescan or new quote saved. Current first-page monetary amounts match prior reports.
- Production-font PDFs comprise **9 customer / 12 admin pages**, versus the previous 10/14. All 21 pages were rendered and visually inspected: zero out-of-page characters, two images per report, candidate 4's distinct **13.09 mm² bending / 12.51 mm² axial** areas, **1.80 N** with gravity-equivalent units, top local-analysis notice and audience boundaries. This is one live fixture, not proof for every possible report input.
- Actual browser inspection confirmed H2C/Vortek commands 280/110/65 °C, six selected candidates, first 25 mm reference **183 g / 1.80 N**, candidate 4's axial area label and expandable process/distance details. Captured errors/warnings and candidate-region horizontal overflow were zero. Copy explicitly scopes selection to maximum six spatial windows and ordering to comparable selected 25 mm scenarios, not all weaknesses or physical failure order.
- Seven local alternating-order pairs on the same 100-estimate snapshot gave median encoding times of **0.8870276000 → 0.1746041000 s**, an **80.3158% elapsed reduction**. Both paths exactly matched the original **14,437,579-byte** response, SHA-256 `96419583b33b8c4cbc641bb680f046c4271bb208ff75bb42a3953c56417048cd`. This Python 3.12 encoding benchmark excludes database, LAN, browser parsing and rare legacy fallbacks; it is not a whole-system speed percentage or tail-SLA guarantee.

Frozen identity: `3a418320a51d42cb4adce75477804b7e473e36755271f254b09f5bb0f13655d4`; image: `sha256:a73bb812da32e4b68a91257d4144dac9b02ed77671f1b6e830edfc67eeb2ea84`. G-code **v0.28.0** and quote **v0.13.0** are unchanged.

The same **72 read-only GET** schedule was measured before/after: eight serial requests per endpoint, sixteen per endpoint at mixed concurrency four. Both snapshots had zero errors; p95 was recomputed from preserved raw rows using nearest rank. History medians were **2.5340 → 1.2974 seconds serial (48.80%)**, and **9.0129 → 2.3505 seconds mixed (73.92%)**. Mixed maximum/p95 values were config **0.540 seconds**, viewer **1.317 seconds**, history **4.355 seconds**. Large-history latency remains, and config's median increased **0.0571 → 0.2633 seconds**. This is not an all-endpoint improvement claim, controlled paired-load experiment, whole-system percentage or tail-SLA certification; live LAN/load were uncontrolled.

The narrow candidate pane measured 515px with three approximately 156.9px cards: expanded technical copy remains too dense despite no horizontal overflow. Responsive presentation and large-history payload/latency remain follow-ups.

The [material review](material-evidence-review-20261007.md), [fracture review](fracture-evidence-review-20261007.md) and [D01 supporting qualification](d01-supporting-data-qualification-20261007.md) retain the physical evidence gaps. D01's supporting payload and 35 settings were inspected; raw CSV units, gauge area and first-failure endpoints remain unqualified. No calibrated physical accuracy, safe design load, patentability or commercial certification is established.
