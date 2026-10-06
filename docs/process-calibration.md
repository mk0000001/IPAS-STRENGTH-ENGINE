# 공정 근거와 보정 검증 / Process evidence and calibration audit

## 한국어

`process_adjustment(analysis, directional_mpa, *, reference_context=None,
target_context=None, calibration_id=None)`는 기존 참고값과 미보정 상태를
유지한다. 추가된 `calibration` 결과는 누락된 조건, 불일치, 승인되지 않은
모델 ID, 미확인 실제 소재 등급, 노즐 직경으로 대신한 선폭을 구체적으로
기록한다. 현재 승인된 공정 전이 모델은 없으며 `effective_mpa`는 null이다.
아래 공개 자료와 소프트웨어 테스트는 임의 부품의 강도 정확도를 입증하지 않는다.

`material_factors()`에도 `calibration`과 `evidence_coverage`가 있으므로
방향별 참고응력이 없는 소재도 자료와 공백을 표시할 수 있다. runtime은
두 범위를 분리한다. `curated_numeric_catalog`는 요청한 물성에 맞는 엔진
수치 관측값이며, `researched_comparison_evidence`는 여러 물성을 포함한
소재 계열별 문헌 검토다. 새로운 ABS/PETG/PPA-CF 비교 문헌을 자료 없음으로
표시하지 않으면서도 전단·최대하중·시험온도 자료를 인장 공정 보정으로 승격하지
않는다. 후보 출처가 있다는 사실도 검증된 수치행이 있다는 뜻은 아니다.

`registered_material_coverage`는 등록된 18개 소재 계열 전체를 제공한다.
이번 검토에서 비교 근거가 있는 6개는 PLA, PETG, ABS, ASA, PPA-CF, PC이며
나머지 12개는 `INSUFFICIENT`다. ASA-CF와 PEI의 기존 엔진 수치 자료는
이 18개 등록 계열 목록과 별도로 유지한다. 각 행에 출처 URL과 제한 사유가
있으며 `research_manifest`에는 원본 coverage/manifest 해시가 있다.
`research_coverage_catalog()`는 원본 취득자료 해시까지 포함한 전체 복사본을
반환한다. 승인된 공정 보정 모델은 모든 계열에서 0개다.

호출 측의 `reference_product`, `source_ref`, `raw_reference_mpa`,
`test_conditions`, `internal_conservative_factor`를 받을 수 있다.
원래 context는 보존하고 시험조건은 별도의 `reference_matching_context`에
펼친다. 제조사 제품명은 원자료 시편을 설명할 뿐 사용자의 실제 스풀을
인증하지 않는다. 1이 아닌 내부 여유계수는
`REFERENCE_CONTAINS_UNVALIDATED_INTERNAL_MARGIN`으로 표시하며 실측 허용응력으로
취급하지 않는다. 따라서 기존 0.85를 검증된 허용값으로 소비하지 않는다.

출처와 목표를 비교하려면 독립적으로 확인한 `material_family`,
`material_grade`, `property`, `orientation`, `stress_area_basis`,
`test_standard`, `moisture_condition`, `annealing`, `printer`,
`nozzle_diameter_mm`, `layer_height_mm`, `line_width_mm`, `nozzle_c`,
`bed_c`, `chamber_c`, `fan_percent`, `speed_mm_s`, `speed_basis`,
`infill_percent`, `pattern`, `walls`, `raster_angles_deg`, `flow_ratio`가
필요하다. 시험조건에는 `test_temperature_c`, `test_relative_humidity_percent`,
`crosshead_speed_mm_min`, `conditioning_duration_h`가 포함된다.
시험온도는 노즐온도가 아니며 미상 값은 미상으로 남긴다.
`grade_identity_verified`는 외부 확인의 표시로, 프로파일 이름에서 추론하지
않는다. 추가 context는 G-code 관측과 충돌하는 값을 덮어쓰지 못한다.
명령 이동속도의 중앙값과 논문 출력속도 설정을 구분하고, XY/Z 재분류·다른 등급
전이·응력 면적 기준 변환을 자동 적용하지 않는다.

### 공개 데이터 계산과 적격성 재현

