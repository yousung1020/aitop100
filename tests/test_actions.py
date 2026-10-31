"""
산지 액션 서버 연동 모듈 단위 테스트 (tests/test_actions.py)
MockActionHandler와 ActionServerClient 간의 3대 전산 업무 프로토콜 및
장애 상황(타임아웃, 네트워크 실패, 500 오류) 방어 Fallback 로직을 검증합니다.
"""

import pytest
import httpx
from app.actions.client import ActionServerClient, FALLBACK_MESSAGE
from app.actions.mock_server import MockActionHandler


@pytest.fixture
def mock_handler():
    return MockActionHandler()


@pytest.fixture
def action_client(mock_handler):
    return ActionServerClient(
        base_url="http://mock-action-server.local",
        token="test_secret_token_12345",
        timeout=1.0,  # 테스트 신속성을 위해 1.0초로 설정
        mock_handler=mock_handler,
    )


# ==========================================
# 1. 계정 및 세션 복구 테스트
# ==========================================

@pytest.mark.anyio
async def test_reset_account_session_success(action_client):
    """정상 전화번호와 user_key로 세션 복구 요청 시 인증코드 및 티켓 발급 확인"""
    res = await action_client.reset_account_session(
        user_key="user_kakao_001",
        phone_number="010-1234-5678",
        reason="로그인 5회 실패로 세션 잠김",
    )
    assert res["status"] == "SUCCESS"
    assert res["success"] is True
    assert "data" in res
    data = res["data"]
    assert data["reset_ticket_id"].startswith("AUTH-20370630-")
    assert "verification_code" in data
    assert "verification_url" in data
    assert data["reason"] == "로그인 5회 실패로 세션 잠김"


@pytest.mark.anyio
async def test_reset_account_session_invalid_phone(action_client):
    """비정상적인 전화번호 형식 제출 시 INVALID_PHONE_NUMBER 에러 반환 확인"""
    res = await action_client.reset_account_session(
        user_key="user_kakao_001",
        phone_number="1234",  # 잘못된 번호
        reason="비밀번호 분실",
    )
    assert res["status"] == "FAILED"
    assert res["success"] is False
    assert res["error_code"] == "INVALID_PHONE_NUMBER"


@pytest.mark.anyio
async def test_reset_account_session_missing_user_key(action_client):
    """user_key 누락 시 INVALID_PARAMS 에러 반환 확인"""
    res = await action_client.reset_account_session(
        user_key="",
        phone_number="010-1234-5678",
    )
    assert res["status"] == "FAILED"
    assert res["success"] is False
    assert res["error_code"] == "INVALID_PARAMS"


# ==========================================
# 2. 배송지 주소 변경 테스트
# ==========================================

@pytest.mark.anyio
async def test_change_shipping_address_pending_success(action_client):
    """집하 전 주문(ORDER-PENDING-001)에 대해 신규 주소 정정 성공 확인"""
    res = await action_client.change_shipping_address(
        order_id="ORDER-PENDING-001",
        user_key="user_kakao_111",
        recipient_name="홍길동",
        recipient_phone="010-1111-2222",
        zipcode="06234",
        new_address="서울특별시 서초구 강남대로 456",
        detailed_address="10층",
    )
    assert res["status"] == "SUCCESS"
    assert res["success"] is True
    data = res["data"]
    assert data["order_id"] == "ORDER-PENDING-001"
    assert data["updated_address"] == "서울특별시 서초구 강남대로 456 10층"
    assert "정상적으로 변경되었습니다" in data["message"]


@pytest.mark.anyio
async def test_change_shipping_address_shipped_fail(action_client):
    """이미 집하 완료된 주문(ORDER-SHIPPED-001) 주소 변경 요청 시 ALREADY_SHIPPED 거부 확인"""
    res = await action_client.change_shipping_address(
        order_id="ORDER-SHIPPED-001",
        user_key="user_kakao_222",
        recipient_name="김철수",
        recipient_phone="010-3333-4444",
        zipcode="13494",
        new_address="인천광역시 연수구 송도동 789",
        detailed_address="1동 101호",
    )
    assert res["status"] == "FAILED"
    assert res["success"] is False
    assert res["error_code"] == "ALREADY_SHIPPED"
    assert "이미 산지 출고 및 송장 집하가 완료되어" in res["message"]


