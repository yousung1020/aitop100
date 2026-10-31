# API 인터페이스 및 액션 프로토콜 규격서 (API_AND_PROTOCOLS)

본 문서는 카카오톡 i 오픈빌더 스킬 서버의 메시지 송수신 인터페이스 규격과 산지 쇼핑몰 백엔드 액션 서버 간의 연동 프로토콜을 정의합니다.

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
대회 심사 규정상 **오직 SimpleText 단일 포맷만 허용**됩니다. BasicCard, CommerceCard, Carousel, QuickReplies 등의 버튼이나 복합 UI가 포함될 경우 즉시 0점 및 탈락 처리되므로 엄격히 배제해야 합니다.

```json
{
  "version": "2.0",
  "template": {
    "outputs": [
      {
        "simpleText": {
          "text": "안녕하세요! 교동마을 산지직송입니다.\n\n주문하신 감귤은 교동마을 선과장에서, 은갈치는 갯마을 어판장 전용 콜드체인 물류센터에서 각각 발송되어 하나의 상자로 합포장이 불가합니다.\n\n각 상품은 서로 다른 택배사로 개별 발송되므로 도착일과 시간이 다를 수 있는 점 양해 부탁드립니다."
        }
      }
    ]
  }
}
```

- `template.outputs`: 반드시 1개의 SimpleText 요소만 포함하는 배열이어야 합니다. 2개 이상의 출력을 반환하면 평균 말풍선 수 규정 위반이 됩니다.
- `simpleText.text`: 전체 글자 수가 공백 포함 500자를 초과하지 않도록 480자 이하로 안전하게 제어해야 합니다.

---

## 2. 산지 액션 서버 연동 프로토콜

에이전트가 복합 문의를 처리할 때 백엔드 액션 서버(`ACTION_SERVER_URL`)와 통신하여 실시간 데이터를 조회 및 변경하는 프로토콜입니다.

### 프로토콜 1: 회원 계정 및 로그인 장애 처리 API
- **엔드포인트**: `POST /v1/auth/reset-session`
- **목적**: 간편로그인 오류, 비밀번호 분실, 본인인증 세션 잠김 시 안전한 임시 복구 링크 또는 인증 코드를 발급합니다.
- **요청 헤더**:
  - `Authorization: Bearer <ACTION_SERVER_TOKEN>`
  - `Content-Type: application/json`
- **요청 본문 (JSON)**:
  ```json
  {
    "user_key": "kakao_user_unique_hash_98234",
    "phone_number": "010-1234-5678",
    "reason": "로그인 연속 실패 및 비밀번호 분실"
  }
  ```
- **응답 본문 (JSON)**:
  ```json
  {
    "status": "SUCCESS",
    "data": {
      "reset_ticket_id": "AUTH-20370630-0192",
      "verification_url": "https://gyodong-live.com/auth/verify?t=AUTH-20370630-0192",
      "expires_at": "2037-06-30T17:30:00+09:00"
    }
  }
  ```

### 프로토콜 2: 주문 배송지 주소 변경 API
- **엔드포인트**: `PATCH /v1/orders/{order_id}/shipping-address`
- **목적**: 상품이 출고되기 전(상태: '결제완료' 또는 '주문접수') 단계에서 고객이 요청한 신규 배송지로 주소를 즉시 정정합니다.
- **제약 조건**: 이미 산지에서 송장이 출력되었거나 집하 완료된 '배송중' 상태에서는 변경이 불가하며 거부 사유를 반환합니다.
- **요청 본문 (JSON)**:
  ```json
  {
    "order_id": "ORD-20370630-9982",
    "recipient_name": "홍길동",
    "recipient_phone": "010-9876-5432",
    "new_address": "서울특별시 강남구 테헤란로 123 4층",
    "new_zipcode": "06234"
  }
  ```
