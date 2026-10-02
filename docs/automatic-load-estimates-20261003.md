# 힘 입력 없는 자동 하중 추정 / Automatic reference loads without force input

## 한국어

강도 엔진 v0.16.0, `LOCAL_DECLARED_ROAD_SECTIONS_V2`, `CAPACITY_SCENARIO_V6_AUTOMATIC_LOCAL_REFERENCE_LOADS`의 적용 기록입니다. 사용자가 힘이나 고정점을 입력하지 않아도 점검 지점별 인장·굽힘 참고 하중을 계산합니다. 숫자는 **조건을 명시한 추정값**이며 실제 파단시험으로 보정한 허용하중이 아닙니다.

### 계산에 사용하는 형상과 조건

1. 기존 외벽 형상 검사는 국부 점검 영역과 절단 위치를 제공합니다. 그 순서는 형상 선별 순서이며 파손 순위가 아닙니다.
2. worker가 선택한 원본 G-code를 처음부터 끝까지 읽습니다. 저장 한도로 잘린 압출 캐시나 뷰어의 간략 경로로 재료 단면을 계산하지 않습니다.
3. 모델·브리지 경로의 명시된 선폭과 층 높이로 직사각형 재료 영역을 만들고 각 국부 단면에서 합집합을 구합니다. 공극과 분리된 조각을 유지하며 겹친 면적을 중복 합산하지 않습니다. 서포트·브림·타워는 제외합니다. 비스듬한 XY 경로도 포함합니다.
4. 단면 면적, 도심, 단면 2차 모멘트의 전체 행렬을 계산합니다. 두 주축만 비교하지 않고 모든 단위 굽힘 모멘트 방향에서 가장 큰 정상응력을 찾습니다. 정사각형도 대각선 굽힘을 빠뜨리지 않습니다.
5. 단일 툴 단면에 방향별 소재 참고응력을 적용합니다. 실제 고정점 대신 명시적인 10·25·50 mm 거리를 비교하며 기본 표시는 25 mm입니다. 다른 툴의 상대 강성이 확인되지 않은 단면은 하중을 보류합니다.

`A`는 선언된 국부 경로 순단면, `Z`는 모든 굽힘 모멘트 방향 중 최소 단면계수, `σref`는 방향별 소재 참고응력입니다.

```text
인장 참고 하중 F = σref × A
굽힘 참고 모멘트 M = σref × Z
거리 L에서 굽힘 참고 하중 F = M / L
```

