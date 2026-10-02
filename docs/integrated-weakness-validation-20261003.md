# 강도·취약부 통합 검증 / Integrated weakness and strength validation

[한국어](#한국어) · [English](#english)

## 한국어

**상태: 소프트웨어·배포 검증 완료.** 최종 배포의 출처, 컨테이너 회귀, 데스크톱 브라우저와 PDF 결과를 독립 검토했다. 아래 기록은 확인한 범위의 릴리스 검증이며 물리적 파단 정확도나 모든 기기의 화면 동작을 인증하지 않는다.

검증일: 2026-10-03. 이 기록은 `print-strength-engine 0.18.0`, 호스트 `0.5.13-material-reference`, 견적 엔진 `0.13.0`의 소프트웨어 회귀, 익명화한 464층 입력의 재현, 배포된 출력의 일치성을 다룬다. **실제 최초 파손 위치나 파단하중 정확도를 검증한 기록은 아니다.** 설계·문헌 근거와 미확인 물성은 [통합 재설계 근거](weakness-research-redesign-20261003.md)를 참조한다. 사용자 파일, 원본 형상, 견적 금액, 내부 주소와 식별자는 공개하지 않는다.

### 원자료·여유계수 분리와 표시

제조사 방향별 물성을 원자료로 보존하고, 예상 하중용 입력을 별도로 만든다. 예를 들어 원자료 XY 33.36 / Z 55 MPa는 소재 표시와 공정 근거에 그대로 남고, 내부 여유계수 0.85를 한 번 적용한 X/Y 28.356 / Z 46.75 MPa만 하중 시나리오에 전달한다. 계수는 실측 보정계수나 검증된 안전율이 아니다. 보고서·뷰어·사용자 지정 하중 계산이 같은 분리 경로를 소비한다. 소재 메타데이터 없는 복원에서는 저장 원자료·하중 참고값을 재사용하지 않는다.

방향별 소재 참고와 공식 특성은 기본 접힘이며 취약 후보 요약은 밖에 남는다. 사용자가 펼친 방향별 참고 영역은 표시 단위를 바꾸어도 유지한다. 실제 운영 Chrome에서 두 영역의 기본 접힘, 후보 요약 표시, 원자료 X/Y 33.36 / Z 55 MPa, 계수 분리와 단위 변경 후 펼침 유지가 확인됐다. 데스크톱의 실제 client/scroll 폭은 모두 1905 px였고 카드 겹침과 콘솔 오류는 없었다. provider가 반응형 폭 변경을 무시했으므로 **모바일·좁은 화면 검증 완료로 표시하지 않는다.**

견적 엔진은 전체/모델 시간의 출처를 구분한다. 전체 준비 포함 시간과 유효한 명시 모델 시간이 있으면 평균 출력 전력에는 모델 시간을 사용하고, 조건이 맞는 과거 준비 에너지를 별도로 한 번 합산한다. 명시 모델 시간이 없으면 역사적 시간차/미확정 계산 기준을 기록하며, 사용할 수 없는 모델 시간 입력에는 추가 진단을 남긴다. 모호한 시간 범위나 수동 시간 불일치는 원본 모델 시간으로 대체하지 않는다. 같은 계량값에 포함된 보조 장치·건조 전력은 다시 더하지 않는다. 배포된 API의 읽기 전용 검증에서 이 분리 경로와 현재 계량 이력 사용을 확인했으며, 저장 견적·HA 설정·전원 상태를 변경하지 않았다. 해당 작업의 직접 계량 소비량 인증은 아니다.

### 구현과 계산 계약

외형 선별은 동일 단면의 긴 중간 구간을 대표 후보로 합치고, 끝 연결부와 국부 단면 감소를 보존한다. 자유단의 작은 끝 캡 대신 안쪽 평가 구간을 사용한다. 급격한 단면 변화의 선별 기준과 안쪽 구간은 명시한 기하 정책이며 실증 보정한 파괴 법칙이 아니다. 복셀 연결 영역은 원본 객체 식별자가 아니고, 단일 복셀 두께 등 해상도 제한 후보는 확정된 참고 하중 순위에 섞지 않는다. 표시한 뿌리가 실제 부착부·고정점이라는 주장도 하지 않는다.

원본 모델 경로를 한 번 스트리밍하여 후보 단면과 국부 인접 층의 선언 경로 footprint 교집합을 함께 계산한다. 서포트와 보조 경로를 제외하고, 선폭·층 높이가 누락되거나 잘못된 모델 경로, 비평면 경로, 처리 한도와 불완전 스캔은 보류 사유로 남긴다. 가변 층 높이의 실제 선언 구간을 사용하며, 같은 평면의 높이 구간이 불일치하면 완전한 계면으로 취급하지 않는다.

굽힘 참고 하중은 같은 25 mm 거리, 같은 지원 모델·단일 소재 도구·참고 면적 정의·전이 가정에서 비교한다. 10·25·50 mm는 명시한 정적 비교 거리다. 소재의 정상응력 참고값을 선언된 순단면에 전이하고, 국부 경로 조각이 완전히 접합된 균질 연속체처럼 변형한다는 가정은 **미검증**이다. 원자료의 응력 면적 기준 `UNKNOWN`은 그대로 유지한다. 계면 파괴에너지나 파괴인성을 인장 MPa로 대신하거나 접촉비를 하중 배수로 사용하지 않는다.

접촉 진단에는 작은 면적, 첫·마지막 계면, Z 창 경계, XY 잘림, 충분한 양쪽 깊이, 단순 확장·축소와 반복적인 겹침 손실을 구별하는 조건이 있다. 전체 관찰은 작업자 캐시에 보존하고, 표시용 관찰 배열을 32개로 제한해도 모든 관찰 종류·개수는 유지한다. **겹침 100% 또는 진단 `COMPLETE`도 실제 비드 접촉이나 용융 접합강도의 확인이 아니다.**

### 익명화한 원본 재현

재현 원본 SHA-256: `373f78b503cbd4ce172bc29e6867e064044ca0316457c716a0fd944e50af0473`.

선택한 G-code 구성원을 51,010,921/51,010,921바이트, 1,986,902줄까지 읽었으며 모델 경로 기록은 627,302개였다. 원본 스캔과 기하 처리 완료, 제외·처리 한도 초과 곡선 0개, 거부 기록 0개를 확인했다. 이 완료 표시는 선언된 입력을 읽었다는 뜻이며 실측 접합·부품 하중 경로 검증을 뜻하지 않는다.

참고 하중에 따른 후보 순서는 다음과 같다. 이전 기하 후보 3·4번은 참고 하중 비교에서 순서가 바뀌며, 웹과 보고서 번호는 이 비교 순서를 따른다.

|후보|선정 근거|25 mm 굽힘 참고 하중 (N)|최소 작은 footprint 대비 겹침|진단 조건을 만족한 계면 수|
|---|---|---:|---:|---:|
|1|좁아지는 끝 연결부|1.836|95.274%|155|
|2|좁아지는 끝 연결부|2.104|95.062%|166|
|3|좁아지는 끝 연결부|2.220|94.857%|173|
|4|좁아지는 끝 연결부|2.379|94.692%|173|
|5|국부 단면 감소|4.221|92.948%|71|
|6|국부 단면 감소|4.547|96.448%|85|

네 끝 연결부가 여섯 후보 안에 남고, 이전에 우선되던 해상도 제한 고립 조각이 이 목록을 지배하지 않는다. 여섯 후보 모두 국부 선언 접촉 진단은 완료됐고, 해당 조건에서 선언 높이 간격·반복적인 겹침 손실 관찰은 없었다. 용융 접합강도는 모두 `UNMEASURED`이고 층간 파단하중은 미산출이다. 약 95%의 겹침을 실제 접합 양호나 층분리 부재로 해석할 수 없다. 관찰된 끝 파손 경험도 정량 하중 실측으로 바꾸지 않았다.

### 캐시와 보고서 검증

캐시는 원본 해시·선택 구성원·기하/단면/접촉 모델 버전·후보의 위치와 단면 창·끝 의미·해상도 품질을 검사한다. 완전한 입력 바이트와 모델 기록 수, 유한한 숫자, 면적과 단면계수의 상위/상세 값 일치, 후보 절단 위치, 단면 창, 관성 텐서와 방향도 검사한다. NaN·무한대뿐 아니라 유한한 수치라도 정합성 검사에 실패하면 완전한 단면이나 하중으로 표시하지 않는다.

후보의 표시 순서는 형상 식별에서 제외하되 모든 의미 행과 중복 개수는 보존한다. 실제 여섯 후보의 기하 순서와 하중 순서 양쪽에서 같은 단면·접촉 캐시가 검증됐다. 소재 참고값이 없어지면 기하 순서로 복원하며, 소재·원본·plate·단면 창이 바뀌거나 일치하는 참고 결과가 없으면 과거 하중 순위를 유지하지 않는다. 보고서 이미지 캐시에는 재정렬 후 첫 후보 레이어도 포함한다.

운영 캐시 이전은 이미 완료한 동일 원본 스캔의 결과를 재사용했다. 이전 순서 의존 fingerprint를 검증한 뒤 순서와 무관한 형상 fingerprint만 갱신했으며, 접촉·단면 trace의 의미는 바꾸지 않았다. 원본 해시·선택 구성원·버전·엄격한 검사와 복구 가능한 이전 파일 쌍을 확인했다. **이 이전은 새 원본 전수 스캔이 아니다.**

HTML과 PDF는 후보 번호·이유·참고 하중·접촉 진단을 공유한다. HTML의 저장 비용 행 7개 유지와 보고서 생성 후 저장 견적 불변 검사가 통과했다. 과거 비용·에너지 결과는 저장 당시 엔진 기준으로 남고, 현재 보고서 환경 및 소재·하중 재계산의 출처는 따로 표시한다. 소재 참고값과 하중이 모두 없는 경우에도 실제 PDF 생성 회귀에서 끝 연결부 이유, 접촉 수치와 미측정 접합강도 문구가 남는 것을 확인했다.

최종 생성 PDF는 A4 세로 7쪽, 199,256바이트이며 SHA-256은 `0d0d100e5c0b22a731527c3c41c83b2f8fb525948f084e85805060771aa72bf9`이다. 실제 파일의 해시·바이트 수·쪽 크기·필수 문구를 독립 확인하고 7쪽 모두 다시 렌더링해 시각 검토했다. 표·이미지 잘림, 문자 겹침과 깨진 한글이 관찰되지 않았다. 원자료 표의 33.36/55 MPa, 0.85 적용 범위 문구, 여섯 후보와 층간 접촉 진단이 유지됐다.

### 검증 범위와 배포 식별

|검사|결과와 범위|
|---|---|
|공개 강도 엔진 전체 회귀|193개 통과. 끝·캡·좌우 반사·축 변경·다물체·해상도·단면·접촉·미산출 순서 복원과 원자료/여유계수 분리 포함.|
|공개 견적 엔진 전체 회귀|45개 통과. 명시 모델 시간·준비 에너지 분리와 미확정 시간 범위 방어 포함.|
|최종 호스트 통합 컨테이너 회귀|395개 통과, 6개 건너뜀, 138개 subtest 통과, 167.41초. 의존성 사용 중단 예고 경고 2개.|
|건너뛴 검사 보완|Node 관련 소재·근거 표시 3개와 HA bridge 재시작 3개를 Windows에서 별도로 실행해 6개 모두 통과. 컨테이너의 skip이 사라졌다고 표시하지 않는다.|
|PDF·복원·접힘 검증|관련 PDF 레이아웃 7개 통과. 무소재 PDF, 저장 참고값 보류, 원자료 유지, 기본 접힘과 펼침 유지도 회귀 검증.|
|브라우저 코드 회귀|9개 JS 회귀 파일 통과. 하중 표시·소재 변경·지연 응답·원본/plate 불일치 방어 포함.|
|공개 근거 형식|10개 검사 통과. Windows stdin 처리 수정은 검증 코드에 한정.|
|배포 서비스|API·분석·뷰어·작업자 4개 서비스의 실제 이미지 ID·버전·출처 해시 일치, native scanner 사용, 실행 중·OOM 종료 없음·재시작 횟수 0 확인. 시점 검사이며 장기 안정성 시험은 아니다.|

네 서비스의 호스트 버전은 `0.5.13-material-reference`, 엔진 버전은 G-code `0.26.0`, strength `0.18.0`, quote `0.13.0`이다. 배포 강도 계산 소스는 `e5cee3bf13c68ec8e253d372ebd297d36e240b8b`, 견적 계산 소스는 `1178ba904a7c30cca7f861dcabdb36be997eb80e`다. 최종 이미지 식별자는 `sha256:fdfb11642a3c6c78b5edbd30300992bc1647aa58bbef68894a17f9d64df980aa`이다. 이 식별자는 계산 소스와 배포 이미지의 재현 기준이며 물리적 정확도 등급이 아니다.

### 성능과 남은 검증

같은 Windows 재현에서 외형 후보 계산은 2.141초, 단면과 접촉의 원본 공동 스캔은 30.246초였다. 이전 단면 계산 기록 24.666초에 접촉 검사가 추가된 측정이며 속도 향상 근거가 아니다. 단면·접촉 작업자 artifact는 약 1.19 MB, 접촉 표시 요약은 약 55 KB였다. 0.206초의 운영 뷰어 API 측정은 이미 준비된 캐시의 응답이며 냉간 재분석이나 사용자 전체 대기 시간 벤치마크가 아니다.

소프트웨어·배포 검증과 물리적 실증은 구분한다. 제품·공정·면적·방향·fixture가 일치하는 최초 균열 위치, 하중–변위 원자료, 반복 수와 분산이 아직 필요하다. 기존 내부 0.85 여유 계수도 이번 회귀로 실증 보정되지 않았다. 계면 열림·미끄럼·찢김, 노치/균열 성장, 충격·피로·크리프·좌굴과 부품 전체의 최초 파손 순위를 해결하거나 정확도·속도 향상률을 입증한 릴리스로 표시하지 않는다.

## English

**Status: software and deployment verification complete.** Final provenance, container regressions, desktop browser behavior and PDF output received independent review. This is a scoped release receipt, not certification of physical fracture accuracy or every device layout.

Validation date: 2026-10-03. This record covers software regressions, reproduction of an anonymized 464-layer input, and deployed-output consistency for `print-strength-engine 0.18.0`, host `0.5.13-material-reference` and quote engine `0.13.0`. **It does not validate first-fracture locations or breaking-load accuracy.** Literature, design decisions and missing material properties are recorded in the [integrated redesign evidence](weakness-research-redesign-20261003.md). User files, source geometry, quoted prices, private addresses and identifiers are excluded.

### Separate raw data, the internal margin and display state

Manufacturer directional properties are preserved while a separate load-scenario input is derived. For example, raw XY 33.36 / Z 55 MPa stays unchanged in material displays and process evidence; only X/Y 28.356 / Z 46.75 MPa, after applying the internal 0.85 margin once, reaches load scenarios. The factor is neither an empirical correction nor a validated safety factor. Reports, the viewer and user-defined load calculations consume the same separation. Restoration without material metadata withholds saved material and load-reference values.

Production Chrome confirmed that directional references and official properties start collapsed while the candidate summary stays visible. Raw X/Y 33.36 / Z 55 MPa, separate margin application and preservation of a user-opened reference panel after unit changes were checked. Actual desktop client/scroll widths were both 1905 px; cards did not overlap and no console errors were observed. The provider ignored responsive width overrides, so **mobile and narrow-screen validation are not claimed.**

The quote engine distinguishes model-only and preparation-inclusive durations. Valid explicit model time takes precedence for average printing-power integration; matched historical preparation energy is added once. Missing model time retains a historical-difference/unresolved duration basis, while unusable supplied model time also produces a diagnostic. Ambiguous scopes and manual duration mismatches do not gain an original-model-time override. Accessory/drying energy already included in the meter total is not added again. A read-only check in the deployed API confirmed this separation with current telemetry, without changing saved quotes, HA settings or power state. It is not direct metering of the proposed job.

### Implemented contract

The envelope screen collapses equivalent long body buckets and retains terminal connections and local section reductions. It evaluates interior terminal regions rather than vanishing free caps. Abrupt-transition thresholds and root windows are declared geometric policies, not calibrated fracture laws. Voxel components are not source-object identities; resolution-limited fragments do not enter compatible numerical reference-load ordering. A selected root is not an identified attachment or fixture.

One original model-road stream feeds both local section cuts and adjacent-layer declared-footprint intersections. Support and auxiliary roads are excluded. Missing or invalid model-road dimensions, nonplanar roads, budgets and incomplete scans retain withholding reasons. Adaptive declared layer intervals are used; inconsistent intervals at one plane do not establish a complete interface.

Reference bending order requires compatible model, single material tool, stress-area definition and transfer assumptions under the same explicit 25 mm static moment arm. The 10/25/50 mm arms are scenarios. Transferring coupon normal stress to the declared net section and treating road fragments as a perfectly bonded homogeneous continuum remain unverified. `UNKNOWN` source area basis stays unknown. Fracture energy/toughness is not replaced with tensile MPa, and overlap is not a strength multiplier.

Contact qualifiers distinguish small caps, first/last interfaces, Z crop boundaries, XY clipping, two-sided depth, ordinary footprint growth/shrinkage and repeated overlap loss. Full traces remain in the worker artifact; compact arrays retain every observation kind/count even when only 32 observation rows are sent. Neither 100% overlap nor `COMPLETE` establishes actual bead contact or weld strength.

### Anonymized reproduction

Source SHA-256: `373f78b503cbd4ce172bc29e6867e064044ca0316457c716a0fd944e50af0473`. The selected member was read through 51,010,921/51,010,921 bytes and 1,986,902 lines, containing 627,302 model-road records. Scan and declared geometry were complete; rejected records and excluded/capped arcs were zero. These flags establish input coverage, not measured adhesion or a complete part load path.

|Candidate|Reason|25 mm bending reference (N)|Minimum overlap / smaller footprint|Qualifying interfaces|
|---|---|---:|---:|---:|
|1|Tapered terminal connection|1.836|95.274%|155|
|2|Tapered terminal connection|2.104|95.062%|166|
|3|Tapered terminal connection|2.220|94.857%|173|
|4|Tapered terminal connection|2.379|94.692%|173|
|5|Local section reduction|4.221|92.948%|71|
|6|Local section reduction|4.547|96.448%|85|

The four terminal regions remain among six candidates. Previous geometry candidates 3/4 exchange order under the reference-load comparison, and presentation numbers follow that condition. All six have complete declared-contact diagnostics, with no qualifying declared-gap or repeated-overlap-loss observations. Weld strength remains `UNMEASURED` and interlayer failure loads are unavailable. Approximately 95% overlap does not establish sound welding or exclude delamination. The qualitative end-failure observation was not converted into a measured force label.

### Cache and report verification

Cache validation checks source/member, geometry/section/contact model versions, semantic candidate geometry and terminal/quality metadata, complete byte/record coverage, finite values and cross-field consistency. Area/modulus, cut stations, crop bounds, inertia and directions are checked. Metrics failing these consistency checks, including finite values as well as NaN/infinity, cannot become completed sections or displayed loads.

Canonical candidate identity preserves all semantic rows and duplicate counts while ignoring presentation order. Both geometric and load-reordered lists reuse the same validated evidence. Removing material reference restores geometric order; pending or unmatched material/source/plate/window evidence clears old load ranking. Figure identity includes the first layer after reordering.

The production cache migration reused the completed scan of the same source. The legacy signature was checked and only the order-independent fingerprint changed; section/contact trace semantics were unchanged. Source/member/version guards, strict validation and a restorable artifact pair were checked. **This was not a fresh full-source scan.**

HTML/PDF share candidate numbers, reasons, reference loads and contact diagnostics. All seven saved HTML cost rows remained, and saved-estimate immutability checks passed. Historical cost/energy values retain their saved engine basis; current report environment and material/load recalculation provenance are disclosed separately. A real-PDF regression with no material reference and no numerical capacities retains terminal/contact evidence and unmeasured-weld language.

The final PDF has seven A4 portrait pages and 199,256 bytes; SHA-256 is `0d0d100e5c0b22a731527c3c41c83b2f8fb525948f084e85805060771aa72bf9`. File hash, size, page geometry and required text were independently checked; all seven pages were rendered and visually re-inspected. No clipped tables/images, overlapping text or broken Korean glyphs were observed. Raw 33.36/55 MPa, the 0.85 scope statement, six candidates and contact diagnostics remained.

### Software and deployment scope

The public strength and quote suites passed 193 and 45 tests respectively. The final host container suite passed 395 tests and 138 subtests, with 6 skipped, in 167.41 seconds; two dependency deprecation warnings were recorded. All six skipped checks—three Node material/evidence checks and three HA bridge restart checks—passed separately on Windows; they remain skips in the container result. Seven PDF layout checks, nine JS regression files and ten public-evidence-format checks passed. No-reference PDF evidence, missing-metadata withholding, raw material preservation and collapsed/open display states were also covered.

Actual image IDs, versions and source hashes matched across API, analysis, viewer and worker. Each was running with native scanners, no OOM termination and zero restarts. This is a point-in-time check, not long-term reliability testing. Host: `0.5.13-material-reference`; engines: G-code `0.26.0`, strength `0.18.0`, quote `0.13.0`. Strength source: `e5cee3bf13c68ec8e253d372ebd297d36e240b8b`; quote source: `1178ba904a7c30cca7f861dcabdb36be997eb80e`. Final image: `sha256:fdfb11642a3c6c78b5edbd30300992bc1647aa58bbef68894a17f9d64df980aa`. These identify reproducible code/deployment, not a physical validation rating.

The Windows reproduction took 2.141 seconds for envelope selection and 30.246 seconds for the shared section/contact source pass. The older section-only record was 24.666 seconds; added diagnostics do not establish a speedup. Worker evidence was approximately 1.19 MB and compact contact summaries 55 KB. A 0.206-second warm viewer API response is not a cold analysis or end-to-end latency benchmark.

Matched product/process/area/direction/fixture tests, raw load–displacement curves, observed crack initiation and replication/dispersion remain necessary. The existing internal 0.85 margin was not calibrated by these regressions. Interface opening/sliding/tearing, crack/notch growth, impact, fatigue, creep, buckling and whole-part first-fracture order remain unsolved; no physical accuracy or speedup claim is made.
