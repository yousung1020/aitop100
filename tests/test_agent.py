"""AgentOrchestrator 및 시스템 프롬프트 단위 테스트 (tests/test_agent.py)."""

import pytest
import anyio

from app.agent.orchestrator import AgentOrchestrator, MockAgentOrchestrator
from app.agent.prompts import SYSTEM_PROMPT, build_user_prompt
from app.guardrails import FALLBACK_MESSAGES
from app.schema import KakaoSkillResponse


@pytest.fixture
def orchestrator():
    return AgentOrchestrator(api_key="")


# ==========================================
# 1. 오케스트레이터 초기화 및 프롬프트 검증
# ==========================================

def test_orchestrator_init():
    """기본 인자 초기화 시 올바른 기본값과 MockActionHandler 장착 검증"""
    orch = AgentOrchestrator(api_key="")
    assert orch.gemini_client is None  # 키 미제공 시 Fallback 모드
    assert orch.model_name in (
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash-latest",
    )
    assert orch.timeout in (4.5, 12.0)
    assert orch.action_client is not None


def test_orchestrator_production_without_action_url(monkeypatch):
    """프로덕션 환경에서 ACTION_SERVER_URL 부재 시 Mock 자동 활성화 방지 검증"""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("ACTION_SERVER_URL", raising=False)
    orch = AgentOrchestrator(api_key="")
    assert orch.action_client is None


def test_system_prompt_guardrails():
    """시스템 프롬프트 내 핵심 규칙 및 심사 가드레일 키워드 포함 검증"""
    assert "2037년" in SYSTEM_PROMPT
    assert "교동마을" in SYSTEM_PROMPT
    assert "갯마을" in SYSTEM_PROMPT
    assert "합포장" in SYSTEM_PROMPT
    assert "집하 스캔 전" in SYSTEM_PROMPT
    assert "5만원" in SYSTEM_PROMPT
    assert "이민준" in SYSTEM_PROMPT
    assert "고길동" in SYSTEM_PROMPT
    assert "선약속" in SYSTEM_PROMPT
    assert "8%" in SYSTEM_PROMPT
    assert "AI 조작" in SYSTEM_PROMPT
    assert "450자" in SYSTEM_PROMPT


def test_build_user_prompt():
    """사용자 프롬프트 생성 시 규정, 액션 결과, 고객 발화 바인딩 검증"""
    prompt = build_user_prompt(
        utterance="배송비가 얼마인가요?",
        knowledge_text="교동 4천원, 5만원 이상 무료",
        action_context="조회 결과 정상",
    )
    assert "배송비가 얼마인가요?" in prompt
    assert "교동 4천원, 5만원 이상 무료" in prompt
    assert "조회 결과 정상" in prompt
    assert "450자 이내" in prompt


# ==========================================
# 2. 비즈니스 정책 및 전산 액션 연동 시나리오 검증
# ==========================================

@pytest.mark.anyio
async def test_combined_shipping_inquiry(orchestrator):
    """농수산물 합포장 불가 질의 시 독립 포장/발송 및 송장 분리 안내 검증"""
    res = await orchestrator.respond("감귤이랑 갈치 같이 포장해서 한 박스로 보내주세요")
    assert isinstance(res, KakaoSkillResponse)
    text = res.template.outputs[0].simpleText.text

    assert len(text) <= 500
    assert "합포장" in text or "합배송" in text
    assert "불가" in text
    assert "독립" in text or "개별" in text
    assert "구방만" in text or "송장" in text


@pytest.mark.anyio
async def test_address_change_pending_order(orchestrator):
    """집하 전 주문(ORDER-PENDING-001)에 대한 배송지 변경 성공 검증"""
    res = await orchestrator.respond(
        "주문번호 ORDER-PENDING-001 주소 서울시 강남구 테헤란로 200으로 변경해주세요",
        user_key="user_kakao_111",
    )
    text = res.template.outputs[0].simpleText.text

    assert len(text) <= 500
    assert "ORDER-PENDING-001" in text
    assert "정상 변경" in text or "성공" in text
    assert "서울시 강남구 테헤란로 200" in text


