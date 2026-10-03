# 프로파일 이름 매칭과 원본 재분석 / Profile matching and source reanalysis

## 한국어

### 변경 범위

PrintOps 통합 앱의 프로파일 해석 규칙을 가격 선택과 소재 강도 참고자료 선택에 공통 적용한다. 원본 `sku_profile`과 G-code의 실제 소재·노즐 설정은 보존한다. 이 변경은 소재 식별을 보완하며 물성이나 실제 파단하중의 실증 정확도를 높였다는 의미가 아니다.

프로파일 형식은 `브랜드 / 소재·제품 등급 / 출력 설정 / 노즐 지름`이다. `_`, `*`, 공백과 노즐 지름의 괄호를 인식한다. 사용자가 확인한 `High Flow`는 출력 설정이다. `ABS-HF`, `PA6-CF`, `ABS-GF`, `PLA+` 같은 제품 등급은 출력 설정으로 지우지 않는다.

| 프로파일 예시 | 제품 식별 | 별도 프로파일 정보 |
|---|---|---|
| `FusRock_ABS_Default_0.2` | FusRock ABS | Default, 0.2 mm |
| `퍼즈락*ABS*HighFlow*(0.4)` | FusRock ABS | High Flow, 0.4 mm |
| `Bambu_PA6-CF_Default_0.4` | Bambu PA6-CF | Default, 0.4 mm |
| `FusRock_ABS-HF_Default_0.4` | FusRock ABS-HF | Default, 0.4 mm; 기본 ABS로 대체하지 않음 |

소재 이름이 없는 `FusRock_Default_0.4`는 활성 G-code 소재를 확인한 경우에만 해당 소재를 힌트로 사용한다. 복수 소재 파일에서 하나의 힌트를 모든 프로파일에 적용하지 않는다. 브랜드·소재 충돌, 알 수 없는 등급, 명시적 빈 이름, 슬롯 불일치나 연결 근거가 없는 일부 활성 소재는 자동 제품 매칭을 막는다. 사용자가 실제 사용 제품을 선택하면 그 선택에 맞춰 식별 정보를 다시 만든다.

일반 G-code에서 제품 이름이 헤더에만 저장된 경우에는 원본 툴 번호에 해당하는 헤더 슬롯을 확인해 연결한다. 원본 소재별 행과 연결 근거를 보존하며, 서포트 소재나 사용량이 0인 행을 제거한 뒤 순번으로 제품을 끼워 맞추지 않는다. 제품 이름 정보가 전혀 없는 파일은 기존 일반 소재 가격 정책을 사용할 수 있지만 실제 제조사·제품이 확인됐다고 표시하지 않는다. 정확히 확인된 FusRock 카탈로그 강화재 제품을 슬라이서가 기본 수지 유형으로 기록한 경우에는 해당 제품 등급을 유지한다. 강화재에 기본 수지의 강도값을 대신 적용하지 않는다.

가격 매칭은 기존 검증 가격 카탈로그를 사용한다. FusRock ABS의 기존 운영 기준은 구매가 22,000원 + 필라멘트 입고 배송비 4,000원 + 포장당 가산액 2,000원 = 28,000원/1 kg이다. 미확인 제품의 가격이나 다른 등급의 강도값을 새로 만들어 채우지 않는다.

### 재분석과 온도 경고

사용자가 지정한 원본 3MF를 서버 저장본과 SHA-256으로 대조한 후 같은 프로젝트의 가장 최근 파일 항목에 새로운 분석 작업을 연결했다. 원본은 1,986,902줄, 464개 레이어다. 재분석은 약 27.3초에 성공했고 기존 견적은 변경하지 않았다. 완성품 취약 후보 6곳의 원본 경로·명령 체적 분석은 완전한 상태였다.

`INDEXED_NOZZLE_HEATER_MAPPING_UNVERIFIED`는 `M104 S280 T0` 및 종료 시 `M104 S0 T0/T1`의 물리 히터 번호를 논리 소재·툴 번호와 연결할 근거가 부족하다는 경고다. 데이터에서는 경고를 유지하고 웹에서는 분석 실패와 구분하는 한국어 안내를 제공한다. 이후 노즐 280°C, 베드 110°C, 챔버 65°C의 명령값이 읽혀도 실제 센서 온도나 용융 접합강도가 측정됐다는 뜻은 아니다.

기존 국부 경로 단면·명령 체적 모델에서 최우선 후보는 228번째 레이어의 좁아지는 끝 연결부다. 같은 25 mm 모멘트 암 가정의 정적 굽힘 참고 하중은 약 1.80 N, 약 183 gf이다. 이는 균질 단면에 소재 시편 참고값을 전달한 비교 계산이며 실제 파단하중·허용하중이나 층간 박리 실측값이 아니다.

### 버전과 검증 기록

통합 앱은 `0.5.15-profile-match`로 구분한다. 공개 엔진 코드는 이 작업에서 변경하지 않으므로 G-code `0.27.0`, 강도 `0.19.0`, 가격 `0.13.0`은 유지한다. 조회 시 현재 원본 메타데이터에서 식별 정보를 재생성해 가격 선택과 강도 참고자료에 공통 적용한다. 저장 견적은 재계산하지 않는다.

