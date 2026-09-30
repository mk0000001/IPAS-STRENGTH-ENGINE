# Process evidence API

[한국어](#한국어) · [English](#english)

## 한국어

현재 계약은 `process.VERSION = GCODE_PROCESS_EVIDENCE_V3_THERMAL_CONTEXT`다. V2에서 범용 속도·층 높이 감쇠계수를 철회했고 V3는 도구별 온도·유량 문맥을 보존한다. 문헌의 시험편에서 대상 부품으로 전이할 보정식은 검증되지 않았다. 출처와 제한은 [연구 근거](docs/research-evidence.md)에 정리했다.

2026-10-01: [소재별 연구 범위와 공정 보정 승인 조건](docs/process-calibration.md)을 추가했다. 수치 catalog와 추가 검토 논문을 별도로 표시하며, 연구 계보 단위 분리·면적 정의·등급·시험 조건을 충족하지 않으면 보정식 적용을 보류한다. 공개 시편 180개를 사용한 진단에서도 정확도 향상이 입증되지 않아 승인 모델은 0개다.

`process_adjustment(analysis, directional_mpa, *, reference_context=None)`는 두 위치 인자를 유지하고 다음 값을 반환한다.

- `status: UNCALIBRATED_PROCESS_MODEL`, `factor_status: NOT_APPLIED`, `is_prediction: false`.
- `reference_mpa`: 입력 X/Y/Z를 수치 변경 없이 문자열로 보존한다.
- `effective_mpa: null`, `adjusted: false`, `applied: []`.
- `factors: {X: 1, Y: 1, Z: 1}`은 호환용 표시다. 서로 다른 설정에서 같은 강도라는 예측이 아니다.
- `reference_context`: 호출 측 시험편 문맥 또는 null. `target_context`·`settings`는 대상 파일의 정보다.
- `literature_comparisons`: 감지된 소재군의 조건을 명시한 인장 관측값이다.

방향별 참고값이 잘못됐거나 불완전하면 null을 반환한다. `effective_mpa`가 없을 때 `reference_mpa`로 대체하면서 실제 출력물의 예측값이라고 표시해서는 안 된다. 별도 표기한 소재 참고값 시나리오는 호스트의 선택이며 공정 보정 결과가 아니다.

입력에 있는 노즐·베드·챔버 온도, 팬, grade, 수분·열처리 문맥을 보존한다. 도구별 온도·유량 목록의 미상 슬롯도 유지하며 충돌·불완전 목록을 단일 대표값으로 바꾸지 않는다. 최소 레이어 시간과 팬 값은 명령이지 실측 국소 재방문 시간이나 접합면적이 아니다. 설정에 소재군이 없으면 `detected_materials`를 사용할 수 있지만 여러 소재군 중 하나를 임의로 선택하지 않는다. 슬라이서 프로필명을 실물 grade의 검증으로 취급하지 않는다.

`evidence.literature_comparisons(target_context, property_name='tensile_strength')`는 같은 소재군의 출처 URL·위치, 원 조건, 대상 조건, 미상·불일치 조건을 반환한다. Generic PLA는 `SAME_FAMILY_NOT_GRADE_MATCH`이며 `EXACT_GRADE_NAME_ONLY`도 공정 전이를 보장하지 않는다. 모든 결과는 `applied: false`, `transfer_factor: null`, `is_prediction: false`다.

S050의 32.15 MPa는 보고된 33.37−1.22로 역산한 비열처리 기준값이며 비교값은 30.07 MPa다. 대상 층 높이가 관측 수준 0.1/0.2 mm일 때만 문헌 비율을 반환하고 보간·외삽하지 않는다. 그 비율도 대상 부품 보정이 아니며 시험축·반복 분산은 미확인이다. S088의 XY/XZ 관측값은 같은 Tukey 그룹을 유지하므로 평균 차이를 유의성으로 해석하지 않는다. S028은 `property_name='interlayer_shear_strength'`에서만 제공하고 기본 인장 목록에는 넣지 않는다.

지수·패턴 계수·임의 사전값을 적합하지 않았다. NumPy·SciPy·Shapely 설치 후 `python -m unittest discover -s tests`로 시험한다. 소프트웨어 시험 통과가 물리적 예측 정확도의 검증은 아니다. [시스템 검증](docs/system-validation.md)을 함께 확인한다.

## English

2026-10-01: added [material coverage and calibration gates](docs/process-calibration.md). Numerical observations and additional reviewed studies are reported separately. Study-lineage splits, area definitions, grades and test context gate transfer eligibility. The 180-specimen diagnostic did not demonstrate improvement; no transfer model is approved.

Current contract: `process.VERSION = GCODE_PROCESS_EVIDENCE_V3_THERMAL_CONTEXT`. Universal speed and layer-height knockdowns were retired in V2; V3 additionally preserves per-tool thermal/flow context. The audit did not establish calibrated transfers between published reference coupons and target parts. See the [research evidence review](docs/research-evidence.md) for public sources and their limits.

`process_adjustment(analysis, directional_mpa, *, reference_context=None)` retains its two positional arguments and returns:

- `status: UNCALIBRATED_PROCESS_MODEL`, `factor_status: NOT_APPLIED`, `is_prediction: false`.
- `reference_mpa`: supplied X/Y/Z values represented as strings, unchanged numerically.
- `effective_mpa: null`, `adjusted: false`, `applied: []`.
- `factors: {X: 1, Y: 1, Z: 1}` for compatibility only. These are **not** predictions of equal strength at different settings.
- `reference_context`: caller-supplied coupon context or null; `target_context` and `settings`: parsed target information.
- `literature_comparisons`: qualified tensile observations for the detected material family.

Invalid/incomplete directional reference inputs still return null. Consumers must not fall back from missing `effective_mpa` to `reference_mpa` while describing that fallback as an as-printed prediction. A separately labeled reference-material scenario is an application decision, not a calibrated process result.

Target settings retain nozzle/bed/chamber temperatures, fan percentage, grade, moisture and annealing metadata when supplied. Per-tool temperature and flow lists retain their slots, including unknown values. Conflicting or incomplete lists do not become a single representative temperature or multiplier. Minimum-layer-time and fan settings are commands, not measured local return time or bonded contact area. `detected_materials` can supply the family if configuration lacks it. Multiple distinct detected families do not select an arbitrary one. A slicer profile name is not promoted to a verified material grade.

`evidence.literature_comparisons(target_context, property_name='tensile_strength')` returns same-family evidence with source URLs/locators, original conditions, target context, unknown conditions and explicit mismatches. Generic PLA is `SAME_FAMILY_NOT_GRADE_MATCH`; even `EXACT_GRADE_NAME_ONLY` establishes no process transfer. Every result has `applied: false`, `transfer_factor: null` and `is_prediction: false`.

S050 retains 32.15 MPa as a derived unannealed baseline (33.37−1.22), versus reported 30.07 MPa. The ratio is exposed only when the target layer height is one of the observed 0.1/0.2 mm levels; no interpolation or extrapolation occurs. Even at those levels, it is a literature ratio, not a target correction. Axis and replicate dispersion remain unverified. S088 XY/XZ observations retain their same Tukey group; the module does not infer significance from different means. S028 is available only with `property_name='interlayer_shear_strength'` and cannot enter the default tensile list.

The [public research review](docs/research-evidence.md) summarizes the source audit and distinguishes original-source checks, literature replay and experimental comparisons. No exponent, pattern coefficient or arbitrary prior was fitted.

Verification: run `python -m unittest discover -s tests` with NumPy, SciPy and Shapely installed. A passing software test suite does not establish physical prediction accuracy; see [system validation](docs/system-validation.md).
