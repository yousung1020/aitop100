"""정책 지식 베이스 및 라우터 단위 테스트 (tests/test_policies.py)

공식 판매·환불 규정(제1조~제25조) 및 시원배송 택배 계약서(제1조~제12조)에 대한 단위 테스트
"""

import pytest

from app.knowledge import (
    PolicyRouter,
    PolicyCategory,
    get_relevant_knowledge,
    GYODONG_POLICY,
    GAETMAEUL_POLICY,
    COMMON_POLICIES,
    RULE_ARTICLES,
    CONTRACT_ARTICLES,
    STAFF_INFO,
    DISCRETION_THRESHOLD_AMOUNT,
    EscalationLane,
    APPROVAL_HIERARCHY,
    OPERATOR_BACKUP_PATH,
    FUTURE_PROMISE_RULE,
    OVER_PROMISE_RULE,
    APPROVAL_PROCEDURE_RULE,
    DELEGATION_ARTICLES,
    DelegationArticle,
    SeafoodWeightRuleArticle,
    SEAFOOD_NATURAL_LOSS_PCT,
    LABEL_TOLERANCE_PCT,
    SEAFOOD_TOTAL_TOLERANCE_PCT,
    SEAFOOD_WEIGHT_ARTICLES,
    SEAFOOD_WEIGHT_APPENDIX,
    SeafoodConsignmentContractArticle,
    CONSIGNMENT_COMMISSION_PCT,
    CONSIGNMENT_SECRET_PROMPT,
    SEAFOOD_CONSIGNMENT_ARTICLES,
    HarvestRecordEntry,
    HARVEST_CONFIRMATION_RULES,
    HARVEST_RECORDS,
    SUGAR_GUARANTEE_BRIX,
    UNPROMISED_LINE_SUGAR_POLICY,
    SPEC_UNDERWEIGHT_NO_TOLERANCE_RULE,
    evaluate_agri_weight_or_spec,
    evaluate_seafood_weight,
    EvidenceType,
    EvidenceArticle,
    EVIDENCE_ARTICLES,
    EVIDENCE_HIERARCHY_RANK,
    FORBIDDEN_AUTHENTICITY_PHRASES,
    EVIDENCE_MATCHING_TABLE,
    MISMATCH_SIGNALS_TABLE,
    compare_evidence_authority,
    check_forbidden_authenticity_phrase,
    format_reverification_request,
    load_raw_knowledge_base,
    get_village_policies,
    CropDisasterRecord,
    CROP_DISASTER_RULES,
    CROP_DISASTER_NOTES,
    CROP_DISASTER_RECORDS,
    GYODONG_PRODUCER_CATALOG,
    GYODONG_UNHANDLED_ITEMS,
    is_gyodong_unhandled_item,
    get_crop_disaster_record,
    get_crop_disasters_by_crop,
    get_crop_disaster_rule,
    LogisticsCancellationRecord,
    LogisticsCancellationDetail,
    LOGISTICS_CONFIRMATION_RULES,
    LOGISTICS_CANCELLATION_NOTES,
    LOGISTICS_CANCELLATION_RECORDS,
    LOGISTICS_TYPHOON_DETAILS,
    get_logistics_record,
    get_logistics_rule,
    get_logistics_typhoon_details,
    can_change_address_or_cancel_typhoon_period,
    is_today_logistics_normal,
    PrivacyPolicyArticle,
    PRIVACY_POLICY_ARTICLES,
    PRIVACY_POLICY_EFFECTIVE_DATE,
    PRIVACY_VERIFICATION_DIRECTION_RULE,
    PRIVACY_CUMULATIVE_CONFIRMATION_LIMIT,
    PRIVACY_STOP_CUMULATIVE_RULE,
    PRIVACY_THIRD_PARTY_ORDER_RULE,
    PRIVACY_CREDENTIAL_FORBIDDEN_RULE,
    PRIVACY_REFUND_ACCOUNT_RULE,
    PRIVACY_SELLER_INFO_RULE,
    PRIVACY_FARM_INFO_RULE,
    PRIVACY_DATA_RIGHTS_RULE,
    PRIVACY_EXTERNAL_REQUEST_RULE,
    PRIVACY_GROUP_COLLECTION_RULE,
    PRIVACY_NON_DISCLOSABLE_RULE,
    PRIVACY_RETENTION_PERIODS,
    get_privacy_article,
    check_reverse_privacy_query,
    check_credential_solicitation,
    check_cumulative_confirmation_limit,
    validate_refund_account_name,
    SubscriptionArticle,
    SUBSCRIPTION_TERMS_ARTICLES,
    SUBSCRIPTION_CUTOFF_BUSINESS_DAYS,
    SUBSCRIPTION_ADVANCE_NOTICE_DAYS,
    SUBSCRIPTION_CONSECUTIVE_SKIP_CHECK_THRESHOLD,
    SUBSCRIPTION_CANCELLATION_FORBIDDEN_ACTIONS,
    SUBSCRIPTION_POST_CUTOFF_ALTERNATIVES,
    SUBSCRIPTION_DECISION_STEPS,
    SUBSCRIPTION_DECISION_MATRIX,
    get_subscription_article,
    get_all_subscription_articles,
    calculate_cutoff_datetime,
    is_before_or_at_cutoff,
    evaluate_subscription_request,
    FarmPickupSection,
    PICKUP_ADVANCE_RESERVATION_REQUIRED,
    PICKUP_RESERVATION_DEADLINE,
    PICKUP_LOCATION_RULE,
    PICKUP_TIME_RULE,
    PICKUP_PAYMENT_RULE,
    PICKUP_AUTH_RULE,
    PICKUP_PROXY_RULE,
    PICKUP_THIRD_PARTY_PRIVACY_RULE,
    PICKUP_TEMP_RESPONSIBILITY_BOUNDARY,
    PICKUP_VEHICLE_TEMP_CLAIM_RULE,
    PICKUP_SHIPPING_FEE,
    PICKUP_INSPECTION_RIGHT,
    PICKUP_NO_SHOW_RULE,
    PICKUP_ASSOCIATION_FAULT_RULE,
    PICKUP_GUIDE_SCRIPT,
    FARM_PICKUP_SECTIONS,
    get_pickup_section,
    get_all_pickup_sections,
    evaluate_pickup_eligibility,
    evaluate_pickup_temp_claim,
    PAYMENT_PROOF_RULES,
    CASH_RECEIPT_RULES,
    TAX_INVOICE_RULES,
    PROOF_CORRECTION_CODES,
    PROOF_REFUND_RULES,
    PROOF_REFUSAL_RULES,
    PROOF_COUNSELING_TEMPLATES,
    calculate_tax_and_vat,
    evaluate_proof_request,
    evaluate_cash_receipt_request,
    evaluate_tax_invoice_request,
    evaluate_proof_correction,
    check_proof_refusal,
    OfficialProductSKU,
    OFFICIAL_PRODUCTS,
    get_official_product,
    evaluate_product_sugar_claim,
    evaluate_product_weight_claim,
    ReconciliationCode,
    ReconciliationRule,
    RECONCILIATION_RULES,
    RECONCILIATION_TIME_TOLERANCE_MINUTES,
    RECONCILIATION_TIME_TOLERANCE_SECONDS,
    RECONCILIATION_KEYS_DESCRIPTION,
    RECONCILIATION_GUIDE_SCRIPTS,
    check_reconciliation_time_match,
    verify_reconciliation_4_keys,
    diagnose_reconciliation_case,
    evaluate_m01_order_recovery,
    SeasonStatus,
    SeasonStatusInfo,
    SeasonRuleArticle,
    AgriSeasonLine,
    SEASON_STATUS_DEFINITIONS,
    SEASON_RULE_ARTICLES,
    AGRI_SEASON_LINES,
    SEASON_2037_TRANSITIONS,
    SEASON_2037_UPCOMING,
    get_agri_season_line,
    get_agri_season_status,
    get_current_season_status,
    get_active_lines_in_month,
    is_summer_house_citrus_normal,
    check_season_closed_forbidden_words,
    evaluate_season_inquiry,
)


class TestKnowledgeRules:
    """기본 데이터 클래스 및 규정 무결성 검증"""

    def test_gyodong_policy_structure(self):
        assert GYODONG_POLICY.village_name == "교동마을"
        assert GYODONG_POLICY.item_type == "농산물"
        assert "감귤" in GYODONG_POLICY.items
        assert GYODONG_POLICY.base_shipping_fee == 4000
        assert GYODONG_POLICY.free_shipping_threshold == 50000
        assert "시원배송" in GYODONG_POLICY.logistics_partner
        assert "구방만" in GYODONG_POLICY.logistics_partner
        assert "TR-KD-01" in GYODONG_POLICY.logistics_partner
        assert "7일 이내" in GYODONG_POLICY.damage_compensation
        assert "고객이 선택" in GYODONG_POLICY.damage_compensation

    def test_gaetmaeul_policy_structure(self):
        assert GAETMAEUL_POLICY.village_name == "갯마을"
        assert GAETMAEUL_POLICY.item_type == "수산물"
        assert "은갈치" in GAETMAEUL_POLICY.items
        assert GAETMAEUL_POLICY.base_shipping_fee == 5000
        assert GAETMAEUL_POLICY.free_shipping_threshold == 70000
        assert "시원배송" in GAETMAEUL_POLICY.logistics_partner
        assert "콜드체인" in GAETMAEUL_POLICY.damage_compensation
        assert "선구제" in GAETMAEUL_POLICY.damage_compensation

    def test_official_rules_coverage(self):
        """제1조부터 제25조까지 전 조항이 존재하는지 검증"""
        for i in range(1, 26):
            assert i in RULE_ARTICLES, f"제{i}조 규정이 누락되었습니다."
            rule = RULE_ARTICLES[i]
            assert len(rule.title) > 0
            assert len(rule.content) > 0
            assert len(rule.key_points) > 0

        # 핵심 조항 세부 검증
        assert "±5%" in RULE_ARTICLES[6].content  # 제6조 중량 오차
        assert "11브릭스" in RULE_ARTICLES[7].content  # 제7조 당도
        assert "50%" in RULE_ARTICLES[10].content  # 제10조 상함 책임
        assert "원결제수단" in RULE_ARTICLES[12].content  # 제12조 환불 원칙
        assert "7일" in RULE_ARTICLES[20].content  # 제20조 접수 기한
        assert "인과관계" in RULE_ARTICLES[25].content  # 제25조 손해배상

    def test_official_contract_coverage(self):
        """택배 위탁 계약서 제1조부터 제12조까지 전 조항이 존재하는지 검증"""
        for i in range(1, 13):
            assert i in CONTRACT_ARTICLES, f"계약서 제{i}조가 누락되었습니다."
            contract = CONTRACT_ARTICLES[i]
            assert len(contract.title) > 0
            assert len(contract.content) > 0
            assert len(contract.key_points) > 0

        # 핵심 계약 조항 검증
        assert "집하 전" in CONTRACT_ARTICLES[3].content  # 제3조 배송 단계
        assert "3~5시간" in CONTRACT_ARTICLES[3].content  # 제3조 송장 조회
        assert "당일배송이 불가" in CONTRACT_ARTICLES[4].content  # 제4조 배송 소요
        assert "합배송이 제한" in CONTRACT_ARTICLES[6].content  # 제6조 합배송 제한
        assert "최대 3회차" in CONTRACT_ARTICLES[8].content  # 제8조 분할 배송
        assert "선구제" in CONTRACT_ARTICLES[11].key_points[0]  # 제11조 배송 중 파손
        assert "선재발송" in CONTRACT_ARTICLES[12].key_points[1]  # 제12조 배송 분실

    def test_staff_info(self):
        """구방만 기사님, 고길동 조합장님, 박수복/문귀남/최덕만 등 현장 인물 검증"""
        assert "구방만" in STAFF_INFO
        assert STAFF_INFO["구방만"].vehicle_no == "TR-KD-01"
        assert "시원배송" in STAFF_INFO["구방만"].organization

        assert "고길동" in STAFF_INFO
        assert "승인권자" in STAFF_INFO["고길동"].role
        assert "이민준" in STAFF_INFO

        # 농산물 생산 총괄 4인 및 생산자 라인업 검증
        assert "박수복" in STAFF_INFO
        assert "수박·멜론 생산 총괄" in STAFF_INFO["박수복"].role
        assert "문귀남" in STAFF_INFO
        assert "감귤(하우스/노지) 및 만감류 총괄" in STAFF_INFO["문귀남"].role
        assert "하동철" in STAFF_INFO
        assert "과수(애플망고·참다래) 총괄" in STAFF_INFO["하동철"].role
        assert "최덕만" in STAFF_INFO
        assert "밭작물(감자·고구마·절임배추) 총괄" in STAFF_INFO["최덕만"].role

    def test_delegation_articles_coverage(self):
        """권한 위임표 제1조부터 제10조까지 전 조항 검증"""
        for i in range(1, 11):
            assert i in DELEGATION_ARTICLES, f"권한 위임표 제{i}조 누락"
            art = DELEGATION_ARTICLES[i]
            assert len(art.title) > 0
            assert len(art.content) > 0
            assert len(art.key_points) > 0

        # 핵심 조항 세부 검증
        assert "50,000원" in DELEGATION_ARTICLES[4].content  # 제4조 5만원 임계
        assert "레인" in DELEGATION_ARTICLES[5].content  # 제5조 레인 정의
        assert "영업일 3일" in DELEGATION_ARTICLES[6].content  # 제6조 승인 기한
        assert "선약속" in DELEGATION_ARTICLES[7].content  # 제7조 선약속
        assert "쿠폰" in DELEGATION_ARTICLES[7].content  # 제7조 대체 쿠폰
        assert "상담 이력" in DELEGATION_ARTICLES[8].content  # 제8조 이력 조회
        assert "인적 서열" in DELEGATION_ARTICLES[10].content  # 제10조 서열

    def test_delegation_threshold_and_constants(self):
        """재량 한도 임계값(5만원), 승인 서열 및 대체 경로 상수 검증"""
        assert DISCRETION_THRESHOLD_AMOUNT == 50000
        assert len(APPROVAL_HIERARCHY) == 3
        assert "1단" in APPROVAL_HIERARCHY[0]
        assert "2단" in APPROVAL_HIERARCHY[1]
        assert "3단" in APPROVAL_HIERARCHY[2]
        assert "이민준" in APPROVAL_HIERARCHY[1]
        assert "고길동" in APPROVAL_HIERARCHY[2]

        assert OPERATOR_BACKUP_PATH == ["이민준", "구방만", "박민아"]
        assert EscalationLane.LANE_1_BOT == "LANE_1_BOT"
        assert EscalationLane.LANE_2_OPERATOR == "LANE_2_OPERATOR"
        assert EscalationLane.LANE_3_COMPENSATION == "LANE_3_COMPENSATION"
        assert EscalationLane.LANE_PARTNER == "LANE_PARTNER"

    def test_delegation_staff_info_extension(self):
        """신규 인물 홍이장, 박민아 및 기존 인물 역할 확장 검증"""
        assert "홍이장" in STAFF_INFO
        assert "협의" in STAFF_INFO["홍이장"].role
        assert "승인권자는 아님" in STAFF_INFO["홍이장"].responsibility

        assert "박민아" in STAFF_INFO
        assert "대체" in STAFF_INFO["박민아"].role
        assert "대체" in STAFF_INFO["박민아"].responsibility

        assert "3단" in STAFF_INFO["고길동"].role
        assert "2단" in STAFF_INFO["이민준"].role
        assert "대체" in STAFF_INFO["구방만"].role

    def test_common_policies(self):
        assert "합포장 절대 불가" in COMMON_POLICIES.no_combined_shipping_rule
        assert "계약서 제6조" in COMMON_POLICIES.no_combined_shipping_rule
        assert "전액 면제" in COMMON_POLICIES.island_shipping_exemption_rule
        assert "이민준" in COMMON_POLICIES.bulk_order_rule
        assert "09:00~18:00" in COMMON_POLICIES.operating_hours_rule

    def test_loader_functions(self):
        raw_text = load_raw_knowledge_base()
        assert len(raw_text) > 0
        assert "교동마을" in raw_text
        assert "구방만" in raw_text
        assert "고길동" in raw_text

        policies = get_village_policies()
        assert "gyodong" in policies
        assert "gaetmaeul" in policies


