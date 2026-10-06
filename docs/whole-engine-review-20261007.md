# 엔진 전체 재검토와 연구 근거 — 2026-10-07

## 한국어

이번 검토는 강도 엔진의 소재 참조·공정 맥락·단면 역학·층간 접촉·취약 후보 순위와 이를 연결하는 웹·보고서·캐시를 다뤘다. G-code와 가격 엔진의 연결은 통합 시험으로 점검한다. 기존 전체 파일군 검증을 반복하지 않고 새로 재현된 오류와 부족한 1차 자료를 검토했다.

**강도 v0.23.0은 재현된 소프트웨어 오류를 수정한 개정이다. 실제 부품의 최초 파단 하중·위치에 대한 정확도 인증은 아니다.** 제조사 참고응력, 명령 기반 기하학, 조건부 하중과 실제 파단 시험은 구분한다. 등록 소재 18개에 승인된 범용 공정 전이 모델 및 독립 외부 부품 검증은 여전히 없다. 특허 가능성을 평가하거나 확인한 작업도 아니다.

### 구성별 검토 결론

|구성|입력과 담당 범위|이번 결론|
|---|---|---|
|G-code v0.28.0|활성 tool·프로파일·모달 이동·E·선폭·층 높이·온도·속도·팬·벽/인필 등의 명령 해석|명령값을 실측 압출량·계면 온도·완전 접합으로 바꾸지 않는다. 기존 전체 원본/플레이트 검증을 재사용한다.|
|강도 v0.23.0|원자료 참고응력, 선언/명령 체적 단면, 조건부 정상응력·인장/굽힘 하중, 끝 연결부와 층 접촉 관찰|아래 다섯 오류를 수정했다. 100% 속 찬 외형을 대신 쓰거나 공정 변수를 임의 배율로 곱하지 않는다.|
|가격 v0.13.0|사용 소재·중량·가격정책·시간·전력·세금·할인·반올림|강도 참고값이나 위험 순위를 소재 가격으로 전이하지 않는다. 가격 엔진 코드는 이번 개정에서 변경하지 않았다.|
|PrintOps v0.5.21-strength-review|소스 식별, 작업·캐시, 뷰어·웹·관리자/거래처 보고서|강도 패키지를 동기화하고 캐시 검증에 동일 단면 증명 검사를 적용한다. 기존 견적 원본은 변경하지 않는다.|

### 재현해서 수정한 오류

|문제|재현과 수정|검증 의미|
|완전 층 접촉 단절 경고 누락|충분한 면적·양쪽 깊이를 가진 인접한 내부 계면의 겹침이 0이어도 주변 반복성 조건 때문에 경고가 빠졌다. 적격한 완전 단절은 즉시 경고하며 부분 감소의 반복성 규칙은 유지한다.|접촉 기하학 경고 수정이며 접합강도 또는 파단하중을 새로 측정한 것은 아니다.|
|서로 다른 레이어의 반복 Z를 완료 처리|다른 layer ID가 같은 Z 평면에 있으면 writer가 `COMPLETE`를 냈지만 reader 검증에는 실패했다. 평면 정체성이 모호하면 `WITHHELD`로 일치시켰다. 같은 레이어 중복 경로의 union은 유지한다.|원본 명령의 계면 대응을 확정할 수 없는 경우를 구분한다.|
|모순된 캐시 단면계수 통과|정상 단면의 JSON 사본에서 관성·면적은 그대로 두고 단면계수만 1.5배 바꾸면 참고 굽힘 하중이 50% 올라갈 수 있었다. 경계 support hull을 보존하고 관성·주축·모든 방향 단면계수·최약 응력 방향을 재검산한다. 단위가 있는 값의 비교는 작은 형상에서도 비율 오차를 검사한다.|정상 원본에서 같은 계산 오류가 발생한 증거는 없다. 검사는 내부 산술 정합성에 한정되며 함께 위조한 소스·기하학이나 실제 비드·접합을 인증하지 않는다.|
|끝단 반전 시 연결부 설명 불일치|X 반전 형상의 실제 선택 뿌리 면적은 같아도 설명용 면적비와 분류가 달랐다. 설명 통계도 실제 선택한 단면 구간에서 계산하도록 수정했다.|선별 설명의 반전 불변성을 회복했다. 실제 파단 위치 검증은 별도다.|
|불리언 참고응력을 1 MPa로 수용|명시적 하중 검토에서 `true`가 부동소수점 1로 변환됐다. 참고응력 비교는 보류하며 유효한 기하학 정상응력 계산은 유지한다.|잘못된 재료 입력을 수치로 만들지 않는다.|

