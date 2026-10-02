# Print Strength Engine

## 한국어

릴리스 **v0.16.0** · 코드 개정 16회(최초 등록 이후 업데이트 15회). [커밋 집계](VERSION_HISTORY.json). 패키지 변경 비병합 커밋을 세며 문서·시험 전용 변경과 자동 생성 버전 파일은 제외합니다. 개정 수는 정확도 검증 횟수가 아닙니다.

**힘을 입력하지 않아도 G-code의 국부 경로 단면으로 인장·굽힘 하중을 자동 추정합니다. 형상 선별·문헌 비교·명시적 하중 조건의 정상응력 계산도 제공합니다. 자동 추정은 조건을 명시한 참고 시나리오이며 실제 파단하중이나 가장 먼저 부러질 위치를 검증한 예측은 아닙니다.**

- 내부 협착과 국부 두께는 기하학적 점검 후보입니다. 후보 순서는 파손 순위가 아닙니다.
- `automatic_sections.StreamingSections`는 원본 전체 G-code에서 모델·브리지의 명시된 폭·높이를 읽어 국부 단면을 합칩니다. 공극을 유지하고 겹침을 중복 계산하지 않으며 비스듬한 XY 경로도 처리합니다. 외벽 면적이나 100% 속 찬 단면으로 대체하지 않습니다.
- `CAPACITY_SCENARIO_V6_AUTOMATIC_LOCAL_REFERENCE_LOADS`는 완성된 단일 툴 국부 단면과 소재 참고값으로 인장 및 굽힘 추정을 반환합니다. 모든 굽힘 모멘트 방향의 가장 작은 단면계수를 사용하고, 명시적인 10·25·50 mm 거리를 비교합니다. 기본 25 mm는 자동 비교 조건이며 실제 고정점이 아닙니다. 폭·높이 미기록, 불완전 스캔, 계산 한도 초과, 복수 툴 강성 미확인은 하중을 보류합니다.
- `load_case.evaluate_load_case`는 고정 영역, 작용점, 방향, 선택 입력 하중을 받습니다. 전체 G-code의 명시된 압출 폭·높이로 직사각형 경로 단면을 구성하며 공극과 겹침을 구분합니다. 이는 실제 비드·접합면 측정이 아닙니다.
- 계산 범위는 단일 툴의 연결된 일정·구간별 가변 단면 직선 보, 축에 평행한 경로, 전체 단면 고정과 끝단 하중입니다. 구간별 면적·도심·단면 2차 모멘트와 경계 양쪽의 명목 응력을 평가합니다. 복잡한 형상·비스듬한 경로·다중 툴·비틀림·불완전 형상·계산 한도 초과는 `WITHHELD`입니다. 지원 범위에서는 `CONDITIONAL_NORMAL_STRESS`와 MPa 또는 MPa/N을 반환합니다. `failure_load_n=null`, `is_failure_prediction=false`입니다.
- 명시적 하중 검토는 문헌 응력의 면적 정의가 확인되지 않으면 재료 순단면의 응력과 직접 비교하지 않습니다. 자동 참고 하중은 시편 참고값을 균질 경로 단면 응력에 적용한다는 별도 가정을 기록하며 원자료의 면적 정의가 미상이면 그대로 `UNKNOWN`을 유지합니다. 이 전이는 실측 보정 전입니다. 승인된 공정 보정 모델은 없으며 `effective_mpa=null`입니다. 기존 0.85 계수도 실측 보정값이 아닙니다.
- 등록 소재 18개를 검토했습니다. 공개 실험 180개 중 학습 108개, 동일 연구 내 보류 54개, 별도 패턴 18개 제외의 진단에서 후보와 학습 평균 기준선의 MAE가 모두 0.802253 MPa였습니다. 정확도 향상을 입증하지 못했으며 부품 또는 독립 연구 검증으로 해석하지 않습니다.

