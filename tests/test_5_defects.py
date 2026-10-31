"""5대 핵심 결함 수정 사항 전수 검증 테스트 (tests/test_5_defects.py).

검증 항목:
1. L-05 현금영수증 API 연동 (API-07 -> API-32, 카드 결제 제외)
2. L-47 가격 인하 보상 API 연동 (API-07 -> API-01 -> API-33, API-29 절대 미호출)
3. L-23 타인 주문 조회 방어 및 에스컬레이션 (API-07 -> API-35, API-11 절대 미호출)
4. 배송 조회 실패 시 주소 변경 접수 차단 (API-11 실패 시 API-24 호출 금지)
5. Mock 접수 계약 스펙 일치 (동일 대상 재접수 멱등성, 원본 주소 즉시 변경 방지, 테스트 데이터 완비)
"""

import pytest
import httpx
from app.actions.client import ActionServerClient
from app.actions.mock_server import MockActionHandler
from app.agent.orchestrator import AgentOrchestrator
from app.agent.session import SessionStore


@pytest.fixture
def mock_handler():
    return MockActionHandler()


@pytest.fixture
def action_client(mock_handler):
    return ActionServerClient(
        base_url="http://mock-action.local",
        default_test_case_id="L-05",
        mock_handler=mock_handler,
    )


@pytest.fixture
def orchestrator(action_client):
    return AgentOrchestrator(
        api_key="",
        action_client=action_client,
        session_store=SessionStore(),
    )


# ==============================================================================
# 1. L-05 현금영수증 API 연동 (API-07 -> API-32)
# ==============================================================================
@pytest.mark.anyio
async def test_defect_1_cash_receipt_flow(orchestrator, mock_handler):
    """
    무통장입금 주문(100100005)에 대해 현금영수증 요청 시:
    API-07로 승인번호(PAY-3706-0003) 확인 후 API-32로 receipt_number만 전송하여 접수
    """
    res = await orchestrator.respond(
        "지난주 주문건 100100005 현금영수증 소득공제 처리 부탁드립니다. 019-2314-9701로 발행해주세요.",
        user_key="MB-77005",
        test_case_id="L-05",
    )
    text = res.template.outputs[0].simpleText.text

    # API-07 호출 확인
    api_07 = [h for h in mock_handler.history if h["path"] == "/api/orders/100100005"]
    assert len(api_07) >= 1

    # API-32 호출 확인
    api_32 = [h for h in mock_handler.history if h["path"] == "/api/payments/PAY-3706-0003/cash-receipt-requests"]
    assert len(api_32) == 1
    assert api_32[0]["body"] == {"receipt_number": "019-2314-9701"}
    assert api_32[0]["headers"].get("x-aitop100-test-case-id") == "L-05"

    # 응답 안내 문구 검증
    assert "100100005" in text
    assert "접수" in text
    assert "019-2314-9701" in text
    assert len(text) <= 500


# ==============================================================================
# 2. L-47 가격 인하 보상 API 연동 (API-07 -> API-01 -> API-33; API-29 미호출)
# ==============================================================================
@pytest.mark.anyio
async def test_defect_2_price_drop_compensation_flow(orchestrator, mock_handler):
    """
    주문 100100047 가격 인하 차액 보상 요청 시:
    API-07(주문) -> API-01(상품 WTM-STD-8 정상가 27900원 확인) -> 차액 4100원 계산 ->
    API-33(CARE5000 쿠폰 발급 접수). 절대로 API-29(환불)을 호출하지 않음!
    """
    res = await orchestrator.respond(
        "어제 정가로 샀는데 오늘 보니 20% 세일이네요. 주문번호 100100047 차액 돌려주세요.",
        user_key="MB-77017",
        test_case_id="L-47",
        incoming_account={"member_id": "MB-77017", "name": "석민경"},
    )
    text = res.template.outputs[0].simpleText.text

    # API-07 호출 확인
    api_07 = [h for h in mock_handler.history if h["path"] == "/api/orders/100100047"]
    assert len(api_07) >= 1

    # API-01 호출 확인
    api_01 = [h for h in mock_handler.history if h["path"] == "/api/products/WTM-STD-8"]
    assert len(api_01) >= 1

    # API-33 쿠폰 발급 접수 확인
    api_33 = [h for h in mock_handler.history if h["path"] == "/api/members/MB-77017/coupon-issue-requests"]
    assert len(api_33) == 1
    assert api_33[0]["body"] == {"promo_code": "CARE5000"}

    # API-29 환불은 절대 호출되지 않아야 함!
    api_29 = [h for h in mock_handler.history if h["path"] == "/api/refunds"]
    assert len(api_29) == 0

    # 응답 안내 문구 검증 (차액 4,100원, 보상 쿠폰 CARE5000, 90일 유효)
    assert "4,100" in text or "4100" in text
    assert "CARE5000" in text or "5,000" in text
    assert "90일" in text
    assert len(text) <= 500


