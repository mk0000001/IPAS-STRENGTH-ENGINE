# 공정 열이력과 층간 파괴의 추가 근거 / Additional process-thermal and interlayer-fracture evidence

[한국어](#한국어) · [English](#english)

## 한국어

검토일: 2026-10-03. 이 문서는 기존 `research-evidence.md`, `research-update-20261001.md`, `weakness-research-redesign-20261003.md`에서 **완료하지 않았던 정량 전사와 새로운 공개 데이터**를 기록한다. 표적 문헌 검토이며 전 세계 논문의 전수 조사라는 뜻은 아니다. 이 연구 문서 작성 단계에서는 제품 코드·보정 등록부를 변경하지 않았다. 같은 날 후속 구현에 문헌 비교 자료와 명령 공정 정보가 추가되었으며 채택·검증 범위는 [공정 취약부 검증 기록](process-aware-weakness-validation-20261003.md)을 참조한다. 아래 관측이나 비율은 문헌 조건의 비교이며 목표 부품의 보정계수·파단확률·예측 정확도가 아니다.

### 새로 확보한 공개 PA6-CF 시편 데이터

Nesheim 등, *Identifying thermal effects during 3D printing by comparing in-layer infrared pre- and postheating of carbon fiber reinforced polyamide 6*, [논문 DOI 10.1016/j.addma.2025.104705](https://doi.org/10.1016/j.addma.2025.104705), [Bristol 기관 초록](https://research-information.bris.ac.uk/en/publications/identifying-thermal-effects-during-3d-printing-by-comparing-in-la/), 대응 [Mendeley Data v1, 10.17632/pdfz6y8bmh.1](https://data.mendeley.com/datasets/pdfz6y8bmh/1). 논문과 데이터는 **하나의 실험 계보**다. 기관 초록과 공개 데이터는 확인했으나 논문 전문의 Methods를 확보하지 못했다.

약 40 W 할로겐 가열기의 없음/전가열/후가열, 3–50 mm/s, 단일벽 두께 0.8 mm·층높이 0.3 mm의 층간 인장 시편이다. 정확한 상품 grade, 건조·잔류수분, 베드·챔버, 시험 속도, 전체 시편 형상은 아직 미확인이다. 저자 `temp_plot.py`에는 노즐 300°C 상수가 있지만 이를 노즐 실측이나 논문 Methods 확인으로 승격하지 않는다.

공식 API의 루트와 CSV 폴더를 읽고 XLSX 1개·CSV 6개·저자 코드 1개의 바이트 SHA-256을 공식 값과 대조했다. 원파일은 저장소에 복제하지 않았다. 데이터는 **개별 최대하중·면적·UTS 및 온도 관측 표**이며 계측기의 전체 하중–변위곡선이나 영상 스트림은 아니다. numeric UTS가 있는 CSV 행은 전가열 45·후가열 39·무가열 24, 합계 108개다. 결측과 `TOO WEAK`는 0 MPa로 채우지 않았다.

다음은 CSV의 `Load / Area`로 재계산한 조건 평균 ± 표본 SD다. 분모는 파일에 보고된 시편 `Area`이며 **현미경 실제 용접 접촉면적임을 확인하지 못했다**. 각 열의 반복 관측을 독립 연구로 세지 않는다.

|속도 mm/s|무가열 MPa (n)|전가열 MPa (n)|후가열 MPa (n)|같은 속도의 전가열/무가열, 후가열/무가열 평균비|
|---:|---:|---:|---:|---:|
|20|8.061 ± 0.709 (6)|25.439 ± 1.232 (6)|14.920 ± 1.693 (6)|3.156, 1.851|
|30|8.976 ± 0.709 (6)|25.556 ± 0.989 (6)|18.928 ± 1.121 (6)|2.847, 2.109|
|40|11.672 ± 1.365 (6)|26.314 ± 2.462 (6)|21.425 ± 1.481 (5)|2.255, 1.836|
|50|7.166 ± 0.837 (6)|20.852 ± 1.792 (6)|16.991 ± 3.909 (5)|2.910, 2.371|

검증 제한을 구체적으로 보존한다. 3 mm/s 전가열 XLSX `Strength data!D11:D12`는 `D6:D10` 5개만 평균/SD로 쓰지만 CSV에는 8개가 들어 있다. `B30`의 `Broke in gripper`와 일부 서식이 제외 처리를 암시하지만 CSV에는 시편별 파단위치 플래그가 없다. 해당 조건은 보정 입력에서 제외해야 한다. 온도 XLSX의 우측 요약은 무가열 6 mm/s 일부 칸이 12 mm/s 칸을 참조하며, 30 mm/s 일부 평균도 원행 전체와 다르다. 따라서 요약 칸 전체를 자동 학습값으로 읽으면 안 된다. 기관 초록의 52.28/59.84 MPa는 최대 관측값이고 조건 평균과 다르다.

저속에서는 보조 가열기의 체류시간, 고속에서는 짧은 층시간에 따른 잔열 축적이 함께 작용한다. 이 자료로 일반 H2C 출력의 속도·챔버 보정이나 균열 열림 저항을 결정할 수 없다. 20–50 mm/s의 위 12조건은 추출·통계 검증용 공개 기준으로 유용하나, 상품·시험 조건이 완성되기 전에는 calibration 입력 자격이 없다. 소규모 파생 집계와 파일 계보는 [동반 JSON](process-thermal-evidence-20261003.json)에 기록했다.

### 완전한 factorial 연구가 보여 주는 공정 상호작용

Belei, Joeressen, Amancio-Filho (2022), [10.3390/polym14071292](https://doi.org/10.3390/polym14071292), [공개 전문](https://pmc.ncbi.nlm.nih.gov/articles/PMC9002508/), Methods §2.1–2.4, Tables 1–2, §3.1. BASF Ultrafuse **PAHT CF15**를 Ultimaker S5·0.6 mm 노즐로 출력했다. ISO 527 I-BA 형상, 0°/90° raster, 초기 시편 단면으로 응력 계산, 19°C·2 mm/min 인장, 조건당 초기 n=4. 필라멘트는 40°C 상자·실리카겔에 보관했으나 수분함량은 측정하지 않았다. PAHT를 PA6/PA12/PPA로 확정하지 않는다. Table 1의 bead width 0.4 mm·air gap 0.4 mm 표기는 원표의 정의대로 보존해야 한다.

|Table 2 통제 비교|나머지 고정조건|보고 평균 ± 값 MPa|평균 변화|
|---|---|---|---:|
|C1→C5: 노즐 240→280°C|v=30 mm/s, bed=100°C, h=0.4 mm|97.0 ± 5.4 → 89.2 ± 2.5|−8.04%|
|C3→C7: 노즐 240→280°C|v=80 mm/s, bed=100°C, h=0.4 mm|91.0 ± 3.5 → 100.2 ± 3.3|+10.11%|
|C9→C10: bed 100→120°C|v=30 mm/s, nozzle=240°C, h=0.2 mm|111.0 ± 4.6 → 115.0 ± 5.4|+3.60%|
|C11→C12: bed 100→120°C|v=80 mm/s, nozzle=240°C, h=0.2 mm|99.3 ± 0.5 → 110.0 ± 0.8|+10.78%|

온도의 효과 방향이 속도·층높이에 의존한다. 서로 다른 한 변수 표의 배율을 곱하거나 “노즐이 높으면 항상 강해짐”을 적용하면 이 통제쌍을 설명하지 못한다. 저자는 15개 추가 조건 각 n=4를 시험했고, factorial 모델이 낮은 강도 범위의 새 조건에서 잘 맞지 않았다고 보고했다. 최적조건 n=8의 117.1 ± 5.7 MPa 재시험은 최적조건 확인이며 독립 실험실/다른 부품 검증이 아니다. raw 데이터는 요청 방식이며 공개로 확보한 자료로 세지 않는다. ±의 통계 정의를 구조화 입력에서 SD로 단정하기 전 원문 확인을 더 해야 한다.

### 실제 층온도와 시편강도: 최근 PA6-CF 실험의 경계

Ørnes 등(2026), [10.1017/pds.2026.10563](https://doi.org/10.1017/pds.2026.10563), [출판사 전문](https://www.cambridge.org/core/journals/proceedings-of-the-design-society/article/characterising-thermal-effects-on-ultimate-tensile-strength-strain-and-tensile-modulus-by-material-extrusion-of-carbon-fibre-reinforced-polyamide-6/C921F564CEEC2122D079C0EF30F4B4B0), Methods §§2.2–2.5, Results §3.1, Discussion §4. Polymaker PA6-CF·Creality K2 Plus, standing Z, 수정 ISO 527-2 시편 길이 65 mm/gauge 17 mm/단면 50 mm², 노즐 280°C·베드 120°C·층 0.2 mm·최대 유량 설정 12 mm³/s. 80°C에서 최소 6 h 열처리 후 5 mm/min 시험이다. 각 조건 제작 n=5지만 69/119°C는 데이터 손상으로 분석 n=3이다.

측정 이전 층 표면온도 PDT 104°C의 UTS는 **14.26 ± 1.73 MPa**, 106°C는 **11.82 ± 0.79 MPa**다. 140/165°C는 **28.41 ± 1.36 / 36.04 ± 1.88 MPa**다(보고 SD). 104→106°C에서 오히려 17.1% 감소했다. 팬·속도·개방/폐쇄를 동시에 바꿔 온도범위를 만들었으므로 독립 온도 인과계수로 사용할 수 없다. 1 Hz의 외벽 한 점을 여러 층에 걸쳐 관찰하여 최소값을 PDT로 삼았으며 실제 접합면 온도장이 아니다. H2D 부품의 온도 관찰은 부품 파단하중 검증이 아니다. 저자들이 서로 다른 부품 온도 범위를 본문에 보고하므로 단일 정확 범위나 부품 강도 라벨로 전사하지 않았다. 상품 grade와 원시 결과 파일의 추가 확인도 필요하다.

### 기존 ABS 계보의 새 전문 확인: 파괴면적을 분리해야 한다

기존 Aliheidari 등(2018), [10.1016/j.matdes.2018.07.001](https://doi.org/10.1016/j.matdes.2018.07.001)의 단순 초록 참조를 보완하기 위해 Aliheidari의 [WSU 2017 학위논문](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Characterization-of-interlayer-adhesion-and-fracture/99900525131701842)을 읽었다. **같은 연구군/실험 계보의 보완이며 새로운 독립 연구로 세지 않는다.** 원문 PDF pp.16–20, 38–44(파일 pp.28–32, 50–56), Tables 1–3/Figs.13,15,17.

BuMat ABS, Felix pro I, 0.35 mm 노즐, 100% longitudinal linear·perimeter 없음. DCB 길이32.5/너비10/arm높이6/starter crack19.5 mm, n=5 순차출력, Mode I 0.01 mm/s, 광학 균열 성장 약150–200 µm를 initiation으로 정의했다. nozzle220/230/240°C·bed85/95/105°C·h0.1/0.2/0.3 mm·width0.25/0.35/0.45 mm를 각각 바꾸고 기준230/95/0.2/0.35를 고정했다.

노즐220→240°C의 apparent J는 **1981.45 ± 41.22 → 2731.87 ± 100.48 J/m²**, 실제 fracture-surface intact ratio를 반영한 interlayer J는 **3391.04 ± 69.83 → 3907.54 ± 143.13 J/m²**다(평균±SD). 같은 온도변화의 증가율도 각각 **37.9%/15.2%**로 다르다. bed85→105°C의 interlayer J는 **3527.91 ± 221.16 → 3798.54 ± 204.04 J/m²(+7.67%)**다. 이것은 DCB opening의 에너지 저항이며 tensile MPa나 임의 부품 파단하중 배율이 아니다. 인접경로 겹침만으로 실제 intact ratio와 용접 품질을 동시에 알 수 없음을 뒷받침한다. raw 계측파일은 확보하지 않았다.

### PLA에서 확인한 열 경로: 베드 효과의 공간 의존성

Liparoti 등(2021), [10.3390/polym13030399](https://doi.org/10.3390/polym13030399), [공개 전문](https://pmc.ncbi.nlm.nih.gov/articles/PMC7865617/), Methods §2, Table3/Fig.12. Robotics3D **PLA 02-B-0015**, Replicator2X, 노즐0.4 mm, 40 mm/s, infill99%, 인접층90° raster, ANSI/ASTM D638 TypeV, 최소5반복·0.16 mm/min. 응력 분모·± 통계 정의의 정밀 확인은 미완료다.

200°C 노즐에서 bed70/90/110°C의 UTS는 **76.5±0.7 / 74.6±0.7 / 73.6±0.7 MPa**(Table3 D/E/F)다. 열전대로 bed/layer4/layer7을 기록했고 같은 노즐에서 초기 접촉 냉각률은 **80/35/20°C/s**였다(Fig.12 본문). 베드가 높아져 냉각이 느려져도 이 coupon 전체 UTS는 단조 증가하지 않는다. 이 값은 Z 단일용접 강도나 fracture toughness가 아니다. 가까운 옆 경로 증착도 재가열을 만들므로 층 재방문만 기록하면 열 입력을 놓칠 수 있다. raw 온도·하중곡선은 확보하지 않았다.

### 제외하거나 후속 검토로 남긴 근거

[Nguyen 등 ABS 챔버 연구(2025)](https://www.sciepublish.com/article/pii/758)의 Table2는 chamber30/45/60°C, n=5, ABS30.75±0.82/30.53±0.35/30.45±0.85 MPa를 보고한다. nozzle240/bed110°C·40 mm/s·h0.25·100%·shell3이나 grade·raster·시험축·면적 기준이 미확인이다. 본문은 강도 감소 표와 “챔버가 높으면 인장성능 개선”이라는 설명이 충돌하고 TPU 45°C 요약도 표와 다르다. 따라서 생산 보정 근거에서 제외했다.

[Thumsorn 등 PLA chamber/fracture 연구](https://doi.org/10.3390/jmmp7010044)는 fan×chamber full-factorial supplementary matrix를 제공하는 유망 후보지만 이번에 전체표·geometry·반복·raw를 검증하지 못해 숫자를 전사하지 않았다. [PA12 MWD/DCB 연구(2026)](https://doi.org/10.1007/s40964-026-01594-y)는 grade별 유량·속도 변경과 Mode I을 보여 주는 후보로 남긴다. PA12를 PA6-CF 또는 PPA-CF의 계수로 전이하지 않는다.

### 엔진에 보존할 수 있는 입력과 승인 경계

아래는 연구를 근거로 한 **설계 제안**이다. 구현·검증 완료 기능 목록이 아니다. 후속 구현의 국부 명령 범위·길이 커버리지·역할별 체적은 별도 검증 기록에 있으며, 국소 재방문 시간·열전달량·실제 접합면 온도까지 구현했다는 뜻은 아니다.

|입력/관측|저장할 의미|그것만으로 결정하지 못하는 것|
|---|---|---|
|도구별 nozzle/bed/chamber 온도 이벤트|설정·대기 명령·실측을 분리하고 timestamp/레이어/도구·출처 보존|노즐 설정값→실제 melt/접합면온도 변환|
|국소 층 재방문|이전 모델경로 footprint와 다음층 교차 위치의 증착시간 간격; 경로별 시간구간·누락/시간범위|총시간÷층수 또는 minimum-layer-time→국소 열이력 대체|
|층 내 옆벽 재방문|같은 층 인접벽·연결부 주변의 후속 증착시간과 거리·도구 기록|근접 거리만으로 열전달량·결합강도 계산|
|실제 명령 경로와 wall index|내/외벽별 length, commanded ΔE·활성 M221, 선폭/층높이·flow, speed·override, tool/material|wall count × 보편 상수. ΔE는 모터명령이며 실제 유량실측이 아님|
|공정 시간 기준|G04, heating waits, toolchange, acceleration/firmware unknown을 표시; timing estimate와 sensor time 분리|F 명령속도를 실제 도착속도로 확정|
|별도 열 측정|위치별 PDT/peak/reheating cycles·sampling·emissivity·IR 또는 thermocouple 출처|한 점 IR 최소값→전체 벽/계면 온도장|
|소재/시험 식별|grade/batch, moisture/anneal, build/raster/load axis, area basis, tensile vs GI/J/K mode, n/SD|family 이름·CF 함유율만으로 property 호환|

부품 메커니즘에는 **기하상 경로 겹침**, **실제 bonded area**, **그 면적의 결합/파괴 저항**이 모두 필요하다. 현재 자료로 첫 항을 G-code에서 계측할 수 있어도 둘째·셋째를 임의 배율로 채우면 안 된다. 특정 조건의 coupon 비교는 지원할 수 있다. 범용 nozzle/bed/chamber/return-time/speed/wall별 factor는 승인하지 않는다. 별도 열 모델을 시도한다면 냉각·옆경로 재가열·베드와 Z거리·팬·수분·grade rheology를 포함하고, 먼저 온도 holdout, 다음 동일 shape/process의 기계시험 holdout을 통과해야 한다. 한 연구의 시편을 무작위 분할하여 독립 실험실 검증으로 제시하지 않는다. 균열 위치와 실제 force/restraint가 없는 사용자의 “손으로 쉽게 부러짐”은 정량 failure label로 쓰지 않는다.

## English

This targeted review adds previously uncompleted quantitative extraction and new public data. The research-document stage did not change product code or authorize runtime correction factors. Subsequent literature-comparison and commanded-process features are documented in the [process-aware validation record](process-aware-weakness-validation-20261003.md). The design proposals below do not establish implemented local revisit timing, heat transfer or measured interface temperature. Paper and dataset pairs, and related thesis/article experiments, retain one lineage.

The new [Nesheim PA6-CF dataset, Mendeley v1](https://data.mendeley.com/datasets/pdfz6y8bmh/1) accompanies [10.1016/j.addma.2025.104705](https://doi.org/10.1016/j.addma.2025.104705). Official SHA-256 checks passed for the workbook, six CSV files, and author code. It contains 108 numeric specimen records of peak load/area/UTS, plus thermal observations, rather than complete instrument curves. The 20–50 mm/s condition means and sample SDs above were recomputed from load/area. Exact grade, bed/chamber, mechanical test speed, conditioning, complete geometry, and the meaning of the reported area remain incomplete. The institutional abstract establishes a 0.8 mm single wall, 0.3 mm layer, approximately 40 W IR heater, and 3–50 mm/s domain. Full article Methods remain inaccessible in this review.

At 40 mm/s, no heating/preheating/postheating give 11.672±1.365 (n=6), 26.314±2.462 (n=6), and 21.425±1.481 MPa (n=5). These are within-study heating contrasts. The 3 mm/s preheat workbook excludes three numeric records in its aggregate while the CSV includes eight. Thermal workbook summaries also contain formula/range discrepancies. Missing `TOO WEAK` conditions are not zero-filled; maxima in the abstract are not condition means. The accompanying JSON preserves selected aggregates, file provenance, unknowns, and extraction limits. It contains no approved model.

[Belei et al., 2022](https://doi.org/10.3390/polym14071292), Methods §2/Tables1–2, provides a four-factor experiment for BASF Ultrafuse PAHT CF15, Ultimaker S5, ISO527 I-BA, 0/90° raster, initial specimen area, n=4 per initial condition, 19°C and 2 mm/min. Raising nozzle240→280°C decreases mean UTS97.0→89.2 MPa at v30/bed100/h0.4, but increases91.0→100.2 at v80 with the same bed/layer. Speed and temperature effects interact. The paper reports poor lower-range predictions for new within-study conditions; optimized n=8 verification is not external validation. Raw data are request-only. PAHT matrix identity must not be relabelled PA6/PA12/PPA.

[Ørnes et al., 2026](https://doi.org/10.1017/pds.2026.10563), Methods §§2.2–2.5 and Results §3.1, uses Polymaker PA6-CF, K2 Plus, standing-Z modified ISO527-2 specimens, 50 mm² cross-section, nozzle280/bed120°C, h0.2, max-flow setting12 mm³/s and 80°C/minimum6 h heat treatment. UTS at measured PDT104/106°C is14.26±1.73/11.82±0.79 MPa;140/165°C gives28.41±1.36/36.04±1.88. Speed, fan and enclosure were changed together. Outer-wall1 Hz temperature minima approximate PDT; they are not interface temperature fields. Data corruption reduces n to3 at69/119°C; other conditions use n=5. Thermal monitoring of an H2D component is not component failure validation.

The [Aliheidari WSU thesis](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Characterization-of-interlayer-adhesion-and-fracture/99900525131701842) completes metadata for an existing ABS lineage. BuMat ABS/Felix pro I DCBs use longitudinal100% infill/no perimeter, L32.5/W10/arm6/precrack19.5 mm, n=5, opening0.01 mm/s. Nozzle220→240°C raises apparent J1981.45±41.22→2731.87±100.48 J/m², but area-corrected interlayer J3391.04±69.83→3907.54±143.13:37.9% versus15.2%. Actual fractured area and bond quality are distinct. These opening energies cannot replace tensile MPa or arbitrary-part force.

[Liparoti et al., 2021](https://doi.org/10.3390/polym13030399), Methods/Table3/Fig.12, studies Robotics3D PLA02-B-0015, Replicator2X,40 mm/s,99% infill,90° adjacent rasters, TypeV tensile specimens, at least five repeats. With nozzle200°C, bed70/90/110°C gives76.5±0.7/74.6±0.7/73.6±0.7 MPa, while measured initial cooling rates decrease80/35/20°C/s. Slower cooling does not guarantee monotonic whole-coupon UTS. Neighboring roads also reheat a layer. The stress denominator and statistical meaning of ± remain incompletely structured.

The [2025 ABS chamber paper](https://www.sciepublish.com/article/pii/758) is excluded from calibration because grade/orientation/area metadata are incomplete and its narrative conflicts with its table. [PLA chamber/fracture](https://doi.org/10.3390/jmmp7010044) and [PA12 molecular-weight/DCB](https://doi.org/10.1007/s40964-026-01594-y) remain follow-up candidates without completed numeric extraction here.

Runtime design should preserve timestamped per-tool thermal commands separately from measurements; local interlayer and neighboring-wall return times with timing uncertainty; per-wall length, commanded extrusion/flow/speed overrides and geometry; sampling/emissivity/source for thermal observations; and grade/batch/moisture/annealing, loading axes, property/mode, area basis and scatter. G-code overlap can describe declared geometry, while measured bonded area and its fracture resistance remain separate unknowns. No universal temperature, speed, return-time or wall-count factors are approved. Thermal holdouts and matched-shape mechanical holdouts are required before transfer, and qualitative hand-break observations are not numeric labels.
