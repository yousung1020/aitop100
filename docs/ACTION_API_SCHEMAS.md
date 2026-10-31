# 공식 액션 API 스키마 참조

확인일: 2026-10-31. [대회 액션 API](https://aitop100.org/contest/docs#description/introduction)의 공식 OpenAPI 3.1.0 정의를 표로 정리했습니다. 원본은 [official_actions_openapi.json](source_materials/official_actions_openapi.json)에 보관합니다. 실제 토큰·쿠키는 저장하지 않았습니다.

표의 필수 여부는 공식 `required` 배열을 따릅니다. 필수이면서 `null` 허용인 필드도 있으므로 누락과 null을 구분합니다. enum이 없는 문자열에 임의의 API 수준 enum을 추가하지 않습니다. JSON Schema의 중첩 객체 상세 및 응답별 오류 본문은 원본을 함께 확인합니다.

## 1. API별 요청·성공 응답 계약

### API-01: 상품 조회

- 요청: `GET /api/products/{sku}`
- 태그: 상품·로트·재고

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `sku` | 예 | string |

- 성공: 200, `Products`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-02: 품목별 상품 검색

- 요청: `GET /api/products`
- 태그: 상품·로트·재고

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| query | `item` | 예 | string |

- 성공: 200, `array[Products]`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-03: 로트 조회

- 요청: `GET /api/lots/{lot_id}`
- 태그: 상품·로트·재고

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `lot_id` | 예 | string |

- 성공: 200, `Lots`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-04: 로트 조사 조회

- 요청: `GET /api/lots/{lot_id}/investigation`
- 태그: 상품·로트·재고

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `lot_id` | 예 | string |

- 성공: 200, `LotInvestigations`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-05: 회원별 상담 이력 검색

- 요청: `GET /api/tickets`
- 태그: 조합원

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| query | `member_id` | 예 | string |

- 성공: 200, `array[Tickets]`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-06: 로트별 상담 이력 검색

- 요청: `GET /api/tickets`
- 태그: 조합원

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| query | `lot_id` | 예 | string |

- 성공: 200, `array[Tickets]`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-07: 주문 조회

- 요청: `GET /api/orders/{order_no}`
- 태그: 주문

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `order_no` | 예 | string |

- 성공: 200, `Orders`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-08: 회원별 주문 검색

- 요청: `GET /api/orders`
- 태그: 주문

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| query | `member_id` | 예 | string |

- 성공: 200, `array[Orders]`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-09: 유입태그별 주문 검색

- 요청: `GET /api/orders`
- 태그: 주문

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| query | `inflow_tag` | 예 | string |

- 성공: 200, `array[Orders]`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-10: 배송 조회

- 요청: `GET /api/shipments/{shipment_id}`
- 태그: 배송·구독

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `shipment_id` | 예 | string |

- 성공: 200, `Shipments`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-11: 주문별 배송 검색

- 요청: `GET /api/shipments`
- 태그: 배송·구독

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| query | `order_no` | 예 | string |

- 성공: 200, `array[Shipments]`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-12: 조합원 조회

- 요청: `GET /api/members/{member_id}`
- 태그: 조합원

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `member_id` | 예 | string |

- 성공: 200, `Members`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-13: 이름 조합원 검색

- 요청: `GET /api/members`
- 태그: 조합원

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| query | `name` | 예 | string |

- 성공: 200, `array[Members]`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-14: 추천인별 조합원 검색

- 요청: `GET /api/members`
- 태그: 조합원

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| query | `referred_by` | 예 | string |

- 성공: 200, `array[Members]`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-15: 적립금 내역 검색

- 요청: `GET /api/point-entries`
- 태그: 조합원

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| query | `member_id` | 예 | string |

- 성공: 200, `array[PointEntries]`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-16: 회원별 쿠폰 검색

- 요청: `GET /api/coupons`
- 태그: 프로모션·쿠폰

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| query | `member_id` | 예 | string |

- 성공: 200, `array[Coupons]`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-17: 결제 조회

- 요청: `GET /api/payments/{approval_no}`
- 태그: 결제·환불

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `approval_no` | 예 | string |

- 성공: 200, `Payments`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-18: 주문별 결제 검색

- 요청: `GET /api/payments`
- 태그: 결제·환불

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| query | `order_no` | 예 | string |

- 성공: 200, `array[Payments]`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-19: 구독 조회

- 요청: `GET /api/subscriptions/{subscription_id}`
- 태그: 배송·구독

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `subscription_id` | 예 | string |

- 성공: 200, `Subscriptions`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-20: 프로모션 조회

- 요청: `GET /api/promos/{code}`
- 태그: 프로모션·쿠폰

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `code` | 예 | string |

- 성공: 200, `Promotions`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-21: 재고 조회

- 요청: `GET /api/inventory`
- 태그: 상품·로트·재고

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| query | `sku` | 예 | string |

- 성공: 200, `array[Inventory]`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-22: 주문 복구 접수

- 요청: `POST /api/orders/{order_no}/restore-requests`
- 태그: 주문

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `order_no` | 예 | string |

본문 필수: 아니요. 추가 필드 허용: False.

본문에 정의된 업무 필드는 없습니다. 임의 필드를 보내지 않습니다.

- 성공: 200, `OrderRestoreRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-23: 주문 변경 접수

- 요청: `POST /api/orders/{order_no}/change-requests`
- 태그: 주문

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `order_no` | 예 | string |

본문 필수: 예. 추가 필드 허용: False.

| 본문 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `requested_items` | 예 | array[string] | 변경할 품목마다 SKU와 수량을 문자열 하나로 적습니다. 표기 형식은 자유입니다. |

- 성공: 200, `OrderChangeRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-24: 배송지 변경 접수

- 요청: `POST /api/orders/{order_no}/address-change-requests`
- 태그: 배송·구독

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `order_no` | 예 | string |

본문 필수: 예. 추가 필드 허용: False.

| 본문 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `new_address` | 예 | string |  |

- 성공: 200, `AddressChangeRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-25: 배송 일정 변경 접수

- 요청: `POST /api/orders/{order_no}/schedule-change-requests`
- 태그: 배송·구독

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `order_no` | 예 | string |

본문 필수: 예. 추가 필드 허용: False.

| 본문 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `requested_date` | 예 | string (date) |  |

- 성공: 200, `ScheduleChangeRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-26: 주문 메모 접수

- 요청: `POST /api/orders/{order_no}/memos`
- 태그: 주문

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `order_no` | 예 | string |

본문 필수: 예. 추가 필드 허용: False.

| 본문 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `memo` | 예 | string |  |

- 성공: 200, `OrderMemosReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-27: 긴급 출고 접수

- 요청: `POST /api/orders/{order_no}/expedite-requests`
- 태그: 배송·구독

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `order_no` | 예 | string |

본문 필수: 예. 추가 필드 허용: False.

| 본문 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `qty` | 예 | integer (int32) |  |
| `reason` | 예 | string |  |

- 성공: 200, `ExpediteRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-28: 재배송 접수

- 요청: `POST /api/shipments/{shipment_id}/reship-requests`
- 태그: 배송·구독

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `shipment_id` | 예 | string |

본문 필수: 아니요. 추가 필드 허용: False.

본문에 정의된 업무 필드는 없습니다. 임의 필드를 보내지 않습니다.

- 성공: 200, `ReshipRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-29: 환불 신청

- 요청: `POST /api/refunds`
- 태그: 결제·환불

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |

본문 필수: 예. 추가 필드 허용: False.

| 본문 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `order_no` | 예 | string |  |
| `amount` | 예 | integer (int32) |  |
| `reason` | 예 | string |  |

- 성공: 200, `RefundsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-30: 주문별 환불 검색

- 요청: `GET /api/refunds`
- 태그: 결제·환불

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| query | `order_no` | 예 | string |

- 성공: 200, `array[Refunds]`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-31: 카드 취소 접수

- 요청: `POST /api/payments/{approval_no}/cancellation-requests`
- 태그: 결제·환불

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `approval_no` | 예 | string |

본문 필수: 아니요. 추가 필드 허용: False.

본문에 정의된 업무 필드는 없습니다. 임의 필드를 보내지 않습니다.

- 성공: 200, `PaymentCancellationRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-32: 현금영수증 발행 접수

- 요청: `POST /api/payments/{approval_no}/cash-receipt-requests`
- 태그: 결제·환불

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `approval_no` | 예 | string |

본문 필수: 예. 추가 필드 허용: False.

| 본문 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `receipt_number` | 예 | string |  |

- 성공: 200, `CashReceiptRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-33: 쿠폰 발급 접수

- 요청: `POST /api/members/{member_id}/coupon-issue-requests`
- 태그: 프로모션·쿠폰

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `member_id` | 예 | string |

본문 필수: 예. 추가 필드 허용: False.

| 본문 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `promo_code` | 예 | string |  |

- 성공: 200, `CouponIssueRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-34: 리워드 지급 접수

- 요청: `POST /api/members/{member_id}/reward-requests`
- 태그: 조합원

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `member_id` | 예 | string |

본문 필수: 아니요. 추가 필드 허용: False.

본문에 정의된 업무 필드는 없습니다. 임의 필드를 보내지 않습니다.

- 성공: 200, `RewardRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-35: 에스컬레이션

- 요청: `POST /api/escalations`
- 태그: 에스컬레이션

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |

본문 필수: 예. 추가 필드 허용: False.

| 본문 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `lane` | 예 | string |  |
| `reason` | 예 | string |  |

- 성공: 200, `EscalationsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 429, 500, 503

### API-36: 에스컬레이션 조회

- 요청: `GET /api/escalations/{escalation_id}`
- 태그: 에스컬레이션

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `escalation_id` | 예 | string |

- 성공: 200, `Escalations`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-37: 재배송비 청구 접수

- 요청: `POST /api/shipments/{shipment_id}/reship-charge-requests`
- 태그: 배송·구독

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `shipment_id` | 예 | string |

본문 필수: 예. 추가 필드 허용: False.

| 본문 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `charge_amount` | 예 | integer (int32) |  |

- 성공: 200, `ReshipChargeRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-38: 픽업 접수

- 요청: `POST /api/orders/{order_no}/pickup-requests`
- 태그: 배송·구독

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `order_no` | 예 | string |

본문 필수: 예. 추가 필드 허용: False.

| 본문 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `qty` | 예 | integer (int32) |  |
| `trigger` | 예 | string |  |
| `cost_bearer` | 예 | string; enum=["SELLER", "CUSTOMER"] |  |

- 성공: 200, `PickupRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-39: 재입고 알림 등록

- 요청: `POST /api/products/{sku}/restock-notification-requests`
- 태그: 상품·로트·재고

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `sku` | 예 | string |

본문 필수: 아니요. 추가 필드 허용: False.

본문에 정의된 업무 필드는 없습니다. 임의 필드를 보내지 않습니다.

- 성공: 200, `RestockNotificationRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### API-40: 구독 변경 접수

- 요청: `POST /api/subscriptions/{subscription_id}/change-requests`
- 태그: 배송·구독

| 위치 | 이름 | 필수 | 타입·제약 |
| :--- | :--- | :--- | :--- |
| header | `X-Aitop100-Test-Case-Id` | 예 | string; minLength=1; maxLength=100; pattern=^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ |
| path | `subscription_id` | 예 | string |

본문 필수: 예. 추가 필드 허용: False.

| 본문 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `kind` | 예 | string; enum=["SKIP", "CANCEL"] |  |

- 성공: 200, `SubscriptionChangeRequestsReceipt`
- 정의된 상태 코드: 200, 400, 401, 403, 404, 429, 500, 503

### resetMyActionData: 내 액션 데이터 전체 초기화

- 요청: `POST /api/action-data/reset`
- 태그: 내 데이터

요청 본문은 정의되어 있지 않습니다.

- 성공: 204, 본문 없음
- 정의된 상태 코드: 204, 401, 403, 409, 429, 500, 503

## 2. 응답·데이터 모델 필드

### Error

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `code` | 예 | string | 오류 코드 |
| `message` | 예 | string | 오류 메시지 |

### OrderRestoreRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `order_no` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### OrderChangeRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `order_no` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### AddressChangeRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `order_no` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### ScheduleChangeRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `order_no` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### OrderMemosReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `memo_id` | 예 | string | 접수번호 |
| `order_no` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### ExpediteRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `order_no` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### ReshipRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `shipment_id` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### RefundsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `refund_id` | 예 | string | 접수번호 |
| `order_no` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### PaymentCancellationRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `approval_no` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### CashReceiptRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `approval_no` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### CouponIssueRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `member_id` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### RewardRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `member_id` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### EscalationsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `escalation_id` | 예 | string | 접수번호 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### ReshipChargeRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `shipment_id` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### PickupRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `order_no` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### RestockNotificationRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `sku` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### SubscriptionChangeRequestsReceipt

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string | 접수번호 |
| `subscription_id` | 예 | string | 접수 대상 식별자 |
| `request_status` | 예 | string; enum=["SUBMITTED"] | 접수 상태 |
| `requested_at` | 예 | string (date-time) | 접수 시각 |

### AddressChangeRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `order_no` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |
| `new_address` | 예 | string |  |

### CashReceiptRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `approval_no` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |
| `receipt_number` | 예 | string |  |

### CouponIssueRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `member_id` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |
| `promo_code` | 예 | string |  |

### Coupons

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `coupon_id` | 예 | string |  |
| `member_id` | 예 | string |  |
| `promo_code` | 예 | string |  |
| `issued_at` | 예 | string (date-time) |  |
| `expires_at` | 예 | string (date) |  |
| `used_at` | 예 | string / null (date-time) |  |

### Escalations

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `escalation_id` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |
| `lane` | 예 | string |  |
| `reason` | 예 | string |  |
| `status` | 예 | string; enum=["APPROVED", "REJECTED", "PENDING"] |  |

### ExpediteRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `order_no` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |
| `qty` | 예 | integer |  |
| `reason` | 예 | string |  |

### Inventory

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `sku` | 예 | string |  |
| `total_qty` | 예 | integer |  |
| `sale_state` | 예 | string; enum=["ON_SALE", "PREORDER", "SOLD_OUT", "CLOSED"] |  |

### LotInvestigations

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `lot_id` | 예 | string |  |
| `status` | 예 | string; enum=["IN_PROGRESS", "CLOSED"] |  |
| `symptom` | 예 | string; enum=["BLACK_HEART", "MOLD"] |  |
| `liability` | 예 | string / null; enum=["DISTRIBUTION", "PRODUCTION", "CARRIER", null] |  |
| `finding` | 예 | string / null |  |
| `disclosure_approved` | 예 | boolean / null |  |
| `opened_at` | 예 | string (date-time) |  |
| `closed_at` | 예 | string / null (date-time) |  |

### Lots

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `lot_id` | 예 | string |  |
| `sku` | 예 | string |  |
| `packed_at` | 예 | string (date-time) |  |
| `measured_weight_g` | 예 | integer |  |
| `measured_brix` | 예 | number / null |  |
| `grade` | 예 | string; enum=["PREMIUM", "STANDARD", "FAIR", "IMPERFECT", "REJECT"] |  |
| `qty_in_stock` | 예 | integer |  |
| `status` | 예 | string; enum=["ACTIVE", "HOLD", "DISPOSED"] |  |
| `sprayed_at` | 예 | string / null (date) |  |

### Members

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `member_id` | 예 | string |  |
| `name` | 예 | string |  |
| `phone` | 예 | string |  |
| `birth_year` | 예 | integer |  |
| `member_type` | 예 | string; enum=["INDIVIDUAL", "BUSINESS", "GROUP_BUY_OPERATOR"] |  |
| `grade` | 예 | string; enum=["MEMBER", "REGULAR"] |  |
| `status` | 예 | string; enum=["ACTIVE", "WITHDRAWAL_REQUESTED", "WITHDRAWN"] |  |
| `address` | 예 | string / null |  |
| `joined_at` | 예 | string (date) |  |
| `referred_by_member_id` | 예 | string / null |  |

### OrderChangeRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `order_no` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |
| `requested_items` | 예 | array[string] |  |

### OrderItems

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `order_no` | 예 | string |  |
| `sku` | 예 | string |  |
| `name` | 예 | string |  |
| `qty` | 예 | integer |  |
| `unit_price` | 예 | integer |  |

### OrderMemos

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `memo_id` | 예 | string |  |
| `order_no` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |
| `memo` | 예 | string |  |

### OrderRestoreRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `order_no` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |

### Orders

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `order_no` | 예 | string |  |
| `member_id` | 예 | string |  |
| `status` | 예 | string; enum=["PAID", "CONFIRMED", "CANCEL_REQUESTED", "CANCELED", "FAILED"] |  |
| `status_changed_at` | 예 | string / null (date-time) |  |
| `ordered_at` | 예 | string (date-time) |  |
| `amount` | 예 | integer |  |
| `recipient_name` | 예 | string |  |
| `shipping_address` | 예 | string |  |
| `inflow_tag` | 예 | string / null |  |
| `ship_scheduled_at` | 예 | string / null (date) |  |
| `failure_code` | 예 | string / null |  |
| `payment_refs` | 예 | array[string] |  |
| `refund_ids` | 예 | array[string] |  |
| `change_request_ids` | 예 | array[string] |  |
| `items` | 예 | array[object] |  |

### PaymentCancellationRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `approval_no` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |

### Payments

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `approval_no` | 예 | string |  |
| `order_no` | 예 | string / null |  |
| `pay_method` | 예 | string |  |
| `amount` | 예 | integer |  |
| `paid_at` | 예 | string (date-time) |  |
| `status` | 예 | string; enum=["APPROVED", "CANCELED"] |  |
| `payer_name` | 예 | string / null |  |
| `cancellation_request_ids` | 예 | array[string] |  |
| `card_last4` | 예 | string / null |  |

### PickupRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `order_no` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |
| `qty` | 예 | integer |  |
| `trigger` | 예 | string |  |
| `cost_bearer` | 예 | string; enum=["SELLER", "CUSTOMER"] |  |

### PointEntries

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `entry_id` | 예 | string |  |
| `member_id` | 예 | string |  |
| `amount` | 예 | integer |  |
| `granted_at` | 예 | string (date) |  |
| `expires_at` | 예 | string (date) |  |

### Products

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `sku` | 예 | string |  |
| `name` | 예 | string |  |
| `origin` | 예 | string |  |
| `variety` | 예 | string / null |  |
| `listed_weight` | 예 | string |  |
| `grade` | 예 | array / null |  |
| `price` | 예 | integer |  |
| `sale_state` | 예 | string; enum=["ON_SALE", "PREORDER", "SOLD_OUT", "CLOSED"] |  |

### Promotions

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `code` | 예 | string |  |
| `name` | 예 | string |  |
| `benefit_type` | 예 | string; enum=["RATE", "AMOUNT"] |  |
| `benefit_value` | 예 | integer |  |
| `valid_from` | 예 | string (date) |  |
| `valid_until` | 예 | string / null (date) |  |
| `target_skus` | 예 | array / null |  |
| `stackable_with` | 예 | array[string; enum=["DISCOUNT_CODE", "REWARD_COUPON", "POINTS"]] |  |

### Refunds

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `refund_id` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |
| `order_no` | 예 | string |  |
| `amount` | 예 | integer |  |
| `reason` | 예 | string |  |

### ReshipChargeRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `shipment_id` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |
| `charge_amount` | 예 | integer |  |

### ReshipRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `shipment_id` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |

### RestockNotificationRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `sku` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |

### RewardRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `member_id` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |

### ScheduleChangeRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `order_no` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |
| `requested_date` | 예 | string (date) |  |

### ShipmentItems

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `shipment_id` | 예 | string |  |
| `sku` | 예 | string |  |
| `qty` | 예 | integer |  |
| `lot_id` | 예 | string |  |

### Shipments

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `shipment_id` | 예 | string |  |
| `order_no` | 예 | string |  |
| `status` | 예 | string; enum=["READY", "IN_TRANSIT", "DELIVERED", "RETURNED"] |  |
| `carrier` | 예 | string |  |
| `invoice_no` | 예 | string |  |
| `picked_up_at` | 예 | string / null (date-time) |  |
| `delivered_at` | 예 | string / null (date-time) |  |
| `delivered_location` | 예 | string / null |  |
| `return_reason` | 예 | string / null |  |
| `item_condition` | 예 | string / null |  |
| `ship_notice_sent_at` | 예 | string / null (date-time) |  |
| `items` | 예 | array[object] |  |

### SubscriptionChangeRequests

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `request_id` | 예 | string |  |
| `subscription_id` | 예 | string |  |
| `request_status` | 예 | string; enum=["SUBMITTED"] |  |
| `requested_at` | 예 | string (date-time) |  |
| `kind` | 예 | string; enum=["SKIP", "CANCEL"] |  |

### Subscriptions

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `subscription_id` | 예 | string |  |
| `member_id` | 예 | string |  |
| `sku` | 예 | string |  |
| `status` | 예 | string; enum=["ACTIVE", "CANCELED"] |  |
| `interval` | 예 | string |  |
| `started_at` | 예 | string (date) |  |

### Tickets

추가 필드 허용: False.

| 필드 | 필수 | 타입·허용값 | 설명 |
| :--- | :--- | :--- | :--- |
| `ticket_id` | 예 | string |  |
| `member_id` | 예 | string |  |
| `lot_id` | 예 | string / null |  |
| `created_at` | 예 | string (date-time) |  |
| `content` | 예 | string |  |
| `handler` | 예 | string |  |
