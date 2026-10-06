# 층간 접합·파괴·공정 상호작용 근거 재검토 — 2026-10-07

23개 논문 항목과 3개 추가 공개 데이터 후보를 확인했다. 기존 전문·원자료 감사 결과를 재사용하고, 접근 가능한 출판사·NIST·기관 자료로 부족한 내용을 보완했다. 모든 논문을 망라한 체계적 문헌고찰은 아니다. **이 문서는 연구 근거이며 보정계수나 파손 예측의 검증 결과가 아니다.** 엔진 코드·배포·승인된 수치 계수를 변경하지 않았다.

세부 조건, 단위, 표본 수의 범위, 분산, 접근 수준, 출처 계보는 [research-provenance-20261007.json](./research-provenance-20261007.json)에 기록했다. “기존 감사 재사용”은 이번에 원자료 재계산을 반복했다는 뜻이 아니다.

## 지금 고칠 수 있는 가정과 실험이 필요한 주장

| 엔진에서 고칠 수 있는 가정 | 이번 문헌으로 확정할 수 없는 주장 |
|---|---|
| 명령 온도·팬·속도와 측정/추정 계면 열이력을 분리한다. | 대상 프린터·재료의 온도/팬/속도 공통 강도 계수 |
| 실제 형상·단면·접촉면을 구분하고, 중복 flow/infill/wall 보정을 방지한다. | 접촉면 전체가 완전 접합됐다는 가정 |
| 단위·시험 모드·초기/전파 저항·분산 정의·시험 불능 상태를 보존한다. | Mode I/II/III 에너지를 인장 MPa 또는 허용 하중으로 직접 환산 |
| 하중·지지·접촉 위치를 명시하고 root의 수요를 계산한다. | 얇은 끝단 또는 root가 최초 파단 위치라는 일반 법칙 |
| 논문·학위논문·데이터의 동일 계보를 합쳐 중복 검증 수를 줄인다. | 현재 대상 부품의 최초 파단 하중·위치와 안전 하한 |

핵심 공백은 **동일 출력물의 G-code/실제 열이력/결함 관찰/명시된 fixture/하중 곡선/최초 균열 위치를 연결하는 독립 검증 데이터**다. 문헌 쿠폰의 UTS나 균열 저항만으로 이 연결을 대신할 수 없다. 정적 조건부 응력 또는 구조적 취약 후보와 실제 파손 예측을 구분해야 한다.

## 공개 1차 자료 행렬

“재사용”은 기존 전문/원자료 추출 근거를 뜻한다. “새 전문”은 이번에 Methods/표를 추가 확인한 항목이다. 표의 짧은 이름은 검색용이다. JSON의 `title_kind`와 `bibliographic_metadata`로 정식 제목 확인 여부를 구분하며, 메타데이터 조회에 실패한 P07/P14의 설명용 이름을 확인된 정식 제목으로 취급하지 않는다.