@pytest.mark.anyio
async def test_address_change_shipped_order(orchestrator):
    """집하 완료 주문(ORDER-SHIPPED-001)에 대한 배송지 변경 불가 및 반품 절차 안내 검증"""
    res = await orchestrator.respond(
        "주문번호 ORDER-SHIPPED-001 주소 부산시 해운대구로 변경해줘",
        user_key="user_kakao_222",
    )
    text = res.template.outputs[0].simpleText.text

    assert len(text) <= 500
    assert "집하" in text or "출고" in text
    assert "불가" in text
    assert "반품" in text


@pytest.mark.anyio
async def test_address_change_without_order_id(orchestrator):
    """주문번호 없는 단순 주소 변경 질의 시 집하 전 가능 기준 및 주문번호 요청 안내 검증"""
    res = await orchestrator.respond("배송지 주소 변경하고 싶어요")
    text = res.template.outputs[0].simpleText.text

    assert len(text) <= 500
    assert "집하 스캔 전" in text
    assert "주문번호" in text


@pytest.mark.anyio
async def test_auth_reset_session(orchestrator):
    """로그인 장애 및 계정 잠김 질의 시 전산 복구 티켓 발급 및 문자 발송 안내 검증"""
    res = await orchestrator.respond(
        "로그인이 안 돼요 계정 잠김 해제해주세요 010-1234-5678",
        user_key="user_kakao_001",
    )
    text = res.template.outputs[0].simpleText.text

    assert len(text) <= 500
    assert "AUTH-20370630-" in text
    assert "임시 복구 링크" in text or "인증 코드" in text
    assert "010-1234-5678" in text


@pytest.mark.anyio
async def test_escalate_to_human_agent(orchestrator):
    """상담원 연결 요청 시 긴급 이관 티켓 발급 및 이민준 총괄 안내 검증"""
    res = await orchestrator.respond("상담원 연결해주세요")
    text = res.template.outputs[0].simpleText.text

    assert len(text) <= 500
    assert "TICKET-20370630-" in text
    assert "이민준" in text
    assert "09:00~18:00" in text


@pytest.mark.anyio
async def test_escalate_high_claim_amount(orchestrator):
    """5만원 초과 피해 보상 요청 시 고액 이관 및 심사 안내 검증"""
    res = await orchestrator.respond("상담원 연결해주세요 피해액이 10만원입니다")
    text = res.template.outputs[0].simpleText.text

    assert len(text) <= 500
    assert "TICKET-20370630-" in text
    assert "이관" in text


@pytest.mark.anyio
async def test_seafood_weight_natural_loss(orchestrator):
    """수산물 감량 질의 시 8% 판정선(3% 자연감량 + 5% 표기오차) 및 고객선택권 안내 검증"""
    res = await orchestrator.respond("갈치 중량이 10%나 빠져서 왔어요")
    text = res.template.outputs[0].simpleText.text

    assert len(text) <= 500
    assert "8%" in text
    assert "자연감량 3%" in text or "자연감량" in text
    assert "환불" in text or "재배송" in text


@pytest.mark.anyio
async def test_no_authenticity_check(orchestrator):
    """증빙 진위 감정 질의 시 의심 발언 금지 및 대조 절차 안내 검증"""
    res = await orchestrator.respond("사진 보냈는데 AI로 조작했다고 의심하시는 거 아니죠?")
    text = res.template.outputs[0].simpleText.text

    assert len(text) <= 500
    assert "의심하거나 감정하지 않습니다" in text
    assert "기록과 대조" in text or "절차" in text
    # 진위 감정 금지어 검증
    for forbidden in ("AI 조작", "색칠", "합성"):
        assert f"고객님께서 {forbidden}" not in text


