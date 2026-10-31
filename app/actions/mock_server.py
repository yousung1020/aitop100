"""
산지 액션 서버 Mock 핸들러 모듈 (MockActionHandler).
외부 백엔드 액션 서버가 없거나 단위/통합 테스트 환경에서
공식 액션 API (/api/...) 40개 스키마 및 레거시 3대 전산 업무를 모의 수행합니다.
대회 필수 헤더(X-Aitop100-Test-Case-Id) 검증 및 기록을 지원합니다.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import unquote
from uuid import uuid4

import anyio
import httpx


class MockActionHandler:
    """공식 OpenAPI 3.1.0 규격 지원 산지 백엔드 액션 모의 핸들러."""

    def __init__(self):
        self.auth_counter: int = 0
        self.ticket_counter: int = 0
        self.orders: Dict[str, Dict[str, Any]] = {
            # 기본 단위 테스트용 주문
            "ORDER-PENDING-001": {
                "order_no": "ORDER-PENDING-001",
                "order_id": "ORDER-PENDING-001",
                "user_key": "user_kakao_111",
                "member_id": "user_kakao_111",
                "status": "ORDER_CONFIRMED",
                "recipient_name": "홍길동",
                "recipient_phone": "010-1111-2222",
                "zipcode": "06234",
                "address": "서울특별시 강남구 테헤란로 123",
                "detailed_address": "4층",
                "shipped": False,
                "amount": 25000,
            },
            "ORDER-SHIPPED-001": {
                "order_no": "ORDER-SHIPPED-001",
                "order_id": "ORDER-SHIPPED-001",
                "user_key": "user_kakao_222",
                "member_id": "user_kakao_222",
                "status": "SHIPPED",
                "recipient_name": "김철수",
                "recipient_phone": "010-3333-4444",
                "zipcode": "13494",
                "address": "경기도 성남시 분당구 판교역로 166",
                "detailed_address": "8층",
                "shipped": True,
                "amount": 48000,
            },
            # 공개 TC L-03 주문 (서지호)
            "100100003": {
                "order_no": "100100003",
                "order_id": "100100003",
                "user_key": "user_kakao_seo",
                "member_id": "M-SEO-01",
                "customer_name": "서지호",
                "recipient_name": "서지호",
                "recipient_phone": "019-2314-5231",
                "status": "ORDER_CONFIRMED",
                "address": "서울시 영등포구 여의대로 1",
                "detailed_address": "",
                "shipped": False,
                "amount": 38000,
            },
            # 공개 TC L-05 주문 (임태경, 무통장입금)
            "100100005": {
                "order_no": "100100005",
                "order_id": "100100005",
                "user_key": "user_kakao_lim",
                "member_id": "M-LIM-01",
                "customer_name": "임태경",
                "recipient_name": "임태경",
                "payment_method": "BANK_TRANSFER",
                "approval_no": "PAY-3706-0003",
                "status": "PAID",
                "shipped": True,
                "amount": 42000,
            },
            # 공개 TC L-11 주문 (강은비, 수박 8kg 하자)
            "100100011": {
                "order_no": "100100011",
                "order_id": "100100011",
                "user_key": "user_kakao_kang",
                "member_id": "M-KANG-01",
                "customer_name": "강은비",
                "product_name": "교동 고당도 수박 8kg",
                "lot_id": "KD-WTM-370624-03",
                "status": "DELIVERED",
                "shipped": True,
                "amount": 34900,
            },
            # 공개 TC L-23 주문 (타 계정 주문)
            "100100033": {
                "order_no": "100100033",
                "order_id": "100100033",
                "user_key": "user_other_secret",
                "member_id": "M-OTHER-99",
                "customer_name": "박타인",
                "recipient_name": "박타인",
                "address": "서울특별시 종로구 사직로 161",
                "detailed_address": "101동 202호",
                "status": "SHIPPED",
                "shipped": True,
                "amount": 55000,
            },
            # 공개 TC L-47 주문 (석민경, 가격 인하 차액 요구)
            "100100047": {
                "order_no": "100100047",
                "order_id": "100100047",
                "user_key": "MB-77017",
                "member_id": "MB-77017",
                "customer_name": "석민경",
                "recipient_name": "석민경",
                "recipient_phone": "019-2314-9440",
                "sku": "WTM-STD-8",
                "product_name": "교동 고당도 수박 8kg (표준)",
                "amount": 32000,
                "purchased_price": 32000,
                "status": "DELIVERED",
                "shipped": True,
                "ordered_at": "2037-06-25T14:20:00Z",
            },
        }
        self.products: Dict[str, Dict[str, Any]] = {
            "WTM-STD-8": {
                "sku": "WTM-STD-8",
                "name": "교동 고당도 수박 8kg (표준)",
                "price": 27900,
                "normal_price": 27900,
                "status": "AVAILABLE",
            },
            "WTM-08": {
                "sku": "WTM-08",
                "name": "교동 고당도 수박 8kg",
                "price": 34900,
                "normal_price": 34900,
                "status": "AVAILABLE",
            },
        }
        self.members: Dict[str, Dict[str, Any]] = {
            "MB-77017": {"member_id": "MB-77017", "name": "석민경", "phone": "019-2314-9440", "grade": "REGULAR"},
            "MB-77023": {"member_id": "MB-77023", "name": "윤재호", "phone": "019-2314-8326", "grade": "REGULAR"},
            "MB-77005": {"member_id": "MB-77005", "name": "임태경", "phone": "019-2314-9701", "grade": "REGULAR"},
            "M-LIM-01": {"member_id": "M-LIM-01", "name": "임태경", "phone": "019-2314-9701", "grade": "REGULAR"},
            "M-SEO-01": {"member_id": "M-SEO-01", "name": "서지호", "phone": "019-2314-5231", "grade": "REGULAR"},
            "M-KANG-01": {"member_id": "M-KANG-01", "name": "강은비", "phone": "019-2314-4165", "grade": "REGULAR"},
            "MB-77016": {"member_id": "MB-77016", "name": "박도매", "phone": "019-2314-8888", "grade": "REGULAR"},
        }
        self.submitted_requests: Dict[str, Dict[str, Any]] = {}
        self.delay: float = 0.0
        self.force_status_code: Optional[int] = None
        self.force_network_error: bool = False
        self.history: List[Dict[str, Any]] = []

    def register_order(
        self,
        order_id: str,
        user_key: str = "test_user",
        status: str = "ORDER_CONFIRMED",
        shipped: bool = False,
        recipient_name: str = "홍길동",
        recipient_phone: str = "010-1234-5678",
        zipcode: str = "06234",
        address: str = "서울특별시 강남구 테헤란로 123",
        detailed_address: str = "4층",
        amount: int = 30000,
    ) -> None:
        """테스트용 주문 데이터 동적 등록"""
        self.orders[order_id] = {
            "order_no": order_id,
            "order_id": order_id,
            "user_key": user_key,
            "member_id": user_key,
            "status": status,
            "shipped": shipped or (status in ("SHIPPED", "DELIVERED")),
            "recipient_name": recipient_name,
            "recipient_phone": recipient_phone,
            "zipcode": zipcode,
            "address": address,
            "detailed_address": detailed_address,
            "amount": amount,
        }

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """주문 정보 조회"""
        return self.orders.get(order_id)

    async def handle_request(self, request: httpx.Request) -> httpx.Response:
        """httpx.MockTransport와 연동되는 비동기 요청 처리기"""
        # 강제 네트워크 장애 시뮬레이션
        if self.force_network_error:
            raise httpx.ConnectError("Mock network connection error", request=request)

        # 지연 시간 시뮬레이션
        if self.delay > 0:
            await anyio.sleep(self.delay)

        # 강제 HTTP 상태 코드 시뮬레이션
        if self.force_status_code is not None:
            return httpx.Response(
                status_code=self.force_status_code,
                json={
                    "status": "ERROR",
                    "error_code": f"HTTP_{self.force_status_code}",
                    "message": f"Server forced error response {self.force_status_code}",
                },
                request=request,
            )

        url_path = request.url.path
        method = request.method.upper()
        tc_id = request.headers.get("X-Aitop100-Test-Case-Id", "")

        try:
            body_bytes = request.content
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            body = {}

        # 요청 기록 저장
        self.history.append({
            "method": method,
            "path": url_path,
            "headers": dict(request.headers),
            "body": body,
            "query": dict(request.url.params),
            "test_case_id": tc_id,
        })

        # =====================================================================
        # 테스트 전용 특수 엔드포인트 (빈 본문 에러 시뮬레이션)
        # =====================================================================
        if url_path == "/api/test/empty-400":
            return httpx.Response(status_code=400, content=b"", request=request)
        if url_path == "/api/test/empty-404":
            return httpx.Response(status_code=404, content=b"", request=request)

        # =====================================================================
        # 공식 OpenAPI 3.1.0 엔드포인트 (/api/...)
        # =====================================================================

        # API-24: 배송지 변경 접수 (POST /api/orders/{order_no}/address-change-requests)
        addr_match = re.fullmatch(r"/api/orders/([^/]+)/address-change-requests", url_path)
        if addr_match and method == "POST":
            order_no = unquote(addr_match.group(1))
            return self._handle_official_address_change(order_no, body, request)

        # API-11: 주문별 배송 검색 (GET /api/shipments?order_no=...)
        if url_path == "/api/shipments" and method == "GET":
            order_no = request.url.params.get("order_no")
            return self._handle_official_search_shipments(order_no, request)

        # API-10: 배송 조회 (GET /api/shipments/{shipment_id})
        shipment_match = re.fullmatch(r"/api/shipments/([^/]+)", url_path)
        if shipment_match and method == "GET":
            shipment_id = unquote(shipment_match.group(1))
            return httpx.Response(
                200,
                json={
                    "shipment_id": shipment_id,
                    "order_no": "ORDER-PENDING-001",
                    "status": "IN_TRANSIT",
                    "tracking_no": "TR-KD-01-9988",
                    "carrier": "시원배송",
                },
                request=request,
            )

        # API-07: 주문 조회 (GET /api/orders/{order_no})
        order_match = re.fullmatch(r"/api/orders/([^/]+)", url_path)
        if order_match and method == "GET":
            order_no = unquote(order_match.group(1))
            order_info = self.orders.get(order_no)
            if order_info:
                return httpx.Response(200, json=order_info, request=request)
            return httpx.Response(
                404,
                json={"error_code": "ORDER_NOT_FOUND", "message": f"주문 {order_no}을(를) 찾을 수 없습니다."},
                request=request,
            )

        # API-08: 회원별 주문 검색 (GET /api/orders?member_id=...)
        if url_path == "/api/orders" and method == "GET":
            member_id = request.url.params.get("member_id")
            matched = [o for o in self.orders.values() if o.get("member_id") == member_id or o.get("user_key") == member_id]
            return httpx.Response(200, json=matched, request=request)

        # API-01: 상품 조회 (GET /api/products/{sku})
        prod_match = re.fullmatch(r"/api/products/([^/]+)", url_path)
        if prod_match and method == "GET":
            sku = unquote(prod_match.group(1))
            if sku in self.products:
                return httpx.Response(200, json=self.products[sku], request=request)
            return httpx.Response(
                200,
                json={"sku": sku, "name": "교동 고당도 수박 8kg", "price": 34900, "status": "AVAILABLE"},
                request=request,
            )

        # API-02: 품목별 상품 검색 (GET /api/products?item=...)
        if url_path == "/api/products" and method == "GET":
            item = request.url.params.get("item", "")
            return httpx.Response(
                200,
                json=[{"sku": "WTM-08", "name": f"교동 {item}", "price": 30000}],
                request=request,
            )

        # API-03: 로트 조회 (GET /api/lots/{lot_id})
        lot_match = re.fullmatch(r"/api/lots/([^/]+)", url_path)
        if lot_match and method == "GET":
            lot_id = unquote(lot_match.group(1))
            return httpx.Response(
                200,
                json={
                    "lot_id": lot_id,
                    "sku": "WTM-08",
                    "product_name": "교동 고당도 수박 8kg",
                    "harvest_date": "2037-06-24",
                    "origin": "제주특별자치도 교동마을",
                },
                request=request,
            )

        # API-04: 로트 조사 조회 (GET /api/lots/{lot_id}/investigation)
        lot_inv_match = re.fullmatch(r"/api/lots/([^/]+)/investigation", url_path)
        if lot_inv_match and method == "GET":
            lot_id = unquote(lot_inv_match.group(1))
            return httpx.Response(
                200,
                json={
                    "lot_id": lot_id,
                    "investigation_id": "INV-370624-001",
                    "status": "NOT_STARTED",
                    "findings": None,
                },
                request=request,
            )

        # API-05 / API-06: 상담 이력 검색 (GET /api/tickets?...)
        if url_path == "/api/tickets" and method == "GET":
            lot_id = request.url.params.get("lot_id")
            member_id = request.url.params.get("member_id")
            return httpx.Response(200, json=[], request=request)

        # API-12: 조합원 조회 (GET /api/members/{member_id})
        member_match = re.fullmatch(r"/api/members/([^/]+)", url_path)
        if member_match and method == "GET":
            member_id = unquote(member_match.group(1))
            if member_id in self.members:
                return httpx.Response(200, json=self.members[member_id], request=request)
            return httpx.Response(
                200,
                json={"member_id": member_id, "name": "서지호", "phone": "019-2314-5231", "grade": "REGULAR"},
                request=request,
            )

        # API-13: 이름 조합원 검색 (GET /api/members?name=...)
        if url_path == "/api/members" and method == "GET":
            name = request.url.params.get("name", "")
            return httpx.Response(
                200,
                json=[{"member_id": "M-SEO-01", "name": name, "phone": "019-2314-5231"}],
                request=request,
            )

        # API-16: 회원별 쿠폰 검색 (GET /api/coupons?member_id=...)
        if url_path == "/api/coupons" and method == "GET":
            member_id = request.url.params.get("member_id")
            return httpx.Response(200, json=[], request=request)

        # API-17: 결제 조회 (GET /api/payments/{approval_no})
        pay_match = re.fullmatch(r"/api/payments/([^/]+)", url_path)
        if pay_match and method == "GET":
            approval_no = unquote(pay_match.group(1))
            return httpx.Response(
                200,
                json={
                    "approval_no": approval_no,
                    "order_no": "100100005",
                    "method": "BANK_TRANSFER",
                    "amount": 42000,
                    "status": "PAID",
                },
                request=request,
            )

        # API-18: 주문별 결제 검색 (GET /api/payments?order_no=...)
        if url_path == "/api/payments" and method == "GET":
            order_no = request.url.params.get("order_no")
            return httpx.Response(
                200,
                json=[{"approval_no": "PAY-3706-0003", "order_no": order_no, "method": "BANK_TRANSFER"}],
                request=request,
            )

        # API-20: 프로모션 조회 (GET /api/promos/{code})
        promo_match = re.fullmatch(r"/api/promos/([^/]+)", url_path)
        if promo_match and method == "GET":
            code = unquote(promo_match.group(1))
            if code in ("SUBAK15", "CARE3000"):
                return httpx.Response(200, json={"code": code, "discount_pct": 15, "valid": True}, request=request)
            return httpx.Response(404, json={"error_code": "PROMO_NOT_FOUND"}, request=request)

        # API-28: 재배송 접수 (POST /api/shipments/{shipment_id}/reship-requests)
        reship_match = re.fullmatch(r"/api/shipments/([^/]+)/reship-requests", url_path)
        if reship_match and method == "POST":
            shipment_id = unquote(reship_match.group(1))
            idem_key = f"RESHIP:{shipment_id}"
            if idem_key in self.submitted_requests:
                return httpx.Response(200, json=self.submitted_requests[idem_key], request=request)
            self.ticket_counter += 1
            res_data = {
                "request_id": f"RESHIP-{self.ticket_counter:04d}",
                "shipment_id": shipment_id,
                "request_status": "SUBMITTED",
                "requested_at": "2037-06-30T17:37:00Z",
            }
            self.submitted_requests[idem_key] = res_data
            return httpx.Response(200, json=res_data, request=request)

        # API-29: 환불 신청 (POST /api/refunds)
        if url_path == "/api/refunds" and method == "POST":
            order_no = body.get("order_no", "")
            amount = body.get("amount", 0)
            idem_key = f"REFUND:{order_no}"
            if idem_key in self.submitted_requests:
                return httpx.Response(200, json=self.submitted_requests[idem_key], request=request)
            self.ticket_counter += 1
            res_data = {
                "refund_id": f"REF-{self.ticket_counter:04d}",
                "order_no": order_no,
                "amount": amount,
                "request_status": "SUBMITTED",
                "requested_at": "2037-06-30T17:37:00Z",
            }
            self.submitted_requests[idem_key] = res_data
            return httpx.Response(200, json=res_data, request=request)

        # API-32: 현금영수증 발행 접수 (POST /api/payments/{approval_no}/cash-receipt-requests)
        cr_match = re.fullmatch(r"/api/payments/([^/]+)/cash-receipt-requests", url_path)
        if cr_match and method == "POST":
            approval_no = unquote(cr_match.group(1))
            receipt_number = body.get("receipt_number", "")
            idem_key = f"CR:{approval_no}"
            if idem_key in self.submitted_requests:
                return httpx.Response(200, json=self.submitted_requests[idem_key], request=request)
            self.ticket_counter += 1
            res_data = {
                "request_id": f"CR-{self.ticket_counter:04d}",
                "approval_no": approval_no,
                "receipt_number": receipt_number,
                "request_status": "SUBMITTED",
                "requested_at": "2037-06-30T18:54:00Z",
            }
            self.submitted_requests[idem_key] = res_data
            return httpx.Response(200, json=res_data, request=request)

        # API-33: 쿠폰 발급 접수 (POST /api/members/{member_id}/coupon-issue-requests)
        coupon_match = re.fullmatch(r"/api/members/([^/]+)/coupon-issue-requests", url_path)
        if coupon_match and method == "POST":
            member_id = unquote(coupon_match.group(1))
            promo_code = body.get("promo_code", "")
            idem_key = f"COUPON:{member_id}:{promo_code}"
            if idem_key in self.submitted_requests:
                return httpx.Response(200, json=self.submitted_requests[idem_key], request=request)
            self.ticket_counter += 1
            res_data = {
                "request_id": f"COUPON-{self.ticket_counter:04d}",
                "member_id": member_id,
                "promo_code": promo_code,
                "request_status": "SUBMITTED",
                "requested_at": "2037-06-30T17:44:00Z",
            }
            self.submitted_requests[idem_key] = res_data
            return httpx.Response(200, json=res_data, request=request)

        # API-35: 에스컬레이션 (POST /api/escalations)
        if url_path == "/api/escalations" and method == "POST":
            lane = body.get("lane", "LANE2_HANDOFF")
            reason = body.get("reason", "")
            idem_key = f"ESC:{lane}:{reason.strip()}"
            if idem_key in self.submitted_requests:
                return httpx.Response(200, json=self.submitted_requests[idem_key], request=request)
            self.ticket_counter += 1
            res_data = {
                "escalation_id": f"ESC-{self.ticket_counter:04d}",
                "lane": lane,
                "reason": reason,
                "status": "ASSIGNED",
                "assigned_to": "이민준 (청년회 CS총괄)",
                "requested_at": "2037-06-30T17:37:00Z",
            }
            self.submitted_requests[idem_key] = res_data
            return httpx.Response(200, json=res_data, request=request)

        # =====================================================================
        # 하위 호환성 레거시 엔드포인트 (/v1/...)
        # =====================================================================

        if url_path == "/v1/auth/reset-session" and method == "POST":
            return self._handle_reset_session(body, request)

        if re.fullmatch(r"/v1/orders/[^/]+/shipping-address", url_path) and method == "PATCH":
            return self._handle_change_address(url_path, body, request)

        if url_path == "/v1/support/escalate" and method == "POST":
            return self._handle_escalate_ticket(body, request)

        # 라우트 미매칭 시 404
        return httpx.Response(
            status_code=404,
            json={"status": "FAILED", "error_code": "NOT_FOUND", "message": f"Endpoint {url_path} not found"},
            request=request,
        )

    # =====================================================================
    # 공식 핸들러 구현부
    # =====================================================================

    def _handle_official_address_change(self, order_no: str, body: Dict[str, Any], request: httpx.Request) -> httpx.Response:
        """API-24 공식 주소 변경 접수 처리."""
        new_address = body.get("new_address")
        if not new_address:
            return httpx.Response(
                400,
                json={"error_code": "INVALID_BODY", "message": "new_address 필드가 필요합니다."},
                request=request,
            )

        idem_key = f"ADDR:{order_no}"
        if idem_key in self.submitted_requests:
            existing = dict(self.submitted_requests[idem_key])
            existing["new_address"] = new_address
            self.submitted_requests[idem_key] = existing
            return httpx.Response(200, json=existing, request=request)

        self.ticket_counter += 1
        req_id = f"REQ-{order_no[-4:]}" if order_no[-4:].isdigit() else f"REQ-{self.ticket_counter:04d}"
        res_data = {
            "request_id": req_id,
            "order_no": order_no,
            "new_address": new_address,
            "request_status": "SUBMITTED",
            "requested_at": "2037-06-30T15:16:00Z",
        }
        self.submitted_requests[idem_key] = res_data
        return httpx.Response(200, json=res_data, request=request)

    def _handle_official_search_shipments(self, order_no: Optional[str], request: httpx.Request) -> httpx.Response:
        """API-11 공식 배송 검색 처리."""
        if not order_no:
            return httpx.Response(400, json={"error_code": "MISSING_ORDER_NO"}, request=request)

        # ORDER-PENDING-001 또는 100100003(L-03)은 집하 전(빈 배열)
        if order_no in ("ORDER-PENDING-001", "100100003"):
            return httpx.Response(200, json=[], request=request)

        # ORDER-SHIPPED-001은 출고 완료 상태
        if order_no == "ORDER-SHIPPED-001":
            return httpx.Response(
                200,
                json=[{
                    "shipment_id": "SHIP-001",
                    "order_no": order_no,
                    "status": "SHIPPED",
                    "carrier": "시원배송",
                    "tracking_no": "TR-KD-01-8899",
                }],
                request=request,
            )

        # 등록된 주문에 대한 배송 상태 검사
        order_info = self.orders.get(order_no)
        if order_info and order_info.get("shipped"):
            return httpx.Response(
                200,
                json=[{
                    "shipment_id": f"SHIP-{order_no}",
                    "order_no": order_no,
                    "status": "SHIPPED",
                    "carrier": "시원배송",
                    "tracking_no": f"TR-KD-01-{order_no[-4:]}",
                }],
                request=request,
            )

        # 기본은 집하 전 빈 배열 반환
        return httpx.Response(200, json=[], request=request)

    # =====================================================================
    # 레거시 핸들러 구현부 (/v1/...)
    # =====================================================================

    def _handle_reset_session(self, body: Dict[str, Any], request: httpx.Request) -> httpx.Response:
        user_key = body.get("user_key")
        phone_number = body.get("phone_number")
        reason = body.get("reason", "비밀번호 분실 및 세션 잠김")

        if not user_key or not phone_number:
            return httpx.Response(
                status_code=400,
                json={
                    "status": "FAILED",
                    "error_code": "INVALID_PARAMS",
                    "message": "user_key와 phone_number는 필수 파라미터입니다.",
                },
                request=request,
            )

        clean_phone = phone_number.replace("-", "").strip()
        if len(clean_phone) < 10 or not clean_phone.isdigit():
            return httpx.Response(
                status_code=400,
                json={
                    "status": "FAILED",
                    "error_code": "INVALID_PHONE_NUMBER",
                    "message": "유효하지 않은 휴대폰 번호 형식입니다.",
                },
                request=request,
            )

        self.auth_counter += 1
        ticket_id = f"AUTH-20370630-{self.auth_counter:04d}"
        verification_code = f"{849200 + (self.auth_counter % 1000):06d}"

        return httpx.Response(
            status_code=200,
            json={
                "status": "SUCCESS",
                "data": {
                    "reset_ticket_id": ticket_id,
                    "verification_code": verification_code,
                    "verification_url": f"https://gyodong-live.com/auth/verify?t={ticket_id}",
                    "expires_at": "2037-06-30T17:30:00+09:00",
                    "reason": reason,
                },
            },
            request=request,
        )

    def _handle_change_address(self, path: str, body: Dict[str, Any], request: httpx.Request) -> httpx.Response:
        order_id = unquote(path.split("/")[3])
        if body.get("order_id", order_id) != order_id:
            return httpx.Response(400, json={
                "status": "FAILED", "error_code": "ORDER_ID_MISMATCH",
                "message": "주문번호를 확인해 주세요.",
            }, request=request)

        new_address = body.get("new_address")
        detailed_address = body.get("detailed_address", "")
        zipcode = body.get("zipcode") or body.get("new_zipcode", "")
        recipient_name = body.get("recipient_name", "")
        recipient_phone = body.get("recipient_phone", "")

        if not new_address:
            return httpx.Response(
                status_code=400,
                json={
                    "status": "FAILED",
                    "error_code": "MISSING_ADDRESS",
                    "message": "변경할 신규 배송지 주소가 누락되었습니다.",
                },
                request=request,
            )

        order_info = self.orders.get(order_id)
        if order_info is None:
            return httpx.Response(
                status_code=404,
                json={
                    "status": "FAILED",
                    "error_code": "ORDER_NOT_FOUND",
                    "message": "해당 주문을 찾을 수 없습니다.",
                },
                request=request,
            )

        user_key = body.get("user_key")
        if not user_key or order_info.get("user_key") != user_key:
            return httpx.Response(
                status_code=403,
                json={
                    "status": "FAILED",
                    "error_code": "FORBIDDEN",
                    "message": "해당 주문에 대한 접근 권한이 없습니다.",
                },
                request=request,
            )

        if order_info.get("shipped") is True or order_info.get("status") in ("SHIPPED", "DELIVERED"):
            return httpx.Response(
                status_code=200,
                json={
                    "status": "FAILED",
                    "error_code": "ALREADY_SHIPPED",
                    "message": "해당 주문은 이미 산지 출고 및 송장 집하가 완료되어 배송지 변경이 불가합니다.",
                },
                request=request,
            )

        full_address = f"{new_address} {detailed_address}".strip()
        order_info["address"] = new_address
        order_info["detailed_address"] = detailed_address
        order_info["zipcode"] = zipcode
        if recipient_name:
            order_info["recipient_name"] = recipient_name
        if recipient_phone:
            order_info["recipient_phone"] = recipient_phone

        return httpx.Response(
            status_code=200,
            json={
                "status": "SUCCESS",
                "data": {
                    "order_id": order_id,
                    "status": "ORDER_CONFIRMED",
                    "updated_address": full_address,
                    "zipcode": zipcode,
                    "recipient_name": order_info.get("recipient_name", recipient_name),
                    "recipient_phone": order_info.get("recipient_phone", recipient_phone),
                    "message": "배송지 주소가 정상적으로 변경되었습니다.",
                },
            },
            request=request,
        )

    def _handle_escalate_ticket(self, body: Dict[str, Any], request: httpx.Request) -> httpx.Response:
        user_key = body.get("user_key")
        category = body.get("category", "GENERAL")
        customer_name = body.get("customer_name", "고객")
        contact = body.get("contact", "")
        issue_summary = body.get("issue_summary") or body.get("summary", "")
        order_id = body.get("order_id")
        claim_amount = body.get("claim_amount", 0)
        requested_resolution = body.get("requested_resolution", "")

        if not user_key:
            return httpx.Response(
                status_code=400,
                json={
                    "status": "FAILED",
                    "error_code": "MISSING_USER_KEY",
                    "message": "user_key는 필수 파라미터입니다.",
                },
                request=request,
            )

        try:
            claim_amount_int = int(claim_amount) if claim_amount is not None else 0
        except (ValueError, TypeError):
            claim_amount_int = 0

        self.ticket_counter += 1
        ticket_id = f"TICKET-20370630-{self.ticket_counter:04d}"

        is_urgent = claim_amount_int > 50000 or category in ["DISPUTE_REFUND", "LEGAL", "URGENT"]
        requires_chairman_approval = claim_amount_int > 50000
        assigned_to = "이민준 (청년회 CS총괄)"
        authority_level = "LEVEL_2_MANAGER"

        data: Dict[str, Any] = {
            "ticket_id": ticket_id,
            "user_key": user_key,
            "category": category,
            "customer_name": customer_name,
            "contact": contact,
            "order_id": order_id,
            "claim_amount": claim_amount_int,
            "is_urgent": is_urgent,
            "assigned_to": assigned_to,
            "authority_level": authority_level,
            "requires_chairman_approval": requires_chairman_approval,
            "requested_resolution": requested_resolution,
            "operating_hours": "평일 09:00~18:00",
            "message": "상담원 긴급 이관 티켓이 등록되었습니다. 담당자가 순차 연락 예정입니다.",
        }

        if requires_chairman_approval:
            data["approval_note"] = "5만 원 초과 건으로 고길동 조합장 승인 필요 사안"
            data["message"] = (
                "상담원 긴급 이관 티켓이 등록되었습니다. "
                "(5만 원 초과 건으로 고길동 조합장 승인 필요 사안) "
                "담당자가 순차 연락 예정입니다."
            )

        return httpx.Response(
            status_code=200,
            json={
                "status": "SUCCESS",
                "data": data,
            },
            request=request,
        )
