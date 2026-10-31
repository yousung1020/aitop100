"""
공식 대회 규격 7대 P1 결함 전면 해결 검증 테스트 모듈 (tests/test_official_p1_fixes.py).

7대 결함:
1. [Unit 3] API 경로·본문 공식 규격 준수 (POST /api/orders/{order_no}/address-change-requests, body: new_address만 허용)
2. [Unit 3] 필수 TC ID 헤더 (X-Aitop100-Test-Case-Id) 주입 및 전송
3. [Unit 3] 공식 성공 응답 판정 (request_status: SUBMITTED -> success=True) 및 빈 본문 400/404 안전 처리
4. [Unit 3·4] 공개 TC 15개 필수 API (API-01~API-35) 공식 조회 및 접수
5. [Unit 4] 가능 여부 문의 시 임의 변경 실행 방지 (집하 조회 후 동·호수 상세주소 확인 유도)
6. [Unit 4] 후속 대화 및 상담 문맥 유지 (SessionStore 멀티턴 및 웹훅 TC ID/상담일/인입 계정 연동)
7. [Unit 4] 접수와 완료 명확 분리 (배송지 변경 요청 접수 안내 및 완료 확약 금지)
"""

import pytest
import httpx

from app.actions.client import ActionServerClient
from app.actions.mock_server import MockActionHandler
from app.agent.orchestrator import AgentOrchestrator
from app.agent.session import SessionStore
from app.main import app, set_orchestrator
from app.schema import KakaoSkillResponse


@pytest.fixture
def mock_handler():
    return MockActionHandler()


@pytest.fixture
def action_client(mock_handler):
    return ActionServerClient(
        base_url="http://mock-action.local",
        default_test_case_id="L-03",
        mock_handler=mock_handler,
    )


@pytest.fixture
def orchestrator(action_client):
    return AgentOrchestrator(
        api_key="",
        action_client=action_client,
        session_store=SessionStore(),
    )


@pytest.fixture
async def async_client(orchestrator):
    set_orchestrator(orchestrator)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    set_orchestrator(None)


# ==============================================================================
# 결함 1 & 2: API 경로·본문 공식 규격 및 필수 TC ID 헤더 검증
# ==============================================================================

@pytest.mark.anyio
async def test_official_address_change_endpoint_and_headers(action_client, mock_handler):
    """
    공식 주소 변경은 POST /api/orders/{order_no}/address-change-requests 경로를 사용하며
    본문에 오직 new_address 단일 필드만 포함하고, X-Aitop100-Test-Case-Id 헤더가 필수 전송되는지 검증
    """
    res = await action_client.change_address(
        order_no="100100003",
        new_address="경기도 성남시 분당구 판교역로 166 8층",
        test_case_id="L-03",
    )

    assert res["success"] is True
    assert res["request_status"] == "SUBMITTED"
    assert "request_id" in res
    assert res["order_no"] == "100100003"

    # Mock에 기록된 실제 HTTP 요청 검증
    last_req = mock_handler.history[-1]
    assert last_req["method"] == "POST"
    assert last_req["path"] == "/api/orders/100100003/address-change-requests"
    assert last_req["headers"].get("x-aitop100-test-case-id") == "L-03"
    # 본문 검증: new_address만 존재해야 하며, 임의의 zipcode, user_key, recipient_name 등이 없어야 함
    assert last_req["body"] == {"new_address": "경기도 성남시 분당구 판교역로 166 8층"}
    assert "recipient_name" not in last_req["body"]
    assert "user_key" not in last_req["body"]


# ==============================================================================
# 결함 3: 공식 성공 응답 판정 (SUBMITTED -> success=True) 및 빈 본문 400/404 방어 검증
# ==============================================================================

