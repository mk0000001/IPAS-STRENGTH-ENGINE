# 2026-09-30 추가 성능 검증 / Additional performance validation

## 한국어

이 문서는 앞선 [통합 검증](release-validation-20260930.md) 이후의 추가 성능 변경을
기록한다. 강도 수식·소재 참고값·가격 정책은 이번 변경 대상이 아니다. 실물 파단하중의
새 실증 보정이나 모든 파일에서 동일한 속도 향상을 주장하지 않는다.

### 실제 native 스캔 비교

동일 Linux 호스트, CPython 3.12/Cython, 작업당 4 CPU·1536 MiB에서 기존/후보
이미지를 분리 실행했다. 매 실행마다 새 프로세스를 사용했고 원본은 읽기 전용으로
마운트했다. OS 페이지 캐시와 배경 서비스 부하는 완전히 통제하지 않았다.

| 입력·범위 | 기존 | 개선 후보 | 해석 |
|---|---:|---:|---|
| 대형 Q1 SKULL G-code, 각 3회 교차 실행 중앙값 | 110.812초 | 85.183초 | 시간 23.13% 감소 |
| H2C 슬라이스 3MF, 직렬 경로 각 1회 | 28.447초 | 29.285초 | 약 2.95% 증가; 개선 근거 없음 |

대형 병렬 입력은 전체 체크포인트 스캔이 끝나기를 기다리지 않고 완료 구간부터
분석한다. 이번 입력은 16구간이며 첫 작업을 약 5.1초에 제출했고, 체크포인트 완료 전에
11구간 분석을 마쳤다. 기존 첫 병렬 단계는 약 51초 이후였다. H2C의 해당 직렬
경로에는 이 변경이 적용되지 않으므로 한 번의 차이를 성능 향상/회귀의 확정치로 보지 않는다.

모든 Decimal 문자열·레이어·반올림 형상·기타 분석값을 정확 비교했다. 두 원시 float
누적 필드만 상대 오차 1e-10 또는 절대 오차 1e-7 이내를 허용했다. 실제 최대 차이는
압출 경로 길이 1.2033e-6 mm, 명목 압출 시간 1.4057e-8초였다. 이는 분할 수에 따른
덧셈 순서 차이이며 소재 물성·단면적·가격에 임의 배율을 적용한 것이 아니다.
H2C 비교에서는 이 차이도 없었다. 이 시험은 물리적 강도 예측 정확도를 검증하지 않는다.

### 동시 부하

6코어 VM에서 스캔·뷰어를 각각 4 CPU/1536 MiB로 제한해 단독과 동시 실행을
한 번씩 비교했다. 스캔은 82.14→97.52초, 뷰어·국부 두께는 157.38→169.49초로
개별 작업은 느려졌다. 두 작업의 총 완료 시간은 순차 239.52초에서 동시 169.49초로
29.24% 짧았다. 한 번의 부하 실험이며 일반적인 처리량 개선률은 아니다.

스캔 결과와 뷰어 파일 1,179개의 크기·SHA-256이 정확히 같았다. 종료 코드는
모두 0이고 OOM은 없었다. 동시 실행 cgroup 메모리 최고치는 스캔 128.0 MiB,
뷰어 565.1 MiB였다. 당시 구버전 API의 실제 동시 구간 GET은 두 endpoint 모두
30/30 성공했으나, 뷰어만 실행되던 관측 구간에는 health 응답의 2초 timeout이
한 번 있었다. 최신 API 배포 후 83회씩 후속 관측에서도 health 2회·resources 1회의
약 2초 timeout이 발생했다. API는 healthy·재시작 0회, 스캔·뷰어 결과는 그대로였다.
이 지연의 원인은 아직 확정하지 않았으며 부하 응답 검증을 통과했다고 하지 않는다.
잘못된 루프백 주소를 쓴
초기 관측은 서비스 가용성 판단에서 제외했다.

### 다른 경로의 한정된 측정

| 측정 경로 | 시간 감소 | 조건 |
|---|---:|---|
| 완료 뷰어 manifest 응답 조립 | 52.98% | 실제 H2C 디스크 형상, 같은 DB stub, 반복 ASGI 응답 |
| 반복 상세 PDF 생성 | 43.26% | 같은 로컬 렌더·DB stub, 5쌍, invariant PDF 바이트 동일 |
| HA 28일 freshness 집계 재수집 | 85.57% | 같은 DB snapshot, 3 cold/warm 쌍, 전체 결과 hash 동일 |
| 짧은 PostgreSQL 트랜잭션 60개 | 95.64% | 실제 테스트 DB, 새 연결 대비 제한된 풀 재사용 |
| 자원 정보 20개 동시 요청 | 93.52% | 실제 테스트 DB, 2초 공유 샘플 |
| 작업 목록 20개 동시 요청 | 81.65% | 실제 테스트 DB, 200ms 공유 스냅샷 |

서로 다른 경로의 감소율을 합산하거나 전체 사용자 작업 시간의 감소율로 일반화하지
않는다. HA warm 실행은 cold 다음 순서였다. 최근 48시간은 항상 다시 조회하고
캐시는 6시간 후 재조회하므로 새 이력을 영구히 놓치지 않는다. 기존 준비 구간의
원시 전력 20,001행 한도는 별도로 유지되며 초과 표본은 제외한다.

캐시는 개수·바이트 한도를 가지며 매 요청의 원본 접근 검사와 파일/결과/엔진 변경
무효화를 유지한다. 보고서는 저장 견적의 엔진과 현재 생성 환경을 구분한다. DB 풀은
짧은 HTTP 트랜잭션만 대상으로 하며 세션 잠금 연결은 전용으로 남긴다. 무결성 검사는
파일별 전체 해시를 유지하고 배치 진행 상태를 DB에 저장한다.

