# 강도·취약부 통합 구현 계획

## 한국어

목표는 누락된 끝 연결부를 보존하고, 국부 단면·인접 층 접촉·소재 원자료와 예상 하중을 동일한 분석 및 보고서 계약으로 연결하는 것이다. 완료한 원본 스캔은 재사용하며 프린터 제어·저장 견적 금액 수정은 하지 않는다.

1. 끝·균일 벽·둥근 캡·다물체·축 변경 회귀를 만들고, 끝 연결부의 안쪽 단면을 선별한다.
2. 동일한 원본 스트림에서 국부 단면과 선언된 인접 층 접촉을 수집한다. 불완전·예산 초과·부정합 캐시는 보류한다.
3. 비교 가능한 25 mm 하중만 정렬하고, 근거가 부족하면 기하 순서를 복원한다. 웹·HTML·PDF의 후보 번호와 근거를 통일한다.
4. 제조사 소재 MPa는 그대로 표시하고, 예상 강도·하중에만 별도 내부 여유계수를 한 번 적용한다. 소재·공식 특성 상세는 기본 접힘으로 제공한다.
5. 1차 문헌·실측자료의 시험 정의와 전이 한계를 확인하고, 독립 검토·전체 통합 시험·운영 웹·PDF·출처 해시를 검증한 뒤 버전 및 공개 문서를 갱신한다.

기하 접촉 비율이나 미측정 접합강도를 파단하중으로 대신하지 않는다. 실제 최초 파손·노치·충격·피로·크리프의 실증 정확도는 별도 측정이 필요하다. 자세한 작업 점검표는 아래 영어 원문에 유지한다.

## English

# Integrated Strength and Weakness Implementation Plan

> **For agentic workers:** Use subagent-driven-development for the independent tasks below.

**Goal:** Correct missed terminal regions and integrate traceable mechanism diagnostics with consistent reference-load ranking and reports.

**Architecture:** Outer-contour candidate generation feeds complete-source declared-road section/contact collection. A dedicated weakness assessment integrates evidence without inventing weld or fracture properties. Host presentation consumes the same assessment for the viewer and reports.

**Tech Stack:** Python, NumPy/SciPy, Shapely, existing G-code scanner, vanilla JavaScript, ReportLab, Docker.

**Spec:** ../specs/2026-10-03-integrated-weakness-design.md

## Global Constraints

- No hardware writes; reuse completed scans and cached contours.
- Preserve strict source/member/version/fingerprint/finite-value/completeness guards.
- No unknown-to-zero data conversion, empirical-validation claims, or universal welding knockdown.
- Keep material prices and immutable saved quote amounts unchanged.
- Korean documentation precedes English.

## Review Focus

- Rounded caps and naturally changing cross-layer footprint must not become guaranteed defects.
- Neighboring parts must not be aggregated or spatially suppress one another.
- Incomplete or heterogeneous evidence must not be ranked as complete comparable loads.
- Material/source changes must invalidate stale loads and diagnostics.
- HTML/PDF must retain costs and use matching candidate numbers and rationale.

### Task 1: Geometry selection

- [x] Add failing terminal, uniform strip, rounded cap, multi-object and coordinate regressions.
- [x] Implement terminal-root evaluation and section-based geometric comparison in local_thickness.py.
- [x] Replay the complete cached contours and check both right terminal features.

### Task 2: Declared-road contact diagnostics

- [x] Add analytic overlap, shrink/grow, missing interface, tool, incomplete/budget and cache regressions.
- [x] Implement bounded interlayer_contact.py and integrate the existing one-pass collector.
- [x] Validate finite exact-source cached metadata and compare the original file once after integration.

### Task 3: Unified weakness assessment and presentation

- [x] Add regressions for reversed reference loads, incomparable candidates and good-overlap/unmeasured weld.
- [x] Implement weakness.py with mechanism evidence and compatible-scenario ordering.
- [x] Connect host strength_points, viewer, HTML and PDF to the same assessment and reasons.

### Task 4: Research, independent review and release

- [x] Cross-check primary studies, actual data, measurement definitions and transfer limits.
- [x] Run full core/host/Node tests and independent final review; repair findings.
- [x] Update engine/source versions, build and deploy all four services.
- [x] Verify the original-file web result, fresh PDF, immutable costs and live hashes.
- [ ] Publish bilingual validation/provenance and the public engine release to GitHub.
