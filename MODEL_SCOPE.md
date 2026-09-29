# Strength model scope

[한국어](#한국어) · [English](#english)

## 한국어

이 패키지는 형상 선별, 소재 참고값, 하중을 구분한다.

`weakest_layer_candidate`는 관측한 층 높이로 모델 압출 체적을 나눈 값을 사용해 내부 Z 경계 후보를 선별한다. 이는 메모리 사용량을 제한한 비교 지표이며 실제 단면 합집합이나 하중 지지능력이 아니다. 힘의 방향, 지지·구속조건, 실제 유효 단면의 재구성 없이는 출력물 전체의 최약점을 확정할 수 없다. `weakest_section`은 독립적으로 검증된 단면·국소 허용응력과 지정 축력·굽힘 모멘트를 받아 비례 하중에서 처음 한계에 도달하는 위치를 반환한다.

제공된 연구 보고서 세 편은 설계 입력으로 검토했다. 보고서의 정확도 주장(±6%, ±10–25%, 2–5%)은 동일한 시험 조건이 없으므로 상호 비교하거나 합칠 수 없다. `cos²45°≈0.707`이라는 산술 주장은 틀리며 올바른 값은 0.5다. 미보정 온도·접합·패턴 계수는 암묵적으로 적용하지 않는다. 예측 정확도를 주장하려면 독립 시험편의 측정 자료가 필요하다.

## English

This package separates geometry screening from material references and loads.

`weakest_layer_candidate` ranks interior Z interfaces by deposited model filament volume divided by observed layer height. This is a bounded-memory screening proxy, not a topological slice union or load capacity. Without force direction, supports/restraints and real net-section reconstruction, a global weakest part cannot be proven. `weakest_section` accepts independently validated sections, local allowable stress and a specified axial force/bending moment, then returns the first local limit for proportional loading.

The three user-supplied research reports were reviewed as design inputs. Their numerical accuracy claims (±6%, ±10–25%, and 2–5%) are mutually incompatible without matching test fixtures. An arithmetic assertion that cos²45°≈0.707 is incorrect (it is 0.5). Their uncalibrated temperature/healing and pattern coefficients are not silently applied. Independent specimen measurements are required before claiming prediction accuracy.
