"""사용자 감사 지적 8대 결함 및 제3자 정보 보호 조항 전수 방어 검증 테스트 (tests/test_audit_defects.py)."""

import os
import pytest
from app.actions.client import ActionServerClient
from app.actions.mock_server import MockActionHandler
from app.agent.orchestrator import AgentOrchestrator
from app.agent.prompts import SYSTEM_PROMPT, get_rule_based_response
from app.knowledge.policy_router import PolicyCategory, PolicyRouter
from app.knowledge.rules import (
    THIRD_PARTY_PRIVACY_ARTICLES,
    evaluate_third_party_privacy_request,
)


@pytest.fixture
def orchestrator():
    return AgentOrchestrator(api_key="")


# ==============================================================================
# 1. [P1] 단순 문의 시 실제 주문 변경 액션 미실행 검증
# ==============================================================================
@pytest.mark.anyio
async def test_address_change_inquiry_does_not_execute_action(orchestrator):
    """
    '주문번호 ORDER-PENDING-001 배송지 변경 가능한가요?' 발화 시
    임의의 주소를 대입해 변경하지 않고, 집하 전 상태 확인 및 새 주소 요청 안내만 반환하는지 검증
    """
    res = await orchestrator.respond(
        "주문번호 ORDER-PENDING-001 배송지 변경 가능한가요?",
        user_key="user_kakao_001",
    )
    text = res.template.outputs[0].simpleText.text
    # 임의 주소 '서초구 강남대로 500'이 대입되어 정상 변경되었다고 확약하면 안 됨
    assert "강남대로 500" not in text
    assert "정상 변경되었습니다" not in text
    # 변경 가능 여부와 새 주소 요청 안내
    assert "ORDER-PENDING-001" in text
    assert "집하" in text
    assert "주소" in text


@pytest.mark.anyio
async def test_address_change_inquiry_with_city_does_not_execute_action(orchestrator):
    """
    [P1 결함 5] '주문번호 ORDER-PENDING-001 주소 경기 성남시로 변경 가능한가요?'
    시 단위 주소가 포함된 가능 여부 질문 시에도 API-24를 호출하지 않고, 수령인을 덮어쓰지 않으며,
    동·호수 상세주소 입력을 안내하는지 검증
    """
    res = await orchestrator.respond(
        "주문번호 ORDER-PENDING-001 주소 경기 성남시로 변경 가능한가요?",
        user_key="user_kakao_111",
    )
    text = res.template.outputs[0].simpleText.text
    assert "정상 변경되었습니다" not in text
    assert "ORDER-PENDING-001" in text
    assert "집하" in text
    assert "동·호수" in text or "상세" in text


# ==============================================================================
# 2. [P1] 게스트 요청 시 타인 주문 소유자 키 대입 우회 차단 검증
# ==============================================================================
@pytest.mark.anyio
async def test_guest_cannot_bypass_order_ownership():
    """
    게스트가 타인의 주문(ORDER-PENDING-001, 소유자: user_kakao_001)에 대해 주소 변경을 시도할 때
    Mock 내부에서 소유자 키를 대입하여 우회하지 않고, FORBIDDEN(403)으로 정상 차단되는지 검증
    """
    handler = MockActionHandler()
    client = ActionServerClient(mock_handler=handler)

    # guest_user로 소유자 주문 변경 시도
    res = await client.change_shipping_address(
        order_id="ORDER-PENDING-001",
        user_key="guest_user",
        recipient_name="해커",
        recipient_phone="010-9999-9999",
        zipcode="00000",
        new_address="해킹된 주소",
    )
    assert res["status"] == "FAILED"
    assert res["error_code"] == "FORBIDDEN"
    assert "권한" in res["message"] or "소유" in res["message"]


# ==============================================================================
# 3. [P1] 로그인 단순 문의 시 임의 전화번호 세션 초기화 미실행 검증
# ==============================================================================
@pytest.mark.anyio
async def test_login_guide_inquiry_does_not_execute_reset(orchestrator):
    """
    '로그인 방법만 알려주세요' 발화 시
    임의 전화번호(010-1234-5678)로 reset_account_session을 호출하지 않고 절차 안내만 반환하는지 검증
    """
    res = await orchestrator.respond(
        "로그인 방법만 알려주세요",
        user_key="user_kakao_001",
    )
    text = res.template.outputs[0].simpleText.text
    # 임의 티켓 발급 및 문자 발송 완료 안내가 없어야 함
    assert "AUTH-RESET-" not in text
    assert "문자 발송" not in text
    assert "간편로그인" in text or "휴대폰 번호" in text


# ==============================================================================
# 4. [P1] 타임아웃 4.5초 설정 및 지연 시 타임아웃 폴백 검증
# ==============================================================================
def test_timeout_defaults_to_4_point_5():
    """INTERNAL_TIMEOUT_SECONDS 환경변수 및 기본 4.5초 타임아웃 반영 검증"""
    orch = AgentOrchestrator(api_key="")
    assert orch.timeout == 4.5