@pytest.mark.anyio
async def test_official_response_status_submitted_success(action_client):
    """request_status: SUBMITTED 반환 시 success=True 로 정확히 판정되는지 검증"""
    res = await action_client.change_address(
        order_no="ORDER-PENDING-001",
        new_address="서울시 강남구 테헤란로 200 4층",
        test_case_id="L-03",
    )
    assert res["request_status"] == "SUBMITTED"
    assert res["success"] is True
    assert res["status"] == "SUCCESS"


@pytest.mark.anyio
async def test_empty_body_400_and_404_handling(action_client):
    """빈 본문의 400 및 404 응답 시 JSON_PARSE_ERROR가 아닌 HTTP 실패 상태로 안전 처리되는지 검증"""
    # 1. 빈 본문 400
    res_400 = await action_client._safe_request("/api/test/empty-400", method="POST")
    assert res_400["success"] is False
    assert res_400["status"] == "FAILED"
    assert res_400["status_code"] == 400
    assert res_400["error_code"] == "HTTP_400"
    assert res_400.get("error_code") != "JSON_PARSE_ERROR"

    # 2. 빈 본문 404
    res_404 = await action_client._safe_request("/api/test/empty-404", method="GET")
    assert res_404["success"] is False
    assert res_404["status"] == "FAILED"
    assert res_404["status_code"] == 404
    assert res_404["error_code"] == "HTTP_404"
    assert res_404.get("error_code") != "JSON_PARSE_ERROR"


# ==============================================================================
# 결함 4: 공개 TC 필수 조회 및 접수 API 전수 검증 (API-01 ~ API-35)
# ==============================================================================

@pytest.mark.anyio
async def test_public_test_case_apis_comprehensive(action_client):
    """공개 TC 필수 API 10종 이상의 공식 호출 스펙 검증"""
    # API-01: 상품 조회
    prod = await action_client.get_product("WTM-08", test_case_id="L-47")
    assert prod["sku"] == "WTM-08"

    # API-03: 로트 조회
    lot = await action_client.get_lot("KD-WTM-370624-03", test_case_id="L-11")
    assert lot["lot_id"] == "KD-WTM-370624-03"

    # API-04: 로트 조사 조회
    inv = await action_client.get_lot_investigation("KD-WTM-370624-03", test_case_id="L-11")
    assert inv["lot_id"] == "KD-WTM-370624-03"

    # API-06: 로트별 상담 이력 검색
    tickets = await action_client.search_tickets_by_lot("KD-WTM-370624-03", test_case_id="L-11")
    assert "items" in tickets or "data" in tickets

    # API-07: 주문 조회
    order = await action_client.get_order("100100005", test_case_id="L-05")
    assert order["order_no"] == "100100005"

    # API-11: 배송 검색
    ship = await action_client.search_shipments_by_order("100100003", test_case_id="L-03")
    assert ship["success"] is True

    # API-17: 결제 조회
    pay = await action_client.get_payment("PAY-3706-0003", test_case_id="L-05")
    assert pay["approval_no"] == "PAY-3706-0003"

    # API-29: 환불 신청 접수
    refund = await action_client.request_refund(
        order_no="100100011",
        amount=34900,
        reason="수박 곰팡이 하자 전액환불",
        test_case_id="L-11",
    )
    assert refund["success"] is True
    assert refund["request_status"] == "SUBMITTED"

    # API-32: 현금영수증 발행 접수
    cr = await action_client.issue_cash_receipt(
        approval_no="PAY-3706-0003",
        receipt_number="019-2314-9701",
        test_case_id="L-05",
    )
    assert cr["success"] is True
    assert cr["request_status"] == "SUBMITTED"

    # API-35: 에스컬레이션 접수
    esc = await action_client.escalate(
        lane="LANE2_HANDOFF",
        reason="수박 곰팡이 위해 신고 및 판매자 조사 요청",
        test_case_id="L-11",
    )
    assert esc["success"] is True
    assert esc["status"] == "ASSIGNED"


