# 보고서 대상별 구성과 G-code 경로 그림 검증

[한국어](#한국어) · [English](#english)

## 한국어

검증 기간: 2026-10-03~04. PrintOps 통합 앱 `0.5.19-report-audience-paths`의 보고서 표시를 수정했다. 강도 `0.22.0`, G-code `0.28.0`, 견적 `0.13.0` 엔진의 계산 코드와 버전은 유지했다. 이번 변경은 보고서 구성과 그림 생성에 관한 것이며 물리적 강도 보정이나 새로운 파단 시험 결과를 뜻하지 않는다.

### 고객용과 관리자용

|보고서|포함 내용|내부 운영 정보|
|---|---|---|
|고객 기본 보고서|출력 조건, 견적 합계, 안내|저장·생성 엔진 이력, 전력 추정 방식, 내부 정책·계수 감사 내역 제외|
|고객 상세 보고서|비용 내역, 실제 경로 그림, 취약 후보별 참고 하중, 출력 설정, 소재 정보|동일한 내부 운영 정보 제외|
|관리자 보고서|상세 보고서 전체 + 관리자 세부 사항|저장·생성 엔진 이력, 전력 산출 상세, 그림 생성 정보, 내부 비용 코드·계산 추적, 저장 입력값 포함|
|관리자 통합 보고서|통합 견적 요약 + 파일별 관리자 보고서 전체|요청한 보고서 종류를 그대로 적용|

PDF와 HTML 모두 같은 대상 구분을 적용했다. 고객용에는 참고 하중의 방향·거리와 실제 파단값과의 구분을 유지한다. 제조사 소재 참고값, G-code 출력 설정, 부품의 가정별 참고 하중은 서로 다른 정보이므로 이를 숨겨 실제 파단강도로 오인하게 하지 않는다. 로컬 서버 처리 고지도 유지했다.

관리자 비용 코드 표는 이미 견적에 포함된 금액의 내부 구성이다. 상세 비용 표에 다시 더하는 항목이 아니다. 보고서 생성은 저장 견적을 다시 저장하거나 금액을 바꾸지 않는다.

### G-code 경로 그림

- 듬성한 전체 경로에 실제 외벽의 연결 경로와 점검 레이어를 함께 표시한다. 레이어를 대표 선별해도 연결 경로의 점을 빼거나 없는 선을 만들어 잇지 않는다.
- 선택 레이어를 강조하고 브리지를 별도 색으로 표시한다. 서포트는 완성품 그림에서 제외한다. 여섯 점검 번호와 연결선을 정렬한다.
- 확대 그림은 실제 선분을 국부 3D 경계와 화면 경계에서 잘라 그린다. 프레임 밖 경로가 그림 영역을 침범하지 않는다.
- 그림 형식 버전은 `2`다. 외벽 경로 파일의 생성·교체·삭제와 렌더링 도중 변경을 캐시 키에 반영해 오래된 그림을 재사용하지 않는다.
- 대표 외벽은 최대 128개 레이어·120,000개 선분, 선택 레이어는 기존 제한을 사용한다. 전체 경로가 항상 전부 그려진다고 보장하지 않으며 관리자 생성 정보에 선별 여부를 기록한다.

실제 기존 G-code 두 견적에서 외벽 선분 34,093개, 대표 레이어 128/464개, 선별하지 않은 점검 레이어, 후보 6개와 그림 2개를 확인했다. 저장 당시 엔진 버전이 다른 견적에서도 저장 이력과 보고서 생성 환경을 구분한다.

### 수행한 검증

|검증|실행 결과|범위|
|---|---|---|
|관련 회귀 검사|46 통과, 세부 검사 5 통과|대상별 공개 범위, 관리자 상세 포함, 비용·소재 정보, 그림·캐시|
|최종 Docker 통합 검사|612 통과, 19 건너뜀, 세부 검사 164 통과|분리된 시험 DB와 읽기 전용 테스트 스냅샷; 232.18초|
|합성 PDF 5종|31페이지|기본·상세·관리자·고객 통합·관리자 통합; 긴 소재 목록 포함|
|실제 서비스 PDF 5종·HTML 2종|51페이지 PDF와 대상별 HTML|기존 두 견적을 사용; 내용 구분·그림·A4 경계·빈 페이지 검사|
|저장 견적 불변|기존 100개 행의 전후 응답 동일|보고서 생성과 실제 경로 검사 후 확인|
|배포 검증|네 서비스의 이미지·소스 해시·버전·네이티브 모듈 일치|API·분석·뷰어·저장 작업; 재시작 0, OOM 표시 없음|

최종 통합 검사 이전에 검증 도구의 경로 진입 오류와 multiprocessing 재진입 문제가 발견됐다. 검증 도구만 수정하고 기존 실패·중단 기록을 보존했다. 수정 전후 제품 코드, 테스트 코드와 빌드 입력의 바이트는 동일하다. 실패·중단된 실행은 통과한 검사로 집계하지 않았다. 최종 실행에서는 테스트·제품 스냅샷이 변하지 않았음을 확인했다.

이 검증은 소프트웨어와 보고서 표시 검증이다. 새로운 G-code 전수 스캔, 실제 파손 시험, 모델 학습, 독립적인 강도 예측 정확도 검증이나 장기간 운영 부하 시험은 수행하지 않았다. 두 의존성의 폐기 예정 API 경고와 19개 건너뛴 검사는 통과 검사와 구분한다.

## English

Validation window: 2026-10-03–04. PrintOps host `0.5.19-report-audience-paths` changes report presentation and figure generation. Strength `0.22.0`, G-code `0.28.0` and quote `0.13.0` calculations and versions remain unchanged. This release adds no fracture measurements or physical calibration.

### Report audiences

Customer basic and detailed PDF/HTML reports omit internal saved/current engine history, power-estimation diagnostics, policy identifiers and coefficient audit notes. Detailed reports retain costs, geometry figures, candidate reference loads, print settings and material information. Load direction, lever distance and the distinction from measured fracture loads remain visible. The local-processing notice remains.

Administrator reports include the entire detailed report plus saved/current engine history, energy calculations, figure metadata, internal component codes, calculation traces and saved inputs. Combined administrator reports contain a summary followed by each complete administrator report. Internal cost breakdowns are already included in the saved total and are not additional charges. Report generation does not rewrite saved estimates.

### Path figures

Real contiguous outer-wall paths are blended with the overview and highlighted inspection layer. Sampling selects whole layers without dropping vertices or inventing connections. Bridges use a separate color, supports are excluded, and six candidate labels are aligned. Zoomed paths are clipped to both the local 3D box and image viewport. Antialiasing improves line clarity.

Figure format `2` and outer-path file fingerprints invalidate cached figures after creation, replacement or deletion. A file change during rendering prevents publication of a mixed cache entry. Representative outer paths are bounded to 128 layers and 120,000 segments; selected-layer rendering retains its existing limit. Sampling status is included in administrator metadata.

Two existing estimates produced 34,093 outer-wall segments, 128 of 464 representative layers, an unsampled inspection layer, six candidates and two figures. Historical engine versions remain distinguishable from the report-generation environment.

### Executed validation and limits

- Focused checks: 46 passed and 5 subtests passed.
- Final built-image host suite: 612 passed, 19 skipped and 164 subtests passed in 232.18 seconds, using an isolated test database and read-only test snapshot.
- Five synthetic PDF variants: 31 pages, including a long material list.
- Five live PDF variants: 51 pages, plus detailed/administrator HTML. Audience content, figures, A4 text bounds and empty pages were checked.
- All 100 existing saved quote responses were identical before and after report generation.
- API, analysis, viewer and storage worker matched the tested image, runtime source hashes, versions and native modules; no restart or OOM flags were observed.

The verification harness initially failed its import-path preflight and later re-entered pytest during multiprocessing. Only the harness was corrected. Failed/interrupted logs were retained and excluded from passing counts. Product, test and build-input bytes remained identical across those corrections; the final run verified unchanged snapshots.

These results concern software and report presentation. No new corpus scan, physical fracture test, model training, independent strength-accuracy evaluation or sustained load test was performed. Two dependency deprecation warnings and 19 skipped tests are not counted as successful tests.