새 계약은 `LOCAL_DECLARED_ROAD_SECTIONS_V3_BOUNDARY_SUPPORT_PROOF`, `LOCAL_DECLARED_INTERLAYER_CONTACT_V3_ZERO_OVERLAP_PLANE_IDENTITY`, `LOCAL_OUTER_ENVELOPE_V7_SELECTED_TERMINAL_ROOT_METADATA`다. 이전 단면 캐시는 새 기하학 증명 없이 재사용하지 않는다. 원본이 있는 뷰어를 다시 준비할 때 필요한 평가만 갱신한다.

### 논문과 원자료를 어떻게 검토했는가

재료 검토 12개 DOI 항목과 층간 접합·파괴 검토 23항목을 정리했다. 일부 기존 전문 감사는 재사용했고, 접근 가능한 새 전문·Methods·표·데이터 목록을 확인했다. 항목 수는 독립 실험 수가 아니며 모든 출판 논문을 망라했다는 뜻도 아니다. 자세한 출처·조건·접근 수준과 미확인 항목은 [재료 근거표](material-evidence-review-20261007.md), [층간 접합·파괴 근거표](fracture-evidence-review-20261007.md), [출처 메타데이터](research-provenance-20261007.json)에 있다. 저작권 원문·개별 곡선·이미지는 공개 저장소에 복제하지 않았다.

핵심 판단은 다음과 같다.

