"""카카오 스킬 스키마 및 가드레일 모듈 단위 테스트."""

import pytest
from pydantic import ValidationError

from app.guardrails import (
    DEFAULT_MAX_CHARS,
    clean_text,
    create_simple_text_response,
    get_fallback_response,
    safe_truncate,
)
from app.schema import (
    KakaoPayload,
    KakaoSkillResponse,
    SimpleText,
    SimpleTextOutput,
    SkillTemplate,
)


def test_clean_text_markdown_links():
    """마크다운 링크가 본문 텍스트로 안전하게 변환되는지 검증."""
    raw = "자세한 사항은 [교동마을 공지사항](https://gyodong.com/notice) 및 [고객센터](https://help.gyodong.com)를 참조하세요."
    cleaned = clean_text(raw)
    assert "[교동마을 공지사항]" not in cleaned
    assert "https://gyodong.com/notice" not in cleaned
    assert "자세한 사항은 교동마을 공지사항 및 고객센터를 참조하세요." == cleaned


def test_clean_text_markdown_images():
    """마크다운 이미지가 완전히 제거되는지 검증."""
    raw = "오늘 수확한 감귤입니다. ![감귤 실물](https://img.gyodong.com/citrus.png) 싱싱합니다!"
    cleaned = clean_text(raw)
    assert "![감귤 실물]" not in cleaned
    assert "https://img.gyodong.com/citrus.png" not in cleaned
    assert "오늘 수확한 감귤입니다. 싱싱합니다!" == cleaned


def test_clean_text_html_tags():
    """HTML 태그가 제거되는지 검증."""
    raw = "<p>교동마을 <b>산지직송</b> 안내입니다.<br/>환불 불가합니다.</p>"
    cleaned = clean_text(raw)
    assert "<p>" not in cleaned
    assert "<b>" not in cleaned
    assert "<br/>" not in cleaned
    assert "</p>" not in cleaned
    assert "교동마을 산지직송 안내입니다.환불 불가합니다." == cleaned


def test_clean_text_markdown_styling():
    """헤더, 볼드, 이탤릭, 코드 블록이 깨끗이 정제되는지 검증."""
    raw = """### 배송 안내
**교동마을**과 *갯마을*은 합포장이 _불가_합니다.
```python
is_valid = True
```
참고 바랍니다."""
    cleaned = clean_text(raw)
    assert "###" not in cleaned
    assert "**" not in cleaned
    assert "*갯마을*" not in cleaned
    assert "_불가_" not in cleaned
    assert "```" not in cleaned
    assert "교동마을과 갯마을은 합포장이 불가합니다." in cleaned
    assert "is_valid = True" in cleaned


def test_safe_truncate_under_limit():
    """임계치 이내의 텍스트는 원본 그대로 보존되는지 검증."""
    short_text = "안녕하세요! 교동마을 산지직송 고객센터입니다."
    assert safe_truncate(short_text, max_chars=480) == short_text


def test_safe_truncate_over_limit_sentence_boundary():
    """500자 초과 긴 텍스트 입력 시 자연스러운 문장 종결 부호에서 480자 이하로 절삭되는지 검증."""
    long_sentences = (
        "교동마을 감귤은 당일 새벽 수확하여 산지에서 직송됩니다. "
        "따라서 신선도가 극히 뛰어나며 중간 유통 마진이 없습니다. "
        "농산물 특성상 단순 변심에 의한 반품이나 교환은 불가합니다. "
        "다만 배송 중 과실 파손이나 부패가 발생한 경우 사진을 첨부해 주시면 신속히 보상해 드립니다. "
        "갯마을 수산물과는 발송지가 상이하여 합포장이 불가하며 개별 택배사로 발송됩니다. "
        "배송지 변경을 원하시는 경우 출고 전 오전 9시까지 고객센터 또는 챗봇을 통해 요청하셔야 합니다. "
        "이미 송장이 출력되어 배송 중인 상태에서는 배송지 변경이나 주문 취소가 절대 불가함을 양해 바랍니다. "
        "항상 정직한 먹거리를 제공하는 교동마을이 되겠습니다. 감사드립니다."
    ) * 3  # 1000자 이상

    assert len(long_sentences) > 800

    truncated = safe_truncate(long_sentences, max_chars=480)

    # 480자 이하 검증
    assert len(truncated) <= 480
    # 문장 종결자('.', '?', '!', '\n')로 끝나는지 확인
    assert truncated[-1] in [".", "!", "?", "…", "..."] or truncated.endswith("...")
    # 내용이 잘 보존되었는지
    assert "교동마을 감귤은 당일 새벽 수확하여" in truncated


