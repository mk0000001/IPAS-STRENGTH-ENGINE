# 시스템 검증 결과와 적용 한계

최신 통합 검증(2026-10-03): [끝 연결부·층간 접촉·원자료/예상 하중 분리](integrated-weakness-validation-20261003.md), [1차 문헌·실측자료 근거](weakness-research-redesign-20261003.md). 아래 기록은 이전 점검 이력입니다.

Latest integrated validation (2026-10-03): [terminal roots, layer contact and separate material/load inputs](integrated-weakness-validation-20261003.md), [primary evidence](weakness-research-redesign-20261003.md). Entries below are historical.

[한국어](#한국어) · [English](#english)

## 한국어

검증일: 2026-09-25. 공개 엔진과 이를 사용하는 PrintOps 통합 앱의 현재 릴리스를 점검했다. 이 문서는 검증 범위를 밝히는 기록이며 무결함 인증이나 출력물의 구조 안전 인증이 아니다.

후속 기록: [2026-10-02 하중 상태·가변 단면 계산](load-status-and-variable-sections-20261002.md), [2026-10-02 강도·뷰어 통합 검토](strength-viewer-audit-20261002.md), [2026-09-30 통합 검증](release-validation-20260930.md), [2026-09-30 추가 성능 검증](performance-validation-20260930.md), [2026-10-01 API 지연 수정](api-latency-validation-20261001.md), [2026-10-01 시편 근거·명시적 하중 검증](strength-release-validation-20261001.md), [2026-10-01 FusRock 공식 소재 카탈로그](fusrock-official-catalog-20261001.md). 아래 내용은 9월 25일 당시의 기록이다.

최신 기능: [2026-10-03 힘 입력 없는 자동 하중 추정](automatic-load-estimates-20261003.md).

관련 문서: [논문·자료의 핵심 근거](research-evidence.md), [공정 근거 API](../PROCESS_EVIDENCE.md).

## 구성과 책임

|구성|담당 범위|다른 구성에 넘기는 값|
|---|---|---|
|[G-code engine](https://github.com/mk0000001/print-gcode-engine)|G-code/슬라이스 3MF, 활성 소재·프린터, 모달 이동 상태, 레이어·공정 명령과 방향 통계|분석 사실 및 설정. 소재 강도·가격을 결정하지 않는다.|
|[Strength engine](https://github.com/mk0000001/print-strength-engine)|레이어 협착과 연결된 국부 단면 선별, 문헌 비교, 미보정 하중 가정|위치 후보, 출처·미확인 조건, 시나리오. 실제 파손 위치·하중의 예측으로 확정하지 않는다.|
|[Quote engine](https://github.com/mk0000001/print-quote-engine)|호스트 정책에 따른 Decimal 비용, 전력 추정, 할인·세금·반올림|정책과 입력의 계산 결과. 운영 요율·접속정보는 공개 엔진에 포함하지 않는다.|
|통합 앱|프로젝트·파일 버전, 업로드·작업 복원, API, 소재 참조 연결, 뷰어·PDF, 저장·백업|각 엔진 출력의 출처를 유지하고 소재 참고값과 부품 하중을 구분한다.|

## 이번 점검에서 수정한 문제

1. **혼합 PLA 제품 오매칭:** Bambu PLA Basic 프로필 하나만 포함돼도 여러 활성 제품 전체를 동일 제품으로 취급할 수 있었다. 이제 활성 제품을 정규화한 뒤 모두 동일한 일반 등급일 때만 해당 참조를 사용한다. 혼합 제품·일부 미상 제품·Silk/Matte/Tough 등 다른 등급은 단일 제품 수치로 대체하지 않는다.
2. **과거 PDF 수치 재사용:** 소재 식별 메타데이터가 없는 견적의 과거 참고응력을 재검증된 현재 수치처럼 표시할 수 있었다. 이제 `REFERENCE_NOT_REVALIDATED`로 보류하며, 그 값을 추가 하중 계산에 사용하지 않는다. 저장된 견적 원본은 변경하지 않는다.
3. **서비스 버전 불일치:** 저장 작업 서비스가 구버전 이미지에 남아 있었다. 유휴 큐 확인 후 API·분석·뷰어·저장 서비스의 배포 이미지를 맞추고 소스 해시와 네이티브 모듈을 확인했다. 이후 배포 검사에도 저장 서비스를 포함한다.

직전 수정한 Bambu ABS 전용 참조도 회귀 검증했다. 해당 프로필이 다른 브랜드의 충돌 자료로 넘어가지 않으며, 같은 제조사 TDS의 XY/Z 인장강도와 열처리 조건을 함께 표시한다. ABS-GF/CF/HF/+ 등은 일반 ABS로 대체하지 않는다.

## 실행한 검증

|검증|결과|범위의 한계|
|---|---|---|
|통합 앱 자동시험|168개 통과, 1개 skip|분리된 시험 DB 사용. 프로젝트 보관·복원·버전 불변성, 동시 업로드·취소·복구, 모든 카탈로그 기종의 견적 입력, 할인·전력, 소재·취약 형상·뷰어·PDF 경로를 포함한다. 모든 실제 프린터에서 출력해 본 것은 아니다.|
|G-code / strength / quote 실제 빌드 시험|각 26 / 54 / 7개 통과|G-code 네이티브 모듈이 로드된 Docker 이미지에서 실행. 실제 제품 파단시험의 정확도를 검증한 수치가 아니다.|
|브라우저 형식 시험|컨테이너에서 Node 부재로 skip한 1개를 로컬 Node로 별도 통과|참고값과 힘 단위의 null/0 처리. 앱·뷰어 JavaScript 문법 검사도 통과.|
|실제 기존 분석 API|Bambu ABS 참고값과 6개 형상 후보 정상 반환|기존 분석 2건을 조회해 확인. 새 파일 재업로드·전체 corpus 재스캔은 하지 않았다.|
|실제 브라우저|해당 분석의 소재 참고값·조건·뷰어 정상 표시, 390px에서 가로 넘침 없음, 검사 시 콘솔 오류 없음|표적 화면 확인이며 모든 화면·기기 조합을 전수 검사한 것은 아니다.|
|상세 PDF|기존 G-code 견적의 5페이지를 생성·렌더링해 확인|비용, 전체/확대 이미지, 후보별 레이어·단면·하중 가정, 제조사 참조와 한계 표시. 수치가 표시된다는 사실은 파단 예측의 정확성을 뜻하지 않는다.|
|배포 운영|API/DB 정상, 네 앱 서비스 이미지·소스 해시 일치, 재시작/OOM 표시 없음|점검 시점의 스냅샷. 장기 무장애를 보장하지 않는다.|
|작업 큐|10분 이상 갱신 없는 RUNNING 작업 없음, 최근 7일 실패한 분석 없음|DB 상태 기준이며 별도의 장시간 부하 시험은 수행하지 않았다.|
|백업|최근 백업 존재, SHA-256과 PostgreSQL archive catalog 검사 통과|DB 백업의 읽기·무결성 확인이다. 새 환경 전체 복구와 사용자 파일 복구 시험은 별도다.|
|전력 데이터|기존 3종 장비의 프로필 API 정상|예상 작업의 직접 계측 kWh가 아니다. 열손실 보정과 다른 장비 전이는 모델 가정이다.|

## 성능 검증의 정확한 해석

직전 동일 서버 CPU 4코어 제한/1536MiB 격리 측정에서, 약 40.7MB 내부 G-code를 가진 3MF는 22.271→21.931초, 약 320.4MB G-code는 106.148→104.492초였다. 압축 파일은 해제 시간도 포함했다. 두 파일의 전체 결과 JSON과 SHA-256은 일치했다.

각 버전 1회 측정의 약 1.5% 차이는 실행 변동과 구분하기 어렵다. 작은 파일은 직렬 경로이므로 그 차이를 사전 스캔 최적화 효과로 해석하지 않는다. 먼저 시도한 파이프라인은 개선되지 않아 되돌렸다. **50% 처리시간 감소나 뷰어 4배 가속을 달성했다는 결론은 아니다.**

## 재현과 남은 검증

각 공개 엔진의 의존성을 준비한 뒤 저장소 루트에서 다음을 실행한다.

```sh
python -m unittest discover -s tests
```

강도 엔진의 형상 시험에는 NumPy·SciPy·Shapely가 필요하다. G-code 네이티브 빌드는 해당 저장소 README의 Cython 빌드 절차를 따른다. 통합 앱의 정책·운영 DB·사용자 파일은 공개하지 않으므로 위 명령은 공개 엔진 시험이며 전체 앱 운영환경의 재현 명령은 아니다.

다음은 아직 해결됐다고 주장하지 않는다.

- 실제 가력점·지지조건·국소 접합면적·공극·노치/균열을 포함한 사용자 부품의 파단하중/파손 위치 실증.
- 서로 다른 제조사·배치·인필·패턴·벽·속도·열이력 간 보정식과 독립 holdout 정확도.
- 신규 기종별 계측 전력 검증, 장시간 최대 동시작업 부하, 장애 후 전체 복구 시험.
- 논문 원문 전수 대조. 핵심 검토 출처와 미확인 조건은 연구 근거 문서에 개별 표시한다.

따라서 현재 제공 가능한 결론은 **기능 회귀시험과 표적 운영 검증을 통과했고 확인된 오매칭·과거수치 재사용·배포 불일치를 수정했다**는 것이다. 소프트웨어 시험과 재료/구조의 실증 검증은 별도로 유지한다.


---

## English

Latest feature: [2026-10-03 automatic reference loads without force input](automatic-load-estimates-20261003.md).

Latest follow-ups: [2026-10-02 strength/viewer integration audit](strength-viewer-audit-20261002.md), [2026-10-01 specimen evidence and explicit-load validation](strength-release-validation-20261001.md). The older sections below are historical records, not the current capacity contract.

### System validation and scope

Later records: [2026-09-30 integration validation](release-validation-20260930.md) and
[additional performance validation](performance-validation-20260930.md), and
[API latency repair](api-latency-validation-20261001.md). The following
sections retain their original September 25 scope.

This is the **2026-09-25** validation record for the public engines and their PrintOps host application. It is a dated record, not a claim that later releases have the same test count, a defect-free certificate, or a structural safety certification. See the [research evidence](research-evidence.md) and [process API](../PROCESS_EVIDENCE.md).

The G-code engine parses files, active materials, modal motion, layers and process statistics; it does not set strength or prices. The strength engine screens constrictions and connected local sections and reports literature comparisons and uncalibrated scenarios. The quote engine applies host-supplied policies using Decimal arithmetic. The host manages projects, file versions, uploads, jobs, material references, viewers, reports and storage. Public packages do not contain production rates, credentials or user files.

### Corrections in this audit

1. Mixed active PLA products could inherit Bambu PLA Basic's reference when only one matching profile was present. Matching now requires the normalized active identities to agree on the ordinary grade. Mixed, partially unknown and Silk/Matte/Tough profiles do not inherit the base-grade value.
2. Historical PDF values without material identity metadata could appear revalidated. They are now withheld as `REFERENCE_NOT_REVALIDATED` and are not reused for new load calculations. Saved estimates remain unchanged.
3. The storage worker was running an older image. After checking its idle queue, API, analysis, viewer and storage services were aligned and their source hashes/native modules checked. Deployment checks now include storage.

The preceding Bambu ABS fix was also regression-tested: the base product uses the same manufacturer's tensile XY/Z references and annealing conditions, rather than a different brand's unresolved evidence. ABS-GF/CF/HF/+ do not inherit ordinary ABS values.

### Executed checks

|Check|Recorded result|Limitation|
|---|---|---|
|Host application|168 passed, 1 skipped, isolated test DB|Covers project/version handling, uploads/cancellation/recovery, catalog quote inputs, discounts, energy, material/geometry/viewer/PDF paths. Not physical printing on every machine.|
|Built G-code / strength / quote packages|26 / 54 / 7 passed|Run in the Docker image with native G-code modules loaded. Not a fracture prediction accuracy test.|
|Browser formatting|The Node-dependent skipped test passed separately with local Node; JS syntax checks passed|Null/zero reference and force formatting.|
|Existing live analyses|Two existing analyses returned Bambu ABS references and six geometry candidates|No fresh upload or full corpus rescan.|
|Browser|Target reference/conditions/viewer visible; no horizontal overflow at 390 px; no observed console errors|Targeted UI checks, not all device/screen combinations.|
|Detailed PDF|All five pages of an existing estimate rendered and inspected|Costs, model/detail images, layer/section/scenario fields and material caveats. Visibility is not physical validation.|
|Runtime|API/DB healthy; four app services on matching image/source hashes; no restart/OOM flags|Point-in-time observation, not long-term reliability.|
|Queues|No RUNNING job stale for more than 10 minutes; no failed analyses in the preceding seven days|DB status check, no prolonged load test.|
|Backup|Recent archive present; SHA-256 and PostgreSQL archive catalog checks passed|No complete fresh-environment/database/user-file restoration drill.|
|Energy|Existing profile API for three machines working|Forecast energy is not metered consumption of the proposed job. Cross-machine transfer remains model-based.|

### Performance interpretation

Earlier isolated runs on the same server with a four-CPU/1536 MiB limit measured 22.271 → 21.931 s for a 3MF containing approximately 40.7 MB of G-code, and 106.148 → 104.492 s for approximately 320.4 MB of G-code. Archive extraction was included. Full result JSON and SHA-256 matched.

One run per version cannot distinguish the roughly 1.5% differences from variability. The smaller case uses the serial path, so its change must not be attributed to checkpoint optimization. An earlier pipeline attempt was reverted after showing no improvement. These results do **not** establish a 50% time reduction or fourfold viewer speedup.

### Reproduction and outstanding work

After installing each package's dependencies, run `python -m unittest discover -s tests` in its root. Strength geometry needs NumPy, SciPy and Shapely; native G-code compilation follows that repository's README. These commands reproduce public package tests, not the private host's production database/policy/files.

Still outstanding: physical validation of user-part failure loads and locations with real fixtures/contact/voids/notches; cross-grade/batch/process calibration and independent holdouts; new-machine energy measurements; sustained concurrency and complete recovery drills; and full-text verification of every listed source. Software regression tests and targeted operational checks must remain distinct from material/structural empirical validation.
