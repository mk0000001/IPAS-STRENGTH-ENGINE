# D01 Supporting 데이터 검토 / Supporting data qualification

## 한국어

D01 [공식 Zenodo record](https://zenodo.org/records/21939238)의 작은 [Supporting Files.zip](https://zenodo.org/api/records/21939238/files/Supporting%20Files.zip/content)을 확인했다. 크기는 **255,838 bytes**, SHA-256은 `70b560238c50647691e1b397864340b35d2bc8a29822ac11c555111a4bf7fdf2`이며 기존 기록과 일치한다. 해시 일치는 내용 무결성 확인이고 측정값·출처 진실성의 독립 인증은 아니다. [공식 API](https://zenodo.org/api/records/21939238)는 관련 논문 식별자를 제공하지 않아 연결 Methods 논문은 확인되지 않았다.

XLSX에는 35조건의 설계별 `Toughness` 값이 있다. 메타데이터와 체크리스트는 초기 LHS 15설계와 sequential B1–B4의 각 5설계, 설계당 3반복을 선언한다. 이것은 원시 시편 105개를 확인한 수가 아니다. B1–B4는 순차 설계 batch이며 독립 제조 campaign의 증거가 아니다. DOI는 publication/version 식별자이다. workbook에는 row→design→replicate 파일 mapping이 없으며 동일 수치로 시편 ID나 독립성을 추정하지 않았다.

공정 메타데이터에서 speed의 mm/s와 layer height의 mm는 확인했다. 공식 record의 재료 표기는 tough PLA/ABS이며 printer는 UltiMaker S7이다. 특정 필라멘트 grade·lot·conditioning은 확인되지 않았다. 계산 노트북은 외부 CSV의 `Stress`와 `Strain`을 변환 없이 적분하고 세 결과를 평균한다. **force/stress/strain 단위, gauge area/length, engineering/true 정의와 first-failure endpoint는 supporting 파일에 없다.** strain의 %/비율 차이도 해결되지 않아 수치에 물리 단위를 부여하지 않았다. 이 적분은 `G_Ic`/`K_Ic` 측정 근거가 아니다.

검토 범위는 supporting 파일이며 **3,882,395,590바이트 Raw Data ZIP과 그 CSV는 검사하지 않았다.** 원시 단위·치수·manifest·시험 조건·first-failure 근거가 추가로 필요하다. 동일 설계의 반복/집계/파생 값은 같은 fold로 묶어야 하며 같은 캠페인의 holdout은 내부 진단이다. 독립 target-part 파괴 검증은 아직 없다. 계산·카탈로그·계수·테스트를 변경하지 않았고 모델을 승인하지 않았다(`APPROVED_MODEL_IDS = ()`).

## English

The small [Supporting Files.zip](https://zenodo.org/api/records/21939238/files/Supporting%20Files.zip/content) associated with the [official D01 Zenodo record](https://zenodo.org/records/21939238) was inspected. Its **255,838-byte** payload matches the previously recorded SHA-256: `70b560238c50647691e1b397864340b35d2bc8a29822ac11c555111a4bf7fdf2`. This establishes content integrity, not independent authentication of measurements or source claims. The [official API](https://zenodo.org/api/records/21939238) supplies no related-publication identifier; a linked Methods paper was not verified.

The workbook contains 35 design-level toughness values. Supporting metadata/checklist declare 15 initial LHS designs and five designs per sequential batch B1–B4, with three repeats per design. This is not verification of 105 raw specimen records. Sequential design batches are not certified independent manufacturing campaigns; a DOI identifies a publication/version. The workbook lacks an explicit row-to-design-to-replicate-file manifest. Equal numbers were not used to infer specimen identity or independence.

Processing metadata specifies print speed in mm/s and layer height in mm. The record names tough PLA/ABS and an UltiMaker S7 printer; filament grade, lot and conditioning remain unverified. The calculation notebook integrates external CSV stress against strain without unit conversion, then averages three integrals. **Force/stress/strain units, gauge area/length, engineering/true conventions and a first-failure endpoint are absent from the supporting files.** Percent versus dimensionless strain is unresolved, so no physical unit was assigned. The integral does not establish `G_Ic` or `K_Ic`.

This is a supporting-only inspection: the **3,882,395,590-byte Raw Data archive and its CSVs were not examined**. Units, measured geometry, lineage manifest, test conditions and endpoint evidence are still required. Replicates, aggregates and derivatives of one design must stay in one fold; a holdout within the same campaign is an internal diagnostic. Independent destructive target-part validation remains absent. No calculations, catalogue values, coefficients or tests changed, and no model was approved (`APPROVED_MODEL_IDS = ()`).