@pytest.mark.anyio
async def test_change_shipping_address_unknown_order(action_client):
    """미등록 주문은 즉시 404 ORDER_NOT_FOUND 에러 반환 확인"""
    res = await action_client.change_shipping_address(
        order_id="ORD-SHIPPED-9988",
        user_key="user_kakao_999",
        recipient_name="박영희",
        recipient_phone="010-9999-8888",
        zipcode="03000",
        new_address="부산광역시 해운대구 마린시티",
    )
    assert res["status"] == "FAILED"
    assert res["error_code"] == "ORDER_NOT_FOUND"
    assert res["message"] == "해당 주문을 찾을 수 없습니다."


@pytest.mark.anyio
async def test_change_shipping_address_missing_order_id(action_client):
    """주문번호 누락 시 MISSING_ORDER_ID 에러 반환 확인"""
    res = await action_client.change_shipping_address(
        order_id="",
        user_key="user_kakao_111",
        recipient_name="홍길동",
        recipient_phone="010-1111-2222",
        zipcode="06234",
        new_address="서울특별시 서초구 강남대로 456",
    )
    assert res["status"] == "FAILED"
    assert res["error_code"] == "MISSING_ORDER_ID"


@pytest.mark.anyio
async def test_change_shipping_address_missing_address(action_client):
    """신규 주소 누락 시 MISSING_ADDRESS 에러 반환 확인"""
    res = await action_client.change_shipping_address(
        order_id="ORDER-PENDING-001",
        user_key="user_kakao_111",
        recipient_name="홍길동",
        recipient_phone="010-1111-2222",
        zipcode="06234",
        new_address="",
    )
    assert res["status"] == "FAILED"
    assert res["error_code"] == "MISSING_ADDRESS"


# ==========================================
# 3. 긴급 상담원/관리자 이관 티켓 테스트
# ==========================================

@pytest.mark.anyio
async def test_create_escalation_ticket_under_50000(action_client):
    """5만 원 이하 일반 CS 이관 시 이민준 총괄(LEVEL_2_MANAGER) 배정 및 티켓 채번 확인"""
    res = await action_client.create_escalation_ticket(
        user_key="user_kakao_333",
        category="DELIVERY_DELAY",
        customer_name="이순신",
        contact="010-5555-6666",
        issue_summary="배송 2일 지연 문의 및 확인 요청",
        claim_amount=30000,
        requested_resolution="배송 현황 확인 및 문자 안내",
    )
    assert res["status"] == "SUCCESS"
    assert res["success"] is True
    data = res["data"]
    assert data["ticket_id"].startswith("TICKET-20370630-")
    assert data["assigned_to"] == "이민준 (청년회 CS총괄)"
    assert data["authority_level"] == "LEVEL_2_MANAGER"
    assert data["is_urgent"] is False
    assert data["claim_amount"] == 30000


@pytest.mark.anyio
async def test_create_escalation_ticket_over_50000(action_client):
    """5만 원 초과 고액 건도 이민준 1차 심사를 거치며 조합장 승인 필요 안내 및 플래그 포함 확인"""
    res = await action_client.create_escalation_ticket(
        user_key="user_kakao_444",
        category="DAMAGED_PRODUCT",
        customer_name="강감찬",
        contact="010-7777-8888",
        issue_summary="갈치 3상자 해동 부패로 전액 환불 요청 (총 120,000원)",
        claim_amount=120000,
        requested_resolution="전액 환불",
    )
    assert res["status"] == "SUCCESS"
    assert res["success"] is True
    data = res["data"]
    assert data["ticket_id"].startswith("TICKET-20370630-")
    assert data["assigned_to"] == "이민준 (청년회 CS총괄)"
    assert data["authority_level"] == "LEVEL_2_MANAGER"
    assert data["is_urgent"] is True
    assert data["claim_amount"] == 120000
    assert data["requires_chairman_approval"] is True
    assert "5만 원 초과 건으로 고길동 조합장 승인 필요 사안" in data["approval_note"]
    assert "5만 원 초과 건으로 고길동 조합장 승인 필요 사안" in data["message"]


@pytest.mark.anyio
async def test_create_escalation_ticket_dispute_refund_category(action_client):
    """금액이 5만원 이하이더라도 분쟁 환불(DISPUTE_REFUND) 카테고리는 긴급(is_urgent=True) 지정 확인"""
    res = await action_client.create_escalation_ticket(
        user_key="user_kakao_555",
        category="DISPUTE_REFUND",
        customer_name="을지문덕",
        contact="010-2222-3333",
        issue_summary="단순변심 거절에 따른 소비자원 고발 언급",
        claim_amount=25000,
    )
    assert res["status"] == "SUCCESS"
    data = res["data"]
    assert data["is_urgent"] is True
    assert data["assigned_to"] == "이민준 (청년회 CS총괄)"