2026-10-03 최종 검증과 실제 배포 결과는 다음과 같다.

| 검증 범위 | 결과 |
|---|---|
| 전체 서버 통합 검사 | 530개 통과, subtest 148개 통과, 189.87초 |
| Docker 환경에서 제외된 검사 | 6개; Windows·Node 환경에서 별도 실행해 6개 모두 통과 |
| 발견된 API·강화재 회귀 4개 | 수정 후 모두 통과; 여러 파일 견적·PDF 묶음과 통합 PDF, 플레이트 선택, FusRock 가격, 강화재 공식 카드 포함 |
| 독립 서버·웹 매칭 검사 | 161개 일치, 불일치 0개 |
| 공식 소재 참조 보존 | FusRock 46개 제품 × Default/High Flow, 92개 확인 |
| 변경된 원본 근거의 이전 식별 재사용 | 16개 모두 차단 |
| 웹 회귀 검사 | JS 검사 파일 11개, 집중 사례 26개, UI 계약 10개 통과 |
| 운영 배포 | API·analysis·viewer·worker 4개 서비스에서 현재 소스 해시 일치, native 스캐너 사용, 재시작 0회 |
| 실제 웹·보고서 | 새 자산 버전, FusRock ABS 프로파일·28,000원/kg 기준, 닫힌 기술 코드, 취약 후보 6개, 상세 HTML 보고서의 현재 앱·엔진 버전 확인 |

운영 이미지 식별자는 `sha256:cbf58e8ad1f041a80ac42dcbfb028d015e77023db9ed674ae1c95b89cd63a61d`다. 기존 운영 견적 2개는 재분석 전후 동일했다. 이 결과는 해당 원본과 회귀 사례의 소프트웨어 검증이며 출력물의 실제 파단하중을 실증한 결과는 아니다.

## English

### Scope

PrintOps applies one profile interpretation rule to price selection and material strength references while preserving raw profile names and actual G-code material/nozzle settings. This is an identity correction, not evidence of improved empirical breaking-load accuracy.

Names contain brand, material/product grade, print preset and nozzle diameter. Underscores, asterisks, whitespace and parentheses around the diameter are recognized. The user confirmed that `High Flow` is a print preset. Compound grades such as ABS-HF, PA6-CF, ABS-GF and PLA+ are preserved.

An absent material name can use a verified active G-code material hint, with provenance. A mixed-material file cannot apply one hint to every profile. Conflicting identities, unresolved grades, explicitly blank names and missing active profiles without consistent source-slot evidence block automatic product matching. Explicit actual-spool selections regenerate identity metadata.

For plain G-code that stores names only in its header, binding uses the original tool number and matching configuration slot, preserving the raw row and provenance. Filtering support or zero-consumption rows does not create a new product index. Complete absence of product metadata retains the established generic-material price policy without claiming a verified spool identity. A base-resin slicer type can coexist with an exact reinforced product from the verified FusRock catalog; the reinforced grade never borrows base-resin strength values.

### Source reanalysis and warning

The authorized source archive matched the server SHA-256. A fresh job was linked to the latest file entry in the same project: 1,986,902 lines, 464 layers, approximately 27.3 seconds, six complete local screening candidates. Saved estimates were preserved.

Indexed nozzle commands, including `M104 S280 T0` and shutdown commands for T0/T1, do not prove a physical heater-to-material mapping. The warning remains in analysis data and is presented separately from a failed scan. Commanded nozzle/bed/chamber temperatures of 280/110/65°C are not measured substrate temperatures or validated weld strengths.

The existing local-section model selects a terminal root at layer 228. Its conditional 25 mm static bending comparison is about 1.80 N (183 gf). It is not a measured breaking force, allowable load or interlayer delamination measurement.

### Release identity

Host app: `0.5.15-profile-match`. Public package code is unchanged: G-code `0.27.0`, strength `0.19.0`, quote `0.13.0`.

### Final verification and deployment

- Full server suite: **530 passed, 148 subtests passed**, 189.87 seconds. All six platform-specific Docker skips passed separately on Windows with Node.
- Four discovered API/material-reference regressions passed after correction, including per-file quotes, PDF bundles and combined PDFs, plate selection, FusRock pricing and reinforced-product facts.
- Independent cross-check: **161 server/browser cases**, zero mismatches; **92 exact official references** across 46 FusRock products and two presets; **16 stale provenance cases rejected**.
- Web checks: 11 JavaScript regression files, 26 focused cases and 10 UI contracts passed.
- All four production services ran the same checked source and image with native scanning and zero restarts.
- The actual browser showed the new asset version, FusRock ABS profile, 28,000 KRW/kg basis, collapsed technical code and six local candidates. The detailed HTML report showed current app/package versions. The two pre-existing production estimates remained unchanged.

Production image: `sha256:cbf58e8ad1f041a80ac42dcbfb028d015e77023db9ed674ae1c95b89cd63a61d`. These are software checks of the authorized source and regression cases, not empirical validation of part breaking loads.