| ID · 자료 | 접근/확인 범위 | 적용 모듈 · 수치 전이 제약 |
|---|---|---|
| P01 [Seppala 2017 · ABS 용접](https://pmc.ncbi.nlm.nih.gov/articles/PMC5684701/) | NIST/PMC 전문 새 확인 | 열이력·Mode III; 계면 온도는 주변층에서 추정 |
| P02 [Davis 2017 · 용접부 역학](https://pmc.ncbi.nlm.nih.gov/articles/PMC5726274/) | 기존 전문 감사 재사용 | 실제 weld 폭; P01과 동일 NIST 계보 |
| P03 [Allum 2020 · 실제 접합면](https://repository.lboro.ac.uk/articles/journal_contribution/Interlayer_bonding_has_bulk-material_strength_in_extrusion_additive_manufacturing_New_understanding_of_anisotropy/12443528) | 공개 accepted manuscript 재사용 | 면적 정규화·이방성; 파괴 에너지/부품 성능과 분리 |
| P04 [Moetazedian 2023 · 공정 제어](https://pmc.ncbi.nlm.nih.gov/articles/PMC10280202/) | 기존 전문 감사 재사용 | 단독 공정변수 제어; 완전 factorial 아님 |
| P05 [Lambiase 2024 · 시간×속도](https://d-nb.info/1346221405/34) | 기존 전문 Methods/표 재사용 | 국소 재방문 시간; mm/min 보존 |
| P06 [Lambiase 2023 · raster DCB](https://link.springer.com/article/10.1007/s00170-023-12223-1) | 출판사 전문 새 확인 | Mode I·kissing bond; 초록/결론 수치 충돌 격리 |
| P07 [Lingua 2022 · miniature CT](https://publications.polymtl.ca/51488/) | 기관 초록/데이터 범위 확인 | 균열 경로/DIC; 대표 시편 1개 데이터 |
| P08 [Young 2018 · ABS/CF-ABS](https://doi.org/10.1016/j.addma.2018.02.010) | 출판사/DOI 메타, 기존 근거 | Mode I; .010/.023 DOI 중복/별칭 미해결 |
| P09 [Aliheidari 2017/2018 · ABS DCB](https://rex.libraries.wsu.edu/esploro/outputs/graduate/Characterization-of-interlayer-adhesion-and-fracture/99900525131701842) | 기관 학위논문 근거 재사용 | apparent/실제면적 에너지; 한 계보 |
| P10 [Belei 2022 · PAHT CF15](https://pmc.ncbi.nlm.nih.gov/articles/PMC9002508/) | 기존 전문 수치 재사용 | 온도 효과가 속도에 따라 반대 방향 |
| P11 [Nesheim 2025 · PA6-CF IR](https://doi.org/10.1016/j.addma.2025.104705) | 기관 초록 + 기존 공개 CSV 감사 | peak/area만; 전문 Methods·곡선 부족 |
| P12 [Ørnes 2026 · PA6-CF PDT](https://doi.org/10.1017/pds.2026.10563) | 기존 출판사 전문 재사용 | 외벽 PDT·팬/속도/enclosure 교란 |
| P13 [Liparoti 2021 · PLA bed](https://pmc.ncbi.nlm.nih.gov/articles/PMC7865617/) | 기존 전문 재사용 | 냉각/결정화·쿠폰 UTS; bed 효과 비단조 |
| P14 [Marković 2024 · ABS flow](https://pmc.ncbi.nlm.nih.gov/articles/PMC11669824/) | 기존 전문/표 재사용 | flow 비단조; outer layer는 top/bottom |
| P15 [Cicero 2024 · ASA 노치](https://doi.org/10.3390/ma17215207) | 논문 + 기존 원곡선 감사 | SENB 노치; 동일 자료 재생은 외부 검증 아님 |
| P16 [Cicero 2025 · ASA-CF 노치](https://doi.org/10.3390/jcs9040185) | 출판사 indexed Methods + 원곡선 감사 | CF grade 제한; 전체 PDF/그림 검증 미주장 |
| P17 [Cole 2020 · NIST PC benchmark](https://pmc.ncbi.nlm.nih.gov/articles/PMC10938461/) | 기존 NIST 전문 재사용 | void/raster/실제 파손; 치수 단위 확인 필요 |
| P18 [Elverum 2026 · 실부품 armrest](https://doi.org/10.1017/pds.2026.10548) | 출판사 전문 새 확인 | n=3; fixture/strut/clamp/후파손 buckling 구분 |
| P19 [Thumsorn 2023 · chamber×fan](https://doi.org/10.3390/jmmp7010044) | 메타만; 전문 403/429 | 재료/Methods/n/표 미확인, 수치 반영 불가 |
| P20 [Zheng 2026 · shear fracture](https://doi.org/10.1016/j.polymertesting.2026.109340) | 새 초록/DOI 확인 | 제조 경로의 FFF 해당 여부 미확인, 제외 |
| P21 [Paygozar 2025 · I/II/III](https://onlinelibrary.wiley.com/doi/10.1111/str.70009) | **새 전문·Tables 1–2** | Mode purity/LEFM 한계; 표 SD와 prose 충돌 |
| P22 [Pejak Simunec 2026 · PA12 MWD](https://link.springer.com/article/10.1007/s40964-026-01594-y) | **새 전문·Table 6**, CC BY | grade×온도; flow/speed 교란·큰 SD·정확 n 공백 |
| P23 [Lambiase 2024 · flow×speed×raster](https://link.springer.com/article/10.1007/s00170-024-14079-5) | **새 전문·Table 4**, CC BY | 72 DCB; 시험 불능 zero·prose/table 충돌 격리 |

## 새로 보완한 정량 근거와 품질 문제

[P21](https://onlinelibrary.wiley.com/doi/10.1111/str.70009)의 3개 build 방향·3개 균열 모드, 각 n=5 결과는 **MPa√m**이며 계면 강도 MPa가 아니다. Table 1 SD를 보존했고 “SD<1%” 설명, Table 2 modulus 단위, 길이 단위의 충돌을 표시했다. Mode II/III crack path와 비선형 거동 때문에 세 계면 법칙으로 바로 쓸 수 없다.

[P22](https://link.springer.com/article/10.1007/s40964-026-01594-y)의 4개 PA12 grade/혼합물은 초기 Mode I 저항을 **J/m²**, 평균±SD로 보고한다. 건조·DCB·온도 조건과 grade별 flow/speed를 함께 기록했다. 정확한 DCB cell별 n과 공개 원곡선이 부족하며, 초기 저항을 전파 저항으로 취급하지 않았다.

[P23](https://link.springer.com/article/10.1007/s00170-024-14079-5)의 factorial DCB에서 ±45°, 1000 mm/min, flow 100→104% 평균은 **7.58→2.44 kJ/m²**, sigma **0.04/0.25**, 각 n=4다. 유량 증가가 항상 유리하지 않다. 시험 불능을 뜻하는 표의 zero는 physical zero로 반영하지 않으며, 별도로 설명과 충돌하는 두 cell도 격리했다.

## 추가 공개 데이터 후보

| ID · 공개 자료 | 실제 확인한 범위 | 안전하게 검증할 대상 |
|---|---|---|
| D01 [2026 multi-material tensile](https://zenodo.org/records/21939238), CC BY | supporting ZIP checksum, 35-row XLSX와 notebook; 3.88 GB 원곡선은 미다운로드 | 곡선/단위 parser. “toughness”는 stress–strain 적분이며 GIc가 아니다. stress/strain 단위 미확정 |
| D02 [KU Leuven thermal DoE](https://rdr.kuleuven.be/dataset.xhtml?persistentId=doi:10.48804/B0CMEN), CC BY | README와 256-row CSV; fan 0–100%, speed 20–140 mm/s, h 0.05–0.30 mm, length 10–20 mm | G-code–IR 열맥락/재방문 검증 후보. print fault/success는 기계적 최초 파단 label이 아니다 |
| D03 [VISTA printer lifecycle](https://github.com/VISTA-Laboratory/dataset-FFF-printer-full-lifecycle-vibration-monitoring), CC BY-SA | lab README; 15상태×5 PLA 시편 기술, maintenance/nozzle 변경 | curve parser와 printer-health 교란. grade·원곡선 checksum·최종 journal DOI 미검증 |

기존 [ASA 곡선](https://zenodo.org/records/14065523), [ASA-CF 곡선](https://zenodo.org/records/14882928), [대표 CT 영상](https://publications.polymtl.ca/58993/), [Nesheim numeric CSV](https://data.mendeley.com/datasets/pdfz6y8bmh/1)의 계보를 유지했다. 공개 데이터가 있다는 사실과 해당 엔진의 예측이 검증됐다는 주장은 다르다.

## 다음 단계

1. source–grade–batch–test–property registry에 단위, n의 범위, 분산 정의, 균열 모드, 초기/전파, nominal/실제면적, license/access와 hash를 고정한다.
2. P08/P21/P23의 충돌과 P11의 row/formula 문제를 격리하고, 공개 원자료 checksum·곡선·fixture를 먼저 확인한다.
3. 대상 grade의 thermal history×speed×flow와 chamber×fan 쿠폰 시험을 설계한다. 실제 접합폭·수분·DSC/rheology를 함께 측정한다.
4. 대상 terminal/root 부품의 fixture·force curve·DIC/최초균열을 등록하고 독립 batch/형상 holdout으로 검증한다. 이 단계 전에는 최초 파단 하중·위치, 안전 하한, 공통 공정계수를 주장하지 않는다.

## 최초 파단 검증용 자료·시험 shortlist

공개 자료 중 가장 가까운 실부품 사례는 P18 armrest이지만 n=3이며 대상 grade/프린터로 전이할 수 없다. P07 CT 영상은 crack-path 관찰 절차, P15/P16 노치 곡선은 fixture별 응답, P17 NIST PC는 void/raster benchmark 후보로 쓴다. 모두 목표 부품의 G-code–실제 열이력–최초균열–하중을 완전히 연결하는 holdout은 아니다.

| 시험 | 필요한 실제 관측 · 검증 목적 |
|---|---|
| T01 terminal/root 독립 변화 부품 | 실제 grade·프린터, terminal 두께/root fillet를 독립 변화. 명시된 lever arm·clamp·접촉 조건에서 force/DIC/video 동기화. 최초균열 N·시간·위치·기전을 peak/후파손 peak와 분리 |
| T02 동일 grade Z tensile + DCB/shear | 실제 접합폭·nominal section, 균열 길이·경로·시험 속도. UTS와 모드별 초기/전파 저항을 구분하고 T01 부품 전이 검증 |
| T03 열이력×flow/speed 및 chamber×fan | 국소 return time, 실제 bead 치수/체적, calibrated IR/thermocouple, 건조/수분·결정화. 명령을 입력으로, 파괴 시험을 결과로 기록 |
| T04 독립 batch·형상/공정 holdout | 시편/곡선 내부 random split을 피하고 batch 전체를 분리. 위치 오차·지역 precision/recall·하중 오차·uncertainty/abstention·검열/실패 기전 평가 |

선택 조건별 5개 이상·독립 print batch 2개 이상은 **pilot 제안**이며 통계적 충분성을 입증한 n이 아니다. 실제 분산·효과·시험 불능률과 허용 오차로 본시험 n을 정해야 한다. 상용 성능·안전 하한·특허 가능성은 이 문서의 결과가 아니다. 특허 가능성은 별도의 선행기술·법적 검토가 필요하다.

## English

This review adds 23 primary-paper records and three qualified public-data candidates. It reuses earlier full-text audits where stated and verifies additional publisher, institution and NIST evidence. It is not an exhaustive systematic review and does not calibrate a universal process multiplier or turn G-code commands into measured fracture outcomes.

New full-text checks cover PLA mode I/II/III fracture, grade-specific PA12 molecular-weight/printing-temperature interactions, and a PLA flow×speed×raster DCB matrix. Units, initiation versus propagation, sample-count scope, dispersion definitions, ambiguous DOI identity, and conflicting prose/table cells remain explicit. Uncomputable tests recorded as zero are censored outcomes, not zero fracture energy. Thermal G-code/IR and print-success labels cannot become first-fracture mechanical targets.

The remaining gap is a matched, independently held-out first-fracture dataset for the actual grade, process, geometry and fixture. The proposed program separates terminal/root parts, same-grade Z tensile/DCB/shear coupons, measured thermal/flow interactions, and independent batch/geometry holdouts. Pilot sample counts do not establish adequate statistical power, safe allowable loads, commercial readiness or patentability.
