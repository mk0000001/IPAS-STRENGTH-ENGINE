# 2026-10-01 상태 API 지연 수정 / Status API latency repair

## 한국어

앞선 [성능 검증](performance-validation-20260930.md)에서 남긴 2초 시간 초과를
추적한 후속 기록이다. 강도·G-code·가격 계산 수식은 변경하지 않았다.

### 확인한 병목

같은 실제 대형 G-code의 스캔·뷰어 동시 부하에서 health 2/83, resources 1/83
시간 초과를 재현했다. 별도 프로세스에서 측정한 저장소 `fsync` 5.843초·4.991초가
해당 구간과 겹쳤다. 기존 health 요청은 DB 검사 후 실제 임시 파일 쓰기·동기화를
동기적으로 기다렸고, 자원 요청도 만료된 표본의 DB 커밋을 기다렸다.

단순 DB 조회 표본은 WAL 쓰기 지연의 증거가 아니다. 디스크 쓰기·flush 지연과
I/O 압력 증가를 확인했으나, 가상 디스크 아래의 물리 장치 원인까지 확정하지 않았다.
`discard` 옵션은 켜져 있었지만 해당 구간의 discard 지연은 43ms/0ms로 작았다.
TRIM 원인으로 단정하거나 마운트·내구성 설정을 바꾸지 않았다.

첫 독립 HTTP 관측기는 이름 충돌로 시작하지 못했다. 그 실행의 빈 HTTP 자료는
통과 근거에서 제외하고, 기존 HTTP 자료와 유효한 별도 I/O 자료만 사용했다.
관측기를 수정하고 실제 로컬 HTTP 서버로 점검했으며, 이후에는 모든 관측 경로의
준비 확인을 통과해야 대형 작업이 시작되도록 했다.

### 수정과 상태 의미

- health 검사 1초·자원 검사 2초 간격의 전용 배경 작업으로 I/O를 분리했다.
  검사별로 실행 중인 작업은 하나뿐이며 느려져도 대기열이 늘어나지 않는다.
- DB와 실제 저장 경로의 파일 쓰기·flush·fsync를 유지했다. 자원 결과도 커밋이
  끝난 뒤에만 발행한다. HTTP 제한 시간은 늘리지 않았다.
- HTTP는 완료한 표본을 반환한다. 검사 시작부터 3초를 넘겼거나 오류·미완료이면
  즉시 503을 반환한다. 느린 검사가 끝났다는 이유로 오래된 관측을 새 값으로
  표시하지 않는다. 응답에는 관측 시각·나이·소요 시간·진행 여부가 포함된다.
- 웹은 503일 때 과거 CPU 값을 현재 값처럼 남기지 않고 확인 지연·자동 재조회
  문구를 표시한다. 정상 표본이 돌아오면 복구한다.
- 겹치는 앱 수명주기 중 하나가 끝나면서 공용 검사기를 중단하던 회귀도 수정했다.

이 변경은 요청이 저장소 I/O를 기다리다 시간 초과되는 경로를 분리한다. 저장소
자체의 긴 지연이 없어졌다는 뜻은 아니다. 503 상태와 요청 시간 초과는 구분해
보고하며, 모든 응답이 200이라는 보장을 하지 않는다.

### 버전과 검증

운영 앱은 **v0.3.1-api-latency**다. 실제 엔진 코드가 바뀌지 않았으므로 G-code
**v0.26.0**, 강도 **v0.11.0**, 가격 **v0.8.0**을 유지했다. 웹과 PDF에 앱·엔진
버전을 표시하고, 과거 견적의 저장 당시 엔진 버전은 보존한다.

최종 후보 통합시험 **240 passed, 4 skipped, 5 subtests passed**. 제외된 4개는
이미지에 없는 Node 1개와 Windows 작업 스케줄러 도구 3개이며, 해당 검사는
호스트에서 별도로 통과했다. Node 폴링·지연 표시·복구 회귀와 버전 보존 시험도
통과했다. 네 운영 서비스의 전체 앱 소스 해시·native 모듈·버전 일치를 확인했다.
기존 H2C 견적·뷰어 결과를 보존하고 4페이지 PDF의 문자 경계와 렌더를 검수했다.

### 운영 동시 부하 재검증

동일한 실제 스캔·뷰어 작업을 함께 실행했다. 독립 HTTP 관측 2,441건에서
**시간 초과 0건, 200 응답 2,395건, 503 응답 46건**이었다.
503은 모두 오래된 표본을 거부한 `STATUS_SAMPLE_STALE`이며 이후 자동 복구했다.
종료 후 여섯 경로에서 각 20회, 총 120회 요청은 모두 200이었다.

| 외부 요청 경로 | 요청 수 | 200 / 503 | p95 | 최대 |
| --- | ---: | ---: | ---: | ---: |
| health | 408 | 399 / 9 | 8.02 ms | 568.88 ms |
| resources | 408 | 394 / 14 | 8.20 ms | 447.76 ms |
| 정적 CSS | 406 | 406 / 0 | 12.12 ms | 574.92 ms |