### 최종 릴리스 확인

최신 이미지의 전체 통합시험은 **228 passed, 1 skipped, 5 subtests passed**다.
Node가 없는 이미지의 skip은 별도 로컬 Node 검증으로 보완했다. 공개 엔진 시험은
G-code 36개·strength 54개·quote 13개 모두 통과했다. 운영 네 서비스에 같은 이미지를
배포하고 소스 해시·native 모듈·버전을 확인했다. 운영 G-code는 **v0.26.0**이며
강도 v0.11.0·가격 v0.8.0의 계산 로직과 버전은 유지했다.

기존 H2C 뷰어와 저장 견적, 4페이지 상세 PDF의 버전·열 설정·그림·텍스트 경계 및
좁은 화면의 후보 목록을 확인했다. HA 수집기의 재시작 잠금 경합도 수정하고 수집기
1개·새 캐시·READY를 확인했다. 구현 담당자가 모두 마친 뒤 마지막 단일 검수자가
새 자원 조회·수집기 재시작 시험 4개를 독립 실행하고 근거를 대조했다. 판정은
**조건부 승인**이며, 위 HTTP 지연은 별도 진단 대상으로 남는다. 좁은 후속 진단
1,683건의 무실패는 원래 부하 지연이 해결됐다는 증거가 아니다.
원본 G-code, HA 이력,
프린터 구성, 비공개 요율과 인증자료는 공개하지 않는다.

## English

This record covers additional performance changes after the earlier integration review.
Strength equations, material references and pricing policies are unchanged. It is not new
physical failure-load calibration or a promise of uniform speedups across files.

### Native scan comparison

Separate old/candidate images ran on the same Linux host with CPython 3.12/Cython,
4 CPU and 1536 MiB per operation, fresh processes and read-only originals. OS page cache
and background load were not fully controlled. Three alternating pairs of a large Q1 SKULL
G-code yielded medians **110.812 → 85.183 seconds: 23.13% less time**. The H2C sliced-3MF
serial path was **28.447 → 29.285 seconds** in one pair; this does not establish improvement.

Completed layer-aligned chunks are submitted while checkpoint generation continues.
The large fixture used 16 chunks, first submission at about 5.1 seconds, with 11 chunks
finished before the checkpoint pass ended. Previously the parallel phase began at about
51 seconds. The unaffected serial route has no expected pipeline gain.

Decimal strings, layers, rounded geometry and all other analysis fields matched exactly.
Only two unrounded floating totals allow relative tolerance 1e-10 or absolute tolerance
1e-7. Maximum observed differences were 1.2033e-6 mm of deposited path length and
1.4057e-8 seconds of nominal deposition time, from accumulation order. No arbitrary
material, section or price multiplier was introduced. H2C had no such differences.

### Contention

One isolated experiment on a 6-core VM gave each scan/viewer task 4 CPU and 1536 MiB.
Individual scan time increased 82.14→97.52 seconds and viewer/local-thickness time
157.38→169.49 seconds under contention. Combined completion fell from 239.52 seconds
of sequential work to 169.49 seconds (29.24%); this single trial is not a general throughput
claim. Scan results and 1,179 viewer artifacts matched exactly. All exits were zero, with
no OOM; concurrent cgroup peaks were 128.0 MiB for scanning and 565.1 MiB for viewing.
The old deployed API passed both 30-request overlap observations, but one 2-second health
timeout occurred in viewer-only observations. A follow-up with the deployed API recorded
two health and one resources timeouts of about two seconds among 83 requests per endpoint.
The API remained healthy with no restarts, and algorithm outputs matched. The cause remains
unconfirmed; the load-responsiveness gate is not claimed to pass.
Initial probes of the wrong loopback bind address are excluded from availability evidence.

### Scoped repeated-work measurements

Manifest assembly decreased 52.98% with real cached H2C geometry and an identical DB
stub. Repeated detailed PDF generation decreased 43.26% over five pairs with identical
invariant PDF bytes. HA freshness recollection decreased 85.57% over three cold/warm
pairs with identical complete snapshots; warm followed cold, and DB caching was not
controlled. Recent 48 hours are reread and sealed-day entries expire after six hours.
The pre-existing 20,001-row preparation-power sample limit remains separate.

Actual test-PostgreSQL comparisons measured 95.64% less time for 60 short pooled
transactions, 93.52% for 20 concurrent shared resource samples, and 81.65% for 20 shared
job-list requests. These independent component results must not be summed or promoted
to a whole-system speedup. Bounded caches retain per-request access checks and source/
result/engine invalidation; advisory-lock sessions remain dedicated. Integrity batches
still hash complete files and persist traversal progress.

The final image passed 228 integration tests and five subtests, with one Node-dependent
skip covered by separate local Node verification. Public-engine suites passed 36 G-code,
54 strength and 13 quote tests. Four deployed services match the image, source hashes,
native modules and versions: G-code v0.26.0, strength v0.11.0 and quote v0.8.0.
Existing H2C viewer data, saved quotes, four PDF pages and narrow-screen candidate layout
were checked. HA collector restart mutex handling was repaired and one collector confirmed
READY with the new cache. After implementers finished, one final independent reviewer reran
four supplemental resource/restart tests and cross-checked the evidence. Approval is conditional:
the HTTP delay remains unresolved. The 1,683 successful narrow diagnostic requests do not
demonstrate that the original load-related delay was fixed.
Raw user inputs, HA history, private rates and credentials are excluded.
