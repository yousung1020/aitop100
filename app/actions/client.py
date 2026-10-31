"""
산지 액션 서버 비동기 클라이언트 모듈 (ActionServerClient).
HTTPX 기반으로 공식 액션 API (/api/...) 및 레거시 엔드포인트와 통신하며,
네트워크 장애, 타임아웃, 서버 오류 발생 시 안전한 Fallback을 반환합니다.
대회 필수 헤더(X-Aitop100-Test-Case-Id) 및 공식 접수 상태(SUBMITTED)를 완벽히 지원합니다.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import anyio
import httpx

from app.actions.mock_server import MockActionHandler

FALLBACK_MESSAGE = (
    "현재 산지 전산망 일시 지연으로 인해 이관 접수가 완료되지 못했습니다. "
    "잠시 후 다시 시도해 주시거나 운영 시간(평일 09:00~18:00) 내 고객센터(청년회 CS)로 문의해 주시기 바랍니다."
)

DEFAULT_TEST_CASE_ID = "TC-DEFAULT"


class ActionServerClient:
    """공식 액션 API 및 산지 백엔드 비동기 클라이언트."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: float = 5.0,
        default_test_case_id: Optional[str] = None,
        mock_handler: Optional[MockActionHandler] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        env_url = (os.getenv("ACTION_SERVER_URL") or "").strip()
        self.base_url = (
            base_url
            or (env_url if env_url else "http://localhost:8000")
        ).rstrip("/")
        self.token = token if token is not None else os.getenv("ACTION_SERVER_TOKEN", "")
        self.timeout = timeout
        self.default_test_case_id = (
            default_test_case_id
            or os.getenv("AITOP100_TEST_CASE_ID", DEFAULT_TEST_CASE_ID)
        )
        self.mock_handler = mock_handler
        self._owned_client = False

        if client is not None:
            self._client = client
        elif mock_handler is not None:
            transport = httpx.MockTransport(mock_handler.handle_request)
            self._client = httpx.AsyncClient(
                transport=transport,
                base_url=self.base_url,
                timeout=self.timeout,
            )
            self._owned_client = True
        else:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
            self._owned_client = True

    @property
    def client(self) -> httpx.AsyncClient:
        return self._client

    async def close(self) -> None:
        """클라이언트 리소스 정리"""
        if self._owned_client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _get_headers(self, test_case_id: Optional[str] = None) -> Dict[str, str]:
        """공식 API 요청 필수 헤더 구성."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        tc_id = test_case_id or self.default_test_case_id
        if tc_id:
            headers["X-Aitop100-Test-Case-Id"] = tc_id
        return headers

    def _build_fallback_response(self, error_code: str, error_detail: Optional[str] = None) -> Dict[str, Any]:
        """장애 발생 시 60초 타임아웃 실격을 방지하는 표준 폴백 응답 생성."""
        return {
            "status": "FALLBACK",
            "success": False,
            "error_code": error_code,
            "error_detail": error_detail or error_code,
            "message": FALLBACK_MESSAGE,
            "data": None,
        }

    async def _safe_request(
        self,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        method: str = "POST",
        params: Optional[Dict[str, Any]] = None,
        test_case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """안전한 HTTP 요청 래퍼 (타임아웃, 네트워크, 5xx 에러 및 빈 본문 방어)."""
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        headers = self._get_headers(test_case_id=test_case_id)

        try:
            with anyio.fail_after(self.timeout):
                kwargs: Dict[str, Any] = {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "timeout": self.timeout,
                }
                if params is not None:
                    kwargs["params"] = params
                if payload is not None:
                    kwargs["json"] = payload

                response = await self._client.request(**kwargs)

            # 5xx 서버 오류는 즉시 Fallback 처리
            if response.status_code >= 500:
                return self._build_fallback_response(
                    error_code="SERVER_ERROR",
                    error_detail=f"HTTP {response.status_code}: {response.text}",
                )

            # 응답 본문 파싱 (빈 본문 및 공백 안전 처리)
            res_text = response.text.strip()
            res_data: Dict[str, Any] = {}

            if res_text:
                try:
                    parsed = response.json()
                    if isinstance(parsed, dict):
                        res_data = parsed
                    elif isinstance(parsed, list):
                        res_data = {"items": parsed, "data": parsed}
                    else:
                        res_data = {"data": parsed}
                except Exception as json_err:
                    if response.status_code >= 400:
                        return {
                            "status": "FAILED",
                            "success": False,
                            "status_code": response.status_code,
                            "error_code": f"HTTP_{response.status_code}",
                            "message": res_text,
                            "data": None,
                        }
                    return self._build_fallback_response(
                        error_code="JSON_PARSE_ERROR",
                        error_detail=str(json_err),
                    )
            elif response.status_code >= 400:
                # 400/404 등 빈 본문 에러
                return {
                    "status": "FAILED",
                    "success": False,
                    "status_code": response.status_code,
                    "error_code": f"HTTP_{response.status_code}",
                    "message": f"HTTP error {response.status_code}",
                    "data": None,
                }

            # 성공 상태 플래그 판정 (SUBMITTED, SUCCESS, 2xx 성공 판정)
            request_status = res_data.get("request_status")
            status_val = res_data.get("status")

            if request_status in ("SUBMITTED", "COMPLETED", "APPROVED"):
                res_data["success"] = True
                res_data.setdefault("status", "SUCCESS")
            elif status_val == "SUCCESS":
                res_data["success"] = True
            elif 200 <= response.status_code < 300:
                if status_val == "FAILED":
                    res_data["success"] = False
                else:
                    res_data["success"] = True
                    res_data.setdefault("status", "SUCCESS")
            else:
                res_data["success"] = False
                res_data.setdefault("status", "FAILED")

            res_data.setdefault("status_code", response.status_code)
            return res_data

        except (httpx.TimeoutException, TimeoutError) as exc:
            return self._build_fallback_response(
                error_code="TIMEOUT",
                error_detail=f"Request timed out after {self.timeout}s: {exc}",
            )
        except httpx.NetworkError as exc:
            return self._build_fallback_response(
                error_code="NETWORK_ERROR",
                error_detail=f"Network error occurred: {exc}",
            )
        except Exception as exc:
            return self._build_fallback_response(
                error_code="UNEXPECTED_CLIENT_ERROR",
                error_detail=str(exc),
            )

    # =========================================================================
    # 공식 OpenAPI 3.1.0 액션 API 메서드 (/api/...)
    # =========================================================================

    # API-01: 상품 조회 (GET /api/products/{sku})
    async def get_product(self, sku: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            f"/api/products/{quote(sku, safe='')}", method="GET", test_case_id=test_case_id
        )

    # API-02: 품목별 상품 검색 (GET /api/products?item={item})
    async def search_products(self, item: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            "/api/products", method="GET", params={"item": item}, test_case_id=test_case_id
        )

    # API-03: 로트 조회 (GET /api/lots/{lot_id})
    async def get_lot(self, lot_id: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            f"/api/lots/{quote(lot_id, safe='')}", method="GET", test_case_id=test_case_id
        )

    # API-04: 로트 조사 조회 (GET /api/lots/{lot_id}/investigation)
    async def get_lot_investigation(self, lot_id: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            f"/api/lots/{quote(lot_id, safe='')}/investigation", method="GET", test_case_id=test_case_id
        )

    # API-05: 회원별 상담 이력 검색 (GET /api/tickets?member_id={member_id})
    async def search_tickets_by_member(self, member_id: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            "/api/tickets", method="GET", params={"member_id": member_id}, test_case_id=test_case_id
        )

    # API-06: 로트별 상담 이력 검색 (GET /api/tickets?lot_id={lot_id})
    async def search_tickets_by_lot(self, lot_id: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            "/api/tickets", method="GET", params={"lot_id": lot_id}, test_case_id=test_case_id
        )

    # API-07: 주문 조회 (GET /api/orders/{order_no})
    async def get_order(self, order_no: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            f"/api/orders/{quote(order_no, safe='')}", method="GET", test_case_id=test_case_id
        )

    # API-08: 회원별 주문 검색 (GET /api/orders?member_id={member_id})
    async def search_orders_by_member(self, member_id: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            "/api/orders", method="GET", params={"member_id": member_id}, test_case_id=test_case_id
        )

    # API-10: 배송 조회 (GET /api/shipments/{shipment_id})
    async def get_shipment(self, shipment_id: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            f"/api/shipments/{quote(shipment_id, safe='')}", method="GET", test_case_id=test_case_id
        )

    # API-11: 주문별 배송 검색 (GET /api/shipments?order_no={order_no})
    async def search_shipments_by_order(self, order_no: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            "/api/shipments", method="GET", params={"order_no": order_no}, test_case_id=test_case_id
        )

    # 별칭 (호환성)
    async def search_deliveries_by_order(self, order_no: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self.search_shipments_by_order(order_no=order_no, test_case_id=test_case_id)

    # API-12: 조합원 조회 (GET /api/members/{member_id})
    async def get_member(self, member_id: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            f"/api/members/{quote(member_id, safe='')}", method="GET", test_case_id=test_case_id
        )

    # API-13: 이름 조합원 검색 (GET /api/members?name={name})
    async def search_members_by_name(self, name: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            "/api/members", method="GET", params={"name": name}, test_case_id=test_case_id
        )

    # API-16: 회원별 쿠폰 검색 (GET /api/coupons?member_id={member_id})
    async def search_coupons_by_member(self, member_id: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            "/api/coupons", method="GET", params={"member_id": member_id}, test_case_id=test_case_id
        )

    # API-17: 결제 조회 (GET /api/payments/{approval_no})
    async def get_payment(self, approval_no: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            f"/api/payments/{quote(approval_no, safe='')}", method="GET", test_case_id=test_case_id
        )

    # API-18: 주문별 결제 검색 (GET /api/payments?order_no={order_no})
    async def search_payments_by_order(self, order_no: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            "/api/payments", method="GET", params={"order_no": order_no}, test_case_id=test_case_id
        )

    # API-20: 프로모션 조회 (GET /api/promos/{code})
    async def get_promo(self, code: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._safe_request(
            f"/api/promos/{quote(code, safe='')}", method="GET", test_case_id=test_case_id
        )

    # API-24: 배송지 변경 접수 (POST /api/orders/{order_no}/address-change-requests)
    async def change_address(
        self,
        order_no: str,
        new_address: str,
        test_case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        POST /api/orders/{order_no}/address-change-requests
        공식 스키마: body에는 new_address 단일 필드만 허용 (추가 필드 False)
        """
        if not order_no or not order_no.strip():
            return {
                "status": "FAILED",
                "success": False,
                "error_code": "MISSING_ORDER_NO",
                "message": "주문번호를 입력해 주세요.",
            }
        if not new_address or not new_address.strip():
            return {
                "status": "FAILED",
                "success": False,
                "error_code": "MISSING_ADDRESS",
                "message": "변경할 신규 배송지 주소를 입력해 주세요.",
            }

        payload = {"new_address": new_address.strip()}
        return await self._safe_request(
            f"/api/orders/{quote(order_no.strip(), safe='')}/address-change-requests",
            payload=payload,
            method="POST",
            test_case_id=test_case_id,
        )

    # API-28: 재배송 접수 (POST /api/shipments/{shipment_id}/reship-requests)
    async def request_reship(
        self,
        shipment_id: str,
        test_case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self._safe_request(
            f"/api/shipments/{quote(shipment_id, safe='')}/reship-requests",
            payload={},
            method="POST",
            test_case_id=test_case_id,
        )

    # 편의 별칭
    async def request_redelivery(
        self,
        order_no: str,
        shipment_id: Optional[str] = None,
        test_case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        sid = shipment_id or order_no
        return await self.request_reship(shipment_id=sid, test_case_id=test_case_id)

    # API-29: 환불 신청 (POST /api/refunds)
    async def request_refund(
        self,
        order_no: str,
        amount: int,
        reason: str,
        test_case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "order_no": order_no,
            "amount": int(amount),
            "reason": reason,
        }
        return await self._safe_request(
            "/api/refunds",
            payload=payload,
            method="POST",
            test_case_id=test_case_id,
        )

    # API-32: 현금영수증 발행 접수 (POST /api/payments/{approval_no}/cash-receipt-requests)
    async def issue_cash_receipt(
        self,
        approval_no: str,
        receipt_number: str,
        test_case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {"receipt_number": receipt_number}
        return await self._safe_request(
            f"/api/payments/{quote(approval_no, safe='')}/cash-receipt-requests",
            payload=payload,
            method="POST",
            test_case_id=test_case_id,
        )

    # API-33: 쿠폰 발급 접수 (POST /api/members/{member_id}/coupon-issue-requests)
    async def issue_coupon(
        self,
        member_id: str,
        promo_code: str,
        test_case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {"promo_code": promo_code}
        return await self._safe_request(
            f"/api/members/{quote(member_id, safe='')}/coupon-issue-requests",
            payload=payload,
            method="POST",
            test_case_id=test_case_id,
        )

    # API-35: 에스컬레이션 (POST /api/escalations)
    async def escalate(
        self,
        lane: str,
        reason: str,
        order_no: Optional[str] = None,
        test_case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "lane": lane,
            "reason": reason,
        }
        return await self._safe_request(
            "/api/escalations",
            payload=payload,
            method="POST",
            test_case_id=test_case_id,
        )

    # =========================================================================
    # 하위 호환성 레거시 프로토콜 (/v1/...)
    # =========================================================================

    async def reset_account_session(
        self,
        user_key: str,
        phone_number: str,
        reason: str = "로그인 오류 및 세션 잠김 해제",
    ) -> Dict[str, Any]:
        payload = {
            "user_key": user_key,
            "phone_number": phone_number,
            "reason": reason,
        }
        return await self._safe_request("/v1/auth/reset-session", payload=payload)

    async def reset_auth_session(
        self,
        user_key: str,
        reason: str = "세션 리셋",
        phone_number: str = "010-0000-0000",
    ) -> Dict[str, Any]:
        return await self.reset_account_session(user_key=user_key, phone_number=phone_number, reason=reason)

    async def change_shipping_address(
        self,
        order_id: str,
        user_key: str,
        recipient_name: str,
        recipient_phone: str,
        zipcode: str,
        new_address: str,
        detailed_address: str = "",
    ) -> Dict[str, Any]:
        if not order_id.strip():
            return {
                "status": "FAILED",
                "success": False,
                "error_code": "MISSING_ORDER_ID",
                "message": "주문번호를 확인해 주세요.",
            }
        payload = {
            "order_id": order_id,
            "user_key": user_key,
            "recipient_name": recipient_name,
            "recipient_phone": recipient_phone,
            "zipcode": zipcode,
            "new_zipcode": zipcode,
            "new_address": new_address,
            "detailed_address": detailed_address,
        }
        return await self._safe_request(
            f"/v1/orders/{quote(order_id, safe='')}/shipping-address",
            payload=payload,
            method="PATCH",
        )

    async def update_shipping_address(
        self,
        order_id: str,
        new_address: str,
        zipcode: str = "",
        user_key: str = "",
        recipient_name: str = "",
        recipient_phone: str = "",
        detailed_address: str = "",
    ) -> Dict[str, Any]:
        return await self.change_shipping_address(
            order_id=order_id,
            user_key=user_key,
            recipient_name=recipient_name,
            recipient_phone=recipient_phone,
            zipcode=zipcode,
            new_address=new_address,
            detailed_address=detailed_address,
        )

    async def create_escalation_ticket(
        self,
        user_key: str,
        category: str,
        customer_name: str,
        contact: str,
        issue_summary: str,
        order_id: Optional[str] = None,
        claim_amount: int = 0,
        requested_resolution: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "user_key": user_key,
            "category": category,
            "customer_name": customer_name,
            "contact": contact,
            "summary": issue_summary,
            "order_id": order_id,
            "claim_amount": claim_amount,
            "requested_resolution": requested_resolution,
        }
        return await self._safe_request("/v1/support/escalate", payload=payload)

    async def escalate_to_manager(
        self,
        user_key: str,
        category: str,
        summary: str,
        customer_name: str = "고객",
        contact: str = "",
        claim_amount: int = 0,
        order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self.create_escalation_ticket(
            user_key=user_key,
            category=category,
            customer_name=customer_name,
            contact=contact,
            issue_summary=summary,
            order_id=order_id,
            claim_amount=claim_amount,
        )