@pytest.mark.anyio
async def test_future_promise_forbidden(orchestrator):
    """미래 덤/쿠폰 약속 요구 시 선약속 금지 및 규정 쿠폰 즉시 보상 안내 검증"""
    res = await orchestrator.respond("배송이 늦었는데 다음 주문 때 덤 더 챙겨주세요")
    text = res.template.outputs[0].simpleText.text

    assert len(text) <= 500
    assert "선약속" in text or "미리 약속" in text
    assert "금지" in text
    assert "CARE3000" in text or "쿠폰" in text


@pytest.mark.anyio
async def test_unhandled_item_carrot(orchestrator):
    """미취급 품목(당근) 질의 시 친절한 미취급 안내 검증"""
    res = await orchestrator.respond("교동마을 당근도 파나요?")
    text = res.template.outputs[0].simpleText.text

    assert len(text) <= 500
    assert "당근" in text
    assert "취급하지 않는" in text or "재배하거나 취급하지 않는" in text


@pytest.mark.anyio
async def test_discretion_hierarchy(orchestrator):
    """보상 승인 서열(1단 봇 5만원 -> 2단 이민준 -> 3단 고길동) 안내 검증"""
    res = await orchestrator.respond("승인 절차와 권한 위임 서열이 어떻게 되나요?")
    text = res.template.outputs[0].simpleText.text

    assert len(text) <= 500
    assert "5만원" in text
    assert "이민준" in text
    assert "고길동" in text


# ==========================================
# 3. 타임아웃, 예외 및 폴백 가드레일 검증
# ==========================================

@pytest.mark.anyio
async def test_empty_utterance_fallback(orchestrator):
    """빈 발화 입력 시 정중한 재입력 안내 폴백 반환 검증"""
    res1 = await orchestrator.respond("")
    assert res1.template.outputs[0].simpleText.text == FALLBACK_MESSAGES["empty"]

    res2 = await orchestrator.respond("   \n\t  ")
    assert res2.template.outputs[0].simpleText.text == FALLBACK_MESSAGES["empty"]


@pytest.mark.anyio
async def test_orchestrator_timeout_fallback():
    """지연 발생 시 12초(테스트에서는 짧은 타임아웃) 초과 시 안전한 timeout 폴백 반환 검증"""
    mock_orch = MockAgentOrchestrator(delay=0.3, timeout=0.05)
    res = await mock_orch.respond("감귤 합포장 되나요?")

    assert isinstance(res, KakaoSkillResponse)
    assert res.template.outputs[0].simpleText.text == FALLBACK_MESSAGES["timeout"]
    assert len(res.template.outputs[0].simpleText.text) <= 500


@pytest.mark.anyio
async def test_orchestrator_error_fallback():
    """내부 예외 발생 시 크래시 없이 안전한 error 폴백 반환 검증"""
    mock_orch = MockAgentOrchestrator(force_error=True)
    res = await mock_orch.respond("감귤 합포장 되나요?")

    assert isinstance(res, KakaoSkillResponse)
    assert res.template.outputs[0].simpleText.text == FALLBACK_MESSAGES["error"]
    assert len(res.template.outputs[0].simpleText.text) <= 500


@pytest.mark.anyio
async def test_markdown_and_html_cleaning():
    """출력 내 마크다운 및 HTML 태그가 완전히 정제되는지 검증"""
    raw_markdown = "오늘의 **특가 상품** [클릭](https://gyodong.com) <font color='red'>신선합니다</font>!"
    mock_orch = MockAgentOrchestrator(mock_response=raw_markdown)
    res = await mock_orch.respond("특가 알려줘")
    text = res.template.outputs[0].simpleText.text

    assert "**" not in text
    assert "[" not in text
    assert "https://" not in text
    assert "<" not in text
    assert "오늘의 특가 상품 클릭 신선합니다!" in text
