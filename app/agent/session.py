"""
교동마을 CS 대화 세션 및 컨텍스트 관리 모듈 (SessionStore & ConversationState).

멀티턴 대화, 진행 중인 업무 플로우(주소 변경, 환불, 현금영수증, 에스컬레이션 등),
주문번호, TC ID, 인입 계정 정보를 세션별로 안전하게 추적 및 관리합니다.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConversationState:
    """개별 사용자 대화 세션 상태 모델."""

    user_id: str
    history: List[Dict[str, str]] = field(default_factory=list)
    current_flow: Optional[str] = None  # "address_change", "refund", "cash_receipt", "escalation", etc.
    order_no: Optional[str] = None
    test_case_id: Optional[str] = None
    incoming_account: Optional[Dict[str, Any]] = None  # {"name": "...", "phone": "...", "member_id": "..."}
    consultation_date: Optional[str] = None
    temp_data: Dict[str, Any] = field(default_factory=dict)
    pending_address: Optional[str] = None
    last_updated: float = field(default_factory=time.time)

    def set_flow(self, flow: str, order_no: Optional[str] = None, **kwargs) -> None:
        """업무 플로우 시작 및 대상 주문번호 설정."""
        self.current_flow = flow
        if order_no:
            self.order_no = order_no
        self.temp_data.update(kwargs)
        self.last_updated = time.time()

    def clear_flow(self) -> None:
        """현재 진행 중인 업무 플로우 및 임시 데이터 초기화."""
        self.current_flow = None
        self.order_no = None
        self.pending_address = None
        self.temp_data.clear()
        self.last_updated = time.time()

    def reset_for_new_tc(self, new_tc_id: Optional[str] = None) -> None:
        """TC 전환 시 이전 세션 상태(주문번호, 플로우, 임시데이터, 주소, 대화이력) 완전 격리 및 초기화."""
        self.clear_flow()
        self.history.clear()
        self.test_case_id = new_tc_id
        self.last_updated = time.time()

    def add_history(self, role: str, content: str) -> None:
        """대화 턴 기록 추가 (최근 10턴 유지)."""
        self.history.append({"role": role, "content": content})
        if len(self.history) > 10:
            self.history = self.history[-10:]
        self.last_updated = time.time()


class SessionStore:
    """인메모리 대화 세션 저장소."""

    def __init__(self, ttl_seconds: float = 3600.0):
        self._sessions: Dict[str, ConversationState] = {}
        self.ttl_seconds = ttl_seconds

    def get(self, user_id: str) -> Optional[ConversationState]:
        """사용자 세션 조회."""
        key = user_id or "anonymous"
        session = self._sessions.get(key)
        if session and (time.time() - session.last_updated > self.ttl_seconds):
            # 세션 만료 시 제거
            del self._sessions[key]
            return None
        return session

    def get_or_create(self, user_id: str) -> ConversationState:
        """사용자 세션 조회 또는 신규 생성."""
        key = user_id or "anonymous"
        session = self.get(key)
        if session is None:
            session = ConversationState(user_id=key)
            self._sessions[key] = session
        return session

    def clear(self, user_id: str) -> None:
        """특정 사용자 세션 삭제."""
        key = user_id or "anonymous"
        if key in self._sessions:
            del self._sessions[key]

    def reset_all(self) -> None:
        """모든 세션 초기화 (테스트용)."""
        self._sessions.clear()