# ==============================================================================
# 3. L-23 타인 주문 조회 방어 및 에스컬레이션 (API-07 -> API-35; API-11 미호출)
# ==============================================================================
@pytest.mark.anyio
async def test_defect_3_other_account_privacy_defense(orchestrator, mock_handler):
    """
    윤재호(MB-77023)가 타인 주문(100100033, 소유: M-OTHER-99) 배송 상태 및 수령인 주소 요구 시:
    API-07로 소유자만 내부 확인 -> API-11 배송 검색 절대 미호출 -> API-35 에스컬레이션 접수 -> 타인 정보 비공개 안내
    """
    res = await orchestrator.respond(
        "저 로그인했어요. 주문번호 100100033 배송 상태랑 받는 사람 주소 확인해주세요.",
        user_key="MB-77023",
        test_case_id="L-23",
        incoming_account={"member_id": "MB-77023", "name": "윤재호"},
    )
    text = res.template.outputs[0].simpleText.text

    # API-07 호출 확인
    api_07 = [h for h in mock_handler.history if h["path"] == "/api/orders/100100033"]
    assert len(api_07) >= 1

    # API-11 배송 조회는 절대 호출되지 않아야 함!
    api_11 = [h for h in mock_handler.history if h["path"] == "/api/shipments"]
    assert len(api_11) == 0

    # API-35 에스컬레이션 호출 확인
    api_35 = [h for h in mock_handler.history if h["path"] == "/api/escalations"]
    assert len(api_35) == 1
    assert api_35[0]["body"]["lane"] == "LANE2_HANDOFF"

    # 비공개 단호한 안내 문구 검증
    assert "제공하지 않는 항목" in text or "타인의 주문" in text or "조회가 불가" in text
    # 타인의 실제 주소가 노출되지 않아야 함
    assert "사직로 161" not in text
    assert len(text) <= 500


# ==============================================================================
# 4. 배송 조회 실패 시 주소 변경 접수 차단
# ==============================================================================
@pytest.mark.anyio
async def test_defect_4_shipment_check_failure_blocks_address_change(orchestrator, mock_handler):
    """
    API-11 배송 조회가 500 에러 등으로 실패했을 때,
    집하 전으로 오인하지 않고 API-24 호출을 차단하며 상태 확인 불가 안내를 반환하는지 검증
    """
    mock_handler.force_status_code = 500

    res = await orchestrator.respond(
        "주문번호 100100003 경기도 성남시 판교역로 166 8층으로 주소 변경해주세요",
        user_key="user_kakao_seo",
        test_case_id="L-03",
    )
    text = res.template.outputs[0].simpleText.text

    # API-24 주소 변경 접수가 호출되지 않아야 함
    api_24 = [h for h in mock_handler.history if "/address-change-requests" in h["path"]]
    assert len(api_24) == 0

    # 배송 상태 확인 불가 안내 포함
    assert "확인할 수 없어" in text or "불가" in text
    assert len(text) <= 500


# ==============================================================================
# 5. Mock 접수 계약 스펙 일치 (동일 대상 재접수 멱등성 및 원본 주소 유지)
# ==============================================================================
@pytest.mark.anyio
async def test_defect_5_mock_idempotency_and_no_immediate_address_overwrite(action_client, mock_handler):
    """
    Mock 접수 POST(API-24, API-32, API-33) 시:
    1. 동일 대상에 대해 재호출 시 기존과 동일한 request_id 반환 (내용 덮어쓰기 멱등성).
    2. API-24 접수 시 mock_handler.orders의 address를 즉시 덮어쓰지 않고 접수 기록만 남김.
    """
    orig_addr = mock_handler.orders["100100003"]["address"]

    # 1차 접수
    res1 = await action_client.change_address(
        order_no="100100003",
        new_address="서울시 강남구 테헤란로 100 2층",
        test_case_id="L-03",
    )
    assert res1["success"] is True
    req_id1 = res1["request_id"]

    # 원본 orders 딕셔너리의 주소가 즉시 변경되지 않았음을 검증
    assert mock_handler.orders["100100003"]["address"] == orig_addr

    # 2차 재접수 (동일 주문)
    res2 = await action_client.change_address(
        order_no="100100003",
        new_address="서울시 강남구 테헤란로 200 5층",
        test_case_id="L-03",
    )
    assert res2["success"] is True
    # 동일한 request_id 반환 확인 (멱등성)
    assert res2["request_id"] == req_id1

    # 현금영수증 멱등성 검증
    cr1 = await action_client.issue_cash_receipt("PAY-3706-0003", "019-2314-9701", test_case_id="L-05")
    cr2 = await action_client.issue_cash_receipt("PAY-3706-0003", "019-2314-9701", test_case_id="L-05")
    assert cr1["request_id"] == cr2["request_id"]

    # 쿠폰 발급 멱등성 검증
    cp1 = await action_client.issue_coupon("MB-77017", "CARE5000", test_case_id="L-47")
    cp2 = await action_client.issue_coupon("MB-77017", "CARE5000", test_case_id="L-47")
    assert cp1["request_id"] == cp2["request_id"]
