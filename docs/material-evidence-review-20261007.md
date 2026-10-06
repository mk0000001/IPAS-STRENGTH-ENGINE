# 재료 실험 근거 검토 — 2026-10-07

18개 등록 소재군과 추가 요청 범위인 PPS-GF를 검토했다. **12개 1차 논문을 새로 확인하거나 기존 후보의 조건을 보완했지만, 이를 12개의 독립 실험으로 세지 않는다.** 새 자료는 비교 근거를 넓히며, 현재 엔진의 임의 부품 파단 예측 정확도를 입증하지 않는다. 승인된 런타임 모델과 독립 외부 검증 시편은 여전히 0이다.

원 연구 담당은 보고서와 구조화된 근거표를 작성했고, 이 문서는 통합 릴리스용으로 정리했다. 코드·카탈로그·배포를 변경하지 않았고, 물리 시험이나 원저자 연락도 수행하지 않았다. 기존 private corpus의 전체 검색·파일 목록 검사·원자료 추출을 반복하지 않았다. 새 PDF/XML은 메모리에서 확인했으며 원문·곡선·이미지·G-code를 공개 저장소에 복사하지 않았다.

## 확인된 데이터 상태와 오류

공개 ASA/ASA-CF 카탈로그 18행의 저장된 하중·실측 폭×두께·그룹 통계 산술은 통과했다. 이번 실행에서 확인한 카탈로그 SHA-256은 `081f38bed7c9eb23b069530a0954a53348041c3b85803dcbd7bff6b5c6bf588f`이다. grade별 9행은 필요한 batch와 시험·공정 조건이 누락돼 calibration 입력에서 거절됐으며, 산술 통과를 독립 정확도로 해석하지 않는다. ASA-CF는 등록 소재 18개 밖의 별도 grade다.

