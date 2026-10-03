# Cura role regression validation

## 한국어

실제 구형 Cura 원본의 `WALL-OUTER` 경로가 외곽선 추출에서 누락되는 통합 문제를 확인했습니다. 공정 집계는 [공식 Cura feature 표기](https://github.com/Ultimaker/Cura/blob/main/plugins/GCodeReader/FlavorParser.py)의 정확한 네 가지 별칭을 보존합니다: `WALL-OUTER`→외벽, `WALL-INNER`→내벽, `FILL`→인필, `SKIN`→솔리드. 공정 자료 버전은 `LOCAL_COMMANDED_PROCESS_V2_CURA_FEATURE_ROLES`입니다. 호스트는 지원·보조 경로를 모델 집계에 전달하기 전에 제외해야 합니다.

새 공개 시험 2개는 별칭별 경로 길이와 역할, 임의 유사 문자열·보조 역할의 비승격을 확인합니다. NumPy 2.2.6·Shapely 2.1.2에서 공개 시험 241개가 통과했습니다. 이 수에는 아직 전체 코퍼스 결과로 교체하지 않은 pilot fixture 시험 4개가 포함됩니다. 코퍼스 전체 완료나 물리 파손 예측 정확도를 주장하지 않습니다.

코퍼스는 소프트웨어 회귀 사례를 제공하며 실측 강도 학습 자료가 아닙니다. 명령 체적·온도 설정·미세 높이를 실제 비드, 접합면 온도, 용접강도나 보정계수로 바꾸지 않습니다. 누락된 실험 증거와 소재 식별은 계속 보류합니다.

## English

A real older Cura source exposed an integration omission: explicit `WALL-OUTER` roads did not enter the host contour extractor. Process accounting now preserves four exact official aliases: `WALL-OUTER`→outer wall, `WALL-INNER`→inner wall, `FILL`→infill and `SKIN`→solid. Its descriptor version is `LOCAL_COMMANDED_PROCESS_V2_CURA_FEATURE_ROLES`; the host must exclude support and auxiliary roads before forwarding model process records.

Two new public tests verify role-specific path accounting and reject promotion of similar or auxiliary names. All 241 public tests passed with NumPy 2.2.6 and Shapely 2.1.2, including four uncommitted pilot-fixture tests awaiting replacement from complete current results. This count is not whole-corpus completion or physical failure-prediction accuracy.

The corpus supplies software regressions, not measured strength-training labels. Commanded volume, temperature settings and thin declared geometry do not establish measured beads, interface temperatures, weld strength or fitted coefficients. Missing experimental evidence and unresolved material identity still withhold estimates.
