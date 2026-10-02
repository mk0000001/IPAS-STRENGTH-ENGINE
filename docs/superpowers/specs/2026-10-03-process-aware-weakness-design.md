# 공정 요인을 연결한 취약부 분석 설계 / Process-aware weakness design

## 한국어

사용자는 기존 취약부 엔진을 신뢰 가능한 논문·실측자료로 다시 검토하고 온도, 벽 수, 벽별 압출량 등 여러 요인을 연결하기를 요청했다. 기존 통합 설계와 소재 원자료/예상 하중 분리는 유지한다. 범위는 기존 원본 경로→국부 단면→취약 후보→웹/PDF 흐름의 확장이다.

1. 명시적인 G-code 명령 상태를 원본 모션에 연결한다. 설정값·명령값·실측값은 서로 바꾸지 않는다. 비활성 히터 온도, 리트랙션 회복, M220/M221/M200, 논리적 소재 도구와 물리적 히터의 불명 매핑, 냉각 팬과 곡선을 구별한다. 기존 콜백 계약은 보존한다.
2. 각 후보 창에서 외벽·내벽·인필·솔리드·브리지의 경로 길이와 명령 압출 체적을 따로 수집한다. 내벽 합계를 설정 벽 수로 나누어 개별 벽 측정값처럼 표시하지 않는다. 출처가 확인되지 않은 직경·압출 모드·유량은 미확인으로 남긴다. 슬라이서 유량 비율을 E에 다시 곱하지 않는다.
3. 기존 선언 선폭/높이의 순단면과 명령 체적 환산 단면을 별도 조건부 기하 시나리오로 평가한다. 후자는 평면 직선 모션, 유효한 직경/체적 모드·유량 상태와 선언 높이가 있는 경우만 계산한다. 체적/길이/높이로 등가 직사각형 폭을 구성하고 선언 폭보다 넓혀 강도를 올리지 않는다. 이는 실제 비드·접합 형상 측정이나 안전 하한이 아니다. 불완전 입력에서는 기존 시나리오를 보존하고 새 시나리오의 불명 사유를 표시한다.
4. 온도·속도·팬·유량과 열 이력의 상호작용은 검토한 실험의 조건 및 응답 정의와 함께 제시한다. 다른 등급/노즐/벽/시험 방향의 단일 변수 비율을 곱하여 범용 강도 계수를 만들지 않는다. 실제 층 온도/복귀시간/분자 접합은 명령값으로 확정하지 않는다. 소재 원자료 MPa는 변경하지 않으며 내부 0.85는 하중 입력에만 한 번 적용한다.
5. 두 단면 결과, 국부 공정 커버리지, 공식 범위 불일치 및 근거가 부족한 파괴 모드를 한 평가에 연결한다. 비교 가능한 시나리오에만 수치 정렬을 적용하고, 서로 다른 공정 이력이 확정 파단 순위라는 인상을 주지 않도록 조건과 미계산 요인을 명시한다.
6. 단위·모드·도구·후행 메타데이터·압출 회복·곡선·창 잘림·캐시 변조를 검증한다. 연구자료 중복 계보, 평균/개별시편, 분산의 정의와 합성/실측을 구분한다. 새 지표 수집에 필요한 원본 스캔은 대상 파일 한 번만 수행한다. 기존 완료 자료를 학습 또는 반복 검증 명목으로 다시 읽지 않는다.

현재 완전한 실증 전이 모델을 새로 승인한다는 설계가 아니다. 독립 검토와 실제 배포·웹/PDF 검증 후 버전을 갱신한다. 사용자 파일·원자료·접속정보는 공개 저장소에 올리지 않는다.

## English

Extend the existing source-road/section/weakness/presentation pipeline with traceable commanded process context and a separate volume-equivalent section scenario. Preserve manufacturer MPa, existing callbacks and saved quote amounts. Collect role-specific extrusion and thermal/speed/fan context without inventing individual inner-wall labels or multiplying slicer flow again.

For supported planar linear roads, programmed volume divided by path length and declared height gives a conditional equivalent rectangular width, capped at declared width. It is neither measured bead geometry nor a guaranteed lower bound. Missing or unsupported evidence withholds only this added scenario. Commanded thermal context is not measured local substrate/weld temperature. Primary experiments constrain interpretation; their unrelated ratios are never multiplied into a universal material factor. Regression, independent review and live source/version/report verification precede release.
