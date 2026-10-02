# 벽 수·선폭·토출량과 국부 취약부 근거 / Walls, width, extrusion and local weaknesses

연구 확인일: 2026-10-03. 연구 착수 시 PrintOps / print-strength-engine v0.18.0을 기준으로 한 문헌 검토와 **구현 전 감사**다. 이 연구 문서 작성 단계에서는 제품 코드·배포·재질 강도값을 변경하지 않았다. 같은 날 후속 공정 구현이 추가되었으므로 아래 과거 감사표를 현재 기능 목록으로 읽지 않는다. 후속 계산·검증 상태는 [공정 취약부 검증 기록](process-aware-weakness-validation-20261003.md)을 참조한다.

## 한국어

### 판단

실제 G-code 경로의 단면 union은 벽 개수, 벽 위치, 선언된 선폭, 그 단면을 통과하는 내부 채움을 이미 반영한다. 여기에 일반적인 `벽 1개당 강도 증가율` 또는 `infill % 보정계수`를 곱하면 형상 효과가 중복된다. 반면 선언된 폭과 높이는 실제 토출량·공극·용접 품질을 보장하지 않는다. E에서 계산한 **명령 토출 체적**을 국부 경로와 연결하면 이 차이를 점검할 수 있다. 현재 근거로 가능한 결과는 토출량 일관성 지표와 조건부 경고이며, 보편적인 MPa 또는 파단 하중 배수가 아니다.

이 문서는 기존 [research-evidence.md](research-evidence.md), [research-update-20261001.md](research-update-20261001.md), [weakness-research-redesign-20261003.md](weakness-research-redesign-20261003.md)의 자료를 먼저 대조한 추가 조사다. 기존 Grigoriev의 180개 인장 시편, Menargues의 벽 1–5개 최대 하중, Desouky의 결과표 부재, Allum/Moetazedian의 실제 접촉면적, NIST 용접 파괴에너지 연구를 새로운 독립 실험으로 중복 집계하지 않았다. 아래 자료는 확인 가능한 원문·저자 공개 원고·실험 데이터에 한정한다. 모든 출판물 또는 비공개 데이터까지 확보했다는 뜻은 아니다.

### 추가 통제시험

`±`는 원문이 정의한 산포만 사용한다. 그래프의 오차막대를 눈대중으로 숫자화하지 않았다. gross 응력은 공극을 포함한 시편 외형 단면으로 나눈 응력이며, road union 또는 실제 접착 목 면적을 분모로 한 응력과 직접 호환되지 않는다.

