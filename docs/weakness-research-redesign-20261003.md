# 취약 위치·강도 통합 재설계 근거 / Evidence for integrated weakness and strength analysis

[한국어](#한국어) · [English](#english)

## 한국어

검토일: 2026-10-03. 이 문서는 v0.16.0 후보 검출의 한계와 후속 재설계의 근거를 기록한다. **설계 권고와 배포된 기능을 구분한다.** 실제 구현·검증·배포 버전은 릴리스 기록에서 확인한다. 원문이나 원시 시험파일을 복제하지 않으며, 기존 [연구 근거](research-evidence.md)의 출처 계보를 재사용한다. 접근 가능한 주요 1차 자료를 표적 검토했으며 모든 관련 논문을 전수 확인했다는 뜻은 아니다.

### 기존 1~6번의 의미와 누락 원인

v0.16.0의 `local_thickness.py`는 외곽 경로를 채운 복셀 형상에서 3×3×3 국소 최대 거리점의 두께가 2.4 mm 이하인 곳을 찾는다. 길이가 긴 축의 구간으로 나누고 최소 점 수·길이·세장비 조건을 적용한다. 두께 25백분위가 작은 구간, 세장비가 큰 구간, 검출점 수가 많은 구간 순으로 정렬한 뒤 거리 중복을 억제하여 최대 6개를 남긴다. 2.4 mm와 구간·점 수 기준은 **소프트웨어 선별 기준**이며 논문에서 검증된 파단 임계값이 아니다.

그 결과 같은 두께의 길고 얇은 중간 영역이 여러 후보를 차지할 수 있다. 얇은 끝이 짧거나 점 수가 적으면 탈락하고, 얇은 영역의 최장축에 수직인 단면은 실제 Z 층계면과 다를 수 있다. 실제 증착 단면을 이용한 자동 굽힘 참고하중도 이미 선택된 후보의 계산을 보완할 뿐, 최초 후보 선택을 다시 하지 않는다. **이 번호는 파손 순위가 아니며, 가장 먼저 부러질 위치를 검증한 결과도 아니다.**

사용자의 “끝에서 층이 갈라지며 쉽게 파손됐다”는 관찰은 끝부분 검출의 누락을 점검할 위치 근거다. 정확한 파단하중, 고정 위치, 힘의 방향 또는 파괴 모드 시험값이 없는 상태에서 그 관찰을 수치 학습 라벨로 바꾸지 않는다.

### 선별과 파괴 계산을 같은 입력으로 연결하는 설계

공통 입력은 원 G-code의 파일 해시와 선택 plate, 실제 레이어 Z·높이, 모델·서포트 구분, 도구·실제 사용 소재 선택, 선폭·압출 경로, 벽·인필·raster 방향, 명령 속도, 온도·팬·대기 명령이다. 설정값과 측정값을 구분하고 누락값을 기본값이나 0으로 메우지 않는다. 전체 모델 경로·인접 층을 다 읽었는지도 결과에 기록한다.

|검사할 메커니즘|G-code에서 가능한 선별·계산|별도 실증이 필요한 값|
|---|---|---|
|얇은 단면·굽힘|연결 부품별 실제 증착 단면의 면적·방향별 단면계수, 끝·뿌리·두께 변화 위치. 명시한 지렛대·방향의 정상응력 참고 시나리오.|실제 재료 응력 기준, 고정·힘 위치, 실제 공극·접합, 균열·소성. 끝을 누르면 최대 굽힘모멘트는 뿌리에 생길 수도 있다.|
|층계면 접촉 부족|실제 Z 경계에서 이전·다음 층의 선언된 모델 경로 footprint를 교차한다. 영역별 겹침 면적, 단절, 방향·도구별 경로 교차를 보존한다.|경로 겹침은 실제 용접 면적·분자 결합을 측정하지 않는다. 충분히 겹쳐도 접합이 불량할 수 있다.|
|끝·자유 모서리의 층분리 노출|끝 주변의 적층 수·두께, 자유 모서리, 인접 층 연결과 접근 가능한 균열 경로를 따로 표시한다. 얇은 끝은 중간 구간의 점 수 필터에만 의존하지 않는다.|Mode I 열림, II 미끄럼, III 찢김의 저항과 실제 하중 경로. 작은 끝 면적 자체가 파단 위치라는 증거는 아니다.|
|노치·뿌리·급격한 변화|연결부, 재진입 모서리, 단면 변화·경로 단절을 선별하여 기존 얇은 구간과 함께 보여준다.|실제 노치 반경·균열 길이와 응력집중/파괴인성. 해상도보다 작은 균열은 G-code에서 식별할 수 없다.|
|공정·층결합 조건|국소 명령 속도·raster, 대기·재방문 시간의 계산 가능한 범위, 온도·팬·공식 권장범위의 불일치를 기록한다.|접합면 온도·유량·공극 실측, 제품·배치별 결합 물성. 노즐 설정온도나 총시간÷층 수로 용접 품질을 계산하지 않는다.|

인필·패턴·벽 수를 임의 상수로 곱하는 대신 읽힌 실제 경로를 사용한다. 소재 참조응력은 면적 정의와 시험 조건을 함께 유지한다. 인필 상대비를 실제 재료 단면에 다시 곱해 이중 감쇠하지 않는다. 접촉 면적비에도 임의의 접합 감쇠계수를 붙이지 않는다.

이번 문헌 검토는 [`calibration.py`](../print_strength_engine/calibration.py)의 검증된 모델 등록부를 자동으로 채우지 않는다. 내부 0.85 계수는 실증 하한이나 검증된 안전율이 아니며, 참조값에 적용한 경우에도 예측 정확도가 확보되는 것은 아니다. 파괴에너지 J/m²·N/mm, 파괴인성 MPa√m, 인장·전단 응력 MPa는 단위·mode·면적 basis를 함께 검증한다.

후보는 메커니즘별 국소 이상을 모은 뒤 동일 위치를 병합한다. 중간의 동일 두께 구간이 모두 6칸을 차지하거나, 멀리 떨어진 다른 부품이 중복 억제로 제거되지 않도록 부품·메커니즘별 공간 범위를 보존한다. 일반 끝단 축소와 실제 좁은 연결부를 구분하는 음성 대조를 둔다. 모든 후보에 검출 이유, 위치·레이어, 수치와 그 분모, 해상도·입력 누락, 적용한 하중 가정을 제공한다.

**임의 가중합을 “파손 확률”로 표시하지 않는다.** 기하·층계면·공정 위험의 검토 우선순위와, 특정 하중 가정에서의 취약 순서는 구분한다. 층계면 열림을 직접 계산할 물성이 없으면 그 메커니즘의 하중은 미산출로 남기되 후보 위치는 숨기지 않는다. 자동 참고하중은 현재 지원하는 굽힘·인장 가정을 명시하고, 미계산 파괴 모드가 지배할 가능성을 함께 보여준다. 여러 조건에서 순서가 달라지면 단일 확정 “최약점” 대신 조건별 최약 후보와 순서의 불확실성을 제시한다.

### 1차 근거 행렬

확인 수준: **재사용**은 기존 근거 문서의 검토 기록, **전문**은 이번 접근 가능한 원문, **초록/메타**는 원문 전체가 아닌 출판사·연구기관 기록이다. 표의 `미확인`을 n=0 또는 분산=0으로 해석하지 않는다. 논문과 대응 데이터는 하나의 실험 계보로 묶는다.

|출처·확인 수준|시험 조건·면적·표본|재설계에 사용 / 전이하지 않을 것|
|---|---|---|
|S026, Seppala 등(2017), [10.1039/C7SM00950J](https://doi.org/10.1039/C7SM00950J), [NIST 원문](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=923318). 재사용.|열이력과 용접 형성, Mode III 파괴에너지. 세부 조건은 기존 기록 참조.|열이력 보존의 근거. 파괴에너지를 인장 MPa나 범용 속도 계수로 바꾸지 않는다.|
|Davis 등(2017), [10.1016/j.addma.2017.06.006](https://doi.org/10.1016/j.addma.2017.06.006), [NIST/PMC 원문](https://pmc.ncbi.nlm.nih.gov/articles/PMC5726274/). 전문 §2–3.|MakerBot ABS, Replicator 2x, 노즐 0.4/층 0.3 mm, 베드 110°C, 노즐 210–250°C·1–100 mm/s. 단일 weld Mode III, 1 mm/s, 조건별 n=5–10, 실제 용접 폭 현미경 측정. 벌크 n=5: 35.9±2.1 **N/mm**.|용접 형상·찢김과 인장 단면을 분리한다. 동일 NIST 연구군의 S026과 독립 실험실 근거로 합산하지 않는다. 수치나 벌크 대비 비율을 FusRock ABS의 MPa 감쇠에 넣지 않는다.|
|W013, Allum 등(2020), [10.1016/j.addma.2020.101297](https://doi.org/10.1016/j.addma.2020.101297), [기관 원고](https://repository.lboro.ac.uk/articles/journal_contribution/Interlayer_bonding_has_bulk-material_strength_in_extrusion_additive_manufacturing_New_understanding_of_anisotropy/12443528). 재사용.|PLA, 0.4 mm 노즐/210°C, 1000 mm/min, 베드 60°C; 층·선폭 변형, F/Z 인장. 실제 하중지지 면적과 국소 응력 구분. 전체 그룹 n·분산 전사 미완료.|작은 접촉면적·국소 집중과 재료 자체 결합강도를 구분한다. 논문 특정 면적비를 모든 100% 인필 출력에 적용하지 않는다.|
|W012, Moetazedian 등(2023), [10.1089/3dp.2021.0112](https://doi.org/10.1089/3dp.2021.0112), [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10280202/). 재사용, 이번 접근 제한.|3DXTECH/NatureWorks 4043D PLA, RepRap X400, 0.4/0.5/0.2 mm 노즐/선폭/층. 기준 210°C/1000 mm/min/10 s. n=5·0.5 mm/min. 실제 Z 파단 접촉면적으로 응력 계산.|일부 벌크 비교가 W013과 계보 중복. 양호한 조건의 결합이 벌크 수준일 수 있으므로 “Z는 항상 일정 비율로 약함”을 넣지 않는다.|
|W011, Lambiase 등(2024), [10.1007/s00170-024-14111-8](https://link.springer.com/article/10.1007/s00170-024-14111-8). 전문 §2–3 및 기존 Tables 1–2.|RS PRO PLA·Ender 6·210/60°C, 0.4/0.5/0.2 mm, 100% rectilinear. 2000/3000/4000 **mm/min** × 21/63/105 s, n=6/조건. 판에서 waterjet 가공한 ASTM D638 Type 2 upright, 2 mm/min. 층 표면 IR 측정; Fig.10 평균·SD, 수치 SD 전사 미완료.|명령 속도와 국소 재방문·기판온도 구분. 해당 조건의 시간 효과를 ABS·H2C·다른 크기 부품에 범용 보정하지 않는다.|
|Lambiase 등(2023), [10.1007/s00170-023-12223-1](https://link.springer.com/article/10.1007/s00170-023-12223-1). 전문 §2–3.|PLA DCB·ASTM D5528 기반, 0.4 mm 노즐/0.2 mm 층, 외곽 shell 없이 전략별 n=5, 1 mm/min. 단방향 0/45/90°, 교차 0/90°·±45°. 실제 접촉비 교차 43±2%, 단방향 70±1.5%; 평균 GIc는 각각 약3/1.3 kJ/m². 제품 grade·온도와 모든 수치 분산은 이번 전사 미확인.|**접촉비가 작아도 파괴에너지가 더 높을 수 있다.** 접촉비만으로 파단 순서를 단조 정렬하지 않는다. 접촉해도 불량 접합인 kissing bond 관측. 원자료는 저자 요청 방식이며 공개 검증파일을 확보했다고 주장하지 않는다.|
|Lingua 등(2022), [10.1016/j.engfracmech.2022.108483](https://doi.org/10.1016/j.engfracmech.2022.108483), [기관 기록](https://publications.polymtl.ca/51488/), [공식 데이터 기록](https://publications.polymtl.ca/58993/), [Zenodo 6382502](https://zenodo.org/records/6382502). 초록/메타.|PLA miniature CT, Mode I 층간·동일 층 filament 분리, 0–0/0–90° 비교, 약4×3 mm² DIC. 공개 raw TIFF/상관 CSV는 0–0 층간 파손 **대표 시편 1개**. grade·n·공정의 전체 전사 미완료.|계면 방향과 crack path를 별도 보존한다. 대표 영상 데이터는 독립 시편 집단이나 정량 파단하중 holdout이 아니다. 이번에 raw 파일 무결성·재계산 완료를 주장하지 않는다.|
|Young 등(2018), [10.1016/j.addma.2018.02.010](https://doi.org/10.1016/j.addma.2018.02.010). 출판사 초록.|ABS/short-CF ABS, modified Mode I DCB, midplane 8 µm Kapton starter crack, glass/epoxy 보강 arm; hot-pressed SENB 비교. grade·n·전체 조건 미확인.|층계면 열림 전용 시험과 starter crack·fixture 필요성. Mode III나 tensile 데이터로 대체하지 않는다. CF 함유를 무조건 결합강도 증가로 해석하지 않는다.|
|Aliheidari 등(2018), [10.1016/j.matdes.2018.07.001](https://doi.org/10.1016/j.matdes.2018.07.001), [연구기관 기록](https://researchwith.njit.edu/en/publications/interlayer-adhesion-and-fracture-resistance-of-polymers-printed-t/). 초록/메타.|ABS DCB Mode I, J-integral·SEM/광학, nozzle/bed/층높이/선폭을 조사. apparent fracture와 실제 interlayer 저항 분리. grade·n·SD 전체 전사 미완료.|공극·neck 형상과 접합 품질을 다른 변수로 취급한다. apparent toughness에서 접합 MPa를 임의 역산하지 않는다.|
|Fonseca 등(2019), [10.1016/j.compstruct.2019.02.005](https://doi.org/10.1016/j.compstruct.2019.02.005). 출판사 초록.|PA12 및 short-fibre PA12, Mode I DCB·수치해석·파면 현미경. 일관된 toughness는 unreinforced 조건에서만 보고. grade·n·전체 공정 미확인.|PA12·PA6·PPA 및 short/continuous fibre를 구분한다. 한 소재의 peel 계수를 다른 나일론에 매핑하지 않는다.|
|W027/W028, Cicero 등(2024), [10.3390/ma17215207](https://doi.org/10.3390/ma17215207), [Zenodo 14065523](https://zenodo.org/records/14065523); W029/W030, Cicero 등(2025), [10.3390/jcs9040185](https://doi.org/10.3390/jcs9040185), [Zenodo 14882928](https://zenodo.org/records/14882928). 기존 raw 감사 재사용.|3DJake ASA/ASA-CF10·flat·0.2/0.42 mm·100%·250/90°C·40 mm/s. ASTM D638/SENB D6068·1 mm/min, 가공 노치·razor crack. 기존 161개 유효 시편 시트(인장18/SENB143), 무데이터1 제외.|두 논문–데이터는 2계보. 굽힘 단면×UTS가 노치 파괴를 그대로 맞힌다는 가정을 반박하는 진단 자료. fitted TCD·동일 자료 replay는 독립 검증이 아니다.|
|Cole 등(2020), [10.1007/s40192-020-00188-y](https://doi.org/10.1007/s40192-020-00188-y), [NIST 연구](https://www.nist.gov/publications/amb2018-03-benchmark-physical-property-measurements-material-extrusion-additive), [benchmark 설명](https://www.nist.gov/ambench/amb2018-03-description). 기관 Methods/메타.|Stratasys PC·Fortus 400mc, 약365°C/환경·베드145°C, 15층·0.13 mm 층/0.20 mm raster, 0/45/90° 인장·CT voids·failure mode/위치. 전체 n·분산 전사 미완료.|실제 공극/계면/재료·형상을 함께 검증하는 기준. 공식 설명 일부 inch–mm 표기는 불일치하므로 표·실제 치수 대조 없이 전사하지 않는다. 다른 PC·ABS의 계수 아님.|
|Elverum 등(2026), [10.1017/pds.2026.10548](https://doi.org/10.1017/pds.2026.10548), [공개 PDF](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/9CAC2CB69BC9B57A7D5D0C0080534AAD/S2732527X26105483a.pdf/achievable-mechanical-performance-of-generatively-designed-pa6-cf-and-pla-components-fabricated-by-desktop-material-extrusion.pdf). 전문 Methods/Table1/Results.|실부품 각 n=3. PolyMide PA6-CF·H2D·275/100/60°C·0.4 nozzle; Polyterra PLA·X1C·220/45°C·0.6 nozzle. 공통0.2 mm/2walls/100%rectilinear, 0.1 mm/s fixture. PA6-CF 건조85°C24h. 얇은strut 결함·층분리, 여러 위치 및 clamp 파손 관측. CI 도표 제공, 숫자 SD 미전사.|소재 TDS만으로 부품 파단 위치·성능을 확정할 수 없다. printer·노즐·결함도 다르므로 동일조건 소재단독 비교가 아니다. n=3이며 Bambu PA6-CF/FusRock ABS로 수치 전이하지 않는다.|

이 행렬은 PLA·ABS·ASA/ASA-CF·PC·PA12·PA6-CF의 서로 다른 실험을 포함하며 동일 grade·mode의 통합 데이터셋이 아니다. PETG, TPU/TPE, ABS-GF, Bambu PA6-CF 및 다른 등록 제품의 계면 파괴 물성을 확보한 것으로 취급하지 않는다. 해당 제품의 숫자를 채우기 전에 기존 [소재별 연구 범위](research-update-20261001.md)와 grade·시험조건·원자료를 대조해야 한다.

### 검증 계약과 남은 실측

소프트웨어 회귀검증과 실증 검증을 따로 보고한다. 회귀검증에는 균일한 두꺼운 바의 끝을 무조건 최약점으로 고르지 않는 대조, 얇은 자유 끝·좁은 뿌리·계면 단절·교차 raster·두 부품·서포트 제외·가변 층 높이·빈 경로/잘린 데이터가 포함되어야 한다. 접촉이 충분한 조건에서도 실제 접합 강도가 높다고 단정하지 않는 테스트를 둔다. 단위·좌표·누적 면적 중복·개별 tool 연결·부품별 중복 억제·재분석 cache 버전을 확인한다.

실증 자료의 필수 키는 제품·배치·건조/조습·후처리, 시험표준·실제치수·면적 기준, 원경로·방향, fixture·하중위치/방향, 하중–변위 원곡선, **최초 균열/최대하중/최종파단의 구분**, 파손 좌표·mode, 반복 n·SD/CI다. 캘리브레이션과 평가를 실험 계보·제품·형상·fixture 단위로 미리 분리한다. 같은 시편의 여러 영상이나 같은 연구의 표·논문·Zenodo 파일을 별도 표본으로 세지 않는다.

위치 성능은 top-k 후보의 관측 최초파손 영역 포함 여부와 거리 오차를 함께 기록한다. 후보 수·공간 허용오차를 사전에 고정하고, 무조건 넓은 박스를 많이 내서 recall만 높이는 설계를 금지한다. 수치 성능은 동일 mode·면적·fixture·환경에서 MAE와 편향·오차분포를 계산한다. 이번 사용자 관찰은 끝부분의 누락 회귀 테스트에 쓸 수 있으나, 뉴턴 또는 kgf 정확도를 검증하는 표본으로 쓰지 않는다.

### 구현 우선순위와 계산 성능

첫 단계는 기존 후보만 개선하는 것이 아니라 **실제 레이어 계면과 끝·뿌리 검사를 별도 입력 채널로 추가**하는 것이다. 다음은 모든 후보에 공통 실제 증착 단면·공정정보·면적 basis·근거 연결을 적용하는 단계다. 마지막 파괴 하중·최초 파손 위치 예측에는 grade와 mode가 맞는 실측·독립 평가를 통과한 모델이 필요하다. 아직 없는 Mode I/II/III 물성을 서로 대체하여 칸을 채우지 않는다.

성능상 원파일을 검사별로 반복 스캔하지 않는다. 전체 source를 한 번 streaming하고 레이어·부품·도구별 footprint/공정 통계를 재사용한다. 넓은 영역은 공간 인덱스로 후보를 찾고 접촉·단면을 후보 창에서 정밀 계산한다. 표시용 경로 간소화를 분석 데이터에 적용하지 않는다. 원source hash·plate·분석버전·경로 치수·coverage·threshold·후보선택 fingerprint가 달라지면 관련 cache를 무효화한다. 속도 향상폭은 같은 파일·실행조건에서 차가운/따뜻한 cache와 계산/전송/렌더링을 나눠 측정한다.

## English

Review date: 2026-10-03. This document records the limitations of v0.16.0 and recommendations for a unified weakness/strength redesign. Implementation and deployment are tracked separately. The linked matrix is a targeted review of primary literature and existing audit records, not an exhaustive review of every available paper. Papers and associated datasets are grouped by experimental lineage.

### What the existing numbers mean

The v0.16.0 candidates come from local distance ridges in a voxelized outer envelope, with a 2.4 mm screening threshold. Long-axis buckets are filtered by ridge count, span and slenderness; thickness percentile, slenderness and point count determine ordering before spatial suppression and a six-candidate limit. These are software screening rules. Short thin tips can be lost while equivalent middle buckets fill the list. Subsequent declared-road bending calculations do not repeat the original candidate search. The numbers are not a validated fracture ranking.

The user's observed easy separation at an end is a location observation. Without measured force, restraints, load direction and failure mode, it is not a breaking-load training label.

### Integrated design

Use one provenance-checked G-code input for connected-part geometry, actual layer boundaries, model/support classification, tool/material selection, deposited road dimensions, raster, walls/infill and process context. Keep declared geometry, commanded settings and measured properties distinct.

Analyze thin sections and bending, adjacent-layer overlap and disconnection, free-edge delamination exposure, roots/notches and abrupt section changes, and process mismatches as distinct mechanisms. Use actual layer interfaces instead of the longest thin-region axis alone. Combine duplicate locations while preserving separate objects and mechanism coverage. Show the detection reason, layer/position, measured quantity and denominator, uncertainty and applicable load assumptions for every candidate.

A declared footprint intersection is geometric overlap, not measured weld area or adhesion. Thin ends need explicit coverage, but an ordinary terminal cap is not automatically the first failure location. A force applied at an end may produce its largest bending moment at the root. Infill ratios must not be applied again to already reconstructed material sections. Missing interface fracture data must not be synthesized from tensile MPa, a generic pattern factor or nozzle setpoints.

This review does not approve a transferable calibration model. The internal 0.85 margin remains unvalidated. Stress, fracture toughness and energy per area must retain their units, mode and area definitions; the matrix does not establish matched interface properties for every registered material/product.

Screening priority and conditional load-case rankings remain distinct. If rankings differ by load case, report the condition-specific candidates and ambiguity. An uncomputed interface mode remains visible rather than disappearing because a numerical load is unavailable.

### Evidence decisions

The Korean matrix supplies links, extraction status and test conditions. Its main design consequences are:

- NIST's single-weld ABS tear tests measure Mode III energy using actual weld width; those results are not tensile-stress correction factors. S026 and the related Davis work do not provide independent-laboratory replication.
- W012/W013 distinguish bond/contact area and local stress from whole-envelope strength. They reject a universal assumption that every Z bond is a fixed fraction of bulk strength.
- Lambiase's PLA DCB experiments include lower measured contact fractions but higher fracture energies for alternating rasters. Contact fraction alone cannot establish a monotonic fracture ranking; contact without adequate adhesion was also observed. Full raw data are available by author request, not an acquired public holdout.
- W011 distinguishes local return time and measured substrate temperature from commanded speed. Its tested PLA conditions cannot be transferred as a universal ABS or H2C coefficient.
- Lingua's official Mode I DIC dataset contains one representative specimen. It supports mechanism inspection, not independent population validation. Young's ABS/CF-ABS DCB and Aliheidari's process–mesostructure work support separating interface opening, geometry and bond quality; complete grade/n/dispersion extraction remains unfinished.
- The existing ASA/ASA-CF raw-curve audit supports notch-bending diagnostics under its actual fixtures. It does not validate arbitrary-part candidate locations or turn fitted replay into holdout validation.
- NIST's PC benchmark links process, voids, interface behavior and tensile failure observations. Inconsistent inch/mm text needs dimensional verification before ingestion.
- Elverum's six real components show different fracture locations and interface/clamp failures. Different printers/nozzles and visible defects preclude a material-only transfer; the small study is not calibration for FusRock ABS or Bambu PA6-CF.

### Verification and remaining measurements

Regression fixtures must include thick bars with ordinary ends, thin free ends, narrow roots, interface gaps, alternating rasters, separate objects, support exclusion, adaptive layers and truncated/missing data. Verify units, coordinate mapping, union rather than duplicate-area summation, tool/part separation and cache invalidation. Synthetic geometry tests establish software behavior, not fracture accuracy.

Physical validation requires matched grade/batch/conditioning, test standard and actual dimensions/area basis, original paths/orientation, fixtures and force locations/directions, raw curves, initiation/peak/final-fracture distinctions, observed coordinates/modes and replication/dispersion. Split experiments by lineage, product, shape and fixture in advance. Report spatial hit rates and distance error with fixed candidate counts/tolerances, and load errors only within matched modes and conditions. A qualitative tip observation cannot establish N or kgf accuracy.

Stream the original file once, reuse layer/tool/part footprints and process summaries, spatially index the search, then refine local windows. Rendering simplification must not affect analysis. Invalidate caches on source/member, dimensions, coverage, analysis policy or selection fingerprints. Benchmark cold/warm paths and compute, transfer and rendering separately. Full fracture prediction needs additional validated mode- and grade-specific measurements; this design does not claim those measurements already exist.