@pytest.mark.anyio
async def test_create_escalation_ticket_missing_user_key(action_client):
    """user_key 누락 시 MISSING_USER_KEY 에러 확인"""
    res = await action_client.create_escalation_ticket(
        user_key="",
        category="GENERAL",
        customer_name="무명",
        contact="010-0000-0000",
        issue_summary="일반 문의",
    )
    assert res["status"] == "FAILED"
    assert res["error_code"] == "MISSING_USER_KEY"


# ==========================================
# 4. 장애 방어 및 Fallback 테스트
# ==========================================

@pytest.mark.anyio
async def test_client_timeout_fallback(mock_handler):
    """서버 지연(delay)이 클라이언트 timeout(0.2초)을 초과할 때 안전한 FALLBACK 반환 확인"""
    mock_handler.delay = 0.5  # 0.5초 지연
    async with ActionServerClient(
        timeout=0.2,  # 0.2초 초과 시 타임아웃
        mock_handler=mock_handler,
    ) as fast_client:
        res = await fast_client.reset_account_session(
            user_key="user_timeout",
            phone_number="010-1234-5678",
        )
        assert res["status"] == "FALLBACK"
        assert res["success"] is False
        assert res["error_code"] == "TIMEOUT"
        assert res["message"] == FALLBACK_MESSAGE


@pytest.mark.anyio
async def test_client_network_error_fallback(mock_handler, action_client):
    """네트워크 연결 단절 시 NETWORK_ERROR FALLBACK 반환 확인"""
    mock_handler.force_network_error = True
    res = await action_client.change_shipping_address(
        order_id="ORDER-PENDING-001",
        user_key="user_111",
        recipient_name="홍길동",
        recipient_phone="010-1111-2222",
        zipcode="06234",
        new_address="서울특별시 송파구",
    )
    assert res["status"] == "FALLBACK"
    assert res["success"] is False
    assert res["error_code"] == "NETWORK_ERROR"
    assert res["message"] == FALLBACK_MESSAGE


@pytest.mark.anyio
async def test_client_server_500_fallback(mock_handler, action_client):
    """백엔드 액션 서버 500 내부 서버 오류 발생 시 SERVER_ERROR FALLBACK 반환 확인"""
    mock_handler.force_status_code = 500
    res = await action_client.create_escalation_ticket(
        user_key="user_kakao_333",
        category="GENERAL",
        customer_name="이순신",
        contact="010-5555-6666",
        issue_summary="시스템 오류 유발 테스트",
    )
    assert res["status"] == "FALLBACK"
    assert res["success"] is False
    assert res["error_code"] == "SERVER_ERROR"
    assert res["message"] == FALLBACK_MESSAGE


# ==========================================
# 5. 별칭 메서드 및 편의 기능 테스트
# ==========================================

@pytest.mark.anyio
async def test_alias_methods(action_client):
    """클라이언트 별칭 메서드(update_shipping_address, escalate_to_manager 등) 정상 연동 확인"""
    # 1) 주소 변경 별칭
    res_addr = await action_client.update_shipping_address(
        order_id="ORDER-PENDING-001",
        new_address="제주특별자치도 제주시 첨단로 242",
        zipcode="63309",
        user_key="user_kakao_111",
    )
    assert res_addr["status"] == "SUCCESS"
    assert res_addr["data"]["order_id"] == "ORDER-PENDING-001"

    # 2) 긴급 이관 별칭
    res_esc = await action_client.escalate_to_manager(
        user_key="user_kakao_alias",
        category="PRODUCT_QUALITY",
        summary="감귤 당도 미달 문의",
        claim_amount=15000,
    )
    assert res_esc["status"] == "SUCCESS"
    assert res_esc["data"]["category"] == "PRODUCT_QUALITY"


@pytest.mark.anyio
async def test_auth_bearer_token_sent(mock_handler):
    """클라이언트에 전달된 토큰이 요청 Authorization 헤더에 Bearer 토큰으로 포함되는지 확인"""
    captured_headers = {}

    async def capturing_handler(request: httpx.Request) -> httpx.Response:
        captured_headers.update(dict(request.headers))
        return await mock_handler.handle_request(request)

    custom_transport = httpx.MockTransport(capturing_handler)
    async with httpx.AsyncClient(transport=custom_transport, base_url="http://test") as raw_client:
        client = ActionServerClient(
            base_url="http://test",
            token="SECRET_TOKEN_XYZ",
            client=raw_client,
        )
        await client.reset_account_session(
            user_key="user_auth",
            phone_number="010-9999-0000",
        )

    assert "authorization" in captured_headers
    assert captured_headers["authorization"] == "Bearer SECRET_TOKEN_XYZ"


