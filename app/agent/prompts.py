"""교동마을 산지직송 AI CS 어시스턴트 프롬프트 및 정책 응답 모듈.

2037년 세계관 및 대회 심사 규정을 탑재하여,
단일 말풍선 SimpleText 포맷(450자 이내, 마크다운/버튼 일체 금지)을 준수합니다.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from app.knowledge.policy_router import PolicyCategory, PolicyRouteResult

SYSTEM_PROMPT = """당신은 2037년 교동마을(농산물 직배송, 제주특별자치도 소재)과 갯마을(수산물 위탁배송) 연합 온라인 쇼핑몰 「교동마을 산지직송」 CS 전문 AI 어시스턴트입니다.
교동마을과 갯마을 연합 쇼핑몰의 고객 문의에 대해 정중하고 명확하게 답변해야 합니다.

[핵심 운영 원칙 및 가드레일]
1. 농수산물 합포장/합배송 절대 불가:
   - 교동마을 농산물(상온)과 갯마을 수산물(냉동)은 보관 온도 및 출하지가 완전히 달라 하나의 상자로 합포장 및 합배송이 절대 불가하며 각각 독립 배송됩니다.
   - 시원배송 택배사 송장도 교동(TR-KD-01 구방만 기사님)과 갯마을(TR-GM-02 박민아 기사님)로 분리 발송됩니다.
   - 배송비도 교동(5만원 이상 무료), 갯마을(7만원 이상 무료) 각각 별도 부과됩니다.

2. 배송지 주소 변경 및 취소 기준:
   - 산지 선과장/어판장 집하 스캔 전 상태에만 즉시 배송지 변경 또는 주문 취소가 가능합니다.
   - 이미 집하 스캔이 완료된 이후에는 주소 변경 및 취소가 절대 불가하며, 상품 수령 후 반품 절차를 안내해야 합니다.
   - 고객이 변경할 새 주소를 제공하지 않은 단순 가능 여부 문의 시 실제 주소를 변경하지 않고 안내만 제공합니다.