# ==============================================================================
# 결함 5: 가능 여부 문의 시 임의 변경 실행 방지 검증
# ==============================================================================

@pytest.mark.anyio
async def test_inquiry_with_address_does_not_execute_change(orchestrator, mock_handler):
    """
    '주문번호 ORDER-PENDING-001 주소 경기 성남시로 변경 가능한가요?' 발화 시:
    1. API-24를 직접 호출하여 주소를 변경하지 않음.
    2. API-11 배송 조회를 통해 집하 전 상태 확인 및 동·호수 상세주소 확인 요청 안내 반환.
    3. 수령인을 임의의 '고객님'으로 덮어쓰지 않음.
    """
    initial_orders = dict(mock_handler.orders["ORDER-PENDING-001"])

    res = await orchestrator.respond(
        "주문번호 ORDER-PENDING-001 주소 경기 성남시로 변경 가능한가요?",
        user_key="user_kakao_111",
        test_case_id="L-03",
    )
    text = res.template.outputs[0].simpleText.text

    # API-24가 호출되지 않았음을 Mock history로 증명
    api_24_calls = [
        h for h in mock_handler.history
        if h["path"] == "/api/orders/ORDER-PENDING-001/address-change-requests"
    ]
    assert len(api_24_calls) == 0

    # API-11은 호출되어 집하 상태를 확인했어야 함
    api_11_calls = [
        h for h in mock_handler.history
        if h["path"] == "/api/shipments" and h["query"].get("order_no") == "ORDER-PENDING-001"
    ]
    assert len(api_11_calls) >= 1

    # 안내 문구 검증: 변경 확약 금지, 집하 전 가능 안내, 동·호수 상세주소 요청
    assert "정상 변경되었습니다" not in text
    assert "집하 전" in text or "집하 스캔 전" in text
    assert "동·호수" in text or "상세" in text

    # 수령인 및 주소 원본 유지 검증
    current_order = mock_handler.orders["ORDER-PENDING-001"]
    assert current_order["recipient_name"] == initial_orders["recipient_name"]
    assert current_order["address"] == initial_orders["address"]


# ==============================================================================
# 결함 6: 멀티턴 대화 및 후속 상담 문맥 유지 검증
# ==============================================================================

@pytest.mark.anyio
async def test_multiturn_address_change_context_flow(orchestrator, mock_handler):
    """
    L-03 시나리오:
    1턴: '주소 잘못 넣었어요. 경기 성남시로 바꿔주세요.' (주문번호 없음)
         -> 주문번호 및 동·호수 상세주소 요청
    2턴: 'ORDER-PENDING-001' (고객이 주문번호만 답변)
         -> 세션 문맥 유지, 집하 전 확인, 동·호수 상세주소 요청
    3턴: '판교역로 166 8층으로 보내주세요' (상세주소 답변)
         -> '경기 성남시 판교역로 166 8층'으로 조합하여 API-24 호출 및 접수 안내
    """
    user_key = "user_seo_multiturn"

    # 1턴: 주문번호 누락 주소 변경 문의
    res1 = await orchestrator.respond(
        "주소 잘못 넣었어요. 경기 성남시로 바꿔주세요.",
        user_key=user_key,
        test_case_id="L-03",
    )
    text1 = res1.template.outputs[0].simpleText.text
    assert "주문번호" in text1
    # API-24 미호출
    assert not any(h["path"].endswith("/address-change-requests") for h in mock_handler.history)

    # 2턴: 주문번호만 응답
    res2 = await orchestrator.respond(
        "ORDER-PENDING-001",
        user_key=user_key,
        test_case_id="L-03",
    )
    text2 = res2.template.outputs[0].simpleText.text
    assert "ORDER-PENDING-001" in text2
    assert "집하" in text2
    assert "동·호수" in text2 or "상세" in text2
    # 아직 상세주소가 완비되지 않았으므로 API-24 미호출
    assert not any(h["path"].endswith("/address-change-requests") for h in mock_handler.history)

    # 3턴: 상세주소 제공
    res3 = await orchestrator.respond(
        "판교역로 166 8층으로 보내주세요",
        user_key=user_key,
        test_case_id="L-03",
    )
    text3 = res3.template.outputs[0].simpleText.text

    # API-24 정상 호출 확인
    api_24_calls = [
        h for h in mock_handler.history
        if h["path"] == "/api/orders/ORDER-PENDING-001/address-change-requests"
    ]
    assert len(api_24_calls) == 1
    # '경기 성남시'와 '판교역로 166 8층'이 조합된 전체 주소로 전송되었는지 확인
    assert "경기 성남시 판교역로 166 8층" in api_24_calls[0]["body"]["new_address"]

    # 응답 안내 확인
    assert "ORDER-PENDING-001" in text3
    assert "접수" in text3


