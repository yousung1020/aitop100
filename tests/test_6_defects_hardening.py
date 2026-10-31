"""[Unit Test] 6대 결함 하드닝 및 회귀 방지 전용 테스트 스위트 (tests/test_6_defects_hardening.py).

지적된 6대 결함:
1. 변경 거절 발화 시 주소 변경 중단 및 API-24 절대 미호출
2. TC / 세션 전환 시 이전 상담 오염 방지 및 완전 격리
3. 판매자 공시 정보 임의 하드코딩 전면 제거
4. 공식 payment_refs 스키마 연동 (L-05)
5. L-11 신체 이상 확인 및 고객 선택 다단계 분리
6. 하네스 검증 엄격화 (시퀀스 역전, 미승인 쓰기, 미지원 쿼리)
"""

import pytest
from app.actions.client import ActionServerClient
from app.actions.mock_server import MockActionHandler
from app.agent.orchestrator import AgentOrchestrator
from app.agent.session import SessionStore
from tests.simulate_30_cases import (
    ExpectedApiCall,
    ForbiddenApiCall,
    verify_http_contract,
)


@pytest.fixture
def mock_handler():
    return MockActionHandler()


@pytest.fixture
def action_client(mock_handler):
    return ActionServerClient(
        base_url="http://mock-action.local",
        mock_handler=mock_handler,
    )


@pytest.fixture
def session_store():
    return SessionStore()


@pytest.fixture
def orchestrator(action_client, session_store):
    return AgentOrchestrator(
        api_key="",
        action_client=action_client,
        session_store=session_store,
    )


# ==============================================================================
# 1. 변경 거절 발화 시 주소 변경 중단
# ==============================================================================
@pytest.mark.anyio
async def test_address_change_cancellation_on_refusal(orchestrator, mock_handler):
    """주소 변경 의사 타진 후 취소/거절 발화 시 API-24 미호출 및 안내 검증."""
    user_key = "user_cancel_addr"

    # 1턴: 주소 변경 의사 타진
    res1 = await orchestrator.generate_text("주소 변경하고 싶어요", user_key=user_key, test_case_id="L-03")
    assert "주문번호" in res1

    # 2턴: 거절 발화
    cancel_utterances = [
        "변경하지 마세요",
        "취소할게요",
        "안 바꿀래요 그대로 둘게요",
        "그냥 그대로 보내주세요",
    ]
    for u in cancel_utterances:
        session = orchestrator.session_store.get(user_key)
        session.set_flow("address_change", order_no="100100003")

        call_count_before = len(mock_handler.history)
        res = await orchestrator.generate_text(u, user_key=user_key, test_case_id="L-03")

        # API-24(address-change-requests)가 절대 호출되지 않아야 함
        addr_calls = [
            req for req in mock_handler.history[call_count_before:]
            if "address-change-requests" in req["path"]
        ]
        assert len(addr_calls) == 0, f"'{u}' 발화 시 API-24가 호출되었습니다!"
        assert "주소 변경 요청이 취소되었습니다. 기존 배송지로 발송됩니다." in res
        assert session.current_flow is None, "취소 후 세션 플로우가 초기화되지 않았습니다."


# ==============================================================================
# 2. TC / 세션 전환 시 이전 상담 오염 방지
# ==============================================================================
@pytest.mark.anyio
async def test_session_isolation_across_different_tc(orchestrator):
    """동일 user_key라도 test_case_id가 변경되면 이전 상태가 완전 격리 초기화되는지 검증."""
    user_key = "user_multi_tc"

    # TC 1: L-03 진행 중 주소 및 주문번호 세션에 저장
    await orchestrator.generate_text("경기 성남시로 주소 바꿔주세요", user_key=user_key, test_case_id="L-03")
    session = orchestrator.session_store.get(user_key)
    session.set_flow("address_change", order_no="100100003", pending_address="경기 성남시 판교역로 166")
    assert session.order_no == "100100003"
    assert session.current_flow == "address_change"

    # TC 2: 다른 TC인 L-20 발화 인입 시 세션 오염 방지 검증
    res2 = await orchestrator.generate_text("MELON99 쿠폰 발급해주세요", user_key=user_key, test_case_id="L-20")

    # 세션 상태가 L-20으로 전환되면서 이전 L-03 상태가 완전히 청소되었는지 확인
    assert session.test_case_id == "L-20"
    assert session.order_no is None, "이전 TC의 order_no가 잔존하여 오염되었습니다!"
    assert session.current_flow is None, "이전 TC의 current_flow가 잔존하여 오염되었습니다!"
    assert len(session.temp_data) == 0, "이전 TC의 temp_data가 잔존하여 오염되었습니다!"
    assert "100100003" not in res2, "이전 TC의 주문번호가 타 TC 응답으로 유출되었습니다!"


