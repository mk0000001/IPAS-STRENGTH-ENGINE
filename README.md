# Print Strength Engine

## 한국어

릴리스 **v0.14.0** · 코드 개정 14회(최초 등록 이후 업데이트 13회). [커밋 집계](VERSION_HISTORY.json). 패키지 변경 비병합 커밋을 세며 문서·시험 전용 변경과 자동 생성 버전 파일은 제외합니다. 개정 수는 정확도 검증 횟수가 아닙니다.

**형상 선별·문헌 비교·명시적 하중 조건의 정상응력 계산 도구입니다. 임의 출력물의 실제 파단하중이나 가장 먼저 부러질 위치를 검증한 예측 모델이 아닙니다.**

- 내부 협착과 국부 두께는 기하학적 점검 후보입니다. 후보 순서는 파손 순위가 아닙니다.
- `CAPACITY_SCENARIO_V5_EXPLICIT_LOAD_CASE_REQUIRED`는 외벽 면적에 소재 참고값을 곱해 파단하중처럼 표시하던 경로를 중단합니다. 임의 패턴 계수·코어 지수·추정 지렛대 길이를 적용하지 않습니다. 기존 출력 구조는 유지하되 하중값은 null입니다.
- `load_case.evaluate_load_case`는 고정 영역, 작용점, 방향, 선택 입력 하중을 받습니다. 전체 G-code의 명시된 압출 폭·높이로 직사각형 경로 단면을 구성하며 공극과 겹침을 구분합니다. 이는 실제 비드·접합면 측정이 아닙니다.
- 계산 범위는 단일 소재의 연결된 일정 단면 직선 보, 축에 평행한 경로, 전체 단면 고정과 끝단 하중입니다. 복잡한 형상·비스듬한 경로·다중 툴·비틀림·불완전 형상·계산 한도 초과는 `WITHHELD`입니다. 지원 범위에서는 `CONDITIONAL_NORMAL_STRESS`와 MPa 또는 MPa/N을 반환합니다. `failure_load_n=null`, `is_failure_prediction=false`입니다.
- 문헌 응력의 면적 정의가 확인되지 않으면 재료 순단면의 응력과 비교하지 않습니다. 공정 보정은 소재 등급·시험 조건·면적 정의·연구 계보를 확인해야 합니다. 승인된 보정 모델은 없으며 `effective_mpa=null`입니다. 기존 0.85 계수는 실측 보정값이 아닙니다.
- 등록 소재 18개를 검토했습니다. 공개 실험 180개 중 학습 108개, 동일 연구 내 보류 54개, 별도 패턴 18개 제외의 진단에서 후보와 학습 평균 기준선의 MAE가 모두 0.802253 MPa였습니다. 정확도 향상을 입증하지 못했으며 부품 또는 독립 연구 검증으로 해석하지 않습니다.

[강도·뷰어 통합 검토](docs/strength-viewer-audit-20261002.md) · [FusRock 공식 소재 카탈로그](docs/fusrock-official-catalog-20261001.md) · [새 연구 검토](docs/research-update-20261001.md) · [보정 승인 조건](docs/process-calibration.md) · [기존 논문 근거](docs/research-evidence.md) · [시스템 검증](docs/system-validation.md) · [공정 API](PROCESS_EVIDENCE.md)

NumPy·SciPy·Shapely 2를 설치한 뒤 시험합니다.

```sh
python -m unittest discover -s tests
```

## English

Release **v0.14.0** · 14 package code revisions (13 updates after initial import). [Commit ledger](VERSION_HISTORY.json). Reachable non-merge package commits are counted; documentation-only, tests-only and generated version metadata changes are excluded. Revision count is not a validation rating.

**Geometry screening, literature comparison and conditional normal-stress calculation under explicit loads—not a validated predictor of arbitrary part failure or fracture location.**

- Constriction and thin-region candidates are geometric inspection points, not failure rankings.
- `CAPACITY_SCENARIO_V5_EXPLICIT_LOAD_CASE_REQUIRED` withholds the former envelope-area force scenarios. Arbitrary pattern constants, core exponents and guessed levers are removed; compatibility fields remain null.
- `load_case.evaluate_load_case` accepts a fixed region, load point, direction and optional force. Complete G-code roads with declared width and height form rectangular material sections accounting for voids and overlaps. These are not measured beads or weld contacts.
- Supported mechanics are limited to a connected, single-material, constant-section straight beam, axis-aligned roads, a full-section fixture and an endpoint load. Complex, oblique, multi-tool, torsional, incomplete or over-budget geometry returns `WITHHELD`. Supported inputs return `CONDITIONAL_NORMAL_STRESS` in MPa or MPa/N, with `failure_load_n=null` and `is_failure_prediction=false`.
- Unknown reference area definitions cannot be compared with net-material stress. Calibration requires compatible grade, test conditions, area definition and study lineage. No transfer model is approved; `effective_mpa=null`. The existing 0.85 reference margin is not experimental calibration.
- All 18 registered material families were reviewed. A within-study diagnostic split of 180 public specimens used 108 for training, 54 held out and 18 excluded for a different pattern. Candidate and training-mean baseline both achieved MAE 0.802253 MPa: no evidence of improvement, and no independent-study or part-level validation.

[Strength/viewer integration audit](docs/strength-viewer-audit-20261002.md) · [FusRock official catalogue](docs/fusrock-official-catalog-20261001.md) · [New research](docs/research-update-20261001.md) · [Calibration gates](docs/process-calibration.md) · [Earlier evidence](docs/research-evidence.md) · [System validation](docs/system-validation.md) · [Process API](PROCESS_EVIDENCE.md)

Tests require NumPy, SciPy and Shapely 2; run the command above.