# ==============================================================================
# 결함 6: 웹훅 인입 시 TC ID, 상담일, 인입 계정 추출 및 오케스트레이터 전달 검증
# ==============================================================================

@pytest.mark.anyio
async def test_webhook_extracts_headers_and_client_extra(async_client, mock_handler):
    """
    POST /skill 호출 시 X-Aitop100-Test-Case-Id 헤더와 clientExtra 메타데이터가
    오케스트레이터와 액션 클라이언트로 정확히 전달되는지 검증
    """
    payload = {
        "bot": {"id": "bot_1"},
        "intent": {"id": "intent_1"},
        "action": {
            "id": "action_1",
            "clientExtra": {
                "test_case_id": "L-03",
                "consultation_date": "2037-06-30T15:16:00Z",
                "incoming_account": {
                    "user_id": "user_seo_123",
                    "user_name": "서지호",
                    "phone": "019-2314-5231",
                },
            },
        },
        "userRequest": {
            "user": {"id": "user_seo_123"},
            "utterance": "주문번호 100100003 경기 성남시 판교역로 166 8층으로 변경해주세요",
        },
    }
    headers = {
        "X-Aitop100-Test-Case-Id": "L-03",
        "X-Consultation-Date": "2037-06-30T15:16:00Z",
    }

    response = await async_client.post("/skill", json=payload, headers=headers)
    assert response.status_code == 200

    parsed = KakaoSkillResponse.model_validate(response.json())
    text = parsed.template.outputs[0].simpleText.text
    assert "100100003" in text
    assert "접수" in text

    # 액션 클라이언트 요청에 L-03 헤더가 전달되었는지 확인
    addr_calls = [
        h for h in mock_handler.history
        if h["path"] == "/api/orders/100100003/address-change-requests"
    ]
    assert len(addr_calls) == 1
    assert addr_calls[0]["headers"].get("x-aitop100-test-case-id") == "L-03"


# ==============================================================================
# 결함 7: 접수와 완료 명확 분리 (확약 금지) 검증
# ==============================================================================

@pytest.mark.anyio
async def test_address_change_acknowledgement_not_completion(orchestrator):
    """
    배송지 변경 접수 성공 시 '배송지가 정상 변경되었습니다'라고 완료를 확약하지 않고,
    '요청 접수' 상태이며 물류센터 확인 후 반영된다는 사실을 명확히 고지하는지 검증
    """
    res = await orchestrator.respond(
        "주문번호 ORDER-PENDING-001 주소 서울시 강남구 테헤란로 200 5층으로 변경해주세요",
        user_key="user_kakao_111",
        test_case_id="L-03",
    )
    text = res.template.outputs[0].simpleText.text

    # 확약 표현 금지
    assert "정상 변경되었습니다" not in text
    assert "이미 변경 완료" not in text

    # 접수 및 물류센터 확인 안내 포함
    assert "요청이 성공적으로 접수" in text or "요청 접수" in text
    assert "접수번호" in text
    assert "확인 후" in text or "물류" in text
