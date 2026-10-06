# 견적 이력 지연 수정과 실측 보정 적격성 / History latency and empirical qualification

## 한국어

상태: **PrintOps v0.5.24-history-summaries를 실제 운영 네 서비스에 배포하고 검증했다. 견적 목록 지연은 개선됐으며, 실측 강도 보정은 적격한 측정자료 부족으로 미완료다.**

이번 작업은 큰 견적 이력의 지연과 실측 강도 보정 자료의 적격성만 다룬다. 강도 v0.24.0, G-code v0.28.0, 가격 v0.13.0의 수치 모델은 변경하지 않는다. 자동 실행은 PAUSED로 유지하며 새로운 대량 스캔이나 전체 문헌 수집을 실행하지 않았다.

### 견적 이력

목록에는 장비·소재·입력 종류·합계·일시만 필요했지만 상세 G-code 분석과 강도 snapshot까지 전송했다. 기존 100건 응답은 14,437,579 bytes였다. 이제 `GET /api/calculator/estimates?summary=true`가 PostgreSQL에서 목록용 필드만 추출하고, 선택한 항목은 `GET /api/calculator/estimates/{id}`로 저장 당시의 상세 정보를 읽는다. 페이지의 목록 요청도 요약 경로를 사용한다.

기본 `summary=false`와 `latest_per_source` 복원은 기존 전체 응답 계약을 유지한다. 저장된 견적을 다시 계산하거나 수정하지 않는다. 목록 갱신과 상세 선택의 요청 순서를 따로 관리해 늦게 온 응답이 새로운 견적이나 다른 프로젝트의 화면을 덮어쓰지 않게 한다. 실패한 상세 조회는 다시 선택할 수 있다.

| 견적 이력 100건 | 이전 중앙값 | 배포 후 중앙값 | 관측 경과시간 감소 |
|---|---:|---:|---:|
| 단독 요청 6건 | 1.2664초 | 0.1946초 | 84.64% |
| 혼합 동시 요청 중 이력 4건 | 2.8845초 | 0.2660초 | 90.78% |

목록 payload는 **14,437,579 → 26,172 bytes (99.82% 감소)**다. 혼합 이력의 최대/nearest-rank p95는 **3.3768 → 0.3242초**였다. config 중앙값은 **0.0232 → 0.1476초**, viewer는 **0.2932 → 0.7927초**로 증가했다. 모든 endpoint가 빨라졌다고 주장하지 않는다. 경과시간에는 응답 수신, JSON 해석과 보존값 검사가 포함된다.

- 최종 동결 이미지의 전체 시험 **658 passed, 21 skipped, 168 subtests passed**, 287.50초, 종료 0, 의존성 deprecation 경고 2건. 별도 시험 DB·읽기 전용 시험 소스를 사용했다. 새 DB 시험의 잘못된 프로젝트 생성 필드로 첫 실행이 실패했고, 해당 시험 입력만 수정 후 최종 전체 시험이 통과했다. 최초 실패 기록은 보존했다.
- 로컬 focused 시험 13개와 실제 JS 이력 회귀 7개가 통과했다. 이미지에는 Node가 없어 새 JS wrapper는 skip이지만 로컬 Node로 실제 스크립트를 실행했다. 기존 batch/material/policy 회귀도 통과했다.
- API·analysis·viewer·worker의 앱 버전·106개 runtime 해시·이미지·네이티브 모듈 일치. 배포 전 진행 작업 0, 확인 시 restart 0·OOM 없음. 이전 운영 이미지 rollback 보존.
- 원래 전체 응답 100건이 **바이트 단위로 동일**하며 SHA-256은 `96419583b33b8c4cbc641bb680f046c4271bb208ff75bb42a3953c56417048cd`다. 최대 상세와 별도 오래된 상세 두 건의 JSON도 해당 원래 저장행과 일치한다. 요약 100건의 라벨·가격·순서 및 기존 cached viewer manifest도 불변이다.
- 실제 기존 프로젝트에서 마우스/Enter 상세 선택, 선택별 basic/detailed/admin PDF 링크 변경, 마우스/키보드 새로고침과 선택 상세 보존을 확인했다. captured browser error/warning 0. 화면 밖 버튼의 초기 자동화 pointer 실패는 포커스/스크롤 후 재확인했으며, 새 업로드·견적 저장은 수행하지 않았다. 변경하지 않은 PDF 구현의 전체 렌더링을 반복하지 않았다.

동결 identity: `f30d1b224d8c623eea46da7eeffa07976801ad0930bc27c6c4de22a506c78365`. 운영 이미지: `sha256:aa54ba6a59c0a1e074f83826407f434f4e403c81c34eed467f93cc0a1c09a8ea`. [호스트 5개 파일 변경 패치](patches/history-summaries-20261007.patch)는 `git apply --unidiff-zero`로 적용하며 이전 소스에 대한 apply-check가 통과했다. 강도 패키지의 물리 모델이나 개정 횟수를 늘리는 변경은 아니다.

