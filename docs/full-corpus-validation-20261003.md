# 전체 G-code 자료 검증 및 회귀 반영

## 한국어

검증 상태: **FULL_CURRENT_CORPUS — 전체 소프트웨어 검증 및 독립 원본 대조 완료.** 누락 0건, 실행·대조 오류 0건. 이 결과는 실제 부품의 파단 정확도 실증을 뜻하지 않는다.

사용자가 제공한 기존 두 폴더, Q1/Q2 묶음, 추가 G-code 폴더와 A1 SD 카드 백업의 실행 가능한 자료를 같은 소프트웨어 검증 집합에 포함했다. G-code에는 실제 파단하중이나 시험 고정 조건이 없으므로, 여기서의 학습 반영은 파서·제품 매칭·공정 정보·형상 계산의 오류 발견과 재현 시험 추가를 뜻한다. 실제 부품 강도의 지도학습이나 검증된 파단 정확도 향상을 주장하지 않는다.

### 자료 범위와 중복 처리

| 항목 | 수량 | 의미 |
|---|---:|---|
| 실행 가능한 G-code/3MF 원본 발생 건수 | 1,682 | 서로 다른 폴더·압축 경로의 별칭을 보존 |
| 내부 G-code 플레이트 발생 건수 | 1,693 | 여러 플레이트가 있는 3MF의 모든 실행 플레이트 포함 |
| 고유 원본 SHA-256 | 1,662 | 바이트가 같은 원본을 구분해서 집계 |
| 고유 G-code SHA-256 | 1,615 | 다른 3MF 설정 문맥에서 같은 실행 내용이 나올 수 있음 |
| 실행 문맥별 원본 캐시 키 | 1,675 | 동일 바이트와 동일 외부 압축 문맥만 재사용 |
| 실행 문맥별 플레이트 캐시 키 | 1,686 | 1,693건의 별칭을 그대로 보존하며 같은 계산만 공유 |
| STL 형상 점검 | 7 | 추가 폴더 6개, 기존 폴더의 1개. 출력 설정·소재·하중은 추정하지 않음 |
| 실행 내용이 없는 추가 3MF | 3 | 빈 파일 2개, 모델만 있는 파일 1개. 실행 플레이트로 처리하지 않음 |

A1 백업은 실행 가능한 자료 610건과 플레이트 619건을 추가했다. 원본 압축 파일은 변경하지 않았고, 필요한 멤버만 제한된 로컬 스냅샷으로 복사했다. 원본 압축 SHA-256, 멤버 위치·CRC·크기, 스냅샷 SHA-256과 실제 G-code 전체 소비 바이트를 연결해서 검증한다. 원본 폴더·파일 이름·G-code·개인 운영 자료는 공개 저장소에 올리지 않는다.

확장 목록 SHA-256: `b01068e705f2eca6efc52762e8c1bf204b0e2b797c7affeabaa2a10c79939b86`.

### 확인된 오류와 반영