기존 검증된 Zenodo 추출자료에서 ASA/ASA-CF 인장 시편 18개, 소재·raster
그룹 6개, 관련된 실험 캠페인 2개를 추가했다. 원본 workbook/sheet/cell,
파일 해시, 실제 최대하중과 단면적, 시편 응력, 그룹 평균과 표본 표준편차를
보존한다. 논문과 대응 데이터셋은 같은 계보이며 각 등급은 캠페인 1개뿐이다.
독립 실험실 재현이나 공정 보정을 의미하지 않는다.

```console
python -m print_strength_engine.public_validation --output docs/public-process-calibration-audit-20261001.json
```

명령은 저장된 추출값의 계산과 보정 적격성을 검사한다. XLSX를 다시 내려받아
원시 곡선을 재추출하는 작업은 아니다. 보고서에서 18개 최대하중/면적 계산과
6개 그룹 통계가 일치하며, batch·조습·공정 metadata 누락은 제외 사유로 남는다.
원출처는 [ASA 데이터](https://zenodo.org/records/14065523),
[ASA 논문](https://doi.org/10.3390/ma17215207),
[ASA-CF 데이터](https://zenodo.org/records/14882928),
[ASA-CF 논문](https://doi.org/10.3390/jcs9040185)이다.
취득·검증 범위의 제한은 `research-evidence.md`에 기록되어 있다.

### 이후 후보 모델 검증

`validate_linear_candidate(records, variable=...)`는 사전에 정한 단일 변수의
최소제곱 선형 모델을 학습 데이터 평균 baseline과 비교한다. 정한 변수 이외의
등급·물성·방향·조습·공정은 일치해야 한다. 계보·batch·조건 안의 반복 시편은
평균하여 평가하며 평가할 계보가 최소 3개 있어야 계보 전체를 하나씩 제외하는
holdout을 실행한다. caller-only 진단은 동일 study ID나 정확히 같은 원출처
시편을 다른 계보로 나누지 못한다. 출판물과 실험 캠페인의 관계는 아래 별도
관측 map으로 표현하며, 한 DOI에 여러 캠페인이 있을 수도 있다.
잘못된 입력은 전체 자료를 기각하며 불리한 행만 조용히 제외하지 않는다.
모든 holdout 조건은 학습 범위 안이어야 하고 모든 fold의 MAE가 baseline보다
작아야 한다. 1e-12 MPa 차이는 수치 반올림 동률 기준일 뿐 공학적
효과 기준이 아니다. RMSE도 기술통계로 보고한다.

```console
python -m print_strength_engine.calibration records.json --variable layer_height_mm --output candidate-audit.json
```

각 행에는 `sample_id`, `study_id`, `lineage_id`, `batch_id`, `source_url`,
`source_locator`, 양수 `value_mpa`와 위 조건을 담은 `context`가 필요하다.
새 ID만 부여해서 독립성을 만들 수 없다. 통과해도 출처·적용범위 심사를 위한
후보일 뿐 runtime 승인이 아니다. 단위 테스트용 합성값은 실제 근거 catalog에
들어가지 않는다.

### 출판물·캠페인·관측 출처 경계

감사 계약은 `PROCESS_CALIBRATION_AUDIT_V2_OBSERVATION_PROVENANCE`, 문헌 비교
계약은 `PRIMARY_LITERATURE_COMPARISONS_V3_OBSERVATION_PROVENANCE`다.
형상·capacity·G-code scanner 계약과 물리 계수는 변경하지 않는다.

`validate_linear_candidate(records, variable=..., provenance_map=None)`의
기존 caller-only 통계 상태와 계산은 유지한다. 이 경로는
`independence_status=CALLER_DECLARED_UNVERIFIED`이며 `experimental_lineages`는
호출자가 선언한 분리 그룹이다. `declared_lineages`, `canonical_campaigns`,
`publication_ids`를 별도로 보고한다. map 없이 추가한 canonical ID는 보존된
입력 metadata일 뿐 인증된 캠페인으로 세지 않는다. 모든 경로에서
`independent_validation_established=false`, `accepted_for_runtime=false`다.

선택적인 map은 `schema=PROVENANCE_OBSERVATION_MAP_V1`, 문자열 `map_id`,
`observations` 배열을 가진다. 각 항목의 `source_id`와 완전한
`source_locator`가 한 관측을 식별하며 `source_doi`도 일치해야 한다.
DOI의 링크 접두사·대소문자는 정규화하지만, DOI·저자·실험실·숫자 일치만으로
원 실험을 추론하지 않는다. archive 시편 locator는
`file#sheet!peak_cell`로 파일명까지 포함한다.

각 map 항목은 `review_locator`, `review_status`, `observation_kind`를
요구한다. `CURATED_IDENTITY`는 출처 검토자가 정한 `canonical_campaign_id`와
전역적으로 구분되는 `original_outcome_id`도 요구한다. 이 ID는 원시 시편 또는
원 aggregate outcome을 식별하며, 출판 alias마다 새로 만들어 독립성을
부여하는 라벨이 아니다. map의 서로 다른 출처가 같은 campaign을 가리키면
fold 전에 한 그룹으로 묶는다. 원 outcome을 다시 제출하면 값·sample ID가
달라도 거부한다. 같은 DOI 아래 서로 다른 검토된 campaign은 허용한다.

`observation_kind`는 `RAW_SPECIMEN`, `PUBLISHED_AGGREGATE`,
`DERIVED_SUMMARY`, `UNKNOWN` 중 하나다. map을 쓰는 specimen 감사는
`RAW_SPECIMEN`만 받는다. 알려진 aggregate/derived summary는 caller-only
감사에서도 거부하며 비교 catalog에는 그대로 보존한다. n은 미상이면 null,
알려졌으면 양의 정수이며 raw 시편의 n은 생략/null/1만 허용한다. 평균과 n을
가지고 가짜 시편 행을 확장하지 않는다. 같은 반올림 결과를 가진 독립 실험은
숫자 중복만으로 삭제하지 않는다.

`UNRESOLVED_IDENTITY` 또는 `UNRESOLVED_OVERLAP` 항목에는 canonical
campaign/specimen ID를 넣지 않는다. overlap은 `overlap_group_id`를 요구한다.
M05/M06/M07의 알려진 DOI는 반복 aggregate와 상충 조건이 있는 미해결 overlap으로만
표시하며 독립 검증 입력을 차단한다. 동일 시편임을 확정하거나 미상의 n을
상속하지 않고, 충돌한 평균·조건을 runtime으로 가져오지 않는다.
다른 출처가 사용하는 일반적인 `M05` 라벨만으로는 격리하지 않는다.

map의 모호한 중복 키, 원 outcome의 campaign 충돌, 잘못된 자료형·boolean
ID/n은 `INVALID_PROVENANCE_MAP`으로 차단한다. 누락된 map 관측이나 DOI/종류
충돌도 입력을 거부하며 caller label로 되돌아가지 않는다. map 없는 caller의
원 outcome label은 제공된 metadata로만 보존한다. 서로 다른 실험실의 로컬
`S1`을 같은 시편으로 취급하지 않는다. map 작성자는 로컬 시편 label을 출처
namespace로 구분한 전역 원 outcome ID를 부여해야 한다.
입력·map을 변경하지 않고 입력 metadata, 행별 검토 사유와 정렬된 JSON의
map SHA-256을 감사 결과에 보존한다.

`INTERNALLY_VALIDATED_METADATA`는 **map 내부 구조와 일관성을 검사했다는
뜻이며 외부 출처 진위·실험 독립성의 인증이 아니다.**
`source_authenticity_verified=false`는 map이 있어도 유지된다. map을 작성한
검토자의 출처 판단은 별도의 신뢰 경계이며 통계 후보 통과만으로 physical
accuracy나 runtime model을 승인하지 않는다.

`literature_comparisons()`와 `evidence_coverage()`도 선택적 map을 받을 수 있다.
출판 DOI 목록/수와 선언 또는 canonical campaign을 분리하며, campaign이
미상이면 DOI로 대신하지 않는다. catalog에 이미 적힌 계보는 선언된 metadata로
보존한다. 공개 ASA 보고서는 현재 기록된 두 계보를 distinct ID로 세지만
이를 출처 인증된 독립 실험 수로 보고하지 않는다. 수치·n·raw 시편 수는 바꾸지 않는다.

```console
python -m print_strength_engine.calibration records.json --variable layer_height_mm --provenance-map observation-map.json --output candidate-audit.json
```

### 실제 연구 내부 infill holdout 진단

[Scientific Reports 2024](https://doi.org/10.1038/s41598-024-79213-5)
보충 DOCX에는 인장 기록 180개가 있다. 별도 진단은 소재·패턴별 25%/75%
인필 시편 108개로 선형 후보를 학습하고, 50% 인필 9조건의 시편 54개를
모두 제외하여 평가한다. 100% lateral 패턴 18개는 대응 학습조건이 없어서
제외한다. 원본 소재 label `PTEG`는 임의로 등급을 바꾸지 않고 그대로 보존한다.
이 결과는 한 연구 안의 조건 holdout이며 **독립 연구 holdout 0개, 독립적으로
확인된 batch holdout 0개**다.

```console
python -m print_strength_engine.study_infill_diagnostic docs/public-infill-holdout-records-20261001.json --output docs/public-infill-holdout-diagnostic-20261001.json
```

후보의 시편 MAE는 0.8022530864 MPa, RMSE는 1.0997787025 MPa다.
학습 평균 baseline도 같은 오차다. 반복 수가 같고 25%/75%가 50%에서 같은
거리에 있어 선형 예측과 학습 평균이 수학적으로 같기 때문이다. 결과는
`NO_EVIDENCE_OF_IMPROVEMENT`이며 정확도 향상 주장이 아니다. holdout 결과를
본 뒤 모델을 바꾸지 않았고 runtime 계수도 승인하지 않았다. 소재 등급과
응력 면적 기준이 충분히 확립되지 않았으며 논문 층높이 표기도 상충한다.
제조사 참고값이나 임의 부품의 강도 인증에 사용할 수 없다. 입력 기록은 원본
표 해시, 정확한 행, 원래 소재·패턴 label, 시편 ID를 보존한다.

---

## English

### Process evidence and calibration audit

`process_adjustment(analysis, directional_mpa, *, reference_context=None,
target_context=None, calibration_id=None)` preserves its existing reference
values and uncalibrated status. Its additive `calibration` result explains
missing metadata, incompatible context, unsupported model IDs, unverified
target grades and nozzle-derived line-width proxies. There are currently no
reviewed runtime transfer models; `effective_mpa` remains null. Neither the
public data below nor the test fixtures establish arbitrary-part accuracy.

`material_factors()` also returns `calibration` and `evidence_coverage`, so a
caller without directional reference values can still show evidence and gaps.
Coverage separates `curated_numeric_catalog` (property-filtered engine numeric
observations) from `researched_comparison_evidence` (family-level research across
multiple properties). Newly reviewed ABS/PETG/PPA-CF sources are therefore not
reported as absent, but shear, load and test-temperature observations cannot
be promoted to tensile process calibration. Candidate source URLs do not imply
verified numerical rows.

`registered_material_coverage` includes all 18 registered families. Six have
comparison evidence in this review: PLA, PETG, ABS, ASA, PPA-CF and PC. Twelve
remain `INSUFFICIENT`. ASA-CF and PEI numeric catalog observations are retained
separately from the 18-family registry. Each row includes source URLs and its
limitation. `research_manifest` provides original coverage/manifest hashes;
`research_coverage_catalog()` returns a copy of the full matrix with acquisition
hashes. Every family still has zero approved process transfer models.

The optional reference context accepts the host's `reference_product`,
`source_ref`, `raw_reference_mpa`, `test_conditions` and
`internal_conservative_factor`. Test conditions are flattened into a separate
`reference_matching_context`; the original is preserved. A reference product
name identifies only the source material, never the user's spool. An internal
factor other than one is marked `REFERENCE_CONTAINS_UNVALIDATED_INTERNAL_MARGIN`
and never treated as a measured allowable.

For meaningful source/target matching, provide independently established
`material_family`, `material_grade`, `property`, `orientation`,
`stress_area_basis`, `test_standard`, `moisture_condition`, `annealing`,
`printer`, `nozzle_diameter_mm`, `layer_height_mm`, `line_width_mm`, `nozzle_c`,
`bed_c`, `chamber_c`, `fan_percent`, `speed_mm_s`, `speed_basis`,
`infill_percent`, `pattern`, `walls`, `raster_angles_deg` and `flow_ratio`.
Test context also requires `test_temperature_c`,
`test_relative_humidity_percent`, `crosshead_speed_mm_min` and
`conditioning_duration_h`. Test temperature is never treated as nozzle temperature.
Unknown values must remain unknown. `grade_identity_verified` is an external
attestation, not a conclusion derived from a profile name. Supplied context
cannot overwrite conflicting G-code observations. Commanded-move median speed
is explicitly distinct from a study's print-speed setting. No XY/Z remapping,
cross-grade transfer or stress-area conversion is implicit.

## Reproducible public-data audit

The catalog adds ASA and ASA-CF tensile comparisons from the existing checked
Zenodo extraction: 18 specimens, six material/raster groups and two related
experimental campaigns. It retains original workbook/sheet/cell identifiers,
raw-file checksums, measured peak loads and areas, specimen stresses, group
means and sample standard deviations. The paper and corresponding dataset are
one lineage, and each grade still has only one campaign. It does not establish
independent laboratory replication or a process calibration.

```console
python -m print_strength_engine.public_validation --output docs/public-process-calibration-audit-20261001.json
```

This command checks the arithmetic of the saved extraction and audits its
calibration eligibility. It does not redownload or re-extract the XLSX files.
The saved report confirms all 18 peak-load/area and six group-statistic
calculations, while recording missing batch/conditioning/settings metadata.
The audit does not promote incomplete evidence to an empirical model.

Primary provenance: [ASA dataset](https://zenodo.org/records/14065523),
[ASA paper](https://doi.org/10.3390/ma17215207),
[ASA-CF dataset](https://zenodo.org/records/14882928),
[ASA-CF paper](https://doi.org/10.3390/jcs9040185).
Source details and acquisition limits remain in `research-evidence.md`.

## Evaluating a future candidate

`validate_linear_candidate(records, variable=...)` evaluates a prespecified,
single-variable ordinary least-squares candidate against the training-only
mean. It requires one exactly matched grade/property/orientation/conditioning
and process stratum, except the named variable. Replicates are averaged within
lineage, batch and condition. At least three evaluation groups are required
for leave-one-lineage-out evaluation. Caller-only diagnostics reject a split of
one study ID or an exactly identified source specimen. A publication can contain
multiple campaigns; an observation map represents that relation. Input errors reject the dataset rather than
silently dropping unfavorable rows. Every held-out condition must be inside
the training domain, and every fold must have lower MAE than the mean baseline.
Reported RMSE is additional descriptive information.

```console
python -m print_strength_engine.calibration records.json --variable layer_height_mm --output candidate-audit.json
```

Records require `sample_id`, `study_id`, `lineage_id`, `batch_id`, `source_url`,
`source_locator`, positive `value_mpa` and a `context` with the matching fields
listed above. Callers must trace experimental lineage to the source; assigning
new labels cannot create independence. A passing result is a candidate for
source and scope review, not runtime authorization. Synthetic unit-test data
exercise these mechanics and are never included in the public evidence catalog.

## Publication, campaign and observation provenance

The audit contract is `PROCESS_CALIBRATION_AUDIT_V2_OBSERVATION_PROVENANCE`;
the comparison contract is `PRIMARY_LITERATURE_COMPARISONS_V3_OBSERVATION_PROVENANCE`.
Geometry, capacity and scanner contracts and physical coefficients are unchanged.

The optional `provenance_map` argument adds observation identity checks without
changing the fitting method. Existing caller-only statistical status and
calculations remain available, explicitly marked
`independence_status=CALLER_DECLARED_UNVERIFIED`. In that mode the legacy
`experimental_lineages` field contains declared split groups, not authenticated
experimental independence. The report separately lists `declared_lineages`,
`canonical_campaigns` and `publication_ids`; a caller-supplied canonical label
without a map remains unverified input metadata.

A map has `schema=PROVENANCE_OBSERVATION_MAP_V1`, a nonempty string `map_id`
and an `observations` array. Each observation requires `source_id`, normalized
`source_doi`, a fully identifying `source_locator`, `review_locator`,
`review_status` and `observation_kind`. Lookup uses source ID and locator with
a matching publication DOI; it never guesses campaign identity from numerical
equality, DOI alone, authors or laboratories. Archived workbook locators include
the filename as `file#sheet!peak_cell`.

`CURATED_IDENTITY` additionally requires a `canonical_campaign_id` and a globally
scoped `original_outcome_id` assigned by the source reviewer. Different paper or
archive aliases of one campaign are grouped before folds are formed. Repeated
submission of one original outcome is rejected even if sample labels, rounding
or recomputed values differ. Different campaigns in the same publication are
allowed. A source map establishes only internally consistent declared identity
metadata; `INTERNALLY_VALIDATED_METADATA` does **not** authenticate source truth
or certify independent experimental validation. Its normalized JSON hash and
review locators make that trust boundary auditable. Caller map flags cannot
change `source_authenticity_verified=false` or
`independent_validation_established=false`.

Kinds are `RAW_SPECIMEN`, `PUBLISHED_AGGREGATE`, `DERIVED_SUMMARY` and `UNKNOWN`.
Mapped specimen audits require raw specimens. Explicit aggregates/derived
summaries are excluded from specimen audits even in legacy mode, while remaining
available as comparison evidence. A catalog aggregate cannot be relabeled as a
raw specimen by its map. Unknown n remains null; known n must be a positive
integer, and a raw specimen accepts only omitted/null/1. No n-based fake
specimen expansion occurs. Independently identified campaigns may have identical
rounded results; numeric-only deduplication would be incorrect.

Unresolved identity entries carry no canonical campaign or original specimen
ID. `UNRESOLVED_OVERLAP` requires an `overlap_group_id`. The known DOIs of M05/M06/M07 are flagged
only as unresolved aggregate overlap/context conflicts; they cannot establish
independent holdouts, even if a supplied map asserts a curated identity. This
does not prove identical specimens, inherit unknown n, or import conflicting
means into runtime. Map conflicts, ambiguous keys, invalid types/boolean IDs/n,
unmapped observations and DOI/kind conflicts fail closed. They do not fall back
to caller labels or silently discard unfavorable rows. Inputs are not mutated;
row provenance and extra legacy source metadata remain visible in the report.
Generic source labels such as `M05` do not quarantine unrelated publications.
Legacy origin labels remain provided metadata; an unqualified local `S1` in two
laboratories is not inferred to be the same specimen. Map reviewers must assign
globally scoped origin IDs, including an appropriate source namespace for local
labels. This internal namespace contract does not authenticate source truth.

`literature_comparisons()` and `evidence_coverage()` accept the same optional map.
They preserve declared catalog campaign IDs, report publication identities
separately, and leave unknown campaign identity unknown instead of substituting
DOI. `public_data_report()` counts distinct recorded campaign IDs rather than
catalog entries as experiments; its current two campaign identities remain
catalog declarations. Values, unknown n and raw specimen counts are unchanged.
Statistical passage never installs a model: `APPROVED_MODEL_IDS` is empty and
`accepted_for_runtime=false` on every path. Independent destructive outcomes
for the actual target part are still required before physical-accuracy claims.

## Actual within-study infill holdout diagnostic

The newly acquired supplementary DOCX for
[Scientific Reports 2024](https://doi.org/10.1038/s41598-024-79213-5)
contains 180 tensile records. The separate diagnostic uses 108 specimens at
25%/75% infill to fit a linear candidate within material/pattern, holding out
all 54 specimens at 50% across nine conditions. Eighteen 100% lateral-pattern
specimens are excluded because that pattern has no matching training levels.
The source label `PTEG` is retained verbatim rather than silently changing grade
identity. These are condition holdouts in one study; they are **zero independent
study holdouts and zero independently identified batch holdouts**.

```console
python -m print_strength_engine.study_infill_diagnostic docs/public-infill-holdout-records-20261001.json --output docs/public-infill-holdout-diagnostic-20261001.json
```

Candidate specimen MAE is 0.8022530864 MPa and RMSE is 1.0997787025 MPa.
The training-mean baseline has the same error: equal replicate counts and
equidistant 25%/75% endpoints make the linear prediction at 50% algebraically
identical to that baseline. The outcome is `NO_EVIDENCE_OF_IMPROVEMENT`, not an
accuracy improvement. The model was not changed after inspecting the held-out
outcomes. No runtime coefficient is accepted. Grade and stress-area definition
remain insufficiently established, while the paper reports inconsistent layer
heights; this study cannot authenticate manufacturer references or arbitrary
part strength. The saved input records retain the source-table hash, exact
table row, original material/pattern labels and specimen IDs.