다른 한 에이전트의 최종 교차 검토는 **PASS_WITH_EMPIRICAL_CALIBRATION_UNRESOLVED**다. v2 동결·수정된 시험·전체 시험 로그·네 서비스 배포·전후 원본 통계·저장 상세 및 공개 문서를 검토했다. 별도 에이전트가 전체 시험이나 브라우저 작업을 다시 실행했다는 의미는 아니다.

성능 측정은 같은 운영 snapshot에 대해 배포 전후 각각 읽기 전용 GET 18건(단독 이력 6건, 동시성 4의 config/viewer/history 혼합 12건)을 수행한다. 배포 후 목록 요약 경로와 배포 전 전체 목록 경로의 차이를 평가한다. LAN·서버 부하가 통제된 실험이나 모든 endpoint의 성능 향상, 전체 부하의 tail SLA로 해석하지 않는다.

### 실측 보정

사용자는 별도 파단 측정 기록이 없다고 확인했다. 보존된 1차 자료 두 개를 좁게 재검토했지만 **현재 계약에 적격한 수치행 0, 새 승인 보정 모델 0, 목표 출력물의 실제 최초 파손 검증 0**이다. 따라서 실측 강도 보정의 한계는 해결되지 않았으며 새로운 계수를 적용하지 않았다. [공개 적격성 기록](empirical-source-qualification-20261007.json)은 검토 범위와 누락 조건을 남긴다.

