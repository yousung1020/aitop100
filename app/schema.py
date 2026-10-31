"""카카오톡 i 오픈빌더 스킬 요청 및 응답 Pydantic 스키마.

대회 심사 기준:
1. 오직 SimpleText 단일 포맷만 허용 (버튼, 이미지, 카드, 리스트, 퀵리플라이 등 불가).
2. 말풍선당 500자 이하 엄격 제한.
3. 단 1개의 출력(outputs)만 허용.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==========================================
# 1. 카카오 오픈빌더 요청 모델 (Incoming Request)
# ==========================================

class KakaoBot(BaseModel):
    """카카오 봇 정보."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="봇 고유 ID")
    name: Optional[str] = Field(None, description="봇 이름")


class KakaoIntent(BaseModel):
    """발화 의도 분석 결과."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="인텐트 ID")
    name: Optional[str] = Field(None, description="인텐트 이름")
    extra: Optional[dict[str, Any]] = Field(default=None, description="추가 메타 정보")


class KakaoAction(BaseModel):
    """스킬 액션 정보."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="액션 ID")
    name: Optional[str] = Field(None, description="액션 이름")
    params: dict[str, Any] = Field(default_factory=dict, description="추출 파라미터")
    detailParams: dict[str, Any] = Field(default_factory=dict, description="상세 파라미터")
    clientExtra: Optional[dict[str, Any]] = Field(default=None, description="클라이언트 추가 정보")


class KakaoBlock(BaseModel):
    """카카오 블록 정보."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="블록 ID")
    name: Optional[str] = Field(None, description="블록 이름")


class KakaoUserProperties(BaseModel):
    """카카오 사용자 추가 속성."""
    model_config = ConfigDict(extra="ignore")

    botUserKey: Optional[str] = Field(None, description="카카오 봇 사용자 고유 키")
    appUserId: Optional[str] = Field(None, description="앱 사용자 식별자")
    plusfriendUserKey: Optional[str] = Field(None, description="플러스친구 사용자 키")


class KakaoUser(BaseModel):
    """카카오 발화자 정보."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="사용자 ID")
    type: Optional[str] = Field(None, description="사용자 식별 타입 (botUserKey 등)")
    properties: KakaoUserProperties = Field(default_factory=KakaoUserProperties, description="사용자 속성")


class KakaoUserRequest(BaseModel):
    """카카오 유저 요청 본문."""
    model_config = ConfigDict(extra="ignore")

    block: Optional[KakaoBlock] = Field(None, description="매핑된 블록")
    user: KakaoUser = Field(..., description="발화 사용자 정보")
    utterance: str = Field(..., description="사용자 입력 발화 텍스트")
    params: dict[str, Any] = Field(default_factory=dict, description="추가 파라미터")
    timezone: Optional[str] = Field("Asia/Seoul", description="타임존")

    def get_utterance(self) -> str:
        """사용자 발화 본문을 공백 정돈 후 반환합니다."""
        return self.utterance.strip()

    def get_user_id(self) -> str:
        """식별 가능한 사용자 고유 키(botUserKey 또는 id)를 반환합니다."""
        if self.user.properties.botUserKey:
            return self.user.properties.botUserKey
        return self.user.id


class KakaoPayload(BaseModel):
    """카카오 오픈빌더 스킬 엔드포인트 전체 요청 페이로드."""
    model_config = ConfigDict(extra="ignore")

    bot: Optional[KakaoBot] = Field(None, description="봇 정보")
    intent: Optional[KakaoIntent] = Field(None, description="인텐트 정보")
    action: Optional[KakaoAction] = Field(None, description="스킬 액션 정보")
    userRequest: KakaoUserRequest = Field(..., description="사용자 요청 정보")
    contexts: Optional[list[Any]] = Field(default=None, description="대화 컨텍스트")

    def get_utterance(self) -> str:
        """발화 텍스트 추출 헬퍼 메서드."""
        return self.userRequest.get_utterance()

    def get_user_id(self) -> str:
        """사용자 식별자 추출 헬퍼 메서드."""
        return self.userRequest.get_user_id()


# ==========================================
# 2. 카카오 오픈빌더 응답 모델 (Strict SimpleText Only)
# ==========================================

class SimpleText(BaseModel):
    """단일 텍스트 말풍선 본문.

    심사 규정에 따라 최대 500자 이하를 엄격히 강제합니다.
    """
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., max_length=500, description="응답 본문 (500자 이하 필수)")

    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("응답 텍스트는 빈 문자열일 수 없습니다.")
        if len(v) > 500:
            raise ValueError(f"응답 텍스트는 500자를 초과할 수 없습니다. (현재: {len(v)}자)")
        return v


class SimpleTextOutput(BaseModel):
    """단일 SimpleText 출력 래퍼."""
    model_config = ConfigDict(extra="forbid")

    simpleText: SimpleText = Field(..., description="단일 텍스트 컴포넌트")


class SkillTemplate(BaseModel):
    """스킬 템플릿 모델.

    심사 규정상:
    - 오직 SimpleTextOutput 1개만 허용 (outputs 길이 1 고정)
    - quickReplies 등 버튼/카드 포맷 일체 불허 (None 강제)
    """
    model_config = ConfigDict(extra="forbid")

    outputs: list[SimpleTextOutput] = Field(
        ...,
        min_length=1,
        max_length=1,
        description="오직 1개의 SimpleText 말풍선만 허용",
    )
    quickReplies: None = Field(default=None, description="버튼 및 퀵리플라이 생성 절대 불가")

    @field_validator("outputs")
    @classmethod
    def validate_outputs(cls, v: list[SimpleTextOutput]) -> list[SimpleTextOutput]:
        if len(v) != 1:
            raise ValueError(f"단일 말풍선 원칙에 따라 outputs는 정확히 1개여야 합니다. (현재: {len(v)}개)")
        return v


class KakaoSkillResponse(BaseModel):
    """카카오 오픈빌더 스킬 표준 응답 모델 (SimpleText 단일 포맷 강제)."""
    model_config = ConfigDict(extra="forbid")

    version: str = Field(default="2.0", description="스킬 API 버전")
    template: SkillTemplate = Field(..., description="스킬 출력 템플릿")
    data: Optional[dict[str, Any]] = Field(default=None, description="추가 커스텀 데이터")
    context: Optional[dict[str, Any]] = Field(default=None, description="블록 컨텍스트")
