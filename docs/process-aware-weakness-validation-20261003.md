# 공정 정보를 연결한 취약부 엔진 검증 / Process-aware weakness validation

## 한국어

검토일 2026-10-03. 기존 끝 연결부·국부 단면·층간 접촉 엔진에 원본 G-code의 명령 공정 정보를 연결했다. 논문 전 세계 전수 조사나 실측 파단 정확도 인증이 아니다. 기존 완료 원본 검증은 반복하지 않았고 새 공정 정보 수집만 한 번 수행했다.

### 적용한 계산과 근거

- 외벽·내벽·인필·솔리드·브리지 경로의 명령 체적을 따로 집계한다. 벽 수·실제 경로 위치·선폭·층높이·인필 패턴은 road union에 이미 반영되므로 벽 수나 인필 배수를 다시 곱하지 않는다. G-code에 개별 내벽 패스 번호가 없으면 합계만 표시하며 설정 벽 수로 나누지 않는다.
- M200 체적 E, M220 명령 속도, M221 툴별 유량, 명시적 리트랙션 회복, 노즐·베드·챔버·팬 명령을 처리한다. 비활성 물리 히터 명령을 논리 소재 툴 온도로 바꾸지 않으며 불명 매크로의 숨은 상태는 보류한다. 후행 직경 설정은 같은 성공 분석·파일 해시·3MF member가 확인된 경우에만 시드로 사용한다.
- 선언 직사각 경로 단면과 `명령 체적/(경로 길이×선언 층높이)`의 등가 직사각 단면을 별도로 계산한다. 등가 폭은 선언 폭을 넘기지 않는다. 축방향과 굽힘 각각 두 조건부 값의 낮은 값을 사용하며 두 모드가 서로 다른 단면을 선택할 수 있다. 이는 실측 비드·파단하중·안전 하한이 아니다.
- 둥근 슬라이서 비드의 정상 체적은 직사각형보다 작을 수 있다. 이를 압출 손실이나 층간 접합 계수로 판정하지 않는다. 국부 체적은 층높이가 창과 교차하는 경로 중심선의 길이로 배분한 명령량이며 정확한 3D 창 내부 실측 체적이 아니다.
- 온도·속도·냉각은 국부 범위와 알려진 길이 커버리지를 표시한다. 명령 온도는 실제 접합면 온도가 아니다. 보편적 온도/벽/유량 강도 계수는 적용하지 않았으며 제조사 원자료 MPa는 유지한다. 내부 0.85는 별도 하중 입력에 한 번만 적용한다.

[열이력·층간 파괴 원문 및 공개 시편 검토](process-thermal-evidence-20261003.md), [벽·유량·공개 500개 조건 평균 감사](process-walls-flow-evidence-20261003.md), [설계](superpowers/specs/2026-10-03-process-aware-weakness-design.md).

Nesheim의 공개 데이터 108개 숫자 시편 행과 8개 파일 해시를 검증했지만 3 mm/s 제외 기준과 열 요약 수식의 불일치가 있어 해당 조건을 보정에 쓰지 않는다. Belei의 동일 베드·층높이 비교에서 노즐 240→280°C 효과는 속도 30/80 mm/s에 따라 감소/증가로 역전된다. Marković의 ABS 유량 증가도 단조적인 강도 증가가 아니다. 런타임에는 조건·분산·미확인 분모를 붙인 비교 자료만 추가했고 승인된 전이 모델은 만들지 않았다.

### 검증 및 배포 기록

신규 회귀는 곡선 전체 원, 0/미확인 체적, 비평면 이동, 창 바깥 중심선의 경로 폭, 불명 치수, 비활성 히터, 단위·유량 명령, 매크로·체크포인트, 축/굽힘 별도 선택과 캐시 출처를 포함한다. 원본 새 공정 수집에서 6개 후보의 두 단면이 모두 계산되었고 원본 해시·전체 바이트·캐시 계약이 일치했다. 새 단면으로 기존 굽힘 참고 하중보다 약 1–2% 낮아졌다. 이것은 예측 정확도 향상율이 아니다.