class TestPolicyRouter:
    """정책 라우팅 엔진 및 공식 조항별 매핑 검증"""

    def test_article_4_and_20_customer_choice_claim(self):
        """제4조 하자 환불 일반(고객선택권) 및 제20조 7일 기한 매핑"""
        utterance = "어제 받은 귤이 몇 개 터지고 짓물렀는데 어떻게 처리되나요?"
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.CLAIM
        assert "제4조" in result.knowledge_text
        assert "제20조" in result.knowledge_text
        assert "고객이 선택" in result.knowledge_text
        assert "7일 이내" in result.knowledge_text

    def test_article_5_disposal_vs_keeping(self):
        """제5조 폐기 및 보관(곰팡이 즉시 폐기 vs 이물/섭취이상 보관촬영) 매핑"""
        # 1. 단순 곰팡이
        mold_query = "귤 상자를 열었는데 하얗게 곰팡이가 피어있어요. 반송해야 하나요?"
        mold_res = PolicyRouter.route(mold_query)
        assert mold_res.primary_category == PolicyCategory.DISPOSAL
        assert "제5조" in mold_res.knowledge_text
        assert "폐기" in mold_res.knowledge_text
        assert "반송을 요구하지 않습니다" in mold_res.knowledge_text

        # 2. 섭취 후 이상 및 배탈 (보관 우선)
        sick_query = "과일을 먹고 나서 가족이 다 배탈이 났는데 병원비 손해배상 되나요?"
        sick_res = PolicyRouter.route(sick_query)
        assert sick_res.primary_category == PolicyCategory.DISPOSAL
        assert "제25조" in sick_res.knowledge_text
        assert "보관" in sick_res.knowledge_text
        assert "인과관계" in sick_res.knowledge_text

    def test_article_6_weight_tolerance(self):
        """제6조 무게·규격 허용오차(±5%) 매핑"""
        utterance = "5kg 박스 주문했는데 저울로 재보니 4.6kg밖에 안 나와요. 중량 미달 아닌가요?"
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.WEIGHT
        assert "제6조" in result.knowledge_text
        assert "±5%" in result.knowledge_text
        assert "차액환불" in result.knowledge_text or "부분환불" in result.knowledge_text

    def test_article_7_sugar_brix_guarantee(self):
        """제7조 당도 보장(11브릭스 이상, 고길동 조합장 승인) 매핑"""
        utterance = "한라봉 당도가 너무 떨어지고 싱거운데 당도 보장 기준이 어떻게 되나요?"
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.SUGAR
        assert "제7조" in result.knowledge_text
        assert "11브릭스" in result.knowledge_text
        assert "재배송" in result.knowledge_text
        assert "고길동 조합장" in result.knowledge_text

    def test_article_10_spoiled_responsibility_share(self):
        """제10조 상함의 책임 배분(50% 부분환불) 매핑"""
        utterance = "배송 온 상품이 좀 상했는데 보관 과실인지 출고 하자상함인지 애매한 경우는 어떻게 되나요?"
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.SPOILED
        assert "제10조" in result.knowledge_text
        assert "50%" in result.knowledge_text
        assert "상온 방치" in result.knowledge_text

    def test_article_11_and_12_refund_principle(self):
        """제11조 단순변심 및 제12조 원결제수단 환불 원칙 매핑"""
        utterance = "단순 변심으로 반품하고 싶은데 다른 계좌로 환불받을 수 있나요?"
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.RETURN_REFUND
        assert "제11조" in result.knowledge_text
        assert "제12조" in result.knowledge_text
        assert "원결제수단" in result.knowledge_text
        assert "왕복 배송비" in result.knowledge_text

    def test_contract_article_3_address_change(self):
        """계약서 제3조 집하 전/후 배송지 변경 및 취소 기준 매핑"""
        utterance = "주문 후 이사 때문에 배송지 주소를 변경하고 싶은데 가능한가요?"
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.ADDRESS
        assert "제3조" in result.knowledge_text
        assert "집하" in result.knowledge_text
        assert "변경" in result.knowledge_text

    def test_contract_article_3_and_4_tracking(self):
        """계약서 제3조(송장 3~5시간) 및 제4조(당일배송 불가) 매핑"""
        # 1. 송장 조회
        track_res = PolicyRouter.route("방금 송장번호를 받았는데 조회가 안 돼요. 오류인가요?")
        assert track_res.primary_category == PolicyCategory.TRACKING
        assert "3~5시간" in track_res.knowledge_text
        assert "정상" in track_res.knowledge_text

        # 2. 당일배송 여부
        day_res = PolicyRouter.route("오늘 주문하면 당일배송으로 오늘 저녁에 도착할 수 있나요?")
        assert day_res.primary_category == PolicyCategory.TRACKING
        assert "당일배송이 불가" in day_res.knowledge_text
        assert "익일 내지 모레" in day_res.knowledge_text

    def test_contract_article_6_combined_shipping(self):
        """계약서 제6조 상온/냉동 합배송 제한 매핑"""
        utterance = "감귤이랑 은갈치 같이 주문했는데 한 상자에 합포장해서 같이 배송 안 되나요?"
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.COMBINED
        assert "제6조" in result.knowledge_text
        assert "합배송 제한" in result.knowledge_text
        assert "구방만" in result.knowledge_text

    def test_contract_article_8_split_shipping(self):
        """계약서 제8조 분할 배송(최대 3회, 7일 이내) 매핑"""
        utterance = "주문한 물량을 한 번에 다 받기 힘들어서 나눠서 분할 배송받고 싶어요."
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.SPLIT_SHIPPING
        assert "제8조" in result.knowledge_text
        assert "최대 3회차" in result.knowledge_text
        assert "7일 이내" in result.knowledge_text

    def test_island_shipping_fee_exemption(self):
        """도서산간 배송비 전액 면제 매핑"""
        utterance = "제주도 섬 지역 배송 시 도서산간 추가 배송비가 얼마 붙나요?"
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.SHIPPING
        assert "전액 면제" in result.knowledge_text

    def test_weather_delay_inquiry(self):
        """기상 악화(풍랑주의보) 지연 매핑"""
        utterance = "제주 해상 풍랑주의보 때문에 결항이라는데 배송 지연되나요?"
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.WEATHER
        assert "풍랑주의보" in result.knowledge_text
        assert "1~2일" in result.knowledge_text

    def test_bulk_order_inquiry(self):
        """대량 구매 단체 주문 매핑"""
        utterance = "명절 선물용으로 30박스 대량 구매하려고 하는데 할인 가능한가요?"
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.BULK
        assert "제5조" in result.knowledge_text
        assert "이민준" in result.knowledge_text

    def test_auth_trouble_inquiry(self):
        """계정 장애 및 본인 인증 매핑"""
        utterance = "카카오 로그인이 안 돼서 비밀번호 찾기를 하려고 합니다."
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.AUTH
        assert "제12조" in result.knowledge_text

    def test_escalate_to_human_agent_inquiry(self):
        """상담원 연결 매핑"""
        utterance = "상담사 직원 연결 원합니다. 전화 통화 가능한 시간 알려주세요."
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.ESCALATE
        assert "이민준" in result.knowledge_text
        assert "09:00~18:00" in result.knowledge_text

    def test_future_promise_prohibition_and_alternative(self):
        """권한위임표 제7조 선약속 금지 및 1회 배송비 쿠폰 대체 매핑"""
        utterance = "다음에 주문할 때 배송비 무료로 해주면 이번 하자는 그냥 넘어갈게요."
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.FUTURE_PROMISE
        assert "제7조" in result.knowledge_text
        assert "선약속" in result.knowledge_text
        assert "조합장 승인으로도" in result.knowledge_text
        assert "쿠폰" in result.knowledge_text

    def test_past_over_promise_handling(self):
        """권한위임표 제8조 과거 과잉 약속 처리 기준 매핑"""
        utterance = "지난번 상담원이 다음 주문 시 무조건 무료배송 해준다고 약속했었는데요."
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.PAST_PROMISE
        assert "제8조" in result.knowledge_text
        assert "이력" in result.knowledge_text
        assert "쿠폰" in result.knowledge_text

    def test_legal_dispute_immediate_escalation(self):
        """권한위임표 제5조 분쟁·법률·안전·언론 사안 긴급 이관(레인 ②) 매핑"""
        utterance = "이거 소비자원에 고발하고 인터넷 뉴스 언론사에 제보해서 공론화하겠습니다."
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.LEGAL_DISPUTE
        assert "제5조" in result.knowledge_text
        assert "레인 ②" in result.knowledge_text
        assert "고길동" in result.knowledge_text

    def test_compensation_claim_formal_procedure(self):
        """권한위임표 제5조·규정 제25조 손해배상(병원비) 정식 이관(레인 ③) 매핑"""
        utterance = "병원비 치료비 손해배상 청구 절차와 승인 기준이 어떻게 되나요?"
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.COMPENSATION_CLAIM
        assert "제25조" in result.knowledge_text
        assert "레인 ③" in result.knowledge_text
        assert "인과관계" in result.knowledge_text
        assert "고길동" in result.knowledge_text

    def test_discretion_threshold_inquiry(self):
        """권한위임표 제4조 5만원 재량 한도 및 임계 매핑"""
        utterance = "상담사 재량 한도 5만원 넘는 보상 건은 누구 승인을 받아야 하나요?"
        result = PolicyRouter.route(utterance)

        assert result.primary_category in (PolicyCategory.DISCRETION, PolicyCategory.DELEGATION_APPROVAL)
        assert "50,000원" in result.knowledge_text or "5만원" in result.knowledge_text
        assert "승인" in result.knowledge_text

    def test_approval_hierarchy_and_backup_path(self):
        """권한위임표 제6조·제10조 승인 단계 인적 서열 및 대체 경로 매핑"""
        utterance = "이민준 상담원 부재 시 승인 대체 경로와 인적 서열, 영업일 3일 승인 절차가 궁금합니다."
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.DELEGATION_APPROVAL
        assert "제10조" in result.knowledge_text
        assert "이민준" in result.knowledge_text
        assert "구방만" in result.knowledge_text
        assert "박민아" in result.knowledge_text
        assert "영업일 3일" in result.knowledge_text

    def test_partner_claim_handling(self):
        """권한위임표 제5조·제10조 위탁(갯마을) 수산물 품질 협의 및 홍이장 경유 매핑"""
        utterance = "갯마을 위탁 상품 품질 클레임은 홍이장 님 공급 측 협의로 진행되나요?"
        result = PolicyRouter.route(utterance)

        assert result.primary_category == PolicyCategory.PARTNER_CLAIM
        assert "홍이장" in result.knowledge_text
        assert "공급 측 협의" in result.knowledge_text
        assert "승인권자" in result.knowledge_text

    def test_compact_knowledge_text_length(self):
        """반환되는 지식 텍스트가 400자 이하로 컴팩트하게 압축되어 있는지 확인"""
        test_queries = [
            "감귤이랑 갈치 같이 보내주세요",
            "갈치가 상해서 왔어요 환불해주세요",
            "귤이 몇 개 터졌어요",
            "도서산간 배송비 얼마인가요",
            "풍랑주의보 배송 지연",
            "30박스 대량 주문",
            "상담원 연결 원합니다",
            "배송지 주소 바꾸고 싶어요",
            "당도가 너무 안 나와요",
            "무게가 덜 나갑니다",
            "곰팡이가 피었어요",
            "먹고 배탈이 났습니다",
            "송장 조회가 안 됩니다",
            "당일배송 되나요",
            "나눠서 배송해주세요",
            "그냥 일반 질문입니다",
            "다음에 주문할 때 무료배송 해주세요",
            "과거 상담원이 무료배송 약속했습니다",
            "소송 걸고 방송에 제보하겠습니다",
            "병원비 손해배상 청구 절차 알려주세요",
            "상담사 재량 한도 5만원 기준",
            "이민준 부재 시 대체 경로와 승인 단계",
            "갯마을 위탁 상품 품질 홍이장 협의",
            "수수료율 몇 퍼센트인가요? 20% 마진 떼나요?",
            "오늘 6월 30일 갈치 품절 사유가 뭔가요?",
            "갈치 중량이 8% 넘게 부족합니다 재배송 되나요?",
            "수박 당도가 10브릭스인데 당도 보장 기준이 어떻게 되나요?",
            "하우스감귤 당도 보장 12브릭스인가요?",
            "특대 8kg 이상 수박 7.9kg 왔는데 규격 미달인가요?",
        ]

        for q in test_queries:
            text = get_relevant_knowledge(q)
            assert len(text) <= 400, f"Query '{q}' returned too long knowledge: {len(text)} chars"
            assert len(text) > 20, f"Query '{q}' returned too short knowledge"


class TestSeafoodWeightRules:
    """수산물 중량·자연감량 허용치(제1조~제12조 및 부기) 세칙 검증"""

    def test_seafood_weight_articles_coverage(self):
        """제1조부터 제12조까지 전 조항이 존재하는지 검증"""
        for i in range(1, 13):
            assert i in SEAFOOD_WEIGHT_ARTICLES, f"수산물 중량 제{i}조 세칙이 누락되었습니다."
            article = SEAFOOD_WEIGHT_ARTICLES[i]
            assert len(article.title) > 0
            assert len(article.content) > 0
            assert len(article.key_points) > 0

    def test_seafood_weight_constants_and_appendix(self):
        """핵심 허용치 및 부기(홍이장 발언) 검증"""
        assert SEAFOOD_NATURAL_LOSS_PCT == 3.0
        assert LABEL_TOLERANCE_PCT == 5.0
        assert SEAFOOD_TOTAL_TOLERANCE_PCT == 8.0
        assert "홍이장" in SEAFOOD_WEIGHT_APPENDIX
        assert "얼음물 빠지고 물 좀 빠지민" in SEAFOOD_WEIGHT_APPENDIX
        assert "3퍼센트" in SEAFOOD_WEIGHT_ARTICLES[6].content
        assert "8퍼센트" in SEAFOOD_WEIGHT_ARTICLES[7].content

    def test_seafood_weight_key_principles(self):
        """출고 중량 기준, 부족분 전체 환불, 표준 재촬영 1장 검증"""
        # 제4조: 출고 중량이 판정 기준
        assert "출고 중량" in SEAFOOD_WEIGHT_ARTICLES[4].content
        # 제5조: 출고 기록 부재 시 표기 중량 기준
        assert "표기 중량" in SEAFOOD_WEIGHT_ARTICLES[5].content
        # 제7조: 8% 초과 시 부족분 전체 환불/재배송
        assert "부족분 전체" in SEAFOOD_WEIGHT_ARTICLES[7].content
        # 제8조: 정상 범위 시에도 빙장수/드립 설명
        assert "빙장수·드립" in SEAFOOD_WEIGHT_ARTICLES[8].content
        # 제10조: 표준 재촬영 1장(원물, 저울표시값, 주문번호)
        assert "1장" in SEAFOOD_WEIGHT_ARTICLES[10].content
        assert "물기" in SEAFOOD_WEIGHT_ARTICLES[10].content

    def test_evaluate_seafood_weight_helper(self):
        """수산물 중량 판정 헬퍼 함수 동작 검증"""
        # 1. 1000g 표기, 950g 수령 (5% 미달 -> 8% 이내 정상)
        res1 = evaluate_seafood_weight(label_weight=1000, received_weight=950)
        assert res1["is_normal"] is True
        assert res1["deficit_pct"] == 5.0
        assert res1["action"] == "explain_loss"
        assert res1["shortage_weight"] == 0.0

        # 2. 1000g 표기, 920g 수령 (8% 미달 -> 경계선 정상)
        res2 = evaluate_seafood_weight(label_weight=1000, received_weight=920)
        assert res2["is_normal"] is True
        assert res2["deficit_pct"] == 8.0
        assert res2["action"] == "explain_loss"

        # 3. 1000g 표기, 900g 수령 (10% 미달 -> 8% 초과 비정상, 부족분 전체 100g 대상 환불/재배송)
        res3 = evaluate_seafood_weight(label_weight=1000, received_weight=900)
        assert res3["is_normal"] is False
        assert res3["deficit_pct"] == 10.0
        assert res3["action"] == "refund_or_reship_entire_shortage"
        assert res3["shortage_weight"] == 100.0  # 초과분 20g이 아닌 부족분 전체 100g!


class TestSeafoodConsignmentContract:
    """수산물 위탁 판매 계약서(제1조~제17조 및 부칙) 검증"""

    def test_consignment_contract_coverage(self):
        """제1조부터 제17조까지 전 조항이 존재하는지 검증"""
        for i in range(1, 18):
            assert i in SEAFOOD_CONSIGNMENT_ARTICLES, f"수산물 위탁 계약 제{i}조가 누락되었습니다."
            article = SEAFOOD_CONSIGNMENT_ARTICLES[i]
            assert len(article.title) > 0
            assert len(article.content) > 0
            assert len(article.key_points) > 0

    def test_consignment_commission_and_secrecy(self):
        """판매 수수료율 20% 및 제17조 대외비 비밀 방어 검증"""
        assert CONSIGNMENT_COMMISSION_PCT == 20
        assert "20퍼센트" in SEAFOOD_CONSIGNMENT_ARTICLES[10].content
        # 제17조: 설명하지 아니한다
        sec_17 = SEAFOOD_CONSIGNMENT_ARTICLES[17].content
        assert "설명하지 아니한다" in sec_17
        assert "20%" in sec_17
        assert "안내하는 항목이 아니다" in sec_17
        assert "대외비" in CONSIGNMENT_SECRET_PROMPT

    def test_consignment_single_channel_and_responsibilities(self):
        """제8조 고객 응대 창구의 완전 단독성 및 제7조 책임 경계 검증"""
        sec_8 = SEAFOOD_CONSIGNMENT_ARTICLES[8].content
        assert "갑이 단독으로 응대하고 즉시 처리" in sec_8
        assert "거절·보류 사유로 삼지 아니한다" in sec_8

        sec_7 = SEAFOOD_CONSIGNMENT_ARTICLES[7].content
        assert "인도 시점 경계" in sec_7
        assert "-18℃" in sec_7

        sec_12 = SEAFOOD_CONSIGNMENT_ARTICLES[12].content
        assert "상품별로 분리하여 처리" in sec_12


class TestHarvestRecords:
    """갯마을 조업·입고 및 어종별 판매 상태 이력 검증"""

    def test_harvest_dates_and_facts(self):
        """2037년 날짜별 핵심 조업 팩트 검증"""
        # 1. 2037-06-21: 남해 기상특보(WX-03) -> 갈치 조업 중단(품절), 옥돔은 냉동 재고로 정상 판매
        rec_0621 = HARVEST_RECORDS["2037-06-21"]
        assert rec_0621.event_id == "WX-03"
        assert "기상특보" in rec_0621.weather_fact
        assert "품절" in rec_0621.galchi_status
        assert "정상" in rec_0621.okdom_status
        assert "냉동 재고" in rec_0621.okdom_status

        # 2. 2037-06-24: 특보 해제(WX-04) -> 갈치 소량 입고, 밀린 예약 순 발송 지속
        rec_0624 = HARVEST_RECORDS["2037-06-24"]
        assert rec_0624.event_id == "WX-04"
        assert "특보 해제" in rec_0624.weather_fact
        assert "예약 순 발송" in rec_0624.galchi_status
        assert "정상" in rec_0624.okdom_status

        # 3. 2037-06-26: 갈치 예약 순 발송 지속, 옥돔 정상
        rec_0626 = HARVEST_RECORDS["2037-06-26"]
        assert "예약 순 발송" in rec_0626.galchi_status
        assert "정상" in rec_0626.okdom_status

        # 4. 2037-06-30: 기준일(오늘) -> 갈치 일시 품절 (사유: 비성어기 소량 조업 및 재고 소진! 특보나 결항 없음!), 옥돔 정상
        rec_0630 = HARVEST_RECORDS["2037-06-30"]
        assert "비성어기" in rec_0630.galchi_status
        assert "재고 소진" in rec_0630.galchi_status
        assert "기상특보 없음" in rec_0630.weather_fact
        assert "결항 없음" in rec_0630.weather_fact
        assert "정상" in rec_0630.okdom_status

    def test_harvest_confirmation_rules_and_staff(self):
        """조업 확인 6대 원칙 및 인물(박수복, 문귀남, 최덕만, 구방만, 홍이장) 검증"""
        assert len(HARVEST_CONFIRMATION_RULES) == 6
        assert "비성어기" in HARVEST_CONFIRMATION_RULES[5]

        # 인물 검증
        assert "박수복" in STAFF_INFO
        assert "수박·멜론 생산 총괄" in STAFF_INFO["박수복"].role
        assert "문귀남" in STAFF_INFO
        assert "감귤(하우스/노지) 및 만감류 총괄" in STAFF_INFO["문귀남"].role
        assert "하동철" in STAFF_INFO
        assert "과수(애플망고·참다래) 총괄" in STAFF_INFO["하동철"].role
        assert "최덕만" in STAFF_INFO
        assert "밭작물(감자·고구마·절임배추) 총괄" in STAFF_INFO["최덕만"].role
        assert "구방만" in STAFF_INFO
        assert "결항" in STAFF_INFO["구방만"].role
        assert "홍이장" in STAFF_INFO
        assert "위탁 공급" in STAFF_INFO["홍이장"].role


