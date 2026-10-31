"""FastAPI 카카오 i 오픈빌더 웹훅 엔드포인트 E2E 테스트 (tests/test_main.py)."""

import pytest
import httpx

from app.agent.orchestrator import AgentOrchestrator, MockAgentOrchestrator
from app.guardrails import FALLBACK_MESSAGES
from app.main import app, set_orchestrator
from app.schema import KakaoSkillResponse


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def reset_orchestrator():
    """각 테스트마다 전역 오케스트레이터를 기본값으로 리셋 (단위 테스트 격리를 위해 api_key 비활성화)"""
    set_orchestrator(AgentOrchestrator(api_key=""))
    yield
    set_orchestrator(None)


@pytest.fixture
async def async_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def make_kakao_payload(utterance: str, user_key: str = "test_user_key") -> dict:
    """테스트용 카카오 오픈빌더 페이로드 생성 헬퍼"""
    return {
        "bot": {"id": "test_bot_id", "name": "교동마을 챗봇"},
        "intent": {"id": "intent_001", "name": "CS질의"},
        "action": {"id": "action_001", "name": "질의응답", "params": {}},
        "userRequest": {
            "block": {"id": "block_001", "name": "기본블록"},
            "user": {
                "id": user_key,
                "type": "botUserKey",
                "properties": {
                    "botUserKey": user_key,
                    "appUserId": "app_user_001",
                },
            },
            "utterance": utterance,
            "params": {"surface": "KakaoTalk"},
            "timezone": "Asia/Seoul",
        },
    }


# ==========================================
# 1. 헬스체크 엔드포인트 테스트
# ==========================================

@pytest.mark.anyio
async def test_health_check(async_client):
    """GET /health 정상 작동 확인"""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "2.0"


# ==========================================
# 2. POST /skill 및 POST /skill/cs E2E 테스트
# ==========================================

@pytest.mark.anyio
async def test_skill_combined_shipping(async_client):
    """POST /skill: 농수산물 합포장 불가 질의 처리 및 단일 SimpleText 검증"""
    payload = make_kakao_payload("감귤이랑 은갈치 같이 한 상자에 포장해줄 수 있나요?")
    response = await async_client.post("/skill", json=payload)

    assert response.status_code == 200
    data = response.json()
    parsed = KakaoSkillResponse.model_validate(data)

    assert parsed.version == "2.0"
    assert len(parsed.template.outputs) == 1
    assert parsed.template.quickReplies is None

    text = parsed.template.outputs[0].simpleText.text
    assert len(text) <= 500
    assert "합포장" in text or "합배송" in text
    assert "불가" in text


@pytest.mark.anyio
async def test_skill_cs_alias_endpoint(async_client):
    """POST /skill/cs: 별칭 엔드포인트 정상 작동 검증"""
    payload = make_kakao_payload("감귤이랑 갈치 같이 포장해줘")
    response = await async_client.post("/skill/cs", json=payload)

    assert response.status_code == 200
    parsed = KakaoSkillResponse.model_validate(response.json())
    assert len(parsed.template.outputs) == 1
    assert parsed.template.quickReplies is None


@pytest.mark.anyio
async def test_skill_address_change_pending(async_client):
    """POST /skill: 집하 전 주문 배송지 변경 E2E 검증"""
    payload = make_kakao_payload(
        "주문번호 ORDER-PENDING-001 주소 서울시 강남구 테헤란로 200으로 변경해주세요",
        user_key="user_kakao_111",
    )
    response = await async_client.post("/skill", json=payload)
    assert response.status_code == 200

    parsed = KakaoSkillResponse.model_validate(response.json())
    text = parsed.template.outputs[0].simpleText.text
    assert "ORDER-PENDING-001" in text
    assert "정상 변경" in text or "성공" in text
    assert len(text) <= 500


@pytest.mark.anyio
async def test_skill_address_change_shipped(async_client):
    """POST /skill: 집하 완료 주문 배송지 변경 불가 및 반품 안내 검증"""
    payload = make_kakao_payload(
        "주문번호 ORDER-SHIPPED-001 주소 부산으로 변경해줘",
        user_key="user_kakao_222",
    )
    response = await async_client.post("/skill", json=payload)
    assert response.status_code == 200

    parsed = KakaoSkillResponse.model_validate(response.json())
    text = parsed.template.outputs[0].simpleText.text
    assert "집하" in text or "출고" in text
    assert "불가" in text
    assert "반품" in text
    assert len(text) <= 500