이 관계는 도심·단면 2차 모멘트와 선형 굽힘 응력의 관계에 따른 비교입니다. [MIT David Roylance, Beam Stresses](https://web.mit.edu/course/3/3.11/www/modules/bstress.pdf). 전체 부품의 지지조건·힘 전달 경로를 푼 유한요소 해석은 아닙니다.

인필률·인필 패턴·벽 설정은 실제 경로의 위치·공극·단면으로 반영됩니다. 명목 인필률에 비례 계수를 곱하거나 100% 속 찬 면적으로 대체하지 않습니다. 속도·온도 등은 출처 설정으로 기록하지만, 승인된 공정 보정식이 없으므로 임의 계수를 적용하지 않습니다.

### 소재 참고값과 검증 수준

실제 사용 소재 선택을 존중하고, 원자료의 면적 기준이 미상이면 `UNKNOWN`을 유지합니다. 자동 하중은 시편 참고응력을 균질한 경로 순단면 응력에 적용하는 **미보정 전이 가정**을 별도로 기록합니다. 모든 국부 경로가 완전히 접합되어 동일한 변형률을 가진다고 가정하며 실제 비드·공극·용접 접촉면은 실측하지 않았습니다.

예제의 FusRock ABS 참고응력은 공식 XY 인장 파단 33.36 MPa에 기존 내부 여유계수 0.85를 적용한 28.356 MPa입니다. 공식 Z 값 55 MPa는 별도의 출력 방향 값입니다. 0.85는 파단시험으로 학습한 계수나 구조 안전계수가 아닙니다. [FusRock 공식 ABS 자료](https://www.fusrock.com/material/performance/id/106/lang/en).

전단·비틀림·좌굴·노치·균열·층간 박리·충격·피로·크리프·응력 집중은 이 국부 선형 계산으로 풀지 않습니다. 실제 출력물은 표시된 참고 하중보다 낮은 힘에서 파손될 수 있습니다. 명시적 고정·가력 조건을 입력하는 기존 정상응력 검토는 별도 기능으로 유지됩니다.

### 실제 G-code 확인

선택한 플레이트의 51,010,921 byte, 1,986,902줄, 모델 경로 627,302개를 모두 소비했고 여섯 국부 단면이 완료됐습니다. 폭·높이 누락, 무효 선언, 생략 곡선은 없었습니다. 아래 수치는 28.356 MPa 참고응력을 적용한 수치 검산이며 물리적 파단 검증이 아닙니다.

|형상 점검|경로 면적 (mm²)|최소 단면계수 (mm³)|25 mm 굽힘 (N)|같은 힘의 무게 환산|50 mm 굽힘 (N)|
|---|---:|---:|---:|---:|---:|
|1|26.514|6.059|6.873|701 g|3.436|
|2|14.274|2.342|2.657|271 g|1.328|
|3|29.707|7.273|8.250|841 g|4.125|
|4|30.743|7.713|8.749|892 g|4.374|
|5|31.246|7.887|8.946|912 g|4.473|
|6|15.399|2.607|2.957|302 g|1.478|

25 mm 거리의 굽힘과 축방향 당김은 서로 다른 조건입니다. 예를 들어 점검 1의 축방향 참고 하중은 약 752 N이지만 25 mm 굽힘은 약 6.87 N입니다. 큰 당김 수치를 손으로 굽히는 힘으로 해석하지 않습니다. 국부 단면 범위 밖의 고정점과 다른 부품 영역은 검증하지 않았습니다.

### 구현 검증

- 공개 엔진 시험 144개 통과. 사각·중공·회전·겹침·공극·국부 절단·늦은 원본 경로·한도 초과·무효 입력을 포함합니다.
- 독립적인 삼각형 적분의 단면 관성과 1,000,001개 모멘트 방향 비교로 비대칭 단면을 교차 확인했습니다.
- 잘못된 WIDTH/HEIGHT 선언 뒤 이전 유효 치수를 재사용하지 않습니다. 손상된 캐시, 잘못된 단면 형식, 전체 스캔 미완료는 재준비 대상으로 처리합니다.
- 캐시는 원본 SHA, 선택 플레이트, 형상 버전, 국부 범위, 단면 모델 버전과 전체 소비·기록 수를 확인합니다. 보고서 재생성은 저장된 견적 금액을 변경하지 않습니다.

### 배포와 실제 전달 확인

- 2026-10-03 최종 운영 이미지: `sha256:2e9806ad53d5ae0ac961de6d6ce10077d846c1c7b4edf7d768d29a946e867b82`. PrintOps `0.5.11-automatic-load`, 강도 `0.16.0`; API·analysis·viewer·worker 네 서비스의 소스 해시·엔진 버전·네이티브 G-code 모듈과 실행 상태가 일치했습니다.
- 최종 컨테이너 통합시험 363개와 하위 시험 106개 통과. 이미지에서 제외된 Windows 수집기 재시작 시험 3개와 Node 시험 2개는 로컬에서 별도로 모두 통과했습니다. 브라우저 회귀 스크립트 17개, UI 계약 9개도 통과했습니다.
- 실제 웹에서 힘·고정점·방향 입력 13개를 비워둔 채 여섯 자동 하중을 확인했습니다. 기본 25 mm와 펼침 항목의 10·50 mm 거리, g/kg 무게 환산, 축방향 당김이 구분됩니다. 한 항목을 펼쳐도 인접 카드가 불필요하게 늘어나지 않도록 정렬을 수정했습니다.
- HTML 상세보고서의 하중 목록이 비용표를 덮던 변수 충돌을 회귀 검증으로 재현·수정했습니다. 운영 응답의 모든 비용 행과 총액, 자동 하중이 함께 유지되는 것을 확인했습니다.
- 6페이지 상세 PDF에 위치 이미지·단면·여섯 하중·거리·소재 가정·현재 엔진 버전이 들어갑니다. 모든 페이지를 렌더링해 겹침·잘림 없이 확인했습니다. 견적 저장 당시 버전과 현재 보고서 환경은 별도로 표시합니다. PDF와 HTML을 다시 생성해도 저장 견적의 입력·결과 JSON 해시와 44,880원 금액은 바뀌지 않았습니다.

운영 자료와 원본 G-code는 비공개 로컬에 보관합니다. 공개 문서는 수식·집계 검증과 구현 근거만 포함합니다.

## English

Record for strength engine v0.16.0, `LOCAL_DECLARED_ROAD_SECTIONS_V2` and `CAPACITY_SCENARIO_V6_AUTOMATIC_LOCAL_REFERENCE_LOADS`. Local tensile and bending reference forces can be calculated without entering a force or fixture. They are conditional comparisons, not calibrated fracture or allowable loads.

The worker consumes the entire selected source G-code. It intersects declared rectangular model/bridge road envelopes with explicit local section windows, unions overlaps once and preserves holes. Oblique XY roads are supported; support, brims and towers are excluded. Truncated deposition caches and sampled viewer paths cannot substitute for this pass.

The full centroidal area-moment matrix determines the worst normal stress over every unit bending-moment orientation. Two principal axes alone are insufficient, including for diagonal loading of a square. Reference tension is `σref A`, reference moment is `σref Z`, and reference force is `M/L` at explicitly declared 10/25/50 mm arms, with 25 mm as the default. [MIT Beam Stresses](https://web.mit.edu/course/3/3.11/www/modules/bstress.pdf) supports the linear stress relation, not arbitrary part-failure accuracy.

Infill, pattern and walls affect actual road geometry and voids. No nominal-infill multiplier, solid-envelope fallback or arbitrary speed/temperature correction is applied. Unverified mixed-tool relative stiffness withholds numeric forces. Original material-reference area definitions remain recorded, including `UNKNOWN`. Transferring coupon reference stress to homogeneous net-road stress is a disclosed uncalibrated assumption; perfectly bonded local road fragments and shared strain are assumed.

The example uses FusRock ABS XY tensile-break reference 33.36 MPa with the existing 0.85 internal margin, yielding 28.356 MPa. That margin is not experimental calibration or a structural safety factor. The manufacturer's Z reference is separate. [Official FusRock ABS data](https://www.fusrock.com/material/performance/id/106/lang/en).

All 51,010,921 source bytes, 1,986,902 lines and 627,302 model roads were consumed; all six local sections completed. The numerical audit table above records 25 mm bending forces of 6.873, 2.657, 8.250, 8.749, 8.946 and 2.957 N. These differ substantially from axial tension: point 1 gives about 752 N in axial reference tension versus 6.87 N at a 25 mm bending arm. Geometry order is not failure order.

The public engine suite passes 144 tests. An independent triangle-integration oracle and 1,000,001 moment directions cross-check asymmetric-section inertia and the all-direction modulus. Invalid declarations cannot retain prior dimensions. Cache reuse checks source SHA, selected member, geometry/crop/model identities, complete source consumption and record counts. Reports do not mutate saved estimate amounts.

Shear, torsion, buckling, weld contact, delamination, cracks, notches, impact, fatigue, creep and stress concentrations are unsolved. Local cropped sections are not verified complete part load paths; actual fracture can occur below these estimates. The separate explicit-load normal-stress solver remains available.

### Deployment and delivery verification

The final production image on 2026-10-03 is `sha256:2e9806ad53d5ae0ac961de6d6ce10077d846c1c7b4edf7d768d29a946e867b82`, with PrintOps `0.5.11-automatic-load` and strength `0.16.0`. All four API, analysis, viewer and worker services match source hashes and engine identities, run native G-code modules and remain running without OOM or restart.

The final container suite passes 363 tests plus 106 subtests. Its three omitted Windows collector-restart checks and two Node checks pass separately locally. All 17 browser regression scripts and nine UI contracts pass. The live web shows all six forces with 13 force/fixture/direction inputs empty, distinguishes 10/25/50 mm bending from axial tension and avoids stretching adjacent cards when distance details expand.

A detailed HTML variable collision that replaced the cost table with a capacity list was reproduced and fixed with a regression. Live HTML retains all cost rows, totals and automatic forces. All six PDF pages were rendered and visually checked for clipping and overlap, including images, sections, distances, assumptions and version provenance. The saved input/result JSON hash and original 44,880 KRW amount remain unchanged after HTML/PDF generation; the saved engine version is distinguished from the current report environment.

Original G-code and operational artifacts remain private locally. This public record contains formulas, aggregate verification and implementation evidence only.
