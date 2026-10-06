# 연구자료 갱신 / Research update — 2026-10-01

[한국어](#한국어) · [English](#english)

## 한국어

공개 논문·보충자료에서 **PLA·ABS·PETG 시편 180행과 조건별 평균/표본 표준편차 30개**를 새로 추출했다. 별도로 공정 논문의 평균 최대 인장하중 25행과 PPA-CF 시험온도별 인장응력 9행을 구조화했다. 논문 평균값과 개별 시편값은 별도 자료이며 합쳐서 독립 시험 수로 세지 않는다. 기존 [연구 근거와 실증 범위](research-evidence.md)의 감사 자료를 재사용했다.

현재 이 갱신은 **범용 공정 보정계수나 임의 부품의 파단강도 정확도를 입증하지 않는다.** 소재군 18개 모두를 검토 범위에 넣었으며, 보정 가능한 근거가 없는 소재는 부족 상태로 유지했다. 자체 물리 시험이나 원저자 연락은 수행하지 않았다.

### 우선 자료에서 확인한 사항

|원출처|확인 내용|사용 범위와 제한|
|---|---|---|
|Grigoriev 등, [Scientific Reports, 2024](https://doi.org/10.1038/s41598-024-79213-5), 공식 보충자료 1|eSUN PLA·ABS·PETG, 소재별 60개 시편, 10개 조건×n=6. Grid/Combs/Triangle의 25·50·75%, Lateral 100%. 보충표의 `PTEG`는 원문 Methods의 PETG와 대응시키고 원표기도 보존.|개별 보고 응력과 치수 자료이며 하중–변위 원시곡선은 아니다. 정확한 제품 grade와 응력 면적 정의 미확인. Methods에 층 높이 0.2와 0.4 mm가 함께 있어 단일값으로 채우지 않음. 인장·전단·굽힘 혼용 금지.|
|Menargues 등, [Processes, 2025](https://doi.org/10.3390/pr13092733)|PLA·ABS·PETG, 조건별 n=5. 벽 수 1–5의 15개 평균, PLA·ABS 층 높이 0.10–0.30 mm의 10개 평균을 본문에서 추출. 조건: grid 20%, 210°C, 45 mm/s.|응답은 **최대 인장하중 N**이다. MPa로 변환하지 않았다. 제품 grade·벽 수 실험의 층 높이·수치 SD 미확인. 서로 다른 단일변수 실험을 곱셈 계수로 합치지 않는다. 본문의 일부 증감률·증가/감소 설명에 산술 불일치가 있다.|
|Desouky 등, [Mendeley Data v1](https://doi.org/10.17632/zvt28hz3kf.1)|공식 API로 47개 폴더 전체와 루트 목록 확인: 사진 960개, G-code 211개, TXT 4개. TXT 4개의 공식 SHA-256 대조 통과.|README에 기술된 결과 스프레드시트는 이 버전의 파일 목록에 없다. 따라서 PETG 수치 원자료 확보로 세지 않는다. 저장소 CC BY 4.0과 메타데이터 파일 CC BY-SA 4.0 표기가 충돌하여 원자료를 재배포하지 않았다.|
|[PPA CF15 연구, Polymers, 2026](https://doi.org/10.3390/polym18121422)|Fiberlogy PPA CF15, Creality K1 MAX, 수평 ±45°, linear 100%, 노즐 290°C/베드 100°C/챔버 50°C, 80 mm/s, 층 0.2 mm, 벽 5. 시험온도별 n=3, Table 2의 9개 UTS 평균과 ±값 추출.|변수는 **시험온도 20–180°C**이며 노즐온도가 아니다. 건조 80°C 12 h, 잔류수분 미측정. ±값의 통계 정의를 확인하지 못해 SD로 단정하지 않았다. 해당 grade 비교에만 사용한다.|

원문과 데이터 DOI는 같은 실험 계보이면 하나로 묶는다. Scientific Reports 논문과 보충표는 두 개의 독립 연구가 아니다. 원문·그림·보충 DOCX·개별 시편표는 이 공개 저장소에 복제하지 않는다. Scientific Reports XML은 CC BY-NC-ND 4.0을 표시하며, 기타 자료도 각 원출처 라이선스를 따른다.

### 같은 연구 내 보류 조건 비교

Scientific Reports의 각 소재·패턴에서 **25%와 75%의 시편만**으로 평균 끝점 선형보간을 만들고 50% 시편 6개 전부를 보류했다. Grid/Combs/Triangle 3개 패턴을 사용했으며, 패턴이 달라지는 Lateral 100%는 제외했다. 관측응력에 대한 시편별 절대오차와 절대백분율오차를 평균했다.

|소재|보류 시편 수|MAE (MPa)|MAPE|
|---|---:|---:|---:|
|PLA|18|0.495|2.530%|
|ABS|18|0.551|4.011%|
|PETG|18|1.361|8.536%|

이는 데이터 구조를 확인한 후 정한 **동일 연구 내 조건 보류 진단**이다. 독립 실험실·다른 grade·다른 형상에 대한 검증도, 현재 엔진의 정확도도 아니다. 생산 엔진에 해당 보간식이나 배율을 적용하지 않았다. 등록 소재 전체의 독립 외부 검증 시편 수는 여전히 **0**, 정확도는 **미확정**이다. 같은 표의 전체값으로 보간하고 같은 표를 다시 맞추는 재현과도 구별한다.

### 등록 소재 전체의 근거 상태

`비교`는 확인된 특정 조건의 문헌 비교가 있다는 뜻이다. `부족`은 아래 1차 연구 후보가 있어도 현재 프로파일에 적용할 grade·공정·면적·독립 검증 정보가 부족하다는 뜻이다. 모든 행의 범용 강도 예측 지원은 미확정이다.

|소재|상태|1차 자료 또는 남은 한계|
|---|---|---|
|PLA / ABS / PETG|비교|위 두 논문; 소재별 관측·조건 보류 진단|
|ASA|비교|기존 [ASA SENB 연구](https://doi.org/10.3390/ma17215207)와 [Zenodo 원자료](https://doi.org/10.5281/zenodo.14065523) 감사 재사용|
|PETG-CF|부족|[층간 인장·열처리 연구](https://doi.org/10.1016/j.addma.2019.100922); grade별 공정 행 미확인|
|PETG-GF|부족|[PETG/GF 인장 연구](https://doi.org/10.1016/j.proeng.2017.02.245), [공정 최적화 연구](https://doi.org/10.1007/s00170-026-19068-4); 원자료 미확보|
|ABS-CF|부족|[층간 파괴인성](https://doi.org/10.1016/j.addma.2018.02.023)을 인장강도로 대체하지 않음|
|ABS-GF|부족|[단섬유·연속섬유 비교](https://doi.org/10.1002/pc.71317); 보강 형태 분리 필요|
|PA6-CF|부족|[인장·피로 연구](https://doi.org/10.3390/polym15030507); 수분·grade 일치 부족|
|PA6-GF|부족|[시험온도 연구](https://doi.org/10.35860/iarej.862304)는 **단유리섬유 PA6**이며 ASTM D638 시험온도 −20/20/40/60°C를 비교함. 노즐온도 실험이나 연속 GF 연구로 분류하지 않음|
|PA12-CF|부족|[층간 파괴 연구](https://doi.org/10.1016/j.compstruct.2019.02.005); 물성 구분 필요|
|PA12-GF|부족|[FFF 마찰·마모 연구](https://doi.org/10.3390/polym18182239)의 인장 TDS 인용은 독립 인장실험이 아님; SLS/MJF 자료 제외|
|PPA-CF|비교|위 Fiberlogy CF15 시험온도 연구|
|PPA-GF|부족|적합한 공개 FFF 시편 강도 원자료를 확인하지 못함|
|PPS-CF|부족|[단섬유 열이력 연구](https://doi.org/10.1177/00219983231194391); grade·응답 행렬 미확인|
|PC|비교|기존 [층간 전단 연구](https://doi.org/10.1016/j.jmrt.2022.12.147), [NIST 벤치마크](https://doi.org/10.1007/s40192-020-00188-y)|
|TPU / TPE|부족|[엘라스토머 인장 연구](https://doi.org/10.1016/j.polymertesting.2020.106687); 경도·grade·변형률속도 일치 부족|

## English

This update extracts **180 specimen rows and 30 condition means/sample standard deviations** for PLA, ABS, and PETG from the Scientific Reports supplement. Separately, it structures 25 reported mean maximum tensile loads from the Processes paper and nine PPA-CF mean tensile stresses across test temperatures. Aggregate observations and specimen records are separate; they are not added together as independent experiments. Earlier audits in [Research evidence](research-evidence.md) are reused.

All **18 registered material families** were considered. No physical tests or author contact were performed. The update does not establish universal process multipliers or arbitrary-part failure accuracy.

The [Scientific Reports study](https://doi.org/10.1038/s41598-024-79213-5) supplies six specimens per material/condition: Grid, Combs, and Triangle at 25/50/75% infill and Lateral at 100%. Its supplement spells PETG `PTEG`; extraction preserves that original label and normalizes it against the article Methods. Exact eSUN grades and the stress denominator remain unverified. Methods report both 0.2 and 0.4 mm layer heights. These are specimen-level reported stresses and dimensions, not raw instrument curves.

The [Processes study](https://doi.org/10.3390/pr13092733) reports **maximum tensile load in N**, not interchangeable MPa. Five specimens were tested per condition. Wall-count and layer-height series retain grid 20%, 210°C, and 45 mm/s context. Product grades, numerical SDs, and the wall-series layer height are unresolved. Separate one-factor series must not be multiplied together. Some narrative percentage/direction statements contradict the reported values.

The complete [Mendeley v1](https://doi.org/10.17632/zvt28hz3kf.1) inventory contains 960 photographs, 211 G-code files, and four TXT files across the root and 47 folders. The four downloaded TXT files match official SHA-256 hashes. The measurement workbook described by its README is absent from the inventory. Consequently, this source does **not** count as acquired PETG tensile outcomes. Repository CC BY 4.0 and embedded metadata CC BY-SA 4.0 labels conflict.

The [PPA-CF study](https://doi.org/10.3390/polym18121422) identifies Fiberlogy PPA CF15 and provides nine Table 2 UTS means at **test temperatures** from 20–180°C, with n=3 per temperature. Nozzle temperature stayed at 290°C. Printing used a Creality K1 MAX, horizontal ±45° linear 100% infill, 0.2 mm layers, five contours, 80 mm/s, bed 100°C, and chamber 50°C. Filament was dried at 80°C for 12 h; residual moisture was not measured. The extracted ± values are not asserted to be SD without verifying their definition.

For an explicitly **within-study diagnostic**, endpoint means from 25% and 75% infill predicted all six held-out 50% specimens per material/pattern by linear interpolation. The three patterns were analyzed separately; Lateral 100% was excluded. There were 18 held-out specimens per material. Mean specimen-level errors were PLA **0.495 MPa / 2.530%**, ABS **0.551 MPa / 4.011%**, and PETG **1.361 MPa / 8.536%** (MAE/MAPE). This protocol was chosen after inspecting the dataset structure. It is not prospective validation, independent-study generalization, or engine accuracy. No interpolation coefficients were applied to the production engine.

Family status is **comparison only** for PLA, ABS, PETG, ASA, PPA-CF, and PC, within the specific source/property limits in the Korean table. It is **insufficient** for PETG-CF/GF, ABS-CF/GF, PA6-CF/GF, PA12-CF/GF, PPA-GF, PPS-CF, TPU, and TPE. Listed primary papers are research candidates where full grade-matched extraction is incomplete. Chopped and continuous fiber, FFF and SLS/MJF, and tensile/flexural/shear/fracture properties remain separate. TDS values quoted in research papers are not independent tests.

Correction verified on 2026-10-07: [DOI 10.35860/iarej.862304](https://dergipark.org.tr/en/pub/iarej/article/862304) studies **short-glass-fiber PA6**, not continuous glass fiber. Its −20/20/40/60°C settings are ASTM D638 **test temperatures**, not extrusion temperatures. The earlier Korean row incorrectly implied a continuous-fiber source; runtime coverage already classified it as short GF.

External independent validation remains **n=0 across all registered families**, with accuracy undetermined. Article and supplement share one experimental lineage. Source texts, figures, DOCX files, and specimen tables are retained privately and are not reproduced in this public repository. The Scientific Reports XML specifies CC BY-NC-ND 4.0; other source rights remain with their respective licensors.
