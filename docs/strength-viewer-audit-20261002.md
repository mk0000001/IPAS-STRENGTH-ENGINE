# Strength and viewer integration audit - 2026-10-02

## 한국어

이번 개정은 입력값·소재 식별·하중 조건의 일관성을 보완합니다. 새로운 실증 보정 모델이나 임의의 강도 배율을 추가하지 않습니다. 문헌 시편의 소재 참고값, 형상 점검 후보, 명시적 하중 조건의 응력 계산은 서로 다른 결과입니다.

| 검토 항목 | 확인한 문제 | 보완한 동작 |
| --- | --- | --- |
| 보 축 추론 | 고정 영역의 빈 공간을 크게 잡으면 동일한 보의 축이 바뀌었습니다. | 실제 압출 재료의 가장 긴 축을 사용하고 기존 연결·일정 단면·세장비·끝단 하중 검사를 유지합니다. |
| 복수 툴 설정 | 노즐·선폭·인필 목록의 첫 값이 전체 파일의 단일값으로 쓰일 수 있었습니다. | 모든 유효 슬롯이 일치할 때만 단일값을 반환합니다. 혼합·미확인은 그대로 보존합니다. |
| 모델 소재 범위 | 서포트 전용 또는 사용량 0인 소재가 모델 참고값 선택에 섞였습니다. | 명시된 서포트 전용과 유한한 0 g 행만 제외합니다. 역할·사용량 미확인은 보수적으로 유지합니다. |
| 실제 제품 선택 | 사용자가 고른 제품을 파일에서 식별한 것처럼 설명했습니다. | 수동 선택 출처를 구분하며 실제 스풀을 확인했다는 의미로 사용하지 않습니다. 방향 강도 쌍이 없는 공식 특성 자료도 같은 규칙을 적용합니다. |
| 과거 전체 중량 단가 선택 | 전체 중량의 가격 선택이 모델·서포트별 소재 확인처럼 재사용될 수 있었습니다. | 보존된 원본의 명확한 단일 모델 소재만 원본 비교자료로 표시합니다. 현재 실사용 소재는 미확인으로 구분하며 혼합·불명확한 원본은 보류합니다. |
| ABS 제품 등급 | 알려지지 않은 등급명이 기본 ABS의 정확한 제품 식별로 통과할 수 있었습니다. | 기본 제품명과 허용된 프로파일 접미사만 연결하고 미확인 변형 등급은 기본 제품의 수치로 대체하지 않습니다. |
| 보고서 그림 출처 | 명시적 파일 버전·플레이트 정보가 서로 다른 경우 그림이 섞일 수 있었습니다. | 충돌을 먼저 검사하여 잘못된 출처의 그림을 보류합니다. 저장 견적은 수정하지 않습니다. |

### 검증 범위

- 100 × 2 × 1 mm 보의 10 mm 구간을 고정하고 자유 길이 90 mm 끝에 1 N을 가하는 회귀 사례를 사용했습니다. 직사각형 재료 단면에서 `M = 90 N·mm`, `I = 2/12 mm⁴`, `c = 0.5 mm`이므로 정상응력은 270 MPa/N입니다. 고정 영역의 재료 밖 폭을 바꿔도 같은 결과를 요구합니다. 이는 해석식 일치 시험이며 출력물 파단 시험이 아닙니다.
- 복수 툴의 혼합·미확인·동일 설정, 소재 역할과 사용량, 사용자 선택 출처, 과거 단가 선택, 파일·플레이트 충돌을 회귀 시험으로 확인합니다.
- 호스트 뷰어는 옅은 실제 외벽과 선명한 실제 경로선을 함께 표시합니다. 회전 중 선택 레이어와 취약부 강조선을 제한하고, 정지하면 상세 경로를 복원합니다. 경로를 이어서 가짜 압출선을 만들지 않습니다. 브라우저 프레임 속도는 별도의 측정이며 Canvas 호출 수 시험과 혼동하지 않습니다.

최종 확인: 공개 패키지 시험 111개·하위 검사 30개, 통합 Docker 시험 328개·하위 검사 69개를 통과했습니다. 통합 시험에는 조건부 생략 5개와 의존성 사용 중단 예고 2개가 있습니다. 독립 검토에서 찾은 병목·출처 설명·제품 등급 매칭을 수정한 뒤 다시 확인했습니다. 상세 3페이지 및 16개 제품 통합 2페이지 PDF의 여백·버전 표시를 렌더링으로 확인했습니다. 네 운영 서비스의 이미지·소스 해시·네이티브 스캐너·버전이 일치하며 점검 시 재시작은 0회였습니다. 실제 기존 파일의 618,192개 경로·438층 뷰어를 재스캔 없이 열어 외벽 128개 대표 층과 경로의 혼합 표시를 확인했고, 점검한 브라우저 화면의 오류 로그는 비어 있었습니다. 강도 릴리스는 `0.14.0`, 통합 앱은 `0.5.9-strength-viewer-audit`입니다.