| 자료 | 확인한 근거 | 보정에 쓰지 못하는 이유 |
|---|---|---|
| [ASA FRADDCO 데이터](https://zenodo.org/records/14065523), [논문](https://doi.org/10.3390/ma17215207) | 보존된 3DJake ASA 시편 9개의 최대하중/초기 단면적 계산을 확인했다. 보존 workbook의 크기·MD5는 현재 공식 metadata와 일치한다. 원시 곡선 재추출은 반복하지 않았다. | 등급별 한 캠페인뿐이며 batch·조습·여러 공정/시험 조건이 불완전하다. 이 자료의 100% 인필 최대 인장응력을 사용자의 국부 최초 파손하중으로 전이할 수 없다. |
| [Nesheim PA6-CF IR 데이터](https://data.mendeley.com/datasets/pdfz6y8bmh/1), [기관 초록](https://research-information.bris.ac.uk/en/publications/identifying-thermal-effects-during-3d-printing-by-comparing-in-la/) | 기존 감사의 최대하중/면적 관측 108개와 8개 파일 해시를 재사용했다. 현재 record/기관 초록만 추가 확인했으며 새 원시행 추출은 하지 않았다. | 정확한 제품 등급·조습·단면 기준·시험 조건·최초 파손 flags가 불완전하고 제외 규칙/집계에 충돌이 남는다. 하나의 논문/데이터 계보가 독립 holdout을 제공하지 않는다. |

기존 [공정 보정 계약](process-calibration.md)은 같은 등급·방향·면적/시험 기준과 공정/시험 context가 일치하는 원시 시편, 최소 세 평가 캠페인, 학습 범위 안의 holdout과 모든 fold의 평균 baseline 대비 개선을 요구한다. 캠페인 ID만 늘리거나 다른 소재를 섞어 이 조건을 충족한 것으로 만들지 않는다. 통계 후보의 통과도 runtime 승인은 아니다.

실제 보정을 진행하려면 [기존 최초 파손 시험 절차](fracture-evidence-review-20261007.md)에 따라 실제 소재·batch·건조 상태와 G-code, 고정/하중 방향·지렛대 거리, 힘-변위 기록 및 최초 균열의 위치/하중을 함께 확보해야 한다. 인장 시편의 최대응력과 출력물의 최초 균열은 서로 다른 목표값이다. 제조사 원자료와 예상 하중용 미검증 여유계수의 구분은 유지한다.

## English

Status: **PrintOps v0.5.24-history-summaries is deployed and verified on all four services. List latency improved; empirical strength calibration remains incomplete because eligible measurements are unavailable.**

This bounded follow-up addresses large estimate-history latency and empirical-data qualification only. Strength v0.24.0, G-code v0.28.0 and quote v0.13.0 numerical models are unchanged. The automation remains PAUSED. No broad literature collection or corpus scan was restarted.

The UI formerly transferred full saved analysis/strength snapshots to display a few history labels, totals and timestamps. The 100-row response was 14,437,579 bytes. The opt-in `summary=true` route now projects list fields in PostgreSQL, and clicking a row reads its original snapshot through `GET /api/calculator/estimates/{id}`. Default full responses and batch latest-per-source restoration remain compatible; saved estimates are not recalculated or mutated. Independent list/detail sequence guards prevent late responses from overwriting a newer selection, project or calculation. Failed detail requests can be retried.

On 100 unchanged saved estimates, serial median elapsed time was **1.2664 → 0.1946 s (84.64% lower)**; mixed-history median was **2.8845 → 0.2660 s (90.78% lower)**. Payload was **14,437,579 → 26,172 bytes (99.82% lower)**. Mixed-history maximum/nearest-rank p95 was **3.3768 → 0.3242 s**. Config median increased **0.0232 → 0.1476 s**, as did viewer **0.2932 → 0.7927 s**. This is not improvement of every endpoint. Timings include response transfer, JSON parsing and preservation checks.

Final frozen-image suite: **658 passed, 21 skipped, 168 subtests passed**, 287.50 s, exit zero, two dependency deprecations, using an isolated test database and read-only test source. The first run failed because the new DB fixture sent a forbidden project-creation field; only that fixture was repaired before the passing final suite. Both receipts remain. Thirteen local focused tests and seven actual Node history cases passed; the container's Node-dependent wrapper skipped. Related batch/material/policy regressions passed.

All four services match the frozen app version, 106 runtime hashes, image and native scanner modules, with no active jobs before deployment and zero observed restart/OOM. The rollback image is retained. The legacy 100-row full response is byte-identical (SHA-256 `96419583b33b8c4cbc641bb680f046c4271bb208ff75bb42a3953c56417048cd`); two representative saved details, all summary labels/prices/order and cached geometry are unchanged. Actual browser mouse/Enter selection and keyboard/mouse refresh preserved selected detail and switched all three PDF links, with no captured browser warnings/errors. Initial off-viewport pointer automation failures were resolved after focus/scroll. No upload or quote was submitted, and unchanged PDF rendering was not repeated.

Freeze: `f30d1b224d8c623eea46da7eeffa07976801ad0930bc27c6c4de22a506c78365`. Image: `sha256:aa54ba6a59c0a1e074f83826407f434f4e403c81c34eed467f93cc0a1c09a8ea`. The [five-file host patch](patches/history-summaries-20261007.patch) passed an apply-check against the preceding source and requires `git apply --unidiff-zero`. It does not change the strength package's physical model or revision count.

A different agent's final cross-review is **PASS_WITH_EMPIRICAL_CALIBRATION_UNRESOLVED**, covering the v2 freeze/fixture repair, complete suite logs, four-service deployment, raw timing statistics, saved details and public documentation. This does not represent an independent repeat of the whole suite or browser session.

The bounded before/after probe performs 18 read-only GETs per phase: six serial history requests and twelve mixed config/viewer/history requests at concurrency four. It compares the UI's new summary path with the former full-list path on the same saved snapshot. Small sequential deployment-time samples with uncontrolled LAN/server load establish neither whole-system speedup nor an all-load tail SLA.

The user has no separately measured failure records. Neither retained primary candidate qualifies: **zero eligible calibration rows, zero newly approved models and zero verified target-part first-failure records**. The physical calibration limitation remains unresolved; no coefficient was invented. See the [qualification record](empirical-source-qualification-20261007.json).

For [ASA FRADDCO](https://zenodo.org/records/14065523), [paper](https://doi.org/10.3390/ma17215207), nine retained peak-load/initial-area calculations were checked and the workbook size/MD5 matched current official metadata. Curves were not newly extracted. One same-grade campaign and missing batch, moisture, process/test metadata prevent transfer of 100%-infill coupon peak stress to target-part first failure.

For [Nesheim PA6-CF IR](https://data.mendeley.com/datasets/pdfz6y8bmh/1), [institutional abstract](https://research-information.bris.ac.uk/en/publications/identifying-thermal-effects-during-3d-printing-by-comparing-in-la/), 108 numerical observations and eight file hashes were reused from the prior audit; only current record/abstract checks were new. Grade, conditioning, area meaning, test context and first-failure flags remain incomplete, with exclusion/aggregation conflicts. One paper/data lineage supplies no independent campaign holdout.

The unchanged [calibration contract](process-calibration.md) requires source-linked matched raw specimens, complete context, at least three evaluation campaigns, in-range holdouts and improvement over the training-mean baseline in every fold. New labels and pooled unrelated grades do not establish independence; a passing statistical candidate would still require runtime scope/source review. Actual target-part calibration needs measured force/displacement, first-crack location/load, fixture/direction/lever arm, material/batch/moisture and source G-code under the [existing test protocol](fracture-evidence-review-20261007.md). Coupon peak stress and first crack are different endpoints.
