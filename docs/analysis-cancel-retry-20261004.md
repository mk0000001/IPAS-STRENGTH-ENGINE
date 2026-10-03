# 취소 상태 표시와 저장 원본 재분석

[한국어](#한국어) · [English](#english)

## 한국어

PrintOps 통합 앱 `0.5.20-analysis-cancel-retry`의 작업 상태와 복구 흐름을 수정했다. G-code `0.28.0`, 강도 `0.22.0`, 견적 `0.13.0`의 계산 코드와 버전은 유지했다.

### 원인과 수정

일괄 목록은 서버의 `CANCELLED`를 `FAILED`로 바꿔 ‘처리 실패’와 원시 오류 코드 `ANALYSIS_CANCELLED`를 표시했다. 또한 기존 ‘목록 비우기’는 진행 중인 분석에 취소 요청을 보냈다. 과거 문제 작업에는 취소 요청 감사 기록이 없어 당시 요청의 출처를 확정할 수 없다.

- 취소와 실패를 구분한다. 취소는 중립 색상·한국어 설명·별도 개수로 표시한다. 폴링, 프로젝트 복원, 업로드 중단에도 같은 구분을 적용한다.
- ‘완료 항목 비우기’는 진행 중인 업로드·분석·재분석·견적을 유지한다. 서버 취소 요청이나 원본 삭제를 수행하지 않는다. 명시적인 취소 기능은 유지한다.
- 실패·취소된 저장 파일에 ‘다시 분석’을 제공한다. `POST /api/analysis-jobs/{id}/retry`가 원본 파일 버전을 사용해 새 작업을 만들고, 기존 작업은 보존한다.
- 프로젝트와 파일 버전 잠금으로 같은 원본의 재시도를 직렬화한다. 이미 대기·실행 중인 작업은 재사용하고, 취소 처리 중이면 명확한 상태 오류를 반환한다. 삭제·누락·크기 또는 저장 메타데이터가 불일치하는 원본은 API에서 차단한다. 같은 크기의 내용 변조는 실제 분석 전 원본 전체 SHA-256 검증으로 차단한다.
- 취소 요청에는 이전 상태·원본·작업 식별자와 제한된 요청 맥락을 감사 기록으로 남긴다. 인증 헤더·쿠키·토큰은 기록하지 않는다. 대기 작업을 취소하면 완료 시각도 저장한다.
- 다른 탭에서 재분석한 최신 작업을 복원할 때 옛 취소·실패 카드를 갱신한다. 실제 소재 선택은 보존한다. 진행 중인 로컬 재시도·견적과 새 프로젝트 방문을 오래된 응답이 덮어쓰지 않는다.

### 검증

|검증|실행 결과|
|---|---|
|재분석·취소 API|구현 전 23 실패, 최종 23 통과. 동시 요청, 권한, 원본 불변성, 취소 진행 중 상태, 저장 원본 검사, 감사 기록 포함|
|브라우저 로직|최종 13사례 통과, 기존 50파일 복원 회귀 통과, 문법 검사와 Python wrapper 통과|
|배포 이미지 전체 시험|635 통과, 20 건너뜀, 세부 검사 164 통과; 247.45초. 분리된 시험 DB와 읽기 전용 소스 스냅샷 사용|
|실제 파일 복구|저장 원본을 웹의 ‘다시 분석’으로 처리해 18.125초에 `SUCCEEDED`. 파일 3개 모두 견적 가능, 일괄 견적 버튼 활성화; 새로고침 뒤에도 복원|
|원본·저장 이력|8,004,947바이트 원본의 SHA-256 동일, 기존 취소 작업과 새 성공 작업만 존재, 재분석 감사 연결 확인. 기존 견적 100건 응답 불변|
|실제 배포|API·분석·뷰어·저장 작업 네 서비스의 이미지·소스 해시·버전·네이티브 모듈 일치. 재시작 0, OOM 표시 없음|

동결된 소스 식별자는 `ac377367308c10a097ca71c0ec29b24cd6c58d49779183de6ba397533fb3e9dd`, 배포 이미지 식별자는 `sha256:7e2f8d3cc3ac8fcc43bd085a7d283e0840dba3d3016a9c1c71c1f7aee31f7448`이다. 테스트·빌드·배포 시 동일 소스를 확인했다. 독립 에이전트가 코드, 로그, 배포와 실제 복구 증거를 검토했다.

첫 API 수정본 시험의 크기 불일치 fixture가 원본과 같은 길이여서 1건이 실패했다. fixture를 실제로 길이가 달라지도록 수정했고 최종 23건은 통과했다. 이 실패를 제품 오류나 통과 결과로 집계하지 않았다. 컨테이너에서 건너뛴 Node 의존 시험과 로컬에서 실제 실행한 브라우저 시험을 구분한다.

이번 검증은 작업 상태와 복구 동작에 관한 것이다. 코퍼스 전수 스캔, 새로운 시편 파단시험, 강도 모델 학습이나 성능 향상률 측정은 수행하지 않았다. 기존 견적을 자동으로 새로 계산하거나 저장하지 않았다.

## English

PrintOps host `0.5.20-analysis-cancel-retry` changes job presentation and recovery. G-code `0.28.0`, strength `0.22.0`, and quote `0.13.0` calculations and versions remain unchanged.

The batch UI previously converted server `CANCELLED` states into `FAILED`, showing a processing failure and raw cancellation code. Clearing the list also sent cancellation requests for active analyses. Historical cancellation requests were not audited, so the origin of the affected request cannot be established.

Cancelled work now has a separate neutral status, Korean explanation, and count. Clearing completed entries preserves active uploads, analyses, retries, and quotations without cancelling server work or deleting sources. Explicit cancellation remains available.

Failed or cancelled saved files have a retry action. The retry API preserves the old job and immutable source version, serializes requests, and reuses an existing pending/running job. Cancellation in progress and unavailable or mismatched sources receive explicit errors. The analysis worker retains its full source SHA-256 verification. Cancellation audit data is bounded and excludes authentication headers, cookies, and tokens; pending cancellations receive a completion timestamp.

Restoration synchronizes newer retries from another tab without losing actual material selections. Commit guards protect active local work and reject stale responses from an earlier project visit.

### Validation

- Retry/cancellation API: 23 failures before implementation, then 23 passes covering concurrent requests, authorization, immutable sources, cancellation in progress, source validation, and audit events.
- Final browser logic: 13 scenarios passed, existing 50-source restoration regression passed, JavaScript syntax check and Python wrapper passed.
- Built-image host suite: 635 passed, 20 skipped, and 164 subtests passed in 247.45 seconds using an isolated test database and read-only snapshots.
- Live UI recovery: the saved source succeeded in 18.125 seconds without reuploading. All three files became quote-ready, the batch quote button was enabled, and reloading restored the recovered state.
- Integrity: the 8,004,947-byte source retained its SHA-256. Only the original cancelled job and one successful retry exist for that source; their retry audit link was verified. The previous 100 saved estimates remained unchanged.
- Deployment: API, analysis, viewer, and storage worker matched the tested image, source hashes, versions, and native modules, with zero restarts and no OOM flag.

Source freeze: `ac377367308c10a097ca71c0ec29b24cd6c58d49779183de6ba397533fb3e9dd`. Image: `sha256:7e2f8d3cc3ac8fcc43bd085a7d283e0840dba3d3016a9c1c71c1f7aee31f7448`. An independent agent reviewed the code, logs, deployment, and live recovery evidence.

An intermediate source-size test failed because its replacement fixture happened to have the original length. The fixture was corrected to guarantee a different size, and the final 23 checks passed. That failure is not counted as a product defect or a passing check. Container skips and separately executed local Node checks are reported separately.

This validates job state and recovery, with no new corpus scan, physical fracture experiment, strength-model training, or speedup measurement. Existing estimates were not automatically recalculated or resaved.