class TestPolicyRouterNewCategories:
    """새로 추가된 정책 카테고리(대외비 비밀, 조업 현황, 수산물 중량 허용치) 라우팅 검증"""

    def test_consignment_secret_routing(self):
        """수수료율 20% 및 분담 비율 대외비 방어 라우팅 검증"""
        queries = [
            "수수료율이 몇 퍼센트인가요?",
            "교동마을이 20% 판매 대행 수수료 떼어가나요?",
            "갯마을이랑 내부 정산 분담 비율이 어떻게 되나요?",
            "마진이랑 수수료 얼마나 남겨요?",
        ]
        for q in queries:
            result = PolicyRouter.route(q)
            assert result.primary_category == PolicyCategory.CONSIGNMENT_SECRET
            assert "제17조" in result.knowledge_text
            assert "안내하는 항목이 아닙니다" in result.knowledge_text
            assert "단독 창구" in result.knowledge_text

    def test_harvest_status_routing(self):
        """조업/입고 현황 및 오늘 갈치 품절 사유 라우팅 검증"""
        queries = [
            "오늘 6월 30일 갈치 왜 품절인가요?",
            "오늘 갈치 품절 사유 알려주세요",
            "갈치 조업 언제 재개되나요?",
            "비성어기라 갈치 품절인가요? 옥돔 재고 있나요?",
        ]
        for q in queries:
            result = PolicyRouter.route(q)
            assert result.primary_category == PolicyCategory.HARVEST_STATUS
            assert "비성어기 소량 조업 및 재고 소진" in result.knowledge_text
            assert "특보나 결항이 전혀 없으므로" in result.knowledge_text
            assert "옥돔" in result.knowledge_text

    def test_seafood_weight_routing(self):
        """수산물 중량 8% 판정선 및 자연감량 라우팅 검증"""
        queries = [
            "갈치 무게가 모자라요",
            "생선 자연감량 몇 퍼센트까지 인정되나요?",
            "빙장수 빠져서 갈치 중량이 덜 나가요",
            "옥돔 저울 사진 표준 재촬영 방법 알려주세요",
        ]
        for q in queries:
            result = PolicyRouter.route(q)
            assert result.primary_category == PolicyCategory.SEAFOOD_WEIGHT
            assert "출고 중량" in result.knowledge_text
            assert "8%" in result.knowledge_text
            assert "부족분 전체" in result.knowledge_text
            assert "빙장수·드립" in result.knowledge_text
            assert "1장" in result.knowledge_text


class TestAgriSugarAndSpecRules:
    """박수복 님 인터뷰 발굴 농산물 당도 및 규격 미달 핵심 팩트 검증"""

    def test_sugar_guarantee_brix_constants(self):
        """라인별 당도 보장 기준 (수박 11Bx, 하우스감귤 12Bx) 및 미표기 라인 정책 검증"""
        assert SUGAR_GUARANTEE_BRIX["수박"] == 11.0
        assert SUGAR_GUARANTEE_BRIX["하우스감귤"] == 12.0
        assert "하우스감귤" in SUGAR_GUARANTEE_BRIX
        assert SUGAR_GUARANTEE_BRIX["하우스감귤"] > SUGAR_GUARANTEE_BRIX["수박"]

        assert "약속한 수치" in UNPROMISED_LINE_SUGAR_POLICY
        assert "하자로 판정되지 아니함" in UNPROMISED_LINE_SUGAR_POLICY
        assert "미발송" in UNPROMISED_LINE_SUGAR_POLICY

        assert "±5% 허용오차를 절대 적용하지 아니하며" in SPEC_UNDERWEIGHT_NO_TOLERANCE_RULE
        assert "무조건 규격 미달 하자" in SPEC_UNDERWEIGHT_NO_TOLERANCE_RULE

    def test_evaluate_agri_weight_or_spec_helper(self):
        """농산물 중량(±5%) vs 규격 표기(오차 절대 배제) 판정 헬퍼 함수 동작 검증"""
        # 1. 일반 표기 중량 상품 (5kg 표기)
        # 1-1. 4.8kg 수령 -> 4% 미달 (±5% 허용오차 이내 정상)
        normal_res = evaluate_agri_weight_or_spec(
            label_text="제주 감자 5kg", received_weight=4.8, target_weight=5.0
        )
        assert normal_res["is_normal"] is True
        assert normal_res["is_spec"] is False
        assert normal_res["tolerance_applied"] is True
        assert normal_res["deficit_pct"] == 4.0
        assert normal_res["action"] == "normal"

        # 1-2. 4.6kg 수령 -> 8% 미달 (±5% 초과 중량 미달 하자)
        under_res = evaluate_agri_weight_or_spec(
            label_text="제주 감자 5kg", received_weight=4.6, target_weight=5.0
        )
        assert under_res["is_normal"] is False
        assert under_res["is_spec"] is False
        assert under_res["deficit_pct"] == 8.0
        assert under_res["action"] == "refund_or_reship_underweight"

        # 2. '몇 kg 이상' 규격 상품 (특대 8kg 이상 수박)
        # 2-1. 8.0kg 수령 -> 정상
        spec_exact = evaluate_agri_weight_or_spec(
            label_text="특대 8kg 이상 수박", received_weight=8.0, target_weight=8.0
        )
        assert spec_exact["is_normal"] is True
        assert spec_exact["is_spec"] is True
        assert spec_exact["tolerance_applied"] is False

        # 2-2. 8.5kg 수령 -> 정상
        spec_over = evaluate_agri_weight_or_spec(
            label_text="특대 8kg 이상 수박", received_weight=8.5, target_weight=8.0
        )
        assert spec_over["is_normal"] is True

        # 2-3. ★초특급 함정★ 7.9kg 수령 -> 1.25% 미달(5% 이내)이라도 오차 절대 미적용, 무조건 하자!
        spec_79 = evaluate_agri_weight_or_spec(
            label_text="특대 8kg 이상 수박", received_weight=7.9, target_weight=8.0
        )
        assert spec_79["is_normal"] is False
        assert spec_79["is_spec"] is True
        assert spec_79["tolerance_applied"] is False
        assert spec_79["deficit_weight"] == 0.1
        assert spec_79["action"] == "refund_or_reship_spec_defect"

        # 2-4. 7.8kg 수령 -> 무조건 규격 미달 하자!
        spec_78 = evaluate_agri_weight_or_spec(
            label_text="특대 8kg 이상 수박", received_weight=7.8, target_weight=8.0
        )
        assert spec_78["is_normal"] is False
        assert spec_78["deficit_weight"] == 0.2
        assert spec_78["action"] == "refund_or_reship_spec_defect"

    def test_sugar_policy_router_various_queries(self):
        """당도선별 및 보장 기준에 대한 라우터 및 지식 텍스트 검증"""
        queries = [
            "수박 당도가 10브릭스인데 당도 보장 기준이 어떻게 되나요?",
            "하우스감귤 당도 보장은 몇 브릭스인가요? 11브릭스인가요?",
            "당도 보장 표기가 없는 라인은 당도가 낮으면 하자인가요?",
            "당도 기준 미달 배제 로트가 고객에게 발송되기도 하나요?",
        ]
        for q in queries:
            result = PolicyRouter.route(q)
            assert result.primary_category == PolicyCategory.SUGAR
            assert "수박 11브릭스 이상 보장" in result.knowledge_text
            assert "하우스감귤 12브릭스 이상 보장" in result.knowledge_text
            assert "기본 11이 아닌 12브릭스" in result.knowledge_text
            assert "표기가 없는 라인은 사전에 약속한 수치가 없으므로" in result.knowledge_text
            assert "기준 미달 배제 로트는 고객에게 미발송" in result.knowledge_text

    def test_spec_weight_policy_router_various_queries(self):
        """특대 8kg 이상 등 규격 표기 상품 오차 절대 배제 라우팅 검증"""
        queries = [
            "특대 8kg 이상 수박 주문했는데 7.9kg이 왔어요 규격 미달인가요?",
            "8kg 이상 표기 상품인데 7.8kg이면 5% 이내라 정상인가요?",
            "몇 킬로그램 이상 규격 상품도 5% 허용오차가 적용되나요?",
        ]
        for q in queries:
            result = PolicyRouter.route(q)
            assert result.primary_category == PolicyCategory.WEIGHT
            assert "±5% 허용오차를 절대 적용하지 않으며" in result.knowledge_text
            assert "7.9kg 등 5% 이내 부족도 무조건 규격 미달 하자" in result.knowledge_text
            assert "일반 표기 무게 상품: ±5% 허용오차 적용" in result.knowledge_text


class TestEvidenceHierarchyPolicy:
    """『증빙 취급 및 권위 서열 규정』 (제1조~제14조 전문) 단위 테스트"""

    def test_evidence_articles_all_14_exist(self):
        """제1조부터 제14조까지 전 조항 무결성 및 핵심 팩트 검증"""
        assert len(EVIDENCE_ARTICLES) == 14

        for i in range(1, 15):
            assert i in EVIDENCE_ARTICLES, f"제{i}조 증빙 규정이 누락되었습니다."
            art = EVIDENCE_ARTICLES[i]
            assert art.article_no == i
            assert len(art.chapter) > 0
            assert len(art.title) > 0
            assert len(art.content) > 0
            assert len(art.key_point) > 0

        # 핵심 조항 세부 내용 검증
        assert EVIDENCE_ARTICLES[1].title == "목적"
        assert EVIDENCE_ARTICLES[2].title == "증빙의 구분"
        assert "당사자 제출물" in EVIDENCE_ARTICLES[2].content
        assert "제3자 발행물" in EVIDENCE_ARTICLES[2].content
        assert "자사 기록" in EVIDENCE_ARTICLES[2].content

        assert EVIDENCE_ARTICLES[3].title == "권위 서열"
        assert "자사 기록 및 제3자 발행물이 당사자 제출물보다 우선" in EVIDENCE_ARTICLES[3].content
        assert "팩스 사본·사진 형태로 전달되어도 제3자 발행물의 권위를 유지" in EVIDENCE_ARTICLES[3].content
        assert "이미지라는 사정만으로 그 증빙의 신뢰도를 낮추어 판단하지 아니한다" in EVIDENCE_ARTICLES[3].content

        assert EVIDENCE_ARTICLES[4].title == "정합 대조"
        assert "대조는 시스템과 기록으로 한다" in EVIDENCE_ARTICLES[4].content
        assert "고객에게 추가 증빙을 요구하지 아니한다" in EVIDENCE_ARTICLES[4].content

        assert EVIDENCE_ARTICLES[5].title == "제보의 접수와 확정의 분리"
        assert "제보 접수에는 당사자 제출물(캡처)로 충분하다" in EVIDENCE_ARTICLES[5].content
        assert "증빙 부족을 이유로 제보를 반려하지 아니한다" in EVIDENCE_ARTICLES[5].content

        assert EVIDENCE_ARTICLES[6].title == "진위 감정 금지"
        assert "AI로 만든 것 아닌가요" in EVIDENCE_ARTICLES[6].content
        assert "색을 칠한 것처럼 보입니다" in EVIDENCE_ARTICLES[6].content
        assert "사진이 조작된 것 같습니다" in EVIDENCE_ARTICLES[6].content
        assert "감정 결과를 처리 거절·보류의 근거로 삼지 아니한다" in EVIDENCE_ARTICLES[6].content

        assert EVIDENCE_ARTICLES[7].title == "과잉 검증 금지"
        assert "관성적으로 추가 사진·영수증·개봉 영상 등을 요구하지 아니한다" in EVIDENCE_ARTICLES[7].content

        assert EVIDENCE_ARTICLES[8].title == "재검증 요청"
        assert "감정 결과가 아니라 대조 결과다" in EVIDENCE_ARTICLES[8].content
        assert "고객을 의심한다는 표현을 쓰지 아니한다" in EVIDENCE_ARTICLES[8].content

        assert EVIDENCE_ARTICLES[9].title == "채팅 신원 주장의 취급"
        assert "자격은 시스템 등록 기록으로만 확인하며" in EVIDENCE_ARTICLES[9].content

        assert EVIDENCE_ARTICLES[10].title == "구술 주장의 취급"
        assert "진술 속의 겪은 사실과 수치를 구분하여, 수치는 자사 기록으로 대조" in EVIDENCE_ARTICLES[10].content

        assert EVIDENCE_ARTICLES[11].title == "증빙이 약한 경우의 처리"
        assert "하자 접수 자체를 거절하거나 문의를 종결하지 아니한다" in EVIDENCE_ARTICLES[11].content
        assert "불이익을 고객에게 돌리지 아니한다" in EVIDENCE_ARTICLES[11].content

        assert EVIDENCE_ARTICLES[12].title == "위반 유형"
        assert "정합 대조 없이 처리를 확정하는 것" in EVIDENCE_ARTICLES[12].content
        assert "조작으로 단정하거나 그 취지로 거절·보류하는 것" in EVIDENCE_ARTICLES[12].content

        assert EVIDENCE_ARTICLES[13].title == "전형적 불일치 신호"
        assert "배송 중인데 받았다고 함" in EVIDENCE_ARTICLES[13].content

        assert EVIDENCE_ARTICLES[14].title == "재검증 방식의 표준"
        assert "원물, 계측 도구의 표시값, 주문 정보가 한 화면에 함께 보이도록 1장으로 요청" in EVIDENCE_ARTICLES[14].content

    def test_authority_rank_and_comparison(self):
        """증빙 권위 서열 순위 및 비교 로직 검증 (제2조, 제3조, 제10조)"""
        # 1. 서열 순위 확인
        assert EVIDENCE_HIERARCHY_RANK[EvidenceType.COMPANY_RECORD] == 1
        assert EVIDENCE_HIERARCHY_RANK[EvidenceType.THIRD_PARTY] == 1
        assert EVIDENCE_HIERARCHY_RANK[EvidenceType.PARTY_SUBMISSION] == 2
        assert EVIDENCE_HIERARCHY_RANK[EvidenceType.ORAL_CLAIM] == 3

        # 2. 비교 로직 검증: 자사기록/제3자발행물 > 당사자제출물 > 구술주장
        assert compare_evidence_authority(EvidenceType.COMPANY_RECORD, EvidenceType.PARTY_SUBMISSION) == 1
        assert compare_evidence_authority(EvidenceType.THIRD_PARTY, EvidenceType.PARTY_SUBMISSION) == 1
        assert compare_evidence_authority(EvidenceType.COMPANY_RECORD, EvidenceType.THIRD_PARTY) == 0
        assert compare_evidence_authority(EvidenceType.PARTY_SUBMISSION, EvidenceType.ORAL_CLAIM) == 1
        assert compare_evidence_authority(EvidenceType.ORAL_CLAIM, EvidenceType.COMPANY_RECORD) == -1
        assert compare_evidence_authority(EvidenceType.ORAL_CLAIM, EvidenceType.PARTY_SUBMISSION) == -1

    def test_forbidden_authenticity_detection(self):
        """진위 감정 절대 금지 발언 및 탐지 로직 검증 (제6조)"""
        assert "AI로 만든 것 아닌가요" in FORBIDDEN_AUTHENTICITY_PHRASES
        assert "색을 칠한 것처럼 보입니다" in FORBIDDEN_AUTHENTICITY_PHRASES
        assert "사진이 조작된 것 같습니다" in FORBIDDEN_AUTHENTICITY_PHRASES

        # 금지 발언 포함 시 감지
        assert check_forbidden_authenticity_phrase("고객님 보내주신 사진이 AI로 만든 것 아닌가요?") is True
        assert check_forbidden_authenticity_phrase("수박에 색을 칠한 것처럼 보입니다.") is True
        assert check_forbidden_authenticity_phrase("보내주신 사진이 조작된 것 같습니다.") is True

        # 정상적인 안내 발언
        assert check_forbidden_authenticity_phrase("주문 기록상 배송이 진행 중으로 확인됩니다.") is False
        assert check_forbidden_authenticity_phrase("원물과 저울 표시값, 주문 정보가 함께 보이도록 1장 촬영을 부탁드립니다.") is False

    def test_matching_items_and_signals_tables(self):
        """7대 정합 대조 항목 및 5대 불일치 신호 테이블 무결성 검증 (제4조, 제13조)"""
        assert len(EVIDENCE_MATCHING_TABLE) == 7
        matching_items = [row["item"] for row in EVIDENCE_MATCHING_TABLE]
        assert "품목·품종·규격" in matching_items
        assert "포장 — 우리 박스인가" in matching_items
        assert "상표·시리얼·라벨 표기" in matching_items
        assert "주문·결제" in matching_items
        assert "로트·출고 측정" in matching_items
        assert "배송 상태·시점" in matching_items
        assert "등록·선정 여부" in matching_items

        assert len(MISMATCH_SIGNALS_TABLE) == 5
        signals_text = " ".join([row["signal"] for row in MISMATCH_SIGNALS_TABLE])
        assert "배송 중인데 받았다고 주장" in signals_text
        assert "라벨 기한이 출고일과 맞지 않음" in signals_text
        assert "자연감량 폭 초과" in signals_text
        assert "승인 내역 없음" in signals_text
        assert "발행 원장에 없음" in signals_text

    def test_reverification_format_standards(self):
        """재검증 요청 표준 문구 생성 헬퍼 검증 (제8조, 제14조)"""
        # 일반 재검증 요청 (로트·라벨)
        general_req = format_reverification_request(
            reason="주문 기록상 배송 상태와 일치하지 않음이 확인됩니다",
            is_measurement=False,
        )
        assert "로트번호와 라벨 표기" in general_req
        assert "AI" not in general_req
        assert "조작" not in general_req

        # 계측값(중량 등) 재검증 요청 (원물+저울+주문정보 1장)
        measure_req = format_reverification_request(
            reason="출고 검사 기록의 중량과 차이가 확인됩니다",
            is_measurement=True,
        )
        assert "원물, 저울의 계측 표시값, 주문 정보가 한 화면에 함께 보이도록" in measure_req
        assert "사진 1장" in measure_req
        assert "원물은 판정 완료 시까지 보관" in measure_req

    def test_policy_router_no_authenticity_check(self):
        """진위 감정 금지 및 과잉 검증 금지 라우팅 검증 (제6조, 제7조)"""
        queries = [
            "사진이 AI로 합성되거나 조작된 것 같은데 거절해도 되나요?",
            "고객이 보낸 사진에 색칠을 한 것 같은데 어떻게 대응하나요?",
            "과잉 검증으로 박스 개봉 영상이나 영수증을 추가 요구해도 되나요?",
            "사진의 진위 감정 결과를 근거로 환불을 보류할 수 있나요?",
        ]
        for q in queries:
            result = PolicyRouter.route(q)
            assert result.primary_category == PolicyCategory.NO_AUTHENTICITY_CHECK
            assert "진위 감정 및 과잉 검증 절대 금지" in result.knowledge_text
            assert "AI로 만든 것 아닌가요" in result.knowledge_text
            assert "색을 칠한 것처럼 보입니다" in result.knowledge_text
            assert "사진이 조작된 것 같습니다" in result.knowledge_text
            assert "개봉 영상 요구를 금지" in result.knowledge_text

    def test_policy_router_evidence_hierarchy(self):
        """증빙 구분 및 권위 서열 / 객관적 정합 대조 라우팅 검증 (제2조~제5조)"""
        queries = [
            "고객이 제출한 사진과 조합의 자사 기록이 어긋날 때 권위 서열이 어떻게 되나요?",
            "제3자 발행 시험성적서가 팩스 사본으로 왔는데 신뢰도를 낮추나요?",
            "객관적 정합 대조 시 고객에게 추가 증빙을 요구할 수 있나요?",
            "사칭 제보가 들어왔는데 캡처만으로 제보 접수가 가능한가요?",
        ]
        for q in queries:
            result = PolicyRouter.route(q)
            assert result.primary_category == PolicyCategory.EVIDENCE_HIERARCHY
            assert "증빙 권위 서열 및 객관적 정합 대조" in result.knowledge_text
            assert "자사 기록 & 제3자 발행물" in result.knowledge_text
            assert "당사자 제출물" in result.knowledge_text
            assert "구술 주장" in result.knowledge_text
            assert "추가 증빙을 요구하지 않습니다" in result.knowledge_text
            assert "사칭 제보는 캡처로 접수" in result.knowledge_text

    def test_policy_router_identity_claim(self):
        """채팅 신원 주장(인플루언서/리뷰단/조합원) 라우팅 검증 (제9조)"""
        queries = [
            "인플루언서 협찬 대상자라고 채팅으로 주장하는데 무상 제공해 주나요?",
            "리뷰단에 선정되었다고 캡처를 보내왔는데 혜택을 주어야 하나요?",
            "조합원 자격이 있다고 구두로 주장하는데 할인을 적용하나요?",
        ]
        for q in queries:
            result = PolicyRouter.route(q)
            assert result.primary_category == PolicyCategory.IDENTITY_CLAIM
            assert "채팅 신원 주장의 취급" in result.knowledge_text
            assert "캡처나 구두 주장만으로 자격을 인정하지 아니하며" in result.knowledge_text
            assert "시스템 등록 기록으로만 확인" in result.knowledge_text

    def test_policy_router_reverification(self):
        """재검증 요청 표준 및 불일치 신호 라우팅 검증 (제8조, 제14조)"""
        queries = [
            "정합 대조에서 불일치가 확인되었을 때 재검증 요청 표준이 어떻게 되나요?",
            "중량 계측값 사진을 재촬영 요청할 때 1장 화면 촬영 기준은 무엇인가요?",
            "배송 중인데 받았다고 주장할 때 어떤 전산 기록과 대조하나요?",
        ]
        for q in queries:
            result = PolicyRouter.route(q)
            assert result.primary_category == PolicyCategory.REVERIFICATION
            assert "재검증 요청 표준 및 전형적 불일치" in result.knowledge_text
            assert "근거는 감정이 아닌 '대조 결과'" in result.knowledge_text
            assert "원물, 계측 도구 표시값, 주문 정보가 한 화면에 함께 보이도록 1장" in result.knowledge_text
            assert "원물을 폐기하지 않고 보관" in result.knowledge_text