나머지는 API 내부 루프백에서 독립 관측한 요청이다. 기존 스레드 관측도 178건 중
시간 초과 0건이었다. 스캔·뷰어 산출물은 이전 결과와 정확히 일치했고 원본과
운영 API 상태를 보존했다. 진단 컨테이너를 정리했고 OOM·API 재시작은 없었다.

**저장소 지연 자체는 미해결이다.** 같은 실행에서 fsync 6.026초와 WAL 커밋
5.769초가 관측됐다. 기존의 ‘모든 응답 200’ 판정은 실패와 종료 코드 1을 그대로
보존했다. 시간 초과 제거와 저장소 정상화를 혼동하지 않는다. HTTP·I/O 관측 자체도
부하를 추가하므로 이 결과로 전체 시스템 성능 향상률을 산출하지 않는다.

최종 단일 독립 감사에서 느린 검사를 중지한 직후 같은 프로세스에서 다시 시작하면
검사기가 멈춘 채 남는 수명주기 경합을 추가로 재현했다. 기존 검사 종료 후에만
재시작하도록 수정하고 두 회귀 시험을 추가했다. 수정 전 실패·수정 후 통과를
확인했다. 위 동시 부하 측정은 이 재시작 수정 전 후보의 결과이며, 최종 후보는
전체 통합시험과 네 서비스 배포 일치·실제 보고서 검증으로 별도 확인했다.
대량 스캔 연산 경로는 이 마지막 수정에서 바뀌지 않았다.
최종 이미지 `7cc28c60418f`에서 240개 시험과 5개 하위 시험이 통과했고,
네 서비스의 소스·native 모듈·버전 일치와 재시작 0회를 확인했다.
재배포 후 기존 견적·뷰어 보존, 전력 동기화 READY, 4페이지 PDF 검수를 완료했다.

## English

This follows the three two-second timeouts in the prior performance record. Equations and
public engine code are unchanged. The same real scan/viewer workload reproduced two health
and one resources timeout. Independent durable flushes took 5.843 and 4.991 seconds during
the affected intervals. The old health route performed DB and real file write/flush/fsync
inline; expired resource samples also required a committed refresh before responding.

Read-only DB timing is not evidence of WAL write latency. Block write/flush delay and I/O
pressure were observed, but the physical cause beneath the virtual disk was not established.
Discard timings were small; mount and durability settings were not changed. An initial
independent HTTP observer failed to start and its empty results are excluded. The corrected
observer is smoke-tested and must signal readiness on every path before a workload starts.

One bounded background check per endpoint now performs the original I/O. Health runs at
one-second intervals and resources at two seconds. Completed observations older than three
seconds from collection start, absent observations and failed checks return 503 promptly.
Slow completion cannot make an old sample fresh. HTTP timeouts were not increased. The UI
replaces stale counters with a retrying message and restores live data upon recovery.
Overlapping app lifespans now retain shared samplers until their last owner exits.

This isolates request latency from durable I/O; it does not eliminate the underlying storage
stall. Prompt 503 degradation and request timeout are separate outcomes, not an all-200 promise.

App **v0.3.1-api-latency** is deployed. Unchanged engines remain G-code **v0.26.0**, strength
**v0.11.0**, quote **v0.8.0**. Web/PDF show the app and current engines while preserving saved
estimate provenance. Integration passed **240 tests and five subtests**, with four environment
skips (one Node and three Windows scheduler tests), covered separately on the host. Four
services match sources/native modules/versions. Existing H2C data and four PDF pages passed
checks.

### Deployed contention check

The same real scan and viewer workload produced **2,441 independent HTTP observations:
zero timeouts, 2,395 HTTP 200 and 46 HTTP 503**. Every 503 was `STATUS_SAMPLE_STALE`;
checks recovered automatically. All 120 post-workload requests across six paths returned 200.
External health: 408 requests, 399/9 status split, p95 8.02 ms, maximum 568.88 ms.
External resources: 408 requests, 394/14 split, p95 8.20 ms, maximum 447.76 ms.
External CSS: 406 requests, all 200, p95 12.12 ms, maximum 574.92 ms.
The remaining observations used independent API loopback probes. The previous thread-based
observer also recorded zero timeouts in 178 requests. Scan/viewer outputs matched exactly;
source data and API state were preserved, with no OOM or API restart. Diagnostic containers
were removed.

**The underlying storage stall remains unresolved:** fsync reached 6.026 seconds and WAL
commit 5.769 seconds. The original all-200 gate remains false with exit code 1 preserved.
Removing HTTP blocking does not prove healthy storage. Probes add load, so this run does not
establish a system-wide speedup percentage.

The final single independent reviewer reproduced a lifecycle race: restarting a sampler in
the same process while a stopped probe was still blocked could leave it stopped permanently.
Restart now waits for that probe to exit. Two added regressions failed before the fix and pass
after it. The contention figures above belong to the pre-lifecycle-fix candidate; the final
candidate is separately checked by full integration tests, four-service source parity and live
report validation. The final lifecycle fix does not alter bulk scan computation.
Final image `7cc28c60418f` passed 240 tests and five subtests; all four deployed services
match sources, native modules and versions, with zero restarts. Post-deployment checks
preserved estimates and viewer outputs, confirmed energy sync READY and reviewed four PDF pages.