1. **제품 이름에 붙은 출력 설정과 기종 구분.** `Bambu PLA Basic_Q2`와 FusRock의 온도·속도 설정이 제품을 가리는 사례를 회귀 규칙에 추가했다. 설정 접미사를 제거한 결과가 실제 카탈로그 제품과 정확히 일치할 때만 연결한다. `ABS-HF`, `ABS-GF`, `PA6-CF` 같은 제품 등급을 일반 제품으로 바꾸지 않는다. 소재가 빠지거나 설정이 충돌하는 프로파일은 확인 대상으로 남긴다.
2. **공식 강도 지표의 의미 보존.** FusRock 제품 페이지의 `Tensile Break Strength XY`와 `Tensile Strength Z`를 같은 파단 지표로 표시하던 오류를 수정했다. [공식 ABS 제품 자료](https://www.fusrock.com/material/performance/id/106/lang/en)의 원자료 숫자는 유지하고, 비교표와 제품 페이지의 Z 지표 명칭 충돌을 별도로 표시한다. 최약 방향은 확정하지 않는다. 제조사 소재 원자료에는 보정계수를 곱하지 않으며, 내부 여유계수는 조건부 하중 참고 계산에만 한 번 적용한다.
3. **층간 접촉률의 수치 경계.** 실제 자료 두 건에서 완전 겹침의 계산 결과가 `1.0000000000000002`가 되어 정상 접촉 기하가 미확인으로 분류됐다. 발생한 면적 차이는 약 `3.55e-15 mm²`였다. 면적 규모의 제한된 부동소수점 오차만 정규화하고, 상한을 크게 벗어나는 값은 계속 보류한다. 시험 기준을 완화하지 않고 생산 계산과 캐시 검증을 수정한다. 접촉률 100%는 용융 접합이나 층간 파단강도의 실측을 뜻하지 않는다.
4. **대량 검증의 실행 상태.** 한글·중국어 이름을 Windows 기본 출력 인코딩으로 기록할 때 발생한 진행 출력 오류를 분리했다. 모든 후속 실행은 UTF-8을 사용한다. 원본 읽기 완료와 최종 취약부 계산 완료를 별개로 대조하며, 이전 실행 환경에서 겹친 분배를 전체 완료로 계산하지 않는다.
5. **얇은 압출층의 선언 높이.** 실제 자료에서 `0.0045 mm` 이상인 양의 선언 높이를 일괄 `0.02 mm` 미만이라는 이유로 버려 전체 모델 단면을 보류하던 오류를 수정했다. 높이의 수치 허용 하한을 `0.001 mm`로 분리하고 폭의 하한은 `0.02 mm`로 유지한다. 0·음수·비유한값과 범위를 벗어나는 값은 계속 제외한다. 매우 얇은 다림질 경로도 선언된 높이로 계산하며, 이를 측정된 비드 두께나 충분한 층간 접합으로 해석하지 않는다.
6. **Cura 역할과 형상 캐시.** Cura의 정확한 `WALL-OUTER`·`WALL-INNER`·`FILL`·`SKIN` 표기를 외벽·내벽·인필·표면 경로에 연결하고, `PRIME-TOWER`를 모델 단면에서 제외한다. 역할은 [Cura 공식 G-code reader](https://github.com/Ultimaker/Cura/blob/main/plugins/GCodeReader/FlavorParser.py)의 명칭과 대조했다. 기존 형상 캐시가 수정 전 결과를 반환하지 않도록 형상 형식 버전을 2로 변경했으며 이전 캐시는 새 작업으로 대체한다. 공정 요약은 V2, 자동 하중 요약은 V5로 변경했다. 웹은 V2와 과거 V1 공정 요약을 구분해서 표시한다.

전체 계산이 정상 종료한 뒤, 과거 선언 높이 문제를 보였던 실제 자료 65건을 최신 결과와 다시 연결했다. 65건 모두 원본·선택 G-code 해시와 전체 바이트가 유지되고 원본 증착 경로의 기하 추출이 완료됐으며, `INVALID_ROAD_DIMENSIONS`는 0건이다. 일부 국부 단면·접촉 평가는 여전히 별도 근거 부족으로 보류되므로, 원본 추출 완료를 모든 하중 산출 완료로 해석하지 않는다. 별도의 엄격한 공정 문맥 재현 12건은 이 65건 안에 포함되므로 합산하지 않는다. 접촉 경계 2건과 Cura 외벽 재현 1건도 서로 겹칠 수 있는 별도 수정 근거이며, 층간 접합강도 실측이나 전체 강도 정확도 표본 수로 세지 않는다.

전체 자료의 기본 스캔 재사용은 별도 의미 동등성 검증을 통과한 RAW 결과만 허용했다. 모든 1,693개 플레이트의 선택된 G-code `25,108,835,104`바이트를 끝까지 읽어 해시를 확인했다. 이번 기본 스캔에서 동작이 달라진 `PRIME-TOWER` 표기는 이 자료에 없었다. 높이 계산 변경은 기본 RAW 스캔의 비활성 문맥 분기에만 존재한다는 코드 대조와 Python·네이티브 양쪽의 실행 대조를 수행했다. 소재 연결·공정 문맥·취약부·단면 결과는 이전 버전에서 가져오지 않고 새 버전으로 다시 계산한다.

### 검증 조건과 하중 해석

검증은 로컬 격리 경로에서 수행한다. 원본 파일과 운영 DB는 학습용으로 변경하지 않는다. 원본 명령과 확인 가능한 인필·패턴·벽·온도·속도·유량 정보를 유지하고, 지지 구조를 모델 단면에 더하지 않는 규칙과 함께 검사한다. 선언된 경로 폭·높이에 기반한 합집합 단면은 실제 비드·공극률의 계측값이 아니다.

자동 축하중 참고값은 `응력 × 유효 단면적`, 굽힘 참고값은 `응력 × 단면계수 / 거리`를 사용한다. 표시한 10/25/50 mm 거리는 비교 시나리오다. 실제 고정점·가력점, 응력 집중, 박리, 충격·피로와 용융 접합강도까지 실증한 허용하중이 아니다. 누락된 공정 조건, 미확인 복수 소재 연결, 지원하지 않는 비평면 증착과 불완전한 형상은 이유와 함께 보류한다.

기존 시편 자료와 공정 보정 승인을 다시 점검했다. 현재 적용 승인된 공정 전이 모델은 0개다. 사용자 파일에 숫자 파단 정답을 만들어 넣거나, 문헌의 서로 다른 소재·시험 조건을 임의 계수로 합치지 않는다. 사용자의 끝부분 층 분리·쉬운 파손 관찰은 위치 검토 근거로 보존하며, 측정된 뉴턴 값으로 취급하지 않는다.

### 재현 자료와 최종 대조

세 병렬 작업군이 모두 제한 없는 최신 실행 환경에서 정상 종료했다. 별도의 한 에이전트가 원본 무결성, 모든 플레이트와 별칭, 실제 네이티브 실행 환경, 캐시·원본의 종료 시점 변경 여부, 실패 이력과 수정된 경계 사례를 독립 대조했다. 최종 판정은 `FULL_CURRENT_CORPUS`이며 누락·오류는 모두 0건이다. 공개 회귀 fixture는 필요한 최소 설정·불변식·출처만 포함하며 사용자 형상이나 원본 경로를 공개하지 않는다.

| 최종 대조 항목 | 결과 |
|---|---:|
| 원본 발생 건수 및 기본 스캔 | 1,682 / 1,682 통과 |
| 플레이트 메타데이터 | 1,693 / 1,693 완료: 통과 505, 정보 보류 포함 1,188 |
| 플레이트 기하 평가 | 1,693 / 1,693 완료: 통과 37, 근거 보류 포함 1,656 |
| 원본·스냅샷 파일의 종료 시점 무결성 확인 | 1,679 파일 |
| 기본 스캔·상세 평가 캐시의 종료 시점 무결성 확인 | 3,361 파일 |
| 확장 압축 멤버 연결 및 분류 | 613건 통과 |
| STL 및 실행 내용 없는 3MF | STL 7건 점검, 3MF 3건 분류 |
| 기존 오류의 엄격한 원본 재현 | 접촉 경계 2건, 얇은 층 문맥 12건 통과 |

독립 대조 기록 SHA-256: `5f08c0a0e308d221af933a6dc4f397fe94ebe285e48047abc6fb10eb1b691b2b`. 종료 후 실제 실행 환경 재확인 기록 SHA-256: `20713a7b82abeabd72d5319c258b9c58683a5696ec444819fb871354b822d0cf`. 원본 A1 백업의 해시는 대조 중 한 번 계산했으며 원본과 제한된 멤버 스냅샷을 구분했다.

`PASS_WITHHELD`는 소프트웨어 검사가 통과했지만 일부 값의 근거가 부족하거나 해당 계산이 필요하지 않다는 뜻이다. 이를 모두 형상 오류나 파단 예측 실패로 세지 않는다. 다음은 1,693개 플레이트 발생 건수를 기준으로 한 **중복 가능한 분류**다.

| 별도 분류 | 플레이트 수 | 해석 |
|---|---:|---|
| 제품 가격 미확인 | 1,163 | 가격 연결 문제이며 형상 오류가 아님 |
| 방향별 소재 참고값 미확인 | 712 | 불명확한 제품 등급·복수 소재 등을 임의 강도로 대체하지 않음 |
| 원본 기하 추출의 실제 한계 | 26 | 선언 치수 누락 13, 비평면 증착 12, 제외된 압출 원호 1. 비정상 치수 오거부 0 |
| 국부 외곽선 범위 불완전 | 54 | 국부 형상 확인 범위를 명시 |
| 국부 증착 단면 보류·부분 계산 | 99 | 완전한 단면으로 가정하지 않음 |
| 국부 층간 접촉 보류·부분 계산 | 753 | 접촉 기하 부족과 실제 용융 접합의 미측정은 별도 |
| 국부 얇은 부위 후보가 없어 추가 구조 스캔 불필요 | 426 | 외곽선 미확인 7, 얇은 부위 미검출 212, 해상도 한계 207 |
| 최종 표시 후보도 없음 | 128 | 위 426건의 부분집합. 나머지 298건은 층 단위 협착 비교 후보만 표시 |

같은 실행 내용과 메타데이터·참고값 문맥을 합친 회귀 분석 문맥은 1,671개다. 위 플레이트 집계, 1,615개 고유 실행 내용, 1,686개 계산 캐시 키와는 집계 기준이 다르다. 발행된 불변식 검사 위반은 0건이고, 새 실측 파단 정답과 적합한 강도 계수는 각각 0개다. 각 검사가 실제 실행된 문맥 범위만 근거로 삼으며, 모든 파일에 역할 보존이나 물리 파단 검사가 수행됐다고 주장하지 않는다.

전체 자료 계산과 별개로, 현재 수정본의 릴리스 검증은 끝났다.

| 확인 범위 | 결과 | 범위의 한계 |
|---|---|---|
| 운영 이미지의 서버 통합 시험 | 594 통과, 18 생략, 160 하위 시험 통과 | 읽기 전용으로 업로드한 테스트 스냅샷에 대한 결과. 이미지에 없는 운영 도구·Node 등의 검사는 별도 수행 |
| 최신 로컬 검증 도구 시험 | 27 통과 | RAW 재사용·의미 동등성·변경된 역할의 재계산 규칙. 시험 중 추가된 마지막 1개를 포함해 별도 확인 |
| 독립 전체 대조 도구 시험 | 23 통과 | 누락·캐시·버전·별칭·검증 도중 원본 변경·미종료 실행·부분 실행·RAW 보조 기록 구분. 위 27개와 합계 50개 통과 |
| 현재 웹 표시·조작 회귀 시험 | Node 11개 스크립트 통과 | 일괄 견적·진행 중 선택 유지·공정 V2/V1·하중 표시·소재 매칭의 확인된 계약 |
| 네이티브 G-code 엔진 | Windows 70 통과, 운영 Linux 이미지 70 통과 | 각 실행 환경의 실제 네이티브 모듈로 수행 |
| 최종 공개 강도 시험 | Windows 244 통과·하위 시험 623 통과, 운영 Linux 이미지 244 통과 | 독립 전체 대조 기록에 연결된 최종 fixture로 수행. 소스·시험·fixture 해시 유지 |
| 형상 캐시 무효화 시험 | 수정 전 실패, 수정 후 통합 시험 통과 | 과거 형식의 성공 결과를 재사용하지 않고 새 형식 작업을 생성 |
| PDF 시각 검수 | 3쪽 검수 | 개인정보와 실제 형상 없는 합성 보고서의 버전·지표·레이아웃 |
| 실제 배포 | API·분석·뷰어·워커 4개 서비스 확인 | 같은 소스 해시와 버전, 네이티브 모듈 로딩 확인 |
| 실제 분석의 웹 복원·뷰어 | 후보 6개와 공정 상세 표시 확인 | 기존 실제 분석을 열어 명령 관측과 두 기하 시나리오가 표시되는지 확인. 견적 저장이나 물리 시험을 수행하지 않음 |

배포 버전은 웹 `0.5.18-corpus-thin-road`, 강도 `0.22.0`, G-code `0.28.0`, 견적 `0.13.0`이다. 강도 계산 소스 커밋은 `dfb4825b39c162db7d33a5e43a77afc55a8ee6a5`, G-code 계산 소스 커밋은 `3f687351f8953182f58010f2e17aa685c9632e56`이다. 현재 전체 자료 실행 환경 지문은 `7c57a945b71ab3214988a234e840201497ac68cc6ca9342b42469723d6b075e0`이다. 실제 웹과 보고서의 버전 표시를 확인했다. 릴리스 확인과 별개로 위 독립 전수 대조를 통과했으며, 두 결과 모두 실제 파단 정확도 실증은 아니다.

통합 시험 중 변경된 파일은 로컬 검증 도구 시험 하나뿐이었다. 원격의 읽기 전용 테스트 스냅샷 해시를 다시 대조해 기존 594개 통과 결과의 범위를 보존했으며, 추가된 검증 도구 시험까지 포함한 최신 27개는 별도로 통과했다. 스냅샷 변경 감지 이력을 성공 기록으로 덮어쓰지 않았다.

그 후 독립 대조 도구의 원본 변경 감지 시험이 추가되어 해당 시험은 18개가 됐다. 최신 로컬 검증 도구 27개와 함께 45개가 별도로 통과했고, 업로드된 서버 시험 스냅샷은 그대로 유지됐다. 두 로컬 도구의 변경을 서버·강도·G-code 엔진 변경으로 세지 않는다.

마지막 대조 사전 검수에서는 아직 끝나지 않았거나 제한된 실행의 기록을 완료 근거로 허용할 수 있는 경계가 발견됐다. 전체 단계의 정상 종료·무제한 실행을 요구하고, RAW 재사용 기록은 보조 근거로만 구분하도록 수정했다. 새 5개 시험은 수정 전 실패했고, 수정 후 독립 대조 시험 23개와 검증 도구 시험 27개가 모두 통과했다. 이전 45개 통과 기록과 서버 스냅샷 변경 감지 이력은 그대로 보존했다.

최종 [공개 회귀 자료](full-corpus-regression-fixtures-20261003.json)는 최소 익명 메타데이터 6건, 접촉 경계의 최소 스칼라 재현 1건, 최신 공정 역할·상태 7건으로 구성된다. 합성 단위 기하·역할 예시는 실제 사용자 형상과 구분한다. 이 14개 사례는 전체 원본 목록을 공개하거나 독립적인 물리 시험 표본을 늘린 것이 아니다. 전체 JSON의 경로·파일 이름·형상·파단 정답 유출 검사도 통과했다.

Windows와 Linux에서 시험한 CRLF 스냅샷 SHA-256은 `328b3096b7c036df21f8361475ee45fe1ac53239ad19f281a760ea086d9819bf`다. Git은 줄바꿈만 LF로 정규화하므로 공개 JSON 파일 SHA-256은 `6c670132a0d0c6f6a7cd1f7c8935cd0199c6bf7251f3a70a746db3a5e1aca47c`다. 두 바이트 표현을 각각 파싱한 JSON 값이 완전히 같음을 확인했으며, 시험한 스냅샷과 그 검증 기록은 그대로 보존했다. [회귀 시험](../tests/test_full_corpus_regression.py) 파일은 이미 LF이며 SHA-256 `58a9aae6cdd22d64dd138a72b2f8fa0e4967c3be30b2e0e7a7886b10d8cf074f`가 유지된다.

---

## English

Validation status: **FULL_CURRENT_CORPUS — software validation and independent original-source reconciliation complete.** Missing records: 0; execution/reconciliation errors: 0. This is not physical failure-prediction validation.

The supplied folders, Q1/Q2 archives, additional G-code folder and A1 SD-card backup form one software regression corpus. These files do not provide measured failure forces or test fixtures. Learning therefore means discovering parser, identity, process and geometry defects and adding reproducible regression cases. It does not establish supervised mechanical training or improved physical failure-prediction accuracy.

### Corpus and identity

The expanded inventory contains 1,682 executable artifact occurrences and 1,693 plate occurrences, with 1,662 artifact hashes and 1,615 executable payload hashes. There are 1,675 canonical artifact execution keys and 1,686 plate execution keys; alias occurrences remain represented. The A1 archive adds 610 executable artifacts and 619 plates. Three additional 3MF sources are excluded as non-executable: two empty files and one model-only file. Seven STL sources receive geometry-only audits, without assumed units, print settings, material identity or force labels.

Only bounded executable archive members are copied into local snapshots. Reconciliation binds the unchanged original archive hash, central-directory member identity/CRC/size, snapshot hash, selected G-code hash and complete stream-consumption proof. Private filenames, original G-code and operating data are not published. Expanded manifest SHA-256: `b01068e705f2eca6efc52762e8c1bf204b0e2b797c7affeabaa2a10c79939b86`.

### Corrections

- Product matching separates supported terminal printer and process-preset suffixes from exact catalog identities. Real grades such as ABS-HF, ABS-GF and PA6-CF remain distinct; incomplete or conflicting identities remain unresolved.
- FusRock source labels retain XY tensile break strength and Z tensile strength separately. The [official ABS product page](https://www.fusrock.com/material/performance/id/106/lang/en) and comparison catalog disagree on the Z endpoint label, so weakest-axis comparability remains unverified. Raw material references stay unchanged; the internal margin applies once only to conditional load scenarios.
- Two actual cases emitted an overlap ratio of `1.0000000000000002`, causing otherwise complete contact geometry to be discarded downstream. The area discrepancy was about `3.55e-15 mm²`. Bounded floating-point normalization corrects this boundary without admitting materially invalid intersections. Complete geometric overlap is not a measured polymer weld or interlayer failure strength.
- UTF-8 progress output avoids the Windows filename-printing failure. Raw scan completion, metadata enrichment and geometry completion are reconciled separately; overlapping partitions from earlier environments do not establish full coverage.
- Positive declared road heights as small as `0.0045 mm` were incorrectly rejected by a shared `0.02 mm` lower bound, withholding entire sections. The declared-height lower bound is now `0.001 mm`, while width remains bounded below by `0.02 mm`. Zero, negative, non-finite and out-of-range dimensions remain invalid. Thin ironing paths retain their declared height without becoming measured bead or weld-strength evidence.
- Exact Cura `WALL-OUTER`, `WALL-INNER`, `FILL` and `SKIN` roles now map to their model roles, while `PRIME-TOWER` remains auxiliary. Labels were checked against the [official Cura G-code reader](https://github.com/Ultimaker/Cura/blob/main/plugins/GCodeReader/FlavorParser.py). Semantic geometry format 2 invalidates old outline/role caches; local process summary V2 and automatic capacity summary V5 prevent earlier summaries from being reused. The viewer handles current V2 and historical V1 process summaries explicitly.

After all calculations exited successfully, 65 previously affected actual sources were rejoined against their latest results. All retain matching original and selected-stream hashes/full byte counts, complete source-deposition geometry extraction and zero `INVALID_ROAD_DIMENSIONS` cases. Some local sections/contact assessments still lack separate evidence, so source extraction completion does not mean every load is available. The strict 12-source process-descriptor replay is a subset of those 65 and is not added to that count. Two contact-boundary cases and one Cura-outline reproduction are separate, potentially overlapping defect evidence, not measured weld-strength or overall mechanical-accuracy sample counts.

Only RAW scans that passed a separate semantic-equivalence audit were reused. The complete selected stream bytes (`25,108,835,104`) and hashes for all 1,693 plate occurrences were verified. No actual source used the newly affected `PRIME-TOWER` label. Code comparison and Python/native execution checks confirmed the declared-height changes only affect inactive context branches in default RAW scanning. Material enrichment, process context, weakness and section calculations run again in the current version.

### Mechanical scope

Validation runs in local isolated paths without changing source files or training on the operating database. Available infill, pattern, walls, temperatures, speed and flow commands retain their coverage and provenance. Declared road-width/height union sections are geometric assumptions, not measured bead or void geometry.

Reference axial loads use stress times effective area; bending loads use stress times section modulus divided by the stated reference arm. The 10/25/50 mm arms are comparison scenarios. They do not validate actual fixtures, load application, stress concentrations, peeling, impact, fatigue or weld strength. Missing process data, unverified mixed-tool attribution, unsupported nonplanar deposition and incomplete geometry retain explicit withholding reasons.

No runtime process-transfer model is approved. Unlabeled user files do not acquire invented failure forces or arbitrary literature multipliers. The reported easy terminal breakage/layer separation remains qualitative location-review evidence, not a measured force target.

All three unlimited native runs exited successfully. One independent agent reconciled the original sources, every plate/alias, current native runtime, cache/source end-state integrity, error history and corrected boundaries. The final flag is `FULL_CURRENT_CORPUS`, with zero missing records or errors. All 1,682 raw artifact occurrences and 1,693 metadata/geometry plate occurrences are represented. Metadata statuses are 505 PASS and 1,188 PASS_WITHHELD; geometry statuses are 37 PASS and 1,656 PASS_WITHHELD. End-state checks cover 1,679 original/snapshot files and 3,361 caches. All 613 expanded archive-member bindings, seven STL audits, three non-executable-source classifications and the strict two-contact/twelve-thin-context original regressions passed. The original A1 archive was hashed once during reconciliation and remains distinct from its bounded member snapshots.

Independent receipt SHA-256: `5f08c0a0e308d221af933a6dc4f397fe94ebe285e48047abc6fb10eb1b691b2b`. Post-exit actual runtime proof SHA-256: `20713a7b82abeabd72d5319c258b9c58683a5696ec444819fb871354b822d0cf`. Public regression fixtures retain only minimal context, invariants and source references; they do not expose private source geometry or paths.

PASS_WITHHELD is not a count of failed geometry or failed physical predictions. **Overlapping categories among the 1,693 plate occurrences** include 1,163 missing product prices, 712 unavailable directional material references, 26 explicit source-geometry limitations, 54 incomplete local-contour coverages, 99 withheld/partial local sections and 753 withheld/partial local contact assessments. The 26 source limitations comprise thirteen missing declared-dimension cases, twelve unsupported nonplanar cases and one excluded deposition-arc case; no `INVALID_ROAD_DIMENSIONS` rejection remains. Price/reference absences are separate from geometry limitations.

For 426 occurrences, no local thin-region candidate requires structural deposition/contact replay: seven lack contours, 212 have no detected thin region and 207 reach the resolution limit. Of these, 298 retain only layer-constriction comparison candidates and 128 have no final presentation candidate. These proxies do not acquire fracture forces. The 128 are a subset, not an additional failed-source count.

The regression miner deduplicates 1,671 executable/member/metadata/reference contexts, distinct from 1,615 unique executable contents and 1,686 execution plate keys. Emitted invariant violations, added measured fracture labels and fitted strength coefficients are all zero. Only actually emitted, checked invariant scopes are certified; no per-source role-conservation or physical failure test is invented.

The release checks are complete separately from full-corpus coverage: the production image passed 594 server tests and 160 subtests, with 18 skips including unavailable private operational helpers or Node. The latest private corpus-helper suite passed 27 tests separately. All 11 checked-in Node UI regression scripts passed against current browser source, including batch restore, progress dropdown stability, current V2/historical V1 process display, loads and identity. All 70 public G-code tests passed with actual Windows native modules and again with the production Linux native modules. An old semantic geometry-cache regression failed before the fix and passed in the new integration suite. Three synthetic PDF pages were visually reviewed for version, metric labels and layout; they contain no customer data or real geometry. All four deployed services—API, analysis, viewer and worker—match source hashes and versions and load their native modules.

The deployed app is `0.5.18-corpus-thin-road`, strength `0.22.0`, G-code `0.28.0` and quote `0.13.0`. Strength source commit: `dfb4825b39c162db7d33a5e43a77afc55a8ee6a5`; G-code source commit: `3f687351f8953182f58010f2e17aa685c9632e56`. Current corpus environment fingerprint: `7c57a945b71ab3214988a234e840201497ac68cc6ca9342b42469723d6b075e0`. Current versions are visible on the deployed web page and synthetic report. The separate independent reconciliation establishes whole-corpus software coverage; neither it nor release checks establishes physical failure accuracy.

Only one local helper-test file changed during the server run, by appending one regression. The immutable uploaded test snapshot was checked again against its saved hashes, preserving the scope of the 594 passing server tests. All 27 current helper tests, including the addition, passed separately. The original detected-drift receipt remains preserved instead of being overwritten as unchanged.

The independent coverage guard subsequently gained a concurrent source-mutation regression. Its 18 tests and the 27 validator/importer tests passed together as 45 isolated tests. The uploaded server snapshot remained unchanged, and neither private helper change modified the app or engine source. An existing actual analysis also rendered all six candidates and process details in the deployed viewer, with command observations and declared/command-volume geometric scenarios shown separately; no quote was saved and no physical failure test was performed.

Final reconciliation preflight found a completion-proof boundary that could admit unfinished or limited runs. The guard now requires successful, completed, unlimited runs for the requested full stage and retains RAW import receipts as auxiliary evidence only. Five new cases failed before the fix; all 23 independent-coverage tests and 27 validator/importer tests passed afterward, for 50 current helper tests. The earlier 45-test receipt and original detected-drift history remain preserved.

The final public strength suite passed all 244 methods on Windows, including 623 successful subtests, and all 244 methods again on the unchanged production Linux image. Its [public regression bundle](full-corpus-regression-fixtures-20261003.json) contains six minimal anonymous metadata cases, one scalar contact-boundary reproduction and seven current role/status cases. Synthetic unit geometry/role probes are distinguished from actual source data. These fourteen cases are not a public dump of the corpus or fourteen new mechanical specimens. Recursive whole-bundle privacy checks passed; source, test and fixture snapshots remained unchanged.

The tested Windows/Linux CRLF fixture snapshot SHA-256 is `328b3096b7c036df21f8361475ee45fe1ac53239ad19f281a760ea086d9819bf`. Git normalizes only line endings to LF, giving the published JSON SHA-256 `6c670132a0d0c6f6a7cd1f7c8935cd0199c6bf7251f3a70a746db3a5e1aca47c`. Parsing both byte representations yields exactly equal JSON values; the tested snapshot and receipts remain preserved. The [regression test](../tests/test_full_corpus_regression.py) already uses LF and retains SHA-256 `58a9aae6cdd22d64dd138a72b2f8fa0e4967c3be30b2e0e7a7886b10d8cf074f`.