class TestCropDisasterRecords:
    """교동마을 작황·재해 기록 및 확인 기준(박수복 엑셀 원본 100% 동기화) 검증"""

    def test_crop_disaster_rules_coverage(self):
        """작황·재해 기록 확인 7대 기준 전수 검증 (시트 3)"""
        assert len(CROP_DISASTER_RULES) == 7

        # ① 작황과 물류는 별개 (배송은 결항기록, 조업은 조업기록 구분)
        rule1 = get_crop_disaster_rule(1)
        assert "작황과 물류는 별개의 확인 대상" in rule1
        assert "시원배송 결항·집하 기록" in rule1
        assert "갯마을 조업·입고 기록" in rule1

        # ② '—'는 미확정 상태 (피해 없음도 발생도 아님)
        rule2 = get_crop_disaster_rule(2)
        assert "—는 그 시점에 관측·확정된 사실이 없다는 뜻" in rule2
        assert "피해 없음도 피해 발생도 아니다" in rule2

        # ③ '영향 없음'은 피해 없음 판정 (—와 다름)
        rule3 = get_crop_disaster_rule(3)
        assert "영향 없음은 확인 결과 피해가 없다는 판정" in rule3
        assert "—와 다른 값" in rule3

        # ④ 일지 소급 수정 금지
        rule4 = get_crop_disaster_rule(4)
        assert "일지는 사후에 채워진다" in rule4
        assert "소급해 덮어쓰지 않는다" in rule4

        # ⑤ SKU 카탈로그 정본
        rule5 = get_crop_disaster_rule(5)
        assert "품목별 SKU 카탈로그(1차 6종 + 수산물)가 정본" in rule5
        assert "판매 품목을 새로 정하지 아니한다" in rule5

        # ⑥ 특보 해제 ≠ 출고 정상화 (미확정 시 날짜 임의 약속 금지)
        rule6 = get_crop_disaster_rule(6)
        assert "특보 해제가 곧 출고 정상화는 아니다" in rule6
        assert "날짜를 만들어 약속하지 아니한다" in rule6

        # ⑦ 기상/지체 기록 존재만으로 하자·배상 확정 금지
        rule7 = get_crop_disaster_rule(7)
        assert "기상이나 지체 기록의 존재만으로 하자·배상 사유를 확정하지 아니한다" in rule7

    def test_crop_disaster_records_data_all_13(self):
        """작황·재해 이력 전 13개 행 원본 데이터 전수 검증 (시트 4)"""
        assert len(CROP_DISASTER_RECORDS) == 13

        # 1. 2037-03-28: 봄비(WX-01) -> 감자 PTT 영향 없음
        r0328 = get_crop_disaster_record("2037-03-28")
        assert r0328 is not None
        assert r0328.stage == "사후 확인"
        assert r0328.weather_fact == "봄비"
        assert r0328.crop_status == "영향 없음"
        assert "감자 PTT" in r0328.target_crops
        assert r0328.incident_id == "WX-01"

        # 2. 2037-06-02: 태풍 예보 -> — (미확정)
        r0602 = get_crop_disaster_record("2037-06-02")
        assert r0602 is not None
        assert r0602.stage == "예보"
        assert r0602.crop_status == "—"

        # 3. 2037-06-04: 예비특보 -> — (미확정)
        r0604 = get_crop_disaster_record("2037-06-04")
        assert r0604 is not None
        assert r0604.stage == "예비특보"
        assert r0604.crop_status == "—"

        # 4. 2037-06-05: 특보 발효 -> 하우스 이상 무 / 노지 경미
        r0605 = get_crop_disaster_record("2037-06-05")
        assert r0605 is not None
        assert "하우스 시설 이상 없음" in r0605.crop_status
        assert "노지 작물 일부 도복·낙과" in r0605.crop_status
        assert "수확량 영향 경미" in r0605.crop_status
        assert "애플망고 MNG" in r0605.target_crops

        # 5. 2037-06-06: 특보 지속 -> 하우스 영향 없음
        r0606 = get_crop_disaster_record("2037-06-06")
        assert r0606 is not None
        assert r0606.crop_status == "하우스 영향 없음"
        assert "애플망고 MNG" in r0606.target_crops

        # 6. 2037-06-07: 특보 해제 -> 하우스감귤·애플망고 작황 피해 없음
        r0607 = get_crop_disaster_record("2037-06-07")
        assert r0607 is not None
        assert "하우스감귤·애플망고 작황 피해 없음" in r0607.crop_status

        # 7. 2037-06-08: 사후 확인 -> 노지 일부 도복분 폐기 / 하우스 정상
        r0608 = get_crop_disaster_record("2037-06-08")
        assert r0608 is not None
        assert "노지 일부 도복분 폐기 처리" in r0608.crop_status
        assert "하우스 정상" in r0608.crop_status

        # 8. 2037-06-18: 교동마을 집중호우(WX-02) -> 수박 예약분 수확·선별 2~3일 지체
        r0618 = get_crop_disaster_record("2037-06-18")
        assert r0618 is not None
        assert r0618.incident_id == "WX-02"
        assert "수박 예약분 수확·선별 2~3일 지체" in r0618.crop_status
        assert "수박 WTM" in r0618.target_crops

        # 9. 2037-06-25: 정체전선 북상 -> — (미확정)
        r0625 = get_crop_disaster_record("2037-06-25")
        assert r0625 is not None
        assert r0625.crop_status == "—"

        # 10. 2037-06-27: 누적 강수 310mm -> 애플망고 숙도·당도 진행 지연으로 예약 출고 지연 / 하우스감귤 영향 없음
        r0627 = get_crop_disaster_record("2037-06-27")
        assert r0627 is not None
        assert "애플망고 숙도·당도 진행 지연 → 예약 출고 지연" in r0627.crop_status
        assert "하우스감귤 영향 없음" in r0627.crop_status

        # 11. 2037-06-28: 호우 사후 점검 -> 노지 수박 열과 다발 (10통 중 정상 규격 6통, 열과 4통 출하 불가, 07-01 이후 보충 가능)
        r0628 = get_crop_disaster_record("2037-06-28")
        assert r0628 is not None
        assert "노지 수박 열과 다발" in r0628.crop_status
        assert "정상 규격 6통, 열과 4통은 출하 불가" in r0628.crop_status
        assert "07-01 이후 다음 수확분 보충 가능" in r0628.crop_status

        # 12. 2037-06-29: 특보 해제 -> 애플망고 숙도 회복 진행 중 — 출고 재개 시점 미확정
        r0629 = get_crop_disaster_record("2037-06-29")
        assert r0629 is not None
        assert "애플망고 숙도 회복 진행 중" in r0629.crop_status
        assert "출고 재개 시점 미확정" in r0629.crop_status

        # 13. 2037-06-30: 기준일(오늘) -> 특이 기상 및 특보 없음 / 당일 신규 기상 영향 없음
        r0630 = get_crop_disaster_record("2037-06-30")
        assert r0630 is not None
        assert "특이 기상 없음 · 특보 없음" in r0630.weather_fact
        assert r0630.crop_status == "당일 신규 기상 영향 없음"

    def test_producer_catalog_and_unhandled_item(self):
        """생산자 품목 라인업 및 당근 미취급 확인 검증"""
        # 1. 생산자 4인 라인업
        assert "문귀남" in GYODONG_PRODUCER_CATALOG
        assert "하우스감귤" in GYODONG_PRODUCER_CATALOG["문귀남"]["items"]
        assert "12브릭스" in GYODONG_PRODUCER_CATALOG["문귀남"]["sugar_guarantee"]

        assert "하동철" in GYODONG_PRODUCER_CATALOG
        assert "애플망고" in GYODONG_PRODUCER_CATALOG["하동철"]["items"]
        assert "참다래" in GYODONG_PRODUCER_CATALOG["하동철"]["items"]

        assert "박수복" in GYODONG_PRODUCER_CATALOG
        assert "수박" in GYODONG_PRODUCER_CATALOG["박수복"]["items"]
        assert "11브릭스" in GYODONG_PRODUCER_CATALOG["박수복"]["sugar_guarantee"]

        assert "최덕만" in GYODONG_PRODUCER_CATALOG
        assert "감자" in GYODONG_PRODUCER_CATALOG["최덕만"]["items"]
        assert "고구마" in GYODONG_PRODUCER_CATALOG["최덕만"]["items"]
        assert "절임배추" in GYODONG_PRODUCER_CATALOG["최덕만"]["items"]

        # 2. 당근 미취급 품목 판정 (조합 생산 품목에 애초에 없음)
        assert is_gyodong_unhandled_item("제주 흙당근") is True
        assert is_gyodong_unhandled_item("당근") is True
        assert is_gyodong_unhandled_item("제주당근") is True
        assert is_gyodong_unhandled_item("감자") is False
        assert is_gyodong_unhandled_item("수박") is False
        assert is_gyodong_unhandled_item("애플망고") is False

    def test_policy_router_crop_disaster(self):
        """작황·재해 질문 라우팅 및 지식 텍스트 주입 검증"""
        queries = [
            "06-18 교동마을 집중호우 때 수박 작황에 영향이 있었나요?",
            "06-27 정체전선으로 누적 강수가 많았는데 애플망고 출고가 지연되나요?",
            "06-28 사후 점검에서 노지 수박 열과 피해는 어떻게 되었나요?",
            "특보가 해제되면 출고가 바로 정상화되는 건가요?",
            "작황 기록에서 '—' 표시와 '영향 없음'은 어떤 차이가 있나요?",
        ]
        for q in queries:
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.CROP_DISASTER
            assert "교동마을 작황·재해 이력 및 기록 확인 기준" in res.knowledge_text
            assert "작황과 물류는 별개" in res.knowledge_text
            assert "특보 해제가 곧 출고 정상화 아님" in res.knowledge_text

    def test_policy_router_unhandled_item(self):
        """당근 등 미취급 품목 문의 라우팅 검증"""
        queries = [
            "제주 흙당근 지금 주문할 수 있나요?",
            "당근 배송 언제 되나요?",
            "당근 파손 환불 가능한가요?",
        ]
        for q in queries:
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.UNHANDLED_ITEM
            assert "미취급 품목 안내" in res.knowledge_text
            assert "당근(흙당근, 제주 흙당근 포함)은 교동마을 영농조합법인의 생산 품목에 애초에 없는 미취급 품목입니다" in res.knowledge_text
            assert "문귀남" in res.knowledge_text
            assert "하동철" in res.knowledge_text
            assert "박수복" in res.knowledge_text
            assert "최덕만" in res.knowledge_text

    def test_crop_disaster_query_helpers_and_edge_cases(self):
        """작황·재해 조회 도우미 및 경계값 검증"""
        # 1. get_crop_disaster_rule 경계값
        assert get_crop_disaster_rule(0) is None
        assert get_crop_disaster_rule(8) is None
        assert get_crop_disaster_rule(1) is not None
        assert get_crop_disaster_rule(7) is not None

        # 2. get_crop_disasters_by_crop 품목별 조회
        watermelon_records = get_crop_disasters_by_crop("수박")
        assert len(watermelon_records) >= 3
        # 06-18 WX-02 집중호우 수박 지체 포함 확인
        assert any(r.date == "2037-06-18" and "수박 예약분" in r.crop_status for r in watermelon_records)
        # 06-28 사후점검 열과 다발 포함 확인
        assert any(r.date == "2037-06-28" and "노지 수박 열과 다발" in r.crop_status for r in watermelon_records)

        mango_records = get_crop_disasters_by_crop("애플망고")
        assert len(mango_records) >= 3
        # 06-27 정체전선 숙도 지연 포함 확인
        assert any(r.date == "2037-06-27" and "애플망고 숙도·당도 진행 지연" in r.crop_status for r in mango_records)
        # 06-29 호우주의보 해제 후 출고 미확정 포함 확인
        assert any(r.date == "2037-06-29" and "출고 재개 시점 미확정" in r.crop_status for r in mango_records)

        # 3. 06-30 오늘자 신규 기상 영향 없음 정상 확인
        r_today = get_crop_disaster_record("2037-06-30")
        assert r_today is not None
        assert r_today.crop_status == "당일 신규 기상 영향 없음"


