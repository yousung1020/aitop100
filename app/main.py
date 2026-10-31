"""FastAPI 기반 카카오 i 오픈빌더 스킬 웹훅 서버.

대회 심사 탈락 요인을 원천 차단합니다:
- 오직 SimpleText 단일 포맷 응답 (500자 이하)
- 단 1개의 말풍선으로 원스톱 답변 종결
- 60초 타임아웃 방어 (12초 오케스트레이터 제한)
- 유효성 오류 및 서버 예외 시에도 500 대신 유효한 SimpleText 폴백 반환
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.agent.orchestrator import AgentOrchestrator
from app.guardrails import get_fallback_response
from app.schema import KakaoPayload, KakaoSkillResponse

logger = logging.getLogger(__name__)

# 전역 오케스트레이터 인스턴스 (테스트 시 교체 가능)
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """오케스트레이터 싱글톤 인스턴스를 반환합니다."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


def set_orchestrator(orchestrator: Optional[AgentOrchestrator]) -> None:
    """테스트 또는 모의 주입을 위해 오케스트레이터를 설정합니다."""
    global _orchestrator
    _orchestrator = orchestrator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 앱 생명주기 관리자: 기동 시 오케스트레이터 준비, 종료 시 리소스 정리."""
    orch = get_orchestrator()
    yield
    if orch and orch.action_client:
        await orch.action_client.close()


app = FastAPI(
    title="Gyodong CS Bot",
    description="2037 AI TOP 100 교동마을 산지직송 CS 에이전트",
    version="2.0",
    lifespan=lifespan,
)


# ==========================================
# 예외 핸들러: 대회 즉시 탈락(500, 422 에러) 방어
# ==========================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """카카오 오픈빌더 요청 형식 불일치 시에도 HTTP 200과 유효한 SimpleText 폴백을 반환합니다."""
    logger.warning(f"카카오 요청 유효성 검사 실패: {exc}")
    fallback = get_fallback_response("empty")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=fallback.model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """서버 내부 모든 예외 시 HTTP 500 대신 정상 HTTP 200과 유효한 SimpleText 폴백을 반환합니다."""
    logger.error(f"서버 내부 미처리 예외 발생: {exc}", exc_info=True)
    fallback = get_fallback_response("error")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=fallback.model_dump(),
    )


# ==========================================
# 라우터 엔드포인트
# ==========================================

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트."""
    return {"status": "ok", "version": "2.0"}


@app.post("/skill", response_model=KakaoSkillResponse, response_model_exclude_none=True)
@app.post("/skill/cs", response_model=KakaoSkillResponse, response_model_exclude_none=True)
@app.post("/api/kakao/chat", response_model=KakaoSkillResponse, response_model_exclude_none=True)
async def handle_skill_webhook(request: Request, payload: KakaoPayload) -> KakaoSkillResponse:
    """카카오 i 오픈빌더 스킬 웹훅 엔드포인트.

    발화 및 TC ID, 상담일, 인입 계정 정보를 추출하여 오케스트레이터를 통해 답변을 생성하고,
    SimpleText 단일 포맷으로 응답합니다.
    """
    try:
        utterance = payload.get_utterance()
        user_key = payload.get_user_id()

        headers = request.headers
        client_extra = payload.action.clientExtra if (payload.action and payload.action.clientExtra) else {}
        action_params = payload.action.params if payload.action else {}
        user_params = payload.userRequest.params or {}

        test_case_id = (
            headers.get("x-aitop100-test-case-id")
            or request.query_params.get("test_case_id")
            or client_extra.get("test_case_id")
            or action_params.get("test_case_id")
            or user_params.get("test_case_id")
        )

        consultation_date = (
            headers.get("x-consultation-date")
            or client_extra.get("consultation_date")
            or action_params.get("consultation_date")
        )

        incoming_account = (
            client_extra.get("incoming_account")
            or {
                "user_id": user_key,
                "name": client_extra.get("user_name"),
                "phone": client_extra.get("phone"),
            }
        )

        orch = get_orchestrator()
        return await orch.respond(
            utterance=utterance,
            user_key=user_key,
            test_case_id=test_case_id,
            consultation_date=consultation_date,
            incoming_account=incoming_account,
            extra=client_extra,
        )
    except Exception as exc:
        logger.error(f"웹훅 처리 중 오류 발생: {exc}", exc_info=True)
        return get_fallback_response("error")
