# 연구 근거와 실증 범위

[한국어](#한국어) · [English](#english)

## 한국어

기준일: 2026-09-25. 이 문서는 검토한 연구자료의 자체 요약이다. 논문 전문·그림·원시 시험파일은 복제하지 않으며, 원문과 공식 데이터 저장소로 연결한다. `S`와 `W` 번호는 검토 자료의 출처 식별자이며 논문 수나 독립 실험 수를 뜻하지 않는다.

**현재 엔진은 임의 출력물의 파단하중이나 가장 먼저 파손될 위치를 실증적으로 검증한 모델이 아니다.** 논문 관측값, 제조사 소재 참조, 기하학적 비교, 미보정 하중 시나리오를 구분한다. 단위가 같더라도 인장·층간 전단·굽힘·파괴인성은 서로 대체하지 않는다.

## 현재 코드에 적용되는 범위

|모듈 / 버전|사용하는 근거와 동작|검증되지 않은 부분|
|---|---|---|
|[`process.py`](../print_strength_engine/process.py), `GCODE_PROCESS_EVIDENCE_V3_THERMAL_CONTEXT`|읽힌 공정조건을 보존한다. `factor_status=NOT_APPLIED`, `is_prediction=false`, `effective_mpa=null`이다.|`factors`의 1은 호환용 미적용 표시다. 동일 강도라는 예측이나 검증 오차 계산에 사용하면 안 된다. 온도·속도·층 높이에서 강도로의 보정식은 적용하지 않는다.|
|[`evidence.py`](../print_strength_engine/evidence.py), `PRIMARY_LITERATURE_COMPARISONS_V1`|S050·S088·S028의 조건과 관측값을 문헌 비교로 제공한다. 물성·소재군을 구분하고 불일치·미확인 조건을 남긴다.|`LITERATURE_COMPARISON_ONLY`이며 목표 제품에 적용되는 전이계수가 없다. 같은 소재군 또는 같은 인장 축만으로 grade·배치·열이력이 일치하지 않는다.|
|[`infill.py`](../print_strength_engine/infill.py)|Ben Amor 등(2024)의 PLA 10–100% 구간을 같은 연구 내 상대응력으로 비교한다. 구간 내 선형보간은 명시적 비교 연산이다.|현재 부품의 패턴·벽 수·브랜드에 보정되지 않았다. 10% 미만 외삽, Z강도 보정, 실제 재료면적에 비율 재적용은 하지 않는다.|
|[`capacity.py`](../print_strength_engine/capacity.py), `CAPACITY_SCENARIO_V5_EXPLICIT_LOAD_CASE_REQUIRED`|기존 외곽 단면 기반 힘 계산을 보류한다. 별도 `load_case` API는 명시적 고정·하중 조건과 완전한 경로 단면이 있어야 정상응력을 계산한다.|`is_failure_prediction=false`, 파단하중 null. 지원하지 않는 형상·조건은 보류한다. [현재 계약](../README.md).|

온도·유량의 도구별 목록은 보존하며, 서로 다른 값 또는 유효하지 않은 슬롯이 섞이면 대표 스칼라를 만들지 않는다. 최소 레이어 시간 설정은 국소 재방문 시간 실측과 다르고, 노즐 설정온도는 기판·접합면 온도 실측과 다르다. 전체 출력시간을 레이어 수로 나누어 국소 열이력을 만들지 않는다.

명목 100% 인필도 공극이 없다는 증거가 아니다. 2026-10-01 V5에서 기존 직사각형 shell/core 축력 가정, 패턴 상수, core 지수 1.4 및 추정 지렛대 계산을 제거했다. 명시적 하중 API의 직사각형 증착 경로 단면도 실제 접합·공극 측정은 아니며, 제한된 보 형상에서 조건부 정상응력만 계산한다. 레이어 압출량 기반 면적 proxy는 연결된 단면이 아니므로 힘으로 환산하지 않는다. [추가 연구와 보류 검증](research-update-20261001.md)을 함께 확인한다.

응력의 분모가 `NET_MATERIAL` 또는 `INTERLAYER_CONTACT`이면 외곽 면적과 곱하는 계산을 차단한다. `UNKNOWN`은 기존 미보정 시나리오만 허용하며 적합성이 검증됐다는 뜻이 아니다. API의 `allowable_mpa`라는 기존 필드명도 인증된 허용응력이나 안전계수의 근거가 되지 않는다.

## 핵심 논문: 관측값과 사용 한계

아래 확인 범위는 기존 원문·표·원자료 검토 기록에 따른다. 수록된 모든 행을 원문 전체와 대조했다는 의미는 아니다.

|출처와 원문|확인한 물성·시험조건|엔진 연결 및 제한|
|---|---|---|
|S050 — **An Experimental Study on the Impact of Layer Height and Annealing Parameters on the Tensile Strength and Dimensional Accuracy of FDM 3D Printed Parts** (Stojković et al., 2023). DOI [10.3390/ma16134574](https://doi.org/10.3390/ma16134574), [공개 원문 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10342851/fullTextXML)|PrimaSelect PLA PRO, 비열처리, ASTM D638-14 Type I. 노즐 210°C, 베드 60°C, 출력속도 설정 50 mm/s, 75% cubic, 벽·상하 두께 0.6 mm. 층 높이 0.1/0.2 mm의 응력 32.15/30.07 MPa. **32.15는 보고된 33.37−1.22를 역산한 값**이다.|층 높이의 문헌 비교. 시험축·수분조건·해당 비교의 n/분산이 충분히 확인되지 않았다. 정규화 비율 0.93530은 목표 부품 보정계수가 아니다.|
|S088 — **Mechanical and Thermal Behavior of Ultem 9085 Fabricated by Fused Deposition Modeling** (Padovano et al., 2020). DOI [10.3390/app10093170](https://www.mdpi.com/2076-3417/10/9/3170)|ULTEM 9085, Fortus 450mc, 100% 인필, 벽 3개, 선폭 0.508 mm, air gap 0, raster ±45°, ASTM D638-14 Type I, 인장속도 5 mm/min. Table 3: XY/X 65.9±0.7, XZ/X 73.0±1.3 MPa, 각각 n=5.|둘 다 인장 방향은 X이나 출력 배치 XY/XZ가 다르다. 같은 축 입력으로 배치효과를 표현할 수 없다는 진단이다. 두 평균은 논문에서 같은 Tukey 그룹이므로 평균차만으로 유의한 차이를 주장하지 않는다. 해당 grade의 검증된 엔진 소재 참조는 없다. 출력온도·층 높이·속도는 비교 입력에서 미확인이다.|
|S028 — **Efficient characterization on the interlayer shear strengths of 3D printing polymers** (2023; 저자 표기 미확인). DOI [10.1016/j.jmrt.2022.12.147](https://doi.org/10.1016/j.jmrt.2022.12.147)|Table 2의 층간 전단: PLA 25.74±1.03 MPa(n=10), ABS 23.01±1.63(n=10), PC 30.16±1.64(n=9). necking-shaped pure-shear 시험, print-surface angle 90°.|층간 **전단** 참고값이다. 인장 참고응력 또는 굽힘 파단하중으로 넣지 않는다. 제품 grade와 일부 공정조건은 비교 입력에서 미확인이다.|
|S026 — **Weld formation during material extrusion additive manufacturing** (Seppala et al., 2017). DOI [10.1039/C7SM00950J](https://doi.org/10.1039/C7SM00950J), [NIST 공개 원문](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=923318)|열이력과 접합 형성, mode III 파괴에너지의 관계를 다룬다.|열이력 확보 필요성의 근거다. 파괴에너지를 MPa로 대체하거나 범용 출력속도 감쇠계수로 사용하지 않는다.|
|S109 — **Impact of process parameters and material selection on the mechanical performance of FDM 3D-Printed components** (Haque et al., 2025). DOI [10.1016/j.hybadv.2025.100502](https://doi.org/10.1016/j.hybadv.2025.100502)|Bambu 소재·공정 조합의 publisher-indexed Methods/Tables 3–4 검토. 추출한 9설정의 36쌍 중 다른 조건을 고정한 단일변수 쌍은 0개였다.|개별 인필·속도·패턴 효과를 분리하지 못한다. 응답행렬·형상·일부 조건 원문 추출도 불완전하다. 연구의 최고값을 독립 검증점이나 단일변수 보정으로 채택하지 않는다.|
|별도 인필 출처 — **Material Investigation and Effect of Printing Orientation, Tensile Speed, and Density on the Mechanical Behaviour of 3D Printed Parts** (Ben Amor et al., 2024), DOI [10.35219/awet.2024.10](https://doi.org/10.35219/awet.2024.10), [원문 PDF](https://www.gup.ugal.ro/ugaljournals/index.php/awet/article/download/7105/6002)|Raise3D Premium PLA, Section 4.2/Table 6: 인필 10/30/60/80/100%에 19/21/24/27/34 MPa.|현재 PLA lookup 자체의 출처다. 같은 표를 lookup과 비교해 일치하는 것은 **same-source replay**이며 독립 예측 검증이 아니다. 현재 패턴·벽 수·조건 일치는 보장되지 않는다.|

## 열이력과 응력 면적 정의에 관한 추가 근거

|출처와 확인 수준|확인한 조건|적용·미적용 판단|
|---|---|---|
|W011 — **The effect of the interlayer time and deposition speed on the tensile properties of material extrusion components** (Lambiase et al., 2024). DOI [10.1007/s00170-024-14111-8](https://link.springer.com/article/10.1007/s00170-024-14111-8), [공개 PDF](https://d-nb.info/1346221405/34). Methods/Tables 1–2 확인.|RS PRO PLA, Ender 6, 노즐 210°C/베드 60°C, 노즐 0.4/선폭 0.5/층 높이 0.2 mm, 100% rectilinear, fan 100%. 2000/3000/4000 **mm/min**와 재방문 21/63/105 s의 3×3 설계, G04 dwell 제어, 조건별 n=6. 판에서 waterjet 가공한 upright ASTM D638 Type 2, 인장 2 mm/min.|속도 단위와 국소 재방문 시간을 구분해야 한다. 결론의 25.5/21.1 MPa 요약은 속도별 고정조건 쌍으로 확정하지 않았다. Fig. 10의 조건별 분산은 이번 자료에 완전히 전사하지 않았다. 범용 시간 보정계수 미적용.|
|W012 — **Bulk-Material Bond Strength Exists in Extrusion Additive Manufacturing for a Wide Range of Temperatures, Speeds, and Layer Times** (Moetazedian et al., 2023). DOI [10.1089/3dp.2021.0112](https://journals.sagepub.com/doi/10.1089/3dp.2021.0112), [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10280202/). publisher-indexed Methods 확인; 원문 일괄 다운로드·부록 확인은 미완료.|3DXTECH/NatureWorks 4043D PLA, RepRap X400, 노즐 0.4/선폭 0.5/층 높이 0.2 mm. 기준 210°C, 1000 mm/min, 10 s. 온도·속도·시간을 별도 통제하며 bead 형상을 유지하도록 압출량 조절. 기계시험 n=5, 0.5 mm/min. 단일 bead 벽의 현미경 측정 **실제 Z 파단 접촉면적**으로 응력 계산.|접촉면 강도가 벌크에 가깝다는 결과를 외곽 면적의 부품강도로 전이하지 않는다. 전체 3요인 factorial 실험도 아니다. 일부 벌크 비교값은 W013과 계보가 겹친다.|
|W013 — **Interlayer bonding has bulk-material strength in extrusion additive manufacturing: New understanding of anisotropy** (Allum et al., 2020). DOI [10.1016/j.addma.2020.101297](https://doi.org/10.1016/j.addma.2020.101297), [기관 저장소](https://repository.lboro.ac.uk/articles/journal_contribution/Interlayer_bonding_has_bulk-material_strength_in_extrusion_additive_manufacturing_New_understanding_of_anisotropy/12443528), [accepted manuscript](https://ndownloader.figshare.com/files/22939619). 원고 확인.|Table 1의 층 높이·선폭 각 5변형, F/Z 방향, 노즐 0.4 mm/210°C, 1000 mm/min, 베드 60°C. Fig. 14의 특정 F/Z 조건에서 하중지지 면적 비율 94.5%/64.8%.|특정 조건의 접촉·재료면적 비율을 모든 100% 인필 출력에 적용하지 않는다. Fig. 15의 국소 응력과 접합 자체 강도는 전체 부품 내력과 구분한다. 모든 그룹의 n·분산 전사는 미완료다.|

논문의 접합 개선 잠재량을 같은 배수의 부품강도 증가로 해석하지 않는다. 위 연구는 열이력·접촉기하를 보존하고 모르는 값을 채우지 않는 설계의 근거이며, 범용 온도·시간 계수를 제공하는 것으로 취급하지 않는다.

## ASA / ASA-CF 노치 굽힘: 실제 원자료 기반 조건부 비교

|논문|공식 대응 데이터|확인 범위|
|---|---|---|
|W027 — **Notch Effect in Acrylonitrile Styrene Acrylate (ASA) Single-Edge-Notch Bending Specimens Manufactured by Fused Filament Fabrication** (Cicero et al., 2024). DOI [10.3390/ma17215207](https://doi.org/10.3390/ma17215207), [공개 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11547397/fullTextXML)|W028 — [Zenodo 14065523](https://zenodo.org/records/14065523), DOI 10.5281/zenodo.14065523|3DJake ASA, flat, 층 높이 0.2/선폭 0.42 mm, 100% 인필, 노즐 250°C/베드 90°C, 40 mm/s. ASTM D638 인장 및 ASTM D6068 SENB, 실온 1 mm/min. 노치는 출력 후 가공하며 crack-like 결함은 razor blade로 형성.|
|W029 — **Fracture Behavior of Additively Manufactured Carbon Fiber Reinforced Acrylonitrile-Styrene-Acrylate Containing Cracks and Notches** (Cicero et al., 2025). DOI [10.3390/jcs9040185](https://www.mdpi.com/2504-477X/9/4/185)|W030 — [Zenodo 14882928](https://zenodo.org/records/14882928), DOI 10.5281/zenodo.14882928|3DJake ASA-CF10, CF 10 wt.%, neat ASA와 대응 출력조건. publisher 검색 색인의 Methods/Table 1과 공식 원자료 확인. 직접 publisher 접근 제한으로 전체 PDF·그림 검증 완료는 주장하지 않는다.|

공식 XLSX 8개는 공개 MD5와 대조했고 SHA-256도 기록했다. 162개 시편 시트 중 인장 18개와 SENB 143개에 유효한 관측값이 있었고, 무데이터 시트 1개를 제외했다. 누락된 하중·변위를 0으로 채우지 않았다. 논문 두 편과 데이터 항목 두 개는 **2개 실험 계보**이며, 같은 연구진·프로젝트의 대응 실험으로 독립 실험실 재현이 아니다.

별도의 시험 전용 비교에서는 같은 소재·raster 인장시험의 평균 UTS와 각 SENB 시편의 실제 치수를 사용했다.

```text
UTS = 인장 곡선 최대하중 / 인장 시편 면적
Znet = B × (W − a)^2 / 6
Fbaseline = 4 × mean(UTS) × Znet / S
```

여기서 B는 SENB 두께, W는 폭, a는 노치 깊이, S는 실제 지지간격이다. 확인한 S는 40 mm다. 인장 시트의 a/b는 인장 단면 치수이므로 SENB 기호 a와 혼용하지 않았다. 파일의 30/60, 45/45 표기는 논문에 근거해 각각 30/−60, 45/−45 raster로 명시적으로 정규화했다.

비교 대상은 곡선의 **관측 최대하중**이며 자동으로 최초 균열하중 또는 최종 파단하중이라고 부르지 않는다. 소재·raster별 인장 n=3을 사용한 무적합 nominal-stress baseline에서 조건별 평균 예측/관측 비율은 ASA 0.384–0.663, ASA-CF 0.438–0.685였다. 이 통계는 시편별 비율의 그룹 평균이며 그룹 평균하중끼리 나눈 값이 아니다.

이는 엔진 전체 정확도가 아닌, 실제 시험 지지조건에 맞춘 **별도 물리 가정의 진단**이다. 노치 응력집중·균열·소성·TCD를 계산하지 않았고 계수를 fitting하지 않았다. 원 G-code와 가공 후 형상·fixture를 엔진에서 재구성한 검증도 아니다. 논문의 fitted critical distance로 같은 시험을 재현하면 fitting/replay에 해당하므로 독립 holdout과 구분해야 한다. 가공 노치 coupon의 파괴는 임의 부품 후보 중 취약 위치를 맞혔다는 증거가 아니다.

## 제조사 참조·자료 감사·통계 검증의 구분

현재 연동 앱이 사용하는 주요 제조사 참조는 아래와 같다. 값은 0.85 적용 **전**의 XY/Z 인장 참고응력이며, 다음 조건은 앱에 기록된 출처·시험 메타데이터다. 이번 문서 보완에서 모든 TDS를 새로 전수 대조했다는 뜻은 아니다.

|제조사 제품·공식 자료|원자료 XY / Z (MPa)|기록된 시험조건과 매칭 한계|
|---|---:|---|
|[eSUN ABS 공식 제품 자료](https://www.esun3d.com/abs-product)|42.23 / 16.97|앱의 해당 참조에는 상세 시험 표준·온도·후처리가 구조화되어 있지 않다. ABS+와 구분한다. Generic ABS에는 동계열 대체 참고값으로 사용하며 실제 스풀 제품을 확정하지 않는다.|
|[eSUN PLA-Basic TDS](https://www.esun3d.com/media/esun/catalog/certification/product/PLA-Basic/PLA-Basic-TDS-EN-_2026.6.5.pdf)|64.27 / 32.34|Bambu P1S, 노즐 0.4 mm, 220°C, 베드 65°C, 인필 100% 제조사 표준 출력 시편. Generic PLA의 대체 참고자료이며 현재 부품과 제품·시험조건의 일치를 인증하지 않는다.|
|[Bambu Lab PLA Basic TDS](https://c.cdnmp.net/712781591/content/Bambu_PLA_Basic_Technical_Data_Sheet.pdf)|35 / 31|노즐 220°C, 베드 35°C, 인필 100%, 55°C에서 8시간 열처리·건조. 명시적인 PLA Basic 프로파일의 참조이며 다른 PLA 등급으로 전이하지 않는다.|
|[Bambu Lab ABS TDS V3.0](https://store.bblcdn.com/s7/default/23b4cf2b83d5470bb96d19970b5f3ae8/Bambu_ABS_Technical_Data_Sheet_V3.pdf)|33 / 28|ISO 527 / GB/T 1040, 노즐 260°C, 베드 80°C, 200 mm/s, 인필 100%, **80°C에서 12시간 열처리·건조**. 기본 ABS 프로파일에 대응하며 무후처리 부품의 강도로 해석하지 않는다.|

앱은 이 원자료에 내부 여유계수 **0.85를 한 번** 적용해 방향별 표시 참고값을 만든다. 이 계수는 논문 실측으로 보정한 계수도, 통계적 하한도, 검증된 안전율도 아니다(`UNVALIDATED_INTERNAL_MARGIN`). 이후 공정 예측은 여전히 보류되며, TDS 프로파일 이름만으로 실제 장착 스풀을 인증하지 않는다. 제조사 데이터의 XY를 X/Y에 함께 사용하는 것도 실제 부품의 두 방향 강도가 동일하다는 실증은 아니다.

제조사 TDS의 출력 coupon 값은 그 제조사·제품·방향·시험조건의 참고값이다. 예를 들어 검토 중 확인한 eSUN PETG XY 34.77/Z 28.65 MPa의 일치는 **같은 제조사 원출처 전사 확인**이었다. 독립 논문 검증, 다른 grade로의 전이, 설계 허용값 인증으로 세지 않는다. 이 엔진은 입력 참고응력의 출처·grade·조건을 호출 측에서 제공해야 하며 소재 이름만으로 provenance를 만들어내지 않는다.

|자료 감사 범위|확인 결과|그 결과로 주장할 수 없는 것|
|---|---|---|
|초기 bundle|출처 200개, 수치행 134개, 수치가 있는 출처 19개. manifest 12개 항목 대조 통과. 시험법 미기재 128행, n 미기재 129행, SD 미기재 118행.|200편 전문 확인 또는 134개 독립 검증점이라는 주장은 불가. 동일 grade·물성·방향·조건 기준으로 당시 비교 가능한 독립 검증행은 0개, 같은 출처 재현은 2개였다.|
|추가 supplement|출처 38개, 수치행 148개, 수치 출처 14개. manifest 7개 항목의 hash/bytes, JSONL/CSV의 행·필드·순서, source FK·단위 정합성 통과.|파일 무결성은 원문 수치의 진실성·시험 설계 타당성 인증이 아니다.|
|추가 자료의 증거 유형|직접 보고 주장 131행, 파생 통계 9행, 초록 6행, 결론 1행, 모델 파생 1행으로 감사상 재분류. n 누락 121행, SD와 CI 모두 누락 114행.|직접 보고라는 제출 라벨을 모두 원문 검증 완료로 바꾸지 않는다. 제출된 148행 모두 구조화된 page/table/figure locator가 없었으며 이후 일부 출처만 표적 대조했다.|
|출처 중복|W020=S027, W037=S186, W038=S051. W019는 앞선 followup에도 존재. W027/W028 및 W029/W030은 논문–데이터 계보 쌍.|새 URL·DOI·표·시편 수를 독립 연구 수로 합산하지 않는다. 중복 제거 후에도 동일 실험실·제품·재인용 관계를 추가 확인해야 한다.|

과거 V1 감사에서 S050/S088에 대해 identity 비율 1과 관측 비율의 차이를 계산한 기록은 **V1 표현력 진단의 역사적 결과**다. 이후 V2에서 보정을 철회했고 현재 V3도 예측을 보류한다. 그러므로 그 차이를 현재 엔진 오차율로 다시 보고하지 않는다. 같은 표의 lookup 재현, 단위 변환, hash 일치, 회귀시험 통과 역시 통계적 예측 검증을 대신하지 않는다.

## 추가 실증에 필요한 자료

독립 검증을 위해서는 동일 제품 grade·배치·건조/조습·열처리, 방향과 raster 정의, 실제 공정조건, 시험 표준과 치수·면적 정의, 지지·가력점, 원 하중 곡선, 반복수와 분산을 함께 확보해야 한다. 위치 정확도를 평가하려면 같은 입력 형상의 관측 파괴 위치와 실제 하중·구속 label이 필요하다.

모델을 보정할 때는 학습과 평가 조건을 사전에 분리하고, 같은 조건의 반복 시편 검증과 미사용 raster·노치·제품·실험실로의 일반화 검증을 구분해야 한다. 현재 문헌 목록과 조건부 비교만으로 범용 정확도, 예측구간 또는 인증된 안전계수를 제시하지 않는다.


---

## English

### Evidence summary and limits

This English section summarizes the core evidence and decisions in the Korean source matrix above. Source IDs, DOI links, conditions and unresolved items remain traceable there. The historical audit scope is not a claim that every listed paper was read in full. **The engine is not empirically validated to predict the first failure location or breaking load of an arbitrary printed part.** Tensile, interlayer shear, bending and fracture-toughness quantities are not interchangeable merely because some share units.

Current process evidence (`GCODE_PROCESS_EVIDENCE_V3_THERMAL_CONTEXT`) preserves conditions, returns `factor_status=NOT_APPLIED`, `is_prediction=false` and `effective_mpa=null`. Identity factors are compatibility placeholders, not predictions. Literature comparisons have no approved transfer coefficient to the target part. Capacity V5 (`CAPACITY_SCENARIO_V5_EXPLICIT_LOAD_CASE_REQUIRED`) withholds legacy force scenarios. The separate explicit-load API returns conditional normal stress for supported complete geometry only, never a validated failure load. See [new research](research-update-20261001.md).

Per-tool temperature/flow slots are retained; conflicting or incomplete lists do not produce a representative scalar. A minimum-layer-time setting is not measured local return time, and nozzle setpoint is not measured substrate/bond temperature. Total duration divided by layer count is not used to invent local thermal history.

Nominal 100% infill is not evidence of void-free material. On 2026-10-01 V5 removed the legacy shell/core force assumption, pattern constants, core exponent 1.4 and guessed lever. Rectangular deposition sections in the explicit-load API still do not measure actual welds or voids. Layer-volume proxies are not connected sections and are not converted to force. Unknown-area material references cannot establish net-material stress margins. The legacy API name `allowable_mpa` does not certify a design allowable or safety factor.

### Primary studies used for comparisons

|Source|Verified observation / context|Use and limitation|
|---|---|---|
|S050, Stojković et al. (2023), [10.3390/ma16134574](https://doi.org/10.3390/ma16134574)|Unannealed PrimaSelect PLA PRO, ASTM D638-14 Type I; 210°C nozzle, 60°C bed, 50 mm/s, 75% cubic, 0.6 mm walls/top/bottom. At 0.1/0.2 mm layer height: 32.15/30.07 MPa. The 32.15 value is reconstructed as 33.37−1.22.|Layer-height comparison only. Axis, moisture and relevant n/variance are incompletely established. Ratio 0.93530 is not a target-part correction.|
|S088, Padovano et al. (2020), [10.3390/app10093170](https://doi.org/10.3390/app10093170)|ULTEM 9085, Fortus 450mc, 100% infill, three walls, 0.508 mm line width, zero air gap, ±45° raster. Table 3 XY/X 65.9±0.7 and XZ/X 73.0±1.3 MPa, n=5 each.|Same tensile X direction, different build placement. Both means share a Tukey group; their difference alone does not establish significance. No validated engine reference for this grade.|
|S028 (2023; author attribution not verified), [10.1016/j.jmrt.2022.12.147](https://doi.org/10.1016/j.jmrt.2022.12.147)|Necking-shaped pure-shear test, 90° print-surface angle. Table 2 PLA 25.74±1.03 (n=10), ABS 23.01±1.63 (n=10), PC 30.16±1.64 MPa (n=9).|Interlayer **shear**, not tensile reference stress or bending breaking load. Grade and some conditions remain unknown.|
|S026, Seppala et al. (2017), [10.1039/C7SM00950J](https://doi.org/10.1039/C7SM00950J)|Thermal history, weld formation and mode III fracture energy.|Supports recording thermal history; supplies no universal speed penalty or interchangeable MPa value.|
|S109, Haque et al. (2025), [10.1016/j.hybadv.2025.100502](https://doi.org/10.1016/j.hybadv.2025.100502)|Publisher-indexed Methods/Tables 3–4 inspected. Of 36 pairs among nine extracted settings, none isolated a single variable while holding others fixed.|Cannot identify independent infill/speed/pattern effects. Matrix/geometry extraction incomplete; maximum values are not independent validation labels.|
|Ben Amor et al. (2024), [10.35219/awet.2024.10](https://doi.org/10.35219/awet.2024.10)|Raise3D Premium PLA, Section 4.2/Table 6: 10/30/60/80/100% infill → 19/21/24/27/34 MPa.|Source of the PLA within-range interpolation. Replaying the same lookup is not independent validation; no guaranteed target pattern/wall/brand match or invented Z correction.|

### Thermal history and stress-area definition

W011, Lambiase et al. (2024), [10.1007/s00170-024-14111-8](https://doi.org/10.1007/s00170-024-14111-8), uses RS PRO PLA and a 3×3 design of 2000/3000/4000 **mm/min** and 21/63/105 s return times controlled by G04 dwell, n=6 per condition. The settings include 210/60°C nozzle/bed, 0.4/0.5/0.2 mm nozzle/line/layer, 100% rectilinear and 100% fan. The conclusion's 25.5/21.1 MPa summaries were not established as fixed-condition speed pairs; all Figure 10 dispersion was not transcribed. No universal time coefficient is applied.

W012, Moetazedian et al. (2023), [10.1089/3dp.2021.0112](https://doi.org/10.1089/3dp.2021.0112), studies 3DXTECH/NatureWorks 4043D PLA on a RepRap X400. Baseline: 210°C, 1000 mm/min, 10 s; 0.4/0.5/0.2 mm nozzle/line/layer. Variables are controlled separately with extrusion adjusted to maintain bead geometry; mechanical tests n=5 at 0.5 mm/min. Stress uses microscopy-measured **actual Z fracture contact area** in single-bead walls. Near-bulk contact strength cannot be transferred to whole-part envelope strength. It is not a complete three-factor factorial, and some bulk comparisons share lineage with W013. Full appendix verification is incomplete.

W013, Allum et al. (2020), [10.1016/j.addma.2020.101297](https://doi.org/10.1016/j.addma.2020.101297), examines five layer-height and line-width variations each, F/Z directions, 0.4 mm nozzle/210°C, 1000 mm/min, bed 60°C. The 94.5%/64.8% load-bearing-area fractions in particular Figure 14 F/Z conditions are not universal factors for 100% infill. Local bond stress is distinct from whole-part capacity; complete group n/variance transcription remains unfinished.

### ASA and ASA-CF raw-data diagnostic

W027, Cicero et al. (2024), [10.3390/ma17215207](https://doi.org/10.3390/ma17215207), pairs with W028 [Zenodo 14065523](https://zenodo.org/records/14065523). W029, Cicero et al. (2025), [10.3390/jcs9040185](https://doi.org/10.3390/jcs9040185), pairs with W030 [Zenodo 14882928](https://zenodo.org/records/14882928). These are two experimental lineages from related investigators/projects, not four independent studies or independent-laboratory replication.

The 3DJake ASA and ASA-CF10 (10 wt.% CF) specimens use corresponding flat-build conditions: 0.2 mm layers, 0.42 mm lines, 100% infill, 250°C nozzle/90°C bed, 40 mm/s. Tensile ASTM D638 and SENB ASTM D6068 tests use room-temperature 1 mm/min loading; notches are machined after printing, with razor-formed crack-like defects. Direct full-PDF/figure verification of W029 remains incomplete.

Eight official XLSX files were matched to public MD5 checksums and additionally logged with SHA-256. Of 162 specimen sheets, 18 tensile and 143 SENB had usable observations; one empty sheet was excluded, not zero-filled. The separate diagnostic used mean UTS from matched material/raster tensile groups (n=3) and actual specimen dimensions:

```text
UTS = peak tensile force / tensile specimen area
Znet = B × (W − a)^2 / 6
Fbaseline = 4 × mean(UTS) × Znet / S
```

B is SENB thickness, W width, a notch depth and S the verified 40 mm span. Tensile-sheet a/b dimensions are not SENB a. File labels 30/60 and 45/45 were explicitly normalized to 30/−60 and 45/−45 using the paper. Targets are observed curve maxima, not automatically crack-initiation or final fracture loads.

Group means of specimen-wise predicted/observed ratios were ASA 0.384–0.663 and ASA-CF 0.438–0.685; these are not ratios of group mean loads. This unfitted nominal-stress baseline is a diagnostic of a separate physical assumption, not whole-engine accuracy. It does not solve notch concentration, cracking, plasticity or TCD, reconstruct source G-code/post-machining fixtures, or demonstrate weak-location accuracy. Fitted critical-distance replay must be separated from independent holdouts.

### Manufacturer references and evidence audits

The host's recorded raw XY/Z tensile references, before its 0.85 margin, are:

|Product|XY / Z MPa|Recorded conditions / limits|
|---|---:|---|
|[eSUN ABS](https://www.esun3d.com/abs-product)|42.23 / 16.97|Detailed standard/temperature/post-processing not structured in the reference. Separate from ABS+. Generic ABS is a family-level substitute, not verified spool identity.|
|[eSUN PLA Basic](https://www.esun3d.com/media/esun/catalog/certification/product/PLA-Basic/PLA-Basic-TDS-EN-_2026.6.5.pdf)|64.27 / 32.34|Bambu P1S, 0.4 mm nozzle, 220°C, 65°C bed, 100% infill manufacturer specimen. Generic PLA substitute, not a target-part match certificate.|
|[Bambu PLA Basic](https://c.cdnmp.net/712781591/content/Bambu_PLA_Basic_Technical_Data_Sheet.pdf)|35 / 31|220°C nozzle, 35°C bed, 100% infill, 55°C/8 h annealing/drying. Explicit Basic grade only.|
|[Bambu ABS TDS V3](https://store.bblcdn.com/s7/default/23b4cf2b83d5470bb96d19970b5f3ae8/Bambu_ABS_Technical_Data_Sheet_V3.pdf)|33 / 28|ISO 527 / GB/T 1040; 260°C nozzle, 80°C bed, 200 mm/s, 100% infill, **80°C/12 h annealing/drying**. Not unannealed-part strength.|

This translation does not claim a new complete TDS audit. The 0.85 margin is applied once and is `UNVALIDATED_INTERNAL_MARGIN`, not experimentally calibrated, a statistical lower bound or a certified safety factor. Displaying XY as X and Y does not prove equal actual-part directional strength. The eSUN PETG 34.77/28.65 MPa check was same-manufacturer-source transcription, not independent prediction validation.

The initial bundle contained 200 sources/134 numerical rows (19 numerical sources), with 12 manifest entries checked. Test method was missing in 128 rows, n in 129, SD in 118. At that audit's matching standard, there were zero comparable independent validation rows and two same-source replays. This is not 200 full-text readings or 134 independent labels.

The supplement contained 38 sources/148 rows (14 numerical sources), with seven manifest entries and hash/byte counts, JSONL/CSV fields/order, foreign keys and units checked. Audit classification: 131 submitted direct-report claims, nine derived statistics, six abstract, one conclusion and one model-derived row. n was missing in 121; both SD and CI in 114. All submitted rows lacked structured page/table/figure locators; later checks targeted only selected sources. File integrity does not establish source truth. Duplicate lineage includes W020=S027, W037=S186, W038=S051 and W019 in an earlier follow-up, plus the paper/data pairs above.

Historical V1 identity-factor discrepancies for S050/S088 are old model-expressiveness diagnostics, not current V3 error rates: V2 withdrew those corrections and V3 continues to withhold predictions. Lookup replay, unit conversions, matching hashes and passing regression tests do not substitute for predictive validation.

### Evidence still required

Independent validation needs matched grade/batch, conditioning/annealing, orientation/raster definitions, actual process conditions, test standards/dimensions/area basis, fixtures/load points, raw curves and repeat counts/dispersion. Weak-location validation additionally needs observed fracture locations and real load/restraint labels for the same input shape. Calibration and evaluation conditions must be split in advance, with repeated-specimen checks distinguished from unseen raster/notch/product/laboratory generalization. The current evidence does not establish universal accuracy, prediction intervals or a certified safety factor.