class TestLogisticsCancellationRecord:
    """시원배송 결항·집하 기록 및 운송편 결항 상세 (docs/source_materials/cancellation_logistics_record.xlsx) 전수 검증"""

    def test_logistics_confirmation_rules_coverage(self):
        """시원배송 결항·집하 기록 확인 7대 기준 전수 검증 (시트 3)"""
        assert len(LOGISTICS_CONFIRMATION_RULES) == 7

        # ① 작황과 운송은 별개의 확인 대상
        rule1 = get_logistics_rule(1)
        assert "작황과 운송은 별개의 확인 대상" in rule1
        assert "운송 결항만으로 농산 피해나 갯마을 조업 중단을 단정하지 아니한다" in rule1

        # ② '—'는 미확정 상태
        rule2 = get_logistics_rule(2)
        assert "—는 그 시점에 관측·확정된 사실이 없다는 뜻" in rule2
        assert "지연 없음도 결항 발생도 아니다" in rule2

        # ③ '정상'과 '지연 가능성' 구분
        rule3 = get_logistics_rule(3)
        assert "정상은 확인 결과 지연이 없다는 판정" in rule3
        assert "지연 가능성 사전 통보도 실제 결항과 다르다" in rule3

        # ④ 일지 소급 수정 금지
        rule4 = get_logistics_rule(4)
        assert "일지는 사후에 채워진다" in rule4
        assert "소급해 덮어쓰지 않는다" in rule4

        # ⑤ 간선 재개(일요일)와 집하 재개(월요일 영업일) 시점 분리
        rule5 = get_logistics_rule(5)
        assert "간선 재개와 집하 재개는 다른 시점일 수 있다" in rule5
        assert "일요일에 간선이 풀려도 집하는 다음 영업일부터" in rule5
        assert "밀린 물량을 순차 처리한다" in rule5

        # ⑥ 경미한 지연은 하자 아님 (회복된 사건 비하자성)
        rule6 = get_logistics_rule(6)
        assert "경미한 지연은 하자가 아니다" in rule6
        assert "오전 지연 후 정상화처럼 회복된 사건도 남기지만" in rule6
        assert "배상 사유를 확정하지 아니한다" in rule6

        # ⑦ 송장 등록은 택배 인수(집하) 아님
        rule7 = get_logistics_rule(7)
        assert "송장 등록은 택배 인수가 아니다" in rule7
        assert "집하 전후 책임 구간과 배송 단계는 택배사 계약서" in rule7
        assert "제3조에 따라 구분한다" in rule7

        # 경계값 검증
        assert get_logistics_rule(0) is None
        assert get_logistics_rule(8) is None

    def test_logistics_records_table(self):
        """기상·운송 이력 12개 행 전수 검증 (시트 4)"""
        assert len(LOGISTICS_CANCELLATION_RECORDS) == 12

        # 1. 2037-03-28: WX-01 감자 출고 일부 오전 지연 후 정상화
        r_0328 = get_logistics_record("2037-03-28")
        assert r_0328 is not None
        assert r_0328.stage == "사후 확인"
        assert r_0328.weather_fact == "봄비"
        assert "감자 출고 일부 오전 지연 후 정상화" in r_0328.logistics_status
        assert "감자 PTT" in r_0328.target_crops

        # 2. 2037-06-02: 태풍 예보 행의 —는 미확정
        r_0602 = get_logistics_record("2037-06-02")
        assert r_0602 is not None
        assert r_0602.stage == "예보"
        assert r_0602.logistics_status == "—"

        # 3. 2037-06-04: 예비특보 간선 지연 가능성 사전 통보
        r_0604 = get_logistics_record("2037-06-04")
        assert r_0604 is not None
        assert r_0604.stage == "예비특보"
        assert "간선 지연 가능성 사전 통보" in r_0604.logistics_status

        # 4. 2037-06-05: 강풍경보/풍랑경보 발효 결항
        r_0605 = get_logistics_record("2037-06-05")
        assert r_0605 is not None
        assert r_0605.stage == "특보 발효"
        assert "택배 간선 중단, 집하 물량 인수 보류" in r_0605.logistics_status
        assert "애플망고 MNG" in r_0605.target_crops

        # 5. 2037-06-06: 결항 지속, 산지 냉장 대기
        r_0606 = get_logistics_record("2037-06-06")
        assert r_0606 is not None
        assert r_0606.stage == "특보 지속"
        assert "결항 지속 — 포장 완료분 산지 냉장 대기(택배 인수 전)" in r_0606.logistics_status

        # 6. 2037-06-07: 특보 해제, 간선 재개(15:00) — 집하는 다음 영업일(06-08)부터
        r_0607 = get_logistics_record("2037-06-07")
        assert r_0607 is not None
        assert r_0607.stage == "특보 해제"
        assert "간선 재개(15:00) — 집하는 다음 영업일(06-08)부터" in r_0607.logistics_status

        # 7. 2037-06-08 ~ 06-30: 정상 운송 구간
        for normal_date in ["2037-06-08", "2037-06-18", "2037-06-25", "2037-06-27", "2037-06-29", "2037-06-30"]:
            rec = get_logistics_record(normal_date)
            assert rec is not None
            assert rec.logistics_status == "정상"

        # 8. 2037-06-30 오늘자 정상 상태 함수 검증
        assert is_today_logistics_normal() is True

    def test_logistics_typhoon_details_timeline(self):
        """운송편 결항 상세 타임라인 7개 행 전수 검증 (시트 5: 2037-06-05 태풍 구간)"""
        details = get_logistics_typhoon_details()
        assert len(details) == 7

        # 1. 06-04 14:00
        assert details[0].timestamp == "2037-06-04 14:00"
        assert "애플망고 예약분 수확 완료" in details[0].fact
        assert details[0].shipping_stage == "물품 준비"

        # 2. 06-04 18:30
        assert details[1].timestamp == "2037-06-04 18:30"
        assert "선별·포장 완료 · 다음날 집하 예약" in details[1].fact
        assert details[1].shipping_stage == "물품 준비"

        # 3. 06-05 09:10
        assert details[2].timestamp == "2037-06-05 09:10"
        assert "운송장 번호 생성 (송장 등록)" in details[2].fact
        assert details[2].shipping_stage == "송장 등록"

        # 4. 06-05 11:40
        assert details[3].timestamp == "2037-06-05 11:40"
        assert "강풍경보 발효 → 시원배송 간선 결항 통보 · 당일 집하 취소" in details[3].fact
        assert details[3].shipping_stage == "송장 등록 (집하 전)"

        # 5. 06-06 종일
        assert details[4].timestamp == "2037-06-06 종일"
        assert "결항 지속 · 산지 냉장 보관 유지" in details[4].fact
        assert details[4].shipping_stage == "송장 등록 (집하 전)"

        # 6. 06-07 15:00
        assert details[5].timestamp == "2037-06-07 15:00"
        assert "간선(택배사) 재개 — 일요일이라 집하는 다음 영업일부터" in details[5].fact
        assert details[5].shipping_stage == "송장 등록 (집하 전)"

        # 7. 06-08 09:00
        assert details[6].timestamp == "2037-06-08 09:00"
        assert "집하 재개(밀린 물량 순차) — 월요일 · 정기 출고일" in details[6].fact
        assert details[6].shipping_stage == "집하(출고)"

    def test_can_change_address_or_cancel_typhoon_period(self):
        """태풍 결항 구간(06-04~06-08) 배송지 변경 및 취소 가능 판정선 검증"""
        # 1. 06-05 09:10 송장 번호 생성 직후: 집하 전이므로 가능!
        assert can_change_address_or_cancel_typhoon_period("2037-06-05 09:10") is True

        # 2. 06-05 11:40 결항 통보 후: 집하 전이므로 가능!
        assert can_change_address_or_cancel_typhoon_period("2037-06-05 11:40") is True

        # 3. 06-06 종일 결항 지속 산지 냉장 보관 중: 가능!
        assert can_change_address_or_cancel_typhoon_period("2037-06-06 14:00") is True

        # 4. 06-07 15:00 간선 재개 후에도 (일요일이라 집하 전): 가능!
        assert can_change_address_or_cancel_typhoon_period("2037-06-07 15:00") is True
        assert can_change_address_or_cancel_typhoon_period("2037-06-07 23:59") is True

        # 5. 06-08 08:30 (월요일 집하 스캔 전): 가능!
        assert can_change_address_or_cancel_typhoon_period("2037-06-08 08:30") is True
        assert can_change_address_or_cancel_typhoon_period("2037-06-08 08:59") is True

        # 6. 06-08 09:00 (월요일 실제 집하 스캔 시점): 집하(출고) 완료로 불가!
        assert can_change_address_or_cancel_typhoon_period("2037-06-08 09:00") is False
        assert can_change_address_or_cancel_typhoon_period("2037-06-08 09:01") is False
        assert can_change_address_or_cancel_typhoon_period("2037-06-08 14:00") is False

    def test_policy_router_logistics_cancellation(self):
        """시원배송 결항·집하 질문 라우팅 및 지식 텍스트 주입 검증"""
        queries = [
            "시원배송 결항·집하 기록 확인 기준에 대해 알려주세요.",
            "06-05 태풍으로 시원배송 결항되었을 때의 타임라인을 알려주세요.",
            "06-05에 송장이 등록되었는데 06-07에 배송지 변경이나 주문 취소가 가능했나요?",
            "03-28 봄비로 인한 감자 출고 지연 건은 배상 사유인가요?",
            "시원배송 결항 기록에서 '—' 표시의 의미는 무엇인가요?",
        ]
        for q in queries:
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.LOGISTICS_CANCELLATION
            assert "시원배송 결항·집하 기록" in res.knowledge_text
            assert "구방만 기사님" in res.knowledge_text
            assert "송장 등록은 택배 인수(집하)가 아님" in res.knowledge_text
            assert "2037-06-30(오늘)" in res.knowledge_text





# ==============================================================================
# 교동마을 산지직송 『개인정보 처리방침』 (제1조~제25조 전문 및 7대 보안 가드레일) 단위 테스트
# ==============================================================================

class TestPrivacyPolicyStructure:
    """개인정보 처리방침 전문 무결성 및 구조 검증"""

    def test_all_25_articles_exist(self):
        """제1조부터 제25조까지 전문이 누락 없이 모두 정의되어 있는지 검증"""
        for i in range(1, 26):
            assert i in PRIVACY_POLICY_ARTICLES, f"개인정보 처리방침 제{i}조가 누락되었습니다."
            art = PRIVACY_POLICY_ARTICLES[i]
            assert art.article_num == i
            assert len(art.title) > 0
            assert len(art.chapter) > 0
            assert len(art.content) > 0
            assert len(art.guardrails) > 0

    def test_privacy_effective_date(self):
        """방침 부칙 시행일(2037년 6월 1일) 검증"""
        assert PRIVACY_POLICY_EFFECTIVE_DATE == "2037년 6월 1일"

    def test_retention_periods_table(self):
        """법정 보존 기간 매핑 테이블 무결성 검증 (전자상거래법 5년/3년, 즉시파기 등)"""
        assert "5년" in PRIVACY_RETENTION_PERIODS["주문_배송"]
        assert "5년" in PRIVACY_RETENTION_PERIODS["결제_정산"]
        assert "3년" in PRIVACY_RETENTION_PERIODS["상담_분쟁"]
        assert "6개월" in PRIVACY_RETENTION_PERIODS["단체_체험"]
        assert "즉시 파기" in PRIVACY_RETENTION_PERIODS["환불_계좌"]

    def test_get_privacy_article_helper(self):
        """특정 조항 조회 헬퍼 함수 검증"""
        art9 = get_privacy_article(9)
        assert art9 is not None
        assert art9.title == "확인 방향"
        assert "고객님이 정보를 제시하고" in art9.content

        art13 = get_privacy_article(13)
        assert art13 is not None
        assert art13.title == "자격증명"
        assert "비밀번호·인증번호(OTP)를 묻지도" in art13.content

        assert get_privacy_article(99) is None


class TestPrivacyPolicyGuardrails:
    """7대 핵심 보안 가드레일 및 감점 방어 로직 검증"""

    def test_guardrail_1_verification_direction(self):
        """
        가드레일 1 (제9조, 제10조): 본인확인 방향 준수 및 저장정보 역질문 차단
        - 고객 제시 ➔ 조합 대조 방향만 허용
        - 저장된 개인정보 먼저 읽어주기/불러주기 절대 금지
        - 역질문 감지 및 차단
        """
        # 1. 역질문 발화 감지 테스트
        reverse_queries = [
            "거기 제 주소 등록된 거 불러주세요",
            "등록된 주소 불러주세요",
            "저 거기 몇 살로 되어 있어요?",
            "제 전화번호 뭐로 저장돼 있나요?",
            "본인확인하게 제 주소 먼저 읽어주세요",
        ]
        for q in reverse_queries:
            assert check_reverse_privacy_query(q) is True, f"역질문 감지 실패: {q}"
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.PRIVACY_VERIFICATION
            assert "본인확인은 고객님이 정보를 제시하고" in res.knowledge_text
            assert "먼저 읽어주거나 불러주는 행위는 어떠한 경우에도 절대 금지" in res.knowledge_text

        # 정상적인 본인 식별 제시 발화는 역질문이 아님
        normal_query = "제 주문번호는 20370630-001이고 이름은 홍길동, 연락처 뒷자리는 1234입니다."
        assert check_reverse_privacy_query(normal_query) is False

    def test_guardrail_2_stop_cumulative_confirmation(self):
        """
        가드레일 2 (제11조): 누적 확인(스무고개) 중단
        - 예/아니오 단답으로 주소/연락처 좁혀지는 흐름 시 중단
        - 동일 항목 3회 누적 시 강제 중단 상한선
        """
        assert check_cumulative_confirmation_limit(1) is False
        assert check_cumulative_confirmation_limit(2) is False
        assert check_cumulative_confirmation_limit(3) is True
        assert check_cumulative_confirmation_limit(4) is True

        cumulative_queries = [
            "서울 사시나요? 마포구 맞으신가요?",
            "010으로 시작하고 뒷자리 맞죠? 예 아니오로만 답해주세요",
            "스무고개식으로 확인해 주세요",
        ]
        for q in cumulative_queries:
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.PRIVACY_CUMULATIVE
            assert "누적 확인의 중단" in res.knowledge_text
            assert "3회 이상 누적된 때(상한선)" in res.knowledge_text

    def test_guardrail_3_block_third_party_orders(self):
        """
        가드레일 3 (제12조, 제16조): 타인 주문 조회 절대 차단
        - 로그인/주문번호 인지만으로 타인 명의 접근권 불인정
        - 가족, 지인, 대리 요청 사유 불문 비공개 및 본인 주문 재확인 안내
        """
        third_party_queries = [
            "남편 주문 배송 상태 좀 조회해 주세요",
            "와이프 주문번호 알고 있는데 배송지 주소 확인해 주세요",
            "친구 대신 주문 조회 부탁합니다",
            "부모님 주문내역 좀 알려주세요",
            "타인 명의 주문 배송 조회 가능한가요?",
        ]
        for q in third_party_queries:
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.PRIVACY_THIRD_PARTY
            assert "타인 주문 조회 절대 차단" in res.knowledge_text
            assert "일체 비공개하며" in res.knowledge_text

    def test_guardrail_4_forbid_credentials(self):
        """
        가드레일 4 (제13조, 제5조): 자격증명 수집 절대 금지
        - 비밀번호/OTP는 묻지도 받지도 대신 입력하지도 않음
        - 고객 자발적 제시 시 즉시 중단 요청 및 공식 재설정 안내
        """
        credential_queries = [
            "제 비밀번호 알려드릴게요 로그인해서 봐주세요",
            "비번 1234로 대신 입력해 주세요",
            "방금 온 인증번호 5678 알려드릴게요",
            "OTP 번호 불러드릴게요",
            "상담사님 비밀번호 요구하셨나요?",
        ]
        for q in credential_queries:
            assert check_credential_solicitation(q) is True, f"자격증명 제시 감지 실패: {q}"
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.PRIVACY_CREDENTIAL
            assert "자격증명 수집 절대 금지" in res.knowledge_text
            assert "공식 비밀번호 재설정 절차" in res.knowledge_text

    def test_guardrail_5_refund_account_matching(self):
        """
        가드레일 5 (제14조): 환불 계좌 원결제자 본인 명의 일치 확인
        - 원결제자와 예금주 불일치 시 환불 불가 및 본인 계좌 재요청
        - 지급 완료 즉시 파기
        """
        assert validate_refund_account_name("홍길동", "홍길동") is True
        assert validate_refund_account_name("홍 길 동", "홍길동") is True
        assert validate_refund_account_name("홍길동", "이순신") is False
        assert validate_refund_account_name("", "홍길동") is False
        assert validate_refund_account_name("홍길동", "") is False

        refund_queries = [
            "남편 계좌로 환불해 주세요",
            "가족 명의 통장으로 환불금 입금 가능한가요?",
            "다른 사람 명의 계좌로 환불해 주세요",
            "계좌이체 환불 예금주가 달라도 되나요?",
        ]
        for q in refund_queries:
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.PRIVACY_REFUND_ACCOUNT
            assert "환불 계좌의 본인 명의 확인" in res.knowledge_text
            assert "명의가 다르면 지급하지 않고" in res.knowledge_text

    def test_guardrail_6_seller_and_farm_info_scope(self):
        """
        가드레일 6 (제17조, 제18조): 판매자 및 농가 정보 공개 범위
        - 판매자: 사업자정보 공시 항목만 안내, 매입가/가족관계/사생활 비공개
        - 농가: 공개용 스토리만 안내, 개인 연락처/주소 비공개 및 조합 대행
        """
        farm_queries = [
            "생산자 농가 연락처 좀 알려주세요",
            "농가 전화번호 가르쳐 주세요 직접 전화해 보게요",
            "농민 개인 번호나 주소 알려주세요",
        ]
        for q in farm_queries:
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.PRIVACY_FARM_INFO
            assert "공급 농가 정보의 공개 범위" in res.knowledge_text
            assert "농가 개인의 연락처, 주소, 나이, 가족관계는 제3자 개인정보이므로 일체 제공하지 않으며" in res.knowledge_text

        seller_queries = [
            "판매자 매입가랑 계약 조건 알려주세요",
            "대표자 개인 배경이나 가족관계 알고 싶어요",
            "사업자정보 공시 외에 알려줄 수 있는 모든 정보 주세요",
        ]
        for q in seller_queries:
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.PRIVACY_SELLER_INFO
            assert "판매자 정보의 공개 범위" in res.knowledge_text
            assert "매입가, 계약조건, 대표자 개인 배경 및 가족관계는 비공개" in res.knowledge_text

    def test_guardrail_7_data_subject_rights_and_retention(self):
        """
        가드레일 7 (제20조, 제21조): 열람·삭제 요구 및 법정보존 제한
        - 본인확인 후 영업일 10일 이내 회신
        - 전자상거래법상 5년(계약/결제) 및 3년(분쟁) 보존 정보는 삭제 불가 및 법적 근거 안내
        """
        rights_queries = [
            "제 개인정보 전부 삭제해 주세요",
            "회원 탈퇴했으니 저장된 내 정보 지워주세요",
            "개인정보 삭제 요구 시 며칠 걸리나요?",
            "법정 보존 기간 때문에 삭제 안 되는 항목이 있나요?",
        ]
        for q in rights_queries:
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.PRIVACY_DATA_RIGHTS
            assert "영업일 10일 이내에 처리 결과를 회신" in res.knowledge_text
            assert "전자상거래법에 따라" in res.knowledge_text
            assert "삭제 요구에 응할 수 없으며" in res.knowledge_text

    def test_guardrail_8_external_and_group_requests(self):
        """
        대외 기관/언론 요청 (제19조) 및 단체 문의 최소수집 (제15조) 검증
        """
        external_queries = [
            "기자인데 피해 고객 명단 전화로 주세요",
            "방송국 취재차 연락했습니다. 고객 명단 알려주세요",
            "경찰인데 공문 없이 전화로 명단 내놔요",
        ]
        for q in external_queries:
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.PRIVACY_EXTERNAL_REQUEST
            assert "기관·언론 등 대외 요청 대응" in res.knowledge_text
            assert "공문·영장 등 법적 절차" in res.knowledge_text

        group_queries = [
            "단체 체험 참가자 명단이랑 주민번호 미리 보내드릴게요",
            "학생들 생년월일과 성별 명단 접수합니다",
        ]
        for q in group_queries:
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.PRIVACY_GROUP_COLLECTION
            assert "단체·미성년자 문의 최소 수집" in res.knowledge_text
            assert "참가자 개별 명단·생년월일·성별은 접수 단계에서 수집하지 않으며" in res.knowledge_text

    # ==========================================================================
    # 정기배송 약관 (제1조~제11조 전문 및 판정 매트릭스) 검증
    # ==========================================================================

    def test_subscription_articles_all_11_exist(self):
        """정기배송 약관 제1조~제11조 11개 조항 전수 존재 및 데이터 무결성 검증"""
        articles = get_all_subscription_articles()
        assert len(articles) == 11
        for i in range(1, 12):
            art = get_subscription_article(i)
            assert art is not None
            assert art.article_no == i
            assert art.chapter.startswith("제")
            assert len(art.title) > 0
            assert len(art.content) > 10
            assert len(art.key_points) > 0

    def test_subscription_article_titles_and_chapters(self):
        """정기배송 약관 장 및 조항 제목 정확성 검증"""
        expected = {
            1: ("제1장 총칙", "목적·적용"),
            2: ("제1장 총칙", "정의"),
            3: ("제2장 컷오프", "컷오프"),
            4: ("제2장 컷오프", "컷오프의 안내"),
            5: ("제3장 스킵", "스킵"),
            6: ("제3장 스킵", "컷오프 이후의 스킵 요청"),
            7: ("제4장 해지", "해지"),
            8: ("제4장 해지", "해지 시 하지 않는 것"),
            9: ("제5장 회차 변경", "회차 변경"),
            10: ("제6장 상담 처리 절차", "판정 순서"),
            11: ("제6장 상담 처리 절차", "판정 매트릭스"),
        }
        for num, (ch, ti) in expected.items():
            art = get_subscription_article(num)
            assert art.chapter == ch
            assert art.title == ti

    def test_subscription_cutoff_calculation_business_days(self):
        """컷오프 기준 검증: 결제일 3영업일 전 24시, 결제일 불산입 (제3조)"""
        # 금요일 결제일 (2037-07-10 금)
        # 1영업일전: 목(07-09), 2영업일전: 수(07-08), 3영업일전: 화(07-07)
        cutoff_fri = calculate_cutoff_datetime("2037-07-10")
        assert cutoff_fri == "2037-07-07 24:00"

        # 월요일 결제일 (2037-07-06 월)
        # 주말 제외: 1영업일전: 금(07-03), 2영업일전: 목(07-02), 3영업일전: 수(07-01)
        cutoff_mon = calculate_cutoff_datetime("2037-07-06")
        assert cutoff_mon == "2037-07-01 24:00"

        # 수요일 결제일 (2037-07-08 수)
        # 1영업일전: 화(07-07), 2영업일전: 월(07-06), 주말제외, 3영업일전: 금(07-03)
        cutoff_wed = calculate_cutoff_datetime("2037-07-08")
        assert cutoff_wed == "2037-07-03 24:00"

        # 공휴일 포함 시: 화요일(07-07)이 공휴일인 경우
        cutoff_holiday = calculate_cutoff_datetime("2037-07-10", holidays=["2037-07-07"])
        assert cutoff_holiday == "2037-07-06 24:00"

        # 상대 표현 금지 및 날짜·시각 YYYY-MM-DD 24:00 형식 검증 (제4조 제3항)
        assert cutoff_fri.endswith(" 24:00")
        assert "며칠 전" not in cutoff_fri

    def test_subscription_cutoff_comparison(self):
        """요청 시각의 컷오프 전/후 판정 (당일 24:00 포함)"""
        cutoff = "2037-07-07 24:00"
        # 컷오프 전 요청
        assert is_before_or_at_cutoff("2037-07-07 14:00", cutoff) is True
        assert is_before_or_at_cutoff("2037-07-06 09:00", cutoff) is True
        # 컷오프 당일 24:00 정각
        assert is_before_or_at_cutoff("2037-07-07 24:00", cutoff) is True
        # 컷오프 경과 후 (다음날 00:01)
        assert is_before_or_at_cutoff("2037-07-08 00:01", cutoff) is False
        assert is_before_or_at_cutoff("2037-07-08 10:00", cutoff) is False

    def test_subscription_skip_unlimited_and_no_termination(self):
        """스킵 횟수 한도 없음 및 반복 스킵 사유 거절/해지 불가 (제5조)"""
        art5 = get_subscription_article(5)
        assert "한도를 두지 아니한다" in art5.content
        assert "스킵이 반복된다는 사정만으로 요청을 거절하거나 계약을 해지하지 아니한다" in art5.content
        assert "임의로 해지하지 아니한다" in art5.content
        assert SUBSCRIPTION_CONSECUTIVE_SKIP_CHECK_THRESHOLD == 3

    def test_subscription_cancellation_and_forbidden_actions(self):
        """해지 위약금 없음, 전액 환불, 할인 미소급 및 3대 금지 행위 (제7조, 제8조)"""
        art7 = get_subscription_article(7)
        assert "언제든지 해지할 수 있다" in art7.content
        assert "위약금을 부과하지 아니한다" in art7.content
        assert "할인은 소급하여 반환하지 아니한다" in art7.content

        art8 = get_subscription_article(8)
        assert "해지 사유를 처리의 조건으로 요구하지 아니하고" in art8.content
        assert "만류를 위한 혜택 제시를 반복하지 아니하며" in art8.content
        assert "별도의 서면·통화 절차를 요구하지 아니한다" in art8.content

        assert len(SUBSCRIPTION_CANCELLATION_FORBIDDEN_ACTIONS) == 3

    def test_subscription_post_cutoff_alternatives(self):
        """컷오프 이후 단순 불가 거절 금지 및 4대 대안 필수 안내 (제6조, 제11조)"""
        alternatives = SUBSCRIPTION_POST_CUTOFF_ALTERNATIVES
        alt_names = [a["name"] for a in alternatives]
        assert "수령일 조정" in alt_names
        assert "배송지 변경" in alt_names
        assert "이번 회차 취소·환불" in alt_names
        assert "다음 회차 스킵 예약" in alt_names

    def test_subscription_evaluation_helper_matrix(self):
        """evaluate_subscription_request 헬퍼를 통한 제11조 매트릭스 전수 판정"""
        payment_date = "2037-07-10"  # 컷오프: 2037-07-07 24:00

        # 1. 컷오프 전 스킵
        res_skip_before = evaluate_subscription_request("스킵", "2037-07-07 15:00", payment_date)
        assert res_skip_before["is_before_cutoff"] is True
        assert res_skip_before["reflected_cycle"] == "이번 회차"
        assert "미결제·미발송" in res_skip_before["decision_summary"]

        # 2. 컷오프 후 스킵 -> 다음 회차부터 반영 & 대안 안내 필수
        res_skip_after = evaluate_subscription_request("스킵", "2037-07-08 10:00", payment_date, shipping_stage="결제완료")
        assert res_skip_after["is_before_cutoff"] is False
        assert res_skip_after["reflected_cycle"] == "다음 회차"
        assert "대안 안내" in res_skip_after["decision_summary"]
        assert len(res_skip_after["alternatives"]) == 4

        # 3. 컷오프 전 해지
        res_cancel_before = evaluate_subscription_request("해지", "2037-07-06 10:00", payment_date)
        assert res_cancel_before["is_before_cutoff"] is True
        assert res_cancel_before["reflected_cycle"] == "이번 회차"
        assert res_cancel_before["penalty_fee"] == 0
        assert res_cancel_before["refund_remaining"] == "전액환불"
        assert res_cancel_before["discount_clawback"] == "소급 반환 없음"
        assert len(res_cancel_before["forbidden_actions"]) == 3

        # 4. 컷오프 후 해지 -> 다음 회차부터 종료 & 대안 안내
        res_cancel_after = evaluate_subscription_request("해지", "2037-07-09 10:00", payment_date, shipping_stage="배송준비중")
        assert res_cancel_after["is_before_cutoff"] is False
        assert res_cancel_after["reflected_cycle"] == "다음 회차"
        # 배송준비중 단계에서는 이번 회차 취소·환불 불가
        cancel_alt = next(a for a in res_cancel_after["alternatives"] if a["name"] == "이번 회차 취소·환불")
        assert cancel_alt["available"] is False

        # 5. 품목·수량·주기 변경 (제9조)
        res_change_before = evaluate_subscription_request("주기 변경", "2037-07-07 18:00", payment_date)
        assert res_change_before["is_before_cutoff"] is True
        assert res_change_before["reflected_cycle"] == "이번 회차"

        res_change_after = evaluate_subscription_request("품목 변경", "2037-07-08 09:00", payment_date)
        assert res_change_after["is_before_cutoff"] is False
        assert res_change_after["reflected_cycle"] == "다음 회차"

    def test_subscription_consultation_steps(self):
        """제10조 상담 처리 4단계 절차 및 임의 단정 금지 원칙 검증"""
        steps = SUBSCRIPTION_DECISION_STEPS
        assert len(steps) == 4
        assert "구독 상태" in steps[0] and "조회" in steps[0]
        assert "컷오프와 대조" in steps[1]
        assert "반영 회차를 판정" in steps[2]
        assert "판정 결과와 그 근거" in steps[3]

        art10 = get_subscription_article(10)
        assert "조회 없이 '취소됐다' 또는 '안 된다'로 단정하지 아니한다" in art10.content

    def test_subscription_policy_router_various_queries(self):
        """정기배송 관련 다양한 질의에 대한 PolicyRouter 라우팅 및 지식 텍스트 검증"""
        test_queries = [
            "정기배송 이번 회차 스킵하고 싶어요",
            "구독 해지하려고 하는데 위약금이 있나요?",
            "다음 회차 배송 주기를 2주에서 4주로 변경할게요",
            "정기구독 컷오프 기준 시간이 언제인가요?",
            "스킵을 3번 연속으로 했는데 자동으로 해지되나요?",
            "컷오프 시간이 지났는데 이번 회차 취소 대안이 뭔가요?",
        ]
        for query in test_queries:
            res = PolicyRouter.route(query)
            assert res.primary_category == PolicyCategory.SUBSCRIPTION
            assert "정기배송 약관 제1조~제11조" in res.knowledge_text
            assert "컷오프: 해당 결제일 3영업일 전 24:00" in res.knowledge_text
            assert "위약금 0원" in res.knowledge_text
            assert "스킵 횟수 한도 없음" in res.knowledge_text
            assert "조회 없이 단정 금지" in res.knowledge_text
            assert len(res.knowledge_text) <= 400