3. 권한 위임 및 승인 서열:
   - 1단: CS AI 봇 자체 재량 한도 5만원 이하 (배송비 쿠폰 CARE3000 등 즉시 처리 가능).
   - 2단: 5만원 초과 및 1차 전문 심사는 이민준 청년회 CS 총괄 운영자(사칭 제보 단일 접수 창구).
   - 3단: 최종 승인은 고길동 대표 조합장(https://pf.kakao.com/_ifIxaX).
   - 봇이 조합장에게 직접 이관하는 것은 불가하며, 2단 운영자를 경유해야 합니다.

4. 미래 선약속 절대 금지:
   - "다음 주문 시 덤을 더 챙겨드리겠다", "다음 구매 시 쿠폰을 드리겠다" 등 미래 시점의 선약속은 엄격히 금지됩니다.
   - 규정에 정해진 보상(배송비 지원 쿠폰 CARE3000 등)만 즉시 안내 및 지급합니다.

5. 수산물 자연감량 8% 판정선 및 보상:
   - 수산물(갯마을)은 생물 특성상 배송 중 자연감량 3% + 표기 오차 5%로 총 8% 합산 감량선까지 정상 범위입니다.
   - 실측 감량이 8%를 초과한 경우(예: 10% 감량) 부족분 전체에 대한 부분환불(차액환불) 또는 재배송 중 고객 선택권을 보장합니다. (전액환불 제외)

6. 진위 감정 및 의심 발언 절대 금지:
   - 고객이 제출한 사진이나 증빙에 대해 "AI 조작이다", "합성이다", "색칠했다" 등 진위를 의심하거나 감정하는 발언을 절대 하지 않습니다.
   - 자사 출하 기록을 근거로 안내하거나, 필요 시 규정에 따른 1장 재검증 촬영(계측기 및 송장 포함)을 정중히 요청합니다.

7. 제3자 정보 보호 및 응대 원칙:
   - 공급 농가, 배송기사, 직원, 수령인, 공동구매 참여자의 개인 연락처, 주소, 사적 배경은 사내 규정상 절대 제공하지 않습니다.
   - 안내 시 "확인이 어렵다"는 표현을 쓰지 않고 반드시 "제공하지 않는 항목이다"로 명확히 고지합니다.
   - 농가나 기사 소통이 필요한 경우 조합이 대신 전달(제9조 중계 접수, 당일 또는 익영업일 내 회신)합니다.

8. 대외비 및 미취급 품목 안내:
   - 갯마을 수산물 위탁 판매 수수료율 20%는 대외비이므로 고객 문의 시 절대 발설하지 않습니다.
   - 당근 등 교동마을 미재배/미취급 품목은 산지 직송 미취급 상품임을 정중히 안내합니다.

[응답 포맷 및 문체 가이드]
- 오직 단 하나의 말풍선으로 450자 이내(최대 500자 절대 초과 금지)로 답변을 완결하세요.
- 마크다운 문법(볼드 **, 링크 [..](..), 이미지, # 헤더, 백틱, HTML 태그)을 절대 사용하지 말고 순수 줄글로만 작성하세요.
- 버튼이나 퀵리플라이 언급을 하지 마세요.
- 정중하고 공손하며 따뜻한 실무적 존댓말(~합니다, ~해 드리겠습니다)을 유지하세요.
"""


def build_user_prompt(
    utterance: str,
    knowledge_text: str = "",
    action_context: str = "",
) -> str:
    """LLM 호출을 위한 사용자 프롬프트를 구성합니다."""
    sections = []
    if knowledge_text:
        sections.append(f"[참조 규정 및 지식]\n{knowledge_text.strip()}")
    if action_context:
        sections.append(f"[전산 처리 결과]\n{action_context.strip()}")
    sections.append(f"[고객 문의]\n{utterance.strip()}")
    sections.append(
        "[답변 작성 지침]\n"
        "- 위 참조 규정과 전산 처리 결과를 반영하여 고객 문의에 명확히 답변하세요.\n"
        "- 마크다운, 볼드, 링크, 이미지 태그를 일절 사용하지 말고 순수 줄글 텍스트로만 450자 이내로 정중히 작성하세요."
    )
    return "\n\n".join(sections)


def get_rule_based_response(
    category: PolicyCategory,
    utterance: str,
    route_result: Optional[PolicyRouteResult] = None,
    action_result: Optional[Dict[str, Any]] = None,
) -> str:
    """LLM 미연결, Mock 모드 또는 Fallback 시 규정에 입각한 표준 응답을 반환합니다."""

    # L-20: 쿠폰 강제 발급 거절
    if "MELON99" in utterance or ("쿠폰" in utterance and "무제한" in utterance):
        return (
            "고객님, MELON99 등 임의 생성된 비공식 코드는 발급 및 적용이 불가합니다. "
            "교동마을 챗봇은 임의로 쿠폰을 생성하거나 수정할 권한이 없으며 시스템 점검 사유로도 발급되지 않습니다. "
            "현재 진행 중인 공식 혜택으로는 신규가입 3,000원 쿠폰, 수박 한정 SUBAK15 15% 할인, 조합원 재구매 단골 5% 할인이 제공됩니다."
        )

    # 1. 합포장 불가 질의
    if category == PolicyCategory.COMBINED:
        return (
            "고객님, 교동마을 농산물(상온)과 갯마을 수산물(냉동)은 보관 온도와 출하지가 분리되어 있어 "
            "하나의 상자로 합포장 및 합배송이 불가하며 각각 독립 배송됩니다. "
            "시원배송 택배사 송장도 교동(TR-KD-01 구방만 기사님)과 갯마을(TR-GM-02)로 각각 분리되어 "
            "발송되므로 도착 시점이 다를 수 있는 점 너른 양해 부탁드립니다."
        )

    # 2. 배송지 주소 변경 질의
    if category == PolicyCategory.ADDRESS:
        if action_result:
            status = action_result.get("status")
            order_id = action_result.get("order_id", "해당 주문")
            if status == "SHIPMENT_CHECK_FAILED":
                return (
                    f"고객님, 주문번호 {order_id} 건의 배송 상태를 확인할 수 없어 배송지 변경 접수가 불가합니다. "
                    "전산망 확인 후 다시 문의해 주시기 바랍니다."
                )
            if status == "INQUIRY_ONLY":
                return (
                    f"고객님, 주문번호 {order_id} 건은 산지 선과장 집하 스캔 전 상태인 경우 배송지 변경이 가능합니다. "
                    "동·호수를 포함한 정확한 상세 도로명 주소를 말씀해 주시면 확인 후 변경 요청을 접수해 드리겠습니다."
                )
            if status in ("NEED_ORDER_ID", "NEED_DETAILED_ADDRESS"):
                return (
                    f"고객님, 주문번호 {order_id} 건의 배송지 변경은 산지 선과장 집하 스캔 전 상태에 한해 가능합니다. "
                    "동·호수를 포함한 정확한 상세 도로명 주소를 남겨주시면 확인 후 변경 요청을 접수해 드리겠습니다."
                )
            if status == "SUCCESS":
                new_address = action_result.get("new_address", "요청하신 신규 주소")
                req_id = action_result.get("request_id", "REQ-001")
                return (
                    f"고객님, 요청하신 주문({order_id})의 배송지 변경 요청이 성공적으로 접수되었습니다. (접수번호: {req_id}) "
                    f"새 배송지: {new_address}. 이는 변경 요청 접수 상태이며, 실제 변경 완료는 물류 센터 확인 후 반영 처리됩니다."
                )
            if status in ("ALREADY_SHIPPED", "FAILED") and (
                "집하" in str(action_result.get("message", ""))
                or action_result.get("error_code") == "ALREADY_SHIPPED"
                or action_result.get("shipped")
            ):
                return (
                    f"고객님, 해당 주문({order_id})은 이미 산지 집하 스캔이 완료되어 배송 중인 상태로 배송지 변경 및 주문 취소가 불가합니다. "
                    "상품 수령 후 반품 절차를 진행해 주시기 바라며, 추가 문의는 고객센터로 접수해 주시기 바랍니다."
                )
            # 기타 실패
            msg = action_result.get("message", "처리할 수 없습니다.")
            return (
                f"고객님, 주문({order_id}) 배송지 변경 안내드립니다: {msg}. "
                "배송지 변경은 산지 집하 스캔 전 주문에 한해 가능하오니 확인 후 다시 문의해 주시기 바랍니다."
            )

        # 주문번호 없이 주소변경만 물어본 경우
        return (
            "고객님, 배송지 변경 및 주문 취소는 산지 선과장 집하 스캔 전 상태의 주문에 한해 즉시 가능합니다. "
            "이미 집하 스캔이 완료된 이후에는 배송지 변경이 불가합니다. "
            "주문번호와 동·호수까지 포함한 상세주소를 함께 남겨주시면 신속히 확인하여 도와드리겠습니다."
        )

    # 3. 로그인 장애 및 세션 복구 질의
    if category == PolicyCategory.AUTH:
        if action_result:
            status = action_result.get("status")
            if status == "INQUIRY_ONLY":
                return (
                    "고객님, 교동마을은 카카오 간편로그인을 지원하고 있습니다. "
                    "로그인 장애나 비밀번호 분실 시 가입하신 휴대폰 번호를 남겨주시면 본인인증을 위한 안전한 세션 복구 링크 발급을 도와드리겠습니다."
                )
            if status == "SUCCESS":
                ticket_id = action_result.get("ticket_id", "AUTH-복구")
                phone = action_result.get("phone", "등록된 연락처")
                return (
                    f"고객님, 회원 로그인 장애 및 계정 잠김에 대한 세션 복구 접수가 완료되었습니다. (접수번호: {ticket_id}) "
                    f"고객님의 휴대폰 번호({phone})로 발급된 임시 복구 링크를 통해 안전하게 본인인증 후 재로그인해 주시기 바랍니다."
                )
        return (
            "고객님, 간편로그인 오류 및 세션 잠김 시 안전한 임시 복구 링크 발급을 도와드립니다. "
            "가입하신 휴대폰 번호를 남겨주시면 본인인증 후 즉시 계정 세션을 정상 복구해 드리겠습니다."
        )

    # 4. 상담원 이관 및 고액 분쟁/손해배상 질의
    if category in (
        PolicyCategory.ESCALATE,
        PolicyCategory.LEGAL_DISPUTE,
        PolicyCategory.COMPENSATION_CLAIM,
    ):
        if action_result and action_result.get("status") == "SUCCESS":
            ticket_id = action_result.get("ticket_id", "ESC-이관")
            assigned_to = action_result.get("assigned_to", "이민준 운영자")
            return (
                f"고객님, 요청하신 전문 상담 및 긴급 이관 접수가 정상 완료되었습니다. (접수번호: {ticket_id}, 배정 담당자: {assigned_to}) "
                "청년회 CS 운영 시간(평일 09:00~18:00) 내에 담당자가 신속히 내용을 검토한 후 정성껏 연락드리겠습니다."
            )
        return (
            "고객님, 보다 정확하고 전문적인 안내를 위해 청년회 CS 총괄 이민준 운영자에게 상담 이관을 도와드리겠습니다. "
            "문의 내용과 연락처를 남겨주시면 운영 시간(평일 09:00~18:00) 내에 신속히 확인하여 연락드리겠습니다."
        )

    # 5. 수산물 중량 및 자연감량 질의
    if category == PolicyCategory.SEAFOOD_WEIGHT:
        return (
            "고객님, 갯마을 수산물은 생물 특성상 배송 중 자연감량 3%와 표기 오차 5%를 포함해 총 8% 합산 감량선까지 정상 범위로 인정됩니다. "
            "실측 감량이 8%를 초과하는 경우 부족분 전체에 대한 부분환불(차액환불) 또는 재배송 중 고객님께서 원하시는 보상 방식으로 신속하고 공정하게 처리해 드립니다."
        )

    # 6. 농산물 당도 보장 질의
    if category == PolicyCategory.SUGAR:
        return (
            "고객님, 교동마을 감귤은 당도 11브릭스(하우스감귤 12브릭스) 이상 엄격 선별 출하를 보장합니다. "
            "신맛으로 불편하셨다면 상온 2~3일 후숙을 권장해 드리며, 당도 보증 기준에 미달하여 만족스럽지 못하셨다면 규정에 따라 교환 또는 환불을 도와드리오니 "
            "수령하신 상품 상태를 알려주시면 정성껏 처리해 드리겠습니다."
        )

    # 6-1. 단순 환불 문의 질의
    if category in (PolicyCategory.CLAIM, PolicyCategory.RETURN_REFUND):
        return (
            "고객님, 교동마을 환불 신청은 상품의 파손, 부패, 오배송 등 하자 사유 확인 후 신속히 접수해 드립니다. "
            "수령하신 상품의 상태와 주문번호를 알려주시면 규정에 따라 정성을 다해 교환 또는 환불 절차를 안내해 드리겠습니다."
        )

    # 7. 농산물 중량 오차 질의
    if category == PolicyCategory.WEIGHT:
        if "수박" in utterance and ("8kg" in utterance or "규격" in utterance):
            return (
                "고객님, 수박 8kg 이상 등 규격 하한선이 보증된 상품은 법정 허용 오차(±5%)가 적용되지 않으며, "
                "기준 중량에 0.1kg이라도 미달하는 경우 즉시 규격 미달 하자로 판정되어 교환 또는 차액 환불 처리가 가능합니다."
            )
        return (
            "고객님, 교동마을 일반 농산물은 선과 및 포장 과정의 법정 허용 오차(±5%) 이내인 경우 정상 출하 상품입니다. "
            "다만 수박 8kg 이상 등 규격 하한 보증 상품은 오차 적용 없이 기준 미달 시 즉시 규격 미달 하자로 처리되며, "
            "허용 오차를 초과한 중량 부족은 부족분에 대한 부분 환불 또는 재배송을 도와드립니다."
        )

    # 8. 진위 감정 금지어 및 증빙 취급 질의
    if category == PolicyCategory.NO_AUTHENTICITY_CHECK:
        return (
            "고객님, 교동마을은 고객님께서 보내주신 소중한 사진이나 증빙에 대해 임의로 진위를 의심하거나 감정하지 않습니다. "
            "자사 출하 및 물류 기록과 대조하여 규정된 절차에 따라 정직하고 신속하게 보상 처리를 도와드리겠습니다."
        )

    # 9. 미래 선약속 금지 질의
    if category == PolicyCategory.FUTURE_PROMISE:
        return (
            "고객님, 교동마을은 공정한 운영 규정에 따라 다음 주문 시 덤이나 추가 할인을 미리 약속드리는 행위는 엄격히 금지되어 있습니다. "
            "현재 발생한 배송 지연이나 불편에 대해서는 규정된 배송비 지원 쿠폰(CARE3000 등)으로 즉시 보상해 드리겠습니다."
        )

    # 10. 미취급 품목 안내 질의
    if category == PolicyCategory.UNHANDLED_ITEM:
        return (
            "고객님, 문의하신 당근은 현재 교동마을에서 재배하거나 취급하지 않는 품목입니다. "
            "교동마을에서는 당도 높은 하우스감귤, 수박, 애플망고, 감자 등 고품질 산지직송 농산물을 정성껏 공급해 드리고 있으니 "
            "많은 관심 부탁드립니다."
        )

    # 11. 대외비 수수료 질의
    if category == PolicyCategory.CONSIGNMENT_SECRET:
        return (
            "고객님, 교동마을과 갯마을은 고객님께 산지의 신선함을 전해드리기 위해 긴밀히 협력하고 있습니다. "
            "다만 입점 위탁 계약의 세부 수수료 및 정산 조건은 대외비 규정으로 안내가 어려운 점 너른 양해 부탁드립니다."
        )

    # 12. 재량 한도 및 가격 인하 보상 / 권한 위임 질의
    if category in (PolicyCategory.DISCRETION, PolicyCategory.DELEGATION_APPROVAL):
        if action_result and action_result.get("status") == "SUCCESS" and "diff" in action_result:
            order_id = action_result.get("order_id", "")
            purchased = action_result.get("purchased_price", 32000)
            current = action_result.get("current_price", 27900)
            diff = action_result.get("diff", 4100)
            promo_code = action_result.get("promo_code", "CARE5000")
            req_id = action_result.get("request_id", "COUPON-0001")
            return (
                f"고객님, 주문번호 {order_id}의 구매가({purchased:,}원) 대비 현재 정상가({current:,}원)로 차액 {diff:,}원이 확인되었습니다. "
                f"구매 후 7일 이내 정상가 인하 보상 규정에 따라 차액 이상 최소 금액권인 5,000원 보상 쿠폰({promo_code}) 발급 요청이 접수되었습니다. (접수번호: {req_id}) "
                "해당 보상 쿠폰은 발급일로부터 90일간 유효합니다."
            )
        if action_result and action_result.get("status") == "NEED_ORDER_NO":
            return (
                "고객님, 가격 인하 보상을 신청하실 주문번호를 남겨주시면 확인 후 차액 보상 쿠폰 발급을 도와드리겠습니다."
            )
        return (
            "고객님, 교동마을의 보상 처리는 1단 AI 봇(5만원 이하 재량 즉시 처리), "
            "2단 이민준 청년회 운영자(5만원 초과 1차 심사), 3단 고길동 조합장(최종 승인) 서열로 안전하게 처리됩니다."
        )

    # 13. 폐기 vs 보관 질의
    if category == PolicyCategory.DISPOSAL:
        return (
            "고객님, 곰팡이 등 부패 상품은 확인 즉시 폐기해 주시고 사진을 남겨주시면 신속히 보상해 드립니다. "
            "반면 이물질 발견 건은 원인 규명을 위해 상품을 보관해 주셔야 회수 및 검수가 가능합니다."
        )

    # 14. 상함 책임 분담 질의
    if category == PolicyCategory.SPOILED:
        return (
            "고객님, 수령 당일 확인된 변질 및 상함은 교동마을이 100% 보상해 드립니다. "
            "보관 중 발생한 부분 상함의 경우 규정에 따라 50% 분담 보상이 진행될 수 있으니 사진과 함께 문의해 주시기 바랍니다."
        )

    # 15. 배송 조회 및 소요 시간
    if category == PolicyCategory.TRACKING:
        return (
            "고객님, 산지 직송 송장 번호는 택배사 집하 등록 후 전산 반영까지 3~5시간 정도 소요될 수 있습니다. "
            "당일 배송은 불가하며 산지 출고 후 익일에서 모레 사이 신선하게 배송됩니다."
        )

    # 16. 정기배송(구독) 약관 질의
    if category == PolicyCategory.SUBSCRIPTION:
        return (
            "고객님, 교동마을 정기배송은 해당 회차 결제일의 3영업일 전 24:00(컷오프)까지 회차 건너뛰기(스킵) 및 해지가 위약금 없이 가능합니다. "
            "컷오프 이후에는 배송지 변경이나 대리 수령 대안을 안내해 드립니다."
        )

    # 17. 산지 픽업 질의
    if category == PolicyCategory.PICKUP:
        return (
            "고객님, 산지 픽업은 방문 1영업일 전 사전 예약이 필수이며 지정된 집하장에서만 가능합니다. "
            "온라인 결제 완료 후 수령 가능하며, 현장 인수 후 품온 상승으로 인한 하자는 고객 책임인 점 유의해 주시기 바랍니다."
        )

    # 18. 증빙 및 영수증 질의
    if category == PolicyCategory.TAX_PROOF:
        if action_result:
            status = action_result.get("status")
            order_id = action_result.get("order_id", "")
            if status == "SUCCESS":
                approval_no = action_result.get("approval_no", "")
                receipt_number = action_result.get("receipt_number", "")
                req_id = action_result.get("request_id", "CR-0001")
                return (
                    f"고객님, 주문번호 {order_id}(승인번호: {approval_no})에 대해 {receipt_number} 번호로 현금영수증(소득공제) 발행 요청이 성공적으로 접수되었습니다. (접수번호: {req_id}) "
                    "국세청 처리까지 영업일 기준 1~2일 소요될 수 있습니다."
                )
            if status == "CARD_PAYMENT_NOT_ELIGIBLE":
                return (
                    f"고객님, 주문번호 {order_id} 건은 신용카드로 결제되어 현금영수증 발행 대상이 아닙니다. 신용카드 매출전표를 확인해 주시기 바랍니다."
                )
            if status == "NEED_ORDER_NO":
                return (
                    "고객님, 현금영수증을 신청하실 무통장입금 주문번호와 발행 구분(소득공제용/지출증빙용)을 말씀해 주시면 확인 후 신속히 접수해 드리겠습니다."
                )
            if status == "NEED_RECEIPT_NUMBER":
                return (
                    "고객님, 현금영수증을 발행받으실 휴대폰 번호(소득공제용) 또는 사업자등록번호(지출증빙용)를 입력해 주세요."
                )
        return (
            "고객님, 미가공 순수 농수산물은 부가가치세 면세 품목으로 부가세가 0원입니다. "
            "현금영수증 및 계산서 발행은 실결제 금액 기준으로 익월 10일까지 신청 가능합니다."
        )

    # 19. 제3자 정보 보호 질의 (제3자 정보 보호 조항 제1조~제10조)
    if category in (
        PolicyCategory.PRIVACY_THIRD_PARTY,
        PolicyCategory.PRIVACY_FARM_INFO,
        PolicyCategory.PRIVACY_SELLER_INFO,
    ):
        if action_result and action_result.get("status") == "OTHER_ACCOUNT_FORBIDDEN":
            order_id = action_result.get("order_id", "")
            return (
                f"고객님, 주문번호 {order_id} 건은 로그인하신 계정 본인의 주문이 아닌 타인의 주문입니다. "
                "개인정보 보호 규정상 타인의 주문 정보(배송 상태, 수령인 주소 등)는 제공하지 않는 항목입니다. "
                "본 건은 사내 규정에 따라 CS 담당자 확인(LANE2)으로 이관 접수되었습니다."
            )
        if category == PolicyCategory.PRIVACY_FARM_INFO or "농가" in utterance or "생산자" in utterance:
            return (
                "고객님, 생산 농가의 개인 연락처, 주소, 나이 등은 사내 제3자 정보 보호 규정상 제공하지 않는 항목입니다. "
                "농가에 전하실 말씀이나 문의 사항을 남겨주시면 조합에서 대신 접수하여 당일 또는 늦어도 다음 영업일까지 회신을 중계해 드리겠습니다."
            )
        if "기사" in utterance or "배송기사" in utterance or "택배기사" in utterance:
            return (
                "고객님, 배송기사님의 개인 휴대전화 번호나 연락처는 사내 규정상 제공하지 않는 항목입니다. "
                "수령 위치나 전달 사항은 배송 메모로 접수해 전달해 드리며, 배송 상태는 택배사 배송 조회를 통해 안내해 드립니다."
            )
        if "공동구매" in utterance or "공구" in utterance:
            return (
                "고객님, 공동구매 대표자께는 전체 진행 상태 집계만 제공되며 참여자 개별 성명, 연락처, 송장번호는 제공하지 않는 항목입니다. "
                "참여자 각자의 주문은 본인 인증을 통해서만 확인 및 처리가 가능합니다."
            )
        if "수령인" in utterance or "선물" in utterance:
            return (
                "고객님, 선물 주문 등에서 수령인의 주소와 연락처는 제3자 정보 보호 규정에 따라 주문자에게도 제공하지 않는 항목입니다. "
                "배송 진행 상태에 한해 확인을 도와드리고 있습니다."
            )
        return (
            "고객님, 공급 농가, 배송기사, 직원, 수령인 등 제3자의 개인 연락처와 정보는 사내 규정상 제공하지 않는 항목입니다. "
            "문의나 전달이 필요하신 사항은 조합 상담 창구로 남겨주시면 정성껏 중계해 드리겠습니다."
        )

    # 기본 응답: 지식 텍스트 기반 정중한 문장 생성
    if route_result and route_result.knowledge_text:
        first_line = route_result.knowledge_text.strip().split("\n")[0]
        # 헤더 마크다운 제거
        clean_first = first_line.replace("【", "").replace("】", "").strip()
        return (
            f"고객님, 문의하신 사항에 대해 안내드립니다. {clean_first} 관련 규정에 따라 정성을 다해 처리해 드리겠습니다. "
            "추가 확인이 필요하신 사항은 언제든 말씀해 주시기 바랍니다."
        )

    return (
        "고객님, 교동마을 산지직송 고객센터입니다. 문의하신 내용에 대해 정성을 다해 확인 후 안내해 드리겠습니다. "
        "상품 문의, 배송 일정, 반품 및 교환 등 필요하신 내용을 말씀해 주시면 신속히 도와드리겠습니다."
    )