@pytest.mark.anyio
async def test_documented_routes_without_project_mock():
    """프로젝트 Mock의 별칭 허용 여부와 무관하게 실제 송신 계약을 검사합니다."""
    import json

    requests = []

    async def strict_server(request):
        requests.append((request.method, request.url.path))
        body = json.loads(request.content)
        if request.method == "PATCH" and request.url.path == "/v1/orders/ORD-123/shipping-address":
            assert body["order_id"] == "ORD-123"
            assert body["new_address"] == "새 주소"
            assert body["new_zipcode"] == "12345"
        elif request.method == "POST" and request.url.path == "/v1/support/escalate":
            assert body["summary"] == "상담 요청"
        else:
            return httpx.Response(404, json={"status": "FAILED"})
        return httpx.Response(200, json={"status": "SUCCESS"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(strict_server)) as raw:
        async with ActionServerClient(base_url="http://test", client=raw) as client:
            address = await client.update_shipping_address("ORD-123", "새 주소", "12345", user_key="owner")
            ticket = await client.escalate_to_manager("owner", "GENERAL", "상담 요청")
    assert address["success"] is True
    assert ticket["success"] is True
    assert requests == [("PATCH", "/v1/orders/ORD-123/shipping-address"), ("POST", "/v1/support/escalate")]


@pytest.mark.anyio
@pytest.mark.parametrize("method,path", [
    ("POST", "/v1/orders/change-address"),
    ("POST", "/v1/orders/ORDER-PENDING-001/shipping-address"),
    ("POST", "/v1/tickets/escalate"),
])
async def test_mock_rejects_undocumented_routes(mock_handler, method, path):
    response = await mock_handler.handle_request(httpx.Request(method, "http://test" + path, json={}))
    assert response.status_code == 404


@pytest.mark.anyio
@pytest.mark.parametrize("order_id,user_key,expected_code,expected_msg", [
    ("ORDER-PENDING-001", "other_user", "FORBIDDEN", "해당 주문에 대한 접근 권한이 없습니다."),
    ("ORDER-SHIPPED-001", "other_user", "FORBIDDEN", "해당 주문에 대한 접근 권한이 없습니다."),
    ("ORDER-PENDING-001", "", "FORBIDDEN", "해당 주문에 대한 접근 권한이 없습니다."),
    ("NO-SUCH-ORDER", "user_kakao_111", "ORDER_NOT_FOUND", "해당 주문을 찾을 수 없습니다."),
])
async def test_inaccessible_order_does_not_change_or_disclose(mock_handler, action_client, order_id, user_key, expected_code, expected_msg):
    import copy

    before = copy.deepcopy(mock_handler.orders)
    result = await action_client.update_shipping_address(order_id, "변경 주소", "12345", user_key=user_key)
    assert result["success"] is False
    assert result["error_code"] == expected_code
    assert result["message"] == expected_msg
    assert "data" not in result
    assert mock_handler.orders == before


@pytest.mark.anyio
async def test_order_name_does_not_determine_shipping_state(mock_handler, action_client):
    mock_handler.register_order("ORD-NOT-SHIPPED", user_key="owner", status="INVOICE_REGISTERED")
    result = await action_client.update_shipping_address("ORD-NOT-SHIPPED", "새 주소", "12345", user_key="owner")
    assert result["success"] is True


@pytest.mark.anyio
@pytest.mark.parametrize("failure", ["network", "timeout", "server"])
async def test_failed_escalation_does_not_claim_delivery(mock_handler, failure):
    mock_handler.force_network_error = failure == "network"
    mock_handler.force_status_code = 500 if failure == "server" else None
    mock_handler.delay = 0.1 if failure == "timeout" else 0
    async with ActionServerClient(mock_handler=mock_handler, timeout=0.01) as client:
        result = await client.escalate_to_manager("owner", "GENERAL", "문의")
    assert result["status"] == "FALLBACK"
    assert result["success"] is False
    assert result["data"] is None
    assert "이관 접수가 완료되지 못했습니다" in result["message"]
    assert "전달되었" not in result["message"]
    assert "연락드리겠" not in result["message"]
    assert mock_handler.ticket_counter == 0
