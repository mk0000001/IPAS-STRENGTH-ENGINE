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

최종 컨테이너·버전·웹·PDF 및 독립 검토 결과는 완료 후 이 기록에 추가한다.

## English

This release connects source-motion process context to the existing terminal-root, section and interlayer-contact pipeline. It is a targeted primary-evidence review, not an exhaustive literature census or empirical part-failure certification.

Role volumes are separate aggregates, never divided by configured wall count. M200/M220/M221, explicit retraction recovery and thermal/fan commands retain units and uncertainty. Physical heater targeting is not logical-material targeting. Diameter seeding requires the linked successful analysis, source checksum and selected archive member.

Declared rectangular road sections and capped command-volume-equivalent rectangles remain distinct assumptions. Axial and bending comparisons independently retain the lower conditional reference; their selected geometry can differ. Rounded normal slicer beads prevent interpreting smaller rectangular-equivalent volume as underextrusion. Cropped-centerline allocation is not measured 3D-window volume.

Primary experiments demonstrate process interactions, non-monotonic flow effects and unresolved grade/conditioning/area provenance. Four additional runtime comparison entries retain these limits; no universal multiplier or approved transfer model was created. Manufacturer MPa remains unchanged, with the existing internal margin applied only once to separate load inputs.

The original source was collected once for the new process facts. All six volume scenarios and the exact source/cache contracts passed. The 1–2% lower conditional bending references are not an accuracy-improvement claim. Additional collection has a cost: the pure-Python source run took 46.177 s versus a historical 30.246 s geometry/contact run; these are not a controlled performance experiment or native production benchmark. Cached results are reused by web/PDF.

Final integration, deployment, independent-review and presentation receipts will be added after completion.