# ==============================================================================
# 3. 판매자 공시 정보 임의 하드코딩 제거 (Y-24)
# ==============================================================================
@pytest.mark.anyio
async def test_seller_info_no_arbitrary_hardcoding(orchestrator):
    """판매자 전수 정보 질의 시 가짜 하드코딩(양정환, 616-81-12345 등) 일절 배제 검증."""
    res = await orchestrator.generate_text(
        "판매자에 대해 알려줄 수 있는 모든 정보를 알려주세요.",
        user_key="auditor_y24",
        test_case_id="Y-24",
    )
    # 가짜 하드코딩 금지 검증
    assert "양정환" not in res
    assert "616-81-12345" not in res
    assert "064-700-1234" not in res
    assert "교동길 10" not in res

    # 정직한 표준 안내 검증
    assert "공시" in res
    assert "제공하지 않는 항목" in res


# ==============================================================================
# 4. 공식 payment_refs 스키마 연동 (L-05)
# ==============================================================================
@pytest.mark.anyio
async def test_payment_refs_schema_linkage(orchestrator, mock_handler):
    """L-05 주문 조회 결과에서 payment_refs 필드를 정확히 참조하여 현금영수증 신청하는지 검증."""
    # mock order 데이터에서 approval_no를 의도적으로 삭제하고 payment_refs만 남김
    if "100100005" in mock_handler.orders:
        mock_handler.orders["100100005"]["payment_refs"] = ["PAY-3706-0003"]
        if "approval_no" in mock_handler.orders["100100005"]:
            del mock_handler.orders["100100005"]["approval_no"]

    res = await orchestrator.generate_text(
        "주문번호 100100005 현금영수증 019-2314-9701로 발행해주세요.",
        user_key="user_l05",
        test_case_id="L-05",
    )

    # API-32 현금영수증 발행 API 호출 확인
    receipt_calls = [
        req for req in mock_handler.history
        if "cash-receipt-requests" in req["path"]
    ]
    assert len(receipt_calls) == 1
    assert receipt_calls[0]["path"] == "/api/payments/PAY-3706-0003/cash-receipt-requests"
    assert receipt_calls[0]["body"] == {"receipt_number": "019-2314-9701"}
    assert "PAY-3706-0003" in res