- **응답 본문 (JSON - 성공 시)**:
  ```json
  {
    "status": "SUCCESS",
    "data": {
      "order_id": "ORD-20370630-9982",
      "status": "ORDER_CONFIRMED",
      "updated_address": "서울특별시 강남구 테헤란로 123 4층",
      "message": "배송지 주소가 정상적으로 변경되었습니다."
    }
  }
  ```
- **응답 본문 (JSON - 출고 완료로 변경 불가 시)**:
  ```json
  {
    "status": "FAILED",
    "error_code": "ALREADY_SHIPPED",
    "message": "해당 주문은 이미 산지 출고 및 송장 집하가 완료되어 배송지 변경이 불가합니다."
  }
  ```

### 프로토콜 3: 상담원/관리자 긴급 이관 (Escalation) API
- **엔드포인트**: `POST /v1/support/escalate`
- **목적**: 악성 민원 고객, 폭언, 법적 분쟁 소지, 시스템에서 처리할 수 없는 환불 예외 사안에 대해 청년회 CS 전담자(이민준)에게 티켓을 이관합니다.
- **요청 본문 (JSON)**:
  ```json
  {
    "user_key": "kakao_user_unique_hash_98234",
    "category": "DISPUTE_REFUND",
    "sentiment": "NEGATIVE",
    "summary": "신선 농산물 단순 변심 환불 불가 규정에 불만 제기 및 소비자원 고발 언급",
    "chat_history": [
      {"role": "user", "content": "그냥 마음에 안 든다고요! 당장 환불해 줘요."},
      {"role": "bot", "content": "신선식품은 단순 변심 환불이 불가함을 안내드렸습니다."}
    ]
  }
  ```
- **응답 본문 (JSON)**:
  ```json
  {
    "status": "SUCCESS",
    "data": {
      "ticket_id": "ESC-20370630-0043",
      "assigned_to": "이민준 (청년회 CS총괄)",
      "operating_hours": "평일 09:00~18:00",
      "message": "상담원 이관 티켓이 등록되었습니다. 담당자가 순차 연락 예정입니다."
    }
  }
  ```

---

## 3. 장애 발생 시 방어적 폴백(Fallback) 가이드라인

심사 기간 중 외부 액션 서버와의 네트워크 지연 또는 Gemini API의 일시적 오류가 발생하더라도, 60초 타임아웃 실격을 방지하고 반드시 45초 이내에 안전한 SimpleText 응답을 반환해야 합니다.

- **외부 액션 서버 장애 및 타임아웃 발생 시**:
  - 액션 서버 호출 제한 시간을 3.0초로 지정하여 지연 누적을 방지합니다.
  - 응답이 지연되거나 실패할 경우 사용자에게 즉시 아래와 같은 표준 안내 메시지를 반환합니다.
  - *폴백 메시지 예시*: "현재 산지 주문 시스템 점검으로 인해 실시간 처리가 지연되고 있습니다. 고객님의 문의 사항은 청년회 담당자에게 긴급 전달되었으며, 평일 운영 시간(09:00~18:00) 내 신속히 확인 후 연락드리겠습니다. 불편을 드려 대단히 죄송합니다."
- **Google Gemini API 호출 지연 및 할당량 초과 시**:
  - 기본 모델인 Gemini Flash Lite(`gemini-3.5-flash-lite` 또는 `gemini-2.0-flash-lite`) 호출 실패 시 즉시 보조 모델(`gemini-1.5-flash-8b`)로 재시도합니다.
  - 2차 재시도마저 10초 이내에 응답하지 못할 경우, 사전에 구축된 룰 기반 기본 응답(마을별 분리 배송 안내 및 운영 시간 안내)을 즉시 조합하여 반환함으로써 60초 초과 실격을 방지합니다.
- **글자 수 초과 방어 로직**:
  - LLM 응답이 480자를 초과할 경우 마지막 온점(`.`) 또는 줄바꿈(`\n`) 기준으로 문장을 완결 짓고 사족을 절단합니다.
  - 이를 통해 500자 초과 10건 누적으로 인한 즉시 탈락을 원천적으로 차단합니다.