선택적 공정 수집은 추가 비용이 있다. 순수 Python 실제 원본 수집 46.177초이며 이전 기하·접촉 수집은 30.246초였다. 동일 코드/환경을 통제한 전후 성능 실험은 아니므로 성능 개선율로 사용하지 않는다. 기본 숫자 스캐너와 기존 모션 콜백은 유지하며 한 번 만든 공정·단면 캐시를 웹/PDF에서 재사용한다. 실제 생산 native 성능은 이 수치로 추론하지 않는다.

### 최종 배포 확인

| 확인 항목 | 결과와 범위 |
| --- | --- |
| 릴리스 | 강도 **v0.19.0**, G-code **v0.27.0**, 가격 v0.13.0, 통합 앱 v0.5.14-process-context. 강도 코드 개정 19회/업데이트 18회, G-code 개정 27회/업데이트 26회이며 정확도 인증 횟수가 아니다. |
| 공개 엔진 | 실제 배포 이미지의 네이티브 스캐너를 로드한 상태에서 강도 231개, G-code 65개 통과; 실패·skip 없음. |
| 통합 앱 | 최종 Docker suite 407개 통과, 148개 subtest 통과, 6개 환경 제외, 178.56초. 제외된 Windows 작업 재시작/Node 브라우저 검사 6개는 로컬에서 모두 통과했다. 별도 JavaScript 회귀 파일 10개도 통과했다. |
| 수정 후 재검증 | 새 ABS 문헌 비교를 막던 이전 테스트 가정과 공정 정보 없는 구형 캐시 fixture를 수정했다. declared/contact가 보류되더라도 volume만 완료인 캐시는 전체 원본의 바이트·레코드·기하 증명을 요구한다. 누락·0·bool·불일치 증명을 거부했다. |
| 독립 검토 | 연구/파서/통합 구현 이후 한 독립 검토자가 단면·단위·캐시·원본 범위·표시를 검토했다. 마지막 volume-only 증명 분기도 재검토를 통과했다. |
| 실제 원본 | 새 공정 정보 수집 1회에서 51,010,921 바이트 전체와 모델 모션 627,302개를 확인했다. 6개 후보 모두 체적 단면을 계산했다. 운영 캐시로 검증한 쌍을 옮기고, 이후 기존 분석 조회는 재스캔 없이 0.349초에 완료했다. 이 시간은 초기 분석 성능이 아니다. |
| 운영 배포 | API·분석·뷰어·저장 4개 서비스의 이미지/소스/버전 일치, 네이티브 모듈 로드, 재시작 0회, OOM 없음. 이미지 `sha256:379479d4b9c17e463bc41106616c129c5ce5190abc149cb977c5f3ab45bf6a93`. 점검 시점의 상태다. |
| 웹 | 실제 기존 분석의 새 하중과 국부 온도·속도·팬·역할 체적·단면 선택을 확인했다. 상세 12개는 기본 닫힘, 선택 상세 펼침 정상, 가로 넘침 및 콘솔 오류 없음. 실제 데스크톱 화면 범위다. |
| 상세 보고서 | 운영 API에서 생성한 A4 PDF 10페이지 전부 Poppler로 렌더링해 확인했다. 원자료/예상 하중/공정 정보/취약 위치 이미지/버전·처리 안내 정상, 문자가 페이지 경계를 넘지 않음. HTML 비용 행과 저장 견적 해시는 유지했다. 저장 당시 엔진과 보고서 생성 엔진을 구분한다. |

강도 소스 커밋: `ded36d8810f7e882789939b7c1b85cd8a5e72ffe`. G-code 소스 커밋: `5e7df32eb7870a7947efcf3f20dc42b35edd7133`. 문서·버전 메타데이터 커밋은 코드 개정 수를 추가하지 않는다. 사용자 형상·견적·전력 데이터와 접속정보는 이 공개 기록에 포함하지 않는다.