[힘 입력 없는 자동 하중 추정](docs/automatic-load-estimates-20261003.md) · [하중 상태·가변 단면 계산](docs/load-status-and-variable-sections-20261002.md) · [강도·뷰어 통합 검토](docs/strength-viewer-audit-20261002.md) · [FusRock 공식 소재 카탈로그](docs/fusrock-official-catalog-20261001.md) · [새 연구 검토](docs/research-update-20261001.md) · [보정 승인 조건](docs/process-calibration.md) · [기존 논문 근거](docs/research-evidence.md) · [시스템 검증](docs/system-validation.md) · [공정 API](PROCESS_EVIDENCE.md)

NumPy·SciPy·Shapely 2를 설치한 뒤 시험합니다.

```sh
python -m unittest discover -s tests
```

## English

Release **v0.16.0** · 16 package code revisions (15 updates after initial import). [Commit ledger](VERSION_HISTORY.json). Reachable non-merge package commits are counted; documentation-only, tests-only and generated version metadata changes are excluded. Revision count is not a validation rating.

**Automatic tensile and bending reference loads from local G-code road sections, without entering a force. Geometry screening, literature comparison and explicit-load normal-stress analysis remain available. Automatic values are conditional reference scenarios, not validated part fracture loads or failure locations.**

- Constriction and thin-region candidates are geometric inspection points, not failure rankings.
- `automatic_sections.StreamingSections` consumes complete source G-code and unions model/bridge sections using declared width and height, including oblique XY roads. Voids are retained and overlaps counted once; exterior area or a solid 100% infill section is not substituted.
- `CAPACITY_SCENARIO_V6_AUTOMATIC_LOCAL_REFERENCE_LOADS` returns tensile and bending estimates from complete single-tool local sections and a material reference. The minimum modulus over every unit bending-moment direction is used with explicit 10/25/50 mm moment arms; default 25 mm is a comparison scenario, not an observed fixture. Missing dimensions, incomplete scans, exceeded limits and unverified mixed-tool stiffness withhold force values.
- `load_case.evaluate_load_case` accepts a fixed region, load point, direction and optional force. Complete G-code roads with declared width and height form rectangular material sections accounting for voids and overlaps. These are not measured beads or weld contacts.
- Supported mechanics are limited to a connected, single-tool straight beam with constant or piecewise variable sections, axis-aligned roads, a full-section fixture and an endpoint load. Local area, centroid and inertia are checked at both limits of each interval. Complex, oblique, multi-tool, torsional, incomplete or over-budget geometry returns `WITHHELD`. Supported inputs return `CONDITIONAL_NORMAL_STRESS` in MPa or MPa/N, with `failure_load_n=null` and `is_failure_prediction=false`.
- Explicit-load evaluation does not directly compare unknown-area references with net-material stress. Automatic reference loads separately disclose an assumed homogeneous net-road stress transfer; an unknown source area definition remains `UNKNOWN`. That transfer is uncalibrated. No process transfer model is approved; `effective_mpa=null`. The existing 0.85 reference margin is not experimental calibration.
- All 18 registered material families were reviewed. A within-study diagnostic split of 180 public specimens used 108 for training, 54 held out and 18 excluded for a different pattern. Candidate and training-mean baseline both achieved MAE 0.802253 MPa: no evidence of improvement, and no independent-study or part-level validation.

[Automatic no-input reference loads](docs/automatic-load-estimates-20261003.md) · [Strength/viewer integration audit](docs/strength-viewer-audit-20261002.md) · [FusRock official catalogue](docs/fusrock-official-catalog-20261001.md) · [New research](docs/research-update-20261001.md) · [Calibration gates](docs/process-calibration.md) · [Earlier evidence](docs/research-evidence.md) · [System validation](docs/system-validation.md) · [Process API](PROCESS_EVIDENCE.md)

Tests require NumPy, SciPy and Shapely 2; run the command above.