### 유지되는 제한

`effective_mpa`와 실제 파단하중은 승인된 공정 보정·부품 실증 없이 제공하지 않습니다. 조건부 응력 계산은 연결된 단일 소재의 일정 단면 직선 보와 명시적 고정·하중 조건에 한정됩니다. 형상 후보 순서는 실제 파손 순위가 아닙니다. 소재 참고값의 면적 정의가 확인되지 않으면 재료 순단면 응력과 비교하지 않습니다.

기존 근거: [공정 보정 승인 조건](process-calibration.md), [공개 인필 진단](research-update-20261001.md), [공식 FusRock 자료](fusrock-official-catalog-20261001.md), [시스템 검증](system-validation.md).

## English

This revision improves input, identity and load-condition consistency. It adds no empirical transfer model or arbitrary strength multiplier. Coupon material references, geometry screening and normal stress under explicit loads remain separate outputs.

| Audit area | Defect | Corrected behavior |
| --- | --- | --- |
| Beam axis | Empty space in an enlarged fixture could change the inferred axis of identical material. | Infer the longest deposited-material axis while retaining connectivity, constant-section, slenderness and endpoint-load guards. |
| Tool settings | The first nozzle, width or infill slot could become a file-wide scalar. | Return a scalar only when all valid slots agree; preserve mixed and unknown values. |
| Model material | Support-only and zero-consumption entries could contaminate model references. | Exclude only explicit support-only rows and finite zero mass. Retain unknown roles and quantities conservatively. |
| Product provenance | A user-selected product could be described as a file-identified product. | Label user selection separately, including properties-only official records; neither source verifies the mounted spool. |
| Legacy price selection | Whole-file pricing could be reused as structural spool identity. | Show only unambiguous preserved original model metadata as a labeled original-source comparison. Actual current identity remains unresolved; mixed or unclear originals are withheld. |
| ABS grade matching | Unknown grade qualifiers could be accepted as exact base ABS identity. | Require the base product name and permitted profile suffixes. Do not replace unidentified variants with base-grade numbers. |
| Report source | Explicit file-version or plate conflicts could mix figures. | Withhold figures on identity conflicts without changing saved estimates. |

### Validation scope

- A 100 × 2 × 1 mm beam clamped over 10 mm has a 90 mm free length. With a 1 N end load, `M = 90 N·mm`, `I = 2/12 mm⁴`, and `c = 0.5 mm` give 270 MPa/N. Extending the fixture outside the material must preserve the result. This verifies agreement with an analytical expression, not printed-part failure.
- Regression cases cover mixed, unknown and uniform tool settings, model/support roles and consumption, selected-product provenance, legacy aggregate pricing, and conflicting file/plate identities.
- The host viewer blends translucent real outer contours with darker real paths. Motion limits selected-layer and local-highlight drawing; resting restores detail. Independent segments are never joined into fabricated roads. Canvas command counts are not measured browser frame rates.

Final checks passed 111 package tests with 30 subtests and 328 Docker integration tests with 69 subtests. The integration run had five conditional skips and two dependency deprecation warnings. Independent review findings were corrected and rechecked. Detailed three-page and sixteen-product combined two-page PDFs were rendered and checked for bounds/version labels. All four production services matched the tested image, source hashes, native scanners and versions with zero restarts at inspection. An existing 618,192-road, 438-layer viewer opened without rescanning and displayed the blended 128-layer representative exterior. No browser errors were recorded in the inspected view. Release identities are strength `0.14.0` and host `0.5.9-strength-viewer-audit`.

### Remaining limits

No approved process-transfer calibration or part validation is introduced: `effective_mpa` and failure loads remain withheld. Conditional stress supports connected, single-material, constant-section straight beams with explicit fixtures and loads. Geometry candidate order is not fracture order. References with unknown area definitions cannot be compared with net-material stress.

Existing evidence: [calibration gates](process-calibration.md), [public infill diagnostic](research-update-20261001.md), [official FusRock records](fusrock-official-catalog-20261001.md), [system validation](system-validation.md).