class TestFarmPickupPolicy:
    """구방만 기사님을 통해 확보된 『산지 픽업 안내』(1~5번 전문) 단위 테스트"""

    def test_farm_pickup_sections_structure(self):
        """산지 픽업 안내 전체 1~5개 조항 무결성 및 구조 검증"""
        sections = get_all_pickup_sections()
        assert len(sections) == 5

        # 1. 요건
        sec1 = get_pickup_section(1)
        assert sec1 is not None
        assert sec1.title == "요건"
        assert "사전 예약" in sec1.items
        assert "예약 마감" in sec1.items
        assert "지정 장소" in sec1.items
        assert "지정 시간" in sec1.items
        assert "결제" in sec1.items
        assert "미운영 사유" in sec1.items
        assert "물량 혼재" in sec1.items["미운영 사유"]

        # 2. 본인확인
        sec2 = get_pickup_section(2)
        assert sec2 is not None
        assert sec2.title == "본인확인"
        assert "계정 귀속" in sec2.items["원칙"]
        assert sec2.items["확인"] == "주문번호 + 계정 명의"
        assert "사전 지정" in sec2.items["대리 수령"]
        assert "정보를 알고 있다는 사실만으로" in sec2.items["금지1"]
        assert "제3자 정보 보호 조항" in sec2.items["금지2"]

        # 3. 냉장 유지 책임
        sec3 = get_pickup_section(3)
        assert sec3 is not None
        assert sec3.title == "냉장 유지 책임"
        assert "조합" in sec3.items["예약 확정 ~ 인수 전"]
        assert "고객" in sec3.items["인수 시점 이후"]
        assert "인수 시점이 책임 경계" in sec3.items["책임 경계"]
        assert "품온 상승은 하자 사유로 접수되지 않는다" in sec3.items["책임 경계"]

        # 4. 배송비 · 기한 · 미수령
        sec4 = get_pickup_section(4)
        assert sec4 is not None
        assert sec4.title == "배송비 · 기한 · 미수령"
        assert "0원" in sec4.items["배송비"] or "미부과" in sec4.items["배송비"]
        assert "픽업일이 수령일이다" in sec4.items["하자 접수 기한"]
        assert "인수 전 개봉·확인 가능" in sec4.items["현장 확인"]
        assert "배송·반송 비용은 발생하지 않는다" in sec4.items["인수 거절 시 비용"]
        assert "당일 1회 재예약" in sec4.items["지정 시간 내 미수령"]
        assert "주문 취소·환불" in sec4.items["재예약분도 미수령"]
        assert "배송 전환(배송비 미부과) 또는 전액환불" in sec4.items["미수령 사유가 조합 측"]

        # 5. 픽업 이용 안내
        sec5 = get_pickup_section(5)
        assert sec5 is not None
        assert sec5.title == "픽업 이용 안내"
        assert "제주 현지에서 직접 수령하실 수 있습니다" in sec5.content
        assert "여름철에는 차량에 장시간 보관하지 마시고" in sec5.content

    def test_pickup_requirement_facts(self):
        """1번 요건 팩트 검증 (사전예약 필수, 마감, 장소, 시간, 결제, 상차시간 미운영)"""
        assert PICKUP_ADVANCE_RESERVATION_REQUIRED is True
        assert PICKUP_RESERVATION_DEADLINE == "수령 희망일 1영업일 전"
        assert "집하장 1곳" in PICKUP_LOCATION_RULE
        assert "밭·하우스 현장 수령 불가" in PICKUP_LOCATION_RULE
        assert "오전 중 1개 시간대" in PICKUP_TIME_RULE
        assert "물량 혼재" in PICKUP_TIME_RULE
        assert "온라인몰에서 결제한 주문에 한함" in PICKUP_PAYMENT_RULE
        assert "현장 결제·현장 주문" in PICKUP_PAYMENT_RULE

    def test_pickup_auth_and_proxy_facts(self):
        """2번 본인확인 및 대리수령 팩트 검증 (주문번호+명의, 사전대리인, 구술인도불가)"""
        assert "주문자 본인" in PICKUP_AUTH_RULE
        assert "주문번호 + 계정 명의" in PICKUP_AUTH_RULE
        assert "사전 지정한 경우에만" in PICKUP_PROXY_RULE
        assert "구술만으로 인도 불가" in PICKUP_PROXY_RULE
        assert "제3자 정보 보호 조항" in PICKUP_THIRD_PARTY_PRIVACY_RULE

    def test_pickup_temp_responsibility_boundary(self):
        """3번 냉장 유지 책임 경계 팩트 검증 (인수 시점 경계, 차량 적재 후 품온 상승 하자 미인정)"""
        assert "인수 시점이 책임 경계" in PICKUP_TEMP_RESPONSIBILITY_BOUNDARY
        assert "인수 전 조합 책임" in PICKUP_TEMP_RESPONSIBILITY_BOUNDARY
        assert "이동 중 온도 관리 포함 고객 책임" in PICKUP_TEMP_RESPONSIBILITY_BOUNDARY
        assert "품온 상승은 하자 사유로 미인정" in PICKUP_VEHICLE_TEMP_CLAIM_RULE

        # 함수 평가 검증
        claim_before = evaluate_pickup_temp_claim("인수전")
        assert claim_before["acceptable"] is True
        assert claim_before["responsible_party"] == "조합"

        claim_after_vehicle = evaluate_pickup_temp_claim("차량적재후")
        assert claim_after_vehicle["acceptable"] is False
        assert claim_after_vehicle["responsible_party"] == "고객"
        assert "품온 상승은 하자 사유로 미인정" in claim_after_vehicle["reason"]

        claim_moving = evaluate_pickup_temp_claim("이동중")
        assert claim_moving["acceptable"] is False
        assert claim_moving["responsible_party"] == "고객"

    def test_pickup_shipping_fee_and_inspection_and_no_show(self):
        """4번 배송비, 기한, 미수령, 현장확인 및 인수거절권 팩트 검증"""
        assert PICKUP_SHIPPING_FEE == 0
        assert "개봉·확인 가능" in PICKUP_INSPECTION_RIGHT
        assert "배송·반송 비용 없이 주문 취소" in PICKUP_INSPECTION_RIGHT
        assert "당일 1회 재예약" in PICKUP_NO_SHOW_RULE
        assert "재예약분도 미수령 시 신선식품 품질 유지 어려워 주문 취소·환불" in PICKUP_NO_SHOW_RULE
        assert "배송 전환(배송비 미부과) 또는 전액환불" in PICKUP_ASSOCIATION_FAULT_RULE

    def test_evaluate_pickup_eligibility(self):
        """evaluate_pickup_eligibility 함수 판정 로직 검증"""
        # 1. 정상 사전 예약 건
        res_ok = evaluate_pickup_eligibility(
            is_reserved=True,
            reservation_days_in_advance=1,
            location_type="집하장",
            time_slot="오전",
            payment_method="온라인몰",
            is_orderer=True,
            has_order_number=True,
        )
        assert res_ok["eligible"] is True
        assert res_ok["shipping_fee"] == 0
        assert len(res_ok["reasons"]) == 0

        # 2. 예약 없는 즉석 방문
        res_no_reserve = evaluate_pickup_eligibility(is_reserved=False)
        assert res_no_reserve["eligible"] is False
        assert any("사전 예약 필수" in r for r in res_no_reserve["reasons"])

        # 3. 밭이나 비닐하우스 방문 요구
        res_field = evaluate_pickup_eligibility(is_reserved=True, location_type="감귤밭")
        assert res_field["eligible"] is False
        assert any("밭이나 비닐하우스" in r for r in res_field["reasons"])

        # 4. 택배 상차 시간대 방문 요구
        res_truck = evaluate_pickup_eligibility(is_reserved=True, time_slot="오후 상차시간")
        assert res_truck["eligible"] is False
        assert any("상차 시간대 미운영" in r for r in res_truck["reasons"])

        # 5. 현장 결제 요구
        res_pay = evaluate_pickup_eligibility(is_reserved=True, payment_method="현장결제")
        assert res_pay["eligible"] is False
        assert any("현장 결제" in r for r in res_pay["reasons"])

        # 6. 사전 미지정 대리인
        res_proxy = evaluate_pickup_eligibility(
            is_reserved=True, is_orderer=False, is_designated_proxy=False
        )
        assert res_proxy["eligible"] is False
        assert any("사전 지정 대리인" in r for r in res_proxy["reasons"])

    def test_pickup_policy_router_various_queries(self):
        """산지 픽업 관련 다양한 고객 발화에 대한 PolicyRouter 라우팅 및 지식 텍스트 검증"""
        test_queries = [
            "제주도 여행 중에 직접 가서 수령할 수 있나요?",
            "산지 픽업 예약하고 싶은데 절차가 어떻게 되나요?",
            "농가 감귤 밭으로 직접 찾아가서 픽업할게요",
            "현장에서 직접 수령하면 배송비는 얼마인가요?",
            "현장에 가서 직접 카드 결제하고 주문할 수 있나요?",
            "픽업해서 제 차에 싣고 왔는데 날씨가 더워서 물렀어요 환불해 주세요",
            "친구가 대신 가서 픽업 수령할 수 있나요?",
            "현장에서 상품 상태 확인하고 마음에 안 들면 인수 거절할 수 있나요?",
            "픽업 시간을 놓쳐서 못 갔는데 취소되나요?",
        ]
        for query in test_queries:
            res = PolicyRouter.route(query)
            assert res.primary_category == PolicyCategory.PICKUP
            assert "산지 픽업 안내 규정" in res.knowledge_text
            assert "사전예약 필수" in res.knowledge_text
            assert "지정 집하장 1곳" in res.knowledge_text
            assert "온라인몰 사전결제" in res.knowledge_text
            assert "인수시점이 경계" in res.knowledge_text
            assert "품온상승 하자 미인정" in res.knowledge_text
            assert "0원" in res.knowledge_text
            assert "인수전 개봉확인" in res.knowledge_text
            assert len(res.knowledge_text) <= 400


