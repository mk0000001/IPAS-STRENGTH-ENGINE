# 층간 접촉률의 부동소수점 경계 회귀 검증

## 한국어

실제 원본 계산에서 완전한 겹침의 접촉률이 부동소수점 오차로
`1.0000000000000002`가 됐다. 캐시 문맥 검사는 이를 허용했지만 취약부
계산은 거부해 같은 접촉 기하가 서로 다른 상태로 표시됐다.

공개 예시는 상한 면적을 1로 정규화한 수치 경계 재현이다. 상한 1에 대해
`1.0000000000000002`를 반환하면 1로 정규화한다. 이 단위 예시는 실제
사용자 부품의 단면적·형상이나 측정된 접합면이 아니다.

계산기는 면적 규모의 64 ULP 이내인 작은 오차만 기하 경계로 정규화한다.
상한·하한·작은 면적 기준 접촉률과 내부 접촉률 모두 정규화된 면적으로
계산한다. 더 큰 초과, 비유한값과 유의미한 음수 면적은 계속 보류한다.
캐시의 비율도 [0, 1]이어야 하며 겹침 면적은 접촉 면적의 상한을 넘지
않아야 한다. 과거의 비정규 접촉 문맥을 재사용하지 않도록 모델 버전도
변경했다.

시험은 최소 익명 스칼라 재현과 합성 단위 사각형의 수치 오차, 생산자·캐시·
취약부 읽기 결과의 일치, 실제 경계를 벗어나는 값의 거부를 확인한다.
완전한 겹침은 기하 근거이며 용융 접합강도는 미측정 상태로 남는다.
층간 파단하중은 실측 근거 없이 생성하지 않는다. 이 산술 오차 범위는
물리적인 여유계수·강도 보정계수나 실증 정확도 검증이 아니다.

전체 원본 대조의 결과는 [통합 검증 기록](full-corpus-validation-20261003.md)에 정리한다.

## English

A fresh full-source assessment emitted a complete-overlap ratio of
`1.0000000000000002` because of floating-point roundoff. The cached descriptor
validator accepted it, while the weakness reader rejected the same contact.

The public boundary illustration normalizes the area bound to 1 and maps
`1.0000000000000002` back to 1. This unit illustration is not a user's measured
section, geometry or polymer interface.

The producer now normalizes overlap area to its geometric bounds only within
64 floating-point steps at the area scale. Upper, lower, smaller-footprint and
interior ratios derive from bounded areas. Larger excesses, nonfinite values
and materially negative areas withhold the result. Cached ratios must be in
[0, 1], and overlap areas must not exceed their footprint bounds. The contact
model version changes so previous noncanonical descriptors are not reused.

Tests preserve the anonymous scalar reproduction, emulate roundoff with unit
squares, verify descriptor and weakness readers agree, and reject materially
invalid intersection and cached ratios. Complete overlap remains geometric
evidence; weld strength stays unmeasured and interlayer failure load stays null.
The arithmetic bound is not a physical margin, fitted strength coefficient or
empirical validation.

Whole-source reconciliation is recorded in the [integrated validation record](full-corpus-validation-20261003.md).