def test_safe_truncate_no_punctuation():
    """종결 부호가 없는 1000자 연속 문자열도 엄격히 480자 이하로 절삭되는지 검증."""
    continuous_text = "가나다라마바사아자차카타파하" * 100  # 1400자
    truncated = safe_truncate(continuous_text, max_chars=480)

    assert len(truncated) <= 480
    assert truncated.endswith("...")


def test_safe_truncate_boundary_exact():
    """경계값 검증 (정확히 480자인 텍스트, 481자인 텍스트)."""
    # 정확히 480자인 문자열
    exact_480 = "가" * 479 + "."
    assert len(exact_480) == 480
    assert safe_truncate(exact_480, max_chars=480) == exact_480

    # 481자인 문자열 (끝이 점)
    exact_481 = "가" * 480 + "."
    res = safe_truncate(exact_481, max_chars=480)
    assert len(res) <= 480


def test_create_simple_text_response_structure():
    """대회 규정상 SimpleText 단일 포맷 규격에 완벽히 부합하는지 검증."""
    sample_text = (
        "안녕하세요! 교동마을 산지직송입니다.\n\n"
        "문의하신 감귤과 은갈치는 산지가 달라 [합포장](https://guide.com)이 불가합니다.\n"
        "각각 개별 발송되오니 양해 부탁드립니다!"
    )

    response = create_simple_text_response(sample_text)

    # 1. 최상위 응답 구조
    assert isinstance(response, KakaoSkillResponse)
    assert response.version == "2.0"
    assert response.template is not None

    # 2. outputs 단 1개 규격 검증
    assert len(response.template.outputs) == 1
    output = response.template.outputs[0]
    assert isinstance(output, SimpleTextOutput)
    assert output.simpleText is not None

    # 3. 마크다운 링크 정제 여부
    assert "https://guide.com" not in output.simpleText.text
    assert "합포장" in output.simpleText.text

    # 4. quickReplies 절대 불가(None) 검증
    assert response.template.quickReplies is None

    # 5. 글자 수 480자 이하 보장
    assert len(output.simpleText.text) <= DEFAULT_MAX_CHARS


def test_create_simple_text_response_empty_handling():
    """빈 문자열이나 공백만 입력되었을 때 폴백 텍스트로 안전하게 응답하는지 검증."""
    empty_resp = create_simple_text_response("   \n\t  ")
    assert isinstance(empty_resp, KakaoSkillResponse)
    assert len(empty_resp.template.outputs[0].simpleText.text) > 0
    assert "문의 내용" in empty_resp.template.outputs[0].simpleText.text


def test_get_fallback_response():
    """60초 타임아웃 및 장애 대비 폴백 응답 검증."""
    timeout_resp = get_fallback_response("timeout")
    assert isinstance(timeout_resp, KakaoSkillResponse)
    text = timeout_resp.template.outputs[0].simpleText.text
    assert len(text) <= 480
    assert "지연" in text or "상담원 연결" in text

    error_resp = get_fallback_response("error")
    err_text = error_resp.template.outputs[0].simpleText.text
    assert len(err_text) <= 480
    assert "오류" in err_text or "상담원 연결" in err_text


