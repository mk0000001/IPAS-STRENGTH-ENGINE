# 2026-09-30 통합 검증 / Integration validation

## 한국어

이번 검증은 G-code 분석·전력 비용·뷰어·PDF를 함께 사용하는 PrintOps 통합 경로를 대상으로 한다. 강도 엔진의 실측 파단하중 보정이 새로 완료됐다는 의미는 아니다. 형상 취약 후보와 검증되지 않은 하중 시나리오의 구분은 유지한다.

### 엔진과 변경 범위

| 엔진 | 버전 | 이번 변경 |
|---|---|---|
| G-code | 0.25.0 | H2C 선택 베드와 챔버 설정 보존, 압출 중 노즐 명령 온도 구분, RatOS 리터럴 베드 온도 해석 |
| 가격 | 0.8.0 | 프린터·부속장치 합산 계측 범위, 출력 시간 범위에 따른 준비 에너지 중복 방지 |
| 강도 | 0.11.0 | 계산 코드 변경 없음; 연구·검증 문서 한글 우선 정리 |

H2C 입력의 베드 110°C, 챔버 65°C, 압출 노즐 명령 280°C가 분석과 상세 PDF에 보존된다. 이 수치는 명령/프로필 값이며 실제 센서 온도가 아니다. 종료 명령의 0°C는 출력 온도로 채택하지 않는다. RatRig V-Core 4 IDEX 400 Hybrid는 읽기 전용으로 확인한 구성에 따라 400×400×400mm 출력 범위와 두 툴헤드로 등록했다. 주차 이동 범위를 베드 크기로 사용하지 않는다.

### 전력 자료의 적용 조건

확인된 플러그는 프린터와 연결된 건조·급지 장치를 합산 계측한다. 출력 중 건조 전력은 계측 합계에 포함하며 별도 가산하지 않는다. 장비·온도·출력 상태가 확인되는 자료만 사용한다. 각 시간 구간의 처음과 끝에 실제 전력 업데이트가 있어야 하며 unknown/unavailable 및 단순 이전 값 유지 구간을 제외한다. 대량 원시 행 제한으로 유효 이력을 버리던 결함은 날짜별 시간 집계로 수정했다.

준비 에너지는 동일 장비·유사 온도·최근 28일·최소 두 관측 조건을 만족해야 한다. PRINT_ONLY는 준비 에너지를 한 번 더하고, TOTAL_WITH_PREPARATION은 준비 시간을 출력 시간에서 분리한다. 시간 범위가 UNKNOWN이면 실측 준비 값을 참고로만 표시하고 자동 보정을 적용하지 않는다. 새 플러그의 짧은 이력, 순간 최대 전력, 사용자 관찰 범위를 검증된 출력 평균으로 만들지 않는다. 실측이 부족하거나 플러그 매핑이 불확실한 장비는 추정/미확정 상태를 유지한다.

### 성능 측정

동일 H2C 자료의 220개 레이어를 각 경로에서 세 번 실행한 중앙값이다.

| 측정 범위 | 기존 | 개선 | 시간 감소 |
|---|---:|---:|---:|
| 레이어 파일 디코딩 | 1.381004초 | 0.825844초 | 40.20% |
| FastAPI 레이어 응답 생성·ASGI 전달 | 9.051689초 | 3.896992초 | 56.95% |

후자는 파일 읽기와 JSON 직렬화를 포함하며, DB 접근은 양쪽 동일 스텁이다. 152,842,407바이트 응답의 동일성을 확인했다. 파일 캐시를 완전히 통제하지 않았고, 실제 네트워크·브라우저 렌더링·전체 G-code 스캔·강도 연산을 포함하지 않는다. 전체 시스템이 57% 빨라졌다는 결과가 아니다.

### 검증과 자료 공개 범위

공개 엔진 시험은 G-code 29개, 강도 54개, 가격 13개 통과했다. 최종 통합 컨테이너 시험은 190개 통과, Node 부재로 1개 건너뜀이며 해당 브라우저 서식 회귀는 로컬 Node에서 별도 통과했다. 실제 H2C 업로드→분석→뷰어→견적→PDF 경로도 통과했다. PDF는 텍스트 경계 검사뿐 아니라 페이지 렌더링으로 검수하며, 마지막 설명만 별도 페이지에 남던 배치와 빈 마지막 페이지를 수정했다. 원본 G-code·프린터 구성·HA 이력·비공개 요율·인증 자료는 이 공개 문서에 포함하지 않는다.

## English

This review covers the PrintOps integration of G-code analysis, energy pricing, the viewer, and PDF reporting. It does not establish new empirical failure-load calibration for the strength engine. Geometry screening and unvalidated load scenarios remain distinct.

### Versions and scope

- G-code **0.25.0** preserves H2C selected-bed/chamber settings and deposition nozzle commands, and parses literal RatOS bed-temperature parameters.
- Quote **0.8.0** represents combined printer/accessory meters and prevents double-counting preparation energy when duration scope is explicit.
- Strength **0.11.0** has no calculation-code change in this release; research documentation is arranged Korean first, English second.

The H2C fixture preserves 110°C bed, 65°C chamber, and 280°C deposition nozzle commands through analysis and PDF generation. These are commands/profile settings, not measured sensor temperatures; shutdown zero commands are excluded. The RatRig V-Core 4 IDEX 400 Hybrid is registered with a 400×400×400mm print envelope and two toolheads based on read-only configuration inspection, excluding parking travel.

### Energy evidence

Confirmed meters include the printer and attached drying/feeding accessories. Drying consumption during printing is included once. Profiles require matching equipment, temperature conditions and printing state, with actual power updates near both ends of each hourly bucket. Unknown/unavailable and carried-forward states are excluded. Daily hourly aggregation fixes the exclusion of valid histories caused by a raw-row cap.

Preparation-energy application requires the same printer, similar temperatures, at least two observations within 28 days, and an explicit duration scope. PRINT_ONLY adds preparation once; TOTAL_WITH_PREPARATION separates preparation time. UNKNOWN retains observations as reference without empirical preparation adjustment. Short new-meter histories, peak power and user observations are not promoted to calibrated printing means. Insufficient or ambiguous measurements remain estimates or unresolved mappings.

### Performance and validation limits

Three runs across 220 H2C layers yielded median decoding time **1.381004→0.825844s (40.20% less)** and FastAPI file-read/JSON/ASGI response time **9.051689→3.896992s (56.95% less)**. Both routes used the same DB stub; all **152,842,407 response bytes** were identical. OS cache state was not fully controlled. Network transfer, browser rendering, complete scans and strength calculations are outside this measurement.

Public engine tests passed: **29 G-code, 54 strength, 13 quote**. Final container integration tests passed **190**, with **one skipped** because Node was absent; that browser-formatting regression passed separately in local Node. The live H2C upload-to-PDF workflow also passed. PDF review includes rendered pages and text bounds, including correction of orphaned explanations and an empty final page. Raw G-code, printer configuration, HA history, private pricing and credentials are not published.
