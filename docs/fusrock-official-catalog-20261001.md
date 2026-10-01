# FusRock 공식 소재 카탈로그 반영 / Official Material Catalogue Integration

[한국어](#한국어) · [English](#english)

## 한국어

### 적용한 공식 자료

2026-10-01에 FusRock의 [공식 소재 비교표](https://www.fusrock.com/fusrock/tools/comparison.html), 비교표 부트스트랩 데이터, [공식 제품 목록](https://www.fusrock.com/products), 각 제품의 공식 성능표와 제품 페이지를 확인했다. 비교표의 **46개 제품과 96개 비교 항목을 모두 구조화 스냅샷으로 보존**한다. 제품 페이지 40개를 제품과 연결했고, 제공된 공식 슬라이서 프로필, 색상 규격, 적용 분야, 출력·물리·열·기계 항목, 시험조건, 유량-온도 행렬 및 제품 페이지 권장조건을 사실 데이터로 저장한다. 빈 값은 추정해 채우지 않는다.

재생성 명령은 `python tools/update_fusrock_catalog.py --checked-date YYYY-MM-DD`다. 현재 부트스트랩 원문의 SHA-256은 `b5457f5b752185af22bc7b2db745bb1a9b365e479c06de5d65688e279233dcb0`이다. 생성 파일에는 광고 문구와 이미지를 복제하지 않고 계산과 식별에 필요한 사실·출처만 남긴다.

### 제품 식별과 계산 경계

- `FusRock_ABS_0.2 @BBL H2C`, `FusRock ABS-GF @QIDI Q2`처럼 활성 슬라이서 프로필이 공식 제품명 하나에 정확히 일치할 때만 제품을 선택한다.
- 여러 활성 프로필이 서로 다른 제품을 가리키거나 `ABS Plus`처럼 공식 등급과 정확히 일치하지 않으면 다른 FusRock 등급 또는 다른 제조사의 값을 대체 적용하지 않는다.
- 공식 기계값은 동일 시험상태의 비교 가능한 XY/Z 인장 파단 쌍이 모두 있을 때만 방향별 소재 참고값에 사용한다. 그 쌍이 없는 제품은 공식 출력·물리·열·기계 자료만 표시하고 방향별 MPa는 보류한다.
- 공식 출력 범위와 G-code의 노즐·베드·명령 속도를 비교해 범위 내/밖을 표시한다. 이 경고를 임의 강도 배율로 환산하지 않는다.
- 전체 공식 항목은 `fusrock_material_catalog.json`에 보존하고, 웹·PDF에는 판단에 필요한 핵심값과 공식 링크를 간결하게 표시한다.

### FusRock ABS에 실제 적용한 기준

공식 ABS 성능표가 같은 비열처리 시험조건에서 공개한 `Tensile Break Strength XY = 33.36 MPa`와 `Tensile Strength Z = 55 MPa`를 방향 쌍으로 사용한다. 시험조건은 0.4 mm 노즐, 250 °C 노즐, 100 °C 베드, 50 mm/s, 인필 100%, ±45° 인필이다. 기존 내부 여유계수 0.85를 한 번 적용한 표시 참고값은 X/Y 28.356 MPa, Z 46.75 MPa다. 이 계수는 실측 보정계수나 검증된 안전율이 아니다.

공식 제품 페이지 권장조건도 별도로 보존한다. ABS의 페이지 기준은 노즐 240–260 °C, 베드 100–110 °C, 챔버 밀폐 또는 60–80 °C, 팬 끔–30%, 속도 30–120 mm/s, 리트랙션 1–5 mm, 리트랙션 속도 1800–3600 mm/min, 70 °C에서 5–6시간 건조, FusFree S-Multi 서포트다. 비교표와 제품 페이지 값은 각 출처의 값으로 분리해 유지한다.

### 제외한 오해 가능 값

공식 원자료의 일부 필드는 이름과 수치의 물리적 의미가 맞지 않을 가능성이 있다. 예를 들어 ABS의 일반 `tensile_unannealed = 2201.74`는 강도라기보다 탄성률 규모이며, 별도 XY/Z 탄성률 항목과 중복될 수 있다. 원문 사실은 스냅샷에 보존하지만 방향별 강도 계산에는 `tbs_xy_unannealed`와 `ts_z_unannealed`만 사용한다. 제조사 시편값은 현재 부품의 인필, 벽, 접합, 노치, 고정조건과 하중 경로가 실증된 파단강도 또는 허용하중이 아니다.

### 구현 검증

- 공개 G-code/강도/가격 엔진 시험은 각각 36/107/22개 통과했다.
- 통합 이미지 시험은 261개 통과, 환경 조건에 따른 5개 제외, 13개 서브테스트 통과였다.
- FusRock 공식 특성표가 포함된 상세 PDF를 실제 생성하고 텍스트 경계와 3페이지 렌더링을 확인했다.
- 운영 배포 후 API·분석·뷰어·작업 서비스가 동일 이미지와 소스 해시, 강도 엔진 v0.13.0을 보고했다. 기존 FusRock ABS 분석 조회도 새 공식 제품 참조로 재계산됐다.

이 시험은 소프트웨어 계약과 표시 경계를 검증한다. 실제 FusRock 제품 배치 또는 임의 부품의 파단 정확도를 실증한 시험은 아니다.

---

## English

### Official sources integrated

The 2026-10-01 snapshot uses FusRock's [official material comparison](https://www.fusrock.com/fusrock/tools/comparison.html), its structured bootstrap payload, the [official product index](https://www.fusrock.com/products), product performance pages and product pages. It preserves **all 46 comparison products and all 96 comparison parameters**. Forty product pages are linked to catalogue products. Official slicer profiles, colour specifications, application scenarios, printing, physical, thermal and mechanical fields, test conditions, flow-temperature matrices and factual product-page recommendations are retained. Missing values remain missing.

Regenerate with `python tools/update_fusrock_catalog.py --checked-date YYYY-MM-DD`. The current bootstrap SHA-256 is `b5457f5b752185af22bc7b2db745bb1a9b365e479c06de5d65688e279233dcb0`. Marketing prose and images are excluded; the snapshot keeps factual fields and provenance needed for identification and review.

### Identification and calculation boundary

- A product is selected only when every active FusRock slicer profile resolves exactly to one official product.
- Mixed, incomplete and unknown grades are withheld rather than borrowing another FusRock grade or another manufacturer's reference.
- Directional material references require a comparable XY/Z tensile-break pair from the same test state. Products without such a pair retain their official properties but receive no directional MPa.
- G-code nozzle, bed and commanded-speed values are compared with official ranges. Out-of-range results are warnings and never become an invented strength multiplier.
- The complete factual record remains in `fusrock_material_catalog.json`; the web and PDF surfaces show a compact review set plus official links.

### FusRock ABS reference used

For ABS, the official same-state pair is `Tensile Break Strength XY = 33.36 MPa` and `Tensile Strength Z = 55 MPa`. The declared specimen conditions are a 0.4 mm nozzle, 250 °C nozzle, 100 °C bed, 50 mm/s, 100% infill and ±45° raster. Applying the existing internal 0.85 margin once gives display references X/Y 28.356 MPa and Z 46.75 MPa. The margin is neither empirical calibration nor a validated safety factor.

The product-page recommendations are retained separately: 240–260 °C nozzle, 100–110 °C bed, sealed or 60–80 °C chamber, off–30% fan, 30–120 mm/s, 1–5 mm retraction, 1800–3600 mm/min retraction speed, 70 °C for 5–6 h drying and FusFree S-Multi support. Comparison and product-page values keep their respective provenance.

### Ambiguous fields excluded from calculation

Some source fields may have labels that do not match their physical scale. For example, ABS `tensile_unannealed = 2201.74` is modulus-sized and may duplicate the explicit XY/Z modulus fields. It remains in the factual snapshot but is excluded from directional strength. Only `tbs_xy_unannealed` and `ts_z_unannealed` form the ABS directional pair. Manufacturer coupon values are not validated failure strength or allowable load for the current part, infill, walls, welds, notches, fixtures or load path.

### Implementation verification

- The public G-code, strength and quote suites passed 36, 107 and 22 tests respectively.
- The integrated image passed 261 tests, skipped 5 environment-dependent cases and passed 13 subtests.
- A detailed PDF containing the FusRock facts table was generated and checked for text bounds and three-page rendering.
- After deployment, API, analysis, viewer and worker services reported one image, matching source hashes and strength engine v0.13.0. An existing FusRock ABS analysis also refreshed to the new exact-product reference.

These checks validate software contracts and presentation boundaries. They do not validate fracture accuracy for a FusRock batch or an arbitrary printed part.