def test_pydantic_schema_strictness():
    """심사 위반 포맷 방어: 500자 초과 텍스트 또는 2개 이상의 말풍선 삽입 시 ValidationError 발생."""
    # 500자 초과 텍스트 검증
    with pytest.raises(ValidationError):
        SimpleText(text="가" * 501)

    # outputs 빈 배열 검증
    with pytest.raises(ValidationError):
        SkillTemplate(outputs=[])

    # outputs 2개 이상 검증
    with pytest.raises(ValidationError):
        SkillTemplate(
            outputs=[
                SimpleTextOutput(simpleText=SimpleText(text="첫 번째")),
                SimpleTextOutput(simpleText=SimpleText(text="두 번째")),
            ]
        )


def test_kakao_payload_parsing():
    """카카오 오픈빌더 요청 JSON 페이로드가 정상 파싱되고 헬퍼 메서드가 동작하는지 검증."""
    raw_payload = {
        "bot": {"id": "gyodong_bot_id_2037", "name": "교동마을 산지직송 CS봇"},
        "intent": {"id": "intent_001", "name": "합포장문의"},
        "action": {
            "id": "action_skill_call",
            "name": "CS질의응답",
            "params": {"category": "delivery"},
            "detailParams": {},
        },
        "userRequest": {
            "block": {"id": "block_001", "name": "문의블록"},
            "user": {
                "id": "kakao_user_raw_id",
                "type": "botUserKey",
                "properties": {
                    "botUserKey": "kakao_user_unique_hash_98234",
                    "appUserId": "app_user_4821",
                },
            },
            "utterance": "  감귤이랑 갈치를 같이 샀는데 왜 택배가 따로 오나요?  ",
            "params": {"surface": "KakaoTalk"},
            "timezone": "Asia/Seoul",
        },
    }

    payload = KakaoPayload.model_validate(raw_payload)

    # 헬퍼 메서드 검증
    assert payload.get_utterance() == "감귤이랑 갈치를 같이 샀는데 왜 택배가 따로 오나요?"
    assert payload.get_user_id() == "kakao_user_unique_hash_98234"
    assert payload.bot.name == "교동마을 산지직송 CS봇"


def test_json_serialization_kakao_format():
    """응답 모델의 직렬화 결과가 카카오 오픈빌더 규격에 완벽히 일치하는지 검증."""
    res = create_simple_text_response("안녕하세요, 교동마을입니다.")
    data = res.model_dump(exclude_none=True)

    assert data == {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": "안녕하세요, 교동마을입니다.",
                    }
                }
            ],
        },
    }


def test_clean_text_consecutive_newlines_and_spaces():
    """과도한 연속 공백과 줄바꿈 정돈 검증."""
    raw = "안녕하세요!     \n\n\n\n\n교동마을입니다.   \t   반갑습니다."
    cleaned = clean_text(raw)
    assert cleaned == "안녕하세요!\n\n교동마을입니다. 반갑습니다."


def test_clean_text_with_emojis():
    """이모지와 한글/영문/숫자가 안전하게 보존되는지 검증."""
    raw = "🍊 제주 감귤 5kg 특가 세일! [링크](https://sale.com) 🎉"
    cleaned = clean_text(raw)
    assert cleaned == "🍊 제주 감귤 5kg 특가 세일! 링크 🎉"


def test_kakao_payload_fallback_user_id():
    """botUserKey가 없는 경우 user.id로 안전하게 사용자 식별자가 추출되는지 검증."""
    raw_payload = {
        "userRequest": {
            "user": {
                "id": "direct_user_id_1234",
                "properties": {},
            },
            "utterance": "배송 조회해 주세요",
        }
    }
    payload = KakaoPayload.model_validate(raw_payload)
    assert payload.get_user_id() == "direct_user_id_1234"
    assert payload.get_utterance() == "배송 조회해 주세요"