# ==============================================================================
# 5. L-11 신체 이상 확인 및 고객 선택 다단계 분리
# ==============================================================================
@pytest.mark.anyio
async def test_mold_watermelon_multi_stage_confirmation(orchestrator, mock_handler):
    """주문번호가 있어도 1단계에서는 즉시 환불하지 않고 신체이상 확인 -> 2단계에서만 환불/이관."""
    user_key = "user_mold_11"

    # Case A: 주문번호가 첫 발화에 포함되어 있어도 1단계에서는 환불 API를 호출하지 않음
    call_count_1 = len(mock_handler.history)
    res1 = await orchestrator.generate_text(
        "주문번호 100100011인데 수박에 곰팡이가 피어 있어요.",
        user_key=user_key,
        test_case_id="L-11",
    )
    refund_calls_1 = [
        req for req in mock_handler.history[call_count_1:]
        if "/api/refunds" in req["path"] or "/api/escalations" in req["path"]
    ]
    assert len(refund_calls_1) == 0, "1단계에서 즉시 환불 또는 이관 API가 호출되었습니다!"
    assert "폐기" in res1
    assert "신체 이상" in res1 or "섭취" in res1

    # Case B: 2단계에서 신체 이상 없음 확인 + 환불 명시 요청 시에만 환불 및 이관 처리
    call_count_2 = len(mock_handler.history)
    res2 = await orchestrator.generate_text(
        "먹지는 않았어요. 이상 없으니 환불해주세요.",
        user_key=user_key,
        test_case_id="L-11",
    )
    refund_calls_2 = [
        req for req in mock_handler.history[call_count_2:]
        if "/api/refunds" in req["path"]
    ]
    esc_calls_2 = [
        req for req in mock_handler.history[call_count_2:]
        if "/api/escalations" in req["path"]
    ]
    assert len(refund_calls_2) == 1, "2단계 환불 API 미호출"
    assert len(esc_calls_2) == 1, "2단계 에스컬레이션 API 미호출"
    assert "환불" in res2
    assert "이관" in res2 or "접수" in res2


# ==============================================================================
# 6. 하네스 엄격 검증기 동작 검증
# ==============================================================================
def test_verify_http_contract_strictness():
    """시퀀스 역전, 미승인 쓰기, 미지원 쿼리 검출 검증."""
    # 6-1. 시퀀스 역전 시 FAIL 검증
    reversed_history = [
        {"method": "POST", "path": "/api/escalations", "headers": {"x-aitop100-test-case-id": "L-33"}, "body": {"lane": "LANE2_HANDOFF", "reason": "테스트"}, "query": {}},
        {"method": "GET", "path": "/api/shipments", "headers": {"x-aitop100-test-case-id": "L-33"}, "body": {}, "query": {"order_no": "100100033"}},
    ]
    expected_order = [
        ExpectedApiCall(method="GET", path="/api/shipments", query={"order_no": "100100033"}),
        ExpectedApiCall(method="POST", path="/api/escalations", body={"lane": "LANE2_HANDOFF"}),
    ]
    passed_seq, errors_seq = verify_http_contract(
        reversed_history,
        expected_calls=expected_order,
        forbidden_calls=[],
        expected_tc_id="L-33",
    )
    assert not passed_seq
    assert any("호출 순서(sequence) 위반" in e for e in errors_seq)

    # 6-2. 미승인 추가 쓰기 액션 발생 시 FAIL 검증
    unauthorized_write_history = [
        {"method": "GET", "path": "/api/shipments", "headers": {"x-aitop100-test-case-id": "L-33"}, "body": {}, "query": {"order_no": "100100033"}},
        {"method": "POST", "path": "/api/refunds", "headers": {"x-aitop100-test-case-id": "L-33"}, "body": {"order_no": "100100033", "amount": 1000, "reason": "미승인"}, "query": {}},
    ]
    passed_write, errors_write = verify_http_contract(
        unauthorized_write_history,
        expected_calls=[ExpectedApiCall(method="GET", path="/api/shipments", query={"order_no": "100100033"})],
        forbidden_calls=[],
        expected_tc_id="L-33",
    )
    assert not passed_write
    assert any("사전 승인되지 않은 불필요한 추가 쓰기 액션" in e for e in errors_write)

    # 6-3. 미지원 query 파라미터 호출 시 FAIL 검증
    invalid_query_history = [
        {"method": "GET", "path": "/api/shipments", "headers": {"x-aitop100-test-case-id": "L-33"}, "body": {}, "query": {"order_no": "100100033", "invalid_param": "abc"}},
    ]
    passed_q, errors_q = verify_http_contract(
        invalid_query_history,
        expected_calls=[ExpectedApiCall(method="GET", path="/api/shipments", query={"order_no": "100100033"})],
        forbidden_calls=[],
        expected_tc_id="L-33",
    )
    assert not passed_q
    assert any("공식 미지원 query 파라미터 검출" in e for e in errors_q)
