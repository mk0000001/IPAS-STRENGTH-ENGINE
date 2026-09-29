# Print Strength Engine

[한국어](#한국어) · [English](#english)

## 한국어

릴리스 **v0.11.0** · 코드 개정 11회(최초 등록 이후 업데이트 10회). [커밋 집계](VERSION_HISTORY.json).

엔진 패키지를 변경한 도달 가능한 비병합 커밋 기준이다. 병합된 개발 이력은 포함하고 문서 전용·시험 전용·호스트 앱 변경과 자동 생성 `_version.py`는 제외한다. 개정 수는 기능 수나 정확도 검증 횟수가 아니다. 버전은 `0.<코드 개정 수>.<릴리스 메타데이터 수정>`이며 과거 결과의 버전이 없으면 미상으로 남긴다.

[논문·자료의 핵심 근거](docs/research-evidence.md) · [시스템 검증과 한계](docs/system-validation.md) · [공정 API](PROCESS_EVIDENCE.md)

**실험적 형상 선별·문헌 비교·조건부 하중 시나리오 엔진이다. 임의 출력물의 실제 파손 위치나 파단하중을 실증 검증한 예측 모델이 아니다.** 소재 참고값, 기하학적 선별, 가정한 하중 계산은 별도 출력이다.

### 현재 동작

- `weakest_layer_candidate(profile)`는 양쪽 이웃의 중앙값과 두 범위에서 비교해 내부 협착 후보를 최대 6개 반환한다. 균일 구간·단조 테이퍼는 자동 후보가 아니며 위쪽 모델 체적이 2% 미만인 끝단은 제외한다. 2% 협착 기준과 후보 간격은 선별 가정이지 검증된 파괴 기준이 아니다. 표식은 Z 레이어를 가리키며 XY 파괴 위치를 해결하지 않는다.
- `local_thickness.screen_contour_layers`는 호스트가 재구성한 외벽을 격자화하고 별도 제공된 서포트 경로를 제외해 얇은 구간을 찾는다. NumPy·SciPy·Shapely 2가 필요하며 각 외곽의 범위로 연산을 잘라내되 격자는 바꾸지 않는다.
- `infill_response()`는 [Ben Amor 등(2024) Table 6](https://doi.org/10.35219/awet.2024.10)의 PLA 10–100% 구간 내 비교 보간이다. 브랜드·패턴·벽 보정이나 부품 내력 예측이 아니며 범위 밖 외삽·임의 Z 보정·재료면적에 중복 적용을 하지 않는다.
- 공정 계약 `GCODE_PROCESS_EVIDENCE_V3_THERMAL_CONTEXT`는 도구별 온도·유량, 셸·냉각 조건을 보존한다. 충돌·누락 목록에서 단일 대표값을 만들지 않는다. `NOT_APPLIED` 계수 1은 미적용 표시이고 `effective_mpa`는 null이다. 레이어 평균 시간을 국소 열이력으로 대체하지 않는다.
- `CAPACITY_SCENARIO_V4_GEOMETRY_QUALIFIED`는 연결된 단면의 축력 최소점과 주축 굽힘 최소점을 구분한다. `section_station_mm`와 `bending_section_station_mm`도 구분해야 한다. 국부 창은 전체 하중 경로 해석이 아니다.
- 희소/미상 인필의 굽힘·지배 하중은 단면 관성모멘트를 알 수 없어 보류한다. 희소 축력은 미보정 직사각형 셸/코어 가정이며 누락 설정을 100% 인필로 간주하지 않는다. 명목 100%도 실제 공극·접촉면 검증이 아니다. 패턴 이름이나 벽 수로 근거 없는 패널티를 추가하지 않는다.
- 참고응력의 면적 기준이 `NET_MATERIAL`·`INTERLAYER_CONTACT`이면 외곽 면적과 곱해 힘을 만들지 않는다. `UNKNOWN`은 미보정 시나리오만 허용한다. 모든 내력 출력은 `is_failure_prediction: false`이며 예측구간을 제공하지 않는다.

별도 net-section 스크리닝은 검증된 입력 허용응력(MPa), 재구성된 단면(mm², mm³), 지정 인장력·굽힘 모멘트 아래의 지배 단면과 비례 하중 배율을 계산한다. 입력의 타당성을 자동 보증하지 않는다. 실제 지지·가력점, 응력집중, 피로, 좌굴, 층간 박리는 해결하지 않는다. 쉽게 부러졌다는 정성 관찰은 수치 정확도의 검증을 대신하지 않는다.

의존성을 설치한 뒤 시험한다.

```sh
python -m unittest discover -s tests
```

---

## English

Release: **v0.11.0** · 11 recorded code revisions (10 updates after initial import). [Commit ledger](VERSION_HISTORY.json).

Count includes reachable non-merge commits touching the engine package, including merged development history; excludes documentation-only, tests-only, host-app changes and generated _version.py. It counts commits, not individual features or validated accuracy. Version convention: 0.<code revision count>.<release metadata fix>. Past results without a recorded version remain unknown.


Public documentation: [research evidence and sources](docs/research-evidence.md) · [system validation and limitations](docs/system-validation.md) · [process API](PROCESS_EVIDENCE.md).

Current contracts are `GCODE_PROCESS_EVIDENCE_V3_THERMAL_CONTEXT` and `CAPACITY_SCENARIO_V4_GEOMETRY_QUALIFIED`. Material references, geometric screening and hypothetical load scenarios are separate outputs; none is a calibrated whole-part failure prediction.

`weakest_layer_candidate(profile)` now returns up to six separated internal constriction candidates in `weak_candidates`; `weakest_section` is the first ranked candidate. It compares the model volume/height area proxy against the median on **both** sides at two neighborhood sizes. Uniform sections and monotonic tapers do not automatically produce a candidate. Terminal features with less than 2% of model volume above them are excluded; this is a relevance heuristic, not a load estimate. Nearby candidates are suppressed into one region. The minimum narrowing threshold (2%), neighborhood sizes and separation are transparent screening assumptions, not empirically validated fracture thresholds. Mild changes are explicitly labeled. Without loads, restraints, connected sections, material bonding and stress concentrations, the ranking is **not** an actual weakest-point or failure-load prediction. Candidate markers locate Z layers, not resolved XY fracture points.

`print_strength_engine.infill.infill_response()` provides a PLA literature comparison over 10–100% infill using within-study piecewise interpolation from [Ben Amor et al. (2024), Table 6](https://doi.org/10.35219/awet.2024.10). It does not assert matching pattern/wall/brand calibration, does not extrapolate outside the study range, and must not be multiplied into the measured material area. Optional `reference_mpa` produces a conditional comparison, not a part capacity; no Z correction is invented.

Experimental independent net-section strength screening. Finds the section with the highest local failure index under a specified tensile force and bending moment. Input: reconstructed sections (mm², mm³) and validated allowable stress (MPa). Output: governing section and proportional load multiplier.

`local_thickness.screen_contour_layers` accepts outer-wall contour layers reconstructed by a host application. It rasterizes their envelopes, excludes support paths supplied separately, and identifies thin-region candidates with section proxies. Raster work is cropped to each contour's bounds without changing the grid. NumPy, SciPy and Shapely 2 are required for geometry screening.

`process` reads deposition settings and preserves reference/target conditions separately. Evidence V2 retires uncalibrated speed/layer multipliers: identity factors are `NOT_APPLIED` placeholders and `effective_mpa` is null. Verified literature observations are comparisons only; tensile and shear properties are not interchangeable and no paper ratio transfers automatically to a part. See [PROCESS_EVIDENCE.md](PROCESS_EVIDENCE.md).

`capacity` combines a section proxy and supplied material reference with explicit, uncalibrated sparse-core/wall assumptions and optional bending lever. Pattern aliases are normalized and unsupported pattern coefficients are marked as fallbacks. Outputs expose calibration status, material reference stress and validation gaps; they provide no prediction interval. A fleet's typical settings are not material calibration data. Layer-summed extrusion areas are comparison proxies and never produce a breaking force or allowable stress.

Geometry schema V4 isolates face-connected material and preserves separate axial-area and principal-bending minima, including finite-cell inertia coupling. `section_station_mm` remains the axial station; `bending_section_station_mm` must be used for a bending scenario. Candidate windows remain cropped geometry screens, not complete load-path solutions.

The current capacity model retains the audit fixes introduced in V2: no uncalibrated wall-count notch penalty; missing structure settings do not imply solid infill; numeric zero settings are preserved. Sparse/unknown infill bending and governing loads are withheld because an area fraction does not establish section inertia. Sparse axial output is an explicitly uncalibrated rectangular shell/core scenario. Nominal 100% scenarios do not receive pattern-name penalties. Hypothetical lever scenarios must not be compared as a common-load failure ranking. All capacities expose `is_failure_prediction: false`.

This must not be presented as a validated whole-part strength predictor. Actual load direction, restraints, local stress concentrations, fatigue, buckling and delamination are not solved. Force estimates depend on the supplied stress and assumed lever; qualitative reports of easy breakage do not validate their numerical accuracy.

Run `python -m unittest discover -s tests` after installing NumPy, SciPy and Shapely.

Process evidence V3 preserves per-tool temperature/flow slots and reports no single temperature for conflicting or incomplete lists. Flow, top/bottom shells and cooling setpoints remain file settings, not observed void fraction or local thermal history. No duration-per-layer approximation is used as local return time.

Capacity V4 separates nominal full infill from verified solid/contact geometry. `reference_area_basis` can be `UNKNOWN`, `GROSS_ENVELOPE`, `NET_MATERIAL` or `INTERLAYER_CONTACT`; the latter two withhold force on an outer-envelope section to prevent mixing stress denominators. Unknown reference basis retains only the existing uncalibrated scenario, never a validated prediction. This API does not reconstruct bonded area, solve cracks/notches, or calibrate a universal void/healing factor.