남은 실증 경계: 실제 부품의 최초 파단 위치, 허용하중, 층간 용융 강도, 접합면 온도·열이력·국부 재방문 시간, 제조사/로트별 wall-flow 보정은 검증되지 않았다. 논문 응력 분모와 타깃 순단면의 전이도 미검증 가정으로 남는다. 계산 가능 범위를 확장한 소프트웨어 검증이며 파단 예측 정확도나 안전 하한을 인증하지 않는다.

## English

This release connects source-motion process context to the existing terminal-root, section and interlayer-contact pipeline. It is a targeted primary-evidence review, not an exhaustive literature census or empirical part-failure certification.

Role volumes are separate aggregates, never divided by configured wall count. M200/M220/M221, explicit retraction recovery and thermal/fan commands retain units and uncertainty. Physical heater targeting is not logical-material targeting. Diameter seeding requires the linked successful analysis, source checksum and selected archive member.

Declared rectangular road sections and capped command-volume-equivalent rectangles remain distinct assumptions. Axial and bending comparisons independently retain the lower conditional reference; their selected geometry can differ. Rounded normal slicer beads prevent interpreting smaller rectangular-equivalent volume as underextrusion. Cropped-centerline allocation is not measured 3D-window volume.

Primary experiments demonstrate process interactions, non-monotonic flow effects and unresolved grade/conditioning/area provenance. Four additional runtime comparison entries retain these limits; no universal multiplier or approved transfer model was created. Manufacturer MPa remains unchanged, with the existing internal margin applied only once to separate load inputs.

The original source was collected once for the new process facts. All six volume scenarios and the exact source/cache contracts passed. The 1–2% lower conditional bending references are not an accuracy-improvement claim. Additional collection has a cost: the pure-Python source run took 46.177 s versus a historical 30.246 s geometry/contact run; these are not a controlled performance experiment or native production benchmark. Cached results are reused by web/PDF.

### Final release receipts

Strength **v0.19.0** and G-code **v0.27.0** are deployed with host v0.5.14-process-context; quote remains v0.13.0. The code revision counts are 19 and 27, not accuracy ratings. Source commits are `ded36d8810f7e882789939b7c1b85cd8a5e72ffe` and `5e7df32eb7870a7947efcf3f20dc42b35edd7133`.

The production image passed 231 strength and 65 G-code public tests with its native scanner loaded. Final host integration passed 407 tests and 148 subtests in 178.56 s; six environment exclusions passed separately on Windows/Node. Ten JavaScript regression files also passed. Stale ABS-literature/cache fixture assumptions were updated without weakening the runtime contracts. A complete volume section now requires full-source proof even when declared sections and contacts are withheld. Missing, zero, boolean and mismatched proof values are rejected. One independent final reviewer approved the integrated calculation and the last proof branch.

One necessary source collection covered all 51,010,921 bytes and 627,302 model motion records; all six volume scenarios were complete. Its validated cache pair was installed in production without another source scan. Reopening the existing analysis took 0.349 s through cache reuse; this is not initial-scan performance. Four services matched the deployed image/source/version and native modules, with zero restarts or OOM at inspection. Image: `sha256:379479d4b9c17e463bc41106616c129c5ce5190abc149cb977c5f3ab45bf6a93`.

The actual desktop browser showed the new loads, role volumes, command ranges and separate geometry assumptions. Twelve disclosures started closed; expansion worked, with no horizontal overflow or console errors. The production A4 detailed PDF was rendered with Poppler and all ten pages visually reviewed, without page-boundary text overflow. HTML cost rows and the saved estimate hash remained unchanged. Stored-engine provenance and current report-generation versions are separate.

These receipts validate implementation and delivery, not first-fracture location, allowable load, molecular weld strength, measured interface temperature, local return/thermal history, product/lot-specific wall-flow calibration, or the coupon-stress-to-net-section transfer. No user geometry, quotes, telemetry or credentials are published here.
