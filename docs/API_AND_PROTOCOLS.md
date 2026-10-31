# API 인터페이스 및 액션 프로토콜 규격서 (API_AND_PROTOCOLS)

본 문서는 프로젝트의 카카오 스킬 메시지 규격과 대회 공식 액션 API를 기록합니다. 프로젝트 웹훅(`/skill` 등)과 외부 액션 서버(`/api/...`)는 서로 다른 서버입니다. 액션 API 부분은 2026-10-31 로그인된 공식 문서와 OpenAPI를 확인하여 교체했으며, 이전 `/v1/...` 가정 명세는 공식 규격으로 사용하지 않습니다.

---

## 1. 카카오 오픈빌더 스킬 인터페이스 규격

카카오 i 오픈빌더는 사용자의 발화를 HTTP POST 요청으로 스킬 서버에 전달하며, 스킬 서버는 정해진 JSON 포맷으로 응답해야 합니다.

### 요청 페이로드 규격 (OpenBuilder -> FastAPI)
사용자가 카카오톡 채널에 입력한 메시지와 컨텍스트 정보가 담긴 표준 요청 구조입니다.

```json
{
  "bot": {
    "id": "gyodong_bot_id_2037",
    "name": "교동마을 산지직송 CS봇"
  },
  "intent": {
    "id": "fallback_intent_id",
    "name": "폴백 블록"
  },
  "action": {
    "id": "action_skill_call",
    "name": "CS질의응답",
    "params": {}
  },
  "userRequest": {
    "block": {
      "id": "fallback_intent_id",
      "name": "폴백 블록"
    },
    "user": {
      "id": "kakao_user_unique_hash_98234",
      "type": "botUserKey",
      "properties": {
        "botUserKey": "kakao_user_unique_hash_98234",
        "appUserId": "app_user_4821"
      }
    },
    "utterance": "감귤이랑 갈치를 같이 샀는데 왜 택배가 따로 오나요?",
    "params": {
      "surface": "KakaoTalk"
    },
    "timezone": "Asia/Seoul"
  }
}
```

- `userRequest.utterance`: 사용자가 입력한 발화 텍스트 본문입니다. Gemini Flash Lite 에이전트의 질의 입력으로 직접 주입됩니다.
- `userRequest.user.properties.botUserKey`: 카카오 사용자 식별 키로, 상담원 이관 티켓 발급 및 세션 추적에 활용됩니다.

### 응답 페이로드 규격 (FastAPI -> OpenBuilder)
AGENTS의 프로젝트 제약으로 **오직 SimpleText 단일 포맷만 허용**합니다. BasicCard, CommerceCard, Carousel, QuickReplies 등의 버튼이나 복합 UI는 배제합니다. 위반 시의 정확한 배점·실격 기준은 참가자 안내 원문으로 별도 확인해야 하며, 이 액션 API 문서로 검증한 사실은 아닙니다.

```json
{
  "version": "2.0",
  "template": {
    "outputs": [
      {
        "simpleText": {
          "text": "안녕하세요! 교동마을 산지직송입니다.\n\n주문하신 감귤은 교동마을 선과장에서, 은갈치는 갯마을 어판장 전용 콜드체인 물류센터에서 각각 발송되어 하나의 상자로 합포장이 불가합니다.\n\n두 품목 모두 '주식회사 시원배송' 위탁이며, 출하지 거점 및 운송 차량/보관 조건(상온 직배송 vs 냉동탑차 TR-GM-02)이 달라 합포장 불가합니다. 각 상품은 개별 발송되므로 도착일과 시간이 다를 수 있는 점 양해 부탁드립니다."
        }
      }
    ]
  }
}
```

- `template.outputs`: 반드시 1개의 SimpleText 요소만 포함하는 배열이어야 합니다. 2개 이상의 출력을 반환하면 평균 말풍선 수 규정 위반이 됩니다.
- `simpleText.text`: 전체 글자 수가 공백 포함 500자를 초과하지 않도록 480자 이하로 안전하게 제어해야 합니다.

---

---

## 2. 공식 액션 API: 출처 및 인증

