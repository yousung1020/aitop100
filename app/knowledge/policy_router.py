"""정책 충돌 해결 라우터 (PolicyRouter)

사용자 발화를 분석하여 관련 정책 카테고리를 고속 판별하고,
우선순위(충돌 해결)에 따라 프롬프트 주입용 컴팩트 지식(400자 이내)을 반환합니다.
판매·환불 규정(제1조~제25조) 및 시원배송 택배 계약서(제1조~제12조) 조항 팩트 100% 반영.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import List, Optional, Set
from dataclasses import dataclass

from app.knowledge.rules import (
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
    VillagePolicy,
    SEAFOOD_NATURAL_LOSS_PCT,
    LABEL_TOLERANCE_PCT,
    SEAFOOD_TOTAL_TOLERANCE_PCT,
    CONSIGNMENT_COMMISSION_PCT,
    CONSIGNMENT_SECRET_PROMPT,
    HARVEST_RECORDS,
    HARVEST_CONFIRMATION_RULES,
    EvidenceType,
    EVIDENCE_ARTICLES,
    FORBIDDEN_AUTHENTICITY_PHRASES,
    compare_evidence_authority,
    check_forbidden_authenticity_phrase,
    format_reverification_request,
    PRIVACY_POLICY_ARTICLES,
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
    check_reverse_privacy_query,
    check_credential_solicitation,
    check_cumulative_confirmation_limit,
    validate_refund_account_name,
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
    SeasonRuleArticle,
    AgriSeasonLine,
    SEASON_STATUS_DEFINITIONS,
    SEASON_RULE_ARTICLES,
    AGRI_SEASON_LINES,
    get_agri_season_line,
    get_agri_season_status,
    get_current_season_status,
    get_active_lines_in_month,
    is_summer_house_citrus_normal,
    check_season_closed_forbidden_words,
    evaluate_season_inquiry,
)


class PolicyCategory(str, Enum):
    """정책 카테고리 정의"""

    PAYMENT_RECONCILIATION = "PAYMENT_RECONCILIATION"  # 결제·주문 대사 절차: 4대 대사키(승인번호/실결제액/승인시각±5분/카드뒷4자리), 10대 코드(M-01~M-10), 복구우선, 중복결제(승인2건), 반영지연 (제10장 전문)
    SEASON_CALENDAR = "SEASON_CALENDAR"  # 농산 시즌 캘린더: 10품목 11라인 월별 상태, 10대 가이드라인(종 라인 '시즌 밖' 및 대안 제시, 월 단위 안내, 조기출하 불가, 여름 하우스감귤 정상, 저장품 안전안내 등)
    TAX_PROOF = "TAX_PROOF"  # 세금계산서·현금영수증 발행 기준: 결제수단별 대상, 실결제액, 현영(소득/지출/선낭독금지/익월10일), 세금계산서(면세0원/배송비과세분리/타사명의거절), TX-01~06, 환불증빙, 7대거절 (1~7번 전문)
    PICKUP = "PICKUP"  # 산지 픽업 안내: 사전예약 필수(1영업일전), 집하장 1곳(밭/하우스 불가), 오전운영(상차시간 미운영), 온라인결제 한정, 사전대리인, 인수후 고객책임(품온상승 하자불가), 배송비 0원, 현장인수거절권 (1~5번 전문)
    SUBSCRIPTION = "SUBSCRIPTION"  # 정기배송(구독) 약관: 컷오프(3영업일전 24시), 스킵(한도없음), 해지(위약금0원/전액환불), 변경 (약관 제1조~제11조)
    COMBINED = "COMBINED"  # 복합 주문 및 합포장 불가 (계약서 제6조)
    SUGAR = "SUGAR"  # 당도 보장 11브릭스 (규정 제7조)
    WEIGHT = "WEIGHT"  # 무게/규격 허용오차 ±5% (규정 제6조)
    SEAFOOD_WEIGHT = "SEAFOOD_WEIGHT"  # 수산물 중량·자연감량 8% 판정선 (수산물 중량 세칙 제1조~제12조)
    DISPOSAL = "DISPOSAL"  # 폐기 vs 보관 및 섭취이상 손해배상 (규정 제5조, 제25조)
    SPOILED = "SPOILED"  # 상함 책임 50% 배분 (규정 제10조)
    RETURN_REFUND = "RETURN_REFUND"  # 단순변심 7일/원결제수단 환불 (규정 제11조, 제12조, 제20조)
    CLAIM = "CLAIM"  # 파손/하자/고객선택권 (규정 제4조, 계약서 제11조, 제12조)
    TRACKING = "TRACKING"  # 송장 조회 3~5시간 / 당일배송 불가 익일~모레 (계약서 제3조, 제4조)
    ADDRESS = "ADDRESS"  # 집하 전/후 배송지 변경 및 취소 (계약서 제3조, 제10조)
    SPLIT_SHIPPING = "SPLIT_SHIPPING"  # 분할 배송 최대 3회 7일 이내 (계약서 제8조)
    SHIPPING = "SHIPPING"  # 배송비 및 도서산간 면제
    WEATHER = "WEATHER"  # 기상 악화(풍랑주의보/폭설) 지연 (계약서 제4조)
    BULK = "BULK"  # 대량/단체 주문 분할배차 (계약서 제5조)
    AUTH = "AUTH"  # 계정/로그인/본인인증
    ESCALATE = "ESCALATE"  # 상담원(이민준) 이관
    FUTURE_PROMISE = "FUTURE_PROMISE"  # 미래 선약속 금지 및 배송비 쿠폰 대체 (제7조)
    PAST_PROMISE = "PAST_PROMISE"  # 과거 약속 이력 조회 및 정정/보정 (제8조)
    LEGAL_DISPUTE = "LEGAL_DISPUTE"  # 분쟁·법률·언론 즉시 이관 레인 ② (제5조)
    COMPENSATION_CLAIM = "COMPENSATION_CLAIM"  # 손해배상(병원비) 정식 이관 레인 ③ (제5조, 제25조)
    DISCRETION = "DISCRETION"  # 5만원 재량 한도 및 권한 위임 (제4조, 제5조)
    DELEGATION_APPROVAL = "DELEGATION_APPROVAL"  # 승인 절차(3일) 및 인적 서열(에이전트->이민준->고길동) (제6조, 제10조)
    PARTNER_CLAIM = "PARTNER_CLAIM"  # 위탁 상품 품질 책임 및 홍이장 경유 (제5조, 제10조)
    CONSIGNMENT_SECRET = "CONSIGNMENT_SECRET"  # 위탁 수수료율 20%/정산구조 고객 대외비 준수 (계약서 제17조)
    HARVEST_STATUS = "HARVEST_STATUS"  # 갯마을 조업·입고 이력 및 06-30 갈치 품절 사유 (조업기록)
    NO_AUTHENTICITY_CHECK = "NO_AUTHENTICITY_CHECK"  # 진위 감정 절대 금지 (AI/조작 의심 발언 금지, 규정 제6조, 제7조)
    EVIDENCE_HIERARCHY = "EVIDENCE_HIERARCHY"  # 증빙 구분 및 권위 서열 (자사기록/제3자 > 제출물 > 구술, 규정 제2조~제5조)
    IDENTITY_CLAIM = "IDENTITY_CLAIM"  # 채팅 신원 주장 (협찬/리뷰단/조합원 - 시스템 등록 기록만 인정, 규정 제9조)
    REVERIFICATION = "REVERIFICATION"  # 재검증 요청 표준 (대조 결과 근거 & 1장 계측 촬영, 규정 제8조, 제14조)
    CROP_DISASTER = "CROP_DISASTER"  # 교동마을 작황·재해 이력 및 7대 기록 확인 기준
    LOGISTICS_CANCELLATION = "LOGISTICS_CANCELLATION"  # 시원배송 결항·집하 이력 및 태풍 구간 상세 타임라인 (기록 확인 기준)
    UNHANDLED_ITEM = "UNHANDLED_ITEM"  # 교동마을 미취급 품목 안내 (당근 등 애초에 없는 품목)
    # 개인정보 보호 및 상담 창구 7대 보안 가드레일 (방침 제1조~제25조)
    PRIVACY_VERIFICATION = "PRIVACY_VERIFICATION"  # 본인확인 방향(고객 제시->대조) 및 저장정보 역질문 차단 (제9조, 제10조)
    PRIVACY_CUMULATIVE = "PRIVACY_CUMULATIVE"  # 스무고개 누적 확인 중단 3회 상한 (제11조)
    PRIVACY_THIRD_PARTY = "PRIVACY_THIRD_PARTY"  # 타인 명의/주문 조회 절대 차단 (제12조, 제16조)
    PRIVACY_CREDENTIAL = "PRIVACY_CREDENTIAL"  # 비밀번호·OTP 수집 절대 금지 (제5조, 제13조)
    PRIVACY_REFUND_ACCOUNT = "PRIVACY_REFUND_ACCOUNT"  # 무통장 환불 계좌 원결제자 본인 명의 일치 (제14조)
    PRIVACY_SELLER_INFO = "PRIVACY_SELLER_INFO"  # 판매자 공시 정보 범위 한정 (제17조)
    PRIVACY_FARM_INFO = "PRIVACY_FARM_INFO"  # 공급 농가 개인정보 비공개 및 조합 대행 (제18조)
    PRIVACY_DATA_RIGHTS = "PRIVACY_DATA_RIGHTS"  # 열람·정정·삭제 요구 10일 이내 회신 및 법정보존(5년/3년) 제한 (제20조, 제21조)
    PRIVACY_EXTERNAL_REQUEST = "PRIVACY_EXTERNAL_REQUEST"  # 기관/언론 대외 요청 공문/영장 필수 및 이관 (제19조)
    PRIVACY_GROUP_COLLECTION = "PRIVACY_GROUP_COLLECTION"  # 단체 체험 문의 최소수집 원칙 (제15조)
    PRIVACY_GENERAL = "PRIVACY_GENERAL"  # 개인정보 처리방침 일반 문의 (제1조~제25조)
    AGRICULTURE = "AGRICULTURE"  # 교동마을 농산물 규정
    FISHERY = "FISHERY"  # 갯마을 수산물 규정
    GENERAL = "GENERAL"  # 일반 문의


@dataclass(frozen=True)
class PolicyRouteResult:
    """정책 라우팅 결과 컨테이너"""

    primary_category: PolicyCategory
    matched_categories: List[PolicyCategory]
    is_combined: bool
    has_agriculture: bool
    has_fishery: bool
    knowledge_text: str


class PolicyRouter:
    """사용자 질의 분석 및 정책 라우팅 엔진"""

    AGRI_PATTERNS = [
        r"감귤", r"귤", r"하우스감귤", r"하우스\s*감귤", r"노지감귤", r"만감류", r"한라봉", r"천혜향", r"타이벡",
        r"수박", r"멜론", r"애플망고", r"참다래", r"감자", r"고구마", r"절임배추",
        r"농산물", r"과일", r"채소", r"밭작물", r"선과장",
        r"작목반", r"교동",
    ]

    FISH_PATTERNS = [
        r"갈치", r"은갈치", r"당일바리", r"옥돔", r"고등어",
        r"자반고등어", r"자반", r"소라", r"활소라", r"굴비",
        r"참굴비", r"수산물", r"생선", r"어패류", r"어판장",
        r"갯마을", r"해동", r"녹아", r"녹았",
    ]

    COMBINED_PATTERNS = [
        r"합포장", r"같이\s*포장", r"한\s*박스", r"한\s*상자",
        r"한박스", r"한상자", r"묶음", r"묶어서", r"함께\s*배송",
        r"같이\s*배송", r"같이\s*보내", r"함께\s*보내", r"따로\s*오",
        r"따로\s*배송", r"분리\s*배송", r"따로따로", r"박스가\s*두\s*개",
        r"박스가\s*따로", r"합배송",
    ]

    SUGAR_PATTERNS = [
        r"당도", r"브릭스", r"brix", r"달지\s*않", r"안\s*달아",
        r"싱거", r"신맛", r"산도", r"맛이\s*없", r"당도선별", r"당도\s*보장",
        r"11브릭스", r"12브릭스", r"배제\s*로트", r"미달\s*로트",
    ]

    WEIGHT_PATTERNS = [
        r"무게", r"중량", r"키로", r"kg", r"그램",
        r"저울", r"오차", r"미달", r"부족", r"덜\s*나",
        r"규격", r"특대", r"이상", r"허용오차",
    ]

    DISPOSAL_PATTERNS = [
        r"폐기", r"버려", r"버릴", r"보관\s*촬영", r"보관\s*해야", r"보관하",
        r"상품\s*보관", r"곰팡이", r"이물", r"벌레", r"섭취\s*후", r"먹고\s*나",
        r"탈\s*났", r"배탈", r"병원", r"병원비", r"진단서", r"손해배상",
        r"위생",
    ]

    SPOILED_PATTERNS = [
        r"상함", r"상했", r"썩음", r"썩었", r"변질",
        r"책임\s*배분", r"50%", r"반반", r"상온\s*방치",
        r"보관\s*과실", r"출고\s*하자",
    ]

    TRACKING_PATTERNS = [
        r"송장", r"운송장", r"조회", r"당일배송", r"언제\s*도착",
        r"도착일", r"출고\s*언제", r"배송\s*소요", r"익일",
        r"모레", r"배송조회", r"택배조회",
    ]

    SPLIT_PATTERNS = [
        r"분할\s*배송", r"나눠서\s*배송", r"따로\s*받", r"나눠\s*받",
        r"회차", r"3회",
    ]

    SHIPPING_PATTERNS = [
        r"배송비", r"배송료", r"택배비", r"무료\s*배송", r"운임",
        r"도서산간", r"제주도\s*배송", r"섬\s*지역", r"추가\s*배송비",
        r"추가\s*운임", r"항공료", r"도선료",
    ]

    CLAIM_PATTERNS = [
        r"환불", r"반품", r"교환", r"취소", r"파손",
        r"하자", r"터짐", r"터져", r"터졌", r"짓무름",
        r"짓물", r"깨짐", r"부서", r"박스\s*훼손", r"포장\s*훼손",
        r"선택", r"재배송",
    ]

    RETURN_REFUND_PATTERNS = [
        r"단순\s*변심", r"변심", r"마음\s*바", r"환불\s*계좌",
        r"원결제", r"타인\s*계좌", r"계좌\s*변경", r"카드\s*취소",
        r"7일", r"기한", r"미개봉",
    ]

    WEATHER_PATTERNS = [
        r"풍랑", r"주의보", r"폭설", r"대설", r"한파",
        r"태풍", r"바람", r"파도", r"결항", r"지연",
        r"날씨", r"기상",
    ]

    BULK_PATTERNS = [
        r"대량", r"단체", r"10박스", r"20박스", r"30박스",
        r"50박스", r"100박스", r"대량\s*구매", r"단체\s*주문",
        r"견적", r"도매", r"기업\s*선물", r"선물\s*세트",
    ]

    ADDRESS_PATTERNS = [
        r"배송지", r"주소", r"주소지", r"수령지", r"배송처",
        r"집하", r"출고\s*전", r"주소\s*변경", r"배송지\s*변경",
    ]

    AUTH_PATTERNS = [
        r"로그인", r"비번", r"비밀번호", r"계정", r"본인인증",
        r"인증", r"인증번호", r"회원가입", r"아이디",
    ]

    ESCALATE_PATTERNS = [
        r"상담원", r"상담사", r"사람\s*연결", r"직원", r"이민준",
        r"전화", r"통화", r"유선", r"관리자", r"담당자",
    ]

    FUTURE_PROMISE_PATTERNS = [
        r"다음\s*주문", r"다음에\s*주문", r"다음번", r"차회", r"다음에도",
        r"선약속", r"다음에\s*무료배송", r"다음\s*주문\s*무료", r"다음\s*구매",
        r"다음에\s*살\s*때", r"다음에\s*시킬\s*때", r"다음번\s*배송비",
    ]

    PAST_PROMISE_PATTERNS = [
        r"과거\s*상담", r"이전\s*상담", r"지난번\s*상담", r"저번\s*상담",
        r"상담원이\s*약속", r"약속했잖아", r"약속했었", r"해준다고\s*했",
        r"무료배송\s*해준다고", r"과거\s*이력", r"이력\s*확인", r"과잉\s*약속",
        r"상담\s*기록\s*확인", r"이전\s*기록\s*확인", r"약속\s*기록", r"상담\s*이력",
    ]

    LEGAL_DISPUTE_PATTERNS = [
        r"소송", r"고소", r"고발", r"변호사", r"법적", r"법률",
        r"소비자원", r"소비자보호원", r"신문고", r"기자", r"언론",
        r"언론\s*제보", r"기자\s*제보", r"방송\s*제보", r"뉴스", r"방송",
        r"공론화", r"인터넷에\s*올", r"커뮤니티", r"고발하",
    ]

    COMPENSATION_CLAIM_PATTERNS = [
        r"병원비", r"치료비", r"약값", r"진단서", r"손해배상",
        r"합의금", r"위자료", r"응급실", r"입원", r"통원",
    ]

    DELEGATION_APPROVAL_PATTERNS = [
        r"승인\s*절차", r"승인\s*단계", r"인적\s*서열", r"결재권자",
        r"영업일\s*3일", r"무응답", r"대체\s*경로", r"조합장\s*직통",
        r"박민아", r"3단계", r"승인권자",
    ]

    DISCRETION_PATTERNS = [
        r"재량", r"5만원", r"50000원", r"오만원", r"권한\s*위임",
        r"재량\s*한도", r"금액\s*임계", r"임계값", r"재량\s*범위",
    ]

    PARTNER_CLAIM_PATTERNS = [
        r"위탁\s*상품", r"갯마을\s*품질", r"홍이장", r"공급\s*측\s*협의",
    ]

    CONSIGNMENT_SECRET_PATTERNS = [
        r"수수료", r"수수료율", r"20%", r"판매\s*대행", r"정산\s*구조",
        r"분담\s*비율", r"얼마나\s*남겨", r"얼마나\s*떼", r"몇\s*프로\s*떼",
        r"마진", r"내부\s*정산", r"계약\s*조건", r"위탁\s*계약", r"선지급분",
        r"정산\s*계약", r"정산\s*조건",
    ]

    SEAFOOD_WEIGHT_PATTERNS = [
        r"자연감량", r"빙장수", r"(?<![합립시])드립(?!니다)", r"글레이징", r"얼음물", r"물기",
        r"8%", r"3%", r"수산물\s*중량", r"수산물\s*재촬영",
    ]

    HARVEST_PATTERNS = [
        r"조업", r"입고", r"어획", r"갈치\s*품절", r"옥돔\s*재고",
        r"비성어기", r"06-30", r"6월\s*30일", r"오늘\s*갈치", r"갈치\s*언제",
        r"특보\s*해제", r"06-21", r"6월\s*21일", r"06-24", r"6월\s*24일",
        r"조업\s*중단", r"품절\s*사유", r"왜\s*품절", r"갈치\s*왜",
        r"조업\s*이력", r"성어기",
    ]

    NO_AUTHENTICITY_PATTERNS = [
        r"진위", r"진짜\s*맞", r"가짜\s*사진", r"조작", r"합성",
        r"AI", r"인공지능", r"색칠", r"색을\s*칠", r"포토샵",
        r"만들어낸", r"조작된", r"과잉\s*검증", r"개봉\s*영상",
        r"개봉영상", r"박스\s*개봉", r"영수증\s*요구", r"사진\s*더\s*보내",
        r"의심",
    ]

    EVIDENCE_HIERARCHY_PATTERNS = [
        r"증빙", r"권위\s*서열", r"증빙\s*서열", r"증빙의\s*구분",
        r"제3자\s*발행", r"시험성적서", r"성적서", r"자사\s*기록",
        r"당사자\s*제출", r"구술", r"구두\s*진술", r"경험담",
        r"신뢰도", r"팩스", r"사진이라서", r"이미지라",
        r"정합\s*대조", r"객관적\s*대조", r"사칭\s*제보", r"가짜\s*행사",
        r"제보\s*접수", r"추가\s*증빙\s*요구",
    ]

    IDENTITY_CLAIM_PATTERNS = [
        r"인플루언서", r"리뷰단", r"체험단", r"협찬", r"무상\s*제공",
        r"조합원\s*자격", r"조합원\s*할인", r"블로거", r"유튜버",
        r"협찬\s*대상", r"신원\s*주장", r"자격\s*확인",
    ]

    REVERIFICATION_PATTERNS = [
        r"재검증", r"재촬영", r"다시\s*찍", r"다시\s*확인",
        r"계측값", r"한\s*화면", r"1장", r"한\s*장",
        r"불일치\s*신호", r"배송\s*중인데", r"라벨\s*기한",
        r"원물\s*보관", r"원물\s*폐기하지",
    ]

    UNHANDLED_ITEM_PATTERNS = [
        r"당근", r"흙당근", r"제주\s*흙당근", r"제주당근", r"당근주스",
    ]

    CROP_DISASTER_PATTERNS = [
        r"작황", r"재해", r"도복", r"낙과", r"열과", r"숙도", r"당도\s*진행",
        r"봄비", r"태풍", r"강풍경보", r"풍랑경보", r"호우경보", r"호우주의보", r"정체전선",
        r"누적\s*강수", r"집중호우", r"일조시간", r"사후\s*점검", r"사후\s*확인",
        r"애플망고\s*지연", r"애플망고\s*숙도", r"애플망고\s*출고",
        r"수박\s*열과", r"수박\s*지체", r"수박\s*예약분",
        r"03-28", r"06-02", r"06-04", r"06-05", r"06-06", r"06-07", r"06-08",
        r"06-18", r"06-25", r"06-27", r"06-28", r"06-29",
        r"WX-01", r"WX-02", r"작황.*물류", r"물류.*작황", r"특보.*해제.*출고", r"특보.*해제",
        r"생산자\s*라인업", r"생산자\s*품목", r"하동철",
    ]

    LOGISTICS_CANCELLATION_PATTERNS = [
        r"시원배송.*결항", r"결항.*시원배송",
        r"간선\s*결항", r"간선\s*중단", r"간선\s*재개",
        r"집하\s*취소", r"집하\s*보류", r"집하\s*재개",
        r"송장\s*번호\s*생성", r"송장.*등록.*집하.*전", r"송장만\s*등록",
        r"송장.*배송\s*시작", r"송장.*배송\s*개시",
        r"03-28.*감자", r"감자.*03-28", r"감자.*출고.*지연", r"감자.*오전.*지연",
        r"06-05.*태풍", r"태풍.*06-05", r"06-05.*송장", r"06-05.*결항",
        r"06-06.*결항", r"06-07.*간선", r"06-08.*집하",
        r"운송편\s*결항", r"결항·집하", r"결항\s*집하", r"결항\s*기록", r"TR-KD-01",
        r"구방만.*기록", r"구방만.*결항", r"구방만.*집하",
        r"태풍\s*구간.*결항", r"태풍.*타임라인",
    ]

    # 개인정보 보호 및 7대 보안 가드레일 패턴 (방침 제1조~제25조)
    PRIVACY_VERIFICATION_PATTERNS = [
        r"(등록된|저장된|거기|제)\s*(주소|주소지|도로명|집주소|전화번호|연락처|번호|이름|성함|나이|생년월일|정보).*(불러|알려|말해|확인해|읽어)\s*(주세요|봐요|줘요|달라|주실래요|주시겠어요|줄래)",
        r"(주소|전화번호|연락처|이름|나이).*(불러|읽어)\s*(주세요|봐요|줘요|달라|주실래요)",
        r"몇\s*살로\s*(되어|저장|등록)",
        r"어디로\s*(되어|저장|등록)",
        r"제\s*(주소|전화번호|이름|정보가)\s*(뭐로|어떻게)",
        r"등록된\s*주소",
        r"저장된\s*주소",
        r"본인확인\s*방향", r"확인\s*방향", r"저장정보\s*역질문", r"역질문",
        r"먼저\s*(읽어|불러)", r"정보\s*대조",
    ]

    PRIVACY_CUMULATIVE_PATTERNS = [
        r"스무고개", r"누적\s*확인", r"예\s*아니오", r"예·아니오",
        r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)\s*(사시|살고|맞으|맞죠)",
        r"(구|동|읍|면|리|로|길)\s*(맞으|맞죠|사시)",
        r"(010|02|031|032|033|041|042|043|051|052|053|054|055|061|062|063|064)\s*(맞으|맞죠)",
        r"3회\s*누적", r"누적\s*3회", r"좁혀지는\s*흐름",
    ]

    PRIVACY_THIRD_PARTY_PATTERNS = [
        r"(남편|아내|와이프|친구|가족|부모님|엄마|아빠|형|누나|동생|지인|대리|동료|다른\s*사람).*(주문|내역|배송|주소|정보|조회)",
        r"타인\s*(명의|주문|정보|조회|배송)",
        r"대신.*(조회|확인|물어|알려)",
        r"주문번호.*(아는데|알고\s*있는데|알면|알려주면).*(남편|아내|타인|다른|친구|가족)",
        r"주문번호\s*알면\s*조회",
        r"(기사|택배기사|배송기사|구방만).*?(휴대전화|전화번호|핸드폰|연락처|번호)",
        r"(공동구매|공구).*?(명단|참여자|연락처|전화번호|송장|운송장)",
        r"선물.*?(주소|상세주소|몇\s*호)",
        r"친구\s*집.*?(상세주소|주소|몇\s*호)",
    ]

    PRIVACY_CREDENTIAL_PATTERNS = [
        r"비밀번호.*(알려|불러|입력|드릴|받아|적어|보내|대신)",
        r"비번.*(알려|불러|입력|드릴|받아|적어|보내|대신)",
        r"(인증번호|OTP|otp).*(알려|불러|입력|드릴|받아|적어|보내|왔는|대신)",
        r"(비밀번호|비번|인증번호|OTP|otp)\s*(요구|수집)",
        r"자격증명",
        r"비번은\s*[^\s]+",
        r"비밀번호는\s*[^\s]+",
        r"otp는\s*[^\s]+",
        r"인증번호는\s*[^\s]+",
        r"비밀번호\s*알려드릴",
        r"비번\s*알려드릴",
        r"비번\s*\d+",
        r"비밀번호\s*\d+",
    ]

    PRIVACY_REFUND_ACCOUNT_PATTERNS = [
        r"환불\s*계좌", r"계좌이체\s*환불", r"무통장\s*환불", r"예금주",
        r"(다른\s*사람|가족|남편|아내|타인).*(통장|계좌).*(환불|입금)",
        r"(남편|아내|가족|타인|다른\s*사람)\s*(계좌|통장)",
        r"환불\s*계좌\s*명의", r"환불\s*계좌\s*파기",
    ]

    PRIVACY_SELLER_INFO_PATTERNS = [
        r"판매자\s*정보", r"사업자\s*정보", r"사업자정보\s*공시",
        r"매입가", r"계약\s*조건", r"대표자\s*(가족|배경|사생활|개인)",
        r"알려줄\s*수\s*있는\s*모든\s*정보",
    ]

    PRIVACY_FARM_INFO_PATTERNS = [
        r"농가.*(연락처|전화번호|주소|번호|위치)",
        r"생산자.*(연락처|전화번호|주소|개인\s*번호)",
        r"농민.*(연락처|전화번호|번호|주소)",
        r"농가에\s*직접\s*(연락|전화|찾아)",
        r"농가\s*스토리", r"농가\s*이야기",
    ]

    PRIVACY_DATA_RIGHTS_PATTERNS = [
        r"개인정보.*(삭제|열람|정정|처리정지|지워|지우|폐기|없애)",
        r"내\s*정보.*(삭제|지워|지우|폐기|없애)",
        r"회원\s*탈퇴.*삭제", r"탈퇴.*개인정보",
        r"영업일\s*10일", r"10일\s*이내",
        r"전자상거래법\s*(5년|3년)", r"법정\s*보존", r"보존\s*기간",
        r"삭제\s*요구.*(거절|거부|제한)", r"삭제\s*(거부|제한)",
    ]

    PRIVACY_EXTERNAL_REQUEST_PATTERNS = [
        r"기자\s*인데", r"방송국\s*(취재|기자|인데)",
        r"(경찰|검찰|구청|시청|세무서|기관)\s*(에서|인데)",
        r"공문\s*없이.*(명단|정보|자료)",
        r"전화로.*(명단|정보|피해)",
        r"(고객\s*명단|피해\s*현황|고객들\s*명단).*(알려|달라|제공|보내|내놔|주세요)",
        r"(언론|기관).*(대외\s*요청|명단\s*제공)",
    ]

    PRIVACY_GROUP_COLLECTION_PATTERNS = [
        r"단체\s*체험\s*명단", r"참가자\s*(명단|생년월일|주민번호|성별)",
        r"학생들\s*(명단|생년월일|성별)", r"명단\s*미리", r"최소\s*수집",
    ]

    PRIVACY_GENERAL_PATTERNS = [
        r"개인정보\s*처리방침", r"개인정보\s*보호", r"개인정보\s*방침",
        r"개인정보\s*규정", r"개인정보\s*처리\s*원칙",
    ]

    # 정기배송(구독) 약관 패턴 (제1조~제11조)
    SUBSCRIPTION_PATTERNS = [
        r"정기배송", r"정기구독", r"구독",
        r"회차", r"컷오프", r"cut-off", r"cutoff",
        r"스킵", r"건너뛰기", r"쉬어가기", r"회차\s*스킵", r"이번\s*회차", r"다음\s*회차",
        r"구독\s*해지", r"정기배송\s*해지", r"구독\s*취소", r"정기배송\s*취소",
        r"남은\s*회차", r"위약금", r"할인\s*소급", r"구독\s*변경", r"주기\s*변경",
        r"배송\s*주기", r"품목\s*변경", r"수량\s*변경", r"회차\s*마감일",
        r"구독\s*상태", r"결제\s*예정일", r"3영업일\s*전",
    ]

    # 산지 픽업 안내 패턴 (1~5번 전문)
    PICKUP_PATTERNS = [
        r"픽업", r"산지\s*픽업", r"방문\s*수령", r"직접\s*수령", r"현장\s*수령",
        r"집하장\s*수령", r"밭에서\s*수령", r"밭으로\s*가서", r"하우스\s*수령",
        r"현장.*결제", r"현장.*주문", r"대리\s*수령", r"인수\s*거절",
        r"품온\s*상승", r"차량에\s*실", r"차량.*보관", r"차에\s*싣",
        r"픽업\s*예약", r"픽업\s*시간", r"픽업\s*장소", r"픽업\s*배송비",
        r"직접\s*가서", r"현장\s*방문", r"현장\s*확인", r"현장에\s*가서",
    ]

    # 세금계산서·현금영수증 발행 기준 패턴 (1~7번 전문)
    TAX_PROOF_PATTERNS = [
        r"세금계산서", r"현금영수증", r"지출증빙", r"소득공제",
        r"매출전표", r"카드전표", r"카드\s*영수증", r"영수증\s*발행",
        r"영수증.*(발행|신청|요청|끊어)", r"현금영수증.*(발행|신청|요청|번호|취소)",
        r"세금계산서.*(발행|신청|요청|명의|취소|재발행)",
        r"부가세", r"부가가치세", r"면세", r"과세", r"세액",
        r"세액이\s*0원", r"세액란", r"공란", r"세액이\s*없",
        r"배송비\s*과세", r"배송비\s*부가세", r"용역분", r"분리\s*기재",
        r"TX-01", r"TX-02", r"TX-03", r"TX-04", r"TX-05", r"TX-06",
        r"tx-01", r"tx-02", r"tx-03", r"tx-04", r"tx-05", r"tx-06",
        r"국세청\s*자율", r"자율\s*발급", r"홈택스", r"익월\s*10일",
        r"소급\s*발행", r"중복\s*증빙", r"명의\s*오류", r"실결제액.*증빙",
        r"사업자등록증.*(명의|대조|계산서)",
    ]

    # 결제·주문 대사 절차 및 10대 불일치 코드 패턴 (M-01 ~ M-10)
    PAYMENT_RECONCILIATION_PATTERNS = [
        r"결제\s*대사", r"주문\s*대사", r"결제.*대사", r"대사\s*키", r"대사키", r"4대\s*대사",
        r"M-01", r"M-02", r"M-03", r"M-04", r"M-05", r"M-06", r"M-07", r"M-08", r"M-09", r"M-10",
        r"m-01", r"m-02", r"m-03", r"m-04", r"m-05", r"m-06", r"m-07", r"m-08", r"m-09", r"m-10",
        r"승인번호", r"결제\s*승인\s*기록", r"승인\s*기록", r"승인\s*시각", r"승인시각",
        r"카드\s*뒷\s*4자리", r"카드\s*뒷자리", r"카드\s*뒷\s*자리", r"뒷\s*4자리",
        r"주문\s*유실", r"주문\s*레코드", r"주문\s*생성\s*실패", r"주문서가\s*생성",
        r"결제\s*문자", r"돈은\s*나갔", r"돈\s*빠져", r"결제는\s*됐", r"결제\s*됐는데\s*주문",
        r"승인\s*문자", r"돈만\s*빠져", r"결제만\s*되", r"결제만\s*됐",
        r"주문이\s*없", r"주문\s*내역이\s*없", r"주문서가\s*없", r"주문\s*내역.*없",
        r"중복\s*결제", r"중복\s*승인", r"승인\s*2건", r"결제\s*2건",
        r"반영\s*지연", r"시스템\s*반영\s*대기", r"일시적\s*미조회",
        r"타\s*계정\s*귀속", r"다른\s*계정.*주문",
        r"WTM-SEL-8", r"HGL-SEL-5", r"HGL-STD-5",
    ]

    # 농산 시즌 캘린더 패턴 (10품목·11라인 월별 상태 및 10대 업무 처리 가이드라인)
    SEASON_CALENDAR_PATTERNS = [
        r"시즌\s*캘린더", r"시즌\s*달력", r"출하\s*시기", r"출하\s*일정", r"출하\s*언제", r"언제\s*출하",
        r"언제\s*(들어와|나와|나옵|들어옵|수확|판매|살\s*수|구매)", r"언제\s*쯤", r"제철", r"시즌\s*종료",
        r"시즌\s*오프", r"시즌\s*아웃", r"시즌\s*초", r"성수기", r"초입", r"출하\s*예정",
        r"예약\s*접수", r"선접수", r"덜\s*익은\s*것", r"조기\s*출하", r"미숙과",
        r"여름.*(귤|감귤)", r"하우스감귤.*여름", r"하우스\s*감귤.*여름",
        r"지금.*(나오|살\s*수|나와|수확|출하|제철)",
        r"품절.*(대안|대체|언제|시즌|다시)", r"품절인가", r"품절인가요", r"품절이에요",
        r"수박.*(언제|출하|나와|제철|지금)", r"멜론.*(언제|출하|나와|제철|지금)",
        r"애플망고.*(언제|출하|나와|제철|지금)", r"청귤.*(언제|출하|나와|제철|예약|지금)",
        r"감자.*(언제|출하|나와|제철|지금|저장)", r"고구마.*(언제|출하|나와|제철|지금|저장)",
        r"참다래.*(언제|출하|나와|제철|지금|키위)", r"절임배추.*(언제|출하|나와|제철|예약)",
        r"노지감귤.*(언제|출하|나와|제철|지금)",
    ]

    @classmethod
    def _matches_any(cls, text: str, patterns: List[str]) -> bool:
        """주어진 패턴 중 하나라도 매칭되는지 확인"""
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                return True
        return False

    @classmethod
    def detect_categories(cls, utterance: str) -> List[PolicyCategory]:
        """발화에서 관련된 모든 정책 카테고리 추출"""
        categories: Set[PolicyCategory] = set()

        has_agri = cls._matches_any(utterance, cls.AGRI_PATTERNS)
        has_fish = cls._matches_any(utterance, cls.FISH_PATTERNS)
        has_combined_explicit = cls._matches_any(utterance, cls.COMBINED_PATTERNS)

        if (has_agri and has_fish) or has_combined_explicit:
            categories.add(PolicyCategory.COMBINED)

        if has_agri:
            categories.add(PolicyCategory.AGRICULTURE)
        if has_fish:
            categories.add(PolicyCategory.FISHERY)

        if cls._matches_any(utterance, cls.SUGAR_PATTERNS):
            categories.add(PolicyCategory.SUGAR)
        if cls._matches_any(utterance, cls.WEIGHT_PATTERNS):
            categories.add(PolicyCategory.WEIGHT)
        if cls._matches_any(utterance, cls.DISPOSAL_PATTERNS):
            categories.add(PolicyCategory.DISPOSAL)
        if cls._matches_any(utterance, cls.SPOILED_PATTERNS):
            categories.add(PolicyCategory.SPOILED)
        if cls._matches_any(utterance, cls.RETURN_REFUND_PATTERNS):
            categories.add(PolicyCategory.RETURN_REFUND)
        if cls._matches_any(utterance, cls.CLAIM_PATTERNS):
            categories.add(PolicyCategory.CLAIM)
        if cls._matches_any(utterance, cls.TRACKING_PATTERNS):
            categories.add(PolicyCategory.TRACKING)
        if cls._matches_any(utterance, cls.SPLIT_PATTERNS):
            categories.add(PolicyCategory.SPLIT_SHIPPING)
        if cls._matches_any(utterance, cls.SHIPPING_PATTERNS):
            categories.add(PolicyCategory.SHIPPING)
        if cls._matches_any(utterance, cls.WEATHER_PATTERNS):
            categories.add(PolicyCategory.WEATHER)
        if cls._matches_any(utterance, cls.BULK_PATTERNS):
            categories.add(PolicyCategory.BULK)
        if cls._matches_any(utterance, cls.ADDRESS_PATTERNS):
            categories.add(PolicyCategory.ADDRESS)
        if cls._matches_any(utterance, cls.AUTH_PATTERNS):
            categories.add(PolicyCategory.AUTH)
        if cls._matches_any(utterance, cls.ESCALATE_PATTERNS):
            categories.add(PolicyCategory.ESCALATE)
        if cls._matches_any(utterance, cls.FUTURE_PROMISE_PATTERNS):
            categories.add(PolicyCategory.FUTURE_PROMISE)
        if cls._matches_any(utterance, cls.PAST_PROMISE_PATTERNS):
            categories.add(PolicyCategory.PAST_PROMISE)
        if cls._matches_any(utterance, cls.LEGAL_DISPUTE_PATTERNS):
            categories.add(PolicyCategory.LEGAL_DISPUTE)
        if cls._matches_any(utterance, cls.COMPENSATION_CLAIM_PATTERNS):
            categories.add(PolicyCategory.COMPENSATION_CLAIM)
        if cls._matches_any(utterance, cls.DELEGATION_APPROVAL_PATTERNS):
            categories.add(PolicyCategory.DELEGATION_APPROVAL)
        if cls._matches_any(utterance, cls.DISCRETION_PATTERNS):
            categories.add(PolicyCategory.DISCRETION)
        if cls._matches_any(utterance, cls.PARTNER_CLAIM_PATTERNS):
            categories.add(PolicyCategory.PARTNER_CLAIM)
        if cls._matches_any(utterance, cls.CONSIGNMENT_SECRET_PATTERNS):
            categories.add(PolicyCategory.CONSIGNMENT_SECRET)
        if cls._matches_any(utterance, cls.HARVEST_PATTERNS):
            categories.add(PolicyCategory.HARVEST_STATUS)
        if cls._matches_any(utterance, cls.NO_AUTHENTICITY_PATTERNS):
            categories.add(PolicyCategory.NO_AUTHENTICITY_CHECK)
        if cls._matches_any(utterance, cls.EVIDENCE_HIERARCHY_PATTERNS):
            categories.add(PolicyCategory.EVIDENCE_HIERARCHY)
        if cls._matches_any(utterance, cls.IDENTITY_CLAIM_PATTERNS):
            categories.add(PolicyCategory.IDENTITY_CLAIM)
        if cls._matches_any(utterance, cls.REVERIFICATION_PATTERNS):
            categories.add(PolicyCategory.REVERIFICATION)
        if cls._matches_any(utterance, cls.UNHANDLED_ITEM_PATTERNS):
            categories.add(PolicyCategory.UNHANDLED_ITEM)
        if cls._matches_any(utterance, cls.CROP_DISASTER_PATTERNS):
            categories.add(PolicyCategory.CROP_DISASTER)
        if cls._matches_any(utterance, cls.LOGISTICS_CANCELLATION_PATTERNS):
            categories.add(PolicyCategory.LOGISTICS_CANCELLATION)
        if cls._matches_any(utterance, cls.PRIVACY_VERIFICATION_PATTERNS) or check_reverse_privacy_query(utterance):
            categories.add(PolicyCategory.PRIVACY_VERIFICATION)
        if cls._matches_any(utterance, cls.PRIVACY_CUMULATIVE_PATTERNS):
            categories.add(PolicyCategory.PRIVACY_CUMULATIVE)
        if cls._matches_any(utterance, cls.PRIVACY_THIRD_PARTY_PATTERNS):
            categories.add(PolicyCategory.PRIVACY_THIRD_PARTY)
        if cls._matches_any(utterance, cls.PRIVACY_CREDENTIAL_PATTERNS) or check_credential_solicitation(utterance):
            categories.add(PolicyCategory.PRIVACY_CREDENTIAL)
        if cls._matches_any(utterance, cls.PRIVACY_REFUND_ACCOUNT_PATTERNS):
            categories.add(PolicyCategory.PRIVACY_REFUND_ACCOUNT)
        if cls._matches_any(utterance, cls.PRIVACY_SELLER_INFO_PATTERNS):
            categories.add(PolicyCategory.PRIVACY_SELLER_INFO)
        if cls._matches_any(utterance, cls.PRIVACY_FARM_INFO_PATTERNS):
            categories.add(PolicyCategory.PRIVACY_FARM_INFO)
        if cls._matches_any(utterance, cls.PRIVACY_DATA_RIGHTS_PATTERNS):
            categories.add(PolicyCategory.PRIVACY_DATA_RIGHTS)
        if cls._matches_any(utterance, cls.PRIVACY_EXTERNAL_REQUEST_PATTERNS):
            categories.add(PolicyCategory.PRIVACY_EXTERNAL_REQUEST)
        if cls._matches_any(utterance, cls.PRIVACY_GROUP_COLLECTION_PATTERNS):
            categories.add(PolicyCategory.PRIVACY_GROUP_COLLECTION)
        if cls._matches_any(utterance, cls.PRIVACY_GENERAL_PATTERNS):
            categories.add(PolicyCategory.PRIVACY_GENERAL)
        if cls._matches_any(utterance, cls.SUBSCRIPTION_PATTERNS):
            categories.add(PolicyCategory.SUBSCRIPTION)
        if cls._matches_any(utterance, cls.PICKUP_PATTERNS):
            categories.add(PolicyCategory.PICKUP)
        if cls._matches_any(utterance, cls.TAX_PROOF_PATTERNS) or (check_proof_refusal(utterance) is not None):
            categories.add(PolicyCategory.TAX_PROOF)
        if cls._matches_any(utterance, cls.PAYMENT_RECONCILIATION_PATTERNS):
            categories.add(PolicyCategory.PAYMENT_RECONCILIATION)
        if cls._matches_any(utterance, cls.SEASON_CALENDAR_PATTERNS) or (
            has_agri
            and cls._matches_any(
                utterance,
                [
                    r"언제", r"시기", r"시즌", r"출하", r"나와", r"나옵", r"들어와", r"들어옵",
                    r"제철", r"품절", r"예약", r"조기", r"덜\s*익", r"지금.*사", r"지금.*판매",
                ],
            )
        ):
            categories.add(PolicyCategory.SEASON_CALENDAR)
        if cls._matches_any(utterance, cls.SEAFOOD_WEIGHT_PATTERNS) or (
            has_fish and cls._matches_any(utterance, cls.WEIGHT_PATTERNS)
        ):
            categories.add(PolicyCategory.SEAFOOD_WEIGHT)

        if not categories:
            categories.add(PolicyCategory.GENERAL)

        return list(categories)

    @classmethod
    def resolve_primary_policy(
        cls,
        utterance: str,
        categories: List[PolicyCategory],
        has_agri: bool,
        has_fish: bool,
    ) -> PolicyCategory:
        """충돌 해결 원칙에 따른 최우선 정책 카테고리 결정"""
        # ★★★ 초특급 감점 방어: 기관/언론 대외 고객 정보 요구는 제19조로 최우선 차단
        if PolicyCategory.PRIVACY_EXTERNAL_REQUEST in categories:
            return PolicyCategory.PRIVACY_EXTERNAL_REQUEST

        # 수수료율(20%) 및 정산/분담 비율 고객 대외비 절대 비밀 방어 (계약서 제17조)
        if PolicyCategory.CONSIGNMENT_SECRET in categories:
            if any(kw in utterance for kw in ("수수료", "수수료율", "마진", "정산", "얼마나 남겨", "얼마나 떼", "몇 프로")):
                return PolicyCategory.CONSIGNMENT_SECRET

        # 1. 분쟁·법률·안전 긴급 사안 최우선
        if PolicyCategory.LEGAL_DISPUTE in categories:
            return PolicyCategory.LEGAL_DISPUTE

        # ★★★ 초특급 감점 방어: 개인정보 보호 및 상담 창구 보안 가드레일 (방침 제1조~제25조)
        if PolicyCategory.PRIVACY_CREDENTIAL in categories:
            return PolicyCategory.PRIVACY_CREDENTIAL
        if PolicyCategory.PRIVACY_VERIFICATION in categories:
            return PolicyCategory.PRIVACY_VERIFICATION
        if PolicyCategory.PRIVACY_CUMULATIVE in categories:
            return PolicyCategory.PRIVACY_CUMULATIVE
        if PolicyCategory.PRIVACY_THIRD_PARTY in categories:
            return PolicyCategory.PRIVACY_THIRD_PARTY
        if PolicyCategory.PRIVACY_REFUND_ACCOUNT in categories:
            return PolicyCategory.PRIVACY_REFUND_ACCOUNT
        if PolicyCategory.PRIVACY_FARM_INFO in categories:
            return PolicyCategory.PRIVACY_FARM_INFO
        if PolicyCategory.PRIVACY_SELLER_INFO in categories:
            return PolicyCategory.PRIVACY_SELLER_INFO
        if PolicyCategory.PRIVACY_DATA_RIGHTS in categories:
            return PolicyCategory.PRIVACY_DATA_RIGHTS
        if PolicyCategory.PRIVACY_GROUP_COLLECTION in categories:
            return PolicyCategory.PRIVACY_GROUP_COLLECTION
        if PolicyCategory.PRIVACY_GENERAL in categories:
            return PolicyCategory.PRIVACY_GENERAL

        # ★진위 감정 절대 금지 (초특급 감점 방어 조항 - 증빙 규정 제6조, 제7조)
        if PolicyCategory.NO_AUTHENTICITY_CHECK in categories:
            return PolicyCategory.NO_AUTHENTICITY_CHECK

        # 수수료율(20%) 및 정산/분담 비율 고객 대외비 절대 비밀 방어 (계약서 제17조)
        if PolicyCategory.CONSIGNMENT_SECRET in categories:
            if any(kw in utterance for kw in ("수수료", "수수료율", "마진", "정산", "얼마나 남겨", "얼마나 떼", "몇 프로")):
                return PolicyCategory.CONSIGNMENT_SECRET

        # 섭취 후 이상(보관 vs 폐기) 및 배탈 질문은 제5조 DISPOSAL 우선
        if PolicyCategory.DISPOSAL in categories and cls._matches_any(
            utterance, [r"폐기", r"버려", r"보관", r"먹고", r"섭취", r"배탈", r"곰팡이", r"이물"]
        ):
            return PolicyCategory.DISPOSAL

        # 손해배상·병원비 청구 정식 절차 (레인 ③)
        if PolicyCategory.COMPENSATION_CLAIM in categories:
            return PolicyCategory.COMPENSATION_CLAIM

        # 2. 선약속 및 과거 약속 특수 규정 (과거 약속 주장 시 이력 조회가 최우선)
        if PolicyCategory.PAST_PROMISE in categories:
            return PolicyCategory.PAST_PROMISE
        if PolicyCategory.FUTURE_PROMISE in categories:
            return PolicyCategory.FUTURE_PROMISE

        # 2-1. 미취급 품목 (당근 등) 안내
        if PolicyCategory.UNHANDLED_ITEM in categories:
            return PolicyCategory.UNHANDLED_ITEM

        # 3. 조업·입고 현황 및 작황·재해 이력, 시원배송 결항 이력, 수산물 중량 자연감량 특수 규정
        if PolicyCategory.LOGISTICS_CANCELLATION in categories:
            return PolicyCategory.LOGISTICS_CANCELLATION
        if PolicyCategory.CROP_DISASTER in categories:
            return PolicyCategory.CROP_DISASTER
        if PolicyCategory.HARVEST_STATUS in categories:
            return PolicyCategory.HARVEST_STATUS
        if PolicyCategory.SEAFOOD_WEIGHT in categories:
            return PolicyCategory.SEAFOOD_WEIGHT

        # 4. 위탁 공급 및 권한/승인 규정
        if PolicyCategory.PARTNER_CLAIM in categories:
            return PolicyCategory.PARTNER_CLAIM
        if PolicyCategory.DELEGATION_APPROVAL in categories:
            return PolicyCategory.DELEGATION_APPROVAL
        if PolicyCategory.DISCRETION in categories:
            return PolicyCategory.DISCRETION

        # 4-1. 채팅 신원 주장 (증빙 규정 제9조 - 시스템 등록 기록으로만 확인)
        if PolicyCategory.IDENTITY_CLAIM in categories:
            return PolicyCategory.IDENTITY_CLAIM

        # 4-2. 재검증 요청 표준 및 불일치 신호 (증빙 규정 제8조, 제14조)
        if PolicyCategory.REVERIFICATION in categories:
            return PolicyCategory.REVERIFICATION

        # 4-3. 증빙 구분 및 권위 서열 / 객관적 정합 대조 (증빙 규정 제2조~제5조)
        if PolicyCategory.EVIDENCE_HIERARCHY in categories:
            return PolicyCategory.EVIDENCE_HIERARCHY

        # 4-4. 정기배송(구독) 약관 (제1조~제11조 전문 및 컷오프·스킵·해지·변경 판정 매트릭스)
        if PolicyCategory.SUBSCRIPTION in categories:
            return PolicyCategory.SUBSCRIPTION

        # 4-5. 산지 픽업 안내 (1~5번 전문)
        if PolicyCategory.PICKUP in categories:
            return PolicyCategory.PICKUP

        # 4-6. 결제·주문 대사 절차 및 10대 불일치 코드 (M-01~M-10)
        if PolicyCategory.PAYMENT_RECONCILIATION in categories:
            return PolicyCategory.PAYMENT_RECONCILIATION

        # 4-7. 세무 증빙 (세금계산서·현금영수증 발행 기준 1~7번 전문)
        if PolicyCategory.TAX_PROOF in categories:
            return PolicyCategory.TAX_PROOF

        # 4-8. 농산 시즌 캘린더 (10품목 11라인 월별 상태 및 10대 업무 처리 가이드라인)
        if PolicyCategory.SEASON_CALENDAR in categories:
            return PolicyCategory.SEASON_CALENDAR

        # 5. 복합 주문 및 합포장 불가 (계약서 제6조)
        if PolicyCategory.COMBINED in categories or (has_agri and has_fish):
            return PolicyCategory.COMBINED

        # 6. 세부 특수 조항 우선순위
        specific_priority = [
            PolicyCategory.SUGAR,
            PolicyCategory.WEIGHT,
            PolicyCategory.SPOILED,
            PolicyCategory.DISPOSAL,
            PolicyCategory.RETURN_REFUND,
            PolicyCategory.SPLIT_SHIPPING,
            PolicyCategory.TRACKING,
            PolicyCategory.CLAIM,
            PolicyCategory.SHIPPING,
            PolicyCategory.WEATHER,
            PolicyCategory.BULK,
            PolicyCategory.ADDRESS,
            PolicyCategory.AUTH,
            PolicyCategory.ESCALATE,
        ]

        for cat in specific_priority:
            if cat in categories:
                return cat

        if PolicyCategory.AGRICULTURE in categories:
            return PolicyCategory.AGRICULTURE
        if PolicyCategory.FISHERY in categories:
            return PolicyCategory.FISHERY

        return PolicyCategory.GENERAL

    @classmethod
    def get_relevant_knowledge(cls, utterance: str) -> str:
        """사용자 발화에 최적화된 프롬프트 주입용 컴팩트 지식 텍스트(400자 이내) 반환"""
        has_agri = cls._matches_any(utterance, cls.AGRI_PATTERNS)
        has_fish = cls._matches_any(utterance, cls.FISH_PATTERNS)
        categories = cls.detect_categories(utterance)
        primary = cls.resolve_primary_policy(utterance, categories, has_agri, has_fish)

        # 0-1. 분쟁·법률·언론·안전 사안 (권한위임표 제5조 레인 ②)
        if primary == PolicyCategory.LEGAL_DISPUTE:
            return (
                "【권한위임표 제5조: 분쟁·법률·안전·언론 사안 긴급 이관】\n"
                "- 소송, 소비자원 민원, 언론 제보, 신체 위해 등 중대 사안은 상담사 재량 밖이며 금액 무관 즉시 레인 ②로 이관됩니다.\n"
                "- 2단 이민준 운영자를 경유하여 3단 고길동 조합장에게 즉시 보고 및 정식 이관 처리됩니다."
            )

        # 0-0-1. 자격증명 수집 절대 금지 (방침 제5조·제13조)
        if primary == PolicyCategory.PRIVACY_CREDENTIAL:
            return (
                "【개인정보 처리방침 제5조·제13조: 자격증명 수집 절대 금지】\n"
                "- 비밀번호·인증번호(OTP)는 묻지도, 받지도, 대신 입력하지도 않습니다 (절대 원칙).\n"
                "- 고객이 자발적으로 알려주려 해도 즉시 중단을 요청하고, 공식 비밀번호 재설정 절차 또는 본인인증 초기화 액션만 안내합니다.\n"
                "- 비밀번호/OTP를 요구하는 상대를 만나면 사칭이므로 상담 창구에 신고하도록 안내합니다."
            )

        # 0-0-2. 본인확인 방향 준수 및 저장정보 역질문 차단 (방침 제9조·제10조)
        if primary == PolicyCategory.PRIVACY_VERIFICATION:
            return (
                "【개인정보 처리방침 제9조·제10조: 본인확인 방향 준수 및 저장정보 역질문 차단 (초특급 감점 방어)】\n"
                "- 본인확인은 고객님이 정보를 제시하고 조합이 대조하는 방향으로만 진행합니다.\n"
                "- 상담사가 저장된 개인정보(주소, 전화번호, 성명 등)를 먼저 읽어주거나 불러주는 행위는 어떠한 경우에도 절대 금지됩니다.\n"
                "- '등록된 주소 불러주세요', '몇 살로 되어 있어요?' 등 역질문에는 절대 응하지 않고, 주문번호·성명·연락처 뒷자리 제시를 고객님께 다시 요청합니다."
            )

        # 0-0-3. 누적 확인(스무고개) 중단 (방침 제11조)
        if primary == PolicyCategory.PRIVACY_CUMULATIVE:
            return (
                "【개인정보 처리방침 제11조: 누적 확인의 중단 (스무고개 차단)】\n"
                "- 예/아니오만으로 답하는 확인이 이어져 주소·연락처가 좁혀지는 흐름이 되면 즉시 중단하고 정식 본인확인 절차로 전환합니다.\n"
                "- 전환 기준: 동일 항목에 대한 예/아니오 확인이 3회 이상 누적된 때(상한선)이며, 3회 미만이라도 정보가 좁혀지면 즉시 중단합니다."
            )

        # 0-0-4. 타인 주문 조회 절대 차단 (방침 제12조·제16조)
        if primary == PolicyCategory.PRIVACY_THIRD_PARTY:
            return (
                "【개인정보 처리방침 제12조·제16조: 타인 주문 조회 절대 차단】\n"
                "- 조회·안내는 요청자 계정에 귀속된 주문에 한합니다. 로그인이나 주문번호 인지만으로는 타인 명의 주문 접근권이 없습니다.\n"
                "- 가족·지인·대리 요청이라도 타인 주문의 배송 상태·수령인 주소는 일체 비공개하며, 본인 주문을 다시 확인해 주시도록 안내합니다."
            )

        # 0-0-5. 환불 계좌 본인 명의 일치 확인 (방침 제14조)
        if primary == PolicyCategory.PRIVACY_REFUND_ACCOUNT:
            return (
                "【개인정보 처리방침 제14조: 환불 계좌의 본인 명의 확인】\n"
                "- 계좌이체(무통장입금) 환불은 예금주가 원결제자 본인과 일치해야만 지급합니다.\n"
                "- 명의가 다르면 지급하지 않고 본인 명의 계좌를 다시 요청하며, 확인 및 지급이 완료되면 계좌 정보는 즉시 파기합니다 (제8조)."
            )

        # 0-0-6. 공급 농가 개인정보 비공개 (방침 제18조)
        if primary == PolicyCategory.PRIVACY_FARM_INFO:
            return (
                "【개인정보 처리방침 제18조: 공급 농가 정보의 공개 범위】\n"
                "- 공급 농가에 관해 안내하는 범위는 공개용 농가 스토리(재배 경력, 품종, 수확 철 등)에 한합니다.\n"
                "- 농가 개인의 연락처, 주소, 나이, 가족관계는 제3자 개인정보이므로 일체 제공하지 않으며, 직접 연락 희망 시 조합이 대신 전달합니다."
            )

        # 0-0-7. 판매자 정보 공개 범위 (방침 제17조)
        if primary == PolicyCategory.PRIVACY_SELLER_INFO:
            return (
                "【개인정보 처리방침 제17조: 판매자 정보의 공개 범위】\n"
                "- 판매자 정보는 사업자정보 공시 항목(상호, 대표자, 사업자등록번호, 주소, 대표 연락처)에 한하여 안내합니다.\n"
                "- 매입가, 계약조건, 대표자 개인 배경 및 가족관계는 비공개하며, 법정 공시 항목은 정당하게 제공합니다."
            )

        # 0-0-8. 기관 및 언론 대외 요청 (방침 제19조)
        if primary == PolicyCategory.PRIVACY_EXTERNAL_REQUEST:
            return (
                "【개인정보 처리방침 제19조: 기관·언론 등 대외 요청 대응】\n"
                "- 기관·언론의 요청에도 고객 명단과 개별 피해 현황은 채팅·전화로 제공하지 않습니다.\n"
                "- 공문·영장 등 법적 절차와 사업자정보 공식 창구로만 응대하며, 상담사 임의 답변 없이 언론·기관 전담자에게 즉시 이관합니다."
            )

        # 0-0-9. 개인정보 열람·정정·삭제 요구 및 법정보존의무 (방침 제20조·제21조)
        if primary == PolicyCategory.PRIVACY_DATA_RIGHTS:
            return (
                "【개인정보 처리방침 제20조·제21조: 열람·정정·삭제 요구 및 법정보존 제한】\n"
                "- 고객님의 개인정보 열람·정정·삭제 요구는 본인확인 후 접수일로부터 영업일 10일 이내에 처리 결과를 회신합니다.\n"
                "- 전자상거래법에 따라 계약·청약철회(5년), 대금결제(5년), 소비자 불만·분쟁(3년) 등 법정 보존 기록은 삭제 요구에 응할 수 없으며 그 근거를 안내합니다."
            )

        # 0-0-10. 단체·미성년자 문의 최소 수집 (방침 제15조)
        if primary == PolicyCategory.PRIVACY_GROUP_COLLECTION:
            return (
                "【개인정보 처리방침 제15조: 단체·미성년자 문의 최소 수집】\n"
                "- 체험 문의 접수 단계에서는 책임자 성명, 연락처, 인원, 연령대, 희망일만 최소 수집합니다.\n"
                "- 참가자 개별 명단·생년월일·성별은 접수 단계에서 수집하지 않으며, 시설 및 일정 확인 후 회신합니다."
            )

        # 0-0-11. 개인정보 처리방침 일반 (방침 제1조~제25조)
        if primary == PolicyCategory.PRIVACY_GENERAL:
            return (
                "【개인정보 처리방침: 교동마을 산지직송 개인정보 처리 원칙】\n"
                "- 본 방침은 2037년 6월 1일부터 시행되며, 주문·배송·결제·상담·환불 전반에 적용됩니다.\n"
                "- 고객 권익 보호 및 정보주체의 권리(영업일 10일 이내 회신)를 철저히 보장하며, 상세 내용은 방침 전문을 따릅니다."
            )

        # 0-1-0. 진위 감정 절대 금지 및 과잉 검증 금지 (증빙 규정 제6조·제7조)
        if primary == PolicyCategory.NO_AUTHENTICITY_CHECK:
            return (
                "【증빙 취급 규정 제6조·제7조: 진위 감정 및 과잉 검증 절대 금지】\n"
                "- 상담사는 이미지 자체의 진위를 감정하지 아니합니다.\n"
                "- 의심 표현 절대 금지: 'AI로 만든 것 아닌가요', '색을 칠한 것처럼 보입니다', '사진이 조작된 것 같습니다'.\n"
                "- 감정 결과를 처리 거절·보류 근거로 삼지 아니하며, 하자 명백 시 관성적인 추가 사진·영수증·개봉 영상 요구를 금지합니다."
            )

        # 0-1-0-1. 채팅 신원 주장의 취급 (증빙 규정 제9조)
        if primary == PolicyCategory.IDENTITY_CLAIM:
            return (
                "【증빙 취급 규정 제9조: 채팅 신원 주장의 취급】\n"
                "- 채팅에서의 신원·자격 주장(인플루언서, 리뷰단, 협찬 대상, 조합원 등)은 당사자 제출물로 봅니다.\n"
                "- 캡처나 구두 주장만으로 자격을 인정하지 아니하며, 오직 조합 시스템 등록 기록으로만 확인하여 혜택을 부여합니다."
            )

        # 0-1-0-2. 증빙 구분 및 권위 서열 / 정합 대조 (증빙 규정 제2조~제5조)
        if primary == PolicyCategory.EVIDENCE_HIERARCHY:
            return (
                "【증빙 취급 규정 제2조~제5조: 증빙 권위 서열 및 객관적 정합 대조】\n"
                "- 권위 서열: 자사 기록 & 제3자 발행물(시험성적서/택배조회/카드승인) > 당사자 제출물(사진/캡처) > 구술 주장(구두 진술).\n"
                "- 서열의 근거는 이해관계 유무이며 매체 형태(이미지/팩스)로 신뢰도를 낮추지 않습니다.\n"
                "- 대조는 시스템과 기록으로 수행하며, 대조를 이유로 고객에게 추가 증빙을 요구하지 않습니다. 사칭 제보는 캡처로 접수(반려 금지)합니다."
            )

        # 0-1-0-3. 재검증 요청 표준 및 불일치 신호 (증빙 규정 제8조·제14조)
        if primary == PolicyCategory.REVERIFICATION:
            return (
                "【증빙 취급 규정 제8조·제14조: 재검증 요청 표준 및 전형적 불일치】\n"
                "- 대조에서 불일치가 확인된 경우에만 재검증을 요청하며, 근거는 감정이 아닌 '대조 결과'여야 합니다(의심 표현 금지).\n"
                "- 계측값(중량 등) 판정 시: 원물, 계측 도구 표시값, 주문 정보가 한 화면에 함께 보이도록 1장으로 요청합니다(표시값 단독 사진 판정 불가).\n"
                "- 원물을 폐기하지 않고 보관해 줄 것을 정중히 안내합니다."
            )

        # 0-1-1. 대외비 준수: 수수료율 20% 및 정산/분담 구조 (수산물 위탁 계약서 제17조)
        if primary == PolicyCategory.CONSIGNMENT_SECRET:
            return (
                "【수산물 위탁 판매 계약서 제17조: 고객 대외비 준수】\n"
                "- 판매 수수료율(20%), 정산 구조, 선지급분 차감 및 갑·을 분담 비율은 내부 계약상 비공개 사항으로 '안내하는 항목이 아닙니다'.\n"
                "- 고객 문의·환불·재배송은 위탁 핑계나 지연 없이 교동마을이 단독 창구(제8조)로서 책임지고 신속하게 즉시 처리해 드립니다."
            )

        # 0-1-2. 갯마을 조업·입고 및 어종별 판매 상태 (조업 기록)
        if primary == PolicyCategory.HARVEST_STATUS:
            return (
                "【갯마을 조업·입고 및 판매 현황 (기준일 2037-06-30)】\n"
                "- 오늘(06-30) 갈치 품절 사유: '비성어기 소량 조업 및 재고 소진' 때문입니다. (오늘 06-30에는 기상특보나 결항이 전혀 없으므로 기상을 사유로 설명하지 않습니다!)\n"
                "- 옥돔: 냉동 재고를 확보하여 정상 판매 중입니다.\n"
                "- 조업 이력: 06-21 기상특보로 갈치 조업 중단(옥돔은 냉동 재고로 정상 판매), 06-24 특보 해제 후 부분 재개되어 밀린 예약 순 발송 진행됨(즉시 정상 발송 약속 불가)."
            )

        # 0-1-2-1. 교동마을 미취급 품목 안내 (당근 등 애초에 없는 품목)
        if primary == PolicyCategory.UNHANDLED_ITEM:
            return (
                "【교동마을 생산 품목 확인: 미취급 품목 안내】\n"
                "- 당근(흙당근, 제주 흙당근 포함)은 교동마을 영농조합법인의 생산 품목에 애초에 없는 미취급 품목입니다.\n"
                "- 교동마을 생산자 품목 라인업: 문귀남(하우스감귤·노지감귤·만감류), 하동철(애플망고·참다래), 박수복(수박·멜론), 최덕만(감자·고구마·절임배추).\n"
                "- 취급하지 않는 품목은 주문 및 보상이 불가함을 정중히 안내합니다."
            )

        # 0-1-2-2. 교동마을 작황·재해 이력 및 7대 기록 확인 기준 (엑셀 원본 100% 동기화)
        if primary == PolicyCategory.CROP_DISASTER:
            return (
                "【교동마을 작황·재해 이력 및 기록 확인 기준 (기준일 2037-06-30)】\n"
                "- 7대 확인 원칙: ① 작황과 물류는 별개(배송 여부는 시원배송 결항기록 확인), ② '—'는 미확정 상태(피해 없음도 발생도 아님), ③ '영향 없음'은 피해 없음 판정, ⑥ 특보 해제가 곧 출고 정상화 아님(숙도 회복 별도 확인, 미확정이면 날짜 조작 약속 금지), ⑦ 기상/지체 기록만으로 하자·배상 자동 확정 금지.\n"
                "- 날짜별 핵심 팩트: 03-28 봄비(감자 영향없음), 06-05 태풍(하우스 시설 이상무/노지 경미), 06-07 특보해제(하우스감귤·애플망고 피해없음), 06-18 호우(수박 예약분 2~3일 지체), 06-25~27 정체전선(애플망고 숙도 지연으로 예약 출고 지연/하우스감귤 영향없음), 06-28 사후점검(노지 수박 열과 다발: 06-18 예약분 10통 중 6통 정상, 열과 4통 출하불가·07-01 이후 보충 가능), 06-29 특보해제(애플망고 숙도 회복 중이나 출고재개 미확정), 06-30 오늘(신규 기상 영향 없음 정상)."
            )

        # 0-1-2-3. 시원배송 결항·집하 기록 및 운송편 결항 상세 (기준일 2037-06-30)
        if primary == PolicyCategory.LOGISTICS_CANCELLATION:
            return (
                "【시원배송 결항·집하 기록 및 운송편 결항 상세 (기준일 2037-06-30)】\n"
                "- 관리: 구방만 기사님 (시원배송 TR-KD-01 교동 전담), 발행: 교동마을 산지직송.\n"
                "- 7대 기록 확인 기준:\n"
                "  ① 작황과 운송은 별개 확인(운송 결항만으로 농산 피해나 조업 중단 단정 불가).\n"
                "  ② '—'는 미확정 상태(지연 없음도 결항도 아님).\n"
                "  ③ '정상'은 지연 없음 판정(지연 가능성 사전 통보와 실제 결항은 다름).\n"
                "  ④ 일지는 사후에 채워지며 예보 행 소급 수정 금지.\n"
                "  ⑤ 간선 재개(일요일 15시)와 집하 재개(월요일 09시 다음 영업일)는 다름(밀린 물량 순차 처리).\n"
                "  ⑥ 경미한 지연은 하자 아님(03-28 감자 일부 오전 지연 후 정상화 완료는 배상 사유 아님).\n"
                "  ⑦ 송장 등록은 택배 인수(집하)가 아님(배송 단계와 집하 전후 책임은 계약서 제3조·제10조 승계).\n"
                "- 6월 태풍 구간 상세 타임라인 (애플망고):\n"
                "  · 06-04 14:00 수확 완료 / 18:30 선별·포장 완료 및 다음날 집하 예약 (물품 준비)\n"
                "  · 06-05 09:10 운송장 번호 생성 (송장 등록)\n"
                "  · 06-05 11:40 강풍경보 발효 -> 시원배송 간선 결항 통보 및 당일 집하 취소 (송장 등록 / 집하 전)\n"
                "  · 06-06 종일 결항 지속, 산지 냉장 보관 유지 (송장 등록 / 집하 전)\n"
                "  · 06-07 15:00 간선 재개(일요일이라 집하는 다음 영업일 월요일부터) (송장 등록 / 집하 전)\n"
                "  · 06-08 09:00 집하 재개(밀린 물량 순차 실음, 월요일 정기 출고일) (배송 단계: 집하(출고))\n"
                "- 핵심 정책 연계 (계약서 제3조·제10조):\n"
                "  · 06-05 09:10 송장 생성 후 06-08 09:00 집하 스캔 전까지는 송장만 등록된 집하 전 상태로 '배송지 변경 및 주문 취소 가능'했음(송장 번호 존재는 배송 시작 증거가 아님).\n"
                "  · 06-08 09:00 실제 집하 스캔 이후부터는 출고 완료로 배송지 변경 및 취소 불가.\n"
                "  · 2037-06-30(오늘): 기상특보 없음, 선박·화물선·항공 결항 없음, 기상 및 운송 전 품목 정상!"
            )

        # 0-1-3. 수산물 중량·자연감량 허용치 (수산물 중량 세칙 제1조~제12조)
        if primary == PolicyCategory.SEAFOOD_WEIGHT:
            return (
                "【수산물 중량·자연감량 허용치 세칙 (제1조~제12조)】\n"
                "- 판정 기준: 출고 시 검정 저울로 측정한 '출고 중량'이 절대 기준입니다 (출고 기록 부재 시 표기 중량 기준).\n"
                "- 합산 판정선: 표기 허용오차(5%) + 자연감량(3%) = 미달 8% 이내는 정상 범위입니다.\n"
                "- 8% 초과 미달 시: 초과분이 아닌 '부족분 전체'에 대해 부분환불(차액환불) 또는 재배송 중 고객 선택으로 즉시 처리합니다.\n"
                "- 정상 판정 시: 단순 거절하지 않고 빙장수·드립으로 실제 감량이 일어난다는 사실을 친절히 안내합니다.\n"
                "- 표준 재촬영: 원물, 저울 표시값, 주문번호가 한 화면에 보이는 1장 요청 (물기 뺀 원물만, 포장재/보랭재 제거)."
            )

        # 0-2. 손해배상(병원비) 정식 절차 (규정 제25조, 권한위임표 제5조 레인 ③)
        if primary == PolicyCategory.COMPENSATION_CLAIM:
            return (
                "【규정 제25조·권한위임표 제5조: 손해배상(병원비) 정식 절차】\n"
                "- 섭취 후 이상, 식중독, 병원비 등 손해배상은 금액 무관 레인 ③(정식 배상) 절차로 진행됩니다.\n"
                "- 상품 하자와 증상 간 인과관계가 객관적 서류(진단서 등)로 확인된 후 고길동 조합장의 최종 승인을 거쳐 지급되며, 임의 배상은 불가합니다."
            )

        # 0-3. 미래 선약속 금지 및 배송비 쿠폰 대체 (권한위임표 제7조)
        if primary == PolicyCategory.FUTURE_PROMISE:
            return (
                "【권한위임표 제7조: 미래 선약속 금지 및 배송비 쿠폰 대체】\n"
                "- '다음 주문 무조건 무료배송' 등 미래 주문에 대한 사전 확약은 재량 밖이며 조합장 승인으로도 절대 불가합니다.\n"
                "- 고객의 선약속 요구 시에는 이를 정중히 설명하고, 당해 주문에 대한 1회분 배송비 상당 할인 쿠폰(교동 4,000원 / 갯마을 5,000원) 제공으로 대체 처리합니다."
            )

        # 0-4. 과거 과잉 약속 처리 기준 (권한위임표 제8조)
        if primary == PolicyCategory.PAST_PROMISE:
            return (
                "【권한위임표 제8조: 과거 과잉 약속 처리 기준】\n"
                "- 과거 상담원의 약속 주장 시 반드시 시스템 내 상담 이력을 먼저 조회합니다.\n"
                "- 1) 기록 확인 & 권한 내: 약속 내용 즉시 이행.\n"
                "- 2) 기록 확인 & 권한 밖(선약속 등): 기록 인정 및 정중히 정정한 뒤 1회분 배송비 상당 쿠폰으로 보정.\n"
                "- 3) 기록 없음: 확인 불가 안내 및 미이행 설명 후 현재 제공 가능한 혜택 안내."
            )

        # 0-5. 상담사 재량 한도 및 금액 임계 (권한위임표 제4조, 제5조)
        if primary == PolicyCategory.DISCRETION:
            return (
                "【권한위임표 제4조·제5조: 상담사 재량 한도 및 금액 임계】\n"
                "- 상담 에이전트의 독자 재량 한도는 건당 50,000원 이하(실결제액 기준)입니다(레인 ① 자율 봇 처리).\n"
                "- 50,000원 초과 부분환불·보상은 2단 이민준 운영자 심사 후 3단 고길동 조합장의 승인이 필수입니다.\n"
                "- 단, 사진 확인 하자 구제(규정 제4조) 및 당연 반환(수량 축소, 출고 지연)은 금액 무관 자율 재량입니다."
            )

        # 0-6. 승인 절차 및 인적 서열 (권한위임표 제6조, 제10조)
        if primary == PolicyCategory.DELEGATION_APPROVAL:
            return (
                "【권한위임표 제6조·제10조: 승인 절차 및 인적 서열】\n"
                "- 승인 3단계 서열: 1단 에이전트(5만원 이하) -> 2단 이민준 운영자(1차 판단) -> 3단 고길동 조합장(최종 결재). 봇의 조합장 직통 승인 요청은 불가합니다.\n"
                "- 2단 이민준 운영자 부재 시 대체 경로: 구방만 기사님 -> 박민아 님.\n"
                "- 승인 회신 기한은 영업일 3일이며, 무응답을 승인으로 간주하지 않습니다."
            )

        # 0-7. 위탁(갯마을) 상품 품질 책임 처리 (권한위임표 제5조, 제10조)
        if primary == PolicyCategory.PARTNER_CLAIM:
            return (
                "【권한위임표 제5조·제10조: 위탁(갯마을) 상품 품질 책임 처리】\n"
                "- 갯마을 수산물 등 위탁 상품 품질 클레임은 금액 무관 공급 측 협의(홍이장 님 경유)로 처리합니다.\n"
                "- 홍이장 님은 공급 협의 대상자이며 교동마을 연합의 내부 승인권자가 아닙니다."
            )

        # 0-8. 정기배송(구독) 약관 (제1조~제11조 전문 및 컷오프·스킵·해지·변경 판정 매트릭스)
        if primary == PolicyCategory.SUBSCRIPTION:
            return (
                "【정기배송 약관 제1조~제11조: 컷오프·스킵·해지·변경 판정 매트릭스】\n"
                "- 컷오프: 해당 결제일 3영업일 전 24:00 (결제일 불산입, 날짜·시각 YYYY-MM-DD 24:00 명시 안내 필수).\n"
                "- 컷오프 전: 스킵/해지/변경 이번 회차 즉시 반영. 해지 시 위약금 0원, 남은 회차 전액환불, 할인 소급 반환 없음.\n"
                "- 컷오프 후: 다음 회차부터 반영. 이번 회차 단순 '불가' 거절 절대 금지, 4대 대안 필수 안내(수령일조정/배송지변경[집하전], 취소·환불[출고준비전], 다음회차스킵[상시]).\n"
                "- 해지 시 금지: 사유 요구·만류 혜택 반복·통화/서면 요구 일체 금지. 스킵 횟수 한도 없음.\n"
                "- 처리 절차: 구독상태 조회 ➔ 컷오프 대조 ➔ 반영 회차 판정 (조회 없이 단정 금지)."
            )

        # 0-9. 산지 픽업 안내 (1~5번 전문)
        if primary == PolicyCategory.PICKUP:
            return (
                "【산지 픽업 안내 규정(1~5번 전문)】\n"
                "- 요건: 사전예약 필수(희망일 1영업일 전 마감), 지정 집하장 1곳(밭/하우스 불가, 예약시 주소안내), 영업일(월~금) 오전 중 1개 시간대(택배상차시간 물량혼재 방지 미운영), 온라인몰 사전결제 한정(현장결제/주문 불가).\n"
                "- 본인확인: 주문번호+계정명의 확인. 대리수령은 예약 시 사전 지정만 허용(정보구술 인도 불가).\n"
                "- 책임경계: 인수시점이 경계(인수전 조합, 인수후 이동온도 포함 고객책임, 차량적재후 품온상승 하자 미인정).\n"
                "- 배송비: 0원(미부과). 픽업일=수령일(하자접수기산). 인수전 개봉확인/인수거절 가능(비용없이 주문취소). 미수령시 당일 1회 재예약, 재미수령시 취소·환불(조합귀책시 배송비무료 전환 또는 전액환불)."
            )

        # 0-10. 결제·주문 대사 절차 및 10대 불일치 처리 기준 (M-01 ~ M-10)
        if primary == PolicyCategory.PAYMENT_RECONCILIATION:
            # 1) 특정 M 코드 질의가 명시된 경우
            for m_code in ReconciliationCode:
                if re.search(rf"\b{m_code.value}\b", utterance, re.IGNORECASE):
                    rule = RECONCILIATION_RULES[m_code]
                    script_part = f"\n- 표준 안내문: \"{rule.guide_script}\"" if rule.guide_script else ""
                    return (
                        f"【결제·주문 대사 지침: {rule.code.value} - {rule.verdict}】\n"
                        f"- 불일치 유형: {rule.mismatch_type}\n"
                        f"- 처리 지침: {rule.action_guideline}\n"
                        f"- 금지 행위: {rule.prohibited_action}{script_part}"
                    )
            # 2) 공식 상품 3종 SKU가 명시된 경우
            for sku_key, prod in OFFICIAL_PRODUCTS.items():
                if sku_key.lower() in utterance.lower():
                    sugar_info = f"{prod.sugar_brix_guarantee}Bx 보장" if prod.has_sugar_guarantee else "당도 미표기 (하자 제외)"
                    spec_info = f"규격 상품(허용오차 없음)" if prod.is_min_spec else "일반 상품(±5% 오차)"
                    return (
                        f"【공식 판매 상품 명세: {prod.sku}】\n"
                        f"- 상품명: {prod.name}\n"
                        f"- 판매가: {prod.price:,}원 (배송비 {prod.shipping_fee:,}원)\n"
                        f"- 규격/중량: {prod.spec_description} / {spec_info}\n"
                        f"- 당도 보장: {sugar_info}\n"
                        f"- {prod.description}"
                    )
            # 3) 일반 결제 대사 전체 요약
            return (
                "【결제·주문 대사(M-01~M-10) 및 3종 상품 기준】\n"
                "- 4대 대사키: 승인번호·실결제액·카드뒷4자리(정확일치/선낭독금지), 승인시각(±5분 허용).\n"
                "- M-01(주문유실): 재결제 요구 절대금지! 실결제액 기준 주문복구 최우선(품절시 환불).\n"
                "- M-03(승인없음): 결제사실 부정금지('조합 기록 부재' 안내 및 결제사 조회 접수).\n"
                "- M-08(중복결제): 승인 2건일 때만 성립. M-09(반영지연): 유실 아님, 재조회 대기.\n"
                "- M-10(타계정): 본인 확인 후 처리, 타계정 내역 일체 비공개.\n"
                "- 공식상품: WTM-SEL-8(수박 8kg이상 11Bx), HGL-SEL-5(감귤 12Bx 선별), HGL-STD-5(당도미달 하자 제외)."
            )

        # 0-11. 세무 증빙 (세금계산서·현금영수증 발행 기준 1~7번 전문)
        if primary == PolicyCategory.TAX_PROOF:
            refusal_match = check_proof_refusal(utterance)
            if refusal_match:
                return (
                    f"【세무 증빙 발행 기준 §6: 7대 거절 대상 - {refusal_match.demand_type}】\n"
                    f"- 판정: {refusal_match.verdict} ({refusal_match.reason})\n"
                    f"- 정상 절차: {refusal_match.proper_procedure}\n"
                    "- 세금계산서는 실제로 결제하고 상품을 공급받은 사업자 명의로만 발행 가능하며 임의 변경 불가합니다."
                )
            if any(k in utterance for k in ["세액", "부가세", "0원", "면세", "과세", "배송비"]):
                return (
                    "【세무 증빙 발행 기준 §3: 세금계산서 면세 0원 및 과세 분리】\n"
                    "- 세액 면세(0원): 취급 품목은 전부 미가공 농·수산물이라 면세 대상(세액 0원)이며 세액란 공란은 정상입니다.\n"
                    "- 과세 분리: 배송·운송비는 용역분이라 부가세(10%) 과세 대상입니다.\n"
                    "- 상품(면세)과 배송비(과세)는 절대 한 항목으로 합쳐 적지 않고 반드시 항목을 나눠 분리 기재합니다."
                )
            if any(k in utterance for k in ["TX-", "tx-", "정정", "명의 오류", "명의오류"]):
                return (
                    "【세무 증빙 발행 기준 §4: 6대 정정 사유 (TX-01~TX-06)】\n"
                    "- TX-01(착오오기 수정), TX-02(부분환불 차액수정), TX-03(전액환불 전액취소), TX-04(중복 후행취소), TX-06(누락 재발행)\n"
                    "- TX-05(명의 오류): 단순 정정이 아니라 반드시 '기존 증빙 취소 후 정당 명의 재발행'하며 거절 대상 우회 발행 절대 금지."
                )
            if any(k in utterance for k in ["카드", "매출전표", "중복"]):
                return (
                    "【세무 증빙 발행 기준 §1: 결제수단별 발행 대상】\n"
                    "- 카드 결제: 카드 매출전표로 세무 증빙 대체. 현금영수증/세금계산서 별도 발행 불가(중복 증빙 방지).\n"
                    "- 현금·계좌이체: 현금영수증 발행 대상(발행 기준액은 실결제액, 적립금/쿠폰 제외).\n"
                    "- 분할결제: 현금분만 현금영수증, 카드분은 매출전표로 수단별 분할 처리."
                )
            if any(k in utterance for k in ["현금영수증", "지출증빙", "소득공제", "자율"]):
                return (
                    "【세무 증빙 발행 기준 §2: 현금영수증 발행 규칙】\n"
                    "- 유형: 소득공제용(개인) · 지출증빙용(사업자, 소득공제 불가).\n"
                    "- 기한: 거래일 익월 10일까지 (경과 시 국세청 홈택스 자율 발급 안내, 조합 발행 불가).\n"
                    "- 개인정보 보호: 고객 번호 제시 전 상담사의 기존 등록 번호 선낭독 절대 금지."
                )
            return (
                "【세금계산서·현금영수증 발행 기준】\n"
                "- 현금/계좌: 현금영수증(소득공제/지출증빙, 익월 10일 한도, 번호 선낭독 금지).\n"
                "- 카드: 카드 매출전표 대체(별도 발행 불가).\n"
                "- 세금계산서: 실결제 사업자 명의, 미가공 농수산물 면세(세액 0원 공란 정상), 배송비 용역분 과세 분리 기재.\n"
                "- 정정: TX-01~TX-06 (TX-05 명의오류는 취소 후 재발행, 우회 금지)."
            )

        # 0-12. 농산 시즌 캘린더 (10품목 11라인 월별 상태 및 10대 업무 처리 가이드라인)
        if primary == PolicyCategory.SEASON_CALENDAR:
            detected_line = None
            for key in ["하우스감귤", "하우스 감귤", "노지감귤", "노지 감귤", "청귤", "수박", "멜론", "애플망고", "감자", "고구마", "참다래", "키위", "절임배추", "한라봉", "천혜향", "만감류"]:
                if key in utterance:
                    detected_line = get_agri_season_line(key)
                    break

            if detected_line:
                st6 = detected_line.monthly_statuses[6]
                st7 = detected_line.monthly_statuses[7]

                # '종' 상태인 경우: 품절 금지, 차기 개시월, 대안 품목 제시
                if st6 == SeasonStatus.CLOSED:
                    active_now = [l.crop_name for l in get_active_lines_in_month(6)]
                    return (
                        f"【교동마을 농산 시즌 캘린더: {detected_line.crop_name} (현재 6월: 시즌 종료)】\n"
                        f"- 안내 기준: '품절'이 아니라 '시즌 종료(시즌 밖)'임을 안내하며 차기 개시월({detected_line.next_season_start})을 고지합니다.\n"
                        f"- [초특급 가드레일] '품절이라 곧 들어와요' 등 품절 단정 표현 절대 금지! 캘린더는 월 단위이므로 확정 입고일/도착일 약속 절대 금지.\n"
                        f"- 대안 제시: 현재 출하 중(초입·성수기)인 신선 농산물({', '.join(active_now[:3])})을 대안으로 안내합니다."
                    )

                # 하우스감귤 여름철 문의
                if detected_line.line_code == "HGL":
                    return (
                        "【교동마을 농산 시즌 캘린더: 하우스감귤 (6~8월 성수기)】\n"
                        "- 상태: 시설 난방 재배로 6~8월 여름철이 가장 물량과 품질이 안정한 성수기(12Bx 보장)입니다.\n"
                        "- [초특급 가드레일] 계절만 보고 오배송·사칭으로 임의 단정하는 행위 절대 금지! 하우스 난방·관리 비용 발생으로 임의 할인 및 지난 시즌 가격 약속 불가."
                    )

                # 수박 문의
                if detected_line.line_code == "WTM":
                    return (
                        "【교동마을 농산 시즌 캘린더: 수박 (6월 초입 / 7월 성수기)】\n"
                        "- 상태: 6월은 초입(물량 적고 가격 높음), 7월은 성수기입니다. 11Bx 당도 보장 및 8kg 규격 상품 허용오차(±5%) 미적용 규정 준수.\n"
                        "- [초특급 가드레일] 캘린더는 월 단위이므로 확정 입고일 약속 금지, 덜 익은 것 골라서 조기 출하 접수 절대 불가."
                    )

                # 청귤 문의
                if detected_line.line_code == "NGL_RSV":
                    return (
                        "【교동마을 농산 시즌 캘린더: 청귤 예약 라인 (6~7월 예약 접수 / 8월 성수기)】\n"
                        "- 상태: 6~7월은 예약 접수 기간이며 출고는 8월 수확분부터입니다. 시기 외 수확은 미숙과로 출하 불가.\n"
                        "- [초특급 가드레일] 접수 시점과 출고 시점이 분리됨을 안내하며 확정 출고일 표현은 절대 금지합니다."
                    )

                # 기타 품목
                info6 = SEASON_STATUS_DEFINITIONS[st6]
                info7 = SEASON_STATUS_DEFINITIONS[st7]
                return (
                    f"【교동마을 농산 시즌 캘린더: {detected_line.crop_name}】\n"
                    f"- 6월 상태: {info6.name}({info6.code}), 7월 상태: {info7.name}({info7.code}), 차기 개시: {detected_line.next_season_start}\n"
                    f"- 안내 기준: {info6.guide_standard}\n"
                    f"- [10대 가이드라인] 확정 입고일 약속 절대 금지, 조기 출하 요구 거절, 기수령 저장품목 보관/안전 안내 필수 제공."
                )

            # 전반적 시즌 캘린더 요약
            return (
                "【교동마을 농산 시즌 캘린더 (기준일: 2037-06-30)】\n"
                "- 6/7월 상태: 수박(6월초/7월성 11Bx), 하우스감귤(6~8월성 12Bx), 감자(6~7월성), 애플망고(6월성/7월말), 청귤(6~7월예/8월성), 노지감귤(시즌종료/차기11월).\n"
                "- [10대 가드레일] ①'종' 라인은 '품절' 아닌 '시즌 밖' 안내 및 초·성 대안 제시 ('품절이라 곧 들어와요' 금지) "
                "②월 단위 안내(확정 입고일 약속 금지) ③조기출하 거절 ⑧하우스 난방비로 할인 불가 ⑨여름 하우스감귤 정상 출하(오배송 단정 금지) ⑩시즌 밖 저장품 보관/안전 안내 제공."
            )

        # 1. 합포장 / 합배송 제한 (계약서 제6조)
        if primary == PolicyCategory.COMBINED:
            return (
                "【계약서 제6조: 상온/냉동 합배송 제한】\n"
                "- 농산물(교동 상온)과 수산물(갯마을 냉동)은 보관 조건이 달라 합배송이 제한되며 각각 개별 포장·발송됩니다.\n"
                "- 시원배송 담당 기사(교동 TR-KD-01 구방만 기사님 vs 갯마을 TR-GM-02) 및 송장번호가 분리됩니다.\n"
                "- 배송비: 교동 4천원(5만원 이상 무료), 갯마을 5천원(7만원 이상 무료) 각각 독립 부과."
            )

        # 2. 당도 보장 (규정 제7조)
        if primary == PolicyCategory.SUGAR:
            return (
                "【규정 제7조: 당도선별 및 보장 기준】\n"
                "- 출고 전 당도 측정으로 기준 미달 상품을 배제합니다(기준 미달 배제 로트는 고객에게 미발송).\n"
                "- 라인별 당도 보장 기준: 수박 11브릭스 이상 보장, 하우스감귤 12브릭스 이상 보장(기본 11이 아닌 12브릭스!).\n"
                "- 당도 보장 표기가 없는 라인은 사전에 약속한 수치가 없으므로 로트상 낮아도 하자로 판정되지 않습니다.\n"
                "- 당도 미달 확인 시 재배송, 재배송분도 미달 시 전액환불 및 쿠폰/적립금 보상(고길동 조합장 승인)."
            )

        # 3. 중량/무게/규격 미달 (규정 제6조)
        if primary == PolicyCategory.WEIGHT:
            return (
                "【규정 제6조: 무게·규격 허용오차 및 예외】\n"
                "- 일반 표기 무게 상품: ±5% 허용오차 적용 (5% 이내 미달은 정상).\n"
                "- '몇 kg 이상' 규격 상품(예: 특대 8kg 이상 수박 등): ±5% 허용오차를 절대 적용하지 않으며, 7.9kg 등 5% 이내 부족도 무조건 규격 미달 하자입니다!\n"
                "- 오차 초과 또는 규격 미달 시 저울 사진 확인 후 부족분 차액환불 또는 재배송 중 고객 선택으로 처리합니다."
            )

        # 4. 폐기 vs 보관 및 손해배상 (규정 제5조, 제25조)
        if primary == PolicyCategory.DISPOSAL:
            is_injury = cls._matches_any(utterance, [r"섭취", r"먹고", r"탈", r"배탈", r"병원", r"손해배상", r"이물"])
            if is_injury:
                return (
                    "【규정 제5조 제2항·제25조: 섭취 이상 및 손해배상】\n"
                    "- 이물 혼입 또는 섭취 후 이상 발생 시 폐기하지 말고 반드시 보관 및 사진 촬영하셔야 합니다(곰팡이 동시 발생 시에도 보관 우선).\n"
                    "- 병원비 등 손해배상은 상품 하자와 증상 간 인과관계 확인 후 정식 절차로 진행하며 임의 배상하지 않습니다."
                )
            return (
                "【규정 제5조: 하자 상품의 폐기 및 보관】\n"
                "- 곰팡이·부패 등 위생 위해가 명백한 경우 즉시 섭취를 중단하고 폐기 안내하며 반송을 요구하지 않습니다.\n"
                "- 이물 혼입이나 섭취 후 이상이 있는 경우 원인규명을 위해 폐기하지 않고 보관·촬영하셔야 합니다(동시 해당 시 보관 우선)."
            )

        # 5. 상함의 책임 배분 (규정 제10조)
        if primary == PolicyCategory.SPOILED:
            return (
                "【규정 제10조: 상함의 책임 배분】\n"
                "- 출고 당시의 하자인지 수령 후 보관 과실인지 구분이 어려운 경우 상품가의 50%를 부분환불합니다.\n"
                "- 여름철 상온 방치 등 보관 과실이 유력한 경우에는 전액환불 대상으로 보지 아니합니다."
            )

        # 6. 단순변심 / 환불 원칙 (규정 제11조, 제12조, 제20조)
        if primary == PolicyCategory.RETURN_REFUND:
            return (
                "【규정 제11조·제12조·제20조: 환불 및 청약철회】\n"
                "- 개봉하거나 절반 이상 섭취한 단순 변심은 전액환불 불가합니다.\n"
                "- 미개봉 단순변심은 수령 후 7일 이내 반품 가능하며 왕복 배송비는 고객 부담입니다.\n"
                "- 환불은 실제 사유 확인 후 원결제수단으로만 처리되며(카드 해지 시도 승인취소 정상), 채팅 안내 타인 계좌 입금은 불가합니다."
            )

        # 7. 배송 단계 및 배송지 변경/취소 (계약서 제3조, 제10조)
        if primary == PolicyCategory.ADDRESS:
            return (
                "【계약서 제3조·제10조: 배송지 변경 및 취소 기준】\n"
                "- 시원배송 집하(스캔 기록 기준) 전에는 배송지 변경 및 주문 취소가 가능합니다.\n"
                "- 기사의 집하 스캔 기록 시각이 절대 기준이며, 송장 번호가 등록되었더라도 집하 스캔 전 상태(예: 06-05 09:10 ~ 06-08 09:00 태풍 결항 구간)에는 배송지 변경 및 취소가 가능합니다.\n"
                "- 집하 스캔 후에는 주소 변경 및 취소가 절대 불가하며 수취 거부 시 자동 반송됩니다.\n"
                "- 단, 고객 귀책 반송 후 재배송 시에는 새 배송지로 변경 가능합니다(제10조 제3항 예외)."
            )

        # 8. 송장 조회 및 배송 소요 (계약서 제3조, 제4조)
        if primary == PolicyCategory.TRACKING:
            return (
                "【계약서 제3조·제4조: 배송 소요 및 송장 조회】\n"
                "- 산지직송 상품은 당일배송이 불가하며 통상 익일 내지 모레 도착합니다.\n"
                "- 송장 등록 후 시원배송 전산 시스템에 반영되기까지 3~5시간이 소요되며 이는 정상 과정입니다(배송 지연 아님).\n"
                "- 교동 집하 담당: 시원배송 구방만 기사님(TR-KD-01).\n"
                "- '송장이 등록되었다고 배송이 시작된 것은 아니다!' 실제 집하 스캔 시각이 절대 기준입니다."
            )

        # 9. 분할 배송 (계약서 제8조)
        if primary == PolicyCategory.SPLIT_SHIPPING:
            return (
                "【계약서 제8조: 분할 배송 기준】\n"
                "- 고객 요청에 의한 분할(부분) 배송은 회차별 배송비가 발생합니다.\n"
                "- 신선도 유지를 위해 최초 출고일로부터 7일 이내, 최대 3회차까지만 가능합니다.\n"
                "- 3회차 초과 요청은 별건 주문으로 접수하셔야 합니다."
            )

        # 10. 일반 클레임 / 파손 / 하자 고객선택권 (규정 제4조, 제20조, 계약서 제11조, 제12조)
        if primary == PolicyCategory.CLAIM:
            if has_agri and not has_fish:
                return (
                    "【규정 제4조·제20조: 교동 농산물 하자 보상】\n"
                    "- 수령일로부터 7일 이내 사진 확인 시 배송비 없이 재배송 또는 전액환불 중 고객이 선택합니다.\n"
                    "- 개봉/섭취 단순변심은 전액환불 불가(제11조).\n"
                    "- 곰팡이·부패 시 즉시 폐기 안내(제5조)."
                )
            elif has_fish and not has_agri:
                return (
                    "【규정 제17조·계약서 제11조: 갯마을 수산물 보상】\n"
                    "- 냉동 수산물 해동·콜드체인 이상 시 7일 이내 재배송 또는 환불 처리합니다(규정 제17조, 제20조).\n"
                    "- 배송 중 파손 발생 시 택배사 내부 정산에 앞서 고객 선구제(재배송/환불)를 우선 진행합니다(계약서 제11조)."
                )
            else:
                return (
                    "【규정 제4조·제20조·계약서 제11조: 하자 및 파손 보상】\n"
                    "- 수령 후 7일 이내 사진 확인 시 무상 재배송 또는 전액환불 중 고객이 직접 선택합니다.\n"
                    "- 배송 중 파손은 시원배송 정산 전 고객 선구제(재배송/환불)를 우선 진행합니다.\n"
                    "- 단순 변심은 미개봉 시 7일 이내 왕복배송비 부담 반품 가능."
                )

        # 11. 배송비 및 도서산간
        if primary == PolicyCategory.SHIPPING:
            is_island = cls._matches_any(utterance, [r"도서산간", r"제주도", r"섬", r"추가\s*배송", r"항공료", r"도선료"])
            if is_island:
                return (
                    "【도서산간 배송비 전액 면제 안내】\n"
                    "- 제주 산지 직접 발송 특전으로 제주 도내 및 전국 모든 도서산간 추가 운임(3,000~5,000원)이 전액 면제됩니다.\n"
                    "- 기본 배송비: 교동마을 4,000원(5만원 이상 무료), 갯마을 5,000원(7만원 이상 무료). 묶음 주문 시 마을별 독립 부과."
                )
            return (
                "【배송비 정책 안내】\n"
                "- 교동마을(농산물): 기본 4,000원 (50,000원 이상 구매 시 무료배송)\n"
                "- 갯마을(수산물): 기본 5,000원 (70,000원 이상 구매 시 무료배송)\n"
                "- 전국 도서산간/제주 추가 운임 전액 면제 (기본 배송비만 부과)\n"
                "- 복합 주문 시 마을별 배송비 각각 독립 산정"
            )

        # 12. 기상 악화 지연 (계약서 제4조 제2항)
        if primary == PolicyCategory.WEATHER:
            return (
                "【계약서 제4조: 기상 악화 출하 지연 안내】\n"
                "- 제주 해상 풍랑주의보(선박 결항) 및 대설·한파 시 품질 보호를 위해 1~2일 순차 출하 지연될 수 있습니다.\n"
                "- 출하 지연 발생 시 알림톡으로 개별 안내를 드립니다."
            )

        # 13. 대량 구매 / 단체 주문 (계약서 제5조)
        if primary == PolicyCategory.BULK:
            return (
                "【계약서 제5조: 대량 구매 및 분할 배차】\n"
                "- 대량 주문은 시원배송 분할 배차될 수 있으며 사전 고지됩니다.\n"
                "- 10박스 이상 대량 주문 시 청년회 CS 담당자(이민준) 1:1 상담을 통해 5~10% 추가 할인 및 배송 희망일 조율이 가능합니다."
            )

        # 14. 계정 장애 / 로그인
        if primary == PolicyCategory.AUTH:
            return (
                "【계정 장애 및 본인인증 안내】\n"
                "- 카카오 간편로그인 오류 시 인증 재시도 또는 가입 전화번호 확인을 통해 신속히 계정 복구를 도와드립니다.\n"
                "- 규정 제12조에 따라 확인되지 않은 정보나 채팅 지시로는 환불 및 계정 변경이 불가합니다."
            )

        # 15. 상담원 이관
        if primary == PolicyCategory.ESCALATE:
            return (
                "【고객센터 및 상담원 연결 안내】\n"
                "- 청년회 현장 CS 담당자(이민준) 1:1 상담: 평일 09:00~18:00 (점심 12:00~13:00, 주말/공휴일 휴무).\n"
                "- 업무 시간 외 문의는 상담 티켓 발급 후 익일 영업 개시 시 최우선 순위로 콜백 드립니다."
            )

        # 16. 단일 품목 일반
        if primary == PolicyCategory.AGRICULTURE:
            return (
                f"【{GYODONG_POLICY.village_name} 농산물 안내】\n"
                f"- 출하: {GYODONG_POLICY.origin}\n"
                f"- 배송: {GYODONG_POLICY.logistics_partner} (기본 {GYODONG_POLICY.base_shipping_fee:,}원, {GYODONG_POLICY.free_shipping_threshold:,}원 이상 무료)\n"
                f"- 당도보장(수박 11Bx, 하우스감귤 12Bx/미표기라인 미적용), 무게오차 ±5%(8kg 이상 규격은 오차 미적용), 하자 접수 7일(제20조)"
            )

        if primary == PolicyCategory.FISHERY:
            return (
                f"【{GAETMAEUL_POLICY.village_name} 수산물 안내】\n"
                f"- 출하: {GAETMAEUL_POLICY.origin}\n"
                f"- 배송: {GAETMAEUL_POLICY.logistics_partner} (기본 {GAETMAEUL_POLICY.base_shipping_fee:,}원, {GAETMAEUL_POLICY.free_shipping_threshold:,}원 이상 무료)\n"
                f"- 콜드체인 이상 시 7일 이내 재배송/환불(규정 제17조, 제20조), 파손 선구제(계약서 제11조)"
            )

        # 기본 일반 안내
        return (
            "【교동마을 산지직송 안내】\n"
            "- 교동마을(농산물)과 갯마을(수산물)의 산지 직송 쇼핑몰입니다.\n"
            "- 택배사: 주식회사 시원배송 (익일~모레 배송, 계약서 제4조).\n"
            "- 규정 제4조·제20조에 따라 하자 발생 시 7일 이내 접수 시 고객 선택으로 무상 재배송 또는 전액환불됩니다."
        )

    @classmethod
    def route(cls, utterance: str) -> PolicyRouteResult:
        """발화 전체 분석 및 결과 컨테이너 생성"""
        has_agri = cls._matches_any(utterance, cls.AGRI_PATTERNS)
        has_fish = cls._matches_any(utterance, cls.FISH_PATTERNS)
        categories = cls.detect_categories(utterance)
        primary = cls.resolve_primary_policy(utterance, categories, has_agri, has_fish)
        knowledge_text = cls.get_relevant_knowledge(utterance)

        return PolicyRouteResult(
            primary_category=primary,
            matched_categories=categories,
            is_combined=(primary == PolicyCategory.COMBINED),
            has_agriculture=has_agri,
            has_fishery=has_fish,
            knowledge_text=knowledge_text,
        )

    @classmethod
    def get_official_product(cls, sku_code: str) -> Optional[OfficialProductSKU]:
        """공식 3종 상품 SKU 조회"""
        return get_official_product(sku_code)

    @classmethod
    def evaluate_sugar_claim(cls, sku_code: str, measured_brix: float) -> Dict[str, Any]:
        """공식 상품 당도 미달 판정 (규정 제7조)"""
        return evaluate_product_sugar_claim(sku_code, measured_brix)

    @classmethod
    def evaluate_weight_claim(cls, sku_code: str, measured_weight_kg: float) -> Dict[str, Any]:
        """공식 상품 중량/규격 미달 판정 (규정 제6조)"""
        return evaluate_product_weight_claim(sku_code, measured_weight_kg)


def get_relevant_knowledge(utterance: str) -> str:
    """간편 호출용 헬퍼 함수"""
    return PolicyRouter.get_relevant_knowledge(utterance)


def evaluate_seafood_weight(
    label_weight: float,
    received_weight: float,
    shipped_weight: Optional[float] = None,
) -> Dict[str, Any]:
    """수산물 중량 판정 헬퍼 함수 (세칙 제1조~제12조 준수)

    1. 기준 중량: 출고 중량이 있으면 출고 중량 기준, 없으면 고객 불이익 없이 표기 중량 기준.
    2. 수령 중량과 대조 시, 표기 중량 대비 미달률(%)을 계산.
    3. 허용치: 표기오차 5% + 자연감량 3% = 미달 8% 이내는 정상 범위.
    4. 미달 8% 초과 시: 초과분만이 아니라 '부족분 전체(label_weight - received_weight)'에 대해 부분환불 또는 재배송.
    """
    base_weight = shipped_weight if (shipped_weight is not None and shipped_weight > 0) else label_weight

    deficit_weight = max(0.0, label_weight - received_weight)
    deficit_pct = (deficit_weight / label_weight * 100.0) if label_weight > 0 else 0.0
    is_normal = deficit_pct <= 8.0

    return {
        "label_weight": label_weight,
        "shipped_weight": shipped_weight,
        "received_weight": received_weight,
        "base_weight": base_weight,
        "deficit_weight": round(deficit_weight, 3),
        "deficit_pct": round(deficit_pct, 2),
        "is_normal": is_normal,
        "shortage_weight": round(deficit_weight, 3) if not is_normal else 0.0,
        "action": "explain_loss" if is_normal else "refund_or_reship_entire_shortage",
    }