- **문서의 PA6-GF 분류 오류:** [Tanabi 원문](https://dergipark.org.tr/en/pub/iarej/article/862304)은 XSTRAND GF30-PA6 **단섬유** 실험이다. `research-update-20261001.md`의 “연속 GF” 암시를 이번 개정에서 수정했다. 런타임 coverage 사유는 이미 short-GF로 정확하며 수치 버그로 보고하지 않는다.
- **반복 수치와 계보 누수:** [2023 ABS/ABS-CF](https://doi.org/10.3390/polym15092011), [2024 ABS 섬유 비교](https://doi.org/10.3390/polym16081106), [2024 복합소재 비교](https://doi.org/10.1016/j.prostr.2024.06.029)가 ABS·ABS-CF 평균/±값을 정확히 반복하고 마지막 논문은 ABS-GF도 반복한다. 속도는 30 대 50 mm/s, ABS-CF bed는 110 대 100°C, 층 높이도 서로 다르게 기술한다. 반복된 집계는 확인됐지만 물리 시편의 동일성은 원자료 없이 확정할 수 없다. 같은 셀을 새 DOI라는 이유로 training/test에 나누면 안 된다.
- **PPS 원문의 수치 충돌:** [PPS/rCF 논문](https://4spepublications.onlinelibrary.wiley.com/doi/10.1002/pc.71040) abstract의 86 MPa와 Table 5의 미열처리 68.5 / 열처리 81 MPa가 맞지 않는다. 다른 배합도 본문과 표가 다르다. ±는 **95% CI**이며 SD로 저장하면 안 된다. 후보 자료를 격리하고 원저자 정정·원자료가 확인될 때까지 예측 target에 넣지 않는다.
- **PPA TDS 표준 오류:** [PPA-CF 원문](https://doi.org/10.3390/polym18121422)은 제조사 인장강도에 ASTM D792를 붙인다. [공식 D792](https://store.astm.org/d0792-20.html)는 밀도·비중 표준이다. 이 TDS 속성을 격리하되 별도의 ISO 527 Table 2 실험값까지 오류로 처리하거나 임의로 D638로 고치지 않는다.
- **물성·표본 수 경계:** [PPS-CF Lyu 연구](https://doi.org/10.1177/00219983231194391)의 164.65 MPa는 굽힘강도다. [PA6/GF hybrid](https://doi.org/10.3390/polym17121590)의 조건당 6개 시험은 인장 3 + 충격 3이며, 인장 n=6이 아니다. hybrid와 연속 GF를 균질한 단섬유 PA6-GF에 전이하지 않는다.

## 새로 확인하거나 보완한 1차 자료

아래 수치는 대표 조건만 기록했다. 확인한 공정·시험 조건·접근 상태·n·미확인값·원문 locator·격리 사유는 JSON의 M01–M12에 있다. JSON의 수치도 대표 집계이며 논문 전체 표나 개별 원자료가 아니다. **± 정의를 확인하지 못한 값은 SD로 부르지 않는다.** 원자료를 받았다고 주장하지 않으며 집계 n만으로 개별 시편행을 만들지 않는다.

|ID / DOI|원문 접근과 재료·시험|확인된 대표 수치와 조건|사용 범위 / 미확인 사항|
|---|---|---|---|
|M01 [10.3390/polym18050563](https://www.mdpi.com/2073-4360/18/5/563)|[공식 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12986956/fullTextXML), Fiberlogy PA12 CF15, ISO 527; n=3×시험온도 6개|23°C UTS 49.07±0.88, 120°C 18.68±0.91 MPa; Table 3의 ±는 SD. K1 MAX, flat ±45°, 100%, 벽 5, 265/100°C, 0.6 mm nozzle, 0.2 mm layer, 60 mm/s. 80°C 12 h 건조.|해당 grade의 시험온도 비교. 잔류수분·batch·실측 응력 분모 미확인. M09와 같은 연구진 계열이며 다른 lab 검증으로 세지 않는다.|
|M02 [10.1002/pc.71040](https://4spepublications.onlinelibrary.wiley.com/doi/10.1002/pc.71040)|publisher full HTML, Fortron PPS/rCF laboratory compound, ASTM D638, n=5|20 wt% rCF Table 5: 68.5±2.5 / annealed 81±2 MPa, ±=95% CI. AON-M2, nozzle 350 / bed 160 / chamber 100°C, flat ±45°, 100%. 23°C/50% RH ≥40 h conditioning.|abstract 86 MPa와 표가 충돌해 인장 수치 격리. laboratory compound를 다른 PPS-CF 제품 grade에 적용하지 않는다. D790 굽힘은 별도.|
|M03 [10.35860/iarej.862304](https://dergipark.org.tr/en/pub/iarej/article/862304)|[journal PDF](https://dergipark.org.tr/en/download/article-file/1512952), Owens XSTRAND GF30-PA6, ASTM D638 Type I, n=5/온도|시험 20°C 51±3, 60°C 26±2 MPa. Zortrax M200, 255/80°C, 40 mm/s, 0.4/0.19 mm nozzle/layer, 100% ±45°. 60°C 48 h 건조, 시험온도 30분 유지.|**단섬유 GF**이며 변수는 시험온도다. ±·면적·수분 상태 미확인. PDF 시각 표 검증은 완료하지 못했다.|
|M04 [10.3390/polym13162752](https://www.mdpi.com/2073-4360/13/16/2752)|[공식 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8401430/fullTextXML), PC EMERGE 8430-15 / TPU Ravathane 140 D70|ASTM D638-2 Type V, 23°C, crosshead 10–300 mm/min. Pellet→자체 filament, 80°C 24 h 및 50°C 4 h 건조. PC nozzle 255–270°C.|grade·속도 의존 경계 보완. 그래프 수치·조건당 n 미추출. D70은 TPU95A와 다르다. Methods의 raster 설명도 임의 정규화하지 않는다.|
|M05 [10.3390/polym15092011](https://www.mdpi.com/2073-4360/15/9/2011)|[공식 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10181410/fullTextXML), REC ABS/short-CF ABS, ISO 527-2, 조건당 ≥15|ABS-CF 0°: nozzle 0.4 mm 70.14±2.61 / 0.8 mm 79.12±1.65 MPa. Raise3D Pro2 Plus, 290/110°C, 30 mm/s, 100%, 0.5 mm/min 인장.|M06/M07 반복 셀 계보와 공정 충돌부터 해결. fiber fraction·정확한 grade·수분·면적 미확인. flexure·CT fracture는 UTS가 아니다.|
|M06 [10.3390/polym16081106](https://www.mdpi.com/2073-4360/16/8/1106)|[공식 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11055083/fullTextXML), REC short-GF ABS 등, ISO 527-2, n=15|ABS-GF 0°: 69.63±2.62 / 76.31±2.53 MPa. nozzle/layer는 0.4/0.2 및 0.8/0.4 mm. 강화재 290/110°C, 30 mm/s.|nozzle 크기 효과와 층 높이가 섞인다. ABS/ABS-CF 수치는 M05와 같으며 독립 holdout으로 사용할 수 없다.|
|M07 [10.1016/j.prostr.2024.06.029](https://www.sciencedirect.com/science/article/pii/S2452321624005663)|publisher 직접 접근 차단; [conference 원본 facsimile](https://fis.cld.bz/Issue-611/33/) pp.225–228 표/방법 확인|PA12-CF 0.4 mm 0° 47.79±3.08 / 90° 17.45±1.91 MPa. PETG-GF 0.8 mm 0° 52.93±2.31 MPa. Table 1은 50 mm/s.|grade·n·conditioning 미확인, PDF 시각 표 검증 미완료. M05/M06 반복 셀과 metadata 충돌. **PA12-GF 실험이 아니다.**|
|M08 [10.3390/polym17121590](https://www.mdpi.com/2073-4360/17/12/1590)|[공식 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12196584/fullTextXML), BASF PA6 + PA6 GF30 국부 hybrid, ISO 527, 인장 n=3/조건|Taguchi L9, geometry·layer·nozzle·150°C 열처리시간을 변화. Table 3 인장 평균 55.88–89.89 MPa.|균질 PA6-GF coupon 근거로 넣지 않는다. 인장/충격 표본 수 분리. 단일인자 곡선이나 모든 상호작용을 식별하는 설계가 아니다.|
|M09 [10.3390/polym18121422](https://www.mdpi.com/2073-4360/18/12/1422)|[공식 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13306934/fullTextXML), Fiberlogy PPA CF15, ISO 527, n=3/온도|기존 Table 2 9행 재사용: 시험 20°C 64.537±0.88 → 180°C 9.190±0.76 MPa. 290/100/50°C nozzle/bed/chamber, ±45°, 100%, 벽 5, 80 mm/s.|해당 grade 시험온도 비교. SD 미확정; TDS ASTM D792 속성 격리. 잔류수분·raw replicate·batch·면적 미확인.|
|M10 [10.3390/polym15030507](https://www.mdpi.com/2073-4360/15/3/507)|[공식 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9919798/fullTextXML), PA6 / Onyx short-CF / 추가 continuous-GF, n≥3|Flashforge process series는 single-wall panel을 die-cut; Mark Two는 다른 infill/continuous-fiber/fatigue series. 5 mm/min 인장.|시편 제작·printer·fiber form을 분리. 그래프 숫자 미추출. continuous-GF를 chopped PA6-GF로 사용하지 않는다.|
|M11 [10.1177/00219983231194391](https://doi.org/10.1177/00219983231194391)|[author-institution manuscript](https://eprints.whiterose.ac.uk/203421/1/lyu-et-al-2023-effects-of-thermal-process-conditions-on-crystallinity-and-mechanical-properties-in-material-extrusion.pdf), Torayca A630T-30V 자체 filament, D7264 3점 굽힘 n=3|Creatbot F430, 0.8 mm nozzle, 20 mm/s, longitudinal 100%, bed 90°C. 최고 굽힘강도 164.65 MPa: feedstock extrusion 280°C / print 320°C / anneal 130°C 6 h.|**굽힘 근거만** 보완. UTS나 다른 상용 PPS-CF grade에 적용하지 않는다. 세 열 이력을 하나의 온도로 합치지 않는다.|
|M12 [10.1108/RPJ-06-2024-0241](https://doi.org/10.1108/RPJ-06-2024-0241)|[primary institution PDF](https://scholar.tecnico.ulisboa.pt/api/records/2lXUe-cvtWaSqq-Yg-kQ4mdGzjNKtzqFgIrN/file/1f4a349c6ca0d4146b82c7830653b4ad170537e73fc6a25d29efb896007d3de6.pdf), Ultimaker TPU95A / Reciflex 92–98A, 조건당 n=4|TPU95A 0/90: nozzle 225/235/240°C에서 26.1±4.2 / 37.5±4.9 / 35.8±0.6 MPa. S5, 100%, 벽 2, top/bottom 0, layer 0.2 mm, 30 mm/s. 21°C/~60% RH, 20 mm/min.|수정 D412/D638 geometry, 3지점 실측 **초기 gross 면적**. ± 정의·건조·batch·raw curve 미확인. 같은 session; 영상 solid ratio를 flow ratio/접촉면적으로 사용하지 않는다.|

## 전 소재군 근거표

현재 상태는 런타임 카탈로그를 설명하며 이 보고서가 상태를 변경하지 않는다. “비교”는 특정 grade/조건/물성의 문헌 비교가 있다는 뜻이다. 모든 행의 범용 부품 강도 예측은 미확정이다. M01–M12는 위 원문 링크 및 JSON DOI에 대응한다.

|소재|현재 상태|가용 근거와 분리할 응답|다음에 필요한 자료|
|---|---|---|---|
|PLA|비교|[Grigoriev](https://doi.org/10.1038/s41598-024-79213-5), [벽 수/층 높이 하중](https://doi.org/10.3390/pr13092733), [cooling](https://doi.org/10.1007/s00170-024-14111-8), [실측 층간 접촉면적](https://doi.org/10.1089/3dp.2021.0112)|정확한 grade, 공정 충돌, 응력 면적 정의와 독립 검증. 접촉면적 강도를 gross 면적으로 전이하지 않음.|
|ABS|비교|Grigoriev·벽 수 하중, [flow](https://doi.org/10.1089/3dp.2023.0170), M05–M07|반복 셀 계보, 공정 metadata, 실제 flow와 batch.|
|PETG|비교|Grigoriev·벽 수 하중·flow; [Desouky v1](https://doi.org/10.17632/zvt28hz3kf.1)의 결과 workbook 없음|정확한 grade/면적, 명령 flow와 측정값 분리. 211 G-code는 인장 라벨이 아님.|
|ASA|비교|[논문](https://doi.org/10.3390/ma17215207)/[Zenodo](https://doi.org/10.5281/zenodo.14065523) 9시편; SENB fracture 별도|산술 통과 외에 batch·수분·시험/공정 context 및 독립 시편.|
|PETG-CF|부족|[층간 인장/열처리 후보](https://doi.org/10.1016/j.addma.2019.100922)|grade별 전체 결과·면적·orientation·조건.|
|PETG-GF|부족|M07 집계 인장, [2017 후보](https://doi.org/10.1016/j.proeng.2017.02.245), [2026 공정 후보](https://doi.org/10.1007/s00170-026-19068-4)|n·grade·fiber fraction·conditioning과 원자료.|
|ABS-CF|부족|M05–M07 인장; [파괴인성](https://doi.org/10.1016/j.addma.2018.02.023) 별도|중복/metadata 충돌 해결 후 시편·batch·면적.|
|ABS-GF|부족|M06/M07 short-GF 인장; [단/연속 보강 비교](https://doi.org/10.1002/pc.71317)|보강 형태·층/nozzle confounding·grade·n·계보.|
|PA6-CF|부족|M10, [local reheating](https://doi.org/10.1016/j.addma.2025.104705), [2026 Z 방향](https://doi.org/10.1017/pds.2026.10563)|moisture·grade·area와 제외 시편 기록; speed/fan/chamber 동시 변화에서 단독 계수 추정 금지.|
|PA6-GF|부족|M03 short-GF 온도 인장; M08 국부 hybrid 별도|문서 분류 수정, grade별 수분·실측 면적·raw replicate.|
|PA12-CF|부족|M01 grade별 인장 온도, M07 집계; [층간 파괴](https://doi.org/10.1016/j.compstruct.2019.02.005) 별도|M01을 비교용으로 정리하되 원자료·수분·batch·면적/습도 확보 전 보정 승인 금지.|
|PA12-GF|부족|[FFF 마찰·마모 후보](https://doi.org/10.3390/polym18182239)의 인장 TDS는 독립 실험 아님|이번 검색에서 적합한 chopped-GF FFF 인장행렬 미확인. PA12-CF, glass bubbles, SLS/MJF 대체 금지.|
|PPA-CF|비교|M09 실험 Table 2|TDS 표준 속성 격리, raw·batch·수분·area·독립 검증.|
|PPA-GF|부족|[microstructure/CT 후보](https://mrforum.com/product/9781644903599-32/)|primary tensile matrix·제품 grade·conditioning 미확인.|
|PPS-CF|부족|M11 굽힘; M02 충돌 있는 인장|굽힘→UTS 금지. 수치 정정 후 grade별 raw 인장 자료.|
|PC|비교|[NIST benchmark](https://doi.org/10.1007/s40192-020-00188-y), [층간 전단](https://doi.org/10.1016/j.jmrt.2022.12.147), M04 rate study|전단→UTS 금지; grade/시험 조건 및 holdout. 기존 NIST 웹 inch/mm typo 감사 재사용.|
|TPU|부족|M12 TPU95A; M04 D70; [elastomer 후보](https://doi.org/10.1016/j.polymertesting.2020.106687)|hardness·grade·rate·대변형·geometry·수분·raw curves와 독립 batch/session.|
|TPE|부족|기존 elastomer 후보|구체 chemistry/hardness/rate/형상; TPU 값을 TPE의 범용 값으로 사용하지 않음.|
|PPS-GF *(미등록 추가 범위)*|부족|이번 targeted 검색에서 적격 1차 FFF 인장 시편행렬 미확인|TDS·injection moulding·neat PPS·PPS-CF를 대체 근거로 넣지 않음.|

## 검증·모델에 적용할 경계

`calibration.py`는 property, grade, orientation, 면적, moisture/annealing, printer/process/test 조건과 study/lineage/batch/sample/source/locator를 요구하고 선언된 중복을 검사한다. 동일 조건 비교·최소 계보 수·leave-lineage-out baseline 검사는 유용하다. 그러나 외부 caller가 같은 실험을 다른 ID/URL로 넣으면 DOI 간 실제 중복은 놓칠 수 있다. **논문/데이터/실험 계보를 curator가 연결하고 관측값·context fingerprint로 중복 후보를 표시하는 절차**가 필요하다. fingerprint만으로 시편 동일성을 확정하지 않는다.

gross 면적, net deposited 면적, 영상의 solid fraction, 파단면 실측 bonded contact 면적은 서로 다른 분모다. 관측 UTS를 infill로 나눠 “net 강도”를 만들거나 PLA 접촉면적 결과를 모든 소재에 곱하지 않는다. 힘 N, 인장 MPa, 굽힘 MPa, 전단 MPa, 파괴인성, 피로, 대변형 elastomer 응답도 별도다. command flow/G-code E와 실측 질량·부피·void/contact fraction을 분리한다.

기존 Grigoriev 180개 개별 시편·30개 평균, Menargues 25개 평균 하중 N, PPA 9개 평균과 18개 공개 ASA/ASA-CF는 서로 다른 단위/집계 수준이다. 논문·supplement·dataset DOI와 시편·평균을 중복 계수하지 않는다. 기존 Aktepe/Ergun 500 configuration means는 보고된 물리 3개/configuration을 개별 라벨로 복원할 수 없고, effective n·제외 실패·raw scatter가 빠져 있다. [기존 감사 문서](research-update-20261001.md)와 [wall/flow 감사](process-walls-flow-data-audit-20261003.json)를 재사용했다.

기존 Grigoriev 중간 infill 보류 오차는 자료 구조를 본 뒤 정한 **같은 연구 내 보간 진단**이다. 새로운 grade/lab/부품의 prospective accuracy가 아니다. M01과 M09가 다른 grade 연구라도 같은 연구진이라는 사실, M12의 여러 pattern이 같은 print session이라는 사실을 기록해야 한다.

## 구체적 다음 작업

1. **수치 수입 전:** M05/M06/M07의 반복 셀은 하나의 관측 계보로 묶고 공정 충돌을 격리한다. M02의 서로 다른 수치와 CI는 원 locator 그대로 보존하고 target 승인을 보류한다.
2. **문서/근거 정리:** M03의 short-GF 설명, M11의 flexural property, M09의 TDS 표준 오류를 바로잡는다. M01 PA12-CF15와 M12 TPU95A는 조건·n·미확인값을 보존한 comparison record 후보로 추가할 수 있다.
3. **추가 데이터 획득:** 시편 ID·제품/lot·raw load/displacement/strain·실측 gauge dimensions·drying/moisture uptake·실패위치/형태·제외사유·논문 간 계보를 요청할 준비를 한다. 이 검토에서는 연락하지 않았다.
4. **새 검증 설계:** grade별 독립 lot/session과 외부 source/lab holdout을 미리 정하고, 측정 flow/면적·thermal history·conditioning을 기록한다. 식별 가능한 효과만 적합하고 entire lineage를 보류하며 context baseline과 비교한다.
5. **부품 검증:** 알려진 fixture/load·stress concentration·failure location을 가진 부품 실험을 coupon UTS와 별도로 수행한다. uncertainty/prediction interval과 failure-mode 경계를 보고하며 범용 정확도 %를 만들지 않는다.

이 보고서가 제안하는 런타임 개선은 근거 입력에서 **실험 계보·물성·면적·섬유 형태·geometry와 미확인 통계값을 더 엄격하게 분리하는 것**이다. 이 자료만으로 새 배율이나 범용 예측을 활성화할 근거는 없다.

## 상용 grade 모델의 최소 결과와 외부 보류 조건

배포 가능한 성능을 보장하는 범용 표본 수는 없다. 아래는 **초기 검증 프로그램의 제안 하한**이며 ASTM의 공통 요구나 안전성 보증이 아니다. 현재 코드의 eligible 계보 ≥3 및 leave-lineage-out 개선은 후보 screening 조건일 뿐, untouched 외부 검증을 대신하지 않는다.

- **정의:** 정확한 제품/grade·fiber form/fraction·hardness·lot·conditioning 범위, 하나의 물성/면적 정의와 허용 공정·형상 범위를 먼저 고정한다.
- **학습 프로그램:** grade가 같은 독립 실험 campaign을 최소 3개 확보하고 lot/session을 구별한다. 선택한 단일 수치 인자는 최소 3개 설계 수준, 시험 조건당 유효 인장 결과는 처음에는 ≥5개를 계획한다. 출력 실패·제외도 전부 기록한다. 논문 DOI가 다르거나 같은 session에서 pattern만 달라졌다는 이유로 독립 campaign을 만들지 않는다.
- **외부 보류:** 새로운 lot/session, 가능하면 다른 lab의 **추가 campaign ≥1개**를 모델 선택 전에 완전히 보류한다. 미리 정한 정상 조건과 경계 조건당 유효 결과 ≥5개를 초기 계획으로 삼고 fit/tuning/조건 선택에 사용하지 않는다.
- **시편별 최소 결과:** raw time/load/displacement/strain, instrument/test 조건, 실측 초기 gauge 면적, failure mode/location, 제품/lot/session ID, 모든 process·thermal·conditioning 기록, actual flow/면적 측정이 필요한 predictor, 모든 실패/제외와 명시된 SD/SE/CI가 필요하다.
- **표본 수와 승인:** lot 내/lot 간 분산을 보고 허용 오차·prediction-interval coverage·목표 신뢰도를 미리 정한 뒤 표본 수를 늘린다. n=5는 tail failure probability나 고신뢰 안전한계를 증명하지 않는다. blind holdout에서 baseline·편향·interval coverage를 확인하고, 실패 뒤 같은 holdout을 다시 독립 검증이라고 부르지 않는다.
- **여러 인자·부품:** wall×flow×thermal 등의 상호작용을 주장하려면 설계된 interaction matrix와 confirmation 조건을 추가한다. 실제 fixture·stress concentration·failure location이 있는 부품 시험은 coupon 모델과 별도다.

상용 수준과 특허 가능성은 작업 목표다. 성능 검증과 신규성·진보성/청구범위 검토를 완료했다는 뜻은 아니다. 이 재료 보고서는 특허성 판단을 수행하지 않았다.

## English research handoff

The review covers all 18 registered families plus requested PPS-GF. Twelve primary paper records were newly checked or refreshed; they are not twelve independent lineages. There are still no approved runtime material models and no independent external validation specimens. Existing public ASA/ASA-CF arithmetic passes, while calibration rejects missing context.

The most useful new aggregate candidates are grade-specific PA12 CF15 test-temperature data (M01, n=3, SD explicit) and TPU95A data (M12, n=4, measured initial gross area, modified geometry). They can improve comparison coverage after curation, not enable transferable multipliers.

Quarantine repeated ABS/ABS-CF/ABS-GF cells across M05–M07 until experiment lineage and conflicting process metadata are resolved. Quarantine M02 PPS/rCF tensile targets because abstract, table and narrative disagree; its spread is a 95% confidence interval. Correct the M03 documentation to short GF; the runtime coverage text is already correct. M11 is flexural, not tensile. M09's manufacturer-data ASTM D792 attribution is erroneous; its separate experimental ISO 527 table remains a different source.

Retain experiment/campaign/batch/lab identities beyond caller-provided DOI/URL IDs. Do not mix gross, deposited and bonded-contact area; tensile, flexural, shear, fracture and fatigue responses; chopped/continuous/local hybrid reinforcement; or commanded and measured flow. No licensed source files, product code or deployment were changed. Access limitations and full dedupable DOI metadata are in the JSON report.
