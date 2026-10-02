# 공정 요인 취약부 보완 구현 계획 / Process-aware weakness implementation plan

> **For agentic workers:** Use subagent-driven-development for independent source research and parser implementation; root integrates the bounded local collector and presentation.

**Goal:** Connect actual commanded extrusion, wall roles and thermal/speed/fan context to local weakness scenarios while preserving empirical limits.

**Architecture:** Optional source-motion context feeds a bounded local-process collector and an independent volume-equivalent road-section collector beside the existing declared sections/contact collector. A shared assessment reaches web, HTML and PDF. Existing paths remain compatible.

**Tech Stack:** Python, Decimal, NumPy/SciPy/Shapely, vanilla JavaScript, ReportLab, existing native scanner and Docker release workflow.

**Spec:** ../specs/2026-10-03-process-aware-weakness-design.md

## Global Constraints

- Korean before English. No user geometry, telemetry, credentials or prices in public repositories.
- Do not manufacture universal temperature/flow/wall knockdowns, measured weld temperatures or fracture labels.
- Raw material references are unchanged; internal margin applies once to load inputs.
- Keep old motion callback and existing declared geometry scenarios; all new unknown data remains explicit.
- No hardware writes or saved quote changes. Reuse completed sources except one necessary new-context scan.

## Review Focus

- Physical heater indices versus logical filament/tool identities.
- Retraction debt across units or flow-override changes; slicer flow double counting.
- Trailing diameter, missing temperature, unrelated support and purge extrusion.
- Arc subdivision, crop fractions and repeated/overlapping material geometry.
- Context/section/cache completeness and consistent web/report scenario labels.

## Tasks

- [ ] Verify new primary thermal/flow/wall experiments, open data hashes, replicates and confounding; document applicability.
- [ ] Reproduce parser bugs with synthetic G-code; implement optional immutable motion context and checkpoint consistency with focused regressions.
- [ ] Test and implement bounded local role/process collection plus volume-equivalent conditional sections; no universal material factor.
- [ ] Connect exact-source cache/version guards and consistent candidate assessment to host/web/PDF.
- [ ] Review and test core/parser/host integration, one needed source replay and performance overhead; fix findings.
- [ ] Conduct one independent final review, build/test/deploy, verify versions and actual browser/PDF, publish bilingual release evidence.

## 한국어 실행 범위

기존 엔진 개선 요청에 따라 입력 해석 오류와 누락된 공정 요인을 연결한다. 실제 실험의 조건이 다른 경우 문헌 계수를 부품 파단하중에 직접 전이하지 않는다. 계획의 완료 표시는 소프트웨어·배포 검증이며 물리 시험 정확도 인증이 아니다.

## English execution scope

This extends the existing engine under the requested improvement scope. Incompatible experimental conditions do not authorize part-fracture transfer. Completion records software/deployment validation, not physical accuracy certification.