class TestProofIssuanceRules:
    """세금계산서·현금영수증 발행 기준 (1~7번 전문) 단위 테스트"""

    def test_payment_method_proof_rules_and_effective_base(self):
        """결제수단별 발행 대상 및 실결제액 기준액 검증 (1번)"""
        # 1. 현금·계좌이체: 현금영수증 발행 대상
        res_cash = evaluate_proof_request(
            payment_method="계좌이체", actual_amount=50000, points_used=5000, coupon_discount=3000
        )
        assert res_cash["issuable"] is True
        assert res_cash["proof_type"] == "현금영수증"
        # 정가 50,000원이 아닌 적립금·쿠폰 차감 후 실결제액 42,000원 기준
        assert res_cash["base_amount"] == 42000

        # 2. 카드 결제: 카드 매출전표 대체 (중복 발행 불가)
        res_card = evaluate_proof_request(payment_method="신용카드", actual_amount=60000)
        assert res_card["issuable"] is False
        assert res_card["proof_type"] == "카드 매출전표"
        assert "중복 증빙 방지" in res_card["reason"]

        # 3. 사업자 거래(도매): 전자세금계산서
        res_b2b = evaluate_proof_request(
            payment_method="계좌이체", actual_amount=300000, is_wholesale_business=True
        )
        assert res_b2b["issuable"] is True
        assert res_b2b["proof_type"] == "전자세금계산서"

        # 4. 분할결제: 현금분 현영 + 카드분 매출전표
        res_split = evaluate_proof_request(
            payment_method="분할결제",
            actual_amount=100000,
            split_cash_amount=40000,
            split_card_amount=60000,
        )
        assert res_split["issuable"] is True
        assert res_split["proof_type"] == "수단별 분할 처리"
        assert res_split["cash_proof"] == "현금영수증"
        assert res_split["card_proof"] == "카드 매출전표"
        assert res_split["cash_amount"] == 40000
        assert res_split["card_amount"] == 60000

    def test_cash_receipt_rules_and_privacy_guardrail(self):
        """현금영수증 발행 유형, 기한, 선낭독 금지 보안 가드레일 검증 (2번)"""
        # 1. 개인의 지출증빙용 요청: 허용
        res_personal_expense = evaluate_cash_receipt_request(
            receipt_type="지출증빙용",
            is_business=False,
            has_provided_id_number=True,
            is_before_deadline=True,
        )
        assert res_personal_expense["issuable"] is True

        # 2. 사업자의 소득공제용 요청: 불허 (사업자는 소득공제용 불가)
        res_biz_deduction = evaluate_cash_receipt_request(
            receipt_type="소득공제용",
            is_business=True,
            has_provided_id_number=True,
            is_before_deadline=True,
        )
        assert res_biz_deduction["issuable"] is False
        assert "사업자는 소득공제용으로 요청할 수 없음" in res_biz_deduction["reason"]

        # 3. 익월 10일 기한 경과: 조합 발행 불가 -> 국세청 자율 발급 안내
        res_expired = evaluate_cash_receipt_request(
            receipt_type="소득공제용",
            is_business=False,
            has_provided_id_number=True,
            is_before_deadline=False,
        )
        assert res_expired["issuable"] is False
        assert "익월 10일 경과" in res_expired["reason"]
        assert "국세청 홈택스 자율 발급" in res_expired["action"]

        # 4. 개인정보 보호: 고객 번호 제시 전 상담사 선낭독 절대 금지
        res_no_id = evaluate_cash_receipt_request(
            receipt_type="소득공제용",
            is_business=False,
            has_provided_id_number=False,
            is_before_deadline=True,
        )
        assert res_no_id["issuable"] is False
        assert "먼저 읽어주는 행위 절대 금지" in res_no_id["reason"]

        # 5. 홈택스 익영업일 조회 및 연말정산 자동 반영 템플릿 검증
        assert "통상 다음 영업일부터 조회" in CASH_RECEIPT_RULES["hometax_reflection"]
        assert "연말정산 자동 반영" in CASH_RECEIPT_RULES["hometax_reflection"]

    def test_tax_invoice_tax_exempt_and_vat_separation(self):
        """세금계산서 면세 0원 및 과세 배송비 분리 기재 검증 (3번 - 초특급 세무 팩트)"""
        # 1. 미가공 농·수산물 면세 및 배송비 10% 부가세 분리 산정
        calc = calculate_tax_and_vat(product_amount=50000, shipping_fee=4000)
        assert calc["product_amount"] == 50000
        assert calc["product_vat"] == 0  # 미가공 농수산물 면세 (세액 0원)
        assert "면세" in calc["product_tax_type"]
        assert calc["shipping_amount"] == 4000
        assert calc["shipping_vat"] == 400  # 배송비는 용역분 부가세 10%
        assert "과세" in calc["shipping_tax_type"]
        assert calc["total_supply_price"] == 54000
        assert calc["total_vat"] == 400
        assert calc["total_payment"] == 54400
        # 합산 기재 절대 금지 및 분리 기재 필수
        assert calc["separate_invoice_required"] is True
        assert calc["combined_entry_forbidden"] is True

        # 2. 결제 사업자 명의와 요청 명의 불일치 시 거절
        res_mismatch = evaluate_tax_invoice_request(
            payment_business_name="주식회사 교동상사",
            requested_business_name="타사유통 주식회사",
            has_biz_registration_cert=True,
            is_before_deadline=True,
        )
        assert res_mismatch["issuable"] is False
        assert res_mismatch["verdict"] == "거절"
        assert "다른 사업자 명의" in res_mismatch["reason"]
        assert "당사자 사이에서 정산 안내" in res_mismatch["proper_procedure"]

        # 3. 사업자등록증 서류 미제출 시 보류
        res_no_cert = evaluate_tax_invoice_request(
            payment_business_name="주식회사 교동상사",
            requested_business_name="주식회사 교동상사",
            has_biz_registration_cert=False,
            is_before_deadline=True,
        )
        assert res_no_cert["issuable"] is False
        assert res_no_cert["verdict"] == "보류"
        assert "사업자등록증 서류 확인 필수" in res_no_cert["reason"]

        # 4. 익월 10일 기한 경과 시 소급 발행 거절
        res_expired = evaluate_tax_invoice_request(
            payment_business_name="주식회사 교동상사",
            requested_business_name="주식회사 교동상사",
            has_biz_registration_cert=True,
            is_before_deadline=False,
        )
        assert res_expired["issuable"] is False
        assert res_expired["verdict"] == "거절"
        assert "소급 발행 불가" in res_expired["reason"]

    def test_proof_correction_codes_tx01_to_tx06(self):
        """세무 증빙 6대 정정 코드(TX-01 ~ TX-06) 및 TX-05 원칙 검증 (4번)"""
        assert len(PROOF_CORRECTION_CODES) == 6

        tx01 = evaluate_proof_correction("TX-01")
        assert tx01.reason == "기재사항 착오"
        assert tx01.method == "수정 발행"

        tx02 = evaluate_proof_correction("TX-02")
        assert tx02.reason == "공급가액 변동"
        assert "부분환불" in tx02.description
        assert tx02.method == "차액분 수정 발행"

        tx03 = evaluate_proof_correction("TX-03")
        assert tx03.reason == "계약 해제"
        assert "전액환불" in tx03.description
        assert tx03.method == "전액 취소 발행"

        tx04 = evaluate_proof_correction("TX-04")
        assert tx04.reason == "중복 발행"
        assert tx04.method == "후행분 취소"

        # TX-05: 명의 오류는 취소 후 재발행 (우회 발행 금지)
        tx05 = evaluate_proof_correction("TX-05")
        assert tx05.reason == "명의 오류"
        assert tx05.method == "취소 후 정당 명의로 재발행"
        assert "우회 발행 및 선발행 후 정정 수단으로 악용 절대 금지" in tx05.description

        tx06 = evaluate_proof_correction("TX-06")
        assert tx06.reason == "필요적 기재사항 누락"
        assert tx06.method == "재발행"

    def test_proof_refund_rules(self):
        """환불 시 증빙 처리 규칙 검증 (5번)"""
        assert "발행하지 아니함" in PROOF_REFUND_RULES["before_issuance"]
        assert "현금영수증 취소" in PROOF_REFUND_RULES["full_refund"]
        assert "TX-03" in PROOF_REFUND_RULES["full_refund"]
        assert "TX-02" in PROOF_REFUND_RULES["partial_refund"]
        assert "원본 증빙을 취소하지 않음" in PROOF_REFUND_RULES["partial_refund"]
        assert "환불 승인일 기준" in PROOF_REFUND_RULES["after_month_close"]
        assert "증빙 정정을 진행하지 아니함" in PROOF_REFUND_RULES["points_refund"]

    def test_proof_refusal_rules(self):
        """7대 거절 대상 판정 및 정상 절차 안내 검증 (6번)"""
        assert len(PROOF_REFUSAL_RULES) == 7

        # 1. 다른 사업자 명의
        ref1 = check_proof_refusal("다른 사업자 명의로 세금계산서 끊어주세요")
        assert ref1 is not None
        assert ref1.verdict == "거절"
        assert "허위 증빙" in ref1.reason
        assert "당사자 사이에서 정산 안내" in ref1.proper_procedure

        # 2. 가공 사업자 명의
        ref2 = check_proof_refusal("페이퍼컴퍼니 가공 사업자 명의로 해주세요")
        assert ref2 is not None
        assert ref2.verdict == "거절"

        # 3. 개인 결제분을 사업자 명의로
        ref3 = check_proof_refusal("개인 카드로 긁고 사업자 명의 세금계산서 주세요")
        assert ref3 is not None
        assert ref3.verdict == "거절"

        # 4. 실결제액보다 많은 금액
        ref4 = check_proof_refusal("실제 결제액보다 금액을 부풀려 많이 적어주세요")
        assert ref4 is not None
        assert ref4.verdict == "거절"

        # 5. 다른 품목 기재
        ref5 = check_proof_refusal("품명을 사무용품으로 바꿔 적어주세요")
        assert ref5 is not None
        assert ref5.verdict == "거절"

        # 6. 소급 발행
        ref6 = check_proof_refusal("익월 10일 지났는데 소급 발행 가능한가요?")
        assert ref6 is not None
        assert ref6.verdict == "거절"
        assert "국세청 홈택스 자율 발급" in ref6.proper_procedure

        # 7. 취소된 거래 증빙 유지
        ref7 = check_proof_refusal("주문 취소했는데 영수증 그대로 두면 안 되나요?")
        assert ref7 is not None
        assert ref7.verdict == "거절"

    def test_tax_proof_policy_router(self):
        """세무 증빙 고객 질의 PolicyRouter 라우팅 및 지식 주입 검증"""
        queries = [
            "계좌이체로 구매했는데 현금영수증 발행해 주세요",
            "카드 결제했는데 세금계산서 별도로 끊어주시나요?",
            "세금계산서 세액이 왜 0원인가요? 부가세 공란이 정상인가요?",
            "배송비 부가세는 세금계산서에 어떻게 기재되나요?",
            "세금계산서 상호 오기가 있어서 TX-01 정정 요청합니다",
            "세금계산서 TX-05 명의 오류 수정 절차가 어떻게 되나요?",
            "다른 회사 명의로 세금계산서 발행해 주세요",
            "지난달 10일 지난 주문 건 세금계산서 소급발행 되나요?",
            "부분환불 받았는데 현금영수증 어떻게 수정되나요?",
        ]
        for q in queries:
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.TAX_PROOF, f"라우팅 실패: {q}"
            assert "세무 증빙" in res.knowledge_text or "세금계산서" in res.knowledge_text
            assert len(res.knowledge_text) <= 400


class TestOfficialProductSKUs:
    """공식 판매 상품 3종(WTM-SEL-8, HGL-SEL-5, HGL-STD-5) 및 당도/규격 판정 검증"""

    def test_official_products_definitions(self):
        """공식 판매 3종 상품 SKU 명세 무결성 검증"""
        assert len(OFFICIAL_PRODUCTS) == 3

        # 1. 수박 WTM-SEL-8
        wtm = get_official_product("WTM-SEL-8")
        assert wtm is not None
        assert wtm.price == 27900
        assert wtm.shipping_fee == 4000
        assert wtm.is_min_spec is True  # 8kg 이상 규격 상품
        assert wtm.sugar_brix_guarantee == 11.0
        assert wtm.has_sugar_guarantee is True

        # 2. 감귤 당도선별 HGL-SEL-5
        hgl_sel = get_official_product("HGL-SEL-5")
        assert hgl_sel is not None
        assert hgl_sel.price == 30000
        assert hgl_sel.shipping_fee == 4000
        assert hgl_sel.is_min_spec is False  # 일반 표기 상품
        assert hgl_sel.sugar_brix_guarantee == 12.0  # 하우스감귤 12브릭스
        assert hgl_sel.has_sugar_guarantee is True

        # 3. 감귤 일반 라인 HGL-STD-5
        hgl_std = get_official_product("HGL-STD-5")
        assert hgl_std is not None
        assert hgl_std.price == 24000
        assert hgl_std.sugar_brix_guarantee is None
        assert hgl_std.has_sugar_guarantee is False  # 규정 제7조 제3항: 당도 미달 하자 적용 제외

    def test_product_sugar_claim_evaluation(self):
        """공식 상품별 당도 미달 클레임 판정 검증 (규정 제7조)"""
        # 수박 11브릭스 기준
        res_wtm_under = evaluate_product_sugar_claim("WTM-SEL-8", 10.5)
        assert res_wtm_under["is_defect"] is True
        assert res_wtm_under["verdict"] == "당도 미달 하자"
        assert "재배송" in res_wtm_under["action"]

        res_wtm_ok = evaluate_product_sugar_claim("WTM-SEL-8", 11.2)
        assert res_wtm_ok["is_defect"] is False
        assert res_wtm_ok["verdict"] == "정상 당도 충족"

        # 감귤선별 12브릭스 기준 (11브릭스는 수박 기준이므로 감귤에서는 미달!)
        res_hgl_11bx = evaluate_product_sugar_claim("HGL-SEL-5", 11.5)
        assert res_hgl_11bx["is_defect"] is True
        assert res_hgl_11bx["verdict"] == "당도 미달 하자"

        res_hgl_ok = evaluate_product_sugar_claim("HGL-SEL-5", 12.3)
        assert res_hgl_ok["is_defect"] is False

        # 감귤 일반 HGL-STD-5: 당도 미표기 라인이므로 아무리 낮아도 하자 적용 제외!
        res_std_low = evaluate_product_sugar_claim("HGL-STD-5", 8.5)
        assert res_std_low["is_defect"] is False
        assert res_std_low["verdict"] == "하자 적용 제외"
        assert "당도 미달 하자 적용 제외" in res_std_low["action"]

    def test_product_weight_claim_evaluation(self):
        """공식 상품별 중량/규격 미달 클레임 판정 검증 (규정 제6조)"""
        # 수박 WTM-SEL-8: '8kg 이상' 규격 상품이므로 ±5% 허용오차 절대 미적용 (7.9kg도 하자!)
        res_wtm_7_9kg = evaluate_product_weight_claim("WTM-SEL-8", 7.9)
        assert res_wtm_7_9kg["is_defect"] is True
        assert res_wtm_7_9kg["verdict"] == "규격 미달 하자"
        assert res_wtm_7_9kg["tolerance_pct"] == 0.0

        res_wtm_8_1kg = evaluate_product_weight_claim("WTM-SEL-8", 8.1)
        assert res_wtm_8_1kg["is_defect"] is False

        # 감귤 HGL-SEL-5: 일반 5kg 표기 상품이므로 ±5% 허용오차 적용 (4.75kg 이상 정상)
        res_hgl_4_8kg = evaluate_product_weight_claim("HGL-SEL-5", 4.8)
        assert res_hgl_4_8kg["is_defect"] is False
        assert res_hgl_4_8kg["verdict"] == "정상 허용오차 범위 내"

        res_hgl_4_6kg = evaluate_product_weight_claim("HGL-SEL-5", 4.6)
        assert res_hgl_4_6kg["is_defect"] is True
        assert res_hgl_4_6kg["verdict"] == "무게 미달 하자"