- **명령 유량은 실측 유량이 아니다.** [Read·Seppala의 계측 연구](https://link.springer.com/article/10.1007/s40192-024-00350-w)는 실제 feed·직경·압력·slip을 계측한다. [NIST AM Bench](https://www.nist.gov/ambench/direct-am-bench-data-links-and-referencing-guidance)는 AMB2022-06의 체적유량 측정·안정성 문제로 PC/PLA 결과 출판을 계획하지 않는다고 명시한다. G-code E를 실측 성공으로 표시할 수 없다.
- **유량·온도·속도의 효과는 공통 선형 배율이 아니다.** [Lambiase 2024](https://link.springer.com/article/10.1007/s00170-024-14079-5)의 PLA DCB 조건에서는 flow 증가가 Mode I 저항을 낮춘 경우도 있다. 시험 불능을 표에서 0으로 기록한 값은 실제 파괴에너지 0으로 학습하지 않는다. 굽힘·인장·Mode I/II/III·초기/전파 저항도 서로 대체하지 않는다.
- **문헌 내 충돌과 중복을 보존한다.** ABS 계열 세 논문의 반복 집계와 상충 공정 정보, PPS/rCF의 초록/표 차이, fracture 논문의 단위·SD 설명 충돌을 분리했다. DOI가 다르다는 이유로 같은 관측 계보를 학습과 외부 검증에 나누지 않는다.
- **시험온도와 출력온도는 별개다.** [PA6-GF 연구](https://dergipark.org.tr/en/pub/iarej/article/862304)는 단유리섬유 PA6의 시험온도 연구다. 기존 문서의 연속 GF 암시를 수정했다. PA12-CF/PPA-CF 시험온도별 응력도 노즐온도 보정계수로 사용하지 않는다.
- **높은 겹침률도 강한 접합을 입증하지 않는다.** 실제 bonded 면적·열이력·void·노치·균열 경로와 fixture가 필요하다. 자유 끝 층 분리·박리·피로·크리프 등의 하중은 현재 단면 인장/굽힘 참고값으로 해결하지 않았다.

### 취약 후보 순위와 상용 검증의 경계

현재는 최대 여섯 개 국부 후보를 선별한다. 같은 소재 전이와 단면 모델을 가진 후보는 **동일 25 mm 가상 거리의 굽힘 참고하중**으로 비교하고, 비교 조건이 없으면 기하학 순위를 유지한다. 실제 고정점·하중 경로를 확인한 전체 부품의 최초 파손 순위가 아니다. 후보 선별 후 원본 경로 단면을 정밀화하지만 전체 부품의 모든 파괴 모드에 대해 다시 전역 최솟값을 찾는 구조도 아니다.

자동 참고하중은 시편/소재 참고응력을 균질한 G-code 순경로 단면 응력으로 전이하는 가정을 기록하며 `verified=false`다. 원자료의 응력 면적이 미상이면 `UNKNOWN`을 유지한다. 명시적 하중 검토의 재료 순단면 응력과 직접 비교하려면 대응하는 `NET_MATERIAL` 면적 근거가 필요하다.

상용 예측으로 승인하려면 정확한 grade·lot·conditioning·측정 면적과 raw 하중/변형 곡선이 연결되어야 한다. 대상 끝단/뿌리 형상에서 fixture·lever arm·최초 균열 위치·파괴 모드를 기록하고, 실험 계보·batch 전체를 학습/검증에서 분리한다. 공개 G-code, IR, 출력 성공/실패 라벨만으로 기계적 파단 정답을 만들지 않는다. 초기 시험 수 제안은 표본 충분성이나 안전 하한의 증거가 아니다.

승인 지표는 시험 전에 정한 하중 오차·편향·위치 오차·위험 영역 precision/recall·예측구간 coverage와 보류 조건이다. 같은 자료를 다시 맞춘 결과나 성공한 소프트웨어 시험을 예측 정확도로 표현하지 않는다. 현 단계는 조건부 하중·기하학 선별을 제공하는 소프트웨어이며, 검증된 안전 설계 하중을 제공한다고 주장하지 않는다.

### 이번 실행의 검증 기록

수정 전 강도 전체 시험은 244개 통과했다. 새 결함을 회귀시험으로 재현한 뒤 수정했고, 최종 강도 전체 **258개**와 단면 증명/호스트 캐시 집중 **10개**가 통과했다. 독립 기하학 수식 검토에서도 회전·이동한 합성 단면 60건이 통과했다. 서로 겹치는 시험 수는 더해서 별도 검증 수로 표현하지 않는다.

소스를 고정한 운영 이미지 통합 시험은 **638개 통과·20개 건너뜀·164개 세부 검사 통과**였다. 건너뛴 검사는 통과한 것으로 계산하지 않는다. api·analysis·viewer·worker 네 서비스가 같은 이미지와 소스, 강도 v0.23.0을 실행하며 재시작 0회·OOM 없음도 확인했다. 이미지 식별자는 `sha256:d18da3b61ad99b5197ff11feeb4e27d1837fac54fc52f53222e1c85d0c9b0b82`다.

실제 저장 G-code 원본 **51,010,921 bytes**의 SHA-256·3MF member·전체 스캔 완료·현재 단면/접촉 계약·여섯 후보를 확인했다. 새 계약으로 한 번 재분석한 시간은 **117.84초**였으며, 이전과 동일한 반복 실험이 아니므로 성능 향상 지표로 사용하지 않는다. 이 파일의 동일 25 mm 조건부 굽힘 참고값은 약 **1.80 / 2.06 / 2.18 / 2.33 / 4.18 / 4.49 N**이다. 실제 파단하중이나 계면 접합강도로 실증한 값은 아니다.

운영 서비스가 생성한 거래처용 PDF 10쪽과 관리자용 PDF 14쪽의 전 페이지를 렌더링해 확인했다. 원본 경로 이미지·로컬 처리 고지·힘 단위·관리자 정보 구분·페이지 범위 검사를 통과했다. 선언 단면과 명령 체적 등가 단면의 하중은 서로 다른 가정이며 같은 계산을 중복한 값이 아니다. 좁은 표에 상세 가정이 많아 거래처용 가독성을 더 개선할 항목은 남아 있다. 뷰어와 보고서 생성 전후 저장 견적 **100건의 내용 해시가 동일**했다. 전체 과거 코퍼스 재스캔은 수행하지 않았다.

## English

This review covers material references, process context, section mechanics, interlayer geometry, local candidate ranking, and the web/report/cache integration. Existing full-corpus evidence is reused. Strength **v0.23.0** fixes demonstrated software defects; it does not certify first-fracture load/location accuracy, commercial prediction readiness, or patentability. G-code remains **v0.28.0**, pricing **v0.13.0**, and the host becomes **v0.5.21-strength-review**.

Five defects were reproduced and corrected: missing qualified zero-overlap interface warnings; ambiguous repeated Z planes falsely marked complete; inconsistent cached moduli capable of raising a conditional force by 50%; reflected terminal-root explanatory metadata using the wrong interval; and boolean material stress accepted as 1 MPa. New cached section support witnesses allow recomputation of inertia-derived moduli and critical directions. Dimensional comparisons use relative tolerances even at small scales. These checks establish internal arithmetic consistency, not source authenticity, physical bead shape, or weld resistance.

The [material review](material-evidence-review-20261007.md), [fracture review](fracture-evidence-review-20261007.md), and [provenance registry](research-provenance-20261007.json) distinguish full-text checks, reused audits, abstracts, missing metadata, aggregate versus specimen outcomes, experimental lineages, units, grades and property endpoints. Twelve material DOI records and 23 fracture-paper records are not independent campaign counts or an exhaustive systematic review. Licensed source files are not reproduced here.

Measured flow and interface thermal histories cannot be invented from G-code commands. Nonmonotonic flow/thermal interactions, uncomputable tests reported as zero, conflicting paper tables, and repeated observations across publications prevent universal multiplier fitting. Tensile, flexural, shear and mode-specific fracture responses, gross/net/bonded area, chopped/continuous reinforcement, and printing/test temperatures remain separate.

Ranking is among at most six retained local candidates under compatible 25 mm reference bending scenarios, otherwise geometric screening order. It is not a whole-part first-failure analysis across all mechanisms. Grade-matched raw specimen outcomes, fixtures, first-crack location/mode and independent batch/lineage holdouts are required before making calibrated part-prediction claims. Proposed pilot sample counts do not establish adequate tail reliability or safe allowable loads.

Automatic reference loads explicitly assume coupon/reference stress as homogeneous net-road-section stress with `verified=false`; an unknown source area basis stays `UNKNOWN`. Explicit-load stress equality requires matching `NET_MATERIAL` reference evidence.

Baseline strength tests: **244 passed**. Final strength suite: **258 passed**. Focused core/host cache checks: **10 passed**. An independent synthetic section probe accepted **60/60** rotated/translated cases. Overlapping suites are not summed into independent evidence.

Frozen-image integration: **638 passed, 20 skipped, 164 subtests passed**; skips are not passes. All four deployed services run the same checked image/source with strength v0.23.0, zero restarts and no OOM. Image: `sha256:d18da3b61ad99b5197ff11feeb4e27d1837fac54fc52f53222e1c85d0c9b0b82`.

One existing **51,010,921-byte** G-code source was refreshed under the new contracts in **117.84 seconds**; SHA-256, archive member, complete scans and all six candidates were verified. This is not a paired speed benchmark. Its conditional 25 mm bending references are approximately **1.80 / 2.06 / 2.18 / 2.33 / 4.18 / 4.49 N**, not empirical failure or weld-resistance labels.

The deployed service generated a 10-page customer PDF and a 14-page administrator PDF. All pages were rendered and checked for page bounds, source-path images, local-processing notice, units and audience separation. Declared-road and commanded-volume-equivalent forces are distinctly labeled scenarios, not duplicate stale results. Dense customer-table presentation remains a usability improvement item. The complete contents of **100 saved estimates** remained unchanged across viewer/report preparation. No historical corpus rescan was performed.