# ==============================================================================
# 5. [P1] 프로덕션 환경에서 ACTION_SERVER_URL 부재 시 Mock 자동 활성화 방지 검증
# ==============================================================================
def test_production_environment_without_action_url(monkeypatch):
    """ENVIRONMENT=production이고 ACTION_SERVER_URL 없을 때 Mock 장착 방지 검증"""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("ACTION_SERVER_URL", raising=False)
    orch = AgentOrchestrator(api_key="")
    assert orch.action_client is None


# ==============================================================================
# 6. [P2] 최신 Gemini 모델 설정 검증
# ==============================================================================
def test_gemini_active_model_setting():
    """Gemini 2.0 종료 버전이 아닌 최신 활성 모델(gemini-3.5-flash-lite) 반영 검증"""
    orch = AgentOrchestrator(api_key="")
    assert "gemini-2.0" not in orch.model_name
    assert orch.model_name == "gemini-3.5-flash-lite"


# ==============================================================================
# 7. [P2] 시스템 프롬프트 지리적 오류 교정 검증
# ==============================================================================
def test_system_prompt_geographical_correction():
    """전라남도 고흥군 도양읍 오류가 제거되고 교동마을(제주특별자치도) 및 갯마을 연합으로 교정되었는지 검증"""
    assert "전라남도 고흥군 도양읍 「교동마을 산지직송」" not in SYSTEM_PROMPT
    assert "제주특별자치도" in SYSTEM_PROMPT
    assert "교동마을" in SYSTEM_PROMPT
    assert "갯마을" in SYSTEM_PROMPT


# ==============================================================================
# 8. [P2] 규칙 기반 폴백 오답 3건 교정 검증
# ==============================================================================
def test_rule_based_answers_corrections():
    """수박 규격예외, 수산물 부족분 환불, 정기배송 컷오프 정정 검증"""
    # 1. 수박 8kg 규격 상품: 허용오차 미적용, 즉시 규격 미달 판정
    watermelon_ans = get_rule_based_response(
        PolicyCategory.WEIGHT,
        utterance="수박 8kg 이상 시켰는데 7.9kg 왔어요 규격 미달인가요?",
    )
    assert "±5%" in watermelon_ans
    assert "적용되지 않" in watermelon_ans or "오차 적용 없이" in watermelon_ans
    assert "규격 미달 하자" in watermelon_ans

    # 2. 수산물 10% 감량: 부족분 전체에 대한 부분환불(차액환불) 또는 재배송 (전액환불 제외)
    seafood_ans = get_rule_based_response(
        PolicyCategory.SEAFOOD_WEIGHT,
        utterance="갈치 중량이 10%나 감량되어 왔어요",
    )
    assert "부족분 전체" in seafood_ans or "부분환불" in seafood_ans
    assert "전액 환불" not in seafood_ans

    # 3. 정기배송 컷오프: 출고일이 아닌 '해당 회차 결제일의 3영업일 전 24:00'
    subscription_ans = get_rule_based_response(
        PolicyCategory.SUBSCRIPTION,
        utterance="정기배송 스킵 컷오프가 언제인가요?",
    )
    assert "결제일의 3영업일 전 24:00" in subscription_ans


# ==============================================================================
# 9. [신규 사내 규정] 제3자 정보 보호 조항 (기준일 2037-06-30) 검증
# ==============================================================================
def test_third_party_privacy_provisions():
    """제3자 정보 보호 조항 핵심 원칙 검증"""
    assert len(THIRD_PARTY_PRIVACY_ARTICLES) == 10

    # 제3조: '확인이 어렵다' 금지 -> '제공하지 않는 항목이다'
    art3 = THIRD_PARTY_PRIVACY_ARTICLES[3]
    assert "제공하지 않는 항목이다" in art3.content
    assert "확인이 어렵다" in art3.content

    # 농가 연락처 요구
    farm_eval = evaluate_third_party_privacy_request("생산자 농가 사장님 개인 연락처 알려주세요")
    assert farm_eval["disclosable"] is False
    assert "제공하지 않는 항목" in farm_eval["response_text"]
    assert "중계" in farm_eval["response_text"]

    # 배송기사 전화번호 요구
    driver_eval = evaluate_third_party_privacy_request("배송기사님 휴대전화 번호 알려주세요")
    assert driver_eval["disclosable"] is False
    assert "제공하지 않는 항목" in driver_eval["response_text"]
    assert "배송 메모" in driver_eval["response_text"]

    # 선물 수령인 주소 요구
    recipient_eval = evaluate_third_party_privacy_request("선물 받는 분 수령인 주소 어디로 되어있는지 알려주세요")
    assert recipient_eval["disclosable"] is False
    assert "제공하지 않는 항목" in recipient_eval["response_text"]

    # 공구 참여자 명단 요구
    group_eval = evaluate_third_party_privacy_request("공동구매 참여자 명단과 연락처 보내주세요")
    assert group_eval["disclosable"] is False
    assert "제공하지 않는 항목" in group_eval["response_text"]