| ID / 1차 자료 | 재질·통제조건·표본 | 실제 결과 및 산포 | 응력 분모·교란·적용 경계 |
| --- | --- | --- | --- |
| WF01 Ghorbani et al. 2022, [DOI](https://doi.org/10.1016/j.jmapro.2022.06.026), [저자 공개 전문](https://www.researchgate.net/publication/363002738_Eliminating_voids_and_reducing_mechanical_anisotropy_in_fused_filament_fabrication_parts_by_adjusting_the_filament_extrusion_rate) | 3DXTECH ABS, ROBO R1 Plus, 250/105°C, h 0.2 mm, w 0.48 mm, 노즐 0.4 mm, 50 mm/s, rectilinear 100%, perimeter·top·bottom 0. EM 1/1.1/1.2, X/Z 각 조건 n=7. 인쇄 블록에서 ASTM D638 IV 가공. | EM 1→1.2에서 X 인장 약 +9%, Z 약 +50%. 공극률 4.5→0.35→검출값 0%. EM +10/+20%에 실제 질량은 +9/+14%. 강도별 수치 SD는 미추출. | 가공 시편 gross 응력으로 해석되지만 치수 측정·분모의 완전한 절차는 미확인. 가공이 표면 요철을 제거한다. 체적·열 이력이 함께 변하며 기어 slip 때문에 E와 실제 질량이 비례하지 않는다. 원시 데이터는 당시 비공개. ABS 기작 근거, FusRock 계수 아님. |
| WF02 Marković et al. 2024, [DOI](https://doi.org/10.1089/3dp.2023.0170), [공개 전문](https://pmc.ncbi.nlm.nih.gov/articles/PMC11669824/) | Devil Design ABS·PETG, Zortrax M200/Z-Suite, 노즐 0.4, flat 0°. ABS 235/90°C·h 0.09, PETG 235/80°C·h 0.14. 설정을 하나씩 변경. ISO 527 5A, n=5, 10 mm/min. | ABS 기준 31.1±1.7, EFR +25% 36.4±1.4, +50% 34.4±1.6 MPa. PETG 44.9±3.1, 58.8±17.7, 37.2±7.2 MPa. ±SD. PETG +25% CV=30.1%. | 실제/명목 외형 치수 분모의 상세 미확인. `outer layers`는 **위·아래 솔리드 층** 7/4→10/6이며 perimeter 벽 수가 아니다. 이 조건 ABS 38.1±0.5, PETG 48.3±2.4 MPa. 데이터는 요청 시 제공. 더 큰 flow가 항상 더 강하지 않다. |
| WF03 Pollard et al. 2017, [DOI](https://doi.org/10.1080/20550340.2017.1306337), [출판사 전문 PDF](https://www.tandfonline.com/doi/pdf/10.1080/20550340.2017.1306337) | RapMan 3.2의 ABS 단일벽 Z 인장. 벽 두께 1.5/2/2.5 mm, 체적 유량 4.08/5.44/6.80 mm³/s. 폭을 유지하도록 이동속도 변경. 전체 재질 시험 100개 중 14개 제외, 유효 86개. 조건별 n 미확인. | ABS 평균 UTS 범위 22.1–26.3 MPa. 4.08 mm³/s에서 1.5 mm 24.2±1.3, 2 mm 26.1±2.4 MPa. 폭·유량에 따른 UTS의 유의 차이 없음. ±의 정확한 정의 미확인. | 최대 힘 / 실제 측정 벽 폭×두께. 면적 확대에 따른 하중 변화와 MPa 변화가 다르다. 유량과 이동속도가 결합됐고 가공·게이지 밖 파단 제외가 있다. ABS 등급·노즐 온도·h를 이번 접근에서 완전히 확인하지 못했다. 공개 원시곡선 미확보. |
| WF04 Lendvai et al. 2024/2025, [DOI](https://doi.org/10.1007/s40964-024-00646-5), [공개 전문](https://link.springer.com/article/10.1007/s40964-024-00646-5), [PDF](https://d-nb.info/1336406976/34) | Fillamentum Extrafill Traffic White PLA, Craftbot Plus, 215/60°C, h 0.2, w 0.4, 노즐 0.4, contour 2, 100%·인장 평행 0°. EM .97/.99/1.01/1.03/1.05, 시험별 n=5. 속도 원문은 `60 mm/min`이며 단위 확인 필요. | 인장 51.1 MPa(.97)→57.1(1.03)→56.6(1.05). 공극 5.82→0.05%. 1.01–1.05 인장 차이는 Tukey에서 유의하지 않음. 그림 SD 미추출. | 공극을 포함한 apparent gross 물성. 높은 EM에서 XY 정확도가 악화·표면 응력집중 발생. 인쇄 표면을 보존하여 WF01의 가공 시편과 차이. 부록은 질량 비교·대표 곡선이며 전체 개별 시험 원시곡선 공개를 뜻하지 않는다. PLA의 기작만 적용, ABS 수치 전이 불가. |
| WF05 Szot & Rudnik 2024, [DOI](https://doi.org/10.2478/adms-2024-0006), [출판사 PDF](https://reference-global.com/2/v2/download/article/10.2478/adms-2024-0006.pdf), [저자 전문](https://www.researchgate.net/publication/379032636_Effect_of_the_Number_of_Shells_on_Selected_Mechanical_Properties_of_Parts_Manufactured_by_FDMFFF_Technology) | PLA 등급 미확인, MakerBot Sketch, 220/50°C, 노즐 .4, h .1, linear 95%, XY 0°, 80 mm/s. wall 2/10. ISO 527 1BA, 인장·굽힘 각 조건 n=10. | 인장 30.98±1.91→39.80±0.68 MPa, 굽힘 37.46±2.76→61.02±5.94 MPa, ±SD. Table 5의 개별 인장값으로 sample SD 1.9086/.6829 재현. 평균 기준 증가율 +28.47/+62.89%. | 각 시편 측정 폭×높이 gross 분모. 원문 증가율은 높은 값 분모를 사용하므로 여기와 다름. 높은 벽 수는 내부 raster를 대체하며 95% infill은 무공극을 뜻하지 않는다. 파단 사진은 위치 좌표 정답 데이터가 아니다. 개별 요약값은 공개, 원시 force/time 파일 미확보. ABS 계수 불가. |
| WF06 Kowalska et al. 2024, [DOI](https://doi.org/10.14314/polimery.2024.3.6), [저자 전문](https://www.researchgate.net/publication/380122683_Effect_of_shells_number_and_machining_on_selected_properties_of_3D-printed_PLA_samples) | MakerBot PLA·Sketch, 220/50°C, linear infill, wall 1–5, w .4. 원문 nozzle .2 mm. h·infill %·출력속도·n 미확인. ISO 527 1BA, 2 mm/min, 폭5×두께4 mm, 개별 치수 측정. | wall 4 최대 29.3±.5, wall 5 26.7±.5 MPa. wall 3 가공 전26.3±.5→후23.9±1.0 MPa. ±는 SD로 해석되는 문맥이나 표에서 정의 불완전. | gross 외형 응력. 벽 증가에 단조 증가하지 않는다. 가공은 외벽을 제거하여 다른 물리조건이다. WF05와 같은 기관 연구로 완전히 독립된 연구실 검증 아님. 방법 누락 때문에 정량 보정 후보에서 제외. |
| WF07 Ćwikła et al. 2017, [DOI](https://doi.org/10.1088/1757-899X/227/1/012033), [기관 기록](https://research.polsl.pl/en/publications/the-influence-of-printing-parameters-on-selected-mechanical-prope/), [저자 전문](https://www.researchgate.net/publication/318922708_The_influence_of_printing_parameters_on_selected_mechanical_properties_of_FDMFFF_3D-printed_parts) | ABS 등급 미확인, modified P3Steel Prusa i3, 240/100°C, 노즐 .4. 그룹당 n=5, 12그룹, 10 mm/min. wall 2·위아래 솔리드 2·honeycomb 40% 고정에서 EM .5/.75/1 비교. | 낮은 EM에서 연결되지 않은 road와 부분 접촉을 관찰. 그룹별 강도·수치 산포는 그래프에서 미추출. | wall 1/2/4/7 비교는 **위아래 솔리드 층도 함께 변경**해 wall 단독 효과 아님. 응력 분모 절차·h·정확한 출력속도 미확인. 매우 낮은 command volume의 결함 기작 근거이며 보편적 임계 flow 근거는 아니다. 원시 데이터 미확보. |

WF03 PDF는 이번 도구의 직접 열기가 제한됐으나 출판사 공개 전문 검색 인덱스에서 시험 방법·Table 1을 확인했다. 나머지 저자 공개본도 논문 자체의 전문으로 사용했으며 주변 추천 논문의 설명은 근거에 포함하지 않았다. WF06의 0.2 mm 노즐과 WF04의 속도 단위를 관행에 맞춰 임의 수정하지 않았다.

### 공개 데이터 감사: Aktepe & Ergün 2026

[Mendeley 원자료 v1](https://data.mendeley.com/datasets/zd6td6svd6/1), [데이터 DOI](https://doi.org/10.17632/zd6td6svd6.1), [연결 논문 DOI](https://doi.org/10.3390/mi17070859), [공개 전문](https://pmc.ncbi.nlm.nih.gov/articles/PMC13413762/)를 함께 확인했다. 이 자료는 흔히 유통되는 50행 Kaggle 자료와 행 수·열 구성이 다르다. 그러나 저장소 등록 자체가 실험 신뢰성이나 전이 가능성을 증명하지 않는다.

확보한 `3d printing parametres dataset.xlsx`는 60,765 bytes이며 SHA-256은 `fc85cbbe019090c55740d86e8bb451159443fa68100cd0a7c99dbdd75330a591`로 공개 파일 메타데이터와 일치했다. 15열·500행의 조건 평균이며 원문은 조건당 3개, 총 1,500개 실물 출력·시험을 보고한다. **500개 개별 시편 원자료가 아니다.** 500개의 명목 입력 조합 중 중복은 없었다. 재질은 PLA+240, PETG92, ABS27, PLA-CF27, TPU27, PLA phosphorus27, PLA-transparent24, PLA18, PP9, rPET9개 조건이다. 개별 반복값·조건별 SD·원시 시험곡선은 이 XLSX에 없다.

ABS는 Creality K1 폐쇄형·250/100°C, h .1/.2/.3 mm, infill20/50/80%, Grid/Triangles/Zigzag, 30/50/70 mm/s이다. 인장 시험속도는 TPU50, 나머지5 mm/min이다. 저자는 전체 조건에서 인장 peak stress 평균 CV 2.89%를 보고하지만 ABS별·조건별 산포를 대신하지 않는다. 브랜드·벽 수·선폭·flow·raster 방향이 없어 FusRock 및 외/내벽 flow 보정용으로 쓸 수 없다. ABS 조건 평균 peak stress는 24.9628–35.2737 MPa이지만 여러 인자가 함께 변하므로 density-only 효과로 읽지 않는다.

단위 감사에서는 `peak stress(kPa) / [1000 × peak load(N)/(width×thickness, mm²)]`를 계산했다. 497/500행은 1% 이내였고 최대 비율은 TPU sample255의 1.1958이다. 개별 응력을 먼저 평균했을 때 비율의 평균과 평균의 비율이 달라질 수 있어 곧바로 오류라고 단정하지 않는다. 개별 반복과 치수·분모를 확인해야 한다. 원문은 catastrophic 실패·sensor 이상값 제거 및 IQR outlier 필터링 후 평균한다고 명시한다. n=3은 계획/보고된 출력 수이며 필터링 후 각 조건의 유효 n은 XLSX에서 확인할 수 없다. 따라서 이 평균 자료로 **불완전 출력·결함 발생 확률**을 학습하면 실제 실패가 누락된다. 기록된 최상의 ML R²는 내부 교차검증 성적이며 새 재질·기계·부품 검증을 대체하지 않는다.

자료 감사의 재현 정보는 [process-walls-flow-data-audit-20261003.json](process-walls-flow-data-audit-20261003.json)에 기록했다. 원시값을 새 가상 시편으로 늘리거나 누락 SD를 생성하지 않았다. 보완해 얻어야 하는 것은 개별 1,500개 기록, 제외된 실패와 사유, 실제 파단 단면 및 fixture/방향, G-code·벽·선폭·flow, 공급업체/lot 정보다.

### FusRock ABS 적용 범위

FusRock의 [공식 ABS 페이지](https://www.fusrock.com/material/performance/id/106/lang/en)는 100%·±45°·노즐 .4 mm·250/100°C·50 mm/s 조건을 제시하지만 n, h, 벽, flow, 응력 분모가 없다. 현재 페이지에는 XY yield `2.32±0.02 MPa`, XY break `33.36±0.53 MPa`, Z tensile `55 MPa`와 XY 약40 MPa라는 설명이 함께 있어 수치·항목의 일관성을 추가 확인해야 한다. 값을 추정 수정하거나 제품의 기존 수치에 덮어쓰지 않는다. 이 TDS에서 wall/flow 반응곡선 또는 국부 취약부 정답은 얻지 못했다.

공개 접근 범위에서 동일한 FusRock ABS lot의 외벽/내벽 유량을 각각 바꾸고 n·산포·실제 단면·파단 위치까지 기록한 통제 데이터를 찾지 못했다. WF01/02/03/07의 ABS 실험은 가능한 기작과 비단조성을 뒷받침하며 FusRock의 강도 배수를 확정하지 않는다. PLA/PETG 결과는 과토출의 표면·공극·산포 문제를 검토하는 데 적용한다. PA-CF는 등급·건조·온도·장비 차이가 크므로 이 조사에서 새 wall/flow 수치를 ABS로 전이하지 않았다.

### 구현 전 감사: v0.18.0에서 중복되는 것과 비어 있던 것

2026-10-03 연구 착수 당시 checkout을 읽어 확인한 관찰이다. 파일과 줄 번호도 **후속 공정 구현 이전**을 가리킨다. 논문 실험 결과 및 현재 기능과 구분한다.

| 구현 위치 | 확인한 사실 | 연구 설계에 주는 의미 |
| --- | --- | --- |
| `print_strength_engine/automatic_sections.py:117,174–202` | `segment(start,end,width,height,tool)`로 road를 받는다. 선언된 직사각 road envelope를 잘라 `union_all` 후 면적·관성·단면계수를 계산한다. 동일 영역의 중첩은 한 번만 센다. | 실제 모델 벽 경로 및 내부 채움이 모두 포함되므로 wall count·infill density 형상 배수는 불필요하다. 선언형상이며 실제 공극·압출 품질은 미반영. |
| `print_strength_engine/interlayer_contact.py:182,232–244` | 같은 선언 road footprint의 층별 union·인접 층 교집합. | 기하학적 겹침을 실제 neck 면적·접착 강도로 읽지 않는다. seam·박리·thermal welding은 추가 검증 필요. |
| `print_strength_engine/process.py:64–75` | flow·per-tool flow·walls·infill 설정을 context로 보존한다. | 설정 context는 유용하지만 자체적인 강도 배수 근거가 되지 않는다. 대표 outer-wall 폭이 개별 road 폭을 대체하면 안 된다. |
| 당시 호스트 `3D-Print-System/app/automatic_capacity.py:212–220` | motion callback에 `deposited` E 회복 후 양이 왔지만 국부 단면 호출에는 width/height/tool만 전달했다. | 당시 E를 region·layer·feature와 연결하는 정보 경로가 비어 있었다. 전역 평균으로 국부 이상을 추정하지 않는 설계가 필요했다. |
| 당시 호스트 `external/print-gcode-engine/print_gcode_engine/scanner.py:199–283`, `process.py:55–69` | M82/M83·G92·단위·툴·retraction recovery 처리 후 체적을 계산했다. 전역 유량은 명령 feed 기반이었으며 **당시에는 M200/M221 상태 처리가 없었다.** | volumetric E·runtime flow 상태의 구분이 후속 과제였다. 명령 기반 계산은 가속·실제 motor/slip 반영 값이 아니다. |

후속 구현은 M200/M220/M221 상태를 처리하고 원본 모션의 공정 정보를 국부 창에 연결한다. 선언 직사각 경로 union과 `Vcmd/(L×h)`로 정의한 등가 직사각 경로 union을 별도 조건부 시나리오로 계산하며 등가 폭은 선언 폭을 넘지 않는다. 축방향과 굽힘 각각 낮은 참고값을 선택한다. **실측 비드 형상·실제 접합 면적·안전 하한 또는 파단 예측으로 검증된 것은 아니다.** 곡선·비평면 이동이나 불명 체적·치수는 추가 체적 시나리오를 보류한다. 역할별 체적은 창과 층높이가 교차하는 경로 중심선 길이로 배분한 명령량이며, 높이가 일부만 교차해도 정확한 3D 창 내부 체적으로 읽지 않는다.

자동 단면의 scope는 `LOCAL_DECLARED_ROAD_REGION`이다. 이 범위가 충분한지, 연결된 하중 경로인지, 얇은 끝·root가 후보에 포함되는지는 별도의 취약부 탐색 문제다. 모델 전체 경로가 포함돼도 자동 선택한 지역 밖 결함을 찾았다고 할 수 없다. WF05/06의 fracture 사진과 WF01의 불규칙 공극은 정성적 위치 근거이며, 복잡 부품의 균일한 좌표 기반 정답 세트가 아니다.

### 외벽·내벽 토출량을 반영하는 제한된 설계

아래는 연구 당시의 설계 권고다. 슬라이서 관례별 비율 `r`과 nominal 유량 `Q` 제안까지 모두 구현되었다는 뜻은 아니다. 후속 구현의 채택 범위는 위 검증 기록과 구분한다.

1. **형상과 토출 진단을 분리한다.** 각 후보에서 outer/inner wall, infill, top/bottom solid, bridge의 경로 길이·선폭·명령 체적을 따로 기록한다. 실제 G-code에 feature 의미가 없으면 role을 추측 확정하지 않는다. 이미 union에 들어간 wall/infill 면적에 일반 배수를 추가하지 않는다.
2. **E 의미를 먼저 확인한다.** 단위를 정규화하고 명시적 리트랙션 회복분을 제외한 `ΔEdeposit`에 대해, 일반 길이형 E의 기본 체적은 `Vbase = ΔEdeposit × π dtool²/4` mm³이다. M200 체적 모드에서는 `Vbase = ΔEdeposit` mm³이므로 필라멘트 면적을 다시 곱하지 않는다. 알려진 통상 M221 상태를 반영한 명령 체적은 `Vcmd = Vbase × flow_override_percent/100`이며 runtime override는 한 번만 적용한다. M82/M83, G92, G20/G21, T, 회복된 retraction, arc 실제 경로길이, prime/purge·0길이 토출을 구분해야 한다. [Marlin M200](https://marlinfw.org/docs/gcode/M200.html) 및 [M221](https://marlinfw.org/docs/gcode/M221.html)의 통상 명령 의미를 사용하더라도 실제 firmware 실행·질량을 실측한 것은 아니다. 알 수 없는 유량 override·회복 상태는 명령 체적을 unavailable로 둔다.
3. **슬라이서의 체적 단면과 비교한다.** 정상 Orca road는 `Aslicer = h(w−h)+πh²/4`, bridge는 `πw²/4`인 rounded bead 모형을 쓴다. [Orca Flow.cpp](https://github.com/OrcaSlicer/OrcaSlicer/blob/main/src/libslic3r/Flow.cpp), 현재 로컬 Orca `Flow.cpp:218–225`도 확인했다. 현 단면의 직사각 `w×h`와 다른 목적이다. w=.4,h=.2이면 rounded .071416 vs rectangle .08 mm²이며 완전한 정상 E도 rectangle 대비 **0.8927**이다. 단순 `V/(Lwh)<.9` 규칙은 정상 G-code를 과소토출로 오인할 수 있다. 다른 슬라이서·특수 road는 해당 체적 관례를 확인해야 한다.
4. **명령 일관성과 nominal 유량을 계산한다.** 같은 tool·role·폭/높이 조건의 국부 window에서 `r = ΣVcmd / Σ(L×Aslicer)`, `qcmd=Vcmd/L` mm², `Qcmd=Vcmd/(L/vcommand)` mm³/s를 기록한다. 분모는 중첩을 제거한 union 체적이 아니라 **각 이동이 계획한 road 체적의 합**이다. 재방문/겹침을 union 체적과 비교하면 정상 명령도 과토출로 오인할 수 있다. 이 r은 void fraction, 실제 접촉 면적, defect probability가 아니다. Q는 가속·센서 측정 전의 명령 기반 값이다.
5. **설정 배수를 E에 다시 곱하지 않는다.** [Orca 재질 flow](https://github.com/OrcaSlicer/OrcaSlicer/wiki/material_flow_ratio_and_pressure_advance), [외/내벽·표면 flow](https://github.com/OrcaSlicer/OrcaSlicer/wiki/quality_settings_wall_and_surfaces), [bridge flow](https://github.com/OrcaSlicer/OrcaSlicer/wiki/quality_settings_bridging)는 이미 G-code E 생성에 반영될 수 있다. 재질·역할·object 설정의 의도와 관측 명령을 병렬 보존한다. 공급업체 TDS, 실제 질량 또는 flow 실험 보정까지 같은 효과를 여러 번 적용하지 않는다.
6. **정량 강도 변환은 보류한다.** 동일 role의 갑작스러운 토출량 변화, 설정과 명령의 불일치, 신뢰할 수 있는 해당 장비/등급의 처리 한도를 넘는 nominal 유량은 확인 대상이 될 수 있다. 임의의 전 재질 threshold나 flow→MPa 곡선을 만들지 않는다. 안정된 r도 막힘·slip·습기·낮은 용접 온도·표면 결함을 배제하지 못한다. WF01의 명령 대비 질량 차이와 WF02/04의 과토출 결과가 이 제한을 직접 지지한다.

명령 체적 등가 직사각 시나리오 및 향후 실측 보정 모델에서는 폭·접촉·공극 변화 중 어디에 그 효과를 적용했는지 하나의 회계로 추적해야 한다. **E로 면적을 감소시킨 뒤 같은 부족량의 강도 penalty를 다시 곱하지 않는다.** 선언된 형상은 별도 시나리오로 보존하며 제안한 r은 독립적 불확실성 표시로 구분한다. 어느 방식도 실제 측정 road/neck와 하중 시험 없는 물성 보정을 정당화하지 않는다.

### 필요한 검증 데이터와 채택 수준

| 제안 | 지금 가능한 수준 | 아직 필요한 데이터 |
| --- | --- | --- |
| wall count·infill %·pattern context와 실제 국부 road 구조 함께 표시 | 기존 G-code·union 근거로 설명 가능 | 높은 벽 수로 바뀌는 raster 방향·연속성과 실제 failure mode |
| 외/내벽별 E 명령 체적·r·Q 진단 | 파서 상태와 슬라이서 체적 관례가 검증된 파일에 제한 | firmware override, actual mass/flow, 이상 위치와 실제 결함의 대조 |
| 두께·root·seam·낮은 층 겹침의 국부 탐색 | 기하학 후보와 독립 지표로 가능 | load/support 조건, true positive/negative 부품의 파단 좌표 |
| FusRock ABS wall/flow에 따른 MPa·N 보정 | 이번 근거로 채택 불가 | 같은 lot·건조·조건·장비에서 wall/width/외·내벽 flow 각각 통제, n·SD·원시곡선·실제 면적 |
| 서로 다른 재질의 회귀 또는 ML 보편 보정 | 이번 근거로 채택 불가 | grade·printer·geometry를 통째로 제외한 외부 검증, 실패가 포함된 데이터 |

우선 실험은 FusRock ABS 동일 lot·동일 방향·온도·h·노즐·속도에서 wall 1/2/4, 선폭, outer/inner flow를 구분하고, 같은 외형의 대조군을 둔다. 계획된 반복 수와 제외 기준을 먼저 정한 후 질량·실측 치수·CT/절단면·실제 neck, 원시 force/displacement, 파단 위치/모드를 함께 저장한다. 작은 균일 시편과 실제 root/neck 부품을 분리해 검증한다. 현재 문헌의 n=5/7/10을 특정 정확도에 충분하다는 보장으로 쓰지 않는다. 반복시편을 무작위로 train/test에 나누는 대신 새로운 부품·grade·장비를 holdout한다.

## English

### Findings and scope

This research began against v0.18.0 on 2026-10-03. Its Korean implementation audit and historical line references describe the **pre-implementation state**, not the later process features. The research-document stage did not change product code or material strengths. See the [process-aware validation record](process-aware-weakness-validation-20261003.md) for subsequent implementation and verification.

The existing local road union already includes the number, placement and declared width of model walls and infill crossing each section. A generic wall-count or infill-density strength multiplier would count this geometry twice. Declared geometry does not establish deposited mass, pores or weld quality. E-derived **commanded** volume can add local consistency evidence without being converted into a universal strength multiplier.

The Korean evidence matrix records the full conditions, n, scatter, area convention and missing information for seven additional primary studies. It distinguishes machined 3DXTECH ABS specimens (WF01), Devil Design ABS/PETG flow trials (WF02), thick single-wall ABS tests (WF03), controlled PLA extrusion trials (WF04), PLA shell trials with reproducible specimen summaries (WF05), a nonmonotonic PLA shell series with incomplete methods (WF06), and ABS under-extrusion microscopy (WF07). These are separate experiments, not universal coefficients. WF05 and WF06 share an institution. Previously reviewed infill, maximum-load and actual-contact-area studies are referenced, not counted again.

The studies show both improvement and saturation/reversal as flow or shell count rises. Fixed material and temperature setpoints do not hold thermal history, actual width, surface shape and void distribution constant. WF02's “outer layers” means top/bottom solid layers, not perimeter walls. WF03 jointly changes speed and flow to hold width. WF07 jointly changes perimeter and top/bottom counts in its shell series. Unknown n, error-bar definitions and stress denominators remain unknown. Gross apparent stress, net road stress, actual bonded-neck stress and maximum load are different labels.

The live FusRock ABS page does not contain a controlled wall/flow series or local failure labels, and several tensile fields require provenance confirmation. Its values were not repaired or used to recalibrate the product. PLA/PETG results support examination of pore closure, surface defects and scatter; their numerical strength factors do not transfer to FusRock ABS or PA-CF.

### Open-data qualification

The Mendeley workbook and associated experimental paper were examined together. It contains 500 configuration averages with 15 columns, including 27 ABS configurations, and is not the common 50-row Kaggle table. The publication reports three physical replicas per configuration; the workbook omits the individual replicate values, per-configuration scatter and raw curves. Its recorded stress approximately matches gross width×thickness in most rows, with a notable unresolved discrepancy in one TPU average. Averaging ratios can explain some mismatch, so specimen-level records are required before declaring an error.

The publication removes catastrophic failures, sensor anomalies and IQR outliers before averaging. This creates a specific selection problem for learning defect or failure probability. The available table can support bounded analysis within its infill/height/speed/material domain. It lacks supplier grade, walls, flow, raster direction and local fracture coordinates, and cannot calibrate wall/flow response or FusRock. The accompanying audit JSON preserves the actual file hash, row meaning, counts and unresolved checks. It does not invent specimen records or scatter.

### Bounded modeling recommendation

The subsequent implementation supports M200/M220/M221 and connects source-motion context to local windows. Declared-road unions and capped `Vcmd/(L×h)` equivalent-rectangle unions remain separate conditional scenarios; axial and bending modes independently select the lower reference. This is not measured bead/bond geometry, a validated failure prediction or a guaranteed safety bound. Curves, nonplanar moves and unresolved volume/dimensions withhold the added volume scenario. Local role volumes use clipped-centerline command allocation and are not measured volume inside a 3D window, including where only part of the declared height intersects it.

The following recommendations include proposed slicer-compatible r and nominal Q diagnostics, not a claim that every item has shipped. Keep declared geometry and commanded-extrusion evidence distinct. Retain local tool and feature role, including outer wall, inner wall, infill, solid surfaces and bridges when identified by source G-code; use source motions rather than a global mean for local regions.

With normalized units and explicit retraction recovery excluded, length-mode E gives `Vbase=ΔEdeposit×πdtool²/4`; volumetric E gives `Vbase=ΔEdeposit` in mm³. A known conventional runtime M221 state gives `Vcmd=Vbase×flow_override_percent/100`, applied once. Validate absolute/relative E, G92, tool changes, recovery, arc length, purge and zero-length prime moves. Unresolved runtime flow overrides or recovery state leave commanded volume unavailable. Conventional command semantics are not measured firmware execution or mass. Slicer material and feature flow modifiers may already be present in E and must not be reapplied.

Compare each move's volume with its slicer-compatible bead cross-section. Orca's rounded normal-road and circular bridge conventions differ from the rectangular envelope used for section union. Accumulate expected move volumes, not deduplicated union volume. A normal .4×.2 mm rounded road has only .8927 of the rectangle's area, making a naive universal .9 threshold unreliable. Report local ratio r, volume per path length and commanded nominal volumetric rate as diagnostics, with provenance. These values are not actual void fraction, weld quality or defect probability.

Preserve source outcomes as experimental evidence. Do not assign a flow-to-MPa curve, universal optimum flow, wall-count bonus, or class-wide FusRock transfer factor. If a future calibrated model modifies width from E, track that effect once; do not then multiply strength by a second penalty for the same volume deficit. A stable E signal cannot rule out clogging, slipping, moisture, welding deficiencies or surface defects.

A future FusRock experiment should independently control shell count, width and outer/inner-wall extrusion, use matched geometry and material lot, retain excluded failures, and measure mass, actual dimensions/neck area, raw mechanical curves and fracture coordinates. Validate uniform coupons and real root/neck parts separately, holding out complete grades, machines and geometries. Current primary papers justify parameter-aware screening and uncertainty labels; they do not establish a product-wide quantitative calibration.
