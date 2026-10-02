# 강도·취약부 통합 설계 / Integrated strength and weakness design

## 한국어

목표는 국부 두께 후보와 하중 참고 계산의 모순을 제거하고, 끝 연결부와 층간 접촉 기하를 같은 분석 흐름에서 검사하는 것이다. 기존 정렬은 동일 두께에서 긴 구간과 많은 격자를 우선하여 짧은 끝 부위를 버렸다. 이를 실제 파손 순위로 사용할 수 없다.

1. 외형 검출은 물체별 얇은 영역·끝 연결부·단면 감소를 보존한다. 자유단의 마지막 둥근 캡은 전체 구조의 최소 파단부로 대체하지 않는다. 비교 단면과 표시 위치를 명시한다.
2. 원본 전체 G-code의 선언 선폭·층 높이로 국부 순단면과 인접 층 footprint 교집합을 재구성한다. 서포트·프라임 타워는 제외한다. 실제 비드 형상·용융 접합·층간 파괴에너지는 측정한 것으로 취급하지 않는다.
3. 통합 평가에서는 동일 25 mm 정적 굽힘 조건의 소재 참고 하중을 비교 가능한 후보끼리 비교한다. 미완료·복수 소재 강성 미확인·서로 다른 면적 정의는 묵시적으로 섞지 않는다. 기하 비교와 층간 진단은 별도의 근거를 남긴다.
4. 겹침이 충분해도 접합 강도 확인은 아니다. 확장·축소·레이어 진입·작은 끝 캡의 면적 변화만으로 층결합 불량을 선언하지 않는다. 접촉 비율을 임의의 MPa 감쇠 또는 파단하중 계수로 사용하지 않는다.
5. 웹·HTML·PDF는 같은 후보, 선택 이유, 참고 하중 및 접합 진단을 사용한다. 값과 번호가 달라지면 비교 기준을 표시한다. 실제 고정점·힘 방향·노치·균열·충격·피로가 미확인일 때 범용 '최초 파단 위치 확정'을 주장하지 않는다.

검증은 좁은 끝 누락, 둥근 캡 오선택, 균일 벽 중복, 다물체 분리, 겹침의 성장/축소, 단절, 원본 누락, 캐시 오염, 소재 변경, 보고서 표 보존을 포함한다. 제공 파일의 끝 파손 경험은 위치에 대한 관찰이며 정량 하중 측정으로 바꾸지 않는다. 새 연구의 계수는 제품·공정·시험법·면적 정의의 일치 또는 독립 검증 없이 적용하지 않는다.

## English

Integrate geometric candidate selection, complete-source local road sections, and adjacent-layer footprint diagnostics. Replace the length/ridge-count preference that suppresses short terminal features. Evaluate terminal connections rather than declaring a vanishing rounded cap the governing failure section.

Rank comparable completed candidates under the same explicit 25 mm static reference scenario, while retaining separate geometric and interlayer evidence. Declared-road overlap is not measured welding, toughness, or proof of a sound bond. Do not convert overlap or literature findings into an unvalidated universal fracture multiplier. Web, HTML and PDF must share the assessment and its limitations. Regression and independent review precede production deployment and release version updates.
