# Fresh corpus contact roundoff regression

A fresh full-source assessment reported footprint areas 15.743535805252982 and
15.743535800771948, with intersection area 15.743535800771951. The intersection
exceeded the smaller footprint by two representable floating-point steps,
producing a ratio of 1.0000000000000002. The cached descriptor validator accepted
it, while the weakness reader rejected the contact.

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