@pytest.mark.anyio
async def test_skill_auth_reset(async_client):
    """POST /skill: 로그인 잠김 세션 복구 전산 연동 E2E 검증"""
    payload = make_kakao_payload(
        "로그인이 안 돼요 계정 잠김 해제해주세요 010-1234-5678",
        user_key="user_kakao_001",
    )
    response = await async_client.post("/skill", json=payload)
    assert response.status_code == 200

    parsed = KakaoSkillResponse.model_validate(response.json())
    text = parsed.template.outputs[0].simpleText.text
    assert "AUTH-20370630-" in text
    assert "임시 복구 링크" in text or "인증 코드" in text
    assert len(text) <= 500


@pytest.mark.anyio
async def test_skill_escalate(async_client):
    """POST /skill: 상담원 이관 E2E 검증"""
    payload = make_kakao_payload("상담원 연결해주세요")
    response = await async_client.post("/skill", json=payload)
    assert response.status_code == 200

    parsed = KakaoSkillResponse.model_validate(response.json())
    text = parsed.template.outputs[0].simpleText.text
    assert "TICKET-20370630-" in text
    assert "이민준" in text
    assert len(text) <= 500


@pytest.mark.anyio
async def test_skill_seafood_loss(async_client):
    """POST /skill: 수산물 감량 8% 허용선 및 보상 선택권 검증"""
    payload = make_kakao_payload("갈치 무게가 줄었어요 10%나 부족해요")
    response = await async_client.post("/skill", json=payload)
    assert response.status_code == 200

    parsed = KakaoSkillResponse.model_validate(response.json())
    text = parsed.template.outputs[0].simpleText.text
    assert "8%" in text
    assert len(text) <= 500


# ==========================================
# 3. 비정상 페이로드 및 장애 방어 검증 (HTTP 500/422 차단)
# ==========================================

@pytest.mark.anyio
async def test_malformed_json_fallback(async_client):
    """형식이 잘못된 JSON 요청에도 HTTP 200과 안전한 폴백을 반환하여 500/422 실격 방지"""
    response = await async_client.post(
        "/skill",
        content="not a json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    data = response.json()
    parsed = KakaoSkillResponse.model_validate(data)
    assert len(parsed.template.outputs) == 1
    assert parsed.template.quickReplies is None
    assert len(parsed.template.outputs[0].simpleText.text) <= 500


@pytest.mark.anyio
async def test_missing_fields_fallback(async_client):
    """필수 필드가 누락된 요청(예: userRequest 없음)에도 HTTP 200과 안전한 폴백 반환"""
    bad_payload = {"bot": {"id": "bot_id"}}
    response = await async_client.post("/skill", json=bad_payload)

    assert response.status_code == 200
    data = response.json()
    parsed = KakaoSkillResponse.model_validate(data)
    assert parsed.template.outputs[0].simpleText.text == FALLBACK_MESSAGES["empty"]


@pytest.mark.anyio
async def test_timeout_fallback_in_endpoint(async_client):
    """오케스트레이터 처리 지연 시 HTTP 200 및 timeout 폴백 반환 검증"""
    slow_orch = MockAgentOrchestrator(delay=0.3, timeout=0.05)
    set_orchestrator(slow_orch)

    payload = make_kakao_payload("느린 요청 테스트")
    response = await async_client.post("/skill", json=payload)

    assert response.status_code == 200
    parsed = KakaoSkillResponse.model_validate(response.json())
    assert parsed.template.outputs[0].simpleText.text == FALLBACK_MESSAGES["timeout"]


@pytest.mark.anyio
async def test_server_error_fallback_in_endpoint(async_client):
    """오케스트레이터 내부 예외 발생 시 HTTP 200 및 error 폴백 반환 검증"""
    error_orch = MockAgentOrchestrator(force_error=True)
    set_orchestrator(error_orch)

    payload = make_kakao_payload("예외 발생 테스트")
    response = await async_client.post("/skill", json=payload)

    assert response.status_code == 200
    parsed = KakaoSkillResponse.model_validate(response.json())
    assert parsed.template.outputs[0].simpleText.text == FALLBACK_MESSAGES["error"]