class TestPaymentReconciliation:
    """『결제·주문 대사 절차서』 4대 대사키 및 10대 불일치 코드 (M-01~M-10) 검증"""

    def test_reconciliation_4_keys_verification(self):
        """4대 대사키(승인번호, 결제금액, 승인시각, 카드 뒷 4자리) 검증"""
        # 1. 4개 키 정상 일치 (승인시각 3분 차이: 5분 이내)
        res_ok = verify_reconciliation_4_keys(
            approval_number_matched=True,
            payment_amount_matched=True,
            time_diff_minutes=3.0,
            card_last_4_matched=True,
            card_last_4_read_by_agent_first=False,
        )
        assert res_ok["all_matched"] is True
        assert res_ok["privacy_violation"] is False

        # 2. 승인시각 6분 차이: ±5분 허용오차 초과
        res_time_fail = verify_reconciliation_4_keys(
            approval_number_matched=True,
            payment_amount_matched=True,
            time_diff_minutes=6.0,
            card_last_4_matched=True,
        )
        assert res_time_fail["all_matched"] is False
        assert res_time_fail["time_matched"] is False

        # 3. 상담사가 카드 뒷 4자리를 먼저 낭독한 경우 (개인정보보호 위반)
        res_privacy_fail = verify_reconciliation_4_keys(
            approval_number_matched=True,
            payment_amount_matched=True,
            time_diff_minutes=2.0,
            card_last_4_matched=True,
            card_last_4_read_by_agent_first=True,
        )
        assert res_privacy_fail["all_matched"] is False
        assert res_privacy_fail["privacy_violation"] is True

    def test_reconciliation_10_codes_diagnosis(self):
        """10대 불일치 코드(M-01 ~ M-10) 진단 로직 검증"""
        # M-01: 네 키 일치, 주문 레코드 없음 -> 주문 유실
        c1 = diagnose_reconciliation_case(has_approval=True, order_exists=False)
        assert c1 == ReconciliationCode.M_01

        # M-02: 취소 상태 주문
        c2 = diagnose_reconciliation_case(has_approval=True, order_exists=True, is_order_cancelled=True)
        assert c2 == ReconciliationCode.M_02

        # M-03: 승인번호 없음 (결제 승인 자체가 없음)
        c3 = diagnose_reconciliation_case(has_approval=False)
        assert c3 == ReconciliationCode.M_03

        # M-04: 금액 불일치
        c4 = diagnose_reconciliation_case(has_approval=True, amount_matched=False)
        assert c4 == ReconciliationCode.M_04

        # M-05: 승인시각 ±5분 초과
        c5 = diagnose_reconciliation_case(has_approval=True, time_diff_minutes=7.0)
        assert c5 == ReconciliationCode.M_05

        # M-06: 카드 뒷 4자리 불일치
        c6 = diagnose_reconciliation_case(has_approval=True, card_last_4_matched=False)
        assert c6 == ReconciliationCode.M_06

        # M-07: 동일 승인번호 2건 이상 중복 전송
        c7 = diagnose_reconciliation_case(has_approval=True, approval_duplicate_count=2)
        assert c7 == ReconciliationCode.M_07

        # M-08: 주문 1건에 결제 승인 2건 (중복 결제)
        c8 = diagnose_reconciliation_case(has_approval=True, approval_count_for_order=2)
        assert c8 == ReconciliationCode.M_08

        # M-09: 일시적 시스템 반영 지연
        c9 = diagnose_reconciliation_case(has_approval=True, is_temporary_delay=True)
        assert c9 == ReconciliationCode.M_09

        # M-10: 타 계정 귀속
        c10 = diagnose_reconciliation_case(has_approval=True, is_different_account=True)
        assert c10 == ReconciliationCode.M_10

    def test_m01_order_recovery_guidelines(self):
        """M-01 주문 유실 확정 시 복구 및 환불 기준 검증 (§4)"""
        # 1. 정상 재고 확보 시: 결제 원본으로 복구 및 정상 출하 (가격 상승 시에도 추가결제 요구 금지)
        rec1 = evaluate_m01_order_recovery(stock_available=True, price_increased=True)
        assert rec1["action"] == "주문 복구 및 정상 출하"
        assert rec1["demand_repayment"] is False
        assert rec1["extra_payment_required"] is False

        # 2. 품절 / 시즌 종료 시: 미배송분 전액 환불
        rec2 = evaluate_m01_order_recovery(stock_available=False, partial_stock_available=False)
        assert rec2["action"] == "전액 환불"
        assert rec2["demand_repayment"] is False

        # 3. 일부 품목만 출하 가능 시: 출하분 유지 + 미배송분 부분환불
        rec3 = evaluate_m01_order_recovery(stock_available=False, partial_stock_available=True)
        assert rec3["action"] == "출하분 유지 + 미배송분 부분환불"

        # 4. 지연으로 고객이 원치 않는 경우: 미배송분 환불
        rec4 = evaluate_m01_order_recovery(stock_available=True, customer_wants_cancel_due_to_delay=True)
        assert rec4["action"] == "미배송분 환불"

    def test_reconciliation_policy_router(self):
        """결제·주문 대사 관련 고객 질의 라우팅 및 지식 주입 검증"""
        queries = [
            "결제 문자는 왔는데 주문내역에 조회가 안 돼요",
            "카드에서 돈만 빠져나가고 주문서가 생성되지 않았습니다",
            "동일한 주문이 중복 결제되어 카드 승인이 2건 났어요",
            "M-01 주문 유실 코드 처리 지침이 어떻게 되나요?",
            "M-03 승인 없는 거래에 대해서는 어떻게 응대하나요?",
            "M-08 중복 결제 판정 기준이 무엇인가요?",
            "M-09 시스템 반영 지연일 때 바로 환불해주면 되나요?",
            "결제 대사할 때 4대 대사키가 무엇인가요?",
            "공식 판매 상품 WTM-SEL-8 규격과 가격 안내해 주세요",
        ]
        for q in queries:
            res = PolicyRouter.route(q)
            assert res.primary_category == PolicyCategory.PAYMENT_RECONCILIATION, f"라우팅 실패: {q}"
            assert len(res.knowledge_text) <= 400
            assert "결제" in res.knowledge_text or "대사" in res.knowledge_text or "공식 판매 상품" in res.knowledge_text


class TestAgriculturalSeasonCalendar:
    """교동마을 농산 시즌 캘린더(기준일 2037-06-30) 및 10대 업무 처리 가이드라인 단위 테스트"""

    def test_season_status_enum_and_definitions(self):
        """농산 시즌 6대 상태(전, 예, 초, 성, 말, 종) Enum 및 정의 검증 (§2)"""
        # 1. 상태별 코드 및 속성 매핑 검증
        assert SeasonStatus.BEFORE.code == "전"
        assert SeasonStatus.BEFORE.label == "출하 전"
        assert SeasonStatus.BEFORE.is_sellable is False

        assert SeasonStatus.RESERVATION.code == "예"
        assert SeasonStatus.RESERVATION.label == "예약 접수"
        assert SeasonStatus.RESERVATION.is_sellable is False
        assert SeasonStatus.RESERVATION.is_reservation_only is True

        assert SeasonStatus.EARLY.code == "초"
        assert SeasonStatus.EARLY.label == "초입"
        assert SeasonStatus.EARLY.is_sellable is True

        assert SeasonStatus.PEAK.code == "성"
        assert SeasonStatus.PEAK.label == "성수기"
        assert SeasonStatus.PEAK.is_sellable is True

        assert SeasonStatus.LATE.code == "말"
        assert SeasonStatus.LATE.label == "시즌 말"
        assert SeasonStatus.LATE.is_sellable is True

        assert SeasonStatus.CLOSED.code == "종"
        assert SeasonStatus.CLOSED.label == "종료"
        assert SeasonStatus.CLOSED.is_sellable is False

        # 2. 한글 약칭으로부터 생성 검증
        for code in ["전", "예", "초", "성", "말", "종"]:
            st = SeasonStatus.from_code(code)
            assert st.code == code

        # 3. 6대 상태 정의표 무결성 검증
        for status in SeasonStatus:
            info = SEASON_STATUS_DEFINITIONS[status]
            assert info.status == status
            assert info.code == status.code

    def test_monthly_season_matrix_june_july_2037(self):
        """2037-06-30 기준 6월 및 7월 농산 10품목·11라인 상태 정확도 검증 (§4)"""
        from datetime import date

        # 1. 수박(WTM): 6월 초, 7월 성 (11Bx 보장, 8kg 규격 상품 오차 미적용)
        wtm = get_agri_season_line("수박")
        assert wtm is not None
        assert wtm.monthly_statuses[6] == SeasonStatus.EARLY
        assert wtm.monthly_statuses[7] == SeasonStatus.PEAK
        assert get_current_season_status("수박", date(2037, 6, 30)) == SeasonStatus.EARLY

        # 2. 하우스감귤(HGL): 6~8월 성 (12Bx 보장)
        hgl = get_agri_season_line("하우스감귤")
        assert hgl is not None
        assert hgl.monthly_statuses[6] == SeasonStatus.PEAK
        assert hgl.monthly_statuses[7] == SeasonStatus.PEAK
        assert hgl.monthly_statuses[8] == SeasonStatus.PEAK
        assert get_current_season_status("하우스감귤", date(2037, 6, 30)) == SeasonStatus.PEAK

        # 3. 노지감귤(NGL): 6~7월 종 (차기 11월)
        ngl = get_agri_season_line("노지감귤")
        assert ngl is not None
        assert ngl.monthly_statuses[6] == SeasonStatus.CLOSED
        assert ngl.monthly_statuses[7] == SeasonStatus.CLOSED
        assert ngl.next_season_start == "11월"
        assert get_current_season_status("노지감귤", date(2037, 6, 30)) == SeasonStatus.CLOSED

        # 4. 청귤(NGL_RSV): 6~7월 예 (8월 성수기)
        green = get_agri_season_line("청귤")
        assert green is not None
        assert green.monthly_statuses[6] == SeasonStatus.RESERVATION
        assert green.monthly_statuses[7] == SeasonStatus.RESERVATION
        assert green.monthly_statuses[8] == SeasonStatus.PEAK
        assert get_current_season_status("청귤", date(2037, 6, 30)) == SeasonStatus.RESERVATION

        # 5. 애플망고(MNG): 6월 성, 7월 말
        mng = get_agri_season_line("애플망고")
        assert mng is not None
        assert mng.monthly_statuses[6] == SeasonStatus.PEAK
        assert mng.monthly_statuses[7] == SeasonStatus.LATE
        assert get_current_season_status("애플망고", date(2037, 6, 30)) == SeasonStatus.PEAK

        # 6. 감자(PTT): 6~7월 성 (연중 공급, 종 없음)
        ptt = get_agri_season_line("감자")
        assert ptt is not None
        assert ptt.monthly_statuses[6] == SeasonStatus.PEAK
        assert ptt.monthly_statuses[7] == SeasonStatus.PEAK
        assert SeasonStatus.CLOSED not in ptt.monthly_statuses.values()  # 감자에는 종이 없다

        # 7. 기타 품목 6~7월 상태 검증
        assert get_agri_season_status("멜론", 6) == SeasonStatus.PEAK
        assert get_agri_season_status("멜론", 7) == SeasonStatus.PEAK
        assert get_agri_season_status("고구마", 6) == SeasonStatus.CLOSED
        assert get_agri_season_status("고구마", 7) == SeasonStatus.CLOSED
        assert get_agri_season_status("참다래", 6) == SeasonStatus.CLOSED
        assert get_agri_season_status("참다래", 7) == SeasonStatus.CLOSED
        assert get_agri_season_status("절임배추", 6) == SeasonStatus.CLOSED
        assert get_agri_season_status("절임배추", 7) == SeasonStatus.CLOSED
        assert get_agri_season_status("만감류", 6) == SeasonStatus.CLOSED
        assert get_agri_season_status("만감류", 7) == SeasonStatus.CLOSED

    def test_season_closed_forbidden_sold_out_guardrail(self):
        """상태가 '종'인 라인에 대한 '품절' 금지어 가드레일 및 대안 제시 검증 (§5 규칙 ①)"""
        # 1. 금지어 탐지 함수 검증
        assert check_season_closed_forbidden_words("품절이라 곧 들어와요") is True
        assert check_season_closed_forbidden_words("현재 상품이 품절되었습니다.") is True
        assert check_season_closed_forbidden_words("노지감귤은 품절입니다.") is True
        assert check_season_closed_forbidden_words("해당 상품은 품절되어서 주문이 어렵습니다.") is True

        # 정정 및 올바른 안내 문안은 통과(False)
        assert check_season_closed_forbidden_words("품절이 아니라 시즌이 끝났습니다. 다음 시즌은 11월입니다.") is False
        assert check_season_closed_forbidden_words("품절 아닌 시즌 종료 상품입니다.") is False

        # 2. 6월 노지감귤 문의 시 '종' 처리 정책 평가
        res = evaluate_season_inquiry("노지감귤")
        assert res["is_closed"] is True
        assert res["rule_no"] == 1
        assert res["prohibit_sold_out_phrase"] is True
        assert "품절이 아니라 시즌이 끝났습니다" in res["guide_message"]
        assert "11월" in res["guide_message"]
        assert len(res["recommended_alternatives"]) > 0
        # 현재 6월 초/성인 수박, 하우스감귤, 감자, 애플망고 등이 대안 목록에 포함되어야 함
        assert any(crop in res["recommended_alternatives"] for crop in ["수박", "하우스감귤", "감자", "애플망고"])

    def test_summer_house_citrus_normality(self):
        """여름철 하우스감귤 출하 정상 판정 및 오배송 단정 금지 검증 (§5 규칙 ⑨)"""
        # 1. 하우스감귤 여름철 정상 여부 함수
        assert is_summer_house_citrus_normal(6) is True
        assert is_summer_house_citrus_normal(7) is True
        assert is_summer_house_citrus_normal(8) is True
        assert is_summer_house_citrus_normal(1) is False  # 1월은 휴식/종료 구간

        # 2. 여름철 하우스감귤 문의 평가
        res = evaluate_season_inquiry("하우스감귤", query_type="summer_citrus")
        assert res["rule_no"] == 9
        assert res["is_summer_citrus_normal"] is True
        assert "시설 난방 재배" in res["guide_message"]
        assert "성수기" in res["guide_message"]
        assert "오배송·사칭으로 임의 단정 절대 금지" in res["restriction"]

    def test_ten_operational_rules(self):
        """10대 업무 처리 기준 핵심 가드레일 상황별 검증 (§5)"""
        # 규칙 ②: "언제 들어와요" -> 월 단위까지만 안내, 확정일 약속 금지
        res_when = evaluate_season_inquiry("노지감귤", query_type="when")
        assert res_when["rule_no"] == 2
        assert "개시 월인 11월까지만" in res_when["guide_message"]
        assert "확정 입고일·도착일 약속 절대 금지" in res_when["restriction"]

        # 규칙 ③: 조기 출하 요구 -> 덜 익은 것 조기 수확/출하 불가
        res_early = evaluate_season_inquiry("노지감귤", query_type="early_harvest")
        assert res_early["rule_no"] == 3
        assert "미숙 개체를 골라 보내드리는 것 또한 불가" in res_early["guide_message"]
        assert '"덜 익은 것 골라서" 접수 절대 금지' in res_early["restriction"]

        # 규칙 ④: 예약 라인 (청귤 6월) -> 예약 접수 진행, 출고일 확정 금지
        res_rsv = evaluate_season_inquiry("청귤")
        assert res_rsv["rule_no"] == 4
        assert res_rsv["is_reservation_only"] is True
        assert "출고일 확정 표현 절대 금지" in res_rsv["restriction"]

        # 규칙 ⑧: 다른 시즌 가격 근거 할인 요구 -> 하우스 난방비 발생, 할인 불가
        res_disc = evaluate_season_inquiry("하우스감귤", query_type="discount_request")
        assert res_disc["rule_no"] == 8
        assert "난방·관리 부하 발생" in res_disc["guide_message"]
        assert "임의 할인 및 지난 시즌 가격 약속 절대 금지" in res_disc["restriction"]

        # 규칙 ⑩: 시즌 밖 기수령 상품 보관/안전 문의 -> 무관하게 안내 제공
        res_storage = evaluate_season_inquiry("감자", query_type="out_of_season_storage")
        assert res_storage["rule_no"] == 10
        assert "보관법 및 섭취 안전 안내는 그대로" in res_storage["guide_message"]
        assert '"지금은 시즌이 아니라 확인이 어렵습니다" 식의 응대 거절 절대 금지' in res_storage["restriction"]

    def test_2037_transitions_and_upcoming(self):
        """2037년 실제 전환일(SEA-01~10) 및 차기 예정(SEA-12) 무결성 검증 (시트 6, 7)"""
        assert len(SEASON_2037_TRANSITIONS) == 10
        assert SEASON_2037_TRANSITIONS["SEA-01"]["date"] == "03-02(월)"
        assert "봄감자 수확 개시" in SEASON_2037_TRANSITIONS["SEA-01"]["fact"]
        assert SEASON_2037_TRANSITIONS["SEA-04"]["date"] == "05-14(목)"
        assert "하우스감귤 초물 출하" in SEASON_2037_TRANSITIONS["SEA-04"]["fact"]
        assert SEASON_2037_TRANSITIONS["SEA-10"]["date"] == "06-20(토)"
        assert "수박 시즌 본격 오픈" in SEASON_2037_TRANSITIONS["SEA-10"]["fact"]

        assert "SEA-12" in SEASON_2037_UPCOMING
        assert SEASON_2037_UPCOMING["SEA-12"]["expected_date"] == "11-18(수)"
        assert "절임배추" in SEASON_2037_UPCOMING["SEA-12"]["plan"]

    def test_season_calendar_policy_router(self):
        """시즌 캘린더 관련 다양한 사용자 발화 라우팅 및 지식 주입 검증"""
        queries = [
            ("노지감귤 언제 들어와요? 지금 품절인가요?", "시즌 종료", "품절"),
            ("여름인데 하우스감귤이 왜 있어요? 사칭 아닌가요?", "하우스감귤", "성수기"),
            ("수박 지금 살 수 있나요? 출하 언제 하나요?", "수박", "초입"),
            ("청귤 예약 접수 언제부터 받나요?", "청귤", "예약 접수"),
            ("애플망고 지금 제철인가요?", "애플망고", "성수기"),
            ("교동마을 농산 시즌 캘린더 확인 부탁드립니다", "농산 시즌 캘린더", "가드레일"),
        ]
        for query, expected_keyword_1, expected_keyword_2 in queries:
            res = PolicyRouter.route(query)
            assert res.primary_category == PolicyCategory.SEASON_CALENDAR, f"라우팅 실패: {query} -> {res.primary_category}"
            assert len(res.knowledge_text) <= 400, f"지식 텍스트 400자 초과: {len(res.knowledge_text)}자"
            assert expected_keyword_1 in res.knowledge_text, f"{expected_keyword_1} 누락: {res.knowledge_text}"
            assert expected_keyword_2 in res.knowledge_text, f"{expected_keyword_2} 누락: {res.knowledge_text}"

    def test_seafood_season_matrix_accuracy(self):
        """갯마을 수산 성어기 공급표 정본 검증: 옥돔(9월 초, 10~2월 성, 3~8월 말), 갈치(8~11월 성, 7월 초, 12~6월 말)"""
        from app.knowledge.rules import (
            SEAFOOD_SEASON_LINES,
            SeasonStatus,
            get_seafood_season_status,
        )

        okd = SEAFOOD_SEASON_LINES["OKD"]
        assert okd.monthly_statuses[9] == SeasonStatus.EARLY  # 9월 초
        for m in (10, 11, 12, 1, 2):
            assert okd.monthly_statuses[m] == SeasonStatus.PEAK  # 10~2월 성
        for m in (3, 4, 5, 6, 7, 8):
            assert okd.monthly_statuses[m] == SeasonStatus.LATE  # 3~8월 말

        assert get_seafood_season_status("OKD", 9) == SeasonStatus.EARLY
        assert get_seafood_season_status("옥돔", 10) == SeasonStatus.PEAK
        assert get_seafood_season_status("제주 옥돔", 5) == SeasonStatus.LATE

        gal = SEAFOOD_SEASON_LINES["GAL"]
        assert gal.monthly_statuses[7] == SeasonStatus.EARLY  # 7월 초
        for m in (8, 9, 10, 11):
            assert gal.monthly_statuses[m] == SeasonStatus.PEAK  # 8~11월 성
        for m in (12, 1, 2, 3, 4, 5, 6):
            assert gal.monthly_statuses[m] == SeasonStatus.LATE  # 12~6월 말

    def test_agri_season_ngl_matrix_accuracy(self):
        """노지감귤 온주밀감(NGL) 계절표 정본 검증: 10월 전, 11월 초, 12~1월 성, 2월 말"""
        from app.knowledge.rules import AGRI_SEASON_LINES, SeasonStatus

        ngl = AGRI_SEASON_LINES["NGL"]
        assert ngl.monthly_statuses[10] == SeasonStatus.BEFORE  # 10월 전 (출하 전)
        assert ngl.monthly_statuses[11] == SeasonStatus.EARLY   # 11월 초 (초입)
        assert ngl.monthly_statuses[12] == SeasonStatus.PEAK    # 12월 성 (성수기)
        assert ngl.monthly_statuses[1] == SeasonStatus.PEAK     # 1월 성 (성수기)
        assert ngl.monthly_statuses[2] == SeasonStatus.LATE     # 2월 말 (시즌 말)
        for m in (3, 4, 5, 6, 7, 8, 9):
            assert ngl.monthly_statuses[m] == SeasonStatus.CLOSED  # 3~9월 종 (시즌 종료)





