"""카카오톡 CS 챗봇 하드 가드레일 모듈.

대회 심사 탈락 및 감점 요인을 원천 방어합니다:
1. SimpleText 단일 포맷 강제
2. 말풍선당 500자 초과 방어 (안전 마진 480자 기준 문장 완성 절삭)
3. 마크다운 링크, 이미지, HTML 태그 정제 (순수 텍스트화)
4. 60초 타임아웃 및 시스템 장애 대비 150자 내외 정중한 폴백 응답
"""

from __future__ import annotations

import re
from app.schema import KakaoSkillResponse, SimpleText, SimpleTextOutput, SkillTemplate

# 안전 절삭 기본 임계치 (카카오 500자 제한 대응)
DEFAULT_MAX_CHARS: int = 480

# 폴백 메시지 정의 (150자 내외 정중하고 명확한 안내문)
FALLBACK_MESSAGES: dict[str, str] = {
    "timeout": (
        "고객님, 현재 산지 물류 확인 요청이 급증하여 조회가 다소 지연되고 있습니다. "
        "잠시 후 다시 문의해 주시거나, 긴급한 배송지 변경 및 취소 요청은 "
        "'상담원 연결'을 입력해 주시면 신속히 도와드리겠습니다."
    ),
    "error": (
        "고객님, 일시적인 시스템 확인 오류로 문의 내용을 즉시 처리하지 못했습니다. "
        "이용에 불편을 드려 죄송하며, 잠시 후 다시 시도해 주시거나 "
        "'상담원 연결'을 입력해 주시면 정성껏 안내해 드리겠습니다."
    ),
    "empty": (
        "고객님, 문의 내용을 명확히 확인하지 못했습니다. "
        "상품 문의, 배송 조회, 반품/환불 등 원하시는 내용을 다시 한번 입력해 주시기 바랍니다."
    ),
    "rate_limit": (
        "고객님, 현재 동시 접속 문의가 많아 답변이 지체되었습니다. "
        "잠시 후 다시 입력해 주시거나 '상담원 연결'을 요청해 주시기 바랍니다."
    ),
}


def clean_text(text: str) -> str:
    """LLM 생성 텍스트에서 불필요한 마크다운 및 태그를 정제하여 순수 텍스트로 변환합니다.

    - 마크다운 이미지 `![alt](url)` 제거
    - 마크다운 링크 `[text](url)` -> `text` 변환
    - HTML 태그 `<tag>` 제거
    - 볼드/이탤릭 `**`, `*`, `__`, `_` 마크업 제거
    - 헤더 기호 `#` 제거
    - 코드 블록 기호 ```, ` 제거
    - 연속된 공백 및 3개 이상의 줄바꿈 정돈
    """
    if not text:
        return ""

    # 1. 마크다운 이미지 제거: ![alt](url)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)

    # 2. 마크다운 링크 변환: [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)

    # 3. HTML 태그 제거: <...>
    text = re.sub(r"<[^>]+>", "", text)

    # 4. 코드 블록 기호 제거 (``` 및 `)
    text = re.sub(r"```[a-zA-Z]*\n?", "", text)
    text = text.replace("```", "").replace("`", "")

    # 5. 헤더 마크다운 제거 (# 제목 -> 제목)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

    # 6. 볼드/이탤릭 마크업 제거 (**text**, *text*, __text__, _text_)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"(?<![a-zA-Z0-9])_([^_]+)_(?![a-zA-Z0-9])", r"\1", text)

    # 7. 인용 기호 (> ) 제거
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)

    # 8. 연속 공백(스페이스/탭) 정리 (줄바꿈 보존)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # 9. 3개 이상의 연속 줄바꿈을 2개로 축소
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def safe_truncate(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """텍스트를 max_chars(기본 480자) 이내로 안전하게 절삭합니다.

    - 500자 초과 시 대회 심사 즉시 탈락(0점)되므로 철저히 480자 이하를 보장합니다.
    - 문장 도중에 잘려 어색하지 않도록 마지막 완성된 문장 종결자('.', '?', '!', '\n')를 우선 탐색합니다.
    - 종결자가 너무 앞부분(기본 임계값 이하)에 있는 경우, 단어 경계(공백)에서 자른 후 '...'을 붙입니다.
    - 최종 결과 길이는 반드시 max_chars 이하입니다.
    """
    if not text:
        return ""

    if len(text) <= max_chars:
        return text

    # 후보 슬라이스 (최대 길이 제한)
    candidate = text[:max_chars]

    # 문장 완성 종결 기호 정규식 탐색 (온점, 물음표, 느낌표, 줄바꿈)
    # 너무 앞에서 잘리지 않도록 max_chars의 65% 이상 위치에서 종결 부호 탐색
    min_boundary = int(max_chars * 0.65)

    # 역방향으로 문장 종결 부호 탐색
    sentence_endings = [".", "!", "?", "\n"]
    best_split_idx = -1

    for i in range(len(candidate) - 1, min_boundary - 1, -1):
        if candidate[i] in sentence_endings:
            best_split_idx = i + 1  # 종결 부호 포함
            break

    if best_split_idx != -1:
        truncated = candidate[:best_split_idx].strip()
        if truncated:
            return truncated

    # 적절한 문장 종결 부호가 없는 경우: 공백(단어 경계) 탐색 후 말줄임표 처리
    ellipsis = "..."
    room_for_ellipsis = max_chars - len(ellipsis)

    space_candidate = candidate[:room_for_ellipsis]
    last_space_idx = space_candidate.rfind(" ")

    if last_space_idx >= min_boundary:
        return space_candidate[:last_space_idx].rstrip() + ellipsis

    # 공백조차 적절치 않으면 엄격히 max_chars에 맞추어 말줄임표 붙임
    return space_candidate.rstrip() + ellipsis


def create_simple_text_response(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> KakaoSkillResponse:
    """정제 및 길이 절삭을 거쳐 규격에 부합하는 KakaoSkillResponse 객체를 생성합니다."""
    cleaned = clean_text(text)
    truncated = safe_truncate(cleaned, max_chars=max_chars)

    if not truncated:
        truncated = FALLBACK_MESSAGES["empty"]

    return KakaoSkillResponse(
        version="2.0",
        template=SkillTemplate(
            outputs=[
                SimpleTextOutput(
                    simpleText=SimpleText(text=truncated)
                )
            ],
            quickReplies=None,
        ),
    )


def get_fallback_response(reason: str = "timeout") -> KakaoSkillResponse:
    """타임아웃(60초 방어) 또는 내부 오류 시 반환할 안전한 단일 SimpleText 응답을 생성합니다."""
    fallback_text = FALLBACK_MESSAGES.get(reason, FALLBACK_MESSAGES["error"])
    return create_simple_text_response(fallback_text)
