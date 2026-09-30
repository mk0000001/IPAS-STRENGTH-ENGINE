# 2026-10-01 릴리스 검증 / Release validation

## 한국어

강도 엔진 **v0.12.0**, 가격 엔진 **v0.10.0**, G-code 엔진 **v0.26.0**을 PrintOps **v0.4.2-profile-pricing**에 통합했다. 실제 실행 중인 네 서비스의 버전·소스 해시 일치와 재시작 0회를 확인했다.

### 검증 결과

- 강도 패키지 103개 시험과 25개 하위 시험, 가격 패키지 22개 시험 통과.
- 배포 이미지 통합 시험 256개 통과, 4개 제외, 13개 하위 시험. 제외된 시험을 통과로 계산하지 않았다.
- 실제 웹에서 명명된 소재 프로파일의 가격 선택, 포장 중량·입고 배송비·부가세 포함 가산액의 중량 배분, 새 견적 저장을 확인했다. 다른 브랜드의 기본 가격을 명명된 프로파일에 자동 대입하지 않는다.
- 저장된 과거 견적은 변경하지 않았다. 기존 뷰어의 반복 조회 결과 및 26,146개 경로가 있는 레이어 조회를 확인했다.
- 상세 PDF를 두 번 생성하고 네 페이지의 표, 모델 이미지, 지역 처리 고지와 저장 당시/현재 보고서 엔진 버전 구분을 시각 확인했다.
- 마지막 독립 검토에서 불완전한 원호 경로가 완전한 적층 데이터로 취급되는 문제를 수정했다. 웹 검증에서는 하중 입력 스크립트 제공 경로 누락을 수정하고 진입점 스크립트 HTTP 응답 시험을 추가했다.

### 과학적 적용 범위

공개 180개 시편 자료를 비교 자료에 반영했지만 현재 부품의 파단하중을 실증한 것은 아니다. 진단용 학습 108개·보류 54개·제외 18개의 분할에서 MAE 0.802253 MPa였으며 평균 기준선보다 개선되지 않았다. 독립 연구 또는 실제 부품 검증으로 해석하지 않는다. [연구 검토](research-update-20261001.md), [공정 보정 기준](process-calibration.md)을 함께 참고한다.

외벽 형상 후보를 속이 찬 단면으로 가정하여 힘으로 환산하지 않는다. 실제 경로 단면, 명시적인 고정 영역·작용점·방향이 있어도 지원되는 단일 재료 직선 보 범위에서만 응력을 평가한다. 미지원 형상·불완전 경로·미검증 소재 보정은 결과를 보류하며 실제 파단하중으로 표시하지 않는다. 적용 승인된 공정 강도 보정 모델은 아직 없다.

## English

Strength **v0.12.0**, quote **v0.10.0**, and G-code **v0.26.0** were integrated into PrintOps **v0.4.2-profile-pricing**. All four running services matched the deployed versions and source hashes, with zero restarts at verification.

### Validation results

- Strength: 103 tests and 25 subtests passed. Quote: 22 tests passed.
- Deployment-image integration: 256 passed, 4 skipped, 13 subtests. Skips are not passes.
- Live web checks covered named-profile pricing, package weight, inbound shipping, VAT-inclusive add-on allocation, and saving a new quote. Named profiles no longer silently inherit another brand's generic price.
- Historical saved quote amounts remained unchanged. Repeated viewer responses and a layer containing 26,146 segments were checked.
- Two detailed PDFs were generated; four pages were visually checked for tables, model illustrations, local-processing notice, and separation of historical quote versions from current report-rendering versions.
- Independent review found and fixed incomplete arc paths being accepted as complete deposition data. Browser verification found and fixed a missing route for the load-case script; an entry-script HTTP regression test was added.

### Scientific limits

The public 180-specimen dataset is comparison evidence, not validation of an arbitrary printed part. The diagnostic split used 108 training, 54 held-out, and 18 excluded records, with MAE 0.802253 MPa and no improvement over the mean baseline. This is neither independent-study nor part-level validation. See the [research review](research-update-20261001.md) and [calibration gates](process-calibration.md).

Outer-envelope candidates are not treated as solid cross-sections and converted to force. Actual deposition sections and explicit fixtures/load points/directions support stress evaluation only within the implemented single-material straight-beam domain. Unsupported geometry, incomplete paths, and unvalidated material calibration withhold predictions. No process-strength calibration model is approved for production prediction yet.