- 확인일: **2026-10-31**. 로그인된 참가자 문서의 OpenAPI 3.1.0 및 공개 TC 15건을 읽었습니다. **업무 API 호출, 접수, 초기화는 실행하지 않았습니다.**
- 재확인: **2026-10-31 13:41 KST**. 실제 로그인된 Chrome에서 현재 액션 API 원문과 기존 스냅샷 전체가 동일함을 확인했습니다. Markdown 계약 표의 대조 범위와 구현 완료 보고의 불일치는 [재확인 기록](API_CONSISTENCY_AUDIT.md)을 참조합니다. 이번 재확인에서 공개 TC 원문은 새로 수집하지 않았습니다.
- 공식 문서: [액션 API](https://aitop100.org/contest/docs#description/introduction), [공개 TC](https://aitop100.org/contest/docs/test-cases).
- 문서 데이터 출처: `https://aitop100.org/api/contest/docs/actions`. 이 URL은 문서 리소스이며 업무 API 서버가 아닙니다.
- 공식 정의 스냅샷: [official_actions_openapi.json](source_materials/official_actions_openapi.json).
- 전체 필드·허용값·응답 모델: [ACTION_API_SCHEMAS.md](ACTION_API_SCHEMAS.md).
- 공개 TC별 문의·조건·호출 순서: [PUBLIC_TEST_CASES.md](PUBLIC_TEST_CASES.md).

```dotenv
ACTION_SERVER_URL=https://gyodong-mall-action.aitop100.org
ACTION_SERVER_TOKEN=aitop100_실제발급값
```

토큰은 참가 동의 시 발급되며 홈페이지에서 재조회할 수 있습니다. 실제 값은 `.env`에만 입력하고 문서·로그에 기록하지 않습니다. 환경변수에는 `Bearer`를 붙이지 않습니다. 서버 주소 끝에 `/api`나 `/v1`을 덧붙이지 않습니다.

업무 API-01~API-40 요청의 공통 헤더:

```http
Authorization: Bearer <ACTION_SERVER_TOKEN>
X-Aitop100-Test-Case-Id: L-03
Content-Type: application/json
```

TC ID는 평가 대화에서 전달된 값을 같은 TC의 모든 요청에 유지합니다. 평가 전에는 공개 TC의 ID만 허용합니다. 형식은 `^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$`이고 길이는 1~100자입니다. 예시 `L-03`을 모든 상담에 고정 사용하면 안 됩니다. 카카오 `botUserKey`·회원 ID·TC ID는 서로 다른 식별자입니다. 카카오 요청에서 평가 TC ID·인입 계정을 어떤 필드로 전달받는지는 이 액션 문서만으로 확정하지 않았습니다.

## 3. 응답 및 접수 의미

- 단건 GET 성공은 객체, 검색 GET 성공은 배열입니다. 검색 결과 없음은 `[]`, 단건 대상 없음은 본문 없는 404입니다.
- 단건 조회에 검색 쿼리를 추가하거나, 지원하지 않는 쿼리·본문 필드·타입·필수값을 보내면 본문 없는 400이 발생할 수 있습니다. 검색은 문서에서 지원하는 검색 파라미터 하나와 값 하나를 사용합니다.
- 공식 정의의 일부 검색 경로 키에는 `/api/orders?member_id=`처럼 쿼리가 붙어 있습니다. 실제 HTTP 경로는 `/api/orders`이고 `member_id`는 query parameter입니다. 아래 표는 공식 API ID별 검색 방식을 분리해 기록합니다.
- **접수 POST는 정책 적합성을 판정하거나 주문·결제의 상태·금액을 변경하지 않습니다. 정책을 위반한 내용도 접수될 수 있으므로 호출 전에 에이전트가 검증해야 합니다.**
- 접수 성공은 HTTP 200이며 `request_status: SUBMITTED`, 접수번호, `requested_at`을 반환합니다. 기존의 `{status: SUCCESS, data: ...}` 래퍼를 가정하지 않습니다.
- 접수번호 필드는 대부분 `request_id`이고 주문 메모는 `memo_id`, 환불은 `refund_id`, 이관은 `escalation_id`입니다. 정확한 대상 식별자 및 필드는 스키마 참조 문서를 따릅니다.
- 같은 접수 API·같은 대상에 재요청하면 접수번호는 같고 내용은 마지막 본문으로 덮어씁니다. 대상이 없는 이관은 본문에 따라 접수번호가 정해집니다. 따라서 멱등 재시도와 고객의 다른 요청을 구분해야 합니다.
- 재조회 시 연결되는 접수번호 필드는 `orders.refund_ids`, `orders.change_request_ids`, `payments.cancellation_request_ids`입니다. 다른 상태·주소·금액이 변경됐다고 추정하지 않습니다.
- 고객에게는 환불·변경·재배송 **요청이 접수되었다고** 안내합니다. 지급·발행·배송지 변경·문자 발송 완료로 바꾸어 말하지 않습니다.

예: API-24의 요청 본문은 아래 필드만 정의되어 있습니다. `recipient_name`, `user_key`, `zipcode` 등을 임의로 추가하면 안 됩니다.

```json
{"new_address": "고객이 확인한 동·호수 포함 상세주소"}
```

성공 응답의 구조 예시(값은 설명용이며 실제 호출 결과가 아님):

```json
{
  "request_id": "<접수번호>",
  "order_no": "<확인한 대상 주문번호>",
  "request_status": "SUBMITTED",
  "requested_at": "2037-06-30T15:16:00+09:00"
}
```

## 4. 공식 업무 API 전체 목록

아래 API-01~API-40은 공식 문서의 operationId입니다. 조회 23개, 접수 17개이며 초기화는 별도입니다. 모든 목록을 로컬 코드 구현 완료로 해석하지 않습니다.


### 조회·검색

| API ID | 이름 | 메서드·경로 | 쿼리 또는 JSON 본문 | 성공 모델 |
| :--- | :--- | :--- | :--- | :--- |
| API-01 | 상품 조회 | `GET /api/products/{sku}` | 없음 (path 식별자 사용) | Products |
| API-02 | 품목별 상품 검색 | `GET /api/products` | `item` (필수) | array[Products] |
| API-03 | 로트 조회 | `GET /api/lots/{lot_id}` | 없음 (path 식별자 사용) | Lots |
| API-04 | 로트 조사 조회 | `GET /api/lots/{lot_id}/investigation` | 없음 (path 식별자 사용) | LotInvestigations |
| API-05 | 회원별 상담 이력 검색 | `GET /api/tickets` | `member_id` (필수) | array[Tickets] |
| API-06 | 로트별 상담 이력 검색 | `GET /api/tickets` | `lot_id` (필수) | array[Tickets] |
| API-07 | 주문 조회 | `GET /api/orders/{order_no}` | 없음 (path 식별자 사용) | Orders |
| API-08 | 회원별 주문 검색 | `GET /api/orders` | `member_id` (필수) | array[Orders] |
| API-09 | 유입태그별 주문 검색 | `GET /api/orders` | `inflow_tag` (필수) | array[Orders] |
| API-10 | 배송 조회 | `GET /api/shipments/{shipment_id}` | 없음 (path 식별자 사용) | Shipments |
| API-11 | 주문별 배송 검색 | `GET /api/shipments` | `order_no` (필수) | array[Shipments] |
| API-12 | 조합원 조회 | `GET /api/members/{member_id}` | 없음 (path 식별자 사용) | Members |
| API-13 | 이름 조합원 검색 | `GET /api/members` | `name` (필수) | array[Members] |
| API-14 | 추천인별 조합원 검색 | `GET /api/members` | `referred_by` (필수) | array[Members] |
| API-15 | 적립금 내역 검색 | `GET /api/point-entries` | `member_id` (필수) | array[PointEntries] |
| API-16 | 회원별 쿠폰 검색 | `GET /api/coupons` | `member_id` (필수) | array[Coupons] |
| API-17 | 결제 조회 | `GET /api/payments/{approval_no}` | 없음 (path 식별자 사용) | Payments |
| API-18 | 주문별 결제 검색 | `GET /api/payments` | `order_no` (필수) | array[Payments] |
| API-19 | 구독 조회 | `GET /api/subscriptions/{subscription_id}` | 없음 (path 식별자 사용) | Subscriptions |
| API-20 | 프로모션 조회 | `GET /api/promos/{code}` | 없음 (path 식별자 사용) | Promotions |
| API-21 | 재고 조회 | `GET /api/inventory` | `sku` (필수) | array[Inventory] |
| API-30 | 주문별 환불 검색 | `GET /api/refunds` | `order_no` (필수) | array[Refunds] |
| API-36 | 에스컬레이션 조회 | `GET /api/escalations/{escalation_id}` | 없음 (path 식별자 사용) | Escalations |

### 접수

| API ID | 이름 | 메서드·경로 | 쿼리 또는 JSON 본문 | 성공 모델 |
| :--- | :--- | :--- | :--- | :--- |
| API-22 | 주문 복구 접수 | `POST /api/orders/{order_no}/restore-requests` | 업무 필드 없음; 본문 생략 또는 `{}` | OrderRestoreRequestsReceipt |
| API-23 | 주문 변경 접수 | `POST /api/orders/{order_no}/change-requests` | `requested_items` (array[string], 필수) | OrderChangeRequestsReceipt |
| API-24 | 배송지 변경 접수 | `POST /api/orders/{order_no}/address-change-requests` | `new_address` (string, 필수) | AddressChangeRequestsReceipt |
| API-25 | 배송 일정 변경 접수 | `POST /api/orders/{order_no}/schedule-change-requests` | `requested_date` (string (date), 필수) | ScheduleChangeRequestsReceipt |
| API-26 | 주문 메모 접수 | `POST /api/orders/{order_no}/memos` | `memo` (string, 필수) | OrderMemosReceipt |
| API-27 | 긴급 출고 접수 | `POST /api/orders/{order_no}/expedite-requests` | `qty` (integer (int32), 필수), `reason` (string, 필수) | ExpediteRequestsReceipt |
| API-28 | 재배송 접수 | `POST /api/shipments/{shipment_id}/reship-requests` | 업무 필드 없음; 본문 생략 또는 `{}` | ReshipRequestsReceipt |
| API-29 | 환불 신청 | `POST /api/refunds` | `order_no` (string, 필수), `amount` (integer (int32), 필수), `reason` (string, 필수) | RefundsReceipt |
| API-31 | 카드 취소 접수 | `POST /api/payments/{approval_no}/cancellation-requests` | 업무 필드 없음; 본문 생략 또는 `{}` | PaymentCancellationRequestsReceipt |
| API-32 | 현금영수증 발행 접수 | `POST /api/payments/{approval_no}/cash-receipt-requests` | `receipt_number` (string, 필수) | CashReceiptRequestsReceipt |
| API-33 | 쿠폰 발급 접수 | `POST /api/members/{member_id}/coupon-issue-requests` | `promo_code` (string, 필수) | CouponIssueRequestsReceipt |
| API-34 | 리워드 지급 접수 | `POST /api/members/{member_id}/reward-requests` | 업무 필드 없음; 본문 생략 또는 `{}` | RewardRequestsReceipt |
| API-35 | 에스컬레이션 | `POST /api/escalations` | `lane` (string, 필수), `reason` (string, 필수) | EscalationsReceipt |
| API-37 | 재배송비 청구 접수 | `POST /api/shipments/{shipment_id}/reship-charge-requests` | `charge_amount` (integer (int32), 필수) | ReshipChargeRequestsReceipt |
| API-38 | 픽업 접수 | `POST /api/orders/{order_no}/pickup-requests` | `qty` (integer (int32), 필수), `trigger` (string, 필수), `cost_bearer` (string; enum=["SELLER", "CUSTOMER"], 필수) | PickupRequestsReceipt |
| API-39 | 재입고 알림 등록 | `POST /api/products/{sku}/restock-notification-requests` | 업무 필드 없음; 본문 생략 또는 `{}` | RestockNotificationRequestsReceipt |
| API-40 | 구독 변경 접수 | `POST /api/subscriptions/{subscription_id}/change-requests` | `kind` (string; enum=["SKIP", "CANCEL"], 필수) | SubscriptionChangeRequestsReceipt |

## 5. 호출 한도·오류·데이터 초기화

| 상황 | 공식 규칙 |
| :--- | :--- |
| 연습 호출 | 최종 제출 전 또는 평가 시작 전. 60초당 최대 100회, 누적 한도 없음 |
| 평가 호출 | 최종 제출 뒤 평가가 시작되면 적용. 60초당 최대 100회, 누적 최대 3,000회 |
| 공유 데이터 | 참가자 본인 데이터는 TC 간 공유되므로 한 TC의 접수가 다른 TC의 조회에도 남음 |
| 평가 시작 | 첫 평가 호출 전에 자동으로 초기 상태로 복원 |
| 호출 계산 | 본문 없는 400·404와 반복 조회도 각 1회로 계산 |
| 한도 변경 | 문서 조회 시점 값이며 대회 중 변경될 수 있음 |

| 상태 | 원인·처리 |
| :--- | :--- |
| 400 + JSON | TC 헤더 누락 `MISSING_TEST_CASE_ID`, 빈 값·중복·형식·허용 목록 오류 `INVALID_TEST_CASE_ID`. 액션 미실행 |
| 400 + 빈 본문 | 잘못된 검색 파라미터, 본문 필드·필수값·타입·허용값 등. JSON 파싱 실패로 원인을 덮지 않음 |
| 401 | `UNAUTHORIZED` 또는 `ACTION_API_SCHEDULE_UNSET` / `ACTION_API_NOT_STARTED` / `ACTION_API_ENDED`. 토큰 오류와 사용 기간 오류를 구분 |
| 403 | 접근 권한 없음. 초기화 금지 시점은 별도 409 |
| 404 + 빈 본문 | 대상 없음 또는 `/api` 아래 미등록 경로·메서드. 대상 부재로 결론내리기 전에 경로 확인 |
| 429 | `RATE_LIMIT_EXCEEDED`. 시간 창은 `Retry-After` 초 이후 재시도. `누적 API 호출 한도를 초과했습니다.` 메시지는 누적 한도이므로 대기해도 복구되지 않음 |
| 500·503 | 일시 오류. 503은 `SERVICE_UNAVAILABLE` / `WORLD_UNAVAILABLE` 등. 잠시 뒤 재시도하되 접수 덮어쓰기 특성을 고려 |

`POST /api/action-data/reset`은 인증 토큰이 필요하지만 **TC 헤더와 요청 본문은 필요하지 않습니다**. 성공은 본문 없는 204입니다. 접수 내역을 모두 지우는 연습용 동작이므로 이번 문서 확인에서는 실행하지 않았습니다. 최종 제출 후 또는 평가 시작 시각부터는 409로 거절됩니다. 두 조건을 모두 만족할 때까지 허용된다고 해석하면 안 됩니다.

카카오 일반 스킬 5초·프로젝트 내부 4.5초 예산과 긴 `Retry-After` 대기는 별개입니다. 현재 요청에서 무작정 기다리면 안 되며, 재시도/후속 안내 구현 방식은 별도 설계·검증 대상입니다. 공식 API 규약 자체가 프로젝트의 LLM 타임아웃이나 모델 재시도 방식을 정해 주지는 않습니다.

## 6. 기존 구현과 차이 및 후속 검증

| 기존 가정 | 공식 규격 및 후속 확인 |
| :--- | :--- |
| `POST /v1/auth/reset-session` | 확보한 API-01~40에 계정 세션 초기화 API 없음. 복구 티켓·SMS 발송 완료를 만들면 안 됨 |
| `PATCH /v1/orders/{order_id}/shipping-address` | API-24: `POST /api/orders/{order_no}/address-change-requests`, 본문 `new_address`만 사용 |
| `POST /v1/support/escalate` | API-35: `POST /api/escalations`, 필수 본문 `lane`, `reason` |
| `status == SUCCESS` 판정 | GET 객체/배열, POST 접수 응답의 식별자·`request_status` 검증 필요 |
| `botUserKey`를 회원 ID로 취급 | 공식 데이터의 `member_id`와 별개. 공개 TC 인입 계정과 고객이 제시한 식별정보를 대조 |
| 액션 서버가 정책 위반을 막아 줌 | 정책 위반 요청도 접수됨. 고객의 요청·본인확인·대상 범위·정책 조건을 먼저 검증 |
| 독립된 1회 발화만 처리 | TC 내 후속 질문, 주문번호·상세주소·선택 확인을 이어서 처리해야 함 |
| 내부 예상 시나리오 30건 = 공식 공개 TC | 공식 공개 사례는 15건. 프로젝트 예상 시나리오와 구분해 관리 |

API-35의 `lane`은 스키마상 자유 문자열입니다. 공개 TC에서 확인된 값은 `LANE2_HANDOFF`, `LANE3_CLAIM`이며, 이는 해당 사례의 지정값입니다. API-35에 임의의 `user_key`, `category`, `claim_amount`, `contact`를 추가하지 않습니다. 대상 주문번호와 필요한 사유는 공식 `reason` 필드에 기록합니다.

구현 완료 여부는 별도입니다. 이번 작업은 공식 문서 확인·기록이며 클라이언트·오케스트레이터·테스트 코드의 교체나 실제 액션 실행을 완료하지 않았습니다.
