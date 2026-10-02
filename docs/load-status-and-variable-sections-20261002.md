# 하중 계산 상태와 가변 단면 / Load status and variable sections

## 한국어

강도 엔진 `0.15.0`과 통합 앱 `0.5.10-load-status`에서 형상 검사 완료, 조건부 응력 계산, 실험 보정 여부를 구분한다. 계산값이 없는 구형 호환 객체는 완료된 형상 후보를 미검증 하중처럼 보이게 했다. 웹은 빈 하중 상세란을 만들지 않고 실제 고정·작용점·방향을 입력하는 동작을 제공한다. 후보 검사 좌표를 물리적 작용점으로 자동 입력하지 않는다.

계산 범위를 연결된 일정 단면 보에서 구간별로 단면이 달라지는 보까지 확장한다. G-code에 선언된 경로 폭·높이의 직사각형 재료 영역을 합집합으로 구성하고, 구간마다 면적·도심·전체 단면 2차 모멘트 행렬을 계산한다. 인필 100%라는 설정을 꽉 찬 재료 단면으로 대체하지 않는다. 축력의 `N/A`와 굽힘의 단면별 응력을 평가한다. 일정 단면 구간에서 응력은 길이 좌표에 선형이므로 양 끝 극한을 확인한다. 단면 변화 경계의 양쪽도 모두 평가한다.

인접 구간은 양의 면적을 가진 공통 재료 단면이 있어야 한다. 모서리나 선만 닿은 구간은 하나의 보로 연결하지 않는다. 단일 툴·축에 평행한 경로·충분히 긴 보·끝단 전체 단면 고정·반대쪽 끝단 집중하중의 범위를 유지한다. 비틀림, 분리 단면, 비스듬한 경로, 불완전한 기록, 계산 한도 초과에는 구체적인 한국어 제한 사유를 표시한다.

반환하는 `section_profile`은 점검한 구간별 재료 단면이며, `section`과 `critical_section`은 이 명목 응력 모델의 지배 단면을 가리킨다. 화면과 보고서는 MPa 또는 MPa/N, 점검 단면 수, 지배 위치와 경로 가정 재료 면적을 표시한다. 전체 하중 조건의 결과를 모든 형상 후보의 개별 응력으로 복제하지 않는다.

해석은 평면 유지·작은 선형 탄성 변형·균질 완전 접합을 가정한다. 단면 변화의 응력 집중, 실제 공극·접합, 전단·균열·좌굴·피로·크리프는 해결하지 않는다. `failure_load_n=null`, `is_failure_prediction=false`, `empirically_validated=false`를 유지한다. 조건부 응력 계산 성공은 실제 파단하중이 검증됐다는 뜻이 아니다. 근거는 [MIT David Roylance, Stresses in Beams](https://web.mit.edu/course/3/3.11/www/modules/bstress.pdf)의 단면 평형·도심·굽힘 응력 관계와 선형 탄성 적용 조건이다. 소프트웨어 시험은 출력물 파괴시험이 아니다.

분석용 경로 캐시는 출처를 유지하면서 저장 한도, 치수 누락, 비평면 경로, 툴 오류, 곡선 제외를 구분한다. 이미 잘린 기존 기록을 완전한 자료로 바꾸지 않는다. 확인한 대용량 기존 사례는 기록 451,958개, `truncated=true`였으며 이 자료의 부품 응력은 계속 보류된다.

검증 사례는 100×10×2 mm 보의 90 mm 자유 길이에서 2 N에 27 MPa, 50 mm 지점부터 2×2 mm로 좁아지는 보의 1 N에 37.5 MPa/N이다. 반대쪽 고정에서도 동일 응답을 확인하며, 모서리 접촉과 비틀림은 보류한다. 실제 API→견적 저장→보고서의 성공 전달과 입력 변경 후 늦게 도착한 웹 결과 폐기를 회귀 시험한다. 패키지 전체 시험 115개, 통합 Docker 시험 343개·하위 검사 72개가 통과했다. 조건부 생략 5개, 의존성 사용 중단 예고 2개가 있다. Node의 후보 상태·하중 입력·요약·뷰어 밀도·캐시·그리기 회귀 시험과 문법 검사도 통과했다. 최종 운영 검증 결과는 [시스템 검증 기록](system-validation.md)에 추가한다.

2026-10-03 운영 확인에서 앱 `0.5.10-load-status`, 강도 `0.15.0`을 확인했다. 네 서비스가 테스트 이미지 `sha256:6e7c40c29c125b77913240316b13c2d6e94f9a654d839e4d05224ce77c3a6671`과 소스 해시·네이티브 스캐너가 일치했으며 재시작은 0회였다. 기존 파일의 6개 후보는 모두 “형상 검사 완료”를 표시하고 빈 하중 상세란은 없어졌다. 후보 버튼은 해당 후보를 선택하고 하중 입력을 열었으며 물리 좌표를 자동으로 채우지 않았다. 브라우저 오류 로그는 비어 있었다. 대용량 사례의 별도 진단 요청은 한국어 저장·처리 한도 사유와 `WITHHELD`를 반환했다. 진단 견적을 고객 이력에 저장하지 않았다.

## English

Strength `0.15.0` and host `0.5.10-load-status` distinguish completed geometry screening, conditional stress calculation and experimental calibration. Empty legacy capacity envelopes no longer create misleading scenario panels. Candidate inspection coordinates are not automatically treated as physical load points, and a global load-case result is not copied to every geometry candidate.

The bounded solver now evaluates piecewise constant, connected, axis-aligned beam sections. Each interval uses the union of declared rectangular deposition envelopes, local area, centroid and the full second-moment matrix. Axial `N/A` and bending normal stress are evaluated at both interval endpoint limits, including both sides of section changes. Adjacent intervals require positive-area transverse overlap. Nominal full-infill metadata does not replace deposited geometry.

The returned section profile, governing nominal plane and stress appear separately from failure validation. Full-section end restraint, opposite-end point loading, slenderness, complete unsampled geometry, single-tool and no-torsion guards remain. Unsupported roads and cache limits have specific reasons. A checked large existing sidecar remained truncated; this release does not fabricate a stress result for it.

Planar sections, small linear-elastic deformation and homogeneous perfect bonding are explicit assumptions. Stress concentrations, shear failure, printed voids, bonding, cracks, buckling, fatigue and creep are unresolved. Failure loads remain null and empirical-validation flags remain false. [Roylance's MIT beam-stress module](https://web.mit.edu/course/3/3.11/www/modules/bstress.pdf) provides the section-equilibrium basis, not experimental validation of printed parts.

Analytical regressions check 27 MPa under 2 N for the constant beam, 37.5 MPa/N for a stepped beam, reversed restraint invariance, and rejection of edge-only contacts and torsion. Host regressions exercise successful API, quote and report delivery plus stale response handling. All 115 package tests and 343 integrated Docker tests with 72 subtests passed; five conditional checks were skipped and two dependency deprecations remain. Node candidate-status, load-input, summary, density, cache and drawing regressions plus syntax checks passed. Final deployment evidence is recorded in the system validation document.

Production verification on 2026-10-03 confirmed host `0.5.10-load-status` and strength `0.15.0`. All four services matched the tested image, source hashes and native scanners, with zero restarts. All six existing candidates displayed completed geometry, without empty capacity details. Candidate actions selected the region and opened the load panel without inventing physical coordinates; inspected browser errors were empty. The separate large-file diagnostic remained withheld with a Korean cache-limit reason and was not saved as a customer quote.
